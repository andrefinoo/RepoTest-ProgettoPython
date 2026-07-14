from datetime import datetime

import pytest

from src.ban_engine.models import BanDecision, LoginAttempt, validate_ip


def test_validate_ip_accepts_valid_ipv4() -> None:
    assert validate_ip("192.168.1.10") == "192.168.1.10"


def test_validate_ip_accepts_valid_ipv6() -> None:
    assert validate_ip("2001:db8::1") == "2001:db8::1"


def test_validate_ip_rejects_invalid_ip() -> None:
    with pytest.raises(ValueError):
        validate_ip("999.999.999.999")


def test_login_attempt_normalizes_empty_username() -> None:
    attempt = LoginAttempt(
        timestamp=datetime(2026, 7, 3, 10, 30),
        ip="192.168.1.10",
        username="",
        raw_line="Failed password from 192.168.1.10",
    )

    assert attempt.username is None


def test_login_attempt_to_dict_is_json_friendly() -> None:
    attempt = LoginAttempt(
        timestamp=datetime(2026, 7, 3, 10, 30),
        ip="192.168.1.10",
        username="root",
        raw_line="Failed password for root from 192.168.1.10",
    )

    data = attempt.to_dict()

    assert data["timestamp"] == "2026-07-03T10:30:00"
    assert data["ip"] == "192.168.1.10"
    assert data["username"] == "root"


def test_ban_decision_rejects_invalid_attempt_count() -> None:
    with pytest.raises(ValueError):
        BanDecision(
            ip="192.168.1.10",
            attempts_count=0,
            window_seconds=600,
            reason="troppi tentativi falliti",
            created_at=datetime(2026, 7, 3, 10, 30),
        )