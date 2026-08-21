"""Check the decoder against golden vectors produced by the reference decoder.

The S-DD1 has no published per-instruction suite, and the obvious substitute,
replaying streams out of a cartridge, cannot be shipped: those streams are the
game's artwork. So the vectors here decode something else entirely.

The input is pseudo random bytes. The S-DD1 decoder does not care whether what it
is handed was ever compressed; it walks its state machine over whatever arrives
and produces a deterministic result. Feeding it noise therefore exercises the
arithmetic coder, the context modelling and the plane interleaving exactly as
real data would, while containing nothing from any cartridge and being free to
distribute.

It also covers more than a cartridge does. The shipped set reaches all sixteen
combinations of bit plane type and context type, which no single game uses.

The expected outputs came from the S-DD1 decoder in snes9x 1.63, not from this
implementation, so agreement is a real cross-check rather than a restatement.
`scripts/regenerate-vectors.md` says how to produce a new set.
"""

import hashlib
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sdd1 import decompress

EXAMPLE_LIMIT = 5

DEFAULT_VECTORS = Path(__file__).resolve().parent / "vectors.json"


def load(path: Path | str | None = None) -> dict[str, Any]:
    """The vector set, from where it was asked for or from the one that ships."""
    with Path(path or DEFAULT_VECTORS).open() as handle:
        loaded: dict[str, Any] = json.load(handle)
    return loaded


def check(blob: bytes, case: Mapping[str, Any]) -> str | None:
    """What went wrong with one case, or nothing when it agreed."""
    try:
        produced = decompress(blob, case["offset"], case["length"]).data
    except Exception as error:  # noqa: BLE001
        return f"offset {case['offset']} length {case['length']}: {type(error).__name__}"

    digest = hashlib.sha256(produced).hexdigest()
    if digest == case["output_sha256"]:
        return None
    return (
        f"offset {case['offset']} length {case['length']}: "
        f"want {case['output_sha256'][:16]} got {digest[:16]}"
    )


def run(found: Mapping[str, Any]) -> tuple[int, int, list[str]]:
    """How many cases agreed, how many did not, and a few that did not."""
    blob = bytes.fromhex(found["input"])
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
    path = Path(argv[0]) if argv else DEFAULT_VECTORS
    if not path.is_file():
        print(f"  no vectors at {path}")
        return 2

    found = load(path)
    passed, failed, examples = run(found)
    print(f"  {passed + failed} cases from {path}, against {found['reference']}")
    print(f"  {passed} agreed, {failed} did not")
    for line in examples:
        print(f"    {line}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
