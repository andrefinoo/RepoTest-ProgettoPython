"""Test completi della persistenza JSON."""

import json
from datetime import datetime

import pytest

from ban_engine.models import BanDecision
from ban_engine.state import load_ban_history, save_ban_decisions


def make_decision(ip: str = "192.0.2.10", reason: str = "troppi tentativi") -> BanDecision:
    return BanDecision(
        ip=ip,
        attempts_count=3,
        window_seconds=60,
        reason=reason,
        created_at=datetime(2026, 7, 16, 8, 0),
    )


def test_load_missing_file_returns_empty_list(tmp_path) -> None:
    assert load_ban_history(tmp_path / "missing.json") == []


def test_load_valid_history(tmp_path) -> None:
    path = tmp_path / "state.json"
    data = [{"ip": "192.0.2.10", "attempts_count": 3}]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert load_ban_history(path) == data


def test_load_invalid_json_raises_value_error(tmp_path) -> None:
    path = tmp_path / "state.json"
    path.write_text("non-json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON non valido"):
        load_ban_history(path)


@pytest.mark.parametrize("data", [{}, "testo", 3, None])
def test_load_requires_list(tmp_path, data) -> None:
    path = tmp_path / "state.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ValueError, match="lista"):
        load_ban_history(path)


def test_save_empty_decisions_does_not_create_file(tmp_path) -> None:
    path = tmp_path / "state.json"
    save_ban_decisions(path, [])
    assert path.exists() is False


def test_save_writes_one_decision(tmp_path) -> None:
    path = tmp_path / "state.json"
    save_ban_decisions(path, [make_decision()])
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == [
        {
            "ip": "192.0.2.10",
            "attempts_count": 3,
            "window_seconds": 60,
            "reason": "troppi tentativi",
            "created_at": "2026-07-16T08:00:00",
        }
    ]


def test_save_appends_without_overwriting(tmp_path) -> None:
    path = tmp_path / "state.json"
    save_ban_decisions(path, [make_decision("192.0.2.10")])
    save_ban_decisions(path, [make_decision("198.51.100.20")])
    history = load_ban_history(path)
    assert [item["ip"] for item in history] == ["192.0.2.10", "198.51.100.20"]


def test_save_multiple_decisions_at_once(tmp_path) -> None:
    path = tmp_path / "state.json"
    save_ban_decisions(
        path,
        [make_decision("192.0.2.10"), make_decision("198.51.100.20")],
    )
    assert len(load_ban_history(path)) == 2


def test_save_creates_parent_directories(tmp_path) -> None:
    path = tmp_path / "nested" / "folder" / "state.json"
    save_ban_decisions(path, [make_decision()])
    assert path.exists()


def test_save_preserves_unicode_text(tmp_path) -> None:
    path = tmp_path / "state.json"
    save_ban_decisions(path, [make_decision(reason="più tentativi falliti")])
    content = path.read_text(encoding="utf-8")
    assert "più" in content
    assert "\\u00f9" not in content


def test_save_fails_when_existing_state_is_invalid(tmp_path) -> None:
    path = tmp_path / "state.json"
    path.write_text("non-json", encoding="utf-8")
    with pytest.raises(ValueError):
        save_ban_decisions(path, [make_decision()])
