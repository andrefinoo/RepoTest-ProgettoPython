"""Test completi della configurazione JSON."""

import json

import pytest

from ban_engine.config import AppConfig, load_config


def write_config(tmp_path, data) -> object:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_app_config_defaults() -> None:
    config = AppConfig()
    assert config.max_attempts == 3
    assert config.window_seconds == 300
    assert config.whitelist == set()
    assert config.backend == "dry-run"
    assert config.dry_run is True
    assert config.state_file == "ban_state.json"


def test_default_whitelist_is_not_shared() -> None:
    first = AppConfig()
    second = AppConfig()
    first.whitelist.add("127.0.0.1")
    assert second.whitelist == set()


def test_load_config_without_path_uses_defaults() -> None:
    assert load_config() == AppConfig()


def test_load_config_reads_all_fields(tmp_path) -> None:
    path = write_config(
        tmp_path,
        {
            "max_attempts": 5,
            "window_seconds": 120,
            "whitelist": ["127.0.0.1", "2001:0db8::1"],
            "backend": "windows",
            "dry_run": False,
            "state_file": "data/state.json",
        },
    )
    config = load_config(path)
    assert config.max_attempts == 5
    assert config.window_seconds == 120
    assert config.whitelist == {"127.0.0.1", "2001:db8::1"}
    assert config.backend == "windows"
    assert config.dry_run is False
    assert config.state_file == "data/state.json"


def test_load_config_uses_defaults_for_missing_keys(tmp_path) -> None:
    config = load_config(write_config(tmp_path, {"max_attempts": 7}))
    assert config.max_attempts == 7
    assert config.window_seconds == 300
    assert config.backend == "dry-run"


def test_load_config_removes_duplicate_whitelist_values(tmp_path) -> None:
    config = load_config(
        write_config(tmp_path, {"whitelist": ["192.0.2.10", "192.0.2.10"]})
    )
    assert config.whitelist == {"192.0.2.10"}


def test_load_config_rejects_missing_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError, match="non trovato"):
        load_config(tmp_path / "missing.json")


def test_load_config_rejects_invalid_json(tmp_path) -> None:
    path = tmp_path / "config.json"
    path.write_text("{non valido", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON non valido"):
        load_config(path)


@pytest.mark.parametrize("data", [[], "testo", 3, None])
def test_load_config_requires_json_object(tmp_path, data) -> None:
    with pytest.raises(ValueError, match="oggetto"):
        load_config(write_config(tmp_path, data))


@pytest.mark.parametrize("value", [0, -1, "3", 3.5, None])
def test_load_config_rejects_invalid_max_attempts(tmp_path, value) -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        load_config(write_config(tmp_path, {"max_attempts": value}))


@pytest.mark.parametrize("value", [0, -1, "60", 1.5, None])
def test_load_config_rejects_invalid_window(tmp_path, value) -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        load_config(write_config(tmp_path, {"window_seconds": value}))


@pytest.mark.parametrize("value", ["192.0.2.10", {}, 3, None])
def test_load_config_requires_whitelist_list(tmp_path, value) -> None:
    with pytest.raises(ValueError, match="whitelist"):
        load_config(write_config(tmp_path, {"whitelist": value}))


def test_load_config_rejects_invalid_whitelist_ip(tmp_path) -> None:
    with pytest.raises(ValueError, match="Indirizzo IP non valido"):
        load_config(write_config(tmp_path, {"whitelist": ["bad-ip"]}))


@pytest.mark.parametrize("backend", ["", "iptables", "mac", None, 3])
def test_load_config_rejects_invalid_backend(tmp_path, backend) -> None:
    with pytest.raises(ValueError, match="backend"):
        load_config(write_config(tmp_path, {"backend": backend}))


@pytest.mark.parametrize("dry_run", ["true", 1, 0, None, []])
def test_load_config_rejects_non_boolean_dry_run(tmp_path, dry_run) -> None:
    with pytest.raises(ValueError, match="dry_run"):
        load_config(write_config(tmp_path, {"dry_run": dry_run}))


@pytest.mark.parametrize("state_file", ["", 3, None, []])
def test_load_config_rejects_invalid_state_file(tmp_path, state_file) -> None:
    with pytest.raises(ValueError, match="state_file"):
        load_config(write_config(tmp_path, {"state_file": state_file}))
