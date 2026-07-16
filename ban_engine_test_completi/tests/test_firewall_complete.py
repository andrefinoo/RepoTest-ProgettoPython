"""Test completi dei backend firewall, senza comandi reali."""

import subprocess
from unittest.mock import patch

import pytest

from ban_engine.firewall.base import FirewallBackend
from ban_engine.firewall.dry_run import DryRunFirewallBackend
from ban_engine.firewall.linux import LinuxIptablesBackend
from ban_engine.firewall.windows import WindowsFirewallBackend


def test_firewall_backend_is_abstract() -> None:
    with pytest.raises(TypeError):
        FirewallBackend()


@pytest.mark.parametrize(
    "backend",
    [DryRunFirewallBackend(), LinuxIptablesBackend(), WindowsFirewallBackend()],
)
def test_concrete_backends_are_firewall_backends(backend: FirewallBackend) -> None:
    assert isinstance(backend, FirewallBackend)


def test_dry_run_starts_empty() -> None:
    backend = DryRunFirewallBackend()
    assert backend.is_blocked("192.0.2.10") is False


def test_dry_run_blocks_ip(capsys) -> None:
    backend = DryRunFirewallBackend()
    backend.block_ip("192.0.2.10")
    assert backend.is_blocked("192.0.2.10") is True
    assert "[DRY-RUN] Blocco IP: 192.0.2.10" in capsys.readouterr().out


def test_dry_run_duplicate_block_is_idempotent() -> None:
    backend = DryRunFirewallBackend()
    backend.block_ip("192.0.2.10")
    backend.block_ip("192.0.2.10")
    assert backend.is_blocked("192.0.2.10") is True
    assert len(backend.blocked_ips) == 1


def test_dry_run_unblocks_ip(capsys) -> None:
    backend = DryRunFirewallBackend()
    backend.block_ip("192.0.2.10")
    backend.unblock_ip("192.0.2.10")
    assert backend.is_blocked("192.0.2.10") is False
    assert "[DRY-RUN] Sblocco IP: 192.0.2.10" in capsys.readouterr().out


def test_dry_run_unblock_missing_ip_does_not_raise() -> None:
    backend = DryRunFirewallBackend()
    backend.unblock_ip("192.0.2.10")
    assert backend.is_blocked("192.0.2.10") is False


@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_block_command(mock_run) -> None:
    LinuxIptablesBackend().block_ip("192.0.2.10")
    mock_run.assert_called_once_with(
        ["iptables", "-A", "INPUT", "-s", "192.0.2.10", "-j", "DROP"],
        check=True,
    )


@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_unblock_command(mock_run) -> None:
    LinuxIptablesBackend().unblock_ip("192.0.2.10")
    mock_run.assert_called_once_with(
        ["iptables", "-D", "INPUT", "-s", "192.0.2.10", "-j", "DROP"],
        check=True,
    )


@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_is_blocked_true(mock_run) -> None:
    mock_run.return_value.returncode = 0
    assert LinuxIptablesBackend().is_blocked("192.0.2.10") is True
    mock_run.assert_called_once_with(
        ["iptables", "-C", "INPUT", "-s", "192.0.2.10", "-j", "DROP"],
        check=False,
        capture_output=True,
    )


@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_is_blocked_false(mock_run) -> None:
    mock_run.return_value.returncode = 1
    assert LinuxIptablesBackend().is_blocked("192.0.2.10") is False


@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_subprocess_error_is_not_hidden(mock_run) -> None:
    mock_run.side_effect = subprocess.CalledProcessError(1, ["iptables"])
    with pytest.raises(subprocess.CalledProcessError):
        LinuxIptablesBackend().block_ip("192.0.2.10")


@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_block_command(mock_run) -> None:
    WindowsFirewallBackend().block_ip("192.0.2.10")
    mock_run.assert_called_once_with(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            "name=BanEngine-192.0.2.10",
            "dir=in",
            "action=block",
            "remoteip=192.0.2.10",
        ],
        check=True,
    )


@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_unblock_command(mock_run) -> None:
    WindowsFirewallBackend().unblock_ip("192.0.2.10")
    mock_run.assert_called_once_with(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "delete",
            "rule",
            "name=BanEngine-192.0.2.10",
        ],
        check=True,
    )


@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_is_blocked_true(mock_run) -> None:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Rule Name: BanEngine-192.0.2.10"
    assert WindowsFirewallBackend().is_blocked("192.0.2.10") is True
    mock_run.assert_called_once_with(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "show",
            "rule",
            "name=BanEngine-192.0.2.10",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_is_blocked_false_for_missing_rule(mock_run) -> None:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "No rules match"
    assert WindowsFirewallBackend().is_blocked("192.0.2.10") is False


@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_is_blocked_false_for_nonzero_return_code(mock_run) -> None:
    mock_run.return_value.returncode = 1
    mock_run.return_value.stdout = "BanEngine-192.0.2.10"
    assert WindowsFirewallBackend().is_blocked("192.0.2.10") is False


@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_subprocess_error_is_not_hidden(mock_run) -> None:
    mock_run.side_effect = subprocess.CalledProcessError(1, ["netsh"])
    with pytest.raises(subprocess.CalledProcessError):
        WindowsFirewallBackend().block_ip("192.0.2.10")


def apply_block(backend: FirewallBackend, ip: str) -> None:
    backend.block_ip(ip)


def test_block_ip_is_polymorphic() -> None:
    dry_run = DryRunFirewallBackend()
    linux = LinuxIptablesBackend()
    windows = WindowsFirewallBackend()

    with (
        patch.object(linux, "block_ip") as linux_block,
        patch.object(windows, "block_ip") as windows_block,
    ):
        for backend in [dry_run, linux, windows]:
            apply_block(backend, "192.0.2.10")

    assert dry_run.is_blocked("192.0.2.10") is True
    linux_block.assert_called_once_with("192.0.2.10")
    windows_block.assert_called_once_with("192.0.2.10")
