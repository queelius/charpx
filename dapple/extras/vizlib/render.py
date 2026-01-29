"""Shared renderer resolution and terminal size helpers."""

from __future__ import annotations

import shutil

from dapple import braille, quadrants, sextants, ascii, sixel, kitty
from dapple.renderers import Renderer

RENDERERS: dict[str, Renderer] = {
    "braille": braille,
    "quadrants": quadrants,
    "sextants": sextants,
    "ascii": ascii,
    "sixel": sixel,
    "kitty": kitty,
}


def get_renderer(name: str) -> Renderer:
    """Get a renderer by name, configured for chart output.

    Args:
        name: Renderer name (braille, quadrants, sextants, ascii, sixel, kitty).

    Returns:
        Configured Renderer instance.

    Raises:
        ValueError: If the renderer name is unknown.
    """
    renderer = RENDERERS.get(name)
    if renderer is None:
        valid = ", ".join(sorted(RENDERERS.keys()))
        raise ValueError(f"Unknown renderer: {name}. Available: {valid}")

    if name == "braille":
        return renderer(threshold=0.2, color_mode="truecolor")
    elif name in ("quadrants", "sextants"):
        return renderer(true_color=True)
    return renderer()


def get_terminal_size() -> tuple[int, int]:
    """Return (columns, lines) of the terminal."""
    return shutil.get_terminal_size(fallback=(80, 24))


def pixel_dimensions(
    renderer: Renderer,
    char_width: int,
    char_height: int,
) -> tuple[int, int]:
    """Convert character dimensions to pixel dimensions for a renderer.

    Args:
        renderer: The dapple renderer.
        char_width: Width in terminal characters.
        char_height: Height in terminal characters.

    Returns:
        (pixel_width, pixel_height) tuple.
    """
    return (char_width * renderer.cell_width, char_height * renderer.cell_height)
