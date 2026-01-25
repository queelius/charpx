"""Pipeline utilities for JSON image encoding/decoding.

Handles serialization of images for Unix pipe composition.
"""

from __future__ import annotations

import base64
import io
import json
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from numpy.typing import NDArray

# Size threshold for base64 vs temp file (1MB)
BASE64_THRESHOLD = 1024 * 1024


@dataclass
class PipelineState:
    """State passed through the pipeline.

    Attributes:
        image: PIL Image in RGBA mode
        metadata: Image metadata (original path, sizes, etc.)
        history: List of operations applied
    """

    image: Image.Image
    metadata: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)

    def add_operation(self, op: str, args: list | None = None) -> None:
        """Record an operation in history."""
        self.history.append({"op": op, "args": args or []})

    def to_json(self) -> str:
        """Serialize state to JSON string."""
        # Convert image to bytes
        buffer = io.BytesIO()
        self.image.save(buffer, format="PNG")
        image_bytes = buffer.getvalue()

        # Decide encoding based on size
        if len(image_bytes) < BASE64_THRESHOLD:
            image_data = {
                "type": "base64",
                "format": "png",
                "data": base64.b64encode(image_bytes).decode("ascii"),
            }
        else:
            # Use temp file for large images
            with tempfile.NamedTemporaryFile(
                suffix=".png", delete=False, prefix="chop_"
            ) as f:
                f.write(image_bytes)
                image_data = {
                    "type": "file",
                    "format": "png",
                    "path": f.name,
                }

        output = {
            "version": 1,
            "image": image_data,
            "metadata": {
                **self.metadata,
                "current_size": list(self.image.size),
            },
            "history": self.history,
        }

        return json.dumps(output)

    @classmethod
    def from_json(cls, json_str: str) -> PipelineState:
        """Deserialize state from JSON string."""
        data = json.loads(json_str)

        if data.get("version", 1) != 1:
            raise ValueError(f"Unsupported pipeline version: {data.get('version')}")

        image_data = data["image"]

        if image_data["type"] == "base64":
            image_bytes = base64.b64decode(image_data["data"])
            image = Image.open(io.BytesIO(image_bytes))
        elif image_data["type"] == "file":
            image = Image.open(image_data["path"])
        else:
            raise ValueError(f"Unknown image type: {image_data['type']}")

        # Ensure RGBA
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        return cls(
            image=image,
            metadata=data.get("metadata", {}),
            history=data.get("history", []),
        )


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


def load_image(source: str) -> Image.Image:
    """Load image from file, URL, or stdin.

    Args:
        source: File path, URL, or "-" for stdin.

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
