"""Test del caricamento della configurazione."""

import json

import pytest

from ban_engine.config import load_config


def test_load_config_uses_defaults_without_file() -> None:
    config = load_config()

    assert config.max_attempts == 3
    assert config.window_seconds == 300
    assert config.backend == "dry-run"
    assert config.dry_run is True


def test_load_config_reads_json_and_whitelist(tmp_path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps(
            {
                "max_attempts": 5,
                "window_seconds": 120,
                "whitelist": ["127.0.0.1", "2001:db8::1"],
                "backend": "windows",
                "dry_run": False,
                "state_file": "state.json",
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_file)

    assert config.max_attempts == 5
    assert config.window_seconds == 120
    assert config.whitelist == {"127.0.0.1", "2001:db8::1"}
    assert config.backend == "windows"
    assert config.dry_run is False


def test_load_config_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "missing.json")


def test_load_config_rejects_invalid_json(tmp_path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text("{non valido", encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(config_file)


def test_load_config_rejects_invalid_whitelist_ip(tmp_path) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"whitelist": ["999.999.999.999"]}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_config(config_file)
