from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

RECORD = Path(__file__).resolve().parent / "prototype.json"

RUNG = 2

AMBIGUOUS = "more than once"


def recorded(where: Path | str | None = None) -> dict[str, Any]:
    path = Path(where) if where is not None else RECORD
    held = json.loads(path.read_text())
    assert isinstance(held, dict), f"{path} does not hold an object"
    return held


def confirmed(rows: Iterable[Mapping[str, Any]]) -> int:
    return sum(int(one["declaredBytes"]) for one in rows)


def located(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    return [str(one["streamAt"]) for one in rows if one["protoAt"] != AMBIGUOUS]
