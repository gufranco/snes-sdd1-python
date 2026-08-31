# Open questions

What this project does not know for certain, and what it would take to find out.

The S-DD1 was a Ricoh part made for Nintendo, and neither published a data sheet.
Everything anybody knows about the algorithm was reconstructed from the silicon
or from its output, so the top rung of the authority ladder is empty here and
[`conformance/hardware.json`](conformance/hardware.json) says so rather than
promoting the rung below it.

That makes this member unusual in the family: it is not that some facts are
undocumented, it is that all of them are. What stands in is a reference decoder,
and the thing worth being precise about is what a reference decoder can and
cannot settle.

Every entry is also in
[`conformance/divergences.json`](conformance/divergences.json) with its status
and severity, so a program can read what a person reads here.

## Why the corpus is noise rather than artwork

Artwork walks the probability model along the path a picture happens to take, and
leaves most of the state table unvisited. A run over a thousand tiles can agree
perfectly while an entire branch of the decoder has never executed.

Noise visits it. The 4,000 noise cases are what makes the agreement mean
something, and the 2,652 cartridge-shaped cases are what makes it mean something
about a cartridge.

## What would settle almost all of them

A Ricoh or Nintendo document, which was searched for and not found, or a capture
of a real cartridge's bus while a compressed block is read.

## Where nothing but a second implementation stands behind it

### Every output value the decoder produces.

**The document says.** Nothing. There is no document.

**What this project follows.** A reference decoder, built from a pinned commit
and asked to expand 6,652 streams.

**It is no longer the only thing standing behind the output.** Somebody expanded
one of the four cartridges years ago, decompressing every stream and rewriting
the game to read the results directly. That expansion was neviksti's, it was not
made with this decoder or with the reference, and the game it produced runs on
hardware that has no S-DD1 fitted, so it is a check with no emulator in it and
one that a playable game already validated.

**How independent it actually is, stated exactly.** Not fully, and the reason is
worth reading before the number below is weighed. The reference decoder's own
header says it is "based on code and documentation by Andreas Naive", and quotes
Naive crediting neviksti with "some steps in the right direction" at the start of
that research. The second reference an obvious reader would reach for, bsnes,
says in its own header that the code is Naive's and the port is byuu's, so it is
the same origin again.

Every implementation of this part, this one included, therefore descends from one
body of research. What the measurement below establishes is that this decoder's
transcription of that algorithm reproduces, on real cartridge data, exactly what a
different author's implementation produced. What it cannot establish is that the
algorithm is what the silicon does. Nothing available can, which is why a capture
is still what would settle it.

Run on 2026-08-25 across the whole of *Star Ocean*: at every offset in the
cartridge, decode sixty four bytes and ask whether they appear in the expanded
image and appear nowhere in the cartridge. Bytes meeting both conditions were not
copied across by the expansion, so something decompressed them, and this decoder
produced the same ones.

| | Confirmed | Kinds reached |
|:--|--:|--:|
| Star Ocean against its own expansion | 55,023 | 16 of 16 |
| Star Ocean against a different game's image | 1,306 | 16 of 16 |

The second row is the point of the first. Graphics repeat, so a sixty four byte
run can match by luck, and a figure published without its noise floor is a figure
nobody can weigh. The separation is 42 to 1, and 238 distinct header bytes are
covered. Both rows and the digests of all three files are in
[`conformance/cartridges.json`](conformance/cartridges.json), and
[`conformance/against_cartridges.py`](conformance/against_cartridges.py)
reproduces them from copies you own.

**Two more cartridges, by a different route.** Street Fighter Alpha 2 has no
expansion, so nothing can confirm its streams the way Star Ocean's are confirmed.
It has something else: a re-release that replaces the eight bytes at each stream
start with the literal `SDD1` and a four byte destination. Those destinations run
forward across the whole image, so the gap between two of them is a decompressed
length and the tag's offset is where the stream begins. That is a stream table
for a cartridge that carries no tag of its own, and
[`conformance/indexed.json`](conformance/indexed.json) is the census of the 2,814
streams it names.

Which of the two candidate starts is the real one was decided rather than
assumed. Read at the tag, the header bytes are 52 distinct values across 8 of the
16 kinds with 88 percent in one of them. Read at the byte after, they are all 256
values spread evenly across all 16, which is what reading data that is not a
header looks like. Star Ocean's confirmed streams have the concentrated shape,
not the even one. The USA and Europe cartridges give identical counts from the
same table.

