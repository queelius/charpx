"""Base adapter protocol for converting library objects to pixdot bitmaps.

Adapters provide a consistent interface for converting graphics library objects
(matplotlib figures, PIL images, pygame surfaces, etc.) to grayscale bitmaps
that pixdot can render to braille.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import numpy as np

from pixdot import (
    RenderConfig,
    auto_contrast,
    compute_target_dimensions,
    floyd_steinberg,
    get_preset,
    render,
    render_ansi,
    resize_bitmap,
)


class BitmapAdapter(ABC):
    """Protocol for converting library objects to pixdot bitmaps.

    Subclasses implement `to_bitmap()` to extract grayscale pixel data
    from their source type. The base class provides the full rendering
    pipeline via `render()`.

    Example:
        >>> class MyAdapter(BitmapAdapter):
        ...     def to_bitmap(self, source, config):
        ...         # Convert source to grayscale numpy array
        ...         return np.array(...)
        ...
        >>> adapter = MyAdapter()
        >>> print(adapter.render(my_object, "dark_terminal"))
    """

    @abstractmethod
    def to_bitmap(self, source: Any, config: RenderConfig) -> np.ndarray:
        """Convert source object to grayscale bitmap.

        Args:
            source: Library-specific object (Figure, Image, Surface, etc.)
            config: Render configuration for target dimensions.

        Returns:
            2D numpy array of shape (H, W), values 0.0-1.0.
            0.0 = black, 1.0 = white.
        """
        ...

    def to_color_bitmap(self, source: Any, config: RenderConfig) -> np.ndarray | None:
        """Convert source object to RGB bitmap (optional).

        Override this method in subclasses to enable color support.

        Args:
            source: Library-specific object (Figure, Image, Surface, etc.)
            config: Render configuration for target dimensions.

        Returns:
            3D numpy array of shape (H, W, 3), values 0.0-1.0, or None
            if color is not available (falls back to grayscale).
        """
        return None

    def render(self, source: Any, config: RenderConfig | str = "default") -> str:
        """Full pipeline: source -> bitmap -> braille string.

        Args:
            source: Library-specific object to convert.
            config: Either a RenderConfig instance or a preset name
                    (default, dark_terminal, light_terminal, high_detail,
                    compact, no_dither, grayscale, truecolor).

        Returns:
            Multi-line string of braille characters.
        """
        if isinstance(config, str):
            config = get_preset(config)

        bitmap = self.to_bitmap(source, config)

        # Get color bitmap if color mode is enabled
        colors = None
        if config.color_mode in ("grayscale", "truecolor"):
            colors = self.to_color_bitmap(source, config)

        return self._apply_pipeline(bitmap, config, colors)

    def _apply_pipeline(
        self,
        bitmap: np.ndarray,
        config: RenderConfig,
        colors: np.ndarray | None = None,
    ) -> str:
        """Apply preprocessing and render to braille.

        The pipeline order is:
        1. Resize to target dimensions
        2. Auto-contrast (if enabled)
        3. Invert (if enabled)
        4. Dither (if enabled, skipped for color modes)
        5. Render to braille (plain or with ANSI color)

        Args:
            bitmap: 2D array (H, W), values 0.0-1.0.
            config: Render configuration.
            colors: Optional 3D array (H, W, 3) for color rendering.

        Returns:
            Multi-line braille string.
        """
        # Get source dimensions
        src_h, src_w = bitmap.shape

        # Compute target dimensions
        target_w, target_h = compute_target_dimensions(
            src_w, src_h, config.width_chars, config.cell_aspect
        )

        # Resize bitmap
        bitmap = resize_bitmap(bitmap, target_w, target_h)

        # Resize colors if provided (resize each channel independently)
        if colors is not None:
            colors = self._resize_color_bitmap(colors, target_w, target_h)

        # Auto-contrast
        if config.auto_contrast:
            bitmap = auto_contrast(bitmap)

        # Invert (convert from dark-on-light to light-on-dark)
        if config.invert:
            bitmap = 1.0 - bitmap
            if colors is not None:
                colors = 1.0 - colors

        # Dither for better grayscale representation (skip for color modes)
        if config.dither and config.color_mode not in ("grayscale", "truecolor"):
            bitmap = floyd_steinberg(bitmap, config.dither_threshold)

        # Render to braille
        if config.color_mode in ("grayscale", "truecolor"):
            return render_ansi(bitmap, config.threshold, config.color_mode, colors)
        else:
            return render(bitmap, config.threshold)

    @staticmethod
    def _resize_color_bitmap(
        colors: np.ndarray, target_w: int, target_h: int
    ) -> np.ndarray:
        """Resize 3D color bitmap by resizing each channel independently.

        Args:
            colors: 3D array (H, W, 3), values 0.0-1.0.
            target_w: Target width in pixels.
            target_h: Target height in pixels.

        Returns:
            Resized 3D array (target_h, target_w, 3).
        """
        # Resize each channel independently
        resized_channels = []
        for i in range(colors.shape[2]):
            channel = resize_bitmap(colors[:, :, i], target_w, target_h)
            resized_channels.append(channel)
        return np.stack(resized_channels, axis=-1)

    @staticmethod
    def validate_bitmap(bitmap: np.ndarray, name: str = "bitmap") -> None:
        """Validate bitmap shape and value range.

        Args:
            bitmap: Array to validate.
            name: Name of the bitmap for error messages.

        Raises:
            ValueError: If bitmap is not 2D or has invalid dtype.
        """
        if bitmap.ndim != 2:
            raise ValueError(
                f"{name} must be 2D array (H, W), got {bitmap.ndim}D with shape {bitmap.shape}"
            )
        if not np.issubdtype(bitmap.dtype, np.floating) and not np.issubdtype(
            bitmap.dtype, np.integer
        ):
            raise ValueError(
                f"{name} must be numeric array, got dtype {bitmap.dtype}"
            )

    @staticmethod
    def validate_color_bitmap(
        colors: np.ndarray, bitmap_shape: tuple[int, int], name: str = "colors"
    ) -> None:
        """Validate color bitmap matches grayscale bitmap dimensions.

        Args:
            colors: Color array to validate.
            bitmap_shape: Expected (H, W) shape from grayscale bitmap.
            name: Name of the color bitmap for error messages.

        Raises:
            ValueError: If shape doesn't match or not 3D with 3 channels.
        """
        if colors.ndim != 3:
            raise ValueError(
                f"{name} must be 3D array (H, W, 3), got {colors.ndim}D with shape {colors.shape}"
            )
        if colors.shape[2] != 3:
            raise ValueError(
                f"{name} must have 3 color channels, got {colors.shape[2]}"
            )
        if colors.shape[:2] != bitmap_shape:
            raise ValueError(
                f"{name} shape {colors.shape[:2]} doesn't match bitmap shape {bitmap_shape}"
            )
