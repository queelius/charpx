"""ASCII renderer - Classic ASCII art characters by brightness.

Maps pixel brightness to ASCII characters, from dark (space) to bright
(dense characters like @). Uses 1x2 pixel sampling to correct for typical
terminal character aspect ratio (~2:1 height:width).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, TextIO

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


# Common ASCII character ramps (dark to bright)
CHARSET_STANDARD = " .:-=+*#%@"
CHARSET_DETAILED = " .'`^\",:;Il!i><~+_-?][}{1)(|\\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
CHARSET_BLOCKS = " ░▒▓█"
CHARSET_SIMPLE = " .oO@"


@dataclass(frozen=True)
class AsciiRenderer:
    """Render bitmap as ASCII characters by brightness.

    Each character represents a 1-wide by 2-tall pixel region (to correct
    for terminal character aspect ratio). Brightness is mapped to characters
    from the charset.

    Attributes:
        charset: String of characters from dark to bright.
        invert: If True, invert brightness (dark becomes light).

    Example:
        >>> from dapple import Canvas, ascii
        >>> canvas = Canvas(np.random.rand(24, 40))
        >>> canvas.out(ascii)                       # to stdout
        >>> canvas.out(ascii(charset=" .oO@"))      # simple charset
    """

    charset: str = CHARSET_STANDARD
    invert: bool = False

    @property
    def cell_width(self) -> int:
        """Pixels per character horizontally."""
        return 1

    @property
    def cell_height(self) -> int:
        """Pixels per character vertically (aspect ratio correction)."""
        return 2

    def __call__(
        self,
        charset: str | None = None,
        invert: bool | None = None,
    ) -> AsciiRenderer:
        """Create a new renderer with modified options.

        Args:
            charset: New character set (None to keep current)
            invert: New invert setting (None to keep current)

        Returns:
            New AsciiRenderer with updated settings.
        """
        return AsciiRenderer(
            charset=charset if charset is not None else self.charset,
            invert=invert if invert is not None else self.invert,
        )

    def render(
        self,
        bitmap: NDArray[np.floating],
        colors: NDArray[np.floating] | None = None,
        *,
        dest: TextIO,
    ) -> None:
        """Render bitmap to stream as ASCII.

        Args:
            bitmap: 2D array (H, W) with values 0.0-1.0.
            colors: Ignored (ASCII renderer doesn't support color).
            dest: Stream to write output to.

        Raises:
            ValueError: If bitmap is not 2D.
        """
        if bitmap.ndim != 2:
            raise ValueError(f"bitmap must be 2D, got shape {bitmap.shape}")

        if len(self.charset) == 0:
            raise ValueError("charset must not be empty")

        h, w = bitmap.shape
        rows = h // 2
        cols = w

        if rows == 0:
            return

        # Average each 2-row vertical strip for aspect ratio correction
        block_data = bitmap[: rows * 2, :cols].reshape(rows, 2, cols).mean(axis=1)

        if self.invert:
            block_data = 1.0 - block_data

        # Map brightness to character indices
        n_chars = len(self.charset)
        indices = (block_data * (n_chars - 0.001)).astype(int)
        indices = np.clip(indices, 0, n_chars - 1)

        # Write output
        first_row = True
        for y in range(rows):
            if not first_row:
                dest.write("\n")
            first_row = False

            line = "".join(self.charset[idx] for idx in indices[y])
            dest.write(line)


# Convenience instance for default usage
ascii = AsciiRenderer()
