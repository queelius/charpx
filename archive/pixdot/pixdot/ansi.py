"""ANSI color rendering for braille output.

Provides colored braille rendering using ANSI escape codes:
- Grayscale mode: 24-level grayscale using 256-color palette (codes 232-255)
- Truecolor mode: Full 24-bit RGB color

Each braille character gets a foreground color based on the average
brightness/color of its corresponding 2x4 pixel region.
"""

from __future__ import annotations

from typing import Literal

import numpy as np

from .braille import _region_to_braille_code

ColorMode = Literal["none", "grayscale", "truecolor"]

# ANSI escape sequences
RESET = "\033[0m"


def grayscale_fg(level: int) -> str:
    """Generate 256-color grayscale foreground escape code.

    Args:
        level: Grayscale level 0-23 (0=darkest, 23=brightest).
               Maps to ANSI 256-color codes 232-255.

    Returns:
        ANSI escape sequence for grayscale foreground.
    """
    code = 232 + min(23, max(0, level))
    return f"\033[38;5;{code}m"


def truecolor_fg(r: int, g: int, b: int) -> str:
    """Generate 24-bit true color foreground escape code.

    Args:
        r: Red component 0-255.
        g: Green component 0-255.
        b: Blue component 0-255.

    Returns:
        ANSI escape sequence for RGB foreground.
    """
    r = min(255, max(0, r))
    g = min(255, max(0, g))
    b = min(255, max(0, b))
    return f"\033[38;2;{r};{g};{b}m"


def render_ansi(
    bitmap: np.ndarray,
    threshold: float | None = 0.5,
    color_mode: ColorMode = "grayscale",
    colors: np.ndarray | None = None,
) -> str:
    """Render bitmap to ANSI-colored braille.

    Args:
        bitmap: 2D grayscale array (H, W), values 0.0-1.0.
        threshold: Dot activation threshold. If None, auto-detect from bitmap mean.
        color_mode: "none" for plain braille, "grayscale" for 24-level grayscale,
                    or "truecolor" for full 24-bit RGB.
        colors: Optional RGB array (H, W, 3) with values 0.0-1.0.
                If None, uses grayscale values for color.

    Returns:
        Multi-line string with ANSI color codes.

    Example:
        >>> import numpy as np
        >>> from pixdot import render_ansi
        >>> bitmap = np.linspace(0, 1, 80).reshape(1, -1).repeat(8, axis=0)
        >>> print(render_ansi(bitmap, color_mode="grayscale"))
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

    if color_mode == "none":
        # Delegate to plain render
        from .braille import render

        return render(bitmap, threshold)

    if threshold is None:
        threshold = max(0.1, min(0.9, float(bitmap.mean())))

    h, w = bitmap.shape
    rows = []

    for cy in range(0, h, 4):
        row_parts = []
        for cx in range(0, w, 2):
            # Extract 2x4 region for braille pattern
            region = np.zeros((4, 2), dtype=np.float32)
            region_h = min(4, h - cy)
            region_w = min(2, w - cx)
            region[:region_h, :region_w] = bitmap[cy : cy + region_h, cx : cx + region_w]

            # Encode to braille codepoint
            code = _region_to_braille_code(region, threshold)
            braille_char = chr(0x2800 + code)

            # Compute color for this region
            if color_mode == "grayscale":
                # Average brightness of the region
                avg_brightness = region[:region_h, :region_w].mean()
                level = int(avg_brightness * 23.999)  # 0-23
                color_code = grayscale_fg(level)
            else:  # truecolor
                if colors is not None:
                    # Extract color region and average
                    color_region = colors[cy : cy + region_h, cx : cx + region_w]
                    avg_color = color_region.mean(axis=(0, 1))
                    r = int(avg_color[0] * 255.999)
                    g = int(avg_color[1] * 255.999)
                    b = int(avg_color[2] * 255.999)
                else:
                    # Use grayscale value for all channels
                    avg_brightness = region[:region_h, :region_w].mean()
                    gray = int(avg_brightness * 255.999)
                    r = g = b = gray
                color_code = truecolor_fg(r, g, b)

            row_parts.append(f"{color_code}{braille_char}")

        # Add reset at end of row
        rows.append("".join(row_parts) + RESET)

    return "\n".join(rows)
