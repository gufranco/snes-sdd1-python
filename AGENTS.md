# Working in this repository

This file is for a coding agent. A person reading it will not be harmed, but
[README.md](README.md) is the document written for them.

## What this project is, in one paragraph

A decoder for the S-DD1, the decompressor Nintendo put in Star Ocean and Street
Fighter Alpha 2. It takes a compressed stream and gives back the bytes the chip
would have produced. It does not read cartridges, drive a bus, or model time.

## The authority ladder, and the fact that its top rung is empty

1. **A manufacturer document.** There is none. Neither Ricoh nor Nintendo
   published a datasheet for this part, and nothing suggests one exists.
2. **A retail cartridge**, for anything a stream in one could settle. See the
   warning below: this project is not currently reading any.
3. **The reference decoder in snes9x**, which produced every expected output in
   both conformance files.

**So rung 3 is carrying this entire package**, and that is worth saying out loud
rather than leaving a reader to infer it from the absence of quotes. Every
constant in `conformance/hardware.json` carries `verified: false` for that reason
and not because anybody doubts the value.

## The thing to know before touching the corpus

`conformance/corpus.json` says its census was measured from real S-DD1
cartridges. It was not, and the measurement is in
`conformance/divergences.json`.

`conformance/extract.py` finds a stream by searching for a four byte `SDD1` tag.
Across a library of 7,578 images on 2026-08-21:

| Build | Tags |
|:------|-----:|
| Star Ocean (Japan) | 0 |
| Street Fighter Alpha 2 (USA), (Europe) | 0 |
| Street Fighter Zero 2 (Japan) | 0 |
| Street Fighter Alpha 2 (U) and (E), Virtual Console, sound restored | 2,815 each |

The retail cartridges carry no tag at all, so their streams are not discoverable
by that tool. The two builds that do carry one are modified re-releases, and they
yield 5,630 streams spread evenly across all sixteen shapes. The shipped census
records 11,306, with 2,815 in a single shape. Neither number reproduces, and
2,815 streams sharing one shape is what coincidental byte matches look like.

**What this does and does not affect.** It does not make the decoder wrong: the
census describes which shapes real data uses, not what the decoder does with one,
and the random vectors reach all sixteen regardless. It does mean the claim that
this decoder has been run against the shapes hardware actually drives is
currently unsupported.

**What would fix it.** A stream table for a retail cartridge, found by following
the game's own code rather than by searching for a tag. `extract.py` already
accepts one as its third argument.

## Every gate, in the order to run them

```bash
ruff format --check .                     # formatting
ruff check .                              # lint, zero warnings
mypy                                      # types, strict
pnpm run format:check                     # every JSON file
for f in sdd1/*.test.py conformance/*.test.py; do python3 "$f"; done
python3 -m coverage report                # fails below 100%

python3 conformance/vectors.py            # random streams, all sixteen shapes
python3 conformance/corpus.py             # the shapes census, see the warning above
python3 -m sdd1.doctor                    # what is missing on this machine
```

`conformance/hardware.test.py` is in that loop and needs nothing else on the
machine. It holds every constant to the record of what it is and where it came
from.

## Things that will bite you

**A stream decodes at most one bank.** Sixty four kilobytes, and a length of zero
means exactly that rather than nothing.

**The header is two bytes and selects sixteen shapes**, four bit plane counts by
four context selections. An encoder takes whichever fits, so the shape is the
chip's interface rather than an author's choice, which is why counting shapes
across cartridges is a measurement rather than a survey of taste.

**Nothing here knows about time.** How long the chip takes, and whether a console
reading the output can outrun it, is unmodelled.

## What is deliberately not here

- **No compressed stream from any cartridge.** Decoding one gives the artwork
  back, so a stream is the protected work in a different container. Both corpora
  generate their bodies from a seed.
- **No cartridge, and no digest of one fine enough to rebuild anything.**

## Conventions

| Thing | Rule |
|:------|:-----|
| Language | Python only |
| Comments | None in source. Docstrings carry the reasoning, and say why rather than what |
| Test layout | `<module>.test.py` beside the module it covers |
| Test structure | Arrange, blank line, one act, blank line, assert. No section labels |
| Package manager for tooling | pnpm, never npm |
| Commits | Conventional Commits |
| Only retail dumps as evidence | A hack or a re-release is somebody's edit. It is fine as a subject and it is not evidence about the chip |
