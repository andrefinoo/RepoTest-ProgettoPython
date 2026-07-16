"""Test essenziali della CLI."""

import json

from ban_engine.cli import main


def test_cli_runs_complete_dry_run(tmp_path, capsys) -> None:
    log_file = tmp_path / "auth.log"
    log_file.write_text(
        "\n".join(
            [
                "Jul 16 08:00:00 server sshd[1]: Failed password for root from 192.0.2.10 port 22 ssh2",
                "Jul 16 08:00:10 server sshd[2]: Failed password for root from 192.0.2.10 port 22 ssh2",
                "Jul 16 08:00:20 server sshd[3]: Failed password for root from 192.0.2.10 port 22 ssh2",
            ]
        ),
        encoding="utf-8",
    )
    state_file = tmp_path / "state.json"
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "max_attempts": 3,
                "window_seconds": 60,
                "whitelist": [],
                "backend": "dry-run",
                "dry_run": True,
                "state_file": str(state_file),
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(["--log", str(log_file), "--config", str(config_file)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "IP bannati: 1" in output
    assert state_file.exists()


def test_cli_returns_error_for_missing_log(tmp_path, capsys) -> None:
    exit_code = main(["--log", str(tmp_path / "missing.log"), "--dry-run"])

    error_output = capsys.readouterr().err
    assert exit_code == 2
    assert "Errore:" in error_output
