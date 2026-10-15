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
    with Path(path or DEFAULT_VECTORS).open() as handle:
        loaded: dict[str, Any] = json.load(handle)
    return loaded


def check(blob: bytes, case: Mapping[str, Any]) -> str | None:
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
