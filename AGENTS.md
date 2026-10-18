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
uvx --python 3.12 --with types-setuptools==84.0.0.20260812 mypy==1.14.1
pnpm run format:check
uvx yamllint==1.38.0 --strict .
cov=(uvx --python 3.12 --from coverage==7.6.10 --with setuptools==84.0.0 coverage)
"${cov[@]}" erase
for file in $(find sdd1 conformance -name '*.test.py' | sort); do
  "${cov[@]}" run -a "$file"
done
"${cov[@]}" report
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
- No comments in source, and a docstring counts as one. A step that would need
  a comment is a step that should be a named function.
- Tests sit beside the module they cover as `<module>.test.py`. Arrange, act
  and assert, each block opened by its bare marker.
- 100% statement and branch coverage, enforced. `mypy` at strict, with every
  optional error class on.
- Everything a caller can catch is defined once, in `sdd1/errors.py`, and
  imported from there.
- A check nobody has seen fail is not known to work. Drive every new check
  against input that should fail it before keeping it.

The linter's ignores in [`pyproject.toml`](pyproject.toml) carry no comments, so
their reasons live here, beside those of the coverage exclusions:

- `N818`: the control flow signals are named the way CPython names its own,
  like `StopIteration`. The exceptions that report a failure do end in `Error`.
- `N999` in tests: a test file is named after the module it covers, with a dot,
  so a module and its tests are read together.
- `T201` in `conformance/`: these are command line tools and printing is their
  output. A logger would put a level and a timestamp in front of a report meant
  for a person.
- `BLE001` and `T201` in the doctor: it must survive whatever a check throws and
  report it, because a narrower catch would let a traceback take the rest of the
  report with it.
- `BLE001` and `T201` in `environment.py`: it reports what a machine is, so a
  check that throws becomes a line in the report rather than ending the run.
- Every optional `mypy` error class is on because the errors that matter in a
  model of hardware are a width, a mask or a `None` crossing a boundary.
- The `__main__` guard is excluded from coverage: it hands argv to a tested
  function, and importing the module to cover it would run the tool.
- The doctor's `sys.path` guard is excluded: a suite that imports the doctor has
  already put the repository on the path, so no test can take that branch.
- `if TYPE_CHECKING:` is excluded: it never runs, and Python 3.14 drops it before
  coverage sees it while earlier versions do not.
- A lone ellipsis and a signature ending in one are excluded: a protocol method
  has no body to run, and the same version split applies.
- `@unittest\.skipUnless\(CLOCKED,` in the coverage exclusions: this member is
  not a clocked part, so the family tests that drive a clock are skipped here
  and their bodies never run.
- `@unittest\.skipUnless\(QUOTED,` in the coverage exclusions: this record
  quotes no document, so the family tests that hold a quote checker to the
  pipeline are skipped here.
- `@unittest\.skipUnless\(SOLD_AS_A_COMPONENT,`, `^def machine_mentions\(` and
  `^def listing\(` in the coverage exclusions: this part only existed inside one
  machine, so the family sweep for machine names is skipped here.

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
  family_*.test.py the family standard, held to this repository, one topic a file
  family_member.py what this member answers to them
  family_shared.py what more than one of them reads
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
