"""PixDot class: A bitmap that renders as Unicode braille characters.

The PixDot class encapsulates a bitmap and provides braille rendering on `__str__`.
This follows a bitmap-first design where the bitmap is the primary data and the
braille string is a derived view.

Design Philosophy: "A bitmap that displays as braille" — composition operates on
bitmaps, rendering happens lazily.

Example:
    >>> import numpy as np
    >>> from pixdot import PixDot
    >>>
    >>> # Create from bitmap
    >>> bitmap = np.random.rand(40, 80).astype(np.float32)
    >>> dot = PixDot(bitmap, threshold=0.5)
    >>> print(dot)  # Renders to braille
    >>>
    >>> # Composition
    >>> left = PixDot(np.ones((40, 40), dtype=np.float32))
    >>> right = PixDot(np.zeros((40, 40), dtype=np.float32))
    >>> combined = left + right  # hstack
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, overload

import numpy as np

from .ansi import ColorMode, render_ansi
from .braille import _region_to_braille_code, render

if TYPE_CHECKING:
    from PIL import Image

# Reverse mapping: bit index -> (row, col) in 2x4 region
BIT_TO_DOT: dict[int, tuple[int, int]] = {
    0: (0, 0),  # bit 0 -> row 0, col 0
    1: (1, 0),  # bit 1 -> row 1, col 0
    2: (2, 0),  # bit 2 -> row 2, col 0
    6: (3, 0),  # bit 6 -> row 3, col 0
    3: (0, 1),  # bit 3 -> row 0, col 1
    4: (1, 1),  # bit 4 -> row 1, col 1
    5: (2, 1),  # bit 5 -> row 2, col 1
    7: (3, 1),  # bit 7 -> row 3, col 1
}


class PixDot:
    """A bitmap that renders as Unicode braille characters.

    The PixDot class wraps a 2D numpy bitmap array and provides lazy rendering
    to braille characters. The bitmap is the primary data; the braille string
    is a derived view computed on demand and cached.

    The class is effectively immutable: all modification methods return new
    PixDot instances rather than modifying in place.

    Attributes:
        width: Character width (pixel_width // 2)
        height: Character height (pixel_height // 4)
        pixel_width: Width in pixels
        pixel_height: Height in pixels
        shape: (pixel_height, pixel_width) — numpy convention
        size: (pixel_width, pixel_height) — PIL convention
        bitmap: Read-only access to underlying bitmap

    Example:
        >>> import numpy as np
        >>> from pixdot import PixDot
        >>>
        >>> # Create and print
        >>> bm = np.random.rand(16, 8) > 0.5
        >>> dot = PixDot(bm.astype(float))
        >>> print(dot)
        >>>
        >>> # Composition
        >>> combined = dot + dot  # hstack
        >>> print(combined)
    """

    __slots__ = ("_bitmap", "_colors", "_threshold", "_color_mode", "_cache")

    def __init__(
        self,
        bitmap: np.ndarray,
        *,
        threshold: float | None = 0.5,
        color_mode: ColorMode = "none",
        colors: np.ndarray | None = None,
    ) -> None:
        """Create a PixDot from a bitmap array.

        Args:
            bitmap: 2D numpy array (H, W) with values 0.0-1.0.
                    0.0 = black (no dot), 1.0 = white (dot on).
            threshold: Dot activation threshold. Pixels > threshold become dots.
                       If None, auto-detect from bitmap mean.
            color_mode: Rendering mode: "none", "grayscale", or "truecolor".
            colors: Optional RGB array (H, W, 3) for truecolor mode.

        Raises:
            ValueError: If bitmap is not 2D or colors shape doesn't match.
        """
        if bitmap.ndim != 2:
            raise ValueError(f"bitmap must be 2D, got shape {bitmap.shape}")

        # Store as float32 for consistent behavior
        self._bitmap: np.ndarray = np.asarray(bitmap, dtype=np.float32)
        self._threshold: float | None = threshold
        self._color_mode: ColorMode = color_mode
        self._cache: str | None = None

        if colors is not None:
            if colors.ndim != 3 or colors.shape[2] != 3:
                raise ValueError(f"colors must be (H, W, 3), got shape {colors.shape}")
            if colors.shape[:2] != bitmap.shape:
                raise ValueError(
                    f"colors shape {colors.shape[:2]} must match bitmap shape {bitmap.shape}"
                )
            self._colors: np.ndarray | None = np.asarray(colors, dtype=np.float32)
        else:
            self._colors = None

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def pixel_width(self) -> int:
        """Width in pixels."""
        return self._bitmap.shape[1]

    @property
    def pixel_height(self) -> int:
        """Height in pixels."""
        return self._bitmap.shape[0]

    @property
    def width(self) -> int:
        """Character width (pixel_width // 2, rounded up)."""
        return (self._bitmap.shape[1] + 1) // 2

    @property
    def height(self) -> int:
        """Character height (pixel_height // 4, rounded up)."""
        return (self._bitmap.shape[0] + 3) // 4

    @property
    def shape(self) -> tuple[int, int]:
        """Pixel dimensions (height, width) — numpy convention."""
        return (self.pixel_height, self.pixel_width)

    @property
    def size(self) -> tuple[int, int]:
        """Pixel dimensions (width, height) — PIL convention."""
        return (self.pixel_width, self.pixel_height)

    @property
    def bitmap(self) -> np.ndarray:
        """Read-only access to underlying bitmap.

        Returns a view of the internal bitmap. Do not modify directly;
        use builder methods to create modified copies.
        """
        # Return view with write disabled
        view = self._bitmap.view()
        view.flags.writeable = False
        return view

    @property
    def colors(self) -> np.ndarray | None:
        """Read-only access to color array, if set."""
        if self._colors is None:
            return None
        view = self._colors.view()
        view.flags.writeable = False
        return view

    @property
    def threshold(self) -> float | None:
        """Dot activation threshold."""
        return self._threshold

    @property
    def color_mode(self) -> ColorMode:
        """Current color mode."""
        return self._color_mode

    # -------------------------------------------------------------------------
    # String representation
    # -------------------------------------------------------------------------

    def __str__(self) -> str:
        """Render to braille string (cached)."""
        if self._cache is None:
            if self._color_mode == "none":
                self._cache = render(self._bitmap, self._threshold)
            else:
                self._cache = render_ansi(
                    self._bitmap,
                    self._threshold,
                    self._color_mode,
                    self._colors,
                )
        return self._cache

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"PixDot({self.pixel_width}x{self.pixel_height}, "
            f"color_mode='{self._color_mode}')"
        )

    # -------------------------------------------------------------------------
    # Pixel access
    # -------------------------------------------------------------------------

    @overload
    def __getitem__(self, key: tuple[int, int]) -> float: ...

    @overload
    def __getitem__(self, key: tuple[slice, slice]) -> "PixDot": ...

    def __getitem__(
        self, key: tuple[int, int] | tuple[slice, slice]
    ) -> float | "PixDot":
        """Access pixel value or slice region.

        Args:
            key: Either (y, x) for single pixel or (y_slice, x_slice) for region.

        Returns:
            Single pixel value (float) or new PixDot for sliced region.

        Example:
            >>> dot = PixDot(np.random.rand(40, 80))
            >>> pixel = dot[10, 20]  # Single pixel
            >>> region = dot[0:20, 0:40]  # Sliced region as new PixDot
        """
        if isinstance(key[0], slice) or isinstance(key[1], slice):
            # Slice access - return new PixDot
            y_slice, x_slice = key
            new_bitmap = self._bitmap[y_slice, x_slice]
            new_colors = None
            if self._colors is not None:
                new_colors = self._colors[y_slice, x_slice]
            return PixDot(
                new_bitmap,
                threshold=self._threshold,
                color_mode=self._color_mode,
                colors=new_colors,
            )
        else:
            # Single pixel access
            y, x = key
            return float(self._bitmap[y, x])

    # -------------------------------------------------------------------------
    # Factory methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_string(
        cls,
        braille_text: str,
        *,
        threshold: float | None = 0.5,
        color_mode: ColorMode = "none",
    ) -> "PixDot":
        """Parse braille text back into a PixDot.

        Creates a bitmap from existing braille characters. Each braille
        character (U+2800-U+28FF) is decoded into its 2x4 dot pattern.

        Args:
            braille_text: Multi-line string of braille characters.
            threshold: Threshold for future rendering (doesn't affect parsing).
            color_mode: Color mode for future rendering.

        Returns:
            New PixDot with bitmap reconstructed from braille.

        Example:
            >>> original = PixDot(np.eye(8, dtype=np.float32))
            >>> text = str(original)
            >>> reconstructed = PixDot.from_string(text)
        """
        bitmap = _parse_braille_to_bitmap(braille_text)
        return cls(bitmap, threshold=threshold, color_mode=color_mode)

    @classmethod
    def load(
        cls,
        path: str,
        *,
        threshold: float | None = 0.5,
        color_mode: ColorMode = "none",
    ) -> "PixDot":
        """Load braille text from a file.

        Reads a text file containing braille characters and parses it
        into a PixDot.

        Args:
            path: Path to .txt or .ans file containing braille text.
            threshold: Threshold for future rendering.
            color_mode: Color mode for future rendering.

        Returns:
            New PixDot with bitmap reconstructed from file contents.

        Example:
            >>> dot.write("output.txt")
            >>> loaded = PixDot.load("output.txt")
        """
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        return cls.from_string(text, threshold=threshold, color_mode=color_mode)

    # -------------------------------------------------------------------------
    # Builder methods (return new PixDot with same bitmap)
    # -------------------------------------------------------------------------

    def with_threshold(self, threshold: float | None) -> "PixDot":
        """Create new PixDot with different threshold.

        Args:
            threshold: New dot activation threshold (0.0-1.0 or None for auto).

        Returns:
            New PixDot with updated threshold.

        Example:
            >>> dot = PixDot(bitmap, threshold=0.5)
            >>> brighter = dot.with_threshold(0.3)  # More dots visible
        """
        return PixDot(
            self._bitmap.copy(),
            threshold=threshold,
            color_mode=self._color_mode,
            colors=self._colors.copy() if self._colors is not None else None,
        )

    def with_color(
        self,
        mode: ColorMode,
        colors: np.ndarray | None = None,
    ) -> "PixDot":
        """Create new PixDot with different color mode.

        Args:
            mode: Color mode: "none", "grayscale", or "truecolor".
            colors: Optional RGB array (H, W, 3) for truecolor mode.

        Returns:
            New PixDot with updated color settings.

        Example:
            >>> dot = PixDot(bitmap)
            >>> gray = dot.with_color("grayscale")
            >>> colored = dot.with_color("truecolor", rgb_array)
        """
        return PixDot(
            self._bitmap.copy(),
            threshold=self._threshold,
            color_mode=mode,
            colors=colors.copy() if colors is not None else None,
        )

    def with_invert(self) -> "PixDot":
        """Create new PixDot with inverted bitmap.

        Inverts all pixel values: new_value = 1.0 - old_value.

        Returns:
            New PixDot with inverted bitmap.

        Example:
            >>> dot = PixDot(bitmap)
            >>> inverted = dot.with_invert()
        """
        inverted_bitmap = 1.0 - self._bitmap
        inverted_colors = None
        if self._colors is not None:
            inverted_colors = 1.0 - self._colors
        return PixDot(
            inverted_bitmap,
            threshold=self._threshold,
            color_mode=self._color_mode,
            colors=inverted_colors,
        )

    # -------------------------------------------------------------------------
    # Composition methods (return new PixDot)
    # -------------------------------------------------------------------------

    def hstack(self, other: "PixDot") -> "PixDot":
        """Horizontally concatenate with another PixDot.

        Aligns heights by padding the shorter one with zeros.

        Args:
            other: PixDot to place to the right.

        Returns:
            New PixDot with combined bitmap.

        Example:
            >>> left = PixDot(np.ones((20, 10)))
            >>> right = PixDot(np.zeros((20, 10)))
            >>> combined = left.hstack(right)
        """
        # Align heights
        h1, w1 = self._bitmap.shape
        h2, w2 = other._bitmap.shape
        max_h = max(h1, h2)

        # Pad to same height
        bm1 = np.zeros((max_h, w1), dtype=np.float32)
        bm1[:h1, :] = self._bitmap
        bm2 = np.zeros((max_h, w2), dtype=np.float32)
        bm2[:h2, :] = other._bitmap

        combined = np.hstack([bm1, bm2])

        # Handle colors
        combined_colors = None
        if self._colors is not None or other._colors is not None:
            c1 = self._colors if self._colors is not None else np.zeros((h1, w1, 3), dtype=np.float32)
            c2 = other._colors if other._colors is not None else np.zeros((h2, w2, 3), dtype=np.float32)
            c1_padded = np.zeros((max_h, w1, 3), dtype=np.float32)
            c1_padded[:h1, :] = c1
            c2_padded = np.zeros((max_h, w2, 3), dtype=np.float32)
            c2_padded[:h2, :] = c2
            combined_colors = np.hstack([c1_padded, c2_padded])

        return PixDot(
            combined,
            threshold=self._threshold,
            color_mode=self._color_mode,
            colors=combined_colors,
        )

    def __add__(self, other: "PixDot") -> "PixDot":
        """Horizontal concatenation via + operator.

        Example:
            >>> combined = left + right
        """
        return self.hstack(other)

    def vstack(self, other: "PixDot") -> "PixDot":
        """Vertically concatenate with another PixDot.

        Aligns widths by padding the narrower one with zeros.

        Args:
            other: PixDot to place below.

        Returns:
            New PixDot with combined bitmap.

        Example:
            >>> top = PixDot(np.ones((10, 20)))
            >>> bottom = PixDot(np.zeros((10, 20)))
            >>> combined = top.vstack(bottom)
        """
        # Align widths
        h1, w1 = self._bitmap.shape
        h2, w2 = other._bitmap.shape
        max_w = max(w1, w2)

        # Pad to same width
        bm1 = np.zeros((h1, max_w), dtype=np.float32)
        bm1[:, :w1] = self._bitmap
        bm2 = np.zeros((h2, max_w), dtype=np.float32)
        bm2[:, :w2] = other._bitmap

        combined = np.vstack([bm1, bm2])

        # Handle colors
        combined_colors = None
        if self._colors is not None or other._colors is not None:
            c1 = self._colors if self._colors is not None else np.zeros((h1, w1, 3), dtype=np.float32)
            c2 = other._colors if other._colors is not None else np.zeros((h2, w2, 3), dtype=np.float32)
            c1_padded = np.zeros((h1, max_w, 3), dtype=np.float32)
            c1_padded[:, :w1] = c1
            c2_padded = np.zeros((h2, max_w, 3), dtype=np.float32)
            c2_padded[:, :w2] = c2
            combined_colors = np.vstack([c1_padded, c2_padded])

        return PixDot(
            combined,
            threshold=self._threshold,
            color_mode=self._color_mode,
            colors=combined_colors,
        )

    def overlay(self, other: "PixDot", x: int, y: int) -> "PixDot":
        """Place another PixDot at specified position.

        Creates a new PixDot with `other` overlaid starting at pixel (x, y).
        The base bitmap is extended if necessary.

        Args:
            other: PixDot to overlay.
            x: X position (column) in pixels.
            y: Y position (row) in pixels.

        Returns:
            New PixDot with overlay applied.

        Example:
            >>> base = PixDot(np.zeros((40, 80)))
            >>> stamp = PixDot(np.ones((10, 10)))
            >>> combined = base.overlay(stamp, 20, 10)
        """
        h1, w1 = self._bitmap.shape
        h2, w2 = other._bitmap.shape

        # Calculate required dimensions
        new_h = max(h1, y + h2)
        new_w = max(w1, x + w2)

        # Create new bitmap
        new_bitmap = np.zeros((new_h, new_w), dtype=np.float32)
        new_bitmap[:h1, :w1] = self._bitmap

        # Overlay other (clip to non-negative region)
        y_start = max(0, y)
        x_start = max(0, x)
        y_end = min(new_h, y + h2)
        x_end = min(new_w, x + w2)

        src_y_start = y_start - y
        src_x_start = x_start - x
        src_y_end = y_end - y
        src_x_end = x_end - x

        new_bitmap[y_start:y_end, x_start:x_end] = other._bitmap[
            src_y_start:src_y_end, src_x_start:src_x_end
        ]

        # Handle colors
        new_colors = None
        if self._colors is not None or other._colors is not None:
            new_colors = np.zeros((new_h, new_w, 3), dtype=np.float32)
            if self._colors is not None:
                new_colors[:h1, :w1] = self._colors
            if other._colors is not None:
                new_colors[y_start:y_end, x_start:x_end] = other._colors[
                    src_y_start:src_y_end, src_x_start:src_x_end
                ]

        return PixDot(
            new_bitmap,
            threshold=self._threshold,
            color_mode=self._color_mode,
            colors=new_colors,
        )

    def crop(self, x1: int, y1: int, x2: int, y2: int) -> "PixDot":
        """Crop by pixel coordinates.

        Args:
            x1: Left edge (column start).
            y1: Top edge (row start).
            x2: Right edge (column end, exclusive).
            y2: Bottom edge (row end, exclusive).

        Returns:
            New PixDot with cropped region.

        Example:
            >>> cropped = dot.crop(10, 10, 50, 30)
        """
        new_bitmap = self._bitmap[y1:y2, x1:x2].copy()
        new_colors = None
        if self._colors is not None:
            new_colors = self._colors[y1:y2, x1:x2].copy()
        return PixDot(
            new_bitmap,
            threshold=self._threshold,
            color_mode=self._color_mode,
            colors=new_colors,
        )

    def crop_chars(self, x1: int, y1: int, x2: int, y2: int) -> "PixDot":
        """Crop by character coordinates.

        Converts character positions to pixel positions:
        - x_pixel = x_char * 2
        - y_pixel = y_char * 4

        Args:
            x1: Left edge in characters.
            y1: Top edge in characters.
            x2: Right edge in characters (exclusive).
            y2: Bottom edge in characters (exclusive).

        Returns:
            New PixDot with cropped region.

        Example:
            >>> cropped = dot.crop_chars(5, 2, 20, 10)
        """
        return self.crop(x1 * 2, y1 * 4, x2 * 2, y2 * 4)

    # -------------------------------------------------------------------------
    # Conversion methods
    # -------------------------------------------------------------------------

    def to_bitmap(self) -> np.ndarray:
        """Return copy of bitmap array.

        Returns:
            Copy of internal bitmap as float32 array.
        """
        return self._bitmap.copy()

    def to_pil(self) -> "Image.Image":
        """Convert to PIL Image.

        Requires PIL to be installed (via `pip install pixdot[cli]`).

        Returns:
            PIL Image in grayscale ('L') or RGB mode.

        Raises:
            ImportError: If PIL is not available.

        Example:
            >>> img = dot.to_pil()
            >>> img.save("output.png")
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError(
                "PIL is required for to_pil(). "
                "Install with: pip install pixdot[cli]"
            )

        if self._colors is not None:
            # RGB image
            rgb_data = (self._colors * 255).astype(np.uint8)
            return Image.fromarray(rgb_data)
        else:
            # Grayscale image
            gray_data = (self._bitmap * 255).astype(np.uint8)
            return Image.fromarray(gray_data)

    def save(self, path: str) -> None:
        """Save as image file.

        Converts to PIL Image and saves to specified path.
        Format is inferred from file extension.

        Args:
            path: Output file path (e.g., "output.png", "output.jpg").

        Example:
            >>> dot.save("output.png")
        """
        img = self.to_pil()
        img.save(path)

    def write(self, path: str) -> None:
        """Write braille text to file.

        Renders to braille string and writes to text file.

        Args:
            path: Output file path (e.g., "output.txt").

        Example:
            >>> dot.write("output.txt")
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(self))


