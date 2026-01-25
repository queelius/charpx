"""Image operations for chop CLI.

Each operation takes a PIL Image and returns a modified PIL Image.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageColor

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


# =============================================================================
# Padding and border operations
# =============================================================================


def _parse_color(color: str) -> tuple[int, int, int, int]:
    """Parse color string to RGBA tuple.

    Args:
        color: Color name, hex (#RGB, #RRGGBB), or "transparent"

    Returns:
        (R, G, B, A) tuple with values 0-255
    """
    if color.lower() == "transparent":
        return (0, 0, 0, 0)

    try:
        rgb = ImageColor.getrgb(color)
        if len(rgb) == 3:
            return (*rgb, 255)
        return rgb
    except ValueError:
        raise ValueError(f"Invalid color: {color}")


def op_pad(
    image: Image.Image,
    top: int,
    right: int | None = None,
    bottom: int | None = None,
    left: int | None = None,
    color: str = "transparent",
) -> Image.Image:
    """Add padding around image.

    Args:
        image: Input image
        top: Top padding (or uniform if only arg)
        right: Right padding (or horizontal if only top+right given)
        bottom: Bottom padding
        left: Left padding
        color: Padding color (name, hex, or "transparent")

    Supports:
        - pad(10): uniform 10px padding
        - pad(10, 20): 10 top/bottom, 20 left/right
        - pad(10, 20, 30, 40): top, right, bottom, left (CSS order)

    Returns:
        Padded image
    """
    # Parse padding values (CSS-style)
    if right is None:
        # Uniform padding
        t = r = b = l = top
    elif bottom is None:
        # Vertical, horizontal
        t = b = top
        r = l = right
    else:
        # All four specified
        t, r, b, l = top, right, bottom, left or right

    w, h = image.size
    new_w = w + l + r
    new_h = h + t + b

    fill_color = _parse_color(color)
    result = Image.new("RGBA", (new_w, new_h), fill_color)
    result.paste(image, (l, t))

    return result


def op_border(
    image: Image.Image,
    width: int,
    color: str = "black",
) -> Image.Image:
    """Add colored border around image.

    Args:
        image: Input image
        width: Border width in pixels
        color: Border color (name or hex)

    Returns:
        Image with border
    """
    fill_color = _parse_color(color)
    w, h = image.size
    new_w = w + width * 2
    new_h = h + width * 2

    result = Image.new("RGBA", (new_w, new_h), fill_color)
    result.paste(image, (width, width))

    return result


# =============================================================================
# Fit and fill operations
# =============================================================================


def op_fit(image: Image.Image, size_str: str) -> Image.Image:
    """Fit image within bounds, preserving aspect ratio.

    The image is scaled down (if needed) to fit entirely within
    the specified dimensions. The result may be smaller than
    the target in one dimension.

    Args:
        image: Input image
        size_str: Target size as "WxH" (e.g., "800x600")

    Returns:
        Fitted image (may be smaller than target in one dimension)
    """
    if "x" not in size_str.lower():
        raise ValueError(f"fit requires WxH format, got: {size_str}")

    parts = size_str.lower().split("x")
    target_w, target_h = int(parts[0]), int(parts[1])
    w, h = image.size

    # Calculate scale to fit within bounds
    scale = min(target_w / w, target_h / h)
    new_w = int(w * scale)
    new_h = int(h * scale)

    return image.resize((new_w, new_h), Image.Resampling.LANCZOS)


def op_fill(image: Image.Image, size_str: str) -> Image.Image:
    """Fill bounds completely, cropping excess (center crop).

    The image is scaled to completely fill the specified dimensions,
    then center-cropped to exact size.

    Args:
        image: Input image
        size_str: Target size as "WxH" (e.g., "800x600")

    Returns:
        Filled and cropped image (exact target size)
    """
    if "x" not in size_str.lower():
        raise ValueError(f"fill requires WxH format, got: {size_str}")

    parts = size_str.lower().split("x")
    target_w, target_h = int(parts[0]), int(parts[1])
    w, h = image.size

    # Calculate scale to fill bounds completely
    scale = max(target_w / w, target_h / h)
    scaled_w = int(w * scale)
    scaled_h = int(h * scale)

    # Scale up
    scaled = image.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)

    # Center crop to exact target size
    left = (scaled_w - target_w) // 2
    top = (scaled_h - target_h) // 2
    return scaled.crop((left, top, left + target_w, top + target_h))


# =============================================================================
# Composition operations
# =============================================================================


def _align_offset(
    size1: int, size2: int, align: str, is_horizontal: bool
) -> tuple[int, int]:
    """Calculate offsets for aligning two dimensions.

    Args:
        size1: First size (target)
        size2: Second size (to align)
        align: Alignment string (top/center/bottom or left/center/right)
        is_horizontal: True for horizontal alignment (left/center/right)

    Returns:
        (offset1, offset2) - offsets for each image
    """
    if size1 == size2:
        return (0, 0)

    max_size = max(size1, size2)

    if is_horizontal:
        # left/center/right
        if align == "left":
            return (0, 0)
        elif align == "right":
            return (max_size - size1, max_size - size2)
        else:  # center
            return ((max_size - size1) // 2, (max_size - size2) // 2)
    else:
        # top/center/bottom
        if align == "top":
            return (0, 0)
        elif align == "bottom":
            return (max_size - size1, max_size - size2)
        else:  # center
            return ((max_size - size1) // 2, (max_size - size2) // 2)


def op_hstack(
    image: Image.Image, other: Image.Image, align: str = "center"
) -> Image.Image:
    """Stack two images horizontally (side by side).

    Args:
        image: Left image
        other: Right image
        align: Vertical alignment (top, center, bottom)

    Returns:
        Combined image
    """
    w1, h1 = image.size
    w2, h2 = other.size

    # Calculate output dimensions
    out_width = w1 + w2
    out_height = max(h1, h2)

    # Calculate vertical offsets for alignment
    offset1, offset2 = _align_offset(h1, h2, align, is_horizontal=False)

    # Create output image with transparency
    result = Image.new("RGBA", (out_width, out_height), (0, 0, 0, 0))

    # Paste images
    result.paste(image, (0, offset1))
    result.paste(other, (w1, offset2))

    return result


def op_vstack(
    image: Image.Image, other: Image.Image, align: str = "center"
) -> Image.Image:
    """Stack two images vertically (one above the other).

    Args:
        image: Top image
        other: Bottom image
        align: Horizontal alignment (left, center, right)

    Returns:
        Combined image
    """
    w1, h1 = image.size
    w2, h2 = other.size

    # Calculate output dimensions
    out_width = max(w1, w2)
    out_height = h1 + h2

    # Calculate horizontal offsets for alignment
    offset1, offset2 = _align_offset(w1, w2, align, is_horizontal=True)

    # Create output image with transparency
    result = Image.new("RGBA", (out_width, out_height), (0, 0, 0, 0))

    # Paste images
    result.paste(image, (offset1, 0))
    result.paste(other, (offset2, h1))

    return result


def op_overlay(
    image: Image.Image,
    overlay: Image.Image,
    x: int,
    y: int,
    opacity: float = 1.0,
    paste: bool = False,
) -> Image.Image:
    """Overlay an image on top of another.

    Args:
        image: Base image
        overlay: Image to overlay
        x: X position for overlay
        y: Y position for overlay
        opacity: Opacity multiplier (0.0-1.0)
        paste: If True, hard paste without alpha blending

    Returns:
        Combined image
    """
    result = image.copy()

    # Apply opacity if needed
    if opacity < 1.0 and overlay.mode == "RGBA":
        # Modify alpha channel
        r, g, b, a = overlay.split()
        a = a.point(lambda p: int(p * opacity))
        overlay = Image.merge("RGBA", (r, g, b, a))

    if paste:
        # Hard paste (no blending)
        result.paste(overlay, (x, y))
    else:
        # Alpha composite
        # Create a full-size overlay layer
        layer = Image.new("RGBA", result.size, (0, 0, 0, 0))
        layer.paste(overlay, (x, y))
        result = Image.alpha_composite(result, layer)

    return result


def op_tile(image: Image.Image, cols: int, rows: int) -> Image.Image:
    """Tile an image NxM times.

    Args:
        image: Image to tile
        cols: Number of columns
        rows: Number of rows

    Returns:
        Tiled image
    """
    w, h = image.size
    result = Image.new("RGBA", (w * cols, h * rows), (0, 0, 0, 0))

    for row in range(rows):
        for col in range(cols):
            result.paste(image, (col * w, row * h))

    return result


def op_grid(
    image: Image.Image, others: list[Image.Image], cols: int = 2
) -> Image.Image:
    """Arrange multiple images in a grid.

    The first image determines the cell size. All other images are
    resized to match.

    Args:
        image: First image (determines cell size)
        others: Additional images
        cols: Number of columns

    Returns:
        Grid image
    """
    all_images = [image] + others
    cell_w, cell_h = image.size

    # Calculate grid dimensions
    total = len(all_images)
    rows = (total + cols - 1) // cols  # Ceiling division

    result = Image.new("RGBA", (cell_w * cols, cell_h * rows), (0, 0, 0, 0))

    for i, img in enumerate(all_images):
        # Resize to cell size if needed
        if img.size != (cell_w, cell_h):
            img = img.resize((cell_w, cell_h), Image.Resampling.LANCZOS)

        row = i // cols
        col = i % cols
        result.paste(img, (col * cell_w, row * cell_h))

    return result


# =============================================================================
# Operations Registry
# =============================================================================


# Map operation names to their functions
# Note: Composition operations (hstack, vstack, overlay, grid) require
# additional images to be loaded, so they're handled specially in apply_operation()
OPERATIONS: dict[str, callable] = {
    # Geometric
    "resize": op_resize,
    "crop": op_crop,
    "rotate": op_rotate,
    "flip": op_flip,
    "fit": op_fit,
    "fill": op_fill,
    # Padding/border
    "pad": op_pad,
    "border": op_border,
    # Composition
    "tile": op_tile,
}


def apply_operation(
    image: Image.Image, op_name: str, *args, **kwargs
) -> Image.Image:
    """Apply a named operation to an image.

    Args:
        image: Input PIL Image
        op_name: Operation name (e.g., "resize", "dither")
        *args: Positional arguments for the operation
        **kwargs: Keyword arguments for the operation

    Returns:
        Processed PIL Image

    Raises:
        ValueError: If operation name is unknown
    """
    # Handle composition operations that need to load additional images
    if op_name == "hstack":
        from chop.pipeline import load_image
        other = load_image(args[0])
        align = kwargs.get("align", "center")
        return op_hstack(image, other, align=align)

    if op_name == "vstack":
        from chop.pipeline import load_image
        other = load_image(args[0])
        align = kwargs.get("align", "center")
        return op_vstack(image, other, align=align)

    if op_name == "overlay":
        from chop.pipeline import load_image
        overlay_img = load_image(args[0])
        x = args[1] if len(args) > 1 else kwargs.get("x", 0)
        y = args[2] if len(args) > 2 else kwargs.get("y", 0)
        opacity = kwargs.get("opacity", 1.0)
        paste = kwargs.get("paste", False)
        return op_overlay(image, overlay_img, x=x, y=y, opacity=opacity, paste=paste)

    if op_name == "grid":
        from chop.pipeline import load_image
        paths = args[0] if args else kwargs.get("paths", [])
        others = [load_image(p) for p in paths]
        cols = kwargs.get("cols", 2)
        return op_grid(image, others, cols=cols)

    # Handle crop specially to parse arguments
    if op_name == "crop":
        x, y, w, h = args[0], args[1], args[2], args[3]
        # Parse if string percentages
        if isinstance(x, str) or isinstance(y, str):
            x, y, w, h = parse_crop([str(x), str(y), str(w), str(h)], image.size)
        return op_crop(image, x, y, w, h)

    # Standard operations
    if op_name not in OPERATIONS:
        raise ValueError(f"Unknown operation: {op_name}")

    op_func = OPERATIONS[op_name]
    return op_func(image, *args, **kwargs)
