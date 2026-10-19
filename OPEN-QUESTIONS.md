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

Run on 2026-08-25 across the whole of _Star Ocean_: at every offset in the
cartridge, decode sixty four bytes and ask whether they appear in the expanded
image and appear nowhere in the cartridge. Bytes meeting both conditions were not
copied across by the expansion, so something decompressed them, and this decoder
produced the same ones.

|                                             | Confirmed | Kinds reached |
| :------------------------------------------ | --------: | ------------: |
| Star Ocean against its own expansion        |    55,023 |      16 of 16 |
| Star Ocean against a different game's image |     1,306 |      16 of 16 |

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

**The fourth cartridge, by a trace.** Street Fighter Zero 2 (Japan) has neither
an expansion nor an indexing re-release, and the USA table read against it gives
167 distinct headers across all 16 kinds, so that build holds its streams at
other offsets. Its table comes from a trace instead:
[snes-street-fighter-alpha-2-nochip](https://github.com/gufranco/snes-street-fighter-alpha-2-nochip)
ran the retail cartridge under snes9x and logged every DMA whose A-bus address
is fixed, which is the condition the chip decompresses under.
[`conformance/traced.json`](conformance/traced.json) is the census of the 2,855
streams that table names, and it holds the table to the USA census rather than
trusting it: 2,732 of the 2,855 expand to bytes identical to a stream in the USA
table, and with every start moved one byte on, 0 do. The other 123 match no USA
stream, and nothing here says what they hold. A trace is a floor rather than a
census of the image: a stream the run never asked for is not in it.

**What it still does not cover.** The corpus in
[`conformance/corpus.json`](conformance/corpus.json) and the vectors still rest on
the reference, and they reach shapes and lengths these cartridges do not use.

**What would settle or reopen it.** A capture of a real S-DD1 expanding a known
block. An expansion of a second cartridge would widen the measurement's reach. A
second implementation would not help and is not available: every one that exists
descends from the same research.

### What the chip does with a malformed stream.

**The document says.** Nothing.

**What this project does.** On the cartridge bus, nothing special. `Chip.read`
feeds the decoder through the four bank windows, and a window never runs out, so
a stream that would be truncated in a buffer runs on into whatever the ROM holds
next. Both implementations read their input that way: ares through
`SDD1::mmcRead` at commit `9408cb43d4948fc3ea6e152a307a34348df3fe04`, snes9x
through its memory map at commit `1bcc369e89f08243e0a462882fb1f3e42e51de3a`.
`decompress` over a buffer still refuses with `TruncatedStream` rather than
returning a short answer, which is a decision about a buffer rather than a claim
about the part.

**What is still open.** Whether the silicon does anything a deterministic decoder
does not: stop, flag an error or hold the bus on input an encoder never produces.
Neither implementation has such a path, and both descend from one reverse
engineering.

**What would settle or reopen it.** A capture of the real part fed bytes no
encoder produced.

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

**What this project does.** Clears `$4800` and `$4801`, sets `$4804` to `$4807`
to 0, 1, 2 and 3, and forgets every watched DMA channel. Construction leaves all
of them holding values drawn from a seed and never calls `reset()`.

**Why.** Two implementations agree on the registers: ares in `SDD1::power` and
snes9x in `S9xResetSDD1`. Only ares clears its copy of the channel registers; in
snes9x that copy is the console's own DMA registers, which this chip's reset does
not touch. Neither is a measurement of the part.

**What would settle or reopen it.** A capture of the cartridge bus across a
console reset, reading `$4800` to `$4807` back before any write.

## Where the two witnesses for the registers part

### How the register interface behaves where ares and snes9x disagree.

**The document says.** Nothing.

**What this project follows.** ares, at commit
`9408cb43d4948fc3ea6e152a307a34348df3fe04`. bsnes at commit
`78474e5d39f58872dc21aca18cf9eb583b147fe7` carries the same file with the same
logic, so ares and bsnes are one witness, and snes9x at commit
`1bcc369e89f08243e0a462882fb1f3e42e51de3a` is the second. They part in five
places, each an entry in
[`conformance/divergences.json`](conformance/divergences.json):

- **The bank registers.** ares keeps bits 7 and 0 to 3 and selects a megabyte by
  bits 0 to 3; snes9x keeps bits 0 to 2. No retail cartridge is larger than 8
  megabytes, so none can tell them apart.
- **Which enable gates decompression.** ares requires a channel's bit in both
  `$4800` and `$4801`; snes9x reads `$4801` alone.
- **What `$4802`, `$4803` and `$4808` to `$480f` read.** ares answers with the
  ROM byte at that linear address; snes9x latches `$4802` and `$4803` and leaves
  the rest to open bus.
- **The program window fold.** ares folds banks `$20-3f` onto `$00-1f` when bit 7
  of `$4805` is set, and `$a0-bf` onto `$80-9f` for bit 7 of `$4807`; snes9x has
  no fold.
- **Decompression outside a transfer.** ares decompresses on any read of an armed
  address; snes9x only inside a DMA transfer with a fixed A-bus address.

What a read past the end of the ROM returns is defined by neither; this package
repeats the ROM.

**What would settle or reopen it.** A capture of the cartridge bus while a
console programs each register and runs a transfer.

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

- **The rest of the cartridge's map.** The chip answers the addresses it
  decodes, and anything else on the board, save RAM included, is
  [snes-mapper-python](https://github.com/gufranco/snes-mapper-python).
- **Any cartridge data.** Nothing here is extracted from a retail image.
- **Anything with a clock.** The part answers one access at a time, a byte a
  read, and how long it takes to produce each byte is the timing question above.
