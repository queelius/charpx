"""Matplotlib figure adapter for dapple.

Provides conversion from Matplotlib figures to Canvas.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from dapple import Canvas
    from dapple.renderers import Renderer


class MatplotlibAdapter:
    """Adapter for Matplotlib figures.

    Converts Matplotlib Figure objects to Canvas by rendering to a bitmap.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from dapple.adapters import MatplotlibAdapter
        >>> fig, ax = plt.subplots()
        >>> ax.plot([0, 1, 2], [0, 1, 0])
        >>> adapter = MatplotlibAdapter(fig, width=80)
        >>> canvas = adapter.to_canvas()
        >>> print(canvas)
    """

    def __init__(
        self,
        figure: Any,
        *,
        width: int | None = None,
        height: int | None = None,
        dpi: int = 100,
        renderer: Renderer | None = None,
    ) -> None:
        """Create a MatplotlibAdapter.

        Args:
            figure: Matplotlib Figure object.
            width: Target width in pixels (None for auto from figure size).
            height: Target height in pixels (None for auto or proportional).
            dpi: Rendering DPI (default 100).
            renderer: Default renderer for the resulting Canvas.

        Raises:
            ImportError: If matplotlib is not installed.
            TypeError: If figure is not a Matplotlib Figure.
        """
        try:
            from matplotlib.figure import Figure
        except ImportError:
            raise ImportError(
                "matplotlib is required for MatplotlibAdapter. "
                "Install with: pip install matplotlib"
            )

        if not isinstance(figure, Figure):
            raise TypeError(f"Expected Matplotlib Figure, got {type(figure)}")

        self._figure = figure
        self._width = width
        self._height = height
        self._dpi = dpi
        self._renderer = renderer

    def to_canvas(self) -> Canvas:
        """Convert to Canvas.

        Returns:
            New Canvas object.
        """
        from dapple import Canvas

        fig = self._figure

        # Compute size
        if self._width is not None or self._height is not None:
            orig_w, orig_h = fig.get_size_inches()
            if self._width is not None and self._height is not None:
                fig_w = self._width / self._dpi
                fig_h = self._height / self._dpi
            elif self._width is not None:
                fig_w = self._width / self._dpi
                fig_h = orig_h * (fig_w / orig_w)
            else:
                fig_h = self._height / self._dpi  # type: ignore
                fig_w = orig_w * (fig_h / orig_h)
            fig.set_size_inches(fig_w, fig_h)

        # Render to buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=self._dpi, bbox_inches="tight", pad_inches=0)
        buf.seek(0)

        # Load as numpy array
        try:
            from PIL import Image

            img = Image.open(buf)
            rgb = img.convert("RGB")
            colors = np.array(rgb, dtype=np.float32) / 255.0
        except ImportError:
            # Fallback without PIL - use matplotlib's internal rendering
            fig.canvas.draw()
            data = np.frombuffer(fig.canvas.tostring_rgb(), dtype=np.uint8)
            w, h = fig.canvas.get_width_height()
            colors = data.reshape((h, w, 3)).astype(np.float32) / 255.0

        bitmap = (
            0.299 * colors[:, :, 0]
            + 0.587 * colors[:, :, 1]
            + 0.114 * colors[:, :, 2]
        )

        return Canvas(bitmap, colors=colors, renderer=self._renderer)


def from_matplotlib(
    figure: Any,
    *,
    width: int | None = None,
    height: int | None = None,
    dpi: int = 100,
    renderer: Renderer | None = None,
) -> Canvas:
    """Create a Canvas from a Matplotlib Figure.

    Convenience function wrapping MatplotlibAdapter.

    Args:
        figure: Matplotlib Figure object.
        width: Target width in pixels (None for auto from figure size).
        height: Target height in pixels (None for auto or proportional).
        dpi: Rendering DPI (default 100).
        renderer: Default renderer for the resulting Canvas.

    Returns:
        New Canvas object.

    Example:
        >>> import matplotlib.pyplot as plt
        >>> from dapple.adapters import from_matplotlib
        >>> fig, ax = plt.subplots()
        >>> ax.plot([0, 1, 2], [0, 1, 0])
        >>> canvas = from_matplotlib(fig, width=80)
    """
    return MatplotlibAdapter(
        figure, width=width, height=height, dpi=dpi, renderer=renderer
    ).to_canvas()
