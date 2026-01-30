"""Shared utilities for dapple extras.

Common renderer selection and preprocessing logic used across
imgcat, pdfcat, mdcat, and other extras.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

    from dapple.renderers import Renderer


def get_renderer(
    name: str,
    *,
    grayscale: bool = False,
    no_color: bool = False,
) -> Renderer:
    """Get a renderer by name with appropriate color configuration.

    Args:
        name: Renderer name ("auto", "braille", "quadrants", "sextants",
              "ascii", "sixel", "kitty", "fingerprint").
        grayscale: Force grayscale output.
        no_color: Disable color output entirely.

    Returns:
        Configured Renderer instance.

    Raises:
        ValueError: If name is not a recognized renderer.
    """
    from dapple import (
        ascii,
        braille,
        fingerprint,
        kitty,
        quadrants,
        sextants,
        sixel,
    )
    from dapple.auto import auto_renderer

    if name == "auto":
        return auto_renderer(
            prefer_color=not grayscale,
            plain=no_color,
        )

    renderers = {
        "braille": braille,
        "quadrants": quadrants,
        "sextants": sextants,
        "ascii": ascii,
        "sixel": sixel,
        "kitty": kitty,
        "fingerprint": fingerprint,
    }

    renderer = renderers.get(name)
    if renderer is None:
        raise ValueError(f"Unknown renderer: {name}")

    if name == "braille":
        if no_color:
            renderer = braille(color_mode="none")
        elif grayscale:
            renderer = braille(color_mode="grayscale")
        else:
            renderer = braille(color_mode="truecolor")
    elif name in ("quadrants", "sextants"):
        if grayscale:
            if name == "quadrants":
                renderer = quadrants(grayscale=True)
            else:
                renderer = sextants(grayscale=True)

    return renderer


def apply_preprocessing(
    bitmap: NDArray[np.floating],
    *,
    contrast: bool = False,
    dither: bool = False,
    invert: bool = False,
) -> NDArray[np.floating]:
    """Apply preprocessing chain to a bitmap.

    Args:
        bitmap: 2D array of shape (H, W), values 0.0-1.0.
        contrast: Apply auto-contrast stretching.
        dither: Apply Floyd-Steinberg dithering.
        invert: Invert brightness values.

    Returns:
        Modified bitmap (new array if any transforms applied, otherwise input).
    """
    from dapple.preprocess import (
        auto_contrast,
        floyd_steinberg,
        invert as invert_fn,
    )

    if contrast:
        bitmap = auto_contrast(bitmap)
    if dither:
        bitmap = floyd_steinberg(bitmap)
    if invert:
        bitmap = invert_fn(bitmap)

    return bitmap
