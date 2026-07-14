"""Configurazione pytest: rende importabile il pacchetto in `src/`.

Aggiunge `src/` al percorso di import, così i test possono fare
`from ban_engine.models import ...` senza installare il pacchetto.
"""

import sys
from pathlib import Path


SRC = Path(__file__).resolve().parent.parent / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))