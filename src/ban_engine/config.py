"""Caricamento della configurazione JSON."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from .models import validate_ip


@dataclass
class AppConfig:
    """Configurazione usata dalla CLI e dall'engine."""

    max_attempts: int = 3
    window_seconds: int = 300
    whitelist: set[str] = field(default_factory=set)
    backend: str = "dry-run"
    dry_run: bool = True
    state_file: str = "ban_state.json"


def load_config(path: str | Path | None = None) -> AppConfig:
    """Carica la configurazione oppure restituisce i valori predefiniti."""
    if path is None:
        return AppConfig()

    config_path = Path(path)

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            data = json.load(config_file)
    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"File di configurazione non trovato: {config_path}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"JSON non valido nel file {config_path}: riga {error.lineno}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError("La configurazione JSON deve essere un oggetto")

    max_attempts = data.get("max_attempts", 3)
    window_seconds = data.get("window_seconds", 300)
    whitelist_data = data.get("whitelist", [])
    backend = data.get("backend", "dry-run")
    dry_run = data.get("dry_run", True)
    state_file = data.get("state_file", "ban_state.json")

    if not isinstance(max_attempts, int) or max_attempts <= 0:
        raise ValueError("max_attempts deve essere un intero maggiore di zero")
    if not isinstance(window_seconds, int) or window_seconds <= 0:
        raise ValueError("window_seconds deve essere un intero maggiore di zero")
    if not isinstance(whitelist_data, list):
        raise ValueError("whitelist deve essere una lista")
    if backend not in {"dry-run", "linux", "windows"}:
        raise ValueError("backend deve essere dry-run, linux oppure windows")
    if not isinstance(dry_run, bool):
        raise ValueError("dry_run deve essere true oppure false")
    if not isinstance(state_file, str) or not state_file:
        raise ValueError("state_file deve essere una stringa non vuota")

    whitelist = {validate_ip(ip) for ip in whitelist_data}

    return AppConfig(
        max_attempts=max_attempts,
        window_seconds=window_seconds,
        whitelist=whitelist,
        backend=backend,
        dry_run=dry_run,
        state_file=state_file,
    )
