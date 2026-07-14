from datetime import datetime

import pytest

from src.ban_engine.parser import SSHLogParser


def test_parse_failed_password_for_existing_user() -> None:
    parser = SSHLogParser()
    line = (
        "Jul  4 10:15:30 server sshd[1234]: "
        "Failed password for root from 192.168.1.10 port 54321 ssh2"
    )

    attempt = parser.parse_line(line)

    assert attempt is not None
    assert attempt.ip == "192.168.1.10"
    assert attempt.username == "root"
    assert isinstance(attempt.timestamp, datetime)


def test_parse_failed_password_for_invalid_user() -> None:
    parser = SSHLogParser()
    line = (
        "Jul  4 10:16:00 server sshd[1235]: "
        "Failed password for invalid user admin from 10.0.0.5 port 4444 ssh2"
    )

    attempt = parser.parse_line(line)

    assert attempt is not None
    assert attempt.ip == "10.0.0.5"
    assert attempt.username == "admin"


def test_parse_invalid_user_line() -> None:
    parser = SSHLogParser()
    line = (
        "Jul  4 10:17:00 server sshd[1236]: "
        "Invalid user test from 203.0.113.9 port 2222"
    )

    attempt = parser.parse_line(line)

    assert attempt is not None
    assert attempt.ip == "203.0.113.9"
    assert attempt.username == "test"


def test_parse_ignores_unrelated_line() -> None:
    parser = SSHLogParser()
    line = "Jul  4 10:18:00 server sshd[1237]: Accepted password for root"

    attempt = parser.parse_line(line)

    assert attempt is None


def test_parse_line_rejects_invalid_ip() -> None:
    parser = SSHLogParser()
    line = (
        "Jul  4 10:19:00 server sshd[1238]: "
        "Failed password for root from 999.999.999.999 port 1234 ssh2"
    )

    with pytest.raises(ValueError):
        parser.parse_line(line)


def test_parse_file_returns_only_failed_attempts(tmp_path) -> None:
    log_file = tmp_path / "auth.log"
    log_file.write_text(
        "\n".join(
            [
                "Jul  4 10:15:30 server sshd[1234]: Failed password for root from 192.168.1.10 port 54321 ssh2",
                "Jul  4 10:16:00 server sshd[1235]: Accepted password for root from 192.168.1.20 port 1111 ssh2",
                "Jul  4 10:17:00 server sshd[1236]: Invalid user test from 203.0.113.9 port 2222",
            ]
        ),
        encoding="utf-8",
    )

    parser = SSHLogParser()
    attempts = parser.parse_file(log_file)

    assert len(attempts) == 2
    assert attempts[0].ip == "192.168.1.10"
    assert attempts[1].ip == "203.0.113.9"