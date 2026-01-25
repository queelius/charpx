"""Braille rasterizer.

Braille characters encode a 2x4 dot pattern directly into the Unicode codepoint.
This is much more accurate than fingerprint matching for braille, because:
1. Font-rendered braille dots are sparse and vary by font
2. The algorithmic approach directly maps pixels to dots
"""

from __future__ import annotations

import numpy as np


def render(
    bitmap: np.ndarray,
    threshold: float | None = 0.5,
) -> str:
    """Rasterize bitmap to Unicode braille.

    Braille characters (U+2800-U+28FF) encode a 2x4 dot pattern per character.
    Directly encodes pixel brightness into the braille codepoint.

    Args:
        bitmap: 2D array of shape (H, W), values 0.0-1.0 (brightness).
                0.0 = black (no dot), 1.0 = white (dot on).
        threshold: Brightness threshold (0.0-1.0) for a dot to be "on".
                   Pixels > threshold become dots.
                   If None, auto-detect from bitmap mean.

    Returns:
        Multi-line string of braille characters representing the bitmap.

    Example:
        >>> import numpy as np
        >>> from pixdot import render
        >>> bitmap = np.eye(8, dtype=np.float32)
        >>> print(render(bitmap))
        >>> print(render(bitmap, threshold=None))  # auto-detect

    Note:
        Each braille character represents a 2x4 pixel region from the bitmap.
        The output will have height//4 rows and width//2 columns.
    """
    if bitmap.ndim != 2:
        raise ValueError(f"bitmap must be 2D, got shape {bitmap.shape}")

    if threshold is None:
        threshold = max(0.1, min(0.9, float(bitmap.mean())))

    h, w = bitmap.shape
    rows = []

    for cy in range(0, h, 4):
        row_chars = []
        for cx in range(0, w, 2):
            # Extract 2x4 region, pad with zeros if needed
            region = np.zeros((4, 2), dtype=np.float32)
            region_h = min(4, h - cy)
            region_w = min(2, w - cx)
            region[:region_h, :region_w] = bitmap[cy:cy + region_h, cx:cx + region_w]

            # Encode to braille codepoint
            code = _region_to_braille_code(region, threshold)
            row_chars.append(chr(0x2800 + code))

        rows.append(''.join(row_chars))

    return '\n'.join(rows)


def _region_to_braille_code(region: np.ndarray, threshold: float) -> int:
    """Convert a 2x4 region to a braille codepoint offset.

    Braille dot positions and their bit indices:
        col 0   col 1
        +---+---+
    row 0| 0 | 3 |  dots 1,4
        +---+---+
    row 1| 1 | 4 |  dots 2,5
        +---+---+
    row 2| 2 | 5 |  dots 3,6
        +---+---+
    row 3| 6 | 7 |  dots 7,8
        +---+---+

    Args:
        region: 2x4 array of brightness values
        threshold: Brightness threshold for dot activation

    Returns:
        Integer offset from U+2800 (0-255)
    """
    # Mapping: (row, col) -> bit index
    # Standard braille bit layout for Unicode
    dot_map = [
        (0, 0, 0),  # dot 1 -> bit 0
        (1, 0, 1),  # dot 2 -> bit 1
        (2, 0, 2),  # dot 3 -> bit 2
        (3, 0, 6),  # dot 7 -> bit 6
        (0, 1, 3),  # dot 4 -> bit 3
        (1, 1, 4),  # dot 5 -> bit 4
        (2, 1, 5),  # dot 6 -> bit 5
        (3, 1, 7),  # dot 8 -> bit 7
    ]

    code = 0
    for row, col, bit in dot_map:
        if region[row, col] > threshold:
            code |= (1 << bit)

    return code
