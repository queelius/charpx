"""Numpy array adapter for dapple.

Provides direct conversion from numpy arrays to Canvas.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from dapple import Canvas
    from dapple.renderers import Renderer


class NumpyAdapter:
    """Adapter for numpy arrays.

    Converts 2D grayscale or 3D RGB numpy arrays to Canvas objects.

    Example:
        >>> import numpy as np
        >>> from dapple.adapters import NumpyAdapter
        >>> array = np.random.rand(48, 80)
        >>> adapter = NumpyAdapter(array)
        >>> canvas = adapter.to_canvas()
    """

    def __init__(
        self,
        array: NDArray[np.floating],
        *,
        renderer: Renderer | None = None,
    ) -> None:
        """Create a NumpyAdapter.

        Args:
            array: 2D grayscale (H, W) or 3D RGB (H, W, 3) array.
                   Values should be in range 0.0-1.0.
            renderer: Default renderer for the resulting Canvas.

        Raises:
            ValueError: If array shape is invalid.
        """
        if array.ndim not in (2, 3):
            raise ValueError(f"Array must be 2D or 3D, got {array.ndim}D")
        if array.ndim == 3 and array.shape[2] != 3:
            raise ValueError(f"3D array must have shape (H, W, 3), got {array.shape}")

        self._array = array
        self._renderer = renderer

    def to_canvas(self) -> Canvas:
        """Convert to Canvas.

        Returns:
            New Canvas object.
        """
        from dapple import Canvas

        if self._array.ndim == 3:
            # RGB array - compute luminance for bitmap
            colors = self._array.astype(np.float32)
            bitmap = (
                0.299 * colors[:, :, 0]
                + 0.587 * colors[:, :, 1]
                + 0.114 * colors[:, :, 2]
            )
            return Canvas(bitmap, colors=colors, renderer=self._renderer)
        else:
            bitmap = self._array.astype(np.float32)
            return Canvas(bitmap, renderer=self._renderer)


def from_array(
    array: NDArray[np.floating],
    *,
    renderer: Renderer | None = None,
) -> Canvas:
    """Create a Canvas from a numpy array.

    Convenience function wrapping NumpyAdapter.

    Args:
        array: 2D grayscale (H, W) or 3D RGB (H, W, 3) array.
               Values should be in range 0.0-1.0.
        renderer: Default renderer for the resulting Canvas.

    Returns:
        New Canvas object.

    Example:
        >>> import numpy as np
        >>> from dapple.adapters import from_array
        >>> array = np.random.rand(48, 80)
        >>> canvas = from_array(array)
    """
    return NumpyAdapter(array, renderer=renderer).to_canvas()
