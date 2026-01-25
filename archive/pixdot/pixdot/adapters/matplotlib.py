"""Matplotlib adapter for converting figures to braille.

Converts matplotlib Figure objects to grayscale bitmaps for braille rendering.

Example:
    >>> import matplotlib.pyplot as plt
    >>> from pixdot.adapters import MatplotlibAdapter
    >>> from pixdot.adapters.matplotlib import figure_to_braille
    >>>
    >>> fig, ax = plt.subplots()
    >>> ax.plot([1, 2, 3], [1, 4, 9])
    >>> print(figure_to_braille(fig, "dark_terminal"))

Requires: matplotlib (pip install pixdot[matplotlib])
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pixdot import RenderConfig

from .base import BitmapAdapter

if TYPE_CHECKING:
    from matplotlib.figure import Figure


def _require_matplotlib() -> None:
    """Raise ImportError with install instructions if matplotlib not available."""
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        raise ImportError(
            "MatplotlibAdapter requires matplotlib. "
            "Install with: pip install pixdot[matplotlib]"
        ) from None


class MatplotlibAdapter(BitmapAdapter):
    """Adapter for matplotlib figures.

    Renders matplotlib figures to an internal buffer and extracts
    the pixel data as a grayscale bitmap.

    Args:
        dpi: Resolution for figure rendering. Higher DPI preserves more
             detail before downsampling to braille. Default: 150.
    """

    def __init__(self, dpi: int = 150) -> None:
        """Initialize adapter and verify matplotlib is available.

        Args:
            dpi: Resolution for figure rendering.
        """
        _require_matplotlib()
        self.dpi = dpi

    def to_bitmap(self, fig: "Figure", config: RenderConfig) -> np.ndarray:
        """Convert matplotlib Figure to grayscale bitmap.

        Args:
            fig: Matplotlib Figure object.
            config: Render configuration (used for target dimensions).

        Returns:
            2D numpy array (H, W), values 0.0-1.0.
        """
        # Ensure figure is rendered at our target DPI
        original_dpi = fig.get_dpi()
        fig.set_dpi(self.dpi)

        try:
            # Render figure to RGBA buffer
            fig.canvas.draw()
            rgba = np.asarray(fig.canvas.buffer_rgba())

            # Convert RGBA to grayscale using luminance formula
            # ITU-R BT.601 luma coefficients
            grayscale = (
                0.299 * rgba[:, :, 0]
                + 0.587 * rgba[:, :, 1]
                + 0.114 * rgba[:, :, 2]
            ) / 255.0

            return grayscale.astype(np.float32)
        finally:
            # Restore original DPI
            fig.set_dpi(original_dpi)

    def to_color_bitmap(self, fig: "Figure", config: RenderConfig) -> np.ndarray:
        """Convert matplotlib Figure to RGB bitmap.

        Args:
            fig: Matplotlib Figure object.
            config: Render configuration (used for target dimensions).

        Returns:
            3D numpy array (H, W, 3), values 0.0-1.0.
        """
        # Ensure figure is rendered at our target DPI
        original_dpi = fig.get_dpi()
        fig.set_dpi(self.dpi)

        try:
            # Render figure to RGBA buffer
            fig.canvas.draw()
            rgba = np.asarray(fig.canvas.buffer_rgba())

            # Extract RGB channels, normalize to 0-1
            return (rgba[:, :, :3] / 255.0).astype(np.float32)
        finally:
            # Restore original DPI
            fig.set_dpi(original_dpi)


def figure_to_braille(
    fig: "Figure",
    config: RenderConfig | str = "default",
    dpi: int = 150,
) -> str:
    """One-liner: matplotlib figure -> braille string.

    Convenience function that creates a MatplotlibAdapter and renders
    the figure in a single call.

    Args:
        fig: Matplotlib Figure object.
        config: RenderConfig instance or preset name.
        dpi: Resolution for figure rendering.

    Returns:
        Multi-line braille string.

    Example:
        >>> fig, ax = plt.subplots()
        >>> ax.plot([1, 2, 3], [1, 4, 9])
        >>> print(figure_to_braille(fig, "dark_terminal"))
    """
    return MatplotlibAdapter(dpi=dpi).render(fig, config)
