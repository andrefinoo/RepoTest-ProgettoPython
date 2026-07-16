"""Test completi della CLI."""

import argparse
import json
import subprocess
from unittest.mock import patch

import pytest

from ban_engine.cli import (
    apply_overrides,
    build_parser,
    create_backend,
    main,
    positive_int,
)
from ban_engine.config import AppConfig
from ban_engine.firewall.dry_run import DryRunFirewallBackend
from ban_engine.firewall.linux import LinuxIptablesBackend
from ban_engine.firewall.windows import WindowsFirewallBackend


def make_log(tmp_path, lines: list[str]):
    path = tmp_path / "auth.log"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def make_config(tmp_path, **overrides):
    data = {
        "max_attempts": 3,
        "window_seconds": 60,
        "whitelist": [],
        "backend": "dry-run",
        "dry_run": True,
        "state_file": str(tmp_path / "state.json"),
    }
    data.update(overrides)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def failed(ip: str, second: int) -> str:
    return (
        f"Jul 16 08:00:{second:02d} server sshd[{second + 1}]: "
        f"Failed password for root from {ip} port 22 ssh2"
    )


def test_positive_int_accepts_positive_number() -> None:
    assert positive_int("5") == 5


@pytest.mark.parametrize("value", ["0", "-1"])
def test_positive_int_rejects_non_positive_number(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int(value)


def test_positive_int_rejects_non_numeric_value() -> None:
    with pytest.raises(ValueError):
        positive_int("abc")


def test_build_parser_requires_log_argument() -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as error:
        parser.parse_args([])
    assert error.value.code == 2


def test_build_parser_help_exits_successfully(capsys) -> None:
    parser = build_parser()
    with pytest.raises(SystemExit) as error:
        parser.parse_args(["--help"])
    assert error.value.code == 0
    assert "Analizza log SSH" in capsys.readouterr().out


def test_create_backend_dry_run() -> None:
    assert isinstance(create_backend("dry-run"), DryRunFirewallBackend)


def test_create_backend_linux() -> None:
    assert isinstance(create_backend("linux"), LinuxIptablesBackend)


def test_create_backend_windows() -> None:
    assert isinstance(create_backend("windows"), WindowsFirewallBackend)


def test_apply_overrides_replaces_requested_values() -> None:
    config = AppConfig()
    args = argparse.Namespace(
        threshold=7,
        window=90,
        dry_run=True,
        state="custom-state.json",
    )
    result = apply_overrides(config, args)
    assert result.max_attempts == 7
    assert result.window_seconds == 90
    assert result.dry_run is True
    assert result.state_file == "custom-state.json"


def test_apply_overrides_keeps_values_when_options_are_missing() -> None:
    config = AppConfig(max_attempts=5, window_seconds=120, dry_run=False)
    args = argparse.Namespace(threshold=None, window=None, dry_run=False, state=None)
    result = apply_overrides(config, args)
    assert result.max_attempts == 5
    assert result.window_seconds == 120
    assert result.dry_run is False


def test_cli_complete_dry_run(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0), failed("192.0.2.10", 10), failed("192.0.2.10", 20)])
    config_path = make_config(tmp_path)
    exit_code = main(["--log", str(log_path), "--config", str(config_path)])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Analisi completata" in output
    assert "Righe analizzate: 3" in output
    assert "Tentativi falliti riconosciuti: 3" in output
    assert "IP sospetti: 1" in output
    assert "IP bannati: 1" in output
    assert (tmp_path / "state.json").exists()


def test_cli_reports_no_ban_below_threshold(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0), failed("192.0.2.10", 10)])
    config_path = make_config(tmp_path)
    assert main(["--log", str(log_path), "--config", str(config_path)]) == 0
    assert "IP bannati: 0" in capsys.readouterr().out


def test_cli_threshold_override(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0), failed("192.0.2.10", 10)])
    config_path = make_config(tmp_path, max_attempts=5)
    exit_code = main(
        [
            "--log",
            str(log_path),
            "--config",
            str(config_path),
            "--threshold",
            "2",
        ]
    )
    assert exit_code == 0
    assert "IP bannati: 1" in capsys.readouterr().out


def test_cli_window_override(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0), failed("192.0.2.10", 10), failed("192.0.2.10", 20)])
    config_path = make_config(tmp_path, window_seconds=5)
    exit_code = main(
        [
            "--log",
            str(log_path),
            "--config",
            str(config_path),
            "--window",
            "30",
        ]
    )
    assert exit_code == 0
    assert "IP bannati: 1" in capsys.readouterr().out


