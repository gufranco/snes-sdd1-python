"""Which parts this package covers, and what each one is.

The S-DD1 shipped in two cartridges, Star Ocean and Street Fighter Alpha 2, and
is one part with one behaviour. What differs between the two games is how the
mapper windows banks into the address space, which belongs to the cartridge
rather than to the decompressor, so it is not modelled here.

A model with no evidence behind it does not belong in this table, because then
its fidelity would be a claim rather than a measurement.
"""

from collections.abc import Callable, Sequence
from typing import Any, override

from sdd1.errors import UnknownModelError


class Model:
    """One part: what it is, what it interleaves, and how to build it."""

    __slots__ = ("aliases", "contexts", "core", "name", "planes", "summary")

    def __init__(
        self,
        name: str,
        summary: str,
        planes: int,
        contexts: int,
        core: Callable[..., Any],
        aliases: Sequence[str] = (),
    ) -> None:
        self.name = name
        self.summary = summary
        self.planes = planes
        self.contexts = contexts
        self.core = core
        self.aliases = tuple(aliases)

    def build(self, **options: Any) -> Any:
        return self.core(self, **options)

    @override
    def __repr__(self) -> str:
        return f"<Model {self.name}, up to {self.planes} bit planes>"


class Chip:
    """The chip as a thing you hold, rather than a function you call."""

    __slots__ = ("model",)

    def __init__(self, model: "Model") -> None:
        self.model = model.name

    def decompress(self, rom: bytes | bytearray, offset: int, length: int) -> Any:
        from .decoder import decompress

        return decompress(rom, offset, length)

    def reset(self) -> "Chip":
        """The console's reset line, which this part carries no state across.

        Every stream is decoded from its own header, and nothing survives from
        one call to the next: the probability model is built per stream and
        discarded with it. So this changes nothing, and it exists because a
        caller driving a board resets every part on it and should not have to
        special-case which ones hold state.

        The part is handed back so a caller can build and reset in one
        expression, as the rest of the family does.
        """
        return self


def _build_sdd1(model: "Model", **options: Any) -> Any:
    return Chip(model, **options)


_CATALOGUE = (
    Model(
        name="sdd1",
        summary=(
            "The S-DD1, a decompressor sitting between the ROM and the console in two "
            "cartridges. An arithmetic coder carrying a run length per context rather "
            "than a probability, over up to eight interleaved bit planes."
        ),
        planes=8,
        contexts=32,
        core=_build_sdd1,
        aliases=("s-dd1", "sdd-1", "sdd", "nintendosdd1"),
    ),
)

MODELS = {model.name: model for model in _CATALOGUE}

_BY_ALIAS = {}
for _model in _CATALOGUE:
    _BY_ALIAS[_model.name] = _model
    for _alias in _model.aliases:
        _BY_ALIAS[_alias] = _model


def _normalise(name: str) -> str:
    return str(name).strip().lower().replace("-", "").replace("_", "")


def lookup(name: str | None) -> Model:
    """The model of that name, however it happens to be written.

    Naming nothing is refused rather than filled in. A default would be the one
    implicit thing in the call that builds a part, and it is worst where it looks
    most harmless: a caller who learns to leave the model out against a member
    covering one part writes the same call against a member covering sixteen.
    The refusal names every model there is, so somebody who did not know what to
    pass learns it here rather than from the source.

    Not exported from the package. What a caller wants is the part, and the part
    carries its own model; handing back a description of a part nobody built
    reads like a test fixture rather than an interface.
    """
    if name is None:
        raise UnknownModelError(
            "no model was named, and this package will not choose one for you."
            f" Name one of: {', '.join(sorted(MODELS))}"
        )
    found = _BY_ALIAS.get(_normalise(name))
    if found is None:
        raise UnknownModelError(
            f"{name} is not a model this package covers; it has {', '.join(sorted(MODELS))}"
        )
    return found
