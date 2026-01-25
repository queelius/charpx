"""pixdot: Bitmap to braille rasterizer.

Pure rasterizer converting 2D bitmaps to Unicode braille patterns (U+2800-U+28FF).
Each braille character encodes a 2x4 dot pattern.

API contract: bitmap -> terminal string.

Example:
    >>> import numpy as np
    >>> from pixdot import render
    >>>
    >>> bitmap = np.eye(8, dtype=np.float32)
    >>> print(render(bitmap))
    >>>
    >>> # Auto-detect threshold from bitmap mean
    >>> print(render(bitmap, threshold=None))

Preprocessing utilities:
    >>> from pixdot import auto_contrast, floyd_steinberg
    >>>
    >>> # Apply contrast stretching and dithering for better results
    >>> bitmap = auto_contrast(raw_bitmap)
    >>> bitmap = floyd_steinberg(bitmap)
    >>> print(render(bitmap))

Configuration and adapters:
    >>> from pixdot import RenderConfig, get_preset, resize_bitmap
    >>>
    >>> # Use a named preset
    >>> config = get_preset("dark_terminal")
    >>>
    >>> # Or customize your own
    >>> config = RenderConfig(width_chars=100, dither=True, invert=True)

ANSI color rendering:
    >>> from pixdot import render_ansi
    >>>
    >>> # Grayscale mode (24 levels)
    >>> print(render_ansi(bitmap, color_mode="grayscale"))
    >>>
    >>> # Truecolor mode (24-bit RGB)
    >>> print(render_ansi(bitmap, color_mode="truecolor"))
    >>>
    >>> # With RGB colors array
    >>> colors = np.stack([bitmap, bitmap, bitmap], axis=-1)
    >>> print(render_ansi(bitmap, color_mode="truecolor", colors=colors))

Adapters for converting library objects:
    >>> from pixdot.adapters import NumpyAdapter, BitmapAdapter
    >>>
    >>> # Direct numpy array rendering with full pipeline
    >>> adapter = NumpyAdapter()
    >>> print(adapter.render(bitmap, "dark_terminal"))
    >>>
    >>> # Optional adapters (require additional packages)
    >>> from pixdot.adapters import PILAdapter  # pip install pixdot[pil]
    >>> from pixdot.adapters import MatplotlibAdapter  # pip install pixdot[matplotlib]
    >>> from pixdot.adapters import CairoAdapter  # pip install pixdot[cairo]
"""

from .ansi import RESET, ColorMode, render_ansi
from .braille import render
from .config import PRESETS, RenderConfig, get_preset
from .pixdot import PixDot
from .preprocess import auto_contrast, floyd_steinberg
from .resize import compute_target_dimensions, resize_bitmap

# Import core adapters (always available)
from .adapters import BitmapAdapter, NumpyAdapter, array_to_braille

__all__ = [
    # Core rendering
    "render",
    "render_ansi",
    "ColorMode",
    "RESET",
    # PixDot class
    "PixDot",
    # Preprocessing
    "auto_contrast",
    "floyd_steinberg",
    # Configuration
    "RenderConfig",
    "get_preset",
    "PRESETS",
    # Resizing
    "resize_bitmap",
    "compute_target_dimensions",
    # Adapters
    "BitmapAdapter",
    "NumpyAdapter",
    "array_to_braille",
]
__version__ = "1.0.0"
