"""PIL/Pillow image adapter for dapple.

Provides conversion from PIL Images to Canvas.
"""

from __future__ import annotations

from os import PathLike
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from dapple import Canvas
    from dapple.renderers import Renderer


class PILAdapter:
    """Adapter for PIL/Pillow images.

    Converts PIL Image objects to Canvas, handling various color modes.

    Example:
        >>> from PIL import Image
        >>> from dapple.adapters import PILAdapter
        >>> img = Image.open("photo.jpg")
        >>> adapter = PILAdapter(img, width=80)
        >>> canvas = adapter.to_canvas()
    """

    def __init__(
        self,
        image: Any,
        *,
        width: int | None = None,
        height: int | None = None,
        renderer: Renderer | None = None,
    ) -> None:
        """Create a PILAdapter.

        Args:
            image: PIL Image object.
            width: Target width (None to keep original).
            height: Target height (None to keep original or scale proportionally).
            renderer: Default renderer for the resulting Canvas.

        Raises:
            ImportError: If PIL is not installed.
            TypeError: If image is not a PIL Image.
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError(
                "PIL is required for PILAdapter. Install with: pip install pillow"
            )

        if not isinstance(image, Image.Image):
            raise TypeError(f"Expected PIL Image, got {type(image)}")

        self._image = image
        self._width = width
        self._height = height
        self._renderer = renderer

    def to_canvas(self) -> Canvas:
        """Convert to Canvas.

        Returns:
            New Canvas object.
        """
        from PIL import Image

        from dapple import Canvas

        img = self._image

        # Resize if requested
        if self._width is not None or self._height is not None:
            orig_w, orig_h = img.size
            if self._width is not None and self._height is not None:
                new_size = (self._width, self._height)
            elif self._width is not None:
                ratio = self._width / orig_w
                new_size = (self._width, int(orig_h * ratio))
            else:
                ratio = self._height / orig_h  # type: ignore
                new_size = (int(orig_w * ratio), self._height)  # type: ignore

            img = img.resize(new_size, Image.Resampling.LANCZOS)

        # Convert to appropriate mode and extract arrays
        if img.mode == "L":
            bitmap = np.array(img, dtype=np.float32) / 255.0
            return Canvas(bitmap, renderer=self._renderer)
        elif img.mode in ("RGB", "RGBA"):
            rgb = img.convert("RGB")
            colors = np.array(rgb, dtype=np.float32) / 255.0
            bitmap = (
                0.299 * colors[:, :, 0]
                + 0.587 * colors[:, :, 1]
                + 0.114 * colors[:, :, 2]
            )
            return Canvas(bitmap, colors=colors, renderer=self._renderer)
        else:
            # Convert unknown modes to grayscale
            gray = img.convert("L")
            bitmap = np.array(gray, dtype=np.float32) / 255.0
            return Canvas(bitmap, renderer=self._renderer)


def from_pil(
    image: Any,
    *,
    width: int | None = None,
    height: int | None = None,
    renderer: Renderer | None = None,
) -> Canvas:
    """Create a Canvas from a PIL Image.

    Convenience function wrapping PILAdapter.

    Args:
        image: PIL Image object.
        width: Target width (None to keep original).
        height: Target height (None to keep original or scale proportionally).
        renderer: Default renderer for the resulting Canvas.

    Returns:
        New Canvas object.

    Example:
        >>> from PIL import Image
        >>> from dapple.adapters import from_pil
        >>> img = Image.open("photo.jpg")
        >>> canvas = from_pil(img, width=80)
    """
    return PILAdapter(image, width=width, height=height, renderer=renderer).to_canvas()


def load_image(
    path: str | PathLike,
    *,
    width: int | None = None,
    height: int | None = None,
    renderer: Renderer | None = None,
) -> Canvas:
    """Load an image file and convert to Canvas.

    Args:
        path: Path to image file (str or PathLike).
        width: Target width (None to keep original).
        height: Target height (None to keep original or scale proportionally).
        renderer: Default renderer for the resulting Canvas.

    Returns:
        New Canvas object.

    Raises:
        ImportError: If PIL is not installed.
        FileNotFoundError: If file doesn't exist.

    Example:
        >>> from dapple.adapters.pil import load_image
        >>> canvas = load_image("photo.jpg", width=80)
    """
    try:
        from PIL import Image
    except ImportError:
        raise ImportError(
            "PIL is required for load_image. Install with: pip install pillow"
        )

    img = Image.open(path)
    return from_pil(img, width=width, height=height, renderer=renderer)
