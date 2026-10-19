from collections.abc import Callable, Sequence
from typing import Any, override

from sdd1.errors import UnknownModelError

from .chip import Chip


class Model:
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


def _build_sdd1(model: "Model", **options: Any) -> Any:
    return Chip(model.name, **options)


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
