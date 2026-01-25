"""Tests for chop CLI."""

from __future__ import annotations

import io
import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from chop.operations import (
    parse_size,
    parse_crop,
    op_resize,
    op_crop,
    op_rotate,
    op_flip,
    op_dither,
    op_invert,
    op_contrast,
)
from chop.pipeline import (
    PipelineState,
    load_image,
    image_to_arrays,
)


@pytest.fixture
def test_image() -> Image.Image:
    """Create a simple test image."""
    img = Image.new("RGBA", (100, 80), color=(128, 64, 32, 255))
    return img


@pytest.fixture
def test_image_file(test_image: Image.Image) -> str:
    """Save test image to temp file and return path."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        test_image.save(f.name)
        return f.name


class TestParseSize:
    """Tests for parse_size function."""

    def test_percentage(self):
        assert parse_size("50%", (100, 80)) == (50, 40)
        assert parse_size("200%", (100, 80)) == (200, 160)

    def test_exact_dimensions(self):
        assert parse_size("800x600", (100, 80)) == (800, 600)
        assert parse_size("50x50", (100, 80)) == (50, 50)

    def test_width_only(self):
        assert parse_size("w50", (100, 80)) == (50, 40)
        assert parse_size("w200", (100, 80)) == (200, 160)

    def test_height_only(self):
        assert parse_size("h40", (100, 80)) == (50, 40)
        assert parse_size("h160", (100, 80)) == (200, 160)


class TestParseCrop:
    """Tests for parse_crop function."""

    def test_pixels(self):
        result = parse_crop(["10", "20", "50", "40"], (100, 80))
        assert result == (10, 20, 50, 40)

    def test_percentages(self):
        result = parse_crop(["10%", "25%", "50%", "50%"], (100, 80))
        assert result == (10, 20, 50, 40)

    def test_invalid_args(self):
        with pytest.raises(ValueError):
            parse_crop(["10", "20", "50"], (100, 80))  # Too few args


class TestOperations:
    """Tests for image operations."""

    def test_resize(self, test_image: Image.Image):
        result = op_resize(test_image, "50%")
        assert result.size == (50, 40)

    def test_crop(self, test_image: Image.Image):
        result = op_crop(test_image, 10, 10, 50, 40)
        assert result.size == (50, 40)

    def test_rotate_90(self, test_image: Image.Image):
        result = op_rotate(test_image, 90)
        # 90 degree rotation swaps dimensions
        assert result.size[0] == test_image.size[1]
        assert result.size[1] == test_image.size[0]

    def test_flip_horizontal(self, test_image: Image.Image):
        result = op_flip(test_image, "h")
        assert result.size == test_image.size

    def test_flip_vertical(self, test_image: Image.Image):
        result = op_flip(test_image, "v")
        assert result.size == test_image.size

    def test_flip_invalid(self, test_image: Image.Image):
        with pytest.raises(ValueError):
            op_flip(test_image, "x")

    def test_dither(self, test_image: Image.Image):
        result = op_dither(test_image)
        assert result.size == test_image.size

    def test_invert(self, test_image: Image.Image):
        result = op_invert(test_image)
        assert result.size == test_image.size

    def test_contrast(self, test_image: Image.Image):
        result = op_contrast(test_image)
        assert result.size == test_image.size


class TestPipeline:
    """Tests for pipeline utilities."""

    def test_state_to_json_and_back(self, test_image: Image.Image):
        state = PipelineState(
            image=test_image,
            metadata={"test": "value"},
        )
        state.add_operation("test_op", ["arg1", "arg2"])

        json_str = state.to_json()
        restored = PipelineState.from_json(json_str)

        assert restored.image.size == test_image.size
        assert restored.metadata["test"] == "value"
        assert len(restored.history) == 1
        assert restored.history[0]["op"] == "test_op"

    def test_load_image_file(self, test_image_file: str):
        image = load_image(test_image_file)
        assert image.mode == "RGBA"
        assert image.size == (100, 80)

    def test_image_to_arrays(self, test_image: Image.Image):
        bitmap, colors = image_to_arrays(test_image)

        assert bitmap.shape == (80, 100)
        assert colors.shape == (80, 100, 3)
        assert bitmap.dtype == np.float32
        assert colors.dtype == np.float32
        assert 0 <= bitmap.min() <= bitmap.max() <= 1
        assert 0 <= colors.min() <= colors.max() <= 1
