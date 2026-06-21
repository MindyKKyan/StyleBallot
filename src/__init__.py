"""StyleBallot package — ensure aesthetic_core is importable."""

from __future__ import annotations

import sys
from pathlib import Path

_BASE = Path(__file__).resolve().parent.parent
_PANEL = _BASE.parent / "AestheticDissectionPanel"

if (_BASE / "aesthetic_core").is_dir():
    if str(_BASE) not in sys.path:
        sys.path.insert(0, str(_BASE))
elif _PANEL.is_dir() and str(_PANEL) not in sys.path:
    sys.path.append(str(_PANEL))
