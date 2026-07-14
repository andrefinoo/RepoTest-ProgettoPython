"""Classe base astratta per i backend firewall."""

from abc import ABC, abstractmethod


class FirewallBackend(ABC):
    """Definisce il contratto comune dei backend firewall."""

    @abstractmethod
    def block_ip(self, ip: str) -> None:
        """Blocca un indirizzo IP."""
        ...

    @abstractmethod
    def unblock_ip(self, ip: str) -> None:
        """Rimuove il blocco di un indirizzo IP."""
        ...

    @abstractmethod
    def is_blocked(self, ip: str) -> bool:
        """Controlla se un indirizzo IP è bloccato."""
        ...