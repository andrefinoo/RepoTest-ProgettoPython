"""Test completi del parser SSH."""

from datetime import datetime

import pytest

from ban_engine.parser import SSHLogParser


@pytest.fixture
def parser() -> SSHLogParser:
    return SSHLogParser()


def test_parse_failed_password_existing_user(parser: SSHLogParser) -> None:
    line = (
        "Jul 16 08:00:00 server sshd[1]: "
        "Failed password for root from 192.0.2.10 port 22 ssh2"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.ip == "192.0.2.10"
    assert attempt.username == "root"


def test_parse_failed_password_invalid_user(parser: SSHLogParser) -> None:
    line = (
        "Jul 16 08:00:00 server sshd[1]: "
        "Failed password for invalid user admin from 198.51.100.20 port 22 ssh2"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.username == "admin"
    assert attempt.ip == "198.51.100.20"


def test_parse_failed_publickey_existing_user(parser: SSHLogParser) -> None:
    line = (
        "Jul 16 08:00:00 server sshd[1]: "
        "Failed publickey for root from 192.0.2.10 port 22 ssh2"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.username == "root"


def test_parse_failed_publickey_invalid_user(parser: SSHLogParser) -> None:
    line = (
        "Jul 16 08:00:00 server sshd[1]: "
        "Failed publickey for invalid user guest from 192.0.2.10 port 22 ssh2"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.username == "guest"


def test_parse_invalid_user_line(parser: SSHLogParser) -> None:
    line = "Jul 16 08:00:00 server sshd[1]: Invalid user test from 203.0.113.9 port 22"
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.username == "test"
    assert attempt.ip == "203.0.113.9"


def test_parse_ipv6_address(parser: SSHLogParser) -> None:
    line = (
        "Jul 16 08:00:00 server sshd[1]: "
        "Failed password for root from 2001:0db8:0:0:0:0:0:1 port 22 ssh2"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.ip == "2001:db8::1"


def test_parse_line_with_optional_numeric_prefix(parser: SSHLogParser) -> None:
    line = (
        "[123] Jul 16 08:00:00 server sshd[1]: "
        "Failed password for root from 192.0.2.10 port 22 ssh2"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.ip == "192.0.2.10"


def test_parse_timestamp_uses_current_year(parser: SSHLogParser) -> None:
    line = (
        "Jan 2 03:04:05 server sshd[1]: "
        "Failed password for root from 192.0.2.10 port 22 ssh2"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert attempt.timestamp.year == datetime.now().year
    assert (attempt.timestamp.month, attempt.timestamp.day) == (1, 2)
    assert (attempt.timestamp.hour, attempt.timestamp.minute, attempt.timestamp.second) == (3, 4, 5)


def test_parse_raw_line_is_stripped(parser: SSHLogParser) -> None:
    line = (
        "Jul 16 08:00:00 server sshd[1]: "
        "Failed password for root from 192.0.2.10 port 22 ssh2\n"
    )
    attempt = parser.parse_line(line)
    assert attempt is not None
    assert not attempt.raw_line.endswith("\n")


@pytest.mark.parametrize(
    "line",
    [
        "",
        "testo casuale",
        "Jul 16 08:00:00 server sshd[1]: Accepted password for root from 192.0.2.10",
        "Jul 16 08:00:00 server sshd[1]: Connection closed by 192.0.2.10",
    ],
)
def test_parse_ignores_unrelated_lines(parser: SSHLogParser, line: str) -> None:
    assert parser.parse_line(line) is None


def test_parse_rejects_invalid_ip(parser: SSHLogParser) -> None:
    line = (
        "Jul 16 08:00:00 server sshd[1]: "
        "Failed password for root from 999.999.999.999 port 22 ssh2"
    )
    with pytest.raises(ValueError):
        parser.parse_line(line)


def test_parse_file_returns_only_failed_attempts(tmp_path, parser: SSHLogParser) -> None:
    log_file = tmp_path / "auth.log"
    log_file.write_text(
        "\n".join(
            [
                "Jul 16 08:00:00 server sshd[1]: Failed password for root from 192.0.2.10 port 22 ssh2",
                "Jul 16 08:00:01 server sshd[2]: Accepted password for root from 192.0.2.10 port 22 ssh2",
                "Jul 16 08:00:02 server sshd[3]: Invalid user test from 203.0.113.9 port 22",
            ]
        ),
        encoding="utf-8",
    )
    attempts = parser.parse_file(log_file)
    assert [attempt.ip for attempt in attempts] == ["192.0.2.10", "203.0.113.9"]


def test_parse_file_empty_returns_empty_list(tmp_path, parser: SSHLogParser) -> None:
    log_file = tmp_path / "empty.log"
    log_file.write_text("", encoding="utf-8")
    assert parser.parse_file(log_file) == []


def test_parse_file_missing_raises_file_not_found(tmp_path, parser: SSHLogParser) -> None:
    with pytest.raises(FileNotFoundError):
        parser.parse_file(tmp_path / "missing.log")


def test_parse_file_propagates_invalid_ip_error(tmp_path, parser: SSHLogParser) -> None:
    log_file = tmp_path / "bad.log"
    log_file.write_text(
        "Jul 16 08:00:00 server sshd[1]: Failed password for root from bad-ip port 22 ssh2",
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        parser.parse_file(log_file)
