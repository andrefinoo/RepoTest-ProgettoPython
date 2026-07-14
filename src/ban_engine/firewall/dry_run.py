"""Backend firewall in modalità simulazione."""

from .base import FirewallBackend


class DryRunFirewallBackend(FirewallBackend):
    """Simula il blocco degli IP senza modificare il firewall reale."""

    def __init__(self) -> None:
        self.blocked_ips: set[str] = set()

    def block_ip(self, ip: str) -> None:
        """Simula il blocco di un indirizzo IP."""
        self.blocked_ips.add(ip)
        print(f"[DRY-RUN] Blocco IP: {ip}")

    def unblock_ip(self, ip: str) -> None:
        """Simula la rimozione del blocco di un indirizzo IP."""
        self.blocked_ips.discard(ip)
        print(f"[DRY-RUN] Sblocco IP: {ip}")

    def is_blocked(self, ip: str) -> bool:
        """Restituisce True se l'IP risulta bloccato nella simulazione."""
        return ip in self.blocked_ips