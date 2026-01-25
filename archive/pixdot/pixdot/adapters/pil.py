"""PIL/Pillow adapter for converting images to braille.

Converts PIL Image objects to grayscale bitmaps for braille rendering.

Example:
    >>> from PIL import Image
    >>> from pixdot.adapters import PILAdapter
    >>> from pixdot.adapters.pil import image_to_braille
    >>>
    >>> image = Image.open("photo.jpg")
    >>> print(image_to_braille(image, "dark_terminal"))

Requires: pillow (pip install pixdot[pil])
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from pixdot import RenderConfig

from .base import BitmapAdapter

if TYPE_CHECKING:
    from PIL.Image import Image


def _require_pillow() -> None:
    """Raise ImportError with install instructions if pillow not available."""
    try:
        import PIL  # noqa: F401
    except ImportError:
        raise ImportError(
            "PILAdapter requires pillow. Install with: pip install pixdot[pil]"
        ) from None


class PILAdapter(BitmapAdapter):
    """Adapter for PIL/Pillow images.

    Converts PIL Image objects to grayscale numpy arrays for braille rendering.
    Handles RGB, RGBA, L (grayscale), and other modes by converting to
    grayscale internally.
    """

    def __init__(self) -> None:
        """Initialize adapter and verify pillow is available."""
        _require_pillow()

    def to_bitmap(self, image: "Image", config: RenderConfig) -> np.ndarray:
        """Convert PIL Image to grayscale bitmap.

        Args:
            image: PIL Image object (any mode: RGB, RGBA, L, etc.)
            config: Render configuration (used for target dimensions).

        Returns:
            2D numpy array (H, W), values 0.0-1.0.
        """
        # Convert to grayscale if not already
        if image.mode != "L":
            gray = image.convert("L")
        else:
            gray = image

        # Convert to numpy array and normalize to 0.0-1.0
        return np.array(gray, dtype=np.float32) / 255.0

    def to_color_bitmap(self, image: "Image", config: RenderConfig) -> np.ndarray:
        """Convert PIL Image to RGB bitmap.

        Args:
            image: PIL Image object (any mode: RGB, RGBA, L, etc.)
            config: Render configuration (used for target dimensions).

        Returns:
            3D numpy array (H, W, 3), values 0.0-1.0.
        """
        # Convert to RGB if not already
        rgb = image.convert("RGB")

        # Convert to numpy array and normalize to 0.0-1.0
        return np.array(rgb, dtype=np.float32) / 255.0


def image_to_braille(
    image: "Image",
    config: RenderConfig | str = "default",
) -> str:
    """One-liner: PIL image -> braille string.

    Convenience function that creates a PILAdapter and renders
    the image in a single call.

    Args:
        image: PIL Image object.
        config: RenderConfig instance or preset name.

    Returns:
        Multi-line braille string.

    Example:
        >>> from PIL import Image
        >>> image = Image.open("photo.jpg")
        >>> print(image_to_braille(image, "dark_terminal"))
    """
    return PILAdapter().render(image, config)


def load_and_render(
    path: str,
    config: RenderConfig | str = "default",
) -> str:
    """Load image from path and render to braille.

    Convenience function for loading and rendering in one step.

    Args:
        path: Path to image file.
        config: RenderConfig instance or preset name.

    Returns:
        Multi-line braille string.

    Example:
        >>> print(load_and_render("photo.jpg", "dark_terminal"))
    """
    _require_pillow()
    from PIL import Image

    with Image.open(path) as image:
        return image_to_braille(image, config)
