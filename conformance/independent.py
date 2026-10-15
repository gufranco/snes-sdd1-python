from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

OUTCOMES = ("identical", "shortByAuthor", "differs")

RECORD = Path(__file__).resolve().parent / "independent.json"


def recorded(where: Path | str | None = None) -> dict[str, Any]:
    path = Path(where) if where is not None else RECORD
    held = json.loads(path.read_text())
    assert isinstance(held, dict), f"{path} does not hold an object"
    return held


def tally(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    found = dict.fromkeys(OUTCOMES, 0)
    for one in rows:
        outcome = str(one.get("outcome"))
        if outcome in found:
            found[outcome] += 1
    return found
