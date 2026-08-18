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
import json
import sys
from pathlib import Path

TAG = b"SDD1"

TAG_BYTES = 8
"""The tag, plus the four byte destination address that follows it."""

HEADER_BYTES = 2


def tagged_streams(rom):
    """Where each tagged stream starts, for builds that carry the tag."""
    found = []
    at = rom.find(TAG)
    while at != -1:
        start = at + TAG_BYTES
        if start + HEADER_BYTES <= len(rom):
            found.append(start)
        at = rom.find(TAG, at + 1)
    return sorted(found)


def table(path):
    """A list of offset and length pairs, however the file spells it."""
    with Path(path).open() as handle:
        found = json.load(handle)
    if isinstance(found, dict):
        found = found["streams"]
    return [(int(offset), int(length)) for offset, length in found]


def shapes(rom, streams):
    """A census of the streams, carrying none of what they hold."""
    headers = collections.Counter()
    lengths = collections.Counter()
    combinations = collections.Counter()
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


def main(argv):
    if len(argv) < 2:
        print("usage: extract.py <rom> <shapes out> [stream table]")
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