**What it still does not cover.** Street Fighter Zero 2 (Japan), which has
neither an expansion nor an indexing re-release: the same table read against it
gives 167 distinct headers across all 16 kinds, so that build holds its streams
at other offsets. The corpus in [`conformance/corpus.json`](conformance/corpus.json)
and the vectors still rest on the reference, and they reach shapes and lengths
these cartridges do not use.

**What would settle or reopen it.** A capture of a real S-DD1 expanding a known
block. An expansion of a second cartridge would widen the measurement's reach. A
second implementation would not help and is not available: every one that exists
descends from the same research.

### What the chip does with a malformed stream.

**The document says.** Nothing.

**What this project does.** Refuses with `TruncatedStream` rather than returning
what it decoded so far.

**Why.** Every implementation guesses here and none of the guesses can be
checked. Refusing is the guess that cannot silently corrupt a caller: a short
answer that looks like a whole one is the failure this decompressor is easiest to
get wrong in.

**What would settle or reopen it.** A capture of the real part fed a truncated
block.

### What the second header byte means beyond selecting a shape.

**The document says.** Nothing.

**What this project follows.** That it selects how many bit planes the stream
interleaves, which is what every stream in both corpora is consistent with.

**Why.** Consistency across 6,652 streams is evidence that nothing else in the
byte is used by any of them. It is not evidence that nothing else is used.

**What would settle or reopen it.** A stream that varies the rest of the byte,
or a document.

## Where a witness outside the lineage now stands

Everything above concerns one problem: every implementation of this part
descends from one body of research, so two of them agreeing is one witness
counted twice. That objection is now answered for part of the output.

Capcom shipped a prototype of the Japanese cartridge dated 1996-09-15. It
declares no coprocessor and stores uncompressed a large amount of data the retail
cartridge compresses. Decompressing every stream in the Japanese table from the
retail cartridge and searching that prototype for the result finds **242 streams
matching in full, 311,264 bytes**, with no partial match counted.

Those bytes are Capcom's own input to Capcom's own compressor. They were written
before Naive's research existed and owe nothing to it, so for those streams this
decoder has been shown to invert the thing itself rather than to agree with a
reading of it. The record is
[`conformance/prototype.json`](conformance/prototype.json), and the run is
[`conformance/prototype.py`](conformance/prototype.py).

**What it does not settle.** The prototype is a different build four months
before release, so most of its art and tables differ: 2,138 streams are absent
from it and 472 share only a first sixty four bytes, which is counted as absent
rather than as partial agreement. It says nothing about timing, nothing about the
chip's registers, and nothing about the streams it does not carry. The remaining
route to the top of the ladder is unchanged: a recording taken off a real S-DD1.

## Where the question is a scope boundary, not an unknown

### Anything about timing.

**What this project does.** Models how a block expands, and nothing about how
long it takes.

**Why it is not a gap.** How long the chip takes to decode a block, and whether a
console can outrun it, would be a property of the board rather than of the
algorithm, and nothing here measures it.

**What would settle or reopen it.** A bus capture.

### What a reset does.

**The document says.** Nothing.

**What this project does.** Nothing, because there is no state to clear: every
stream is decoded from its own header and the probability model is built per
stream and discarded with it.

**Why.** The reset exists so a caller driving a board does not have to
special-case which parts hold state. It is deliberately not a claim about the
real part's reset pin, and the record says so.

**What would settle or reopen it.** A capture across a console reset mid-stream.

## What is not in question

So the boundary is visible rather than implied:

- **That the decoder agrees with the reference on 6,652 streams.** 4,000 of noise
  and 2,652 cartridge-shaped, no disagreements.
- **That the state table is actually visited.** Which is what the noise corpus
  buys and what an artwork corpus would not.
- **That both corpora can ship.** They are generated streams and their expansions,
  not anybody's cartridge data.

## What is deliberately not modelled

Absent rather than unknown, and absent on purpose:

- **Where a compressed block lives.** That is the memory map, and the map is
  [snes-mapper-python](https://github.com/gufranco/snes-mapper-python).
- **Any cartridge data.** Nothing here is extracted from a retail image.
- **Anything with a clock.** A caller hands it a stream and is handed back what
  the stream held.
