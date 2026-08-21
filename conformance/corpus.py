"""Replay a corpus shaped by real S-DD1 cartridges against this decoder.

The S-DD1 has no published per-instruction suite, and the obvious substitute
cannot ship: decoding real streams means carrying the game's artwork. So the
corpus is split along the line copyright draws, and each half does a different
job.

**What is real here.** Every header byte the cartridges use, and the lengths they
ask for. A header says how many bit planes a stream interleaves and which bits of
each plane's history select its context; there are sixteen possibilities and the
encoder takes whichever fits, so it is the chip's interface rather than an
author's choice. A decompressed length is a number. Both are functional or
factual and sit outside what copyright reaches, per 17 U.S.C. 102(b) and Feist.
`extract.py` measures them from a cartridge you own and records nothing else.

**What is not.** The stream bodies. Those are generated from a seed, so no
compressed byte of any game appears in this repository.

**Where the answers come from.** The reference decoder in snes9x, not this
implementation, so agreement is a cross-check rather than a restatement.

**Why this is worth having on top of the random vectors.** The vectors in
`vectors.json` reach all sixteen header shapes but stay short, because they were
built for breadth. Real cartridges use fourteen of the sixteen and run streams out
to a full sixty four kilobyte block. The length distribution here is the one the
hardware actually drives, which takes the decoder much further into its state
machine than a two kilobyte read ever does.
"""

import hashlib
import json
import random
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sdd1 import decompress

EXAMPLE_LIMIT = 5

DEFAULT_CORPUS = Path(__file__).resolve().parent / "corpus.json"

WHOLE_BLOCK = 0x10000


def load(path: Path | str | None = None) -> dict[str, Any]:
    """The corpus, from where it was asked for or from the one that ships."""
    with Path(path or DEFAULT_CORPUS).open() as handle:
        loaded: dict[str, Any] = json.load(handle)
    return loaded


def body(found: Mapping[str, Any]) -> bytes:
    """The image every case decodes from, rebuilt exactly as it was generated.

    One image, not one per case. A stream reads as far past its own offset as its
    length demands, so a case can run through the ground another case sits on. If
    the image were rebuilt differently here than it was when the expected answers
    were computed, every long case would disagree for a reason that has nothing to
    do with the decoder.
    """
    view = bytearray(random.Random(found["body_seed"]).randbytes(found["body_bytes"]))
    for case in found["cases"]:
        view[case["offset"]] = case["header"]
    return bytes(view)


def check(blob: bytes, case: Mapping[str, Any]) -> str | None:
    """What went wrong with one case, or nothing when it agreed."""
    try:
        produced = decompress(blob, case["offset"], case["length"] % WHOLE_BLOCK).data
    except Exception as error:  # noqa: BLE001
        return f"header {case['header']:#04x} length {case['length']}: {type(error).__name__}"

    digest = hashlib.sha256(produced).hexdigest()
    if digest == case["output_sha256"]:
        return None
    return (
        f"header {case['header']:#04x} length {case['length']}: "
        f"want {case['output_sha256'][:16]} got {digest[:16]}"
    )


def run(found: Mapping[str, Any]) -> tuple[int, int, list[str]]:
    """How many cases agreed, how many did not, and a few that did not."""
    blob = body(found)
    passed = failed = 0
    examples: list[str] = []
    for case in found["cases"]:
        wrong = check(blob, case)
        if wrong is None:
            passed += 1
        else:
            failed += 1
            if len(examples) < EXAMPLE_LIMIT:
                examples.append(wrong)
    return passed, failed, examples


def main(argv: Sequence[str]) -> int:
    path = Path(argv[0]) if argv else DEFAULT_CORPUS
    if not path.is_file():
        print(f"  no corpus at {path}")
        return 2

    found = load(path)
    passed, failed, examples = run(found)
    census = found["census"]
    print(f"  {passed + failed} cases from {path}, against {found['reference']}")
    print(
        f"  shapes measured from {census['streams']} real streams, "
        f"{len(census['combinations'])} of 16 kinds"
    )
    print(f"  {passed} agreed, {failed} did not")
    for line in examples:
        print(f"    {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
