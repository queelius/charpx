"""Kitty renderer - Kitty graphics protocol.

The Kitty graphics protocol is a modern terminal graphics standard supported
by Kitty, WezTerm, Ghostty, and Konsole (partial). It can transmit images
as PNG, RGB, or RGBA data encoded in base64.

Format: ESC_G <key>=<value>,... ; <base64 data> ESC \\

Key parameters:
- a=T: action=transmit (display immediately)
- f=100: format=PNG
- f=24: format=RGB
- f=32: format=RGBA
- m=1: more data follows
- m=0: last chunk (default)
"""

from __future__ import annotations

import base64
import io
import zlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, TextIO

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

# APC (Application Program Command) escape sequence for Kitty
APC_START = "\033_G"  # ESC _ G
APC_END = "\033\\"  # ESC \

# Maximum chunk size for base64 data (4096 is commonly used)
MAX_CHUNK_SIZE = 4096


def _make_png_minimal(
    bitmap: NDArray[np.floating],
    colors: NDArray[np.floating] | None = None,
) -> bytes:
    """Create a minimal PNG without external dependencies.

    Uses raw DEFLATE compression (zlib). This is a minimal implementation
    that creates valid PNG files without PIL.

    Args:
        bitmap: 2D array (H, W) with values 0.0-1.0
        colors: Optional 3D array (H, W, 3) with RGB values 0.0-1.0

    Returns:
        PNG file bytes
    """
    h, w = bitmap.shape

    if colors is not None:
        # RGB mode
        rgb = (colors * 255).astype(np.uint8)
        # PNG requires filter byte at start of each row
        raw = bytearray()
        for y in range(h):
            raw.append(0)  # Filter type: None
            raw.extend(rgb[y].tobytes())
        color_type = 2  # RGB
        bit_depth = 8
    else:
        # Grayscale mode
        gray = (bitmap * 255).astype(np.uint8)
        raw = bytearray()
        for y in range(h):
            raw.append(0)  # Filter type: None
            raw.extend(gray[y].tobytes())
        color_type = 0  # Grayscale
        bit_depth = 8

    # PNG signature
    signature = b"\x89PNG\r\n\x1a\n"

    def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
        """Create a PNG chunk with CRC."""
        length = len(data).to_bytes(4, "big")
        chunk_data = chunk_type + data
        crc = zlib.crc32(chunk_data) & 0xFFFFFFFF
        return length + chunk_data + crc.to_bytes(4, "big")

    # IHDR chunk (image header)
    ihdr_data = (
        w.to_bytes(4, "big")  # Width
        + h.to_bytes(4, "big")  # Height
        + bytes([bit_depth, color_type, 0, 0, 0])  # Bit depth, color type, compression, filter, interlace
    )
    ihdr = make_chunk(b"IHDR", ihdr_data)

    # IDAT chunk (compressed image data)
    compressed = zlib.compress(bytes(raw), level=6)
    idat = make_chunk(b"IDAT", compressed)

    # IEND chunk (image end)
    iend = make_chunk(b"IEND", b"")

    return signature + ihdr + idat + iend


def _try_pil_png(
    bitmap: NDArray[np.floating],
    colors: NDArray[np.floating] | None = None,
) -> bytes | None:
    """Try to create PNG using PIL if available.

    PIL produces smaller/better compressed PNGs than our minimal implementation.

    Returns:
        PNG bytes or None if PIL not available.
    """
    try:
        from PIL import Image
    except ImportError:
        return None

    h, w = bitmap.shape

    if colors is not None:
        rgb = (colors * 255).astype(np.uint8)
        img = Image.fromarray(rgb)
    else:
        gray = (bitmap * 255).astype(np.uint8)
        img = Image.fromarray(gray)

    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


