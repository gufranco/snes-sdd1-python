"""Which parts this package covers, and what each one is.

The S-DD1 shipped in two cartridges, Star Ocean and Street Fighter Alpha 2, and
is one part with one behaviour. What differs between the two games is how the
mapper windows banks into the address space, which belongs to the cartridge
rather than to the decompressor, so it is not modelled here.

A model with no evidence behind it does not belong in this table, because then
its fidelity would be a claim rather than a measurement.
"""


class UnknownModelError(Exception):
    pass


class Model:
    """One part: what it is, what it interleaves, and how to build it."""

    def __init__(self, name, summary, planes, contexts, core, aliases=()):
        self.name = name
        self.summary = summary
        self.planes = planes
        self.contexts = contexts
        self.core = core
        self.aliases = tuple(aliases)

    def build(self, **options):
        return self.core(self, **options)

    def __repr__(self):
        return f"<Model {self.name}, up to {self.planes} bit planes>"


class Decompressor:
    """The chip as a thing you hold, rather than a function you call."""

    def __init__(self, model):
        self.model = model.name

    def decompress(self, rom, offset, length):
        from .decoder import decompress

        return decompress(rom, offset, length)


def _build_sdd1(model, **options):
    return Decompressor(model, **options)


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


def _normalise(name):
    return str(name).strip().lower().replace("-", "").replace("_", "")


def describe(name):
    """The model of that name, however it happens to be written."""
    found = _BY_ALIAS.get(_normalise(name))
    if found is None:
        raise UnknownModelError(
            f"{name} is not a model this package covers; it has {', '.join(sorted(MODELS))}"
        )
    return found
