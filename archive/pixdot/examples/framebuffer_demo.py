#!/usr/bin/env python3
"""Framebuffer demo: draw primitives to a bitmap and render as braille.

This demonstrates using pixdot as a framebuffer target. Drawing primitives
are implemented in pure numpy - no external dependencies beyond the core library.

Usage:
    python framebuffer_demo.py

The demo renders:
- A border rectangle
- A filled circle
- Diagonal lines
- A small square
"""

from __future__ import annotations

import numpy as np

from pixdot import render


def draw_circle(fb: np.ndarray, cx: int, cy: int, r: int, filled: bool = True) -> None:
    """Draw a circle on the framebuffer.

    Args:
        fb: 2D numpy array framebuffer to draw on
        cx: Center x coordinate
        cy: Center y coordinate
        r: Radius in pixels
        filled: If True, draw filled circle; if False, draw outline only
    """
    h, w = fb.shape
    y_coords, x_coords = np.ogrid[:h, :w]
    dist_sq = (x_coords - cx) ** 2 + (y_coords - cy) ** 2

    if filled:
        mask = dist_sq <= r ** 2
    else:
        # Outline: distance within 1 pixel of radius
        mask = np.abs(np.sqrt(dist_sq) - r) < 1.5

    fb[mask] = 1.0


def draw_line(fb: np.ndarray, x0: int, y0: int, x1: int, y1: int) -> None:
    """Draw a line using Bresenham's algorithm.

    Args:
        fb: 2D numpy array framebuffer to draw on
        x0, y0: Start point
        x1, y1: End point
    """
    h, w = fb.shape
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy

    x, y = x0, y0
    while True:
        if 0 <= x < w and 0 <= y < h:
            fb[y, x] = 1.0
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def draw_rect(
    fb: np.ndarray,
    x: int,
    y: int,
    w: int,
    h: int,
    filled: bool = False,
) -> None:
    """Draw a rectangle on the framebuffer.

    Args:
        fb: 2D numpy array framebuffer to draw on
        x, y: Top-left corner
        w, h: Width and height
        filled: If True, draw filled rectangle; if False, draw outline only
    """
    fb_h, fb_w = fb.shape

    # Clamp to framebuffer bounds
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(fb_w - 1, x + w - 1)
    y1 = min(fb_h - 1, y + h - 1)

    if filled:
        fb[y0:y1 + 1, x0:x1 + 1] = 1.0
    else:
        # Top and bottom edges
        fb[y0, x0:x1 + 1] = 1.0
        fb[y1, x0:x1 + 1] = 1.0
        # Left and right edges
        fb[y0:y1 + 1, x0] = 1.0
        fb[y0:y1 + 1, x1] = 1.0


def main() -> None:
    """Run the framebuffer demo."""
    # Create framebuffer: 160x80 pixels = 80x20 braille characters
    width, height = 160, 80
    fb = np.zeros((height, width), dtype=np.float32)

    # Draw a border
    draw_rect(fb, 0, 0, width, height, filled=False)

    # Draw a filled circle in the center
    cx, cy = width // 2, height // 2
    draw_circle(fb, cx, cy, r=25, filled=True)

    # Draw a smaller circle outline
    draw_circle(fb, cx, cy, r=35, filled=False)

    # Draw diagonal lines from corners toward center
    margin = 10
    draw_line(fb, margin, margin, cx - 20, cy - 10)
    draw_line(fb, width - margin, margin, cx + 20, cy - 10)
    draw_line(fb, margin, height - margin, cx - 20, cy + 10)
    draw_line(fb, width - margin, height - margin, cx + 20, cy + 10)

    # Draw a small filled rectangle in corner
    draw_rect(fb, 5, 5, 20, 12, filled=True)

    # Render to terminal
    print("Framebuffer Demo")
    print("=" * 40)
    print(render(fb))
    print()
    print(f"Canvas: {width}x{height} pixels -> {width // 2}x{height // 4} characters")


if __name__ == "__main__":
    main()
