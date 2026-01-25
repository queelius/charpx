"""Preprocessing utilities for bitmap images.

Composable transforms that prepare bitmaps for braille rendering.
All functions take and return numpy arrays (H x W, values 0.0-1.0).
"""

from __future__ import annotations

import numpy as np


def auto_contrast(bitmap: np.ndarray) -> np.ndarray:
    """Stretch histogram to full 0-1 range.

    Normalizes the bitmap so the darkest pixel becomes 0.0 and the
    brightest becomes 1.0. This maximizes contrast before thresholding.

    Args:
        bitmap: 2D array of shape (H, W), values 0.0-1.0

    Returns:
        Contrast-stretched bitmap with same shape, values 0.0-1.0
    """
    min_val = bitmap.min()
    max_val = bitmap.max()

    if max_val - min_val < 1e-6:
        # Avoid division by zero for constant images
        return np.full_like(bitmap, 0.5)

    return (bitmap - min_val) / (max_val - min_val)


def floyd_steinberg(bitmap: np.ndarray, threshold: float = 0.5) -> np.ndarray:
    """Apply Floyd-Steinberg dithering for binary output.

    Distributes quantization error to neighboring pixels, creating the
    illusion of grayscale through varying dot density. This is the single
    most effective improvement for binary (braille) output.

    Args:
        bitmap: 2D array of shape (H, W), values 0.0-1.0
        threshold: Threshold for quantization (default 0.5)

    Returns:
        Dithered bitmap with same shape, values are 0.0 or 1.0 only
    """
    # Work on a copy to avoid modifying input
    img = bitmap.astype(np.float64).copy()
    h, w = img.shape

    for y in range(h):
        for x in range(w):
            old_pixel = img[y, x]
            new_pixel = 1.0 if old_pixel > threshold else 0.0
            img[y, x] = new_pixel
            error = old_pixel - new_pixel

            # Distribute error to neighbors using Floyd-Steinberg coefficients:
            #       X   7/16
            # 3/16 5/16 1/16
            if x + 1 < w:
                img[y, x + 1] += error * 7 / 16
            if y + 1 < h:
                if x > 0:
                    img[y + 1, x - 1] += error * 3 / 16
                img[y + 1, x] += error * 5 / 16
                if x + 1 < w:
                    img[y + 1, x + 1] += error * 1 / 16

    return img.astype(np.float32)