@dataclass(frozen=True)
class KittyRenderer:
    """Render bitmap using Kitty graphics protocol.

    The Kitty protocol transmits images as base64-encoded data, with support
    for PNG compression. Supported by Kitty, WezTerm, Ghostty, and Konsole.

    Attributes:
        format: Output format - "png" (compressed), "rgb", or "rgba".
        compression: Use zlib compression for raw formats (default True).
        columns: Display width in terminal columns (None = native pixel size).
        rows: Display height in terminal rows (None = native pixel size).

    Example:
        >>> from dapple import Canvas, kitty
        >>> canvas = Canvas(np.random.rand(48, 80))
        >>> canvas.out(kitty)  # In supported terminal
        >>> canvas.out(kitty(columns=80))  # Scale to 80 columns wide
    """

    format: Literal["png", "rgb", "rgba"] = "png"
    compression: bool = True
    columns: int | None = None
    rows: int | None = None

    @property
    def cell_width(self) -> int:
        """Kitty outputs actual pixels (1:1)."""
        return 1

    @property
    def cell_height(self) -> int:
        """Kitty outputs actual pixels (1:1)."""
        return 1

    def __call__(
        self,
        format: Literal["png", "rgb", "rgba"] | None = None,
        compression: bool | None = None,
        columns: int | None = None,
        rows: int | None = None,
    ) -> KittyRenderer:
        """Create a new renderer with modified options.

        Args:
            format: New format (None to keep current)
            compression: New compression setting (None to keep current)
            columns: Display width in terminal columns (None to keep current)
            rows: Display height in terminal rows (None to keep current)

        Returns:
            New KittyRenderer with updated settings.
        """
        return KittyRenderer(
            format=format if format is not None else self.format,
            compression=compression if compression is not None else self.compression,
            columns=columns if columns is not None else self.columns,
            rows=rows if rows is not None else self.rows,
        )

    def render(
        self,
        bitmap: NDArray[np.floating],
        colors: NDArray[np.floating] | None = None,
        *,
        dest: TextIO,
    ) -> None:
        """Render bitmap to stream as Kitty graphics escape sequence.

        Args:
            bitmap: 2D array (H, W) with values 0.0-1.0.
            colors: Optional 3D array (H, W, 3) with RGB values 0.0-1.0.
            dest: Stream to write output to.

        Raises:
            ValueError: If bitmap is not 2D or colors shape doesn't match.
        """
        if bitmap.ndim != 2:
            raise ValueError(f"bitmap must be 2D, got shape {bitmap.shape}")

        if colors is not None:
            if colors.ndim != 3 or colors.shape[2] != 3:
                raise ValueError(f"colors must be (H, W, 3), got shape {colors.shape}")
            if colors.shape[:2] != bitmap.shape:
                raise ValueError(
                    f"colors shape {colors.shape[:2]} must match bitmap shape {bitmap.shape}"
                )

        h, w = bitmap.shape

        if self.format == "png":
            # Try PIL first for better compression
            data = _try_pil_png(bitmap, colors)
            if data is None:
                data = _make_png_minimal(bitmap, colors)
            fmt_code = 100  # PNG format
            params = f"a=T,f={fmt_code}"
        else:
            # Raw RGB or RGBA
            if colors is not None:
                rgb = (colors * 255).astype(np.uint8)
                if self.format == "rgba":
                    # Add alpha channel (fully opaque)
                    alpha = np.full((h, w, 1), 255, dtype=np.uint8)
                    rgba = np.concatenate([rgb, alpha], axis=2)
                    data = rgba.tobytes()
                    fmt_code = 32  # RGBA
                else:
                    data = rgb.tobytes()
                    fmt_code = 24  # RGB
            else:
                # Grayscale to RGB
                gray = (bitmap * 255).astype(np.uint8)
                rgb = np.stack([gray, gray, gray], axis=2)
                if self.format == "rgba":
                    alpha = np.full((h, w, 1), 255, dtype=np.uint8)
                    rgba = np.concatenate([rgb, alpha], axis=2)
                    data = rgba.tobytes()
                    fmt_code = 32
                else:
                    data = rgb.tobytes()
                    fmt_code = 24

            # Optionally compress raw data
            if self.compression:
                data = zlib.compress(data, level=6)
                params = f"a=T,f={fmt_code},o=z,s={w},v={h}"
            else:
                params = f"a=T,f={fmt_code},s={w},v={h}"

        # Add display size parameters (c=columns, r=rows)
        if self.columns is not None:
            params += f",c={self.columns}"
        if self.rows is not None:
            params += f",r={self.rows}"

        # Encode as base64
        b64_data = base64.b64encode(data).decode("ascii")

        # Write escape sequence, chunking if necessary
        first_chunk = True
        offset = 0
        while offset < len(b64_data):
            chunk = b64_data[offset : offset + MAX_CHUNK_SIZE]
            offset += MAX_CHUNK_SIZE

            # m=1 if more chunks follow, m=0 for last chunk
            more = 1 if offset < len(b64_data) else 0

            if first_chunk:
                # First chunk includes all parameters
                dest.write(f"{APC_START}{params},m={more};{chunk}{APC_END}")
                first_chunk = False
            else:
                # Continuation chunk - only m parameter needed
                dest.write(f"{APC_START}m={more};{chunk}{APC_END}")


# Convenience instance for default usage
kitty = KittyRenderer()
