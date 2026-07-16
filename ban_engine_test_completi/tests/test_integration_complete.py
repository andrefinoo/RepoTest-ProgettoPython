"""Test di integrazione del flusso completo."""

import json

from ban_engine.cli import main
from ban_engine.engine import IncidentResponseEngine
from ban_engine.firewall.dry_run import DryRunFirewallBackend
from ban_engine.parser import SSHLogParser
from ban_engine.state import load_ban_history, save_ban_decisions


def test_parser_engine_state_pipeline(tmp_path) -> None:
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
    attempts = SSHLogParser().parse_file(log_file)
    decisions = IncidentResponseEngine(
        DryRunFirewallBackend(),
        max_attempts=3,
        window_seconds=60,
    ).process_attempts(attempts)
    state_file = tmp_path / "state.json"
    save_ban_decisions(state_file, decisions)
    history = load_ban_history(state_file)
    assert len(attempts) == 3
    assert len(decisions) == 1
    assert history[0]["ip"] == "192.0.2.10"


def test_full_cli_pipeline_with_ipv6(tmp_path, capsys) -> None:
    log_file = tmp_path / "auth.log"
    log_file.write_text(
        "\n".join(
            [
                "Jul 16 08:00:00 server sshd[1]: Failed password for root from 2001:db8::1 port 22 ssh2",
                "Jul 16 08:00:10 server sshd[2]: Failed password for root from 2001:db8::1 port 22 ssh2",
            ]
        ),
        encoding="utf-8",
    )
    state_file = tmp_path / "state.json"
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "max_attempts": 2,
                "window_seconds": 60,
                "whitelist": [],
                "backend": "dry-run",
                "dry_run": True,
                "state_file": str(state_file),
            }
        ),
        encoding="utf-8",
    )
    assert main(["--log", str(log_file), "--config", str(config_file)]) == 0
    assert "IP bannati: 1" in capsys.readouterr().out
    assert load_ban_history(state_file)[0]["ip"] == "2001:db8::1"


def test_full_cli_pipeline_bans_one_and_whitelists_one(tmp_path, capsys) -> None:
    log_file = tmp_path / "auth.log"
    log_file.write_text(
        "\n".join(
            [
                "Jul 16 08:00:00 server sshd[1]: Failed password for root from 192.0.2.10 port 22 ssh2",
                "Jul 16 08:00:10 server sshd[2]: Failed password for root from 192.0.2.10 port 22 ssh2",
                "Jul 16 08:00:00 server sshd[3]: Failed password for root from 198.51.100.20 port 22 ssh2",
                "Jul 16 08:00:10 server sshd[4]: Failed password for root from 198.51.100.20 port 22 ssh2",
            ]
        ),
        encoding="utf-8",
    )
    state_file = tmp_path / "state.json"
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "max_attempts": 2,
                "window_seconds": 60,
                "whitelist": ["198.51.100.20"],
                "backend": "dry-run",
                "dry_run": True,
                "state_file": str(state_file),
            }
        ),
        encoding="utf-8",
    )
    assert main(["--log", str(log_file), "--config", str(config_file)]) == 0
    output = capsys.readouterr().out
    assert "IP sospetti: 2" in output
    assert "IP in whitelist: 1" in output
    assert "IP bannati: 1" in output
    history = load_ban_history(state_file)
    assert [item["ip"] for item in history] == ["192.0.2.10"]


def test_cli_without_config_uses_defaults_safely(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.chdir(tmp_path)
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
    assert main(["--log", str(log_file), "--dry-run"]) == 0
    assert "IP bannati: 1" in capsys.readouterr().out
    assert (tmp_path / "ban_state.json").exists()
