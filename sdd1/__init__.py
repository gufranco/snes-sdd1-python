"""A model of the S-DD1, the decompressor in two SNES cartridges.

    from sdd1 import Chip

    chip = Chip("sdd1", model="sdd1")
    chip.decompress(rom, offset, length).data

Its arithmetic coder carries a run length per context rather than a probability,
and every bit belongs to a plane that keeps its own history. The header byte of a
stream decides how many planes there are and which bits of that history select
the context.
"""

from typing import Any

from . import models as models
from .decoder import BITPLANE_COUNTS, HEADER_BYTES, Stream, bitplane_count, decompress
from .errors import TruncatedStream, UnknownModelError
from .models import MODELS, Model
from .probability import CONTEXT_COUNT, CONTEXT_MASKS, EVOLUTION, MAX_LENGTH, PLANE_COUNT, RUN_TABLE
from .version import VERSION

__version__ = VERSION


def Chip(model: str | None = None, **options: Any) -> Any:  # noqa: N802
    """A chip of the named model, sharing one interface across the family."""
    return models.lookup(model).build(**options)


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
    "Chip",
    "Model",
    "Stream",
    "TruncatedStream",
    "UnknownModelError",
    "__version__",
    "bitplane_count",
    "decompress",
]