def _parse_braille_to_bitmap(braille_text: str) -> np.ndarray:
    """Parse braille text back to a bitmap.

    Each braille character (U+2800-U+28FF) is decoded into its 2x4 dot pattern.
    The resulting bitmap has values 0.0 (no dot) and 1.0 (dot).

    Args:
        braille_text: Multi-line string of braille characters.

    Returns:
        2D numpy array of shape (rows * 4, cols * 2).
    """
    # Strip ANSI codes if present
    import re
    clean_text = re.sub(r'\033\[[0-9;]*m', '', braille_text)

    lines = clean_text.split('\n')

    # Filter out empty lines at end
    while lines and not lines[-1]:
        lines.pop()

    if not lines:
        return np.zeros((0, 0), dtype=np.float32)

    # Find max width
    max_chars = max(len(line) for line in lines)
    num_rows = len(lines)

    # Create bitmap (4 pixel rows per char row, 2 pixel cols per char)
    bitmap = np.zeros((num_rows * 4, max_chars * 2), dtype=np.float32)

    for row_idx, line in enumerate(lines):
        for col_idx, char in enumerate(line):
            code = ord(char)
            if 0x2800 <= code <= 0x28FF:
                offset = code - 0x2800
                # Decode each bit
                for bit in range(8):
                    if offset & (1 << bit):
                        dot_row, dot_col = BIT_TO_DOT[bit]
                        pixel_row = row_idx * 4 + dot_row
                        pixel_col = col_idx * 2 + dot_col
                        bitmap[pixel_row, pixel_col] = 1.0

    return bitmap
