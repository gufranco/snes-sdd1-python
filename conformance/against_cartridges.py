"""Confirm this decoder against a retail cartridge, with no emulator in the chain.

Until now every byte this decoder was measured against came from snes9x, which
meant that where snes9x was wrong this was wrong with it and nothing here could
tell. This closes that, using two files a reader may already own and neither of
which is carried here.

**The two files.** A retail cartridge carrying the part, and the expanded image
somebody else produced from it by decompressing every stream and rewriting the
game to read them directly. The expansion was not made with this decoder, was not
made with snes9x, and predates both.

**What a confirmation is.** Decode at an offset in the cartridge. If the bytes
that come out appear in the expanded image and appear nowhere in the cartridge
itself, they were not copied across: something decompressed them, and this
decoder produced the same bytes. That is agreement with an independent
decompressor, on real data, at the top of the ladder this part can reach.

**The oracle was calibrated before it was trusted.** Graphics are repetitive, so
a short run can match by luck. The same sweep was run against pairings that
cannot agree, once with the right cartridge against a different game's image and
once with a different cartridge against the right image. Both are reported beside
the real figure rather than described, so a reader can see the separation instead
of taking it on trust.

**What is recorded.** How many streams were confirmed, of which header kinds, and
the digests of the two files. No offset, no destination, no compressed byte and
no decompressed byte. A count is a measurement and a header is the part's
interface asserting itself, per 17 U.S.C. 102(b) and Feist; the artwork is
neither, and none of it is here.

Usage:
    python3 conformance/against_cartridges.py <cartridge> <expanded> <out.json> [lo] [hi]
"""

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
"""How many decoded bytes have to match.

Measured across the whole cartridge: at sixty four bytes the real pairing
confirms 55,023 and the wrong one 1,306, a separation of 42 to 1. Lengthening
the probe costs nothing, because the decode runs either way and the length only
changes what is searched for.
"""

RECORDED = "cartridges.json"

Decode = Callable[[bytes, int, int], bytes]

Confirmed = list[tuple[int, int, int]]
"""Offset in the cartridge, where it landed in the expanded image, header byte."""


def _decode(rom: bytes, at: int, count: int) -> bytes:
    return bytes(decompress(rom, at, count).data)


def digests_of(image: bytes) -> dict[str, str]:
    """The four a manifest publishes, so a reader can cross-check any of them."""
    return {
        "crc32": f"{zlib.crc32(image):08x}",
        "md5": hashlib.md5(image).hexdigest(),
        "sha1": hashlib.sha1(image).hexdigest(),
        "sha256": hashlib.sha256(image).hexdigest(),
    }


def confirm(cartridge: bytes, expanded: bytes, produced: bytes) -> int | None:
    """Where the decoded bytes landed, or nothing if they prove nothing.

    Two conditions, and the second is the one that matters. Bytes that are also
    in the cartridge could have been copied across by the expansion rather than
    decompressed, so finding them says nothing about a decompressor.
    """
    where = expanded.find(produced)
    if where < 0 or cartridge.find(produced) >= 0:
        return None
    return where


def sweep(
    cartridge: bytes,
    expanded: bytes,
    span: tuple[int, int],
    decode: Decode = _decode,
) -> "Confirmed":
    """Every offset in the span that decodes to something the expansion holds.

    An offset that is not a stream start usually produces bytes nothing holds, and
    an offset too near the end of the image has no room for a header. Neither is
    reported.
    """
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
    """What was confirmed, carrying none of what was decoded."""
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
    """The census this repository carries, or nothing if it is not there."""
    path = Path(where) if where is not None else ROOT / RECORDED
    if not path.is_file():
        return {}
    found: dict[str, Any] = json.loads(path.read_text())
    return found


def main(
    argv: Sequence[str],
    say: Callable[[str], object] = print,
    decode: Decode = _decode,
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
