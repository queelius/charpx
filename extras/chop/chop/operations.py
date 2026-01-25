"""Image operations for chop CLI.

Each operation takes a PIL Image and returns a modified PIL Image.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from charpx import preprocess

if TYPE_CHECKING:
    pass


def parse_size(size_str: str, current_size: tuple[int, int]) -> tuple[int, int]:
    """Parse size specification string.

    Supports:
        - "50%" - scale by percentage
        - "800x600" - exact dimensions
        - "w800" - width only, maintain aspect
        - "h600" - height only, maintain aspect

    Args:
        size_str: Size specification
        current_size: Current (width, height)

    Returns:
        (width, height) tuple
    """
    w, h = current_size

    # Percentage
    if size_str.endswith("%"):
        pct = float(size_str[:-1]) / 100.0
        return (int(w * pct), int(h * pct))

    # Width x Height
    if "x" in size_str:
        parts = size_str.lower().split("x")
        return (int(parts[0]), int(parts[1]))

    # Width only
    if size_str.lower().startswith("w"):
        new_w = int(size_str[1:])
        new_h = int(h * new_w / w)
        return (new_w, new_h)

    # Height only
    if size_str.lower().startswith("h"):
        new_h = int(size_str[1:])
        new_w = int(w * new_h / h)
        return (new_w, new_h)

    raise ValueError(f"Invalid size format: {size_str}")


def parse_crop(args: list[str], current_size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Parse crop arguments.

    Supports:
        - x y w h (pixels)
        - x% y% w% h% (percentages)

    Args:
        args: List of 4 arguments
        current_size: Current (width, height)

    Returns:
        (x, y, width, height) tuple in pixels
    """
    if len(args) != 4:
        raise ValueError("crop requires 4 arguments: x y width height")

    w, h = current_size
    result = []

    for i, arg in enumerate(args):
        if arg.endswith("%"):
            pct = float(arg[:-1]) / 100.0
            # x and width use image width, y and height use image height
            if i % 2 == 0:  # x or width
                result.append(int(w * pct))
            else:  # y or height
                result.append(int(h * pct))
        else:
            result.append(int(arg))

    return tuple(result)


def op_resize(image: Image.Image, size_str: str) -> Image.Image:
    """Resize image.

    Args:
        image: Input image
        size_str: Size specification (50%, 800x600, w800, h600)

    Returns:
        Resized image
    """
    new_size = parse_size(size_str, image.size)
    return image.resize(new_size, Image.Resampling.LANCZOS)


def op_crop(image: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
    """Crop image.

    Args:
        image: Input image
        x, y: Top-left corner
        width, height: Crop dimensions

    Returns:
        Cropped image
    """
    return image.crop((x, y, x + width, y + height))


def op_rotate(image: Image.Image, degrees: float) -> Image.Image:
    """Rotate image.

    Args:
        image: Input image
        degrees: Rotation angle (counter-clockwise)

    Returns:
        Rotated image
    """
    # Expand=True resizes to fit rotated content
    return image.rotate(degrees, expand=True, resample=Image.Resampling.BICUBIC)


def op_flip(image: Image.Image, direction: str) -> Image.Image:
    """Flip image horizontally or vertically.

    Args:
        image: Input image
        direction: "h" for horizontal, "v" for vertical

    Returns:
        Flipped image
    """
    if direction.lower() == "h":
        return image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    elif direction.lower() == "v":
        return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    else:
        raise ValueError(f"direction must be 'h' or 'v', got {direction!r}")


def _apply_preprocess(
    image: Image.Image,
    func,
    **kwargs,
) -> Image.Image:
    """Apply a charpx preprocess function to a PIL Image.

    Args:
        image: Input image (RGBA)
        func: Preprocess function that takes bitmap array
        **kwargs: Arguments to pass to func

    Returns:
        Processed image
    """
    # Convert to grayscale bitmap
    gray = image.convert("L")
    bitmap = np.array(gray, dtype=np.float32) / 255.0

    # Apply function
    result = func(bitmap, **kwargs)

    # Convert back to image
    result_uint8 = (np.clip(result, 0, 1) * 255).astype(np.uint8)
    result_image = Image.fromarray(result_uint8, mode="L")

    # Preserve color if original was color
    if image.mode == "RGBA":
        # Use processed as luminance, preserve original color hue
        original_rgb = np.array(image.convert("RGB"), dtype=np.float32) / 255.0
        original_lum = (
            0.299 * original_rgb[:, :, 0]
            + 0.587 * original_rgb[:, :, 1]
            + 0.114 * original_rgb[:, :, 2]
        )

        # Avoid division by zero
        original_lum = np.maximum(original_lum, 1e-6)

        # Scale colors by luminance ratio
        scale = result / original_lum
        new_rgb = original_rgb * scale[:, :, np.newaxis]
        new_rgb = np.clip(new_rgb, 0, 1)

        # Convert back
        new_rgb_uint8 = (new_rgb * 255).astype(np.uint8)
        return Image.fromarray(new_rgb_uint8, mode="RGB").convert("RGBA")

    return result_image.convert("RGBA")


def op_dither(image: Image.Image, threshold: float = 0.5) -> Image.Image:
    """Apply Floyd-Steinberg dithering.

    Args:
        image: Input image
        threshold: Dithering threshold (0.0-1.0)

    Returns:
        Dithered image
    """
    return _apply_preprocess(image, preprocess.floyd_steinberg, threshold=threshold)


def op_invert(image: Image.Image) -> Image.Image:
    """Invert image.

    Args:
        image: Input image

    Returns:
        Inverted image
    """
    return _apply_preprocess(image, preprocess.invert)


def op_sharpen(image: Image.Image, strength: float = 1.0) -> Image.Image:
    """Sharpen image.

    Args:
        image: Input image
        strength: Sharpening strength

    Returns:
        Sharpened image
    """
    return _apply_preprocess(image, preprocess.sharpen, strength=strength)


def op_contrast(image: Image.Image) -> Image.Image:
    """Auto-contrast image.

    Args:
        image: Input image

    Returns:
        Contrast-stretched image
    """
    return _apply_preprocess(image, preprocess.auto_contrast)


def op_gamma(image: Image.Image, gamma: float) -> Image.Image:
    """Apply gamma correction.

    Args:
        image: Input image
        gamma: Gamma value (>1 darkens, <1 brightens)

    Returns:
        Gamma-corrected image
    """
    return _apply_preprocess(image, preprocess.gamma_correct, gamma=gamma)


def op_threshold(image: Image.Image, level: float) -> Image.Image:
    """Apply binary threshold.

    Args:
        image: Input image
        level: Threshold level (0.0-1.0)

    Returns:
        Thresholded image
    """
    return _apply_preprocess(image, preprocess.threshold, level=level)
