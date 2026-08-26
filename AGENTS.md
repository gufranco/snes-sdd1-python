# Working in this repository

Read [FAMILY.md](FAMILY.md) first. It is the standard every member of this
family carries, byte for byte, and it decides most questions before they are
asked. What follows is only what is true of this member. [README.md](README.md)
is the document written for a person.

## What this project is, in one paragraph

The S-DD1: the arithmetic decompressor that sits between the ROM and the console
in two cartridges. A caller hands it a stream and is handed back what the stream
held. The S-DD1 was a Ricoh part made for Nintendo and neither published a data
sheet, so the top rung of the authority ladder is empty here and what stands in
is a reference decoder, held to 6,652 streams: 4,000 of noise and 2,652 shaped
like a cartridge's.

## The interface a caller drives

The part answers a request. There is no clock, no instruction to step through and
no cycle count to hand back, so none of the family's clocked interface appears
here.

`Chip(model)` builds one. `decompress(data, offset, length)` does the same thing
without naming a part first, for a caller who only wants the bytes.

| Call | What it does |
|:--|:--|
| `decompress(data, offset, length)` | Expand a stream, returning a `Stream` |
| `reset()` | Nothing, because nothing survives a stream. Handed back for chaining |
| `bitplane_count(mode)` | How many planes a header's mode names |

## The authority ladder

1. **A manufacturer document**, of which there is none.
2. **A retail cartridge**, for anything a stream in one can settle.
3. **The reference decoder**, for the output values, which nothing else on this
   machine can produce.

The record names the empty rung rather than promoting the one below it.

## What is settled and what is not

**Not settled: 5 things**, each in
[OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) with the measurement that would close it.
The honest summary is that every output value rests on agreement between two
implementations, which is not a measurement of silicon.

Settled: that the decoder agrees with the reference on 6,652 streams, and that
the state table is actually visited, which is what the noise corpus buys.

## Noise, not artwork

This is the decision the repository turns on. Artwork walks the probability model
along the path a picture happens to take and leaves most of the state table
unvisited, so a run over a thousand tiles can agree perfectly while a whole
branch of the decoder has never executed.

A change to the corpus that makes it more realistic and less random is a change
that weakens it.

## Every gate, in the order to run them

```bash
ruff format --check .
ruff check .
mypy
pnpm run format:check
python3 -m coverage erase
for file in $(find sdd1 conformance -name '*.test.py' | sort); do
  python3 -m coverage run -a "$file"
done
python3 -m coverage report
```

Then the throughput floor, which runs outside the coverage step because a tracer
costs about ten times what the model does:

```bash
python3 -m conformance.speed
```

And the runs that report what they could not check rather than passing quietly:

```bash
python3 sdd1/doctor.py
python3 -m conformance.vectors
python3 -m conformance.corpus
```

Everything under `conformance/` runs as a module. Run as a script, its own
directory goes on the import path and a file there shadows any standard library
module of the same name. `doctor.py` is the exception and runs as a file on
purpose, so that it still runs when the package itself will not import, which is
the case it exists for.

## Conventions that are not negotiable

- Python only, standard library only, no dependencies.
- No comments in source. Reasoning goes in docstrings, and a step that would need
  a comment is a step that should be a named function.
- Tests sit beside the module they cover as `<module>.test.py`. Arrange, blank
  line, one act, blank line, assert, with no section labels.
- 100% statement and branch coverage, enforced. `mypy` at strict, with every
  optional error class on.
- Everything a caller can catch is defined once, in `sdd1/errors.py`, and
  imported from there.
- A check nobody has seen fail is not known to work. Drive every new check
  against input that should fail it before keeping it.

## Layout

```text
sdd1/
  __init__.py     the package, and the part chosen at construction
  decoder.py      reading a header and expanding the stream behind it
  probability.py  the state table and how a context moves through it
  models.py       the catalogue, and the part as a thing you hold
  errors.py       everything this package raises, in one place
  doctor.py       what is actually on this machine, printed for a bug report
  version.py      rewritten by the release job and by nothing else
conformance/
  family.test.py  the family standard, held to this repository
  vectors.json    4,000 noise streams and what the reference makes of them
  corpus.json     2,652 cartridge-shaped streams, same
  extract.py      generating a corpus from the reference
  hardware.json   what this package asserts, and where each assertion comes from
  divergences.json where sources part, and what would settle each
  speed.py        the throughput floor
```

## Things that will bite you

- **A truncated stream raises rather than returning short.** That is a decision
  rather than an observation: nobody knows what the real part does, and a short
  answer that looks like a whole one is the worst of the available guesses.
- **The corpus is the only source for output values.** A change that alters
  output and still passes the unit tests has not been checked at all until both
  corpora run.
- **`reset()` does nothing on purpose.** It exists so a caller driving a board
  does not special-case this part, and the record says outright that it is not a
  claim about the real reset pin.

## Before calling anything finished

Every gate above, green, with output shown. A claim without a run behind it is
not evidence. If a check was skipped because a file is not on this machine, say
which check and why rather than reporting a pass.

## What a change is expected to leave behind

A test that fails without the change and passes with it. An entry in
[OPEN-QUESTIONS.md](OPEN-QUESTIONS.md) if it turned a settled thing into an open
one, or removed one.
