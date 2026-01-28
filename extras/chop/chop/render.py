"""Terminal rendering utilities for chop CLI using dapple."""

from __future__ import annotations

import shutil
import sys
from typing import TYPE_CHECKING

from PIL import Image

from dapple import braille, quadrants, sextants, ascii, sixel, kitty
from dapple.auto import detect_kitty, detect_sixel
from dapple.canvas import Canvas
from dapple.renderers import Renderer

from chop.pipeline import image_to_arrays

if TYPE_CHECKING:
    pass

# Available renderers
RENDERERS: dict[str, Renderer] = {
    "braille": braille,
    "quadrants": quadrants,
    "sextants": sextants,
    "ascii": ascii,
    "sixel": sixel,
    "kitty": kitty,
}


def render_to_terminal(
    image: Image.Image,
    renderer_name: str = "braille",
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Render image to terminal.

    Args:
        image: PIL Image to render
        renderer_name: Renderer to use
        width: Output width in characters (auto-detect if None)
        height: Output height in characters (auto-detect if None)
    """
    if renderer_name not in RENDERERS:
        raise ValueError(f"Unknown renderer: {renderer_name}. Available: {list(RENDERERS.keys())}")

    renderer = RENDERERS[renderer_name]

    # Auto-detect terminal size
    term = shutil.get_terminal_size(fallback=(80, 24))
    char_width = width or term.columns
    char_height = height or (term.lines - 2)

    # Calculate pixel dimensions for renderer
    pixel_width = char_width * renderer.cell_width
    pixel_height = char_height * renderer.cell_height

    # Resize image to fit
    img_w, img_h = image.size
    scale = min(pixel_width / img_w, pixel_height / img_h)

    if scale < 1:
        new_size = (int(img_w * scale), int(img_h * scale))
        resized = image.resize(new_size, Image.Resampling.LANCZOS)
    else:
        resized = image

    # Convert to bitmap and colors
    bitmap, colors = image_to_arrays(resized)

    # Configure renderer
    if renderer_name == "braille":
        configured = renderer(threshold=0.5, color_mode="truecolor")
    elif renderer_name in ("quadrants", "sextants"):
        configured = renderer(true_color=True)
    else:
        configured = renderer()

    # Render
    canvas = Canvas(bitmap, colors=colors)
    canvas.out(configured)
    print()  # Newline after output


def auto_detect_renderer() -> str:
    """Auto-detect best renderer for current terminal.

    Detection order (best to fallback):
        1. kitty - Kitty graphics protocol (kitty, ghostty)
        2. sixel - Sixel graphics (xterm, mlterm, foot, wezterm)
        3. sextants - Unicode sextant blocks (best fallback)

    Returns:
        Renderer name string.
    """
    if detect_kitty():
        return "kitty"
    elif detect_sixel():
        return "sixel"
    else:
        return "sextants"  # Best fallback for color/resolution
