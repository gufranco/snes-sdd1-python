import ast
import hashlib
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from conformance import extract
from conformance.against_cartridges import digests_of
from sdd1 import decompress

ROOT = Path(__file__).resolve().parent

RECORDED = "traced.json"

TABLE_NAME = "STREAMS"

Table = list[tuple[int, int]]


def _python_table(text: str) -> "Table":
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == TABLE_NAME:
            return [(int(at), int(length)) for at, length in ast.literal_eval(node.value)]
    return []


def table(path: Path | str) -> "Table":
    where = Path(path)
    if where.suffix == ".py":
        return _python_table(where.read_text())
    return [(int(str(at), 0), int(str(length), 0)) for at, length in json.loads(where.read_text())]


def _digest(rom: bytes, at: int, length: int) -> str:
    return hashlib.sha256(decompress(rom, at, length).data).hexdigest()


def agreement(
    traced_image: bytes, traced: "Table", indexed_image: bytes, indexed: "Table"
) -> dict[str, int]:
    known = {_digest(indexed_image, at, length) for at, length in indexed}
    return {
        "identical": sum(_digest(traced_image, at, n) in known for at, n in traced),
        "control": sum(_digest(traced_image, at + 1, n) in known for at, n in traced),
        "streams": len(traced),
    }


def recorded(where: Path | str | None = None) -> dict[str, Any]:
    path = Path(where) if where is not None else ROOT / RECORDED
    held: dict[str, Any] = json.loads(path.read_text())
    return held


def _measured(paths: Sequence[Path]) -> list[dict[str, Any]]:
    roles = ("traced", "indexed", "index")
    return [
        {
            "role": role,
            "name": path.name,
            "bytes": path.stat().st_size,
            **digests_of(path.read_bytes()),
        }
        for role, path in zip(roles, paths, strict=True)
    ]


def main(argv: Sequence[str], say: Callable[[str], object] = print) -> int:
    if len(argv) < 5:
        say("usage: traced.py <traced rom> <table> <indexed rom> <indexing build> <out.json>")
        return 2
    traced_path, table_path, indexed_path, index_path = (Path(one) for one in argv[:4])
    for path in (traced_path, table_path, indexed_path, index_path):
        if not path.is_file():
            say(f"  no such file: {path}")
            return 2
    streams = table(table_path)
    if not streams:
        say("  the table names no stream")
        return 1
    image = traced_path.read_bytes()
    indexed = extract.indexed_streams(index_path.read_bytes())
    written = extract.shapes(image, streams)
    written["agreement"] = agreement(image, streams, indexed_path.read_bytes(), indexed)
    written["measuredFrom"] = _measured((traced_path, indexed_path, index_path))
    Path(argv[4]).write_text(json.dumps(written, indent=2) + "\n")
    found = written["agreement"]
    say(
        f"  {found['streams']} traced streams, {found['identical']} identical to an"
        f" indexed stream, {found['control']} in the control"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
