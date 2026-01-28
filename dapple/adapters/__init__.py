"""Adapters for converting various image sources to Canvas.

Adapters provide a unified interface for creating Canvas objects from
different image libraries and formats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dapple import Canvas


@runtime_checkable
class Adapter(Protocol):
    """Protocol for image source adapters.

    Adapters convert from various image formats/libraries to Canvas.
    """

    def to_canvas(self) -> Canvas:
        """Convert the source to a Canvas.

        Returns:
            New Canvas object.
        """
        ...


# Import adapters for convenient access
from dapple.adapters.numpy import NumpyAdapter, from_array
from dapple.adapters.pil import PILAdapter, from_pil
from dapple.adapters.matplotlib import MatplotlibAdapter, from_matplotlib
from dapple.adapters.cairo import CairoAdapter, from_cairo
from dapple.adapters.ansi import ANSIAdapter, from_ansi

__all__ = [
    "Adapter",
    "NumpyAdapter",
    "from_array",
    "PILAdapter",
    "from_pil",
    "MatplotlibAdapter",
    "from_matplotlib",
    "CairoAdapter",
    "from_cairo",
    "ANSIAdapter",
    "from_ansi",
]
