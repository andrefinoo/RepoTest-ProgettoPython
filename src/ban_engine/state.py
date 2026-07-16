"""Persistenza dello storico dei ban in JSON."""

import json
from pathlib import Path

from .models import BanDecision


def load_ban_history(path: str | Path) -> list[dict[str, object]]:
    """Carica lo storico esistente; se il file non esiste restituisce una lista vuota."""
    state_path = Path(path)

    if not state_path.exists():
        return []

    try:
        with state_path.open("r", encoding="utf-8") as state_file:
            data = json.load(state_file)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"JSON non valido nel file di stato {state_path}: riga {error.lineno}"
        ) from error

    if not isinstance(data, list):
        raise ValueError("Il file di stato deve contenere una lista")

    return data


def save_ban_decisions(
    path: str | Path,
    decisions: list[BanDecision],
) -> None:
    """Aggiunge le nuove decisioni allo storico senza cancellare quelle precedenti."""
    if not decisions:
        return

    state_path = Path(path)
    history = load_ban_history(state_path)
    history.extend(decision.to_dict() for decision in decisions)

    state_path.parent.mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as state_file:
        json.dump(history, state_file, indent=2, ensure_ascii=False)
