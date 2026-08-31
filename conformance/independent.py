"""This decoder against streams somebody else's encoder produced.

Every other check on this decoder compares it against a decompressor, and every
decompressor that exists descends from one body of reverse engineering, so
agreement between two of them is one witness counted twice. `OPEN-QUESTIONS.md`
says so outright and says a second implementation would not help.

These pairs ask the other question. They come from an encoder: somebody
modifying the game had to produce streams the real chip would read, and shipped
each compressed stream beside the bytes it was made from. Reproducing what that
encoder emitted is not agreeing with another decoder, and it is the only source
on this machine that asks it.

**What is recorded.** How many pairs, of what lengths, and four digests for both
halves of each. No compressed byte and no decompressed byte, and none is
recoverable from this. The streams are the game's own data in a different
container, and the digests identify them without carrying them.

**What is not corrected.** Two pairs decode sixty four bytes short of what their
own file declares, and every byte they do produce matches. The record says so
and leaves them short. Editing somebody else's file until a check passes is the
failure the whole record exists to prevent.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

OUTCOMES = ("identical", "shortByAuthor", "differs")
"""What one pair can come to.

`shortByAuthor` is kept apart from `differs` because the two mean opposite
things about this decoder. A pair that differs is a disagreement to explain; a
pair that is short produced nothing wrong, only less than its file claimed.
"""

RECORD = Path(__file__).resolve().parent / "independent.json"


def recorded(where: Path | str | None = None) -> dict[str, Any]:
    """The record this carries, read back."""
    path = Path(where) if where is not None else RECORD
    held = json.loads(path.read_text())
    assert isinstance(held, dict), f"{path} does not hold an object"
    return held


def tally(rows: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """How many pairs came to each outcome, counting only the named ones.

    An outcome nobody named is not folded into the nearest one. A record whose
    totals absorb a value the vocabulary does not have would read as complete
    while describing something else.
    """
    found = dict.fromkeys(OUTCOMES, 0)
    for one in rows:
        outcome = str(one.get("outcome"))
        if outcome in found:
            found[outcome] += 1
    return found
