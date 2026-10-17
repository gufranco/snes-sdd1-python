# S-DD1

The S-DD1, the arithmetic decompressor in two Super Nintendo games, in Python, held to the snes9x 1.63 decoder on 6,652 streams and to two retail cartridges with no emulator involved.

English | [日本語](README.ja.md) | [简体中文](README.zh-Hans.md) | [繁體中文（香港）](README.zh-HK.md)

[![CI](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/gufranco/snes-sdd1-python)](https://github.com/gufranco/snes-sdd1-python/releases)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

**4,000** noise streams and **2,652** cartridge-shaped streams compared with snes9x 1.63, **0** failures, **all 16** header shapes, lengths to **65,536** bytes, shapes from a census of **11,306** streams, **603** tests, **100%** statement and branch coverage, no dependencies

```python
import random

import sdd1

noise = random.Random(1996).randbytes(64)
part = sdd1.Chip("sdd1")

for header in (0x00, 0x50, 0xA0, 0xF0):
    stream = part.decompress(bytes([header]) + noise[1:], 0, 8)
    print(f"{header:#04x}", stream.bitplanes, stream.context, stream.end, stream.data.hex())
```

```
0x00 2 0 7 00000100e204f604
0x50 4 1 7 00000100e104bd72
0xa0 4 2 7 00000100e204e008
0xf0 8 3 7 00000040040d4d2d
```

The same 63 bytes of noise follow four different header bytes. The top two bits of the header pick how many bit planes the output interleaves, and the next two pick which bits of each plane's history select a context. Each stream asks for 8 bytes of output, reads 7 bytes of input, and `end` is the offset of the first byte it did not read.

## Install

| Requirement | Version |
|:--|:--|
| Python | 3.12 or newer |
| git | Any |

```bash
git clone https://github.com/gufranco/snes-sdd1-python.git
cd snes-sdd1-python
python3 sdd1/doctor.py
```

The package imports nothing outside the standard library. The doctor runs as a file, so it still prints a report when the package will not import. It checks the machine, builds the part, feeds the decoder an empty stream, and reads both shipped corpora with their SHA-256 digests. Paste its whole output into any bug report. On a healthy checkout it ends with this line and exits 0; a failed check makes it exit 1.

```
  6 checks, nothing to report
```

`pip install .` from the checkout also installs the same report as the `sdd1-doctor` command.

Releases follow [Semantic Versioning](https://semver.org/) and are cut from the commit history by semantic-release. Every release is tagged and listed on the [releases page](https://github.com/gufranco/snes-sdd1-python/releases).

## The interface

`sdd1.Chip(model)` builds one part. `model` is required: leaving it out raises `UnknownModelError` and lists the names there are. A name is matched with case, hyphens and underscores ignored.

| Model | Aliases | Bit planes | Contexts |
|:--|:--|:--|:--|
| `sdd1` | `s-dd1`, `sdd-1`, `sdd`, `nintendosdd1` | Up to 8 | 32 |

```python
import sdd1

for name in ("sdd1", "s-dd1", "sdd-1", "sdd", "nintendosdd1", "S_DD1"):
    print(name, sdd1.Chip(name).model)

for asked in (None, "s-dd2"):
    try:
        sdd1.Chip(asked)
    except sdd1.UnknownModelError as refused:
        print(refused)
```

```
sdd1 sdd1
s-dd1 sdd1
sdd-1 sdd1
sdd sdd1
nintendosdd1 sdd1
S_DD1 sdd1
no model was named, and this package will not choose one for you. Name one of: sdd1
s-dd2 is not a model this package covers; it has sdd1
```

### Calls

| Call | Effect |
|:--|:--|
| `Chip.decompress(rom, offset, length)` | Decodes the stream whose header byte sits at `rom[offset]` and returns a `Stream` of `length` bytes. A `length` of 0 means 65,536 |
| `Chip.reset()` | Does nothing and returns the part. No state survives from one stream to the next, so there is nothing to clear |
| `sdd1.decompress(rom, offset, length)` | The same decode without building a part first |
| `sdd1.bitplane_count(kind)` | The number of bit planes the header's top two bits name: 2, 4, 4 or 8 for kinds 0 to 3 |

`Chip.model` holds the canonical model name. `rom` is any `bytes` or `bytearray`. A stream is read from its two header bytes onward, and nothing before `rom[offset]` is touched.

### What comes back

`Stream` is a named tuple with four fields.

| Field | Meaning |
|:--|:--|
| `data` | The decoded bytes, as `bytes`, exactly `length` of them |
| `end` | The offset of the first input byte the decoder did not read |
| `bitplanes` | 2, 4 or 8, from the header's top two bits |
| `context` | 0 to 3, the header's next two bits, which pick the row of `CONTEXT_MASKS` |

### Errors

| Error | Raised when |
|:--|:--|
| `UnknownModelError` | `Chip` is given no model, or a name no model answers to. The message lists the models there are |
| `TruncatedStream` | `offset` is negative, fewer than 2 bytes remain from `offset` on, or the input runs out before `length` bytes are decoded. The exception carries `offset` |

A short stream raises rather than returning fewer bytes, so a caller never mistakes a partial block for a whole one.

```python
import random

import sdd1

noise = random.Random(1996).randbytes(64)

print(sdd1.decompress(noise, 10, 8))
print(len(sdd1.decompress(bytes(4096), 0, 0).data))

for offset, length in ((-1, 4), (63, 4), (0, 4096)):
    try:
        sdd1.decompress(noise, offset, length)
    except sdd1.TruncatedStream as refused:
        print("TruncatedStream at", refused)
```

```
Stream(data=b'u\xb3\x94\xe8\xff\x9e\x04\xe1', end=19, bitplanes=8, context=3)
65536
TruncatedStream at -1
TruncatedStream at 63
TruncatedStream at 0
```

### Module contents

| Name | Content |
|:--|:--|
| `sdd1.MODELS` | The `Model` records, keyed by canonical name |
| `sdd1.Model` | One record: `name`, `summary`, `planes`, `contexts`, `aliases` |
| `sdd1.BITPLANE_COUNTS` | `(2, 4, 4, 8)`, the plane count for each of the four plane kinds |
| `sdd1.HEADER_BYTES` | 2, the bytes a stream starts with |
| `sdd1.PLANE_COUNT` | 8, the most planes a stream interleaves |
| `sdd1.CONTEXT_COUNT` | 32, the contexts the coder keeps |
| `sdd1.MAX_LENGTH` | 65,536, the most a stream decodes, and what a `length` of 0 asks for |
| `sdd1.EVOLUTION` | The 33-state machine: for each state, the code size and the next state after each outcome |
| `sdd1.RUN_TABLE` | 128 run lengths, a permutation of 1 to 128, indexed by a 7-bit code word |
| `sdd1.CONTEXT_MASKS` | Four pairs of masks over a plane's 10-bit history, one per context kind |
| `sdd1.UnknownModelError`, `sdd1.TruncatedStream` | Everything a caller can catch |
| `sdd1.__version__` | The installed version |

```python
import sdd1

print(sdd1.BITPLANE_COUNTS, [sdd1.bitplane_count(kind) for kind in range(4)])
print(sdd1.HEADER_BYTES, sdd1.PLANE_COUNT, sdd1.CONTEXT_COUNT, sdd1.MAX_LENGTH)
print(len(sdd1.EVOLUTION), sdd1.EVOLUTION[0], sdd1.EVOLUTION[25])
print(len(sdd1.RUN_TABLE), sorted(sdd1.RUN_TABLE) == list(range(1, 129)))
print([(hex(high), hex(low)) for high, low in sdd1.CONTEXT_MASKS])
```

```
(2, 4, 4, 8) [2, 4, 4, 8]
2 8 32 65536
33 (0, 25, 25) (0, 26, 1)
128 True
[('0x1c0', '0x1'), ('0x180', '0x1'), ('0xc0', '0x1'), ('0x180', '0x3')]
```

### Command-line tools

Every tool runs as a module from the repository root, except the doctor, which runs as a file.

| Command | What it does | Exit codes |
|:--|:--|:--|
| `python3 sdd1/doctor.py` | Reports on the machine, the part and both corpora | 0 clean, 1 a check failed |
| `python3 -m conformance.vectors [file]` | Decodes every noise vector and compares digests. `file` defaults to [`conformance/vectors.json`](conformance/vectors.json) | 0 all agree, 1 a disagreement, 2 no file |
| `python3 -m conformance.corpus [file]` | The same for the cartridge-shaped corpus, [`conformance/corpus.json`](conformance/corpus.json) by default | 0 all agree, 1 a disagreement, 2 no file |
| `python3 -m conformance.extract <rom> <shapes out> [table]` | Writes a census of header bytes and lengths from a cartridge you own. `table` is a JSON list of offset and length pairs, or a build carrying `SDD1` tags | 0 written, 1 no stream found, 2 bad arguments or no ROM |
| `python3 -m conformance.against_cartridges <cartridge> <expanded> <out.json> [lo] [hi]` | Sweeps a cartridge between `lo` and `hi` and counts the streams whose first 64 decoded bytes appear in an expanded image and nowhere in the cartridge | 0 written, 1 nothing confirmed, 2 bad arguments or a missing file |
| `python3 -m conformance.speed` | Decodes 2,000 bytes 5 times and compares the median rate with the floor of 70,000 bytes a second | 0 above the floor, 1 below |
| `python3 -m conformance.package <wheel>` | Checks that a built wheel carries every module and no test file | 0 clean, 1 a fault or no wheel, 2 no argument |
| `python3 -m conformance.links` | Requests every address in this file and prints a JSON report | 0 every address still exists, 1 at least one has status 404 or 410 |

```bash
python3 -m conformance.vectors conformance/vectors.json
```

```
  4000 cases from conformance/vectors.json, against snes9x 1.63
  4000 agreed, 0 did not
```

## Noise rather than artwork

A stream out of a cartridge is the game's graphics, compressed. A repository that ships such streams as test data distributes the game, so the evidence for this decoder is built from streams that hold nothing from any cartridge.

The decoder does not know whether its input was ever compressed. It walks its state machine over whatever bytes arrive and produces one deterministic result. [`conformance/vectors.json`](conformance/vectors.json) is 16,384 pseudo-random bytes from seed 1996, recorded with their SHA-256, and 4,000 cases at offsets and lengths inside them. Each case carries the SHA-256 of what snes9x 1.63 decoded there. Those cases reach all 16 header shapes and 13 output lengths, from 1 byte to 2,048.

Artwork walks the probability model along the path one picture takes, so a set of real streams can agree everywhere while part of the state table never runs. A game uses the shapes its artist needed; the noise set covers all 16.

## How the decoder works

Each of the 32 contexts carries a run length rather than a probability. When the decoder reads a code word, it learns how many times the likely symbol repeats, emits it that many times, and only then reads again. `EVOLUTION` says which code size each state reads and where the context moves after each outcome.

Every bit belongs to a bit plane, and each plane keeps its own 10 bits of history. That history, masked by the row of `CONTEXT_MASKS` the header picks, selects the context. The same input byte decodes differently depending on what came before it in that plane.

| Plane kind, header bits 7 and 6 | Planes interleaved | How the planes rotate |
|:--|:--|:--|
| `0` | 2 | They do not |
| `1` | 4 | Every 16 output bytes the pair moves on by 2, wrapping at 8 |
| `2` | 4 | Every 16 output bytes the pair toggles between planes 0 and 1 and planes 2 and 3 |
| `3` | 8 | Each output byte takes one bit from each of the 8 planes |

Kinds 1 and 2 agree until their second rotation, after 32 bytes:

```python
import random

import sdd1

noise = random.Random(1996).randbytes(64)
one = sdd1.decompress(bytes([0x40]) + noise[1:], 0, 48).data
two = sdd1.decompress(bytes([0x80]) + noise[1:], 0, 48).data

print(one[:32] == two[:32], next(at for at in range(48) if one[at] != two[at]))
```

```
True 32
```

## Models

```python
import sdd1

model = sdd1.MODELS["sdd1"]
print(model)
print(model.name, model.planes, model.contexts, model.aliases)

part = sdd1.Chip("sdd1")
print(part.model, part.reset() is part)
```

```
<Model sdd1, up to 8 bit planes>
sdd1 8 32 ('s-dd1', 'sdd-1', 'sdd', 'nintendosdd1')
sdd1 True
```

There is one model. Both games that carry the part use the same decompressor. Their cartridges differ in how they map banks into the address space, which belongs to the cartridge rather than to the decompressor, and that mapping is not modelled here.

## Is it right

Nobody published a data sheet for this part, so the top rung of the authority ladder is empty. [`conformance/hardware.json`](conformance/hardware.json) records that, marks every constant `"verified": false`, and names the evidence that stands in and what would settle each one.

| Witness | Record | Result |
|:--|:--|:--|
| snes9x 1.63 on noise | [`conformance/vectors.json`](conformance/vectors.json) | 4,000 cases, 0 failures |
| snes9x 1.63 on cartridge shapes | [`conformance/corpus.json`](conformance/corpus.json) | 2,652 cases, 0 failures |
| A retail cartridge against an expansion somebody else made of it, with no emulator | [`conformance/cartridges.json`](conformance/cartridges.json) | 55,023 streams confirmed in Star Ocean (Japan) across all 16 shapes, against 1,306 in a control run on a different game |
| A third party's encoder | [`conformance/independent.json`](conformance/independent.json) | 20 pairs: 18 identical, 2 match on every byte the author's export holds and stop 64 bytes short, 0 differ |
| A Capcom prototype from before the compression | [`conformance/prototype.json`](conformance/prototype.json) | 242 of 2,852 decoded streams appear verbatim in it, 311,264 bytes |
| The tables in source | [`conformance/carried.json`](conformance/carried.json) | `EVOLUTION`, `RUN_TABLE` and `CONTEXT_MASKS` pinned by the SHA-256 of their values |

The suite also checks that `RUN_TABLE` is a permutation, that every chain through `EVOLUTION` settles under both outcomes, that no mask pair selects a bit twice, and that a shorter read is a prefix of a longer one at the same offset.

```python
import json
from pathlib import Path

from conformance import vectors


def record(name):
    return json.loads(Path(f"conformance/{name}.json").read_text())


passed, failed, _ = vectors.run(vectors.load())
print("noise", passed, failed)

found = record("cartridges")
print("cartridge", found["confirmed"], len(found["kinds"]), found["control"]["confirmed"])

held = record("independent")
print("encoder", len(held["pairs"]), held["reproduced"], held["shortByAuthor"], held["differs"])

proto = record("prototype")
print("prototype", proto["decoded"], proto["matchedInFull"], proto["bytesConfirmed"])
```

```
noise 4000 0
cartridge 55023 16 1306
encoder 20 18 2 0
prototype 2852 242 311264
```

### The cartridge-shaped corpus

The noise vectors stay at or under 2,048 bytes. [`conformance/corpus.json`](conformance/corpus.json) reaches a whole 65,536-byte block. Its 2,652 cases use 68 distinct header bytes at 39 lengths, placed in a 131,072-byte body generated from seed 20260818, with expected outputs from snes9x 1.63 `sdd1emu.cpp`. The header byte and the length are the part's interface and a measurement. No compressed byte from a cartridge is in the file.

The shapes come from a census of 11,306 streams in 14 of the 16 kinds. The file records no source for that census, and it cannot be reproduced from the four retail cartridges. [`conformance/divergences.json`](conformance/divergences.json) carries that finding and the measurement behind it. The census decides which shapes the corpus exercises, not what the decoder does with any of them, and the noise set reaches all 16 shapes.

```bash
python3 -m conformance.corpus conformance/corpus.json
```

```
  2652 cases from conformance/corpus.json, against snes9x 1.63 sdd1emu.cpp
  shapes measured from 11306 real streams, 14 of 16 kinds
  2652 agreed, 0 did not
```

### Measuring a cartridge of your own

```bash
python3 -m conformance.extract cartridge.sfc shapes.json table.json
python3 -m conformance.against_cartridges cartridge.sfc expanded.sfc found.json
```

`extract` writes header bytes, lengths and counts and never a compressed byte. `against_cartridges` writes counts, header bytes and four digests of each image. Either output can be shared; the images stay on your machine.

### What is still open

[OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) lists each open question with the measurement that would close it. Every output value rests on implementations rather than on a recording off a real part. The behaviour on a malformed stream is a guess. The meaning of the second header byte beyond the shape is unknown. [`conformance/divergences.json`](conformance/divergences.json) holds each place a source is weaker than it looks.

## Working on it

| Need | Where |
|:--|:--|
| Every gate and the order to run them | [CONTRIBUTING.md](CONTRIBUTING.md) |
| The same material for a coding agent | [AGENTS.md](AGENTS.md) |
| The standard this repository shares with the rest of the family | [FAMILY.md](FAMILY.md) |
| Bug reports | [GitHub Issues](https://github.com/gufranco/snes-sdd1-python/issues) |
| Security reports | [SECURITY.md](SECURITY.md) |

```bash
uvx ruff@0.16.3 format --check .
uvx ruff@0.16.3 check .
uvx --python 3.12 mypy==1.14.1
python3 -m coverage erase
for file in $(find sdd1 conformance -name '*.test.py' | sort); do
  python3 -m coverage run -a "$file"
done
python3 -m coverage report
python3 -m conformance.speed
```

Each module has a test file beside it, named after it, and each runs on its own. Coverage is a hard gate at 100% statement and branch. The throughput floor runs outside the coverage step.

Never attach a cartridge image to an issue or link to one. A digest identifies a file without carrying it.

## References

- snes9x 1.63, `sdd1emu.cpp`, https://github.com/snes9xgit/snes9x, the decoder that produced every expected output in [`conformance/vectors.json`](conformance/vectors.json) and [`conformance/corpus.json`](conformance/corpus.json). Facts only; no code is taken.
- No Ricoh or Nintendo document for the S-DD1 is known. [`conformance/hardware.json`](conformance/hardware.json) records the search and lists `documents` as empty.
- Every cartridge, expansion and prototype image the records mention is identified there by size and four digests. None is carried here.

## Citing this

[CITATION.cff](CITATION.cff) is updated with each release by the script that stamps the package version.

## License

MIT. See [LICENSE](LICENSE).
