"""Test dell'IncidentResponseEngine."""

from datetime import datetime, timedelta

from ban_engine.engine import IncidentResponseEngine
from ban_engine.firewall.dry_run import DryRunFirewallBackend
from ban_engine.models import LoginAttempt


def make_attempt(ip: str, seconds: int) -> LoginAttempt:
    return LoginAttempt(
        timestamp=datetime(2026, 7, 16, 8, 0) + timedelta(seconds=seconds),
        ip=ip,
        username="root",
        raw_line="Failed password",
    )


def test_engine_blocks_ip_when_threshold_is_reached() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    attempts = [
        make_attempt("192.0.2.10", 0),
        make_attempt("192.0.2.10", 20),
        make_attempt("192.0.2.10", 40),
    ]

    decisions = engine.process_attempts(attempts)

    assert len(decisions) == 1
    assert decisions[0].ip == "192.0.2.10"
    assert decisions[0].attempts_count == 3
    assert backend.is_blocked("192.0.2.10") is True


def test_engine_does_not_block_below_threshold() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)

    decisions = engine.process_attempts(
        [make_attempt("192.0.2.10", 0), make_attempt("192.0.2.10", 20)]
    )

    assert decisions == []
    assert backend.is_blocked("192.0.2.10") is False


def test_engine_respects_time_window() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    attempts = [
        make_attempt("192.0.2.10", 0),
        make_attempt("192.0.2.10", 70),
        make_attempt("192.0.2.10", 140),
    ]

    assert engine.process_attempts(attempts) == []


def test_engine_skips_whitelisted_ip() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(
        backend,
        max_attempts=2,
        window_seconds=60,
        whitelist={"192.0.2.10"},
    )

    decisions = engine.process_attempts(
        [make_attempt("192.0.2.10", 0), make_attempt("192.0.2.10", 10)]
    )

    assert decisions == []
    assert backend.is_blocked("192.0.2.10") is False


def test_engine_does_not_block_same_ip_twice() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=2, window_seconds=60)
    attempts = [make_attempt("192.0.2.10", 0), make_attempt("192.0.2.10", 10)]

    first_decisions = engine.process_attempts(attempts)
    second_decisions = engine.process_attempts(attempts)

    assert len(first_decisions) == 1
    assert second_decisions == []
