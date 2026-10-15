import collections
import itertools
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

TAG = b"SDD1"

TAG_BYTES = 8

HEADER_BYTES = 2


def tagged_streams(rom: bytes | bytearray) -> list[int]:
    found = []
    at = rom.find(TAG)
    while at != -1:
        start = at + TAG_BYTES
        if start + HEADER_BYTES <= len(rom):
            found.append(start)
        at = rom.find(TAG, at + 1)
    return sorted(found)


def tag_offsets(index: bytes | bytearray) -> list[int]:
    found = []
    at = index.find(TAG)
    while at != -1:
        found.append(at)
        at = index.find(TAG, at + 1)
    return found


def indexed_streams(index: bytes | bytearray) -> list[tuple[int, int]]:
    spots = tag_offsets(index)
    found = []
    for at, following in itertools.pairwise(spots):
        here = int.from_bytes(index[at + 4 : at + TAG_BYTES], "little")
        there = int.from_bytes(index[following + 4 : following + TAG_BYTES], "little")
        if there > here:
            found.append((at, there - here))
    return found


def table(path: Path | str) -> list[tuple[int, int]]:
    body = Path(path).read_bytes()
    if TAG in body:
        return indexed_streams(body)
    found = json.loads(body)
    if isinstance(found, dict):
        found = found["streams"]
    return [(int(offset), int(length)) for offset, length in found]


def shapes(rom: bytes | bytearray, streams: Sequence[tuple[int, int]]) -> dict[str, Any]:
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
