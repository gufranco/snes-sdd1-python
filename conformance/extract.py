"""Measure the shape of the S-DD1 streams in a cartridge you own.

This is the half of the corpus work that can be published, and the split is
worth being precise about.

**What cannot leave your machine.** The compressed streams are the game's
graphics. Decoding one gives the artwork back, so a stream is the protected work
in a different container, and this tool never writes one out.

**What can.** The header byte of a stream says how many bit planes it interleaves
and which bits of each plane's history select the context. That is the chip's
interface asserting itself rather than an artist's choice: there are exactly
sixteen possibilities and the encoder takes whichever fits, the same way a JPEG
carries a sampling factor. A decompressed length is a number, and a count of how
many streams share a shape is a measurement. Facts and functional elements sit
outside what copyright reaches, per 17 U.S.C. 102(b) and Feist.

So what this produces is a census: how many streams, of which shapes, at which
lengths. It records no compressed byte and cannot be turned back into anything.

**Why the census is worth having.** Random streams reach all sixteen shapes but
stay short. Real cartridges use thirteen of the sixteen and run to a full sixty
four kilobyte block, so their length distribution drives the decoder much further
than noise does. The shipped corpus is built to match what the census found.

**Finding the streams.** Two ways, because cartridges differ. Some builds carry
an eight byte tag ahead of each stream, the literal `SDD1` followed by a little
endian destination address, which makes them findable by search alone. Otherwise
pass a table of offsets and lengths worked out however you like.
"""

import collections
import itertools
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

TAG = b"SDD1"

TAG_BYTES = 8
"""The tag, plus the four byte destination address that follows it."""

HEADER_BYTES = 2


def tagged_streams(rom: bytes | bytearray) -> list[int]:
    """Where each tagged stream starts, for builds that carry the tag."""
    found = []
    at = rom.find(TAG)
    while at != -1:
        start = at + TAG_BYTES
        if start + HEADER_BYTES <= len(rom):
            found.append(start)
        at = rom.find(TAG, at + 1)
    return sorted(found)


def tag_offsets(index: bytes | bytearray) -> list[int]:
    """Where each tag sits in a build that carries an index of them."""
    found = []
    at = index.find(TAG)
    while at != -1:
        found.append(at)
        at = index.find(TAG, at + 1)
    return found


def indexed_streams(index: bytes | bytearray) -> list[tuple[int, int]]:
    """A stream table read out of another author's build of the same game.

    Some re-releases replace the eight bytes at each stream start with the
    literal `SDD1` and a four byte destination. Those destinations run forward
    across the whole image, so the gap between one and the next is the length the
    stream decompresses to, and the tag's own offset is where the stream begins.
    That is an offset and a length per stream, which is what a census needs and
    what searching a retail cartridge for a tag cannot give, because a retail
    cartridge carries no tag.

    **Why the offset is the tag and not the byte after it.** Both are candidates
    and the header bytes decide, calibrated against the one cartridge whose
    streams are confirmed. Star Ocean's 55,023 confirmed streams use 8 of the 16
    kinds heavily and 4 of them under one percent each, which is what an encoder
    taking whichever shape fits looks like. Read at the tag, Street Fighter Alpha
    2 gives 52 distinct header bytes across 8 kinds with 88 percent in one of
    them. Read at the byte after, it gives all 256 byte values spread evenly
    across all 16 kinds, which is what reading random data as a header looks
    like. The USA and Europe builds give identical figures.

    The last tag is dropped, because there is no next destination to subtract
    from and a length nobody can derive is not a measurement.
    """
    spots = tag_offsets(index)
    found = []
    for at, following in itertools.pairwise(spots):
        here = int.from_bytes(index[at + 4 : at + TAG_BYTES], "little")
        there = int.from_bytes(index[following + 4 : following + TAG_BYTES], "little")
        if there > here:
            found.append((at, there - here))
    return found


def table(path: Path | str) -> list[tuple[int, int]]:
    """A stream table, from a list of pairs or from a build that indexes them.

    A file carrying the tag is another author's build of the same game, and the
    table is derived from it. Anything else is read as a list of offset and
    length pairs somebody worked out however they liked.
    """
    body = Path(path).read_bytes()
    if TAG in body:
        return indexed_streams(body)
    found = json.loads(body)
    if isinstance(found, dict):
        found = found["streams"]
    return [(int(offset), int(length)) for offset, length in found]


def shapes(rom: bytes | bytearray, streams: Sequence[tuple[int, int]]) -> dict[str, Any]:
    """A census of the streams, carrying none of what they hold."""
    headers: collections.Counter[int] = collections.Counter()
    lengths: collections.Counter[int] = collections.Counter()
    combinations: collections.Counter[tuple[int, int]] = collections.Counter()
    counted = 0

    for offset, length in streams:
        if offset + HEADER_BYTES > len(rom):
            continue
        header = rom[offset]
        headers[header] += 1
        lengths[length] += 1
        combinations[(header >> 6, (header >> 4) & 3)] += 1
        counted += 1

    return {
        "comment": (
            "A census of the S-DD1 streams in a cartridge: how many, of which header "
            "shapes, at which decompressed lengths. Header bytes and lengths are "
            "interface and measurement. No compressed byte is recorded here."
        ),
        "headers": {str(header): count for header, count in sorted(headers.items())},
        "lengths": {str(length): count for length, count in sorted(lengths.items())},
        "combinations": {
            f"{planes}/{context}": count
            for (planes, context), count in sorted(combinations.items())
        },
        "streams": counted,
    }


def main(argv: Sequence[str]) -> int:
    if len(argv) < 2:
        print("usage: extract.py <rom> <shapes out> [stream table or indexing build]")
        return 2

    rom_path = Path(argv[0])
    if not rom_path.is_file():
        print(f"  no rom at {rom_path}")
        return 2

    rom = rom_path.read_bytes()
    streams = table(argv[2]) if len(argv) > 2 else [(at, 0) for at in tagged_streams(rom)]

    if not streams:
        print(f"  no streams found in {rom_path}; pass a stream table if it carries no tags")
        return 1

    found = shapes(rom, streams)
    Path(argv[1]).write_text(json.dumps(found, indent=2) + "\n")

    print(f"  {found['streams']} streams from {rom_path}")
    print(f"  {len(found['headers'])} header shapes, {len(found['combinations'])} of 16 kinds")
    print(f"  written to {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
