"""Backend firewall per Linux tramite iptables."""

import subprocess

from .base import FirewallBackend


class LinuxIptablesBackend(FirewallBackend):
    """Gestisce il blocco degli IP usando iptables."""

    def block_ip(self, ip: str) -> None:
        """Aggiunge una regola di blocco per l'indirizzo IP."""
        command = [
            "iptables",
            "-A",
            "INPUT",
            "-s",
            ip,
            "-j",
            "DROP",
        ]

        subprocess.run(command, check=True)

    def unblock_ip(self, ip: str) -> None:
        """Rimuove la regola di blocco per l'indirizzo IP."""
        command = [
            "iptables",
            "-D",
            "INPUT",
            "-s",
            ip,
            "-j",
            "DROP",
        ]

        subprocess.run(command, check=True)

    def is_blocked(self, ip: str) -> bool:
        """Controlla se esiste già una regola di blocco."""
        command = [
            "iptables",
            "-C",
            "INPUT",
            "-s",
            ip,
            "-j",
            "DROP",
        ]

        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
        )

        return result.returncode == 0