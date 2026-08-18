"""A model of the S-DD1, the decompressor in two SNES cartridges.

    from sdd1 import Sdd1

    chip = Sdd1(model="sdd1")
    chip.decompress(rom, offset, length).data

Its arithmetic coder carries a run length per context rather than a probability,
and every bit belongs to a plane that keeps its own history. The header byte of a
stream decides how many planes there are and which bits of that history select
the context.
"""

from .decoder import (
    BITPLANE_COUNTS,
    HEADER_BYTES,
    MAX_LENGTH,
    Stream,
    TruncatedStream,
    bitplane_count,
    decompress,
)
from .models import MODELS, UnknownModelError, describe
from .probability import CONTEXT_COUNT, CONTEXT_MASKS, EVOLUTION, PLANE_COUNT, RUN_TABLE
from .version import VERSION

__version__ = VERSION

DEFAULT_MODEL = "sdd1"


def Sdd1(model=DEFAULT_MODEL, **options):  # noqa: N802
    """A chip of the named model, sharing one interface across the family."""
    return describe(model).build(**options)


__all__ = [
    "BITPLANE_COUNTS",
    "CONTEXT_COUNT",
    "CONTEXT_MASKS",
    "EVOLUTION",
    "HEADER_BYTES",
    "MAX_LENGTH",
    "MODELS",
    "PLANE_COUNT",
    "RUN_TABLE",
    "Sdd1",
    "Stream",
    "TruncatedStream",
    "UnknownModelError",
    "__version__",
    "bitplane_count",
    "decompress",
    "describe",
]
