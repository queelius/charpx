"""Adapters for converting various image sources to braille.

This module provides adapters for converting graphics library objects
(matplotlib figures, PIL images, Cairo surfaces, etc.) to grayscale
bitmaps that pixdot can render to braille.

Core exports (always available):
    - BitmapAdapter: Base class for all adapters
    - NumpyAdapter: Adapter for direct numpy array input

Optional adapters (require additional packages):
    - PILAdapter: For PIL/Pillow images (pip install pixdot[pil])
    - MatplotlibAdapter: For matplotlib figures (pip install pixdot[matplotlib])
    - CairoAdapter: For Cairo surfaces (pip install pixdot[cairo])

Example:
    >>> from pixdot.adapters import NumpyAdapter
    >>> import numpy as np
    >>>
    >>> bitmap = np.random.rand(100, 100).astype(np.float32)
    >>> print(NumpyAdapter().render(bitmap, "dark_terminal"))

    >>> from pixdot.adapters import PILAdapter
    >>> from PIL import Image
    >>>
    >>> image = Image.open("photo.jpg")
    >>> print(PILAdapter().render(image, "high_detail"))
"""

from __future__ import annotations

from .base import BitmapAdapter
from .numpy_adapter import NumpyAdapter, array_to_braille


def __getattr__(name: str):
    """Lazy import for optional adapters."""
    if name == "PILAdapter":
        from .pil import PILAdapter

        return PILAdapter
    elif name == "MatplotlibAdapter":
        from .matplotlib import MatplotlibAdapter

        return MatplotlibAdapter
    elif name == "CairoAdapter":
        from .cairo import CairoAdapter

        return CairoAdapter
    elif name == "image_to_braille":
        from .pil import image_to_braille

        return image_to_braille
    elif name == "load_and_render":
        from .pil import load_and_render

        return load_and_render
    elif name == "figure_to_braille":
        from .matplotlib import figure_to_braille

        return figure_to_braille
    elif name == "surface_to_braille":
        from .cairo import surface_to_braille

        return surface_to_braille
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    # Base classes (always available)
    "BitmapAdapter",
    "NumpyAdapter",
    "array_to_braille",
    # PIL adapter (requires pillow)
    "PILAdapter",
    "image_to_braille",
    "load_and_render",
    # Matplotlib adapter (requires matplotlib)
    "MatplotlibAdapter",
    "figure_to_braille",
    # Cairo adapter (requires pycairo)
    "CairoAdapter",
    "surface_to_braille",
]
