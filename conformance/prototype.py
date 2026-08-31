"""This decoder against a cartridge that predates the compression.

Every other witness this decoder has is downstream of one body of reverse
engineering, or comes from an encoder somebody wrote to modify the game.
`OPEN-QUESTIONS.md` says so, and says a second decompressor would not help,
because two implementations of the same reading agree by construction.

This one is neither. Capcom shipped a prototype of the Japanese cartridge dated
1996-09-15. It declares no coprocessor, and it stores uncompressed a substantial
amount of data the retail cartridge compresses. Where a stream this decoder
expands from retail appears verbatim in that prototype, the bytes are Capcom's
own input to Capcom's own compressor. The decoder has then been shown to invert
the thing itself, rather than to agree with anybody's account of it.

**What is recorded.** Two cartridge identities, four digests each, and per match
the retail offset, the declared length, where it sits in the prototype and a
digest of the expanded bytes. No byte of either image, and none recoverable from
this. A digest per stream is the same granularity the pair record beside this one
uses, and at an average of roughly 1.3 kilobytes per stream it identifies without
reconstructing.

**What a miss means.** Nothing. The prototype is a different build four months
before release, so most of its art and tables differ from the shipped cartridge,
and most of them do. A match is required to be full length: a stream sharing only
its first sixty four bytes is counted as a miss, because a prefix agreement is
what coincidence looks like.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

RECORD = Path(__file__).resolve().parent / "prototype.json"

RUNG = 2
"""Where this evidence sits on the family ladder.

The artifact itself, which is the highest rung any question about this chip has
reached. A prototype cartridge is not a document, so it cannot say what the part
is specified to do. It is evidence about what the data was, which is the question
a decompressor answers.
"""

AMBIGUOUS = "more than once"
"""What is recorded when a match occurs at more than one place in the prototype.

Its content is confirmed either way, and that is what is being measured, so the
location is marked rather than a first hit being written down as though it were
the only one.
"""


def recorded(where: Path | str | None = None) -> dict[str, Any]:
    """The record this carries, read back."""
    path = Path(where) if where is not None else RECORD
    held = json.loads(path.read_text())
    assert isinstance(held, dict), f"{path} does not hold an object"
    return held


def confirmed(rows: Iterable[Mapping[str, Any]]) -> int:
    """How many decompressed bytes the matches account for."""
    return sum(int(one["declaredBytes"]) for one in rows)


def located(rows: Iterable[Mapping[str, Any]]) -> list[str]:
    """The matches whose place in the prototype is known rather than ambiguous."""
    return [str(one["streamAt"]) for one in rows if one["protoAt"] != AMBIGUOUS]
