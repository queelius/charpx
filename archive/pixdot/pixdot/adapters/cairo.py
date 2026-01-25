"""Cairo adapter for converting ImageSurface objects to braille.

Converts Cairo ImageSurface objects to grayscale bitmaps for braille rendering.

Example:
    >>> import cairo
    >>> from pixdot.adapters import CairoAdapter
    >>> from pixdot.adapters.cairo import surface_to_braille
    >>>
    >>> surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 100)
    >>> ctx = cairo.Context(surface)
    >>> ctx.set_source_rgb(1, 1, 1)
    >>> ctx.paint()
    >>> ctx.set_source_rgb(0, 0, 0)
    >>> ctx.arc(100, 50, 40, 0, 2 * 3.14159)
    >>> ctx.fill()
    >>> print(surface_to_braille(surface, "dark_terminal"))

Requires: pycairo (pip install pixdot[cairo])
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pixdot import RenderConfig

from .base import BitmapAdapter

if TYPE_CHECKING:
    import cairo


def _require_cairo() -> None:
    """Raise ImportError with install instructions if pycairo not available."""
    try:
        import cairo  # noqa: F401
    except ImportError:
        raise ImportError(
            "CairoAdapter requires pycairo. Install with: pip install pixdot[cairo]"
        ) from None


class CairoAdapter(BitmapAdapter):
    """Adapter for Cairo ImageSurface objects.

    Converts Cairo ImageSurface pixel data to grayscale numpy arrays
    for braille rendering. Handles ARGB32 format surfaces.
    """

    def __init__(self) -> None:
        """Initialize adapter and verify pycairo is available."""
        _require_cairo()

    def to_bitmap(
        self, surface: "cairo.ImageSurface", config: RenderConfig
    ) -> np.ndarray:
        """Convert Cairo ImageSurface to grayscale bitmap.

        Args:
            surface: Cairo ImageSurface object (typically ARGB32 format).
            config: Render configuration (used for target dimensions).

        Returns:
            2D numpy array (H, W), values 0.0-1.0.
        """
        # Get pixel data from surface (ARGB32 format -> BGRA in memory)
        width = surface.get_width()
        height = surface.get_height()
        stride = surface.get_stride()

        # Get raw buffer data
        data = np.frombuffer(surface.get_data(), dtype=np.uint8)

        # Validate stride - must be at least width * 4 bytes
        bytes_per_pixel = 4  # ARGB32 format
        min_stride = width * bytes_per_pixel
        if stride < min_stride:
            raise ValueError(
                f"Cairo surface stride ({stride}) is less than expected "
                f"minimum ({min_stride}) for {width}x{height} ARGB32 surface"
            )

        # Handle stride (row padding)
        # Reshape accounting for stride, then slice to actual width
        if stride == min_stride:
            data = data.reshape((height, width, 4))
        else:
            # Stride includes padding bytes at end of each row
            data = data.reshape((height, stride))
            data = data[:, :min_stride].reshape((height, width, 4))

        # Cairo uses BGRA format (native byte order on little-endian)
        # Convert to grayscale using luminance formula
        grayscale = (
            0.299 * data[:, :, 2]  # R
            + 0.587 * data[:, :, 1]  # G
            + 0.114 * data[:, :, 0]  # B
        ) / 255.0

        return grayscale.astype(np.float32)

    def to_color_bitmap(
        self, surface: "cairo.ImageSurface", config: RenderConfig
    ) -> np.ndarray:
        """Convert Cairo ImageSurface to RGB bitmap.

        Args:
            surface: Cairo ImageSurface object (typically ARGB32 format).
            config: Render configuration (used for target dimensions).

        Returns:
            3D numpy array (H, W, 3), values 0.0-1.0.
        """
        # Get pixel data from surface (ARGB32 format -> BGRA in memory)
        width = surface.get_width()
        height = surface.get_height()
        stride = surface.get_stride()

        # Get raw buffer data
        data = np.frombuffer(surface.get_data(), dtype=np.uint8)

        # Validate stride - must be at least width * 4 bytes
        bytes_per_pixel = 4  # ARGB32 format
        min_stride = width * bytes_per_pixel
        if stride < min_stride:
            raise ValueError(
                f"Cairo surface stride ({stride}) is less than expected "
                f"minimum ({min_stride}) for {width}x{height} ARGB32 surface"
            )

        # Handle stride (row padding)
        if stride == min_stride:
            data = data.reshape((height, width, 4))
        else:
            # Stride includes padding bytes at end of each row
            data = data.reshape((height, stride))
            data = data[:, :min_stride].reshape((height, width, 4))

        # Cairo uses BGRA format, convert to RGB
        rgb = data[:, :, [2, 1, 0]].astype(np.float32) / 255.0

        return rgb


def surface_to_braille(
    surface: "cairo.ImageSurface",
    config: RenderConfig | str = "default",
) -> str:
    """One-liner: Cairo ImageSurface -> braille string.

    Convenience function that creates a CairoAdapter and renders
    the surface in a single call.

    Args:
        surface: Cairo ImageSurface object.
        config: RenderConfig instance or preset name.

    Returns:
        Multi-line braille string.

    Example:
        >>> import cairo
        >>> surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 100)
        >>> # Draw on surface...
        >>> print(surface_to_braille(surface, "dark_terminal"))
    """
    return CairoAdapter().render(surface, config)
