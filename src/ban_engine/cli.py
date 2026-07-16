"""Interfaccia a riga di comando del Ban Engine."""

import argparse
import subprocess
import sys
from pathlib import Path

from .config import AppConfig, load_config
from .engine import IncidentResponseEngine
from .firewall import (
    DryRunFirewallBackend,
    FirewallBackend,
    LinuxIptablesBackend,
    WindowsFirewallBackend,
)
from .parser import SSHLogParser
from .state import save_ban_decisions


def positive_int(value: str) -> int:
    """Converte un argomento CLI in intero positivo."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("il valore deve essere maggiore di zero")
    return number


def build_parser() -> argparse.ArgumentParser:
    """Crea e restituisce il parser degli argomenti."""
    parser = argparse.ArgumentParser(
        prog="ban_engine",
        description="Analizza log SSH e blocca gli IP sospetti.",
    )
    parser.add_argument("--log", required=True, help="Percorso del file auth.log")
    parser.add_argument("--config", help="Percorso del file JSON di configurazione")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula i blocchi senza modificare il firewall",
    )
    parser.add_argument(
        "--threshold",
        type=positive_int,
        help="Numero massimo di tentativi consentiti",
    )
    parser.add_argument(
        "--window",
        type=positive_int,
        help="Finestra temporale in secondi",
    )
    parser.add_argument(
        "--state",
        help="Percorso alternativo del file JSON con lo storico ban",
    )
    return parser


def create_backend(name: str) -> FirewallBackend:
    """Crea il backend richiesto dalla configurazione."""
    if name == "linux":
        return LinuxIptablesBackend()
    if name == "windows":
        return WindowsFirewallBackend()
    return DryRunFirewallBackend()


def apply_overrides(config: AppConfig, args: argparse.Namespace) -> AppConfig:
    """Applica alla configurazione i valori specificati nella CLI."""
    if args.threshold is not None:
        config.max_attempts = args.threshold
    if args.window is not None:
        config.window_seconds = args.window
    if args.dry_run:
        config.dry_run = True
    if args.state is not None:
        config.state_file = args.state
    return config


def main(argv: list[str] | None = None) -> int:
    """Esegue il flusso completo e restituisce il codice di uscita."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = apply_overrides(load_config(args.config), args)
        backend_name = "dry-run" if config.dry_run else config.backend
        backend = create_backend(backend_name)

        log_path = Path(args.log)
        with log_path.open("r", encoding="utf-8") as log_file:
            total_lines = sum(1 for _ in log_file)

        attempts = SSHLogParser().parse_file(log_path)
        engine = IncidentResponseEngine(
            backend=backend,
            max_attempts=config.max_attempts,
            window_seconds=config.window_seconds,
            whitelist=config.whitelist,
        )
        decisions = engine.process_attempts(attempts)
        save_ban_decisions(config.state_file, decisions)

        suspicious_ips = {attempt.ip for attempt in attempts}
        whitelisted_ips = suspicious_ips & config.whitelist

        print("Analisi completata")
        print(f"Righe analizzate: {total_lines}")
        print(f"Tentativi falliti riconosciuti: {len(attempts)}")
        print(f"IP sospetti: {len(suspicious_ips)}")
        print(f"IP in whitelist: {len(whitelisted_ips)}")
        print(f"IP bannati: {len(decisions)}")

        return 0
    except (FileNotFoundError, ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"Errore: {error}", file=sys.stderr)
        return 2
