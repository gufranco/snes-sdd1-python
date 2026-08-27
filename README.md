# S-DD1

A model of the SNES S-DD1, checked against the reference decoder on noise rather than on artwork.

[![CI](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml/badge.svg)](https://github.com/gufranco/snes-sdd1-python/actions/workflows/ci.yml)

**4,000** synthetic vectors + **2,652** cartridge-shaped cases, **0** failures, **all 16** plane and context combinations, shapes from **11,306** real streams, lengths to **65,536**, **410** tests, **100%** statement and branch coverage, no dependencies

```python
from sdd1 import decompress

compressed = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

stream = decompress(compressed, 0, 4)

len(stream.data)

# 4
```


## Install
```bash
pip install git+https://github.com/gufranco/snes-sdd1-python.git
```

Python 3.12 or newer. Nothing else.

## The interface
Everything a caller touches. Nothing else is public.

| Name | What it is |
|:--|:--|
| `Chip(model)` | A part of that model |
| `decompress(data, offset, length)` | The same, without naming a part first |
| `Stream` | What came out: the bytes, where the input ended, and how many planes it interleaves |
| `MODELS` | Every model this package covers, by the name it goes by |
| `bitplane_count(mode)` | How many planes a header's mode names |
| `EVOLUTION`, `RUN_TABLE`, `CONTEXT_MASKS`, `CONTEXT_COUNT` | The tables the decoder works from |
| `BITPLANE_COUNTS`, `PLANE_COUNT`, `HEADER_BYTES`, `MAX_LENGTH` | The shapes a stream can have |
| `UnknownModelError`, `TruncatedStream` | Everything a caller can catch |

`Chip` takes the model first, which is the argument every member of the family
takes first, and the name is the kind rather than the chip.

```python
from sdd1 import MODELS, Chip

chip = Chip("s-dd1")

MODELS[chip.model].planes

# 8
```

There is no default. Naming none raises and lists every model there is, which on
a package covering one part is the point rather than the exception: a caller who
learns to leave it out here writes the same call against a member covering
sixteen.

A name no part answers to is refused rather than quietly building the only one
there is:

```python
from sdd1 import Chip, UnknownModelError

try:
    Chip("s-dd2")
except UnknownModelError as refused:
    print(str(refused).split(";")[0])

# s-dd2 is not a part this package covers
```

A stream that ends before it produced what its header promised is refused rather
than handed back short:

```python
from sdd1 import TruncatedStream, decompress

try:
    decompress(bytes(2), 0, 64)
except TruncatedStream as refused:
    print(type(refused).__name__)

# TruncatedStream
```

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

## Models
```python
from sdd1 import Chip

compressed = bytes([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

Chip("sdd1").decompress(compressed, 0, 4).data

# bytearray(b'\x00\x00\x00\x00')
```

| Model | Planes | Contexts | Notes |
|:------|:------:|:--------:|:------|
| `sdd1` | 8 | 32 | Aliases: `s-dd1`, `sdd-1`, `sdd`, `nintendosdd1` |

> [!NOTE]
> The S-DD1 shipped in two cartridges and is one part with one behaviour. What differs between them is how the mapper windows banks into the address space, which belongs to the cartridge rather than to the decompressor and is not modelled here.

## Is it right
| What | Oracle | Strength |
|:-----|:-------|:---------|
| Whole decoder | 4,000 vectors from snes9x 1.63 over pseudo-random input | Cross-checked against an independent implementation |
| Coverage of shapes | All 16 plane and context combinations | Exhaustive over the header space |
| Run table | Verified to be a permutation of 1 to 128 | Structural, exhaustive |
| State machine | Every state's chain verified to settle under both outcomes | Structural, exhaustive |
| Context masks | Verified disjoint and inside the 32 contexts that exist | Structural, exhaustive |
| Prefix property | A short read is a prefix of a longer read at the same offset | Behavioural |
| Real cartridge shapes | 2,652 cases over every header byte and length four cartridges use | Cross-checked, shaped by hardware |

> [!NOTE]
> The vectors say what this decoder does on inputs no cartridge produces. That is the point, not a limitation: a game exercises the paths its artwork happened to need, and noise exercises the rest. If you want the cartridge check as well, run it locally against a ROM you own; it just cannot ship.

### The cartridge-shaped corpus, and why it can ship

The random vectors above were built for breadth, and they buy it: all sixteen header shapes. What they do not buy is depth. They stay under two kilobytes, and real cartridges run streams out to a full **65,536** byte block, which drives the decoder far deeper into its state machine.

So there is a second corpus, shaped by real cartridges. Building it means separating a stream into the part that can travel and the part that cannot.

| Part of a stream | What it is | Ships? |
|:-----------------|:-----------|:-------|
| The compressed body | The game's graphics, encoded | Never |
| The header byte | How many planes, which context bits. One of sixteen values the chip defines | Yes |
| The decompressed length | A number | Yes |
| How many streams share a shape | A measurement | Yes |

The header is the chip's interface asserting itself, not an artist's choice: there are exactly sixteen possibilities and the encoder takes whichever fits, the same way a JPEG carries a sampling factor. Functional elements and facts sit outside what copyright reaches, per [17 U.S.C. 102(b)](https://www.law.cornell.edu/uscode/text/17/102) and `Feist`. [`conformance/extract.py`](conformance/extract.py) records exactly those and never writes a compressed byte.

[`conformance/corpus.json`](conformance/corpus.json) is then built in three steps:

1. **Shapes measured from real hardware.** A census of **11,306** streams across four cartridges: **68** distinct header bytes and the lengths the games ask for, covering **14 of the 16** kinds a real game uses.
2. **Bodies generated from a seed.** The compressed bytes filling those shapes are arithmetic, not artwork.
3. **Answers computed by the reference decoder.** Expected outputs come from snes9x's `sdd1emu.cpp`, so agreement is a cross-check rather than a restatement.

```bash
python3 -m conformance.corpus

#   2652 cases from conformance/corpus.json, against snes9x 1.63 sdd1emu.cpp

#   shapes measured from 11306 real streams, 14 of 16 kinds

#   2652 agreed, 0 did not
```

> [!IMPORTANT]
> This is how the repository is built, not legal advice. The rule it follows is simple enough to restate: publish behaviour, never content.

### Measuring a cartridge of your own

```bash
python3 -m conformance.extract "Street Fighter Alpha 2 (USA).sfc" shapes.json streams.json

#   2817 streams from Street Fighter Alpha 2 (USA).sfc

#   47 header shapes, 8 of 16 kinds

#   written to shapes.json
```

Some builds carry an eight byte `SDD1` tag ahead of every stream, and those are found by search alone with no table. Otherwise pass a table of offsets and lengths. Either way the profile that comes out holds no compressed byte, and any corpus you build locally with real bodies stays on your machine.

### Regenerating the vectors

The set was produced by feeding pseudo-random bytes to the S-DD1 decoder inside snes9x 1.63 and recording the digest of each output. [`conformance/vectors.json`](conformance/vectors.json) records the seed, the input, and its SHA-256, so the input is reproducible and the outputs are attributable.

Regenerating needs a build of the reference decoder, which is not a dependency of this package and is not required to run the checks. The shipped set is what CI runs.

**Open questions** are listed with the measurement that would close each one:
[`OPEN-QUESTIONS.md`](OPEN-QUESTIONS.md). Where two sources part, both are kept
in [`conformance/divergences.json`](conformance/divergences.json) with what would
settle it.

## Working on it
```bash
python -m coverage erase
for file in $(find sdd1 conformance -name '*.test.py' | sort); do
  python -m coverage run -a "$file"
done
python -m coverage report
```

`python3 sdd1/doctor.py` says what is actually on this machine. It is run as a file rather than with `-m` so that it still runs when the package itself will not import, which is the case it exists for.

[`AGENTS.md`](AGENTS.md) is the document for an agent working here. [`FAMILY.md`](FAMILY.md) is the standard this repository shares with the rest of the family, kept identical in every member.

### Project structure

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

### Tests

```bash
for f in sdd1/*.test.py conformance/*.test.py; do python3 "$f"; done
```

| Suite | File | Covers |
|:------|:-----|:-------|
| Decoder | [`sdd1/decoder.test.py`](sdd1/decoder.test.py) | Header parsing, every plane and context type, lengths, truncation, the prefix property |
| Tables | [`sdd1/probability.test.py`](sdd1/probability.test.py) | The run table as a permutation, the state machine settling, mask disjointness |
| Models | [`sdd1/models.test.py`](sdd1/models.test.py) | The catalogue, alias matching, construction |
| Vectors | [`conformance/vectors.test.py`](conformance/vectors.test.py) | The whole synthetic set, digest integrity, header coverage, reporting |
| Cartridge corpus | [`conformance/corpus.test.py`](conformance/corpus.test.py) | The whole cartridge-shaped set, image reconstruction, reporting |
| Extraction | [`conformance/extract.test.py`](conformance/extract.test.py) | Tag scanning, stream tables, the census, and that no stream byte is recorded |

Coverage is enforced at 100% of statements and branches by [`pyproject.toml`](pyproject.toml), so a new branch without a test fails the build rather than quietly lowering the number.

### Development

| Command | Description |
|:--------|:------------|
| `ruff format .` | Format |
| `ruff check .` | Lint |
| `python3 -m coverage run -a <file>` | Run one test file under coverage |
| `python3 -m coverage report` | Coverage, which fails below 100% |
| `python3 -m conformance.vectors [file]` | Run the synthetic vectors |
| `python3 -m conformance.corpus [file]` | Run the cartridge-shaped corpus |
| `python3 -m conformance.extract <rom> <out> [table]` | Measure a cartridge you own |

### Project conventions

| Convention | Source |
|:-----------|:-------|
| Commit format | [Conventional Commits](https://www.conventionalcommits.org/) |
| Releases | [semantic-release](https://semantic-release.gitbook.io/), driven by [`.releaserc.json`](.releaserc.json) |
| Lint and format | [Ruff](https://docs.astral.sh/ruff/), configured in [`pyproject.toml`](pyproject.toml) |
| Test layout | `<module>.test.py` beside the module it covers |

### Versioning

This project follows [Semantic Versioning](https://semver.org/), and every release is tagged from `main` by semantic-release. See [releases](https://github.com/gufranco/snes-sdd1-python/releases).

> [!IMPORTANT]
> While the version is below `1.0.0`, the public interface may change on a minor release. Pin an exact version if that matters to you.

### FAQ

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

### When something is wrong

```bash
python3 -m sdd1.doctor
```

It looks at this machine and prints what is actually there, and every line is
something it looked at just now rather than something that ought to be true. A
check that fails says what it saw. A check that itself throws is reported as what
it threw rather than taking the report down with it. Paste all of it into an
issue.

### Contributing

Measurements first. [CONTRIBUTING.md](CONTRIBUTING.md) has the gates a change is
expected to pass, [SECURITY.md](SECURITY.md) says what belongs in a private
report, and the [Code of Conduct](CODE_OF_CONDUCT.md) applies wherever this
project is discussed.

Never attach a copyrighted file, and never link to somewhere one can be
downloaded. A digest identifies a file without carrying it.

## References
This repository carries no documents and no cartridge data. Nintendo published
nothing about this part: the top rung of the authority ladder is empty here and
[`conformance/hardware.json`](conformance/hardware.json) says so rather than
promoting the rung below it.

| Source | Used for |
|:-------|:---------|
| [snes9x](https://github.com/snes9xgit/snes9x) `sdd1emu.cpp` | The reference decoder both corpora were generated from, pinned by commit |
| [`conformance/corpus.json`](conformance/corpus.json) | 2,652 cartridge-shaped cases |
| [`conformance/vectors.json`](conformance/vectors.json) | 4,000 noise cases, which is what visits the state table |

## Citing this
[CITATION.cff](CITATION.cff) is kept in step with the released version by the
same script that stamps the package, so the version it names is the version that
shipped.

## License
[MIT](LICENSE)
