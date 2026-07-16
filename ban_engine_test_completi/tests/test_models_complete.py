"""Test completi dei modelli dati."""

import json
from datetime import datetime

import pytest

from ban_engine.models import BanDecision, LoginAttempt, validate_ip


def test_validate_ip_accepts_ipv4() -> None:
    assert validate_ip("192.168.1.10") == "192.168.1.10"


def test_validate_ip_accepts_and_normalizes_ipv6() -> None:
    assert validate_ip("2001:0db8:0:0:0:0:0:1") == "2001:db8::1"


def test_validate_ip_accepts_loopback() -> None:
    assert validate_ip("127.0.0.1") == "127.0.0.1"


@pytest.mark.parametrize(
    "invalid_ip",
    ["", "abc", "999.999.999.999", "192.168.1", "2001:db8:::1"],
)
def test_validate_ip_rejects_invalid_values(invalid_ip: str) -> None:
    with pytest.raises(ValueError, match="Indirizzo IP non valido"):
        validate_ip(invalid_ip)


def test_login_attempt_normalizes_empty_username() -> None:
    attempt = LoginAttempt(
        timestamp=datetime(2026, 7, 16, 8, 0),
        ip="192.0.2.10",
        username="",
        raw_line="riga",
    )
    assert attempt.username is None


def test_login_attempt_keeps_username() -> None:
    attempt = LoginAttempt(
        timestamp=datetime(2026, 7, 16, 8, 0),
        ip="192.0.2.10",
        username="root",
        raw_line="riga",
    )
    assert attempt.username == "root"


def test_login_attempt_accepts_none_username() -> None:
    attempt = LoginAttempt(
        timestamp=datetime(2026, 7, 16, 8, 0),
        ip="192.0.2.10",
        username=None,
        raw_line="riga",
    )
    assert attempt.username is None


def test_login_attempt_rejects_invalid_ip() -> None:
    with pytest.raises(ValueError):
        LoginAttempt(
            timestamp=datetime(2026, 7, 16, 8, 0),
            ip="non-un-ip",
            username="root",
            raw_line="riga",
        )


def test_login_attempt_to_dict_contains_all_fields() -> None:
    attempt = LoginAttempt(
        timestamp=datetime(2026, 7, 16, 8, 0, 5),
        ip="2001:0db8::1",
        username="admin",
        raw_line="Failed password",
    )
    assert attempt.to_dict() == {
        "timestamp": "2026-07-16T08:00:05",
        "ip": "2001:db8::1",
        "username": "admin",
        "raw_line": "Failed password",
    }


def test_login_attempt_to_dict_is_json_serializable() -> None:
    attempt = LoginAttempt(
        timestamp=datetime(2026, 7, 16, 8, 0),
        ip="192.0.2.10",
        username="root",
        raw_line="riga",
    )
    assert json.loads(json.dumps(attempt.to_dict()))["ip"] == "192.0.2.10"


def make_decision(**overrides) -> BanDecision:
    values = {
        "ip": "192.0.2.10",
        "attempts_count": 3,
        "window_seconds": 60,
        "reason": "troppi tentativi",
        "created_at": datetime(2026, 7, 16, 8, 0),
    }
    values.update(overrides)
    return BanDecision(**values)


def test_ban_decision_accepts_valid_data() -> None:
    decision = make_decision()
    assert decision.ip == "192.0.2.10"
    assert decision.attempts_count == 3


@pytest.mark.parametrize("attempts_count", [0, -1, -10])
def test_ban_decision_rejects_invalid_attempt_count(attempts_count: int) -> None:
    with pytest.raises(ValueError, match="attempts_count"):
        make_decision(attempts_count=attempts_count)


@pytest.mark.parametrize("window_seconds", [0, -1, -60])
def test_ban_decision_rejects_invalid_window(window_seconds: int) -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        make_decision(window_seconds=window_seconds)


def test_ban_decision_rejects_invalid_ip() -> None:
    with pytest.raises(ValueError):
        make_decision(ip="999.999.999.999")


def test_ban_decision_to_dict_contains_all_fields() -> None:
    decision = make_decision(ip="2001:0db8::1")
    assert decision.to_dict() == {
        "ip": "2001:db8::1",
        "attempts_count": 3,
        "window_seconds": 60,
        "reason": "troppi tentativi",
        "created_at": "2026-07-16T08:00:00",
    }


def test_ban_decision_to_dict_is_json_serializable() -> None:
    encoded = json.dumps(make_decision().to_dict())
    assert json.loads(encoded)["attempts_count"] == 3
