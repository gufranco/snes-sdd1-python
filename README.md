<div align="center">

<h1>sdd1</h1>

<strong>A model of the SNES S-DD1, checked against the reference decoder on noise rather than on artwork.</strong>

<br>
<br>

[![CI](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml)
[![Vectors](https://img.shields.io/badge/golden%20vectors-4%2C000%20%2F%204%2C000-brightgreen)](#how-this-is-proved)
[![Coverage](https://img.shields.io/badge/coverage-100%25%20statement%20%2B%20branch-brightgreen)](#tests)
[![Python](https://img.shields.io/badge/python-3.12%20%7C%203.13%20%7C%203.14-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

</div>

<p align="center">
  <a href="#quick-start">Quick start</a> &nbsp;|&nbsp;
  <a href="#how-this-is-proved">How this is proved</a> &nbsp;|&nbsp;
  <a href="#how-the-decoder-works">How it works</a> &nbsp;|&nbsp;
  <a href="#regenerating-the-vectors">Regenerating vectors</a> &nbsp;|&nbsp;
  <a href="https://github.com/gufranco/snes-sdd1-python/issues">Issues</a>
</p>

**4,000** golden vectors, **0** failures · **all 16** combinations of plane and context type · **1,121,947** decoded bytes checked · **58** tests · **100%** statement and branch coverage

```python
from sdd1 import decompress

stream = decompress(rom, offset, length)

len(stream.data)
# the expanded bytes, as many as were asked for

stream.bitplanes
# 2, 4 or 8, whichever this stream interleaves
```

---

## The problem

The S-DD1 sits between the ROM and the console and expands graphics on the way past, so the game reads what looks like ordinary data and never knows it was compressed. It shipped in two cartridges, and there is no published per-instruction suite for it.

The obvious substitute is to decode real streams out of a cartridge and check them. That works on your own machine and cannot be shipped: those streams are the game's artwork, so a repository carrying them is distributing the game. Which leaves the usual outcome, a decompressor with no runnable evidence attached to it.

## The solution

Decode noise instead.

The S-DD1 does not know or care whether what it is handed was ever compressed. It walks its state machine over whatever arrives and produces a deterministic result. So a stream of pseudo-random bytes exercises the arithmetic coder, the context modelling and the plane interleaving exactly as real data does, while containing nothing from any cartridge.

The expected outputs come from the S-DD1 decoder in **snes9x 1.63**, not from this implementation, so agreement is a genuine cross-check rather than a restatement of what this code already does. The set ships, runs in CI, and is free to distribute.

It also covers more ground than a cartridge would. A game uses the plane and context types its artist needed; the shipped vectors reach **all sixteen combinations**.

<table>
<tr>
<td width="50%" valign="top">

### Cross-checked, not self-checked

Expected outputs come from snes9x's C decoder. Nothing here grades its own homework.

</td>
<td width="50%" valign="top">

### Ships nothing from a cartridge

The input is pseudo-random bytes with a recorded digest. No game data, so the evidence travels with the code.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### Wider than any game

All 16 plane and context combinations, and 13 output lengths from one byte upward.

</td>
<td width="50%" valign="top">

### Tables checked apart from the walk

The run table is verified to be a permutation of 1 to 128; every state's chain is verified to settle.

</td>
</tr>
</table>

## Quick start

### Prerequisites

| Tool | Version | Install |
|:-----|:--------|:--------|
| Python | >= 3.12 | [python.org](https://www.python.org/downloads/) |

### Setup

```bash
git clone https://github.com/gufranco/snes-sdd1-python.git
cd snes-sdd1-python
```

### Verify

```bash
python3 conformance/vectors.py
#   4000 cases from conformance/vectors.json, against snes9x 1.63
#   4000 agreed, 0 did not
```

## How the decoder works

An arithmetic coder, with one thing that makes it unlike the textbook kind.

**Each context carries a run length, not a probability.** When the decoder consults the stream it gets told how many times the likely symbol repeats, emits it that many times, and only then reads again. The state machine in [`sdd1/probability.py`](sdd1/probability.py) says which code size to use and where to move on each outcome.

**Every bit belongs to a bit plane, and each plane keeps its own history.** That history selects the context, so the same byte of stream decodes differently depending on what came before it *in that plane* and no other.

**The header byte decides the shape.** Its top two bits give the plane type, and the next two select which bits of the history form the context.

| Plane type | Planes interleaved |
|:----------:|:------------------:|
| `0` | 2 |
| `1` | 4 |
| `2` | 4 |
| `3` | 8 |

Types 1 and 2 both use four planes and differ in how they rotate between them as the stream advances, which is why they are separate types rather than one.

## How this is proved

| What | Oracle | Strength |
|:-----|:-------|:---------|
| Whole decoder | 4,000 vectors from snes9x 1.63 over pseudo-random input | Cross-checked against an independent implementation |
| Coverage of shapes | All 16 plane and context combinations | Exhaustive over the header space |
| Run table | Verified to be a permutation of 1 to 128 | Structural, exhaustive |
| State machine | Every state's chain verified to settle under both outcomes | Structural, exhaustive |
| Context masks | Verified disjoint and inside the 32 contexts that exist | Structural, exhaustive |
| Prefix property | A short read is a prefix of a longer read at the same offset | Behavioural |

> [!NOTE]
> The vectors say what this decoder does on inputs no cartridge produces. That is the point, not a limitation: a game exercises the paths its artwork happened to need, and noise exercises the rest. If you want the cartridge check as well, run it locally against a ROM you own; it just cannot ship.

### Regenerating the vectors

The set was produced by feeding pseudo-random bytes to the S-DD1 decoder inside snes9x 1.63 and recording the digest of each output. [`conformance/vectors.json`](conformance/vectors.json) records the seed, the input, and its SHA-256, so the input is reproducible and the outputs are attributable.

Regenerating needs a build of the reference decoder, which is not a dependency of this package and is not required to run the checks. The shipped set is what CI runs.

## Models

```python
from sdd1 import Sdd1, describe

describe("s-dd1").planes
# 8

chip = Sdd1(model="sdd1")
chip.decompress(rom, offset, length).data
```

| Model | Planes | Contexts | Notes |
|:------|:------:|:--------:|:------|
| `sdd1` | 8 | 32 | Aliases: `s-dd1`, `sdd-1`, `sdd`, `nintendosdd1` |

> [!NOTE]
> The S-DD1 shipped in two cartridges and is one part with one behaviour. What differs between them is how the mapper windows banks into the address space, which belongs to the cartridge rather than to the decompressor and is not modelled here.

## Project structure

```
sdd1/
  __init__.py       the package, and the model chosen at construction
  decoder.py        the arithmetic decoder and the plane interleaving
  probability.py    the state machine, the run table, the context masks
  models.py         what each part is
  version.py        rewritten by the release job and by nothing else
conformance/
  vectors.py        runs the golden vectors and reports what disagreed
  vectors.json      4,000 cases over pseudo random input, from snes9x 1.63
```

Each module has its tests beside it as `<module>.test.py`, so a module and the cases that pin its behaviour are read together.

## Tests

```bash
for f in sdd1/*.test.py conformance/*.test.py; do python3 "$f"; done
```

| Suite | File | Covers |
|:------|:-----|:-------|
| Decoder | [`sdd1/decoder.test.py`](sdd1/decoder.test.py) | Header parsing, every plane and context type, lengths, truncation, the prefix property |
| Tables | [`sdd1/probability.test.py`](sdd1/probability.test.py) | The run table as a permutation, the state machine settling, mask disjointness |
| Models | [`sdd1/models.test.py`](sdd1/models.test.py) | The catalogue, alias matching, construction |
| Vectors | [`conformance/vectors.test.py`](conformance/vectors.test.py) | The whole shipped set, digest integrity, header coverage, reporting |

Coverage is enforced at 100% of statements and branches by [`pyproject.toml`](pyproject.toml), so a new branch without a test fails the build rather than quietly lowering the number.

## Development

| Command | Description |
|:--------|:------------|
| `ruff format .` | Format |
| `ruff check .` | Lint |
| `python3 -m coverage run -a <file>` | Run one test file under coverage |
| `python3 -m coverage report` | Coverage, which fails below 100% |
| `python3 conformance/vectors.py [file]` | Run the golden vectors |

## Project conventions

| Convention | Source |
|:-----------|:-------|
| Commit format | [Conventional Commits](https://www.conventionalcommits.org/) |
| Releases | [semantic-release](https://semantic-release.gitbook.io/), driven by [`.releaserc.json`](.releaserc.json) |
| Lint and format | [Ruff](https://docs.astral.sh/ruff/), configured in [`pyproject.toml`](pyproject.toml) |
| Test layout | `<module>.test.py` beside the module it covers |

## Versioning

This project follows [Semantic Versioning](https://semver.org/), and every release is tagged from `main` by semantic-release. See [releases](https://github.com/gufranco/snes-sdd1-python/releases).

> [!IMPORTANT]
> While the version is below `1.0.0`, the public interface may change on a minor release. Pin an exact version if that matters to you.

## FAQ

<details>
<summary><strong>Does decoding random bytes actually prove anything?</strong></summary>
<br>

It proves this decoder and snes9x's agree on 4,000 inputs covering every shape the header can describe. The decoder has no way to tell noise from a real stream, so the paths taken are the same paths; what differs is only which of them get taken and how often. Noise spreads the coverage wider than one game's artwork does.

</details>

<details>
<summary><strong>Why not include a compressor and test by round trip?</strong></summary>
<br>

Because a round trip only proves the pair is self-consistent. If the compressor and decompressor share a misunderstanding, every round trip passes and every real cartridge fails. Checking against an independent implementation catches exactly that, which is why the vectors come from snes9x rather than from anything here.

</details>

<details>
<summary><strong>Can I check it against a real cartridge?</strong></summary>
<br>

Yes, on your own machine, against a ROM you own. That check cannot live in this repository because the streams it would carry are the game's graphics.

</details>

<details>
<summary><strong>Does this handle the memory mapping the two games use?</strong></summary>
<br>

No, and deliberately. The S-DD1 cartridges window banks into the address space, which is the mapper's job rather than the decompressor's. Mixing them would make each harder to test on its own.

</details>

## License

[MIT](LICENSE)
