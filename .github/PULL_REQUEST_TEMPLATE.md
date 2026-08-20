## What this changes

One or two sentences. What is different afterwards, and why it needed to be.

## How it was checked

Paste the output rather than describing it. A claim that the tests pass is not
evidence that they did.

```text
```

- [ ] `ruff format --check .` and `ruff check .` are clean
- [ ] Every test file runs, and coverage is 100% of statements and branches
- [ ] `python3 -m sdd1.doctor` reports nothing on this machine
- [ ] `conformance/vectors.py` and `conformance/corpus.py` were both run

## If this changes what the part does

The encoder is the authority, and a stream it produced that this cannot decode is
a defect here rather than there. A change to what comes out has to name the
vector, the offset, and what both sides produced.

## What it does not carry

- [ ] No cartridge, no artwork, and no bytes from either
- [ ] Nothing that says where to obtain them
