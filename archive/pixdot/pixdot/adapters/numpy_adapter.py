"""Numpy adapter for direct bitmap input.

Adapter for users who already have numpy arrays and want the full
preprocessing pipeline (resize, contrast, invert, dither) applied.

Example:
    >>> import numpy as np
    >>> from pixdot.adapters import NumpyAdapter
    >>>
    >>> bitmap = np.random.rand(100, 100).astype(np.float32)
    >>> print(NumpyAdapter().render(bitmap, "dark_terminal"))
"""

from __future__ import annotations

import numpy as np

from pixdot import RenderConfig

from .base import BitmapAdapter


class NumpyAdapter(BitmapAdapter):
    """Adapter for direct numpy array input.

    Useful when you have a raw bitmap and want the full pipeline
    (resize, contrast, invert, dither) applied automatically.

    Accepts both 2D grayscale arrays and 3D RGB/RGBA arrays.
    """

    def to_bitmap(self, source: np.ndarray, config: RenderConfig) -> np.ndarray:
        """Convert numpy array to grayscale bitmap.

        Args:
            source: 2D grayscale array (H, W) or 3D RGB/RGBA array (H, W, 3|4).
                    Values should be 0.0-1.0 (float) or 0-255 (int).
            config: Render configuration (used for target dimensions).

        Returns:
            2D numpy array (H, W), values 0.0-1.0.
        """
        arr = np.asarray(source)

        # Handle 3D arrays (RGB or RGBA)
        if arr.ndim == 3:
            if arr.shape[2] not in (3, 4):
                raise ValueError(
                    f"3D array must have 3 (RGB) or 4 (RGBA) channels, "
                    f"got {arr.shape[2]} channels with shape {arr.shape}"
                )
            # Convert RGB/RGBA to grayscale using luminance formula
            grayscale = (
                0.299 * arr[:, :, 0]
                + 0.587 * arr[:, :, 1]
                + 0.114 * arr[:, :, 2]
            )
        elif arr.ndim == 2:
            grayscale = arr
        else:
            raise ValueError(
                f"Expected 2D or 3D array, got {arr.ndim}D with shape {arr.shape}"
            )

        # Normalize to 0.0-1.0 if integer type
        if np.issubdtype(grayscale.dtype, np.integer):
            grayscale = grayscale.astype(np.float32) / 255.0
        else:
            grayscale = grayscale.astype(np.float32)

        self.validate_bitmap(grayscale)
        return grayscale

    def to_color_bitmap(
        self, source: np.ndarray, config: RenderConfig
    ) -> np.ndarray | None:
        """Extract RGB color bitmap from array.

        Args:
            source: 3D RGB/RGBA array (H, W, 3|4), or 2D grayscale.
            config: Render configuration.

        Returns:
            3D numpy array (H, W, 3), values 0.0-1.0, or None if grayscale.
        """
        arr = np.asarray(source)

        if arr.ndim == 3 and arr.shape[2] in (3, 4):
            # Extract RGB channels
            rgb = arr[:, :, :3]

            # Normalize to 0.0-1.0 if integer type
            if np.issubdtype(rgb.dtype, np.integer):
                rgb = rgb.astype(np.float32) / 255.0
            else:
                rgb = rgb.astype(np.float32)

            return rgb

        # No color available for grayscale input
        return None


def array_to_braille(
    array: np.ndarray,
    config: RenderConfig | str = "default",
) -> str:
    """One-liner: numpy array -> braille string.

    Convenience function that creates a NumpyAdapter and renders
    the array in a single call.

    Args:
        array: 2D grayscale or 3D RGB/RGBA numpy array.
        config: RenderConfig instance or preset name.

    Returns:
        Multi-line braille string.

    Example:
        >>> import numpy as np
        >>> bitmap = np.eye(16, dtype=np.float32)
        >>> print(array_to_braille(bitmap))
    """
    return NumpyAdapter().render(array, config)
