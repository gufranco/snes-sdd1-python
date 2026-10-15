from typing import Any

from . import models as models
from .decoder import BITPLANE_COUNTS, HEADER_BYTES, Stream, bitplane_count, decompress
from .errors import TruncatedStream, UnknownModelError
from .models import MODELS, Model
from .probability import CONTEXT_COUNT, CONTEXT_MASKS, EVOLUTION, MAX_LENGTH, PLANE_COUNT, RUN_TABLE
from .version import VERSION

__version__ = VERSION


def Chip(model: str | None = None, **options: Any) -> Any:  # noqa: N802
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