def test_cli_state_path_override(tmp_path) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0), failed("192.0.2.10", 10), failed("192.0.2.10", 20)])
    config_path = make_config(tmp_path)
    custom_state = tmp_path / "custom" / "history.json"
    exit_code = main(
        [
            "--log",
            str(log_path),
            "--config",
            str(config_path),
            "--state",
            str(custom_state),
        ]
    )
    assert exit_code == 0
    assert custom_state.exists()


def test_cli_respects_whitelist(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0), failed("192.0.2.10", 10), failed("192.0.2.10", 20)])
    config_path = make_config(tmp_path, whitelist=["192.0.2.10"])
    assert main(["--log", str(log_path), "--config", str(config_path)]) == 0
    output = capsys.readouterr().out
    assert "IP in whitelist: 1" in output
    assert "IP bannati: 0" in output


def test_cli_ignores_unrelated_lines(tmp_path, capsys) -> None:
    log_path = make_log(
        tmp_path,
        [
            "Jul 16 08:00:00 server sshd[1]: Accepted password for root from 192.0.2.10 port 22 ssh2",
            "testo non pertinente",
        ],
    )
    config_path = make_config(tmp_path)
    assert main(["--log", str(log_path), "--config", str(config_path)]) == 0
    output = capsys.readouterr().out
    assert "Righe analizzate: 2" in output
    assert "Tentativi falliti riconosciuti: 0" in output


def test_cli_counts_multiple_suspicious_ips(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0), failed("198.51.100.20", 10)])
    config_path = make_config(tmp_path, max_attempts=5)
    assert main(["--log", str(log_path), "--config", str(config_path)]) == 0
    assert "IP sospetti: 2" in capsys.readouterr().out


def test_cli_missing_log_returns_error(tmp_path, capsys) -> None:
    exit_code = main(["--log", str(tmp_path / "missing.log"), "--dry-run"])
    assert exit_code == 2
    assert "Errore:" in capsys.readouterr().err


def test_cli_missing_config_returns_error(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [])
    exit_code = main(
        ["--log", str(log_path), "--config", str(tmp_path / "missing.json")]
    )
    assert exit_code == 2
    assert "Errore:" in capsys.readouterr().err


def test_cli_invalid_config_returns_error(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [])
    config_path = tmp_path / "config.json"
    config_path.write_text("{bad", encoding="utf-8")
    assert main(["--log", str(log_path), "--config", str(config_path)]) == 2
    assert "Errore:" in capsys.readouterr().err


def test_cli_invalid_ip_in_log_returns_error(tmp_path, capsys) -> None:
    log_path = make_log(
        tmp_path,
        ["Jul 16 08:00:00 server sshd[1]: Failed password for root from bad-ip port 22 ssh2"],
    )
    config_path = make_config(tmp_path)
    assert main(["--log", str(log_path), "--config", str(config_path)]) == 2
    assert "Errore:" in capsys.readouterr().err


def test_cli_dry_run_option_forces_safe_backend(tmp_path) -> None:
    log_path = make_log(tmp_path, [])
    config_path = make_config(tmp_path, backend="windows", dry_run=False)
    with patch("ban_engine.cli.create_backend", wraps=create_backend) as factory:
        assert main(
            [
                "--log",
                str(log_path),
                "--config",
                str(config_path),
                "--dry-run",
            ]
        ) == 0
    factory.assert_called_once_with("dry-run")


def test_cli_uses_configured_backend_when_not_dry_run(tmp_path) -> None:
    log_path = make_log(tmp_path, [])
    config_path = make_config(tmp_path, backend="windows", dry_run=False)
    safe_backend = DryRunFirewallBackend()
    with patch("ban_engine.cli.create_backend", return_value=safe_backend) as factory:
        assert main(["--log", str(log_path), "--config", str(config_path)]) == 0
    factory.assert_called_once_with("windows")


def test_cli_catches_firewall_subprocess_error(tmp_path, capsys) -> None:
    log_path = make_log(tmp_path, [failed("192.0.2.10", 0)])
    config_path = make_config(tmp_path, max_attempts=1, backend="linux", dry_run=False)
    backend = DryRunFirewallBackend()
    backend.block_ip = lambda ip: (_ for _ in ()).throw(
        subprocess.CalledProcessError(1, ["iptables"])
    )
    with patch("ban_engine.cli.create_backend", return_value=backend):
        assert main(["--log", str(log_path), "--config", str(config_path)]) == 2
    assert "Errore:" in capsys.readouterr().err
