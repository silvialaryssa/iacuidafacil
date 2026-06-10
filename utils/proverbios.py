from __future__ import annotations

import json
import random
from pathlib import Path


def random_proverb() -> str:
    path = Path(__file__).resolve().parents[1] / "assets" / "proverbios.json"
    proverbios = json.loads(path.read_text(encoding="utf-8"))
    return random.choice(proverbios)
