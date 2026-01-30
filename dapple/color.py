"""Color utilities for dapple.

Shared luminance constants and functions used across renderers and adapters.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# ITU-R BT.601 luminance coefficients
LUM_R: float = 0.299
LUM_G: float = 0.587
LUM_B: float = 0.114


def luminance(rgb: NDArray[np.floating]) -> NDArray[np.floating]:
    """Compute perceptual luminance from RGB data.

    Uses ITU-R BT.601 coefficients: 0.299*R + 0.587*G + 0.114*B.

    Args:
        rgb: Array with shape (..., 3) where the last dimension is RGB.
             Handles any number of leading dimensions (2D images, 4D blocks, etc.)

    Returns:
        Luminance array with the last dimension removed, dtype float32.

    Example:
        >>> import numpy as np
        >>> from dapple.color import luminance
        >>> rgb = np.array([[[1.0, 0.0, 0.0]]])  # pure red
        >>> luminance(rgb)
        array([[0.299]], dtype=float32)
    """
    return (
        LUM_R * rgb[..., 0] + LUM_G * rgb[..., 1] + LUM_B * rgb[..., 2]
    ).astype(np.float32)
