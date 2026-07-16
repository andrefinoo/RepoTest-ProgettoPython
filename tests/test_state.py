"""Test della persistenza dello storico ban."""

import json
from datetime import datetime

import pytest

from ban_engine.models import BanDecision
from ban_engine.state import load_ban_history, save_ban_decisions


def make_decision(ip: str) -> BanDecision:
    return BanDecision(
        ip=ip,
        attempts_count=3,
        window_seconds=60,
        reason="troppi tentativi",
        created_at=datetime(2026, 7, 16, 8, 0),
    )


def test_load_ban_history_returns_empty_list_for_missing_file(tmp_path) -> None:
    assert load_ban_history(tmp_path / "state.json") == []


def test_save_ban_decisions_writes_json(tmp_path) -> None:
    state_file = tmp_path / "state.json"

    save_ban_decisions(state_file, [make_decision("192.0.2.10")])

    data = json.loads(state_file.read_text(encoding="utf-8"))
    assert len(data) == 1
    assert data[0]["ip"] == "192.0.2.10"


def test_save_ban_decisions_appends_without_overwriting(tmp_path) -> None:
    state_file = tmp_path / "state.json"

    save_ban_decisions(state_file, [make_decision("192.0.2.10")])
    save_ban_decisions(state_file, [make_decision("198.51.100.20")])

    history = load_ban_history(state_file)
    assert [item["ip"] for item in history] == [
        "192.0.2.10",
        "198.51.100.20",
    ]


def test_load_ban_history_rejects_invalid_json(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text("non-json", encoding="utf-8")

    with pytest.raises(ValueError):
        load_ban_history(state_file)
