"""Resize algorithms for bitmap images.

Pure numpy implementations for downscaling and upscaling bitmaps
without requiring PIL or other image libraries.
"""

from __future__ import annotations

import numpy as np


def resize_bitmap(
    bitmap: np.ndarray,
    target_width: int,
    target_height: int,
    method: str = "area",
) -> np.ndarray:
    """Resize bitmap with quality preservation.

    Pure numpy implementation supporting multiple resize methods.
    Automatically adjusts output dimensions to be braille-compatible
    (height % 4 == 0, width % 2 == 0).

    Args:
        bitmap: 2D array of shape (H, W), values 0.0-1.0.
        target_width: Desired output width in pixels.
        target_height: Desired output height in pixels.
        method: Resize method. One of:
            - "area": Area-weighted averaging (best for downscaling)
            - "nearest": Nearest neighbor (fast, pixelated)
            - "bilinear": Bilinear interpolation (smooth, good for upscaling)

    Returns:
        Resized bitmap with braille-compatible dimensions.

    Raises:
        ValueError: If method is not recognized.
    """
    if bitmap.ndim != 2:
        raise ValueError(f"bitmap must be 2D, got shape {bitmap.shape}")

    # Ensure braille-compatible dimensions
    target_height = max(4, (target_height // 4) * 4)
    target_width = max(2, (target_width // 2) * 2)

    if method == "area":
        return _resize_area(bitmap, target_width, target_height)
    elif method == "nearest":
        return _resize_nearest(bitmap, target_width, target_height)
    elif method == "bilinear":
        return _resize_bilinear(bitmap, target_width, target_height)
    else:
        raise ValueError(f"Unknown method '{method}'. Use: area, nearest, bilinear")


def _resize_area(
    bitmap: np.ndarray,
    target_width: int,
    target_height: int,
) -> np.ndarray:
    """Resize using area-weighted averaging (best for downscaling).

    This properly handles the case where multiple source pixels
    contribute to each output pixel, weighting by overlap area.
    """
    src_h, src_w = bitmap.shape

    # Scale factors
    scale_y = src_h / target_height
    scale_x = src_w / target_width

    # If upscaling, fall back to bilinear
    if scale_x < 1.0 or scale_y < 1.0:
        return _resize_bilinear(bitmap, target_width, target_height)

    result = np.zeros((target_height, target_width), dtype=np.float32)

    # Vectorized computation using meshgrid
    y_indices = np.arange(target_height)
    x_indices = np.arange(target_width)

    # Source coordinates for each target pixel
    y0_float = y_indices * scale_y
    y1_float = (y_indices + 1) * scale_y
    x0_float = x_indices * scale_x
    x1_float = (x_indices + 1) * scale_x

    # Integer bounds
    y0 = np.floor(y0_float).astype(int)
    y1 = np.minimum(np.ceil(y1_float).astype(int), src_h)
    x0 = np.floor(x0_float).astype(int)
    x1 = np.minimum(np.ceil(x1_float).astype(int), src_w)

    # For each target pixel, compute weighted average of source region
    for ty in range(target_height):
        for tx in range(target_width):
            sy0, sy1 = y0[ty], y1[ty]
            sx0, sx1 = x0[tx], x1[tx]

            if sy1 > sy0 and sx1 > sx0:
                # Simple area average when region is large enough
                region = bitmap[sy0:sy1, sx0:sx1]
                result[ty, tx] = region.mean()
            else:
                # Fall back to direct sampling
                result[ty, tx] = bitmap[min(sy0, src_h - 1), min(sx0, src_w - 1)]

    return result


def _resize_nearest(
    bitmap: np.ndarray,
    target_width: int,
    target_height: int,
) -> np.ndarray:
    """Resize using nearest neighbor (fast but pixelated)."""
    src_h, src_w = bitmap.shape

    # Compute source indices for each target pixel
    y_indices = (np.arange(target_height) * src_h / target_height).astype(int)
    x_indices = (np.arange(target_width) * src_w / target_width).astype(int)

    # Clip to valid range
    y_indices = np.clip(y_indices, 0, src_h - 1)
    x_indices = np.clip(x_indices, 0, src_w - 1)

    # Use advanced indexing
    return bitmap[y_indices[:, np.newaxis], x_indices[np.newaxis, :]].astype(np.float32)


def _resize_bilinear(
    bitmap: np.ndarray,
    target_width: int,
    target_height: int,
) -> np.ndarray:
    """Resize using bilinear interpolation (smooth, good for upscaling)."""
    src_h, src_w = bitmap.shape

    # Create coordinate grids for target
    y_coords = np.linspace(0, src_h - 1, target_height)
    x_coords = np.linspace(0, src_w - 1, target_width)
    x_grid, y_grid = np.meshgrid(x_coords, y_coords)

    # Integer parts and fractional parts
    x0 = np.floor(x_grid).astype(int)
    y0 = np.floor(y_grid).astype(int)
    x1 = np.minimum(x0 + 1, src_w - 1)
    y1 = np.minimum(y0 + 1, src_h - 1)

    # Fractional parts for interpolation weights
    xf = x_grid - x0
    yf = y_grid - y0

    # Bilinear interpolation
    top_left = bitmap[y0, x0]
    top_right = bitmap[y0, x1]
    bottom_left = bitmap[y1, x0]
    bottom_right = bitmap[y1, x1]

    top = top_left * (1 - xf) + top_right * xf
    bottom = bottom_left * (1 - xf) + bottom_right * xf
    result = top * (1 - yf) + bottom * yf

    return result.astype(np.float32)


def compute_target_dimensions(
    source_width: int,
    source_height: int,
    width_chars: int,
    cell_aspect: float = 0.5,
) -> tuple[int, int]:
    """Compute braille-compatible target dimensions preserving aspect ratio.

    Args:
        source_width: Original image width in pixels.
        source_height: Original image height in pixels.
        width_chars: Target width in terminal characters.
        cell_aspect: Width/height ratio of terminal cell (typically 0.5).

    Returns:
        Tuple of (target_width, target_height) in pixels,
        where target_height is divisible by 4 and target_width by 2.
    """
    # Each braille character is 2 pixels wide, 4 pixels tall
    pixels_per_char_w = 2
    pixels_per_char_h = 4

    target_w = width_chars * pixels_per_char_w

    # Compute height preserving aspect ratio, accounting for cell aspect
    aspect_ratio = source_width / source_height
    target_h = int(target_w / aspect_ratio * cell_aspect * (pixels_per_char_h / pixels_per_char_w))

    # Ensure braille-compatible dimensions
    target_h = max(4, (target_h // 4) * 4)
    target_w = max(2, (target_w // 2) * 2)

    return target_w, target_h
