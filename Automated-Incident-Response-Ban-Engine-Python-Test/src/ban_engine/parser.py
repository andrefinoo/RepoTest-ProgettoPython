import re
from datetime import datetime
from pathlib import Path

from src.ban_engine.models import LoginAttempt


class SSHLogParser:

    log_start_pattern = (
        r"^(?:\[\d+\]\s*)?"
        r"(?P<timestamp>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})"
    )

    failed_password_pattern = re.compile(
        log_start_pattern
        + r".*Failed password for (?:(?:invalid user )?(?P<username>\S+) )?"
        + r"from (?P<ip>\S+)"
    )

    failed_publickey_pattern = re.compile(
        log_start_pattern
        + r".*Failed publickey for (?:(?:invalid user )?(?P<username>\S+) )?"
        + r"from (?P<ip>\S+)"
    )

    invalid_user_pattern = re.compile(
        log_start_pattern
        + r".*Invalid user (?P<username>\S+) from (?P<ip>\S+)"
    )

    def parse_line(self, line: str) -> LoginAttempt | None:

        patterns = (
            self.failed_password_pattern,
            self.failed_publickey_pattern,
            self.invalid_user_pattern,
        )

        for pattern in patterns:
            match = pattern.search(line)

            if match:
                return LoginAttempt(
                    timestamp=self._parse_timestamp(match.group("timestamp")),
                    ip=match.group("ip"),
                    username=match.groupdict().get("username"),
                    raw_line=line.strip(),
                )

        return None

    def parse_file(self, path: str | Path) -> list[LoginAttempt]:

        attempts = []

        with Path(path).open("r", encoding="utf-8") as log_file:
            for line in log_file:
                attempt = self.parse_line(line)

                if attempt is not None:
                    attempts.append(attempt)

        return attempts

    def _parse_timestamp(self, timestamp_text: str) -> datetime:

        current_year = datetime.now().year

        try:
            return datetime.strptime(
                f"{timestamp_text} {current_year}",
                "%b %d %H:%M:%S %Y",
            )
        except ValueError:
            return datetime.now()