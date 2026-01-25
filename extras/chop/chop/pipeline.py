"""Pipeline utilities for lazy image processing.

Implements lazy evaluation: JSON carries only file path + operations list.
Image is loaded and processed only at render/save time.
"""

from __future__ import annotations

import io
import json
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from numpy.typing import NDArray


@dataclass
class PipelineState:
    """Lazy pipeline state - stores path and operations, not image data.

    Attributes:
        path: Source image path, URL, or "<stdin>" for stdin input
        ops: List of operations to apply, each as (name, args, kwargs)
        metadata: Optional metadata dict
    """

    path: str
    ops: list[tuple[str, tuple, dict]] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def add_op(self, name: str, *args, **kwargs) -> None:
        """Append operation to the list.

        Args:
            name: Operation name (e.g., "resize", "dither")
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
        """
        self.ops.append((name, args, kwargs))

    def to_json(self) -> str:
        """Serialize state to JSON string.

        Returns compact JSON with version 2 format:
        {"version": 2, "path": "photo.jpg", "ops": [...], "metadata": {...}}
        """
        # Convert ops to JSON-serializable format
        ops_data = []
        for name, args, kwargs in self.ops:
            ops_data.append([name, list(args), kwargs])

        output = {
            "version": 2,
            "path": self.path,
            "ops": ops_data,
            "metadata": self.metadata,
        }
        return json.dumps(output)

    @classmethod
    def from_json(cls, json_str: str) -> PipelineState:
        """Deserialize state from JSON string.

        Supports version 2 format (lazy) only.
        """
        data = json.loads(json_str)
        version = data.get("version", 1)

        if version == 2:
            # Lazy format: path + ops
            ops = []
            for op_data in data.get("ops", []):
                name = op_data[0]
                args = tuple(op_data[1]) if len(op_data) > 1 else ()
                kwargs = op_data[2] if len(op_data) > 2 else {}
                ops.append((name, args, kwargs))

            return cls(
                path=data["path"],
                ops=ops,
                metadata=data.get("metadata", {}),
            )
        else:
            raise ValueError(
                f"Unsupported pipeline version: {version}. "
                "Only version 2 (lazy) format is supported."
            )

    def materialize(self) -> Image.Image:
        """Load image and apply all operations.

        Called at render/save time to actually process the image.

        Returns:
            Processed PIL Image in RGBA mode.
        """
        from chop.operations import apply_operation

        # Load image from path
        image = load_image(self.path)

        # Apply all operations in order
        for op_name, args, kwargs in self.ops:
            image = apply_operation(image, op_name, *args, **kwargs)

        return image


def read_pipeline_input() -> PipelineState | None:
    """Read pipeline state from stdin if available.

    Returns:
        PipelineState if valid JSON input, None otherwise.
    """
    if sys.stdin.isatty():
        return None

    try:
        data = sys.stdin.read()
        if not data.strip():
            return None
        return PipelineState.from_json(data)
    except (json.JSONDecodeError, KeyError, ValueError):
        return None


def write_pipeline_output(state: PipelineState) -> None:
    """Write pipeline state to stdout."""
    print(state.to_json())


def load_ansi_file(source: str) -> Image.Image:
    """Load ANSI terminal art from file and convert to PIL Image.

    Uses charpx's from_ansi() adapter to parse braille, quadrant, sextant,
    or ASCII art back into a bitmap.

    Args:
        source: File path to .ans file (UTF-8 encoded)

    Returns:
        PIL Image in RGBA mode
    """
    from charpx.adapters.ansi import from_ansi

    with open(source, encoding="utf-8") as f:
        text = f.read()

    canvas = from_ansi(text)
    image = canvas.to_pil()

    # Ensure RGBA mode
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    return image


def load_image(source: str) -> Image.Image:
    """Load image from file, URL, or stdin.

    Args:
        source: File path, URL, or "-" for stdin.
                Supports .ans files (ANSI terminal art).

    Returns:
        PIL Image in RGBA mode.
    """
    if source == "-":
        # Read from stdin (binary)
        image_bytes = sys.stdin.buffer.read()
        image = Image.open(io.BytesIO(image_bytes))
    elif source.startswith(("http://", "https://")):
        # URL
        import urllib.request

        with urllib.request.urlopen(source) as response:
            image_bytes = response.read()
        image = Image.open(io.BytesIO(image_bytes))
    elif source.lower().endswith(".ans"):
        # ANSI terminal art file
        return load_ansi_file(source)
    else:
        # File path
        image = Image.open(source)

    # Convert to RGBA
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    return image


def image_to_arrays(image: Image.Image) -> tuple[NDArray, NDArray]:
    """Convert PIL Image to bitmap and colors arrays.

    Args:
        image: PIL Image in RGBA mode

    Returns:
        (bitmap, colors) tuple where:
        - bitmap is 2D float32 (H, W) with luminance 0.0-1.0
        - colors is 3D float32 (H, W, 3) with RGB 0.0-1.0
    """
    # Convert to numpy array
    arr = np.array(image, dtype=np.float32) / 255.0

    if arr.ndim == 2:
        # Grayscale
        bitmap = arr
        colors = np.stack([arr, arr, arr], axis=-1)
    elif arr.shape[2] == 4:
        # RGBA
        rgb = arr[:, :, :3]
        # ITU-R BT.601 luminance
        bitmap = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        colors = rgb
    elif arr.shape[2] == 3:
        # RGB
        bitmap = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
        colors = arr
    else:
        raise ValueError(f"Unexpected image shape: {arr.shape}")

    return bitmap.astype(np.float32), colors.astype(np.float32)
