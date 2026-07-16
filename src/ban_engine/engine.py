"""Motore che decide quando bloccare un indirizzo IP."""

from datetime import datetime

from .firewall.base import FirewallBackend
from .models import BanDecision, LoginAttempt


class IncidentResponseEngine:
    """Analizza i tentativi falliti e applica le decisioni di ban."""

    def __init__(
        self,
        backend: FirewallBackend,
        max_attempts: int = 3,
        window_seconds: int = 300,
        whitelist: set[str] | None = None,
    ) -> None:
        if max_attempts <= 0:
            raise ValueError("max_attempts deve essere maggiore di zero")
        if window_seconds <= 0:
            raise ValueError("window_seconds deve essere maggiore di zero")

        self.backend = backend
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.whitelist = set(whitelist or set())

    def process_attempts(
        self,
        attempts: list[LoginAttempt],
    ) -> list[BanDecision]:
        """Restituisce le decisioni di ban prodotte dai tentativi ricevuti."""
        grouped_attempts: dict[str, list[LoginAttempt]] = {}

        for attempt in attempts:
            if attempt.ip not in grouped_attempts:
                grouped_attempts[attempt.ip] = []
            grouped_attempts[attempt.ip].append(attempt)

        decisions: list[BanDecision] = []

        for ip, ip_attempts in grouped_attempts.items():
            if ip in self.whitelist:
                continue
            if self.backend.is_blocked(ip):
                continue

            attempts_count = self._count_attempts_in_window(ip_attempts)
            if attempts_count < self.max_attempts:
                continue

            self.backend.block_ip(ip)
            decisions.append(
                BanDecision(
                    ip=ip,
                    attempts_count=attempts_count,
                    window_seconds=self.window_seconds,
                    reason=(
                        f"{attempts_count} tentativi falliti "
                        f"in {self.window_seconds} secondi"
                    ),
                    created_at=datetime.now(),
                )
            )

        return decisions

    def _count_attempts_in_window(
        self,
        attempts: list[LoginAttempt],
    ) -> int:
        """Trova il maggior numero di tentativi dentro una finestra temporale."""
        ordered_attempts = sorted(attempts, key=lambda attempt: attempt.timestamp)
        highest_count = 0

        for start_index, first_attempt in enumerate(ordered_attempts):
            current_count = 0

            for attempt in ordered_attempts[start_index:]:
                elapsed = (attempt.timestamp - first_attempt.timestamp).total_seconds()
                if elapsed > self.window_seconds:
                    break
                current_count += 1

            if current_count > highest_count:
                highest_count = current_count

        return highest_count
