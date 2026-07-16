"""Test completi dell'IncidentResponseEngine."""

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from ban_engine.engine import IncidentResponseEngine
from ban_engine.firewall.base import FirewallBackend
from ban_engine.firewall.dry_run import DryRunFirewallBackend
from ban_engine.models import LoginAttempt


BASE_TIME = datetime(2026, 7, 16, 8, 0)


def make_attempt(ip: str = "192.0.2.10", seconds: int = 0) -> LoginAttempt:
    return LoginAttempt(
        timestamp=BASE_TIME + timedelta(seconds=seconds),
        ip=ip,
        username="root",
        raw_line="Failed password",
    )


@pytest.mark.parametrize("max_attempts", [0, -1])
def test_engine_rejects_invalid_threshold(max_attempts: int) -> None:
    with pytest.raises(ValueError, match="max_attempts"):
        IncidentResponseEngine(DryRunFirewallBackend(), max_attempts=max_attempts)


@pytest.mark.parametrize("window_seconds", [0, -1])
def test_engine_rejects_invalid_window(window_seconds: int) -> None:
    with pytest.raises(ValueError, match="window_seconds"):
        IncidentResponseEngine(
            DryRunFirewallBackend(),
            window_seconds=window_seconds,
        )


def test_engine_empty_input_returns_empty_list() -> None:
    engine = IncidentResponseEngine(DryRunFirewallBackend())
    assert engine.process_attempts([]) == []


def test_engine_blocks_when_threshold_is_reached() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    decisions = engine.process_attempts(
        [make_attempt(seconds=0), make_attempt(seconds=20), make_attempt(seconds=40)]
    )
    assert len(decisions) == 1
    assert decisions[0].ip == "192.0.2.10"
    assert decisions[0].attempts_count == 3
    assert backend.is_blocked("192.0.2.10") is True


def test_engine_does_not_block_below_threshold() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    assert engine.process_attempts([make_attempt(seconds=0), make_attempt(seconds=20)]) == []
    assert backend.is_blocked("192.0.2.10") is False


def test_engine_counts_attempt_at_exact_window_boundary() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    attempts = [make_attempt(seconds=0), make_attempt(seconds=30), make_attempt(seconds=60)]
    assert len(engine.process_attempts(attempts)) == 1


def test_engine_excludes_attempt_outside_window() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    attempts = [make_attempt(seconds=0), make_attempt(seconds=30), make_attempt(seconds=61)]
    assert engine.process_attempts(attempts) == []


def test_engine_finds_best_window_not_only_first_attempt() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    attempts = [
        make_attempt(seconds=0),
        make_attempt(seconds=100),
        make_attempt(seconds=120),
        make_attempt(seconds=140),
    ]
    decisions = engine.process_attempts(attempts)
    assert len(decisions) == 1
    assert decisions[0].attempts_count == 3


def test_engine_handles_unsorted_attempts() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=3, window_seconds=60)
    attempts = [make_attempt(seconds=40), make_attempt(seconds=0), make_attempt(seconds=20)]
    assert len(engine.process_attempts(attempts)) == 1


def test_engine_groups_different_ips_independently() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=2, window_seconds=60)
    attempts = [
        make_attempt("192.0.2.10", 0),
        make_attempt("198.51.100.20", 5),
        make_attempt("192.0.2.10", 10),
        make_attempt("198.51.100.20", 15),
    ]
    decisions = engine.process_attempts(attempts)
    assert {decision.ip for decision in decisions} == {"192.0.2.10", "198.51.100.20"}


def test_engine_does_not_combine_attempts_from_different_ips() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=2, window_seconds=60)
    attempts = [make_attempt("192.0.2.10", 0), make_attempt("198.51.100.20", 10)]
    assert engine.process_attempts(attempts) == []


def test_engine_skips_whitelisted_ip() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(
        backend,
        max_attempts=2,
        window_seconds=60,
        whitelist={"192.0.2.10"},
    )
    decisions = engine.process_attempts([make_attempt(seconds=0), make_attempt(seconds=10)])
    assert decisions == []
    assert backend.is_blocked("192.0.2.10") is False


def test_engine_copies_whitelist_passed_to_constructor() -> None:
    whitelist = {"192.0.2.10"}
    engine = IncidentResponseEngine(DryRunFirewallBackend(), whitelist=whitelist)
    whitelist.clear()
    assert engine.whitelist == {"192.0.2.10"}


def test_engine_skips_already_blocked_ip() -> None:
    backend = DryRunFirewallBackend()
    backend.block_ip("192.0.2.10")
    engine = IncidentResponseEngine(backend, max_attempts=2, window_seconds=60)
    attempts = [make_attempt(seconds=0), make_attempt(seconds=10)]
    assert engine.process_attempts(attempts) == []


def test_engine_does_not_block_same_ip_twice() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=2, window_seconds=60)
    attempts = [make_attempt(seconds=0), make_attempt(seconds=10)]
    assert len(engine.process_attempts(attempts)) == 1
    assert engine.process_attempts(attempts) == []


def test_engine_calls_backend_through_common_interface() -> None:
    backend = Mock(spec=FirewallBackend)
    backend.is_blocked.return_value = False
    engine = IncidentResponseEngine(backend, max_attempts=2, window_seconds=60)
    engine.process_attempts([make_attempt(seconds=0), make_attempt(seconds=10)])
    backend.is_blocked.assert_called_once_with("192.0.2.10")
    backend.block_ip.assert_called_once_with("192.0.2.10")


def test_engine_decision_reason_contains_count_and_window() -> None:
    engine = IncidentResponseEngine(DryRunFirewallBackend(), max_attempts=2, window_seconds=60)
    decision = engine.process_attempts([make_attempt(seconds=0), make_attempt(seconds=10)])[0]
    assert "2 tentativi falliti" in decision.reason
    assert "60 secondi" in decision.reason


def test_engine_supports_ipv6() -> None:
    backend = DryRunFirewallBackend()
    engine = IncidentResponseEngine(backend, max_attempts=2, window_seconds=60)
    decisions = engine.process_attempts(
        [make_attempt("2001:db8::1", 0), make_attempt("2001:db8::1", 10)]
    )
    assert decisions[0].ip == "2001:db8::1"
