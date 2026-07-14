from dataclasses import dataclass
from datetime import datetime
from ipaddress import ip_address


def validate_ip(ip: str) -> str:
    try:
        return str(ip_address(ip))
    except ValueError as error:
        raise ValueError(f"Indirizzo IP non valido: {ip}") from error


@dataclass
class LoginAttempt:

    timestamp: datetime
    ip: str
    username: str | None
    raw_line: str

    def __post_init__(self) -> None:
        self.ip = validate_ip(self.ip)

        if self.username == "":
            self.username = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "ip": self.ip,
            "username": self.username,
            "raw_line": self.raw_line,
        }


@dataclass
class BanDecision:

    ip: str
    attempts_count: int
    window_seconds: int
    reason: str
    created_at: datetime

    def __post_init__(self) -> None:
        self.ip = validate_ip(self.ip)

        if self.attempts_count <= 0:
            raise ValueError("attempts_count deve essere maggiore di zero")

        if self.window_seconds <= 0:
            raise ValueError("window_seconds deve essere maggiore di zero")

    def to_dict(self) -> dict:
        return {
            "ip": self.ip,
            "attempts_count": self.attempts_count,
            "window_seconds": self.window_seconds,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
        }