"""Color palette and ANSI helpers for vizlib charts."""

from __future__ import annotations

# Named colors (RGB 0-1) — bright, saturated for terminal visibility
NAMED_COLORS: dict[str, tuple[float, float, float]] = {
    "cyan": (0.0, 0.8, 1.0),
    "red": (1.0, 0.2, 0.2),
    "green": (0.2, 1.0, 0.2),
    "yellow": (1.0, 1.0, 0.0),
    "magenta": (1.0, 0.0, 1.0),
    "orange": (1.0, 0.6, 0.0),
    "blue": (0.0, 0.5, 1.0),
    "pink": (1.0, 0.4, 0.8),
    "white": (1.0, 1.0, 1.0),
    "gray": (0.5, 0.5, 0.5),
}

# Auto-cycling palette for multi-series charts
COLOR_PALETTE: list[tuple[float, float, float]] = [
    NAMED_COLORS["green"],   # green first — brighter on dark terminals than cyan
    NAMED_COLORS["cyan"],
    NAMED_COLORS["red"],
    NAMED_COLORS["yellow"],
    NAMED_COLORS["magenta"],
    NAMED_COLORS["orange"],
    NAMED_COLORS["blue"],
    NAMED_COLORS["pink"],
]


def parse_color(color_str: str) -> tuple[float, float, float]:
    """Parse a color name or #RRGGBB hex string.

    Args:
        color_str: Color name (e.g. "cyan") or hex (e.g. "#ff0000").

    Returns:
        (R, G, B) tuple with values 0.0-1.0.

    Raises:
        ValueError: If the color string is not recognized.
    """
    if color_str.startswith("#"):
        hex_str = color_str[1:]
        if len(hex_str) == 3:
            hex_str = "".join(c * 2 for c in hex_str)
        if len(hex_str) != 6:
            raise ValueError(f"Invalid hex color: {color_str}")
        r = int(hex_str[0:2], 16) / 255
        g = int(hex_str[2:4], 16) / 255
        b = int(hex_str[4:6], 16) / 255
        return (r, g, b)

    color_lower = color_str.lower()
    if color_lower not in NAMED_COLORS:
        valid = ", ".join(sorted(NAMED_COLORS.keys()))
        raise ValueError(f"Unknown color '{color_str}'. Valid colors: {valid}")
    return NAMED_COLORS[color_lower]


def ansi_fg(r: float, g: float, b: float) -> str:
    """Return ANSI escape for 24-bit foreground color."""
    return f"\033[38;2;{int(r*255)};{int(g*255)};{int(b*255)}m"


def ansi_reset() -> str:
    """Return ANSI reset escape."""
    return "\033[0m"
