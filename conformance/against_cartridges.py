import collections
import hashlib
import json
import sys
import zlib
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sdd1 import decompress
from sdd1.errors import TruncatedStream

ROOT = Path(__file__).resolve().parent

PROBE = 64

RECORDED = "cartridges.json"

Decode = Callable[[bytes, int, int], bytes]

Confirmed = list[tuple[int, int, int]]


def expand(rom: bytes, at: int, count: int) -> bytes:
    return bytes(decompress(rom, at, count).data)


def digests_of(image: bytes) -> dict[str, str]:
    return {
        "crc32": f"{zlib.crc32(image):08x}",
        "md5": hashlib.md5(image).hexdigest(),
        "sha1": hashlib.sha1(image).hexdigest(),
        "sha256": hashlib.sha256(image).hexdigest(),
    }


def confirm(cartridge: bytes, expanded: bytes, produced: bytes) -> int | None:
    where = expanded.find(produced)
    if where < 0 or cartridge.find(produced) >= 0:
        return None
    return where


def sweep(
    cartridge: bytes,
    expanded: bytes,
    span: tuple[int, int],
    decode: Decode = expand,
) -> "Confirmed":
    found: Confirmed = []
    for at in range(*span):
        try:
            produced = decode(cartridge, at, PROBE)
        except TruncatedStream:
            continue
        where = confirm(cartridge, expanded, produced)
        if where is not None:
            found.append((at, where, cartridge[at]))
    return found


def census(found: "Sequence[tuple[int, int, int]]", span: tuple[int, int]) -> dict[str, Any]:
    headers: collections.Counter[str] = collections.Counter()
    kinds: collections.Counter[str] = collections.Counter()
    for _at, _where, header in found:
        headers[str(header)] += 1
        kinds[f"{header >> 6}/{(header >> 4) & 3}"] += 1
    return {
        "swept": [hex(span[0]), hex(span[1])],
        "confirmed": len(found),
        "headers": dict(sorted(headers.items(), key=lambda row: int(row[0]))),
        "kinds": dict(sorted(kinds.items())),
    }


def recorded(where: Path | str | None = None) -> dict[str, Any]:
    path = Path(where) if where is not None else ROOT / RECORDED
    if not path.is_file():
        return {}
    found: dict[str, Any] = json.loads(path.read_text())
    return found


def main(
    argv: Sequence[str],
    say: Callable[[str], object] = print,
    decode: Decode = expand,
) -> int:
    if len(argv) < 3:
        say("usage: against_cartridges.py <cartridge> <expanded> <out.json> [lo] [hi]")
        return 2

    cartridge_path, expanded_path, out = Path(argv[0]), Path(argv[1]), Path(argv[2])
    for path in (cartridge_path, expanded_path):
        if not path.is_file():
            say(f"  no such file: {path}")
            return 2

    cartridge = cartridge_path.read_bytes()
    expanded = expanded_path.read_bytes()
    lo = int(argv[3], 0) if len(argv) > 3 else 0
    hi = int(argv[4], 0) if len(argv) > 4 else len(cartridge)

    found = sweep(cartridge, expanded, (lo, hi), decode)
    if not found:
        say(f"  confirmed nothing across {hex(lo)}..{hex(hi)}")
        return 1

    written = census(found, (lo, hi))
    written["measuredFrom"] = [
        {"role": "cartridge", "bytes": len(cartridge), **digests_of(cartridge)},
        {"role": "expanded", "bytes": len(expanded), **digests_of(expanded)},
    ]
    out.write_text(json.dumps(written, indent=2) + "\n")
    say(
        f"  {written['confirmed']} streams confirmed across {hex(lo)}..{hex(hi)},"
        f" {len(written['kinds'])} of 16 kinds, written to {out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
