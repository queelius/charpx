"""Cairo surface adapter for dapple.

Provides conversion from Cairo surfaces to Canvas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from dapple import Canvas
    from dapple.renderers import Renderer


class CairoAdapter:
    """Adapter for Cairo surfaces.

    Converts Cairo ImageSurface objects to Canvas.

    Example:
        >>> import cairo
        >>> from dapple.adapters import CairoAdapter
        >>> surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        >>> ctx = cairo.Context(surface)
        >>> ctx.set_source_rgb(1, 0, 0)
        >>> ctx.rectangle(20, 20, 60, 60)
        >>> ctx.fill()
        >>> adapter = CairoAdapter(surface)
        >>> canvas = adapter.to_canvas()
    """

    def __init__(
        self,
        surface: Any,
        *,
        renderer: Renderer | None = None,
    ) -> None:
        """Create a CairoAdapter.

        Args:
            surface: Cairo ImageSurface object.
            renderer: Default renderer for the resulting Canvas.

        Raises:
            ImportError: If cairo is not installed.
            TypeError: If surface is not a Cairo ImageSurface.
        """
        try:
            import cairo
        except ImportError:
            raise ImportError(
                "pycairo is required for CairoAdapter. "
                "Install with: pip install pycairo"
            )

        if not isinstance(surface, cairo.ImageSurface):
            raise TypeError(f"Expected Cairo ImageSurface, got {type(surface)}")

        self._surface = surface
        self._renderer = renderer

    def to_canvas(self) -> Canvas:
        """Convert to Canvas.

        Returns:
            New Canvas object.
        """
        import cairo

        from dapple import Canvas

        surface = self._surface
        width = surface.get_width()
        height = surface.get_height()
        fmt = surface.get_format()

        # Get raw data
        data = surface.get_data()
        stride = surface.get_stride()

        if fmt == cairo.FORMAT_ARGB32:
            # ARGB32: 4 bytes per pixel (BGRA in memory on little-endian)
            arr = np.ndarray(
                shape=(height, stride // 4, 4),
                dtype=np.uint8,
                buffer=data,
            )[:, :width, :]

            # Cairo uses BGRA ordering on little-endian systems
            b = arr[:, :, 0].astype(np.float32) / 255.0
            g = arr[:, :, 1].astype(np.float32) / 255.0
            r = arr[:, :, 2].astype(np.float32) / 255.0

            colors = np.stack([r, g, b], axis=2)
            bitmap = 0.299 * r + 0.587 * g + 0.114 * b

            return Canvas(bitmap, colors=colors, renderer=self._renderer)

        elif fmt == cairo.FORMAT_RGB24:
            # RGB24: 4 bytes per pixel (BGR_ in memory)
            arr = np.ndarray(
                shape=(height, stride // 4, 4),
                dtype=np.uint8,
                buffer=data,
            )[:, :width, :]

            b = arr[:, :, 0].astype(np.float32) / 255.0
            g = arr[:, :, 1].astype(np.float32) / 255.0
            r = arr[:, :, 2].astype(np.float32) / 255.0

            colors = np.stack([r, g, b], axis=2)
            bitmap = 0.299 * r + 0.587 * g + 0.114 * b

            return Canvas(bitmap, colors=colors, renderer=self._renderer)

        elif fmt == cairo.FORMAT_A8:
            # A8: 8-bit grayscale
            arr = np.ndarray(
                shape=(height, stride),
                dtype=np.uint8,
                buffer=data,
            )[:, :width]

            bitmap = arr.astype(np.float32) / 255.0
            return Canvas(bitmap, renderer=self._renderer)

        else:
            raise ValueError(f"Unsupported Cairo format: {fmt}")


def from_cairo(
    surface: Any,
    *,
    renderer: Renderer | None = None,
) -> Canvas:
    """Create a Canvas from a Cairo surface.

    Convenience function wrapping CairoAdapter.

    Args:
        surface: Cairo ImageSurface object.
        renderer: Default renderer for the resulting Canvas.

    Returns:
        New Canvas object.

    Example:
        >>> import cairo
        >>> from dapple.adapters import from_cairo
        >>> surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        >>> ctx = cairo.Context(surface)
        >>> # ... draw something ...
        >>> canvas = from_cairo(surface)
    """
    return CairoAdapter(surface, renderer=renderer).to_canvas()
