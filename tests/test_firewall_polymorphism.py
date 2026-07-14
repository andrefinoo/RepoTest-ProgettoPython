"""Test della gerarchia dei backend firewall."""

import pytest
from unittest.mock import patch

from ban_engine.firewall.linux import LinuxIptablesBackend
from ban_engine.firewall.base import FirewallBackend
from ban_engine.firewall.dry_run import DryRunFirewallBackend
from ban_engine.firewall.windows import WindowsFirewallBackend


def test_firewall_backend_is_abstract() -> None:
    """La classe astratta non può essere istanziata direttamente."""
    with pytest.raises(TypeError):
        FirewallBackend()

def test_dry_run_backend_is_firewall_backend() -> None:
    backend = DryRunFirewallBackend()

    assert isinstance(backend, FirewallBackend)

def test_dry_run_backend_blocks_ip() -> None:
    backend = DryRunFirewallBackend()

    backend.block_ip("192.168.1.10")

    assert backend.is_blocked("192.168.1.10") is True

def test_dry_run_backend_unblocks_ip() -> None:
    backend = DryRunFirewallBackend()
    backend.block_ip("192.168.1.10")

    backend.unblock_ip("192.168.1.10")

    assert backend.is_blocked("192.168.1.10") is False

@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_backend_blocks_ip(mock_run) -> None:
    backend = LinuxIptablesBackend()

    backend.block_ip("192.168.1.10")

    mock_run.assert_called_once_with(
        [
            "iptables",
            "-A",
            "INPUT",
            "-s",
            "192.168.1.10",
            "-j",
            "DROP",
        ],
        check=True,
    )

@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_backend_unblocks_ip(mock_run) -> None:
    backend = LinuxIptablesBackend()

    backend.unblock_ip("192.168.1.10")

    mock_run.assert_called_once_with(
        [
            "iptables",
            "-D",
            "INPUT",
            "-s",
            "192.168.1.10",
            "-j",
            "DROP",
        ],
        check=True,
    )

@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_backend_detects_blocked_ip(mock_run) -> None:
    mock_run.return_value.returncode = 0
    backend = LinuxIptablesBackend()

    result = backend.is_blocked("192.168.1.10")

    assert result is True
    mock_run.assert_called_once_with(
        [
            "iptables",
            "-C",
            "INPUT",
            "-s",
            "192.168.1.10",
            "-j",
            "DROP",
        ],
        check=False,
        capture_output=True,
    )

@patch("ban_engine.firewall.linux.subprocess.run")
def test_linux_backend_detects_unblocked_ip(mock_run) -> None:
    mock_run.return_value.returncode = 1
    backend = LinuxIptablesBackend()

    result = backend.is_blocked("192.168.1.10")

    assert result is False

@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_backend_blocks_ip(mock_run) -> None:
    backend = WindowsFirewallBackend()

    backend.block_ip("192.168.1.10")

    mock_run.assert_called_once_with(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            "name=BanEngine-192.168.1.10",
            "dir=in",
            "action=block",
            "remoteip=192.168.1.10",
        ],
        check=True,
    )

@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_backend_unblocks_ip(mock_run) -> None:
    backend = WindowsFirewallBackend()

    backend.unblock_ip("192.168.1.10")

    mock_run.assert_called_once_with(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "delete",
            "rule",
            "name=BanEngine-192.168.1.10",
        ],
        check=True,
    )

@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_backend_detects_blocked_ip(mock_run) -> None:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Rule Name: BanEngine-192.168.1.10"

    backend = WindowsFirewallBackend()

    assert backend.is_blocked("192.168.1.10") is True

@patch("ban_engine.firewall.windows.subprocess.run")
def test_windows_backend_detects_unblocked_ip(mock_run) -> None:
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = ""

    backend = WindowsFirewallBackend()

    assert backend.is_blocked("192.168.1.10") is False

def apply_block(backend: FirewallBackend, ip: str) -> None:
    """Blocca un IP senza conoscere il tipo concreto del backend."""
    backend.block_ip(ip)

def test_block_ip_is_polymorphic() -> None:
    dry_run = DryRunFirewallBackend()
    linux = LinuxIptablesBackend()
    windows = WindowsFirewallBackend()

    backends: list[FirewallBackend] = [
        dry_run,
        linux,
        windows,
    ]

    with (
        patch.object(linux, "block_ip") as linux_block,
        patch.object(windows, "block_ip") as windows_block,
    ):
        for backend in backends:
            apply_block(backend, "192.168.1.10")

    assert dry_run.is_blocked("192.168.1.10") is True
    linux_block.assert_called_once_with("192.168.1.10")
    windows_block.assert_called_once_with("192.168.1.10")