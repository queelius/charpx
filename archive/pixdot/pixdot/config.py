"""Configuration for bitmap-to-braille rendering.

Provides RenderConfig dataclass and named presets for common rendering scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict


@dataclass(frozen=True)
class RenderConfig:
    """Configuration for bitmap-to-braille rendering.

    Attributes:
        width_chars: Target width in terminal characters.
        cell_aspect: Width/height ratio of terminal cell (typically 0.5).
        invert: Flip black/white (True for dark terminal, False for light).
        dither: Apply Floyd-Steinberg dithering for better grayscale.
        dither_threshold: Threshold for dithering quantization.
        auto_contrast: Stretch histogram to full 0-1 range before rendering.
        threshold: Brightness threshold for dot activation.
                   None = auto-detect from bitmap mean.
        color_mode: Color rendering mode. None/"none" for plain braille,
                    "grayscale" for 24-level ANSI grayscale,
                    "truecolor" for 24-bit RGB color.
    """

    width_chars: int = 80
    cell_aspect: float = 0.5
    invert: bool = True
    dither: bool = True
    dither_threshold: float = 0.5
    auto_contrast: bool = False
    threshold: float | None = None
    color_mode: str | None = None

    def with_width(self, width_chars: int) -> RenderConfig:
        """Return a copy with a different width."""
        return replace(self, width_chars=width_chars)

    def with_dither(self, dither: bool) -> RenderConfig:
        """Return a copy with dithering enabled/disabled."""
        return replace(self, dither=dither)

    def with_invert(self, invert: bool) -> RenderConfig:
        """Return a copy with inversion enabled/disabled."""
        return replace(self, invert=invert)

    def with_color(self, color_mode: str | None) -> RenderConfig:
        """Return a copy with color mode set.

        Args:
            color_mode: None/"none" for plain, "grayscale", or "truecolor".

        Returns:
            New RenderConfig with color mode applied.
        """
        return replace(self, color_mode=color_mode)


# Named presets for common use cases
PRESETS: Dict[str, RenderConfig] = {
    "default": RenderConfig(),
    "dark_terminal": RenderConfig(invert=True),
    "light_terminal": RenderConfig(invert=False),
    "high_detail": RenderConfig(width_chars=120, dither=True),
    "compact": RenderConfig(width_chars=40),
    "no_dither": RenderConfig(dither=False, threshold=0.5),
    # Color presets - dithering disabled since color provides grayscale info
    "grayscale": RenderConfig(color_mode="grayscale", dither=False),
    "truecolor": RenderConfig(color_mode="truecolor", dither=False),
}


def get_preset(name: str) -> RenderConfig:
    """Get a named configuration preset.

    Args:
        name: Preset name. One of: default, dark_terminal, light_terminal,
              high_detail, compact, no_dither, grayscale, truecolor.

    Returns:
        RenderConfig instance for the named preset.

    Raises:
        KeyError: If preset name is not found.
    """
    if name not in PRESETS:
        available = ", ".join(sorted(PRESETS.keys()))
        raise KeyError(f"Unknown preset '{name}'. Available: {available}")
    return PRESETS[name]
