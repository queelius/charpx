"""Unit tests for the pixdot library."""

import numpy as np
import pytest

from pixdot import auto_contrast, floyd_steinberg, render
from pixdot.braille import render as braille_render


class TestRender:
    """Tests for braille rendering."""

    def test_output_dimensions(self):
        """Output should have correct dimensions (height/4 rows, width/2 cols)."""
        bitmap = np.zeros((16, 8), dtype=np.float32)
        result = render(bitmap)

        lines = result.split('\n')
        assert len(lines) == 4  # 16 / 4
        assert all(len(line) == 4 for line in lines)  # 8 / 2

    def test_empty_bitmap_produces_blank_braille(self):
        """All-black bitmap should produce blank braille (U+2800)."""
        bitmap = np.zeros((4, 2), dtype=np.float32)
        result = render(bitmap)
        assert result == '\u2800'  # U+2800, blank braille

    def test_full_bitmap_produces_full_braille(self):
        """All-white bitmap should produce full braille (U+28FF)."""
        bitmap = np.ones((4, 2), dtype=np.float32)
        result = render(bitmap)
        assert result == '\u28ff'  # U+28FF, all 8 dots

    def test_single_dot_patterns(self):
        """Individual dots should map to correct characters."""
        # Dot 1 (top-left) -> bit 0 -> U+2801
        bitmap = np.zeros((4, 2), dtype=np.float32)
        bitmap[0, 0] = 1.0
        assert render(bitmap) == '\u2801'  # U+2801

        # Dot 4 (top-right) -> bit 3 -> U+2808
        bitmap = np.zeros((4, 2), dtype=np.float32)
        bitmap[0, 1] = 1.0
        assert render(bitmap) == '\u2808'  # U+2808

        # Dot 7 (bottom-left) -> bit 6 -> U+2840
        bitmap = np.zeros((4, 2), dtype=np.float32)
        bitmap[3, 0] = 1.0
        assert render(bitmap) == '\u2840'  # U+2840

        # Dot 8 (bottom-right) -> bit 7 -> U+2880
        bitmap = np.zeros((4, 2), dtype=np.float32)
        bitmap[3, 1] = 1.0
        assert render(bitmap) == '\u2880'  # U+2880

    def test_threshold_parameter(self):
        """Threshold should control dot activation."""
        bitmap = np.ones((4, 2), dtype=np.float32) * 0.4

        # With threshold 0.5, nothing should be on
        assert render(bitmap, threshold=0.5) == '\u2800'

        # With threshold 0.3, everything should be on
        assert render(bitmap, threshold=0.3) == '\u28ff'

    def test_rejects_non_2d(self):
        """Should reject non-2D input."""
        with pytest.raises(ValueError, match="must be 2D"):
            render(np.zeros((4, 2, 3)))

    def test_threshold_none_auto_detect(self):
        """threshold=None should auto-calculate from bitmap mean."""
        # Create bitmap with mean around 0.5
        bitmap = np.zeros((8, 4), dtype=np.float32)
        bitmap[0:4, :] = 1.0  # top half white

        result = render(bitmap, threshold=None)
        # Should produce non-empty output
        assert len(result) > 0
        assert '\u2800' in result or '\u28ff' in result  # Mix of light and dark

    def test_diagonal_pattern(self):
        """Diagonal should produce recognizable pattern."""
        bitmap = np.eye(8, dtype=np.float32)
        result = render(bitmap, threshold=0.5)

        # Should have 2 rows, 4 columns
        lines = result.split('\n')
        assert len(lines) == 2
        assert all(len(line) == 4 for line in lines)

    def test_large_bitmap(self):
        """Should handle larger bitmaps."""
        bitmap = np.random.rand(100, 80).astype(np.float32)
        result = render(bitmap)

        lines = result.split('\n')
        assert len(lines) == 25  # 100 / 4
        assert all(len(line) == 40 for line in lines)  # 80 / 2

    def test_odd_dimensions_handled(self):
        """Should handle odd dimensions by padding."""
        # 5x3 bitmap (not divisible by 4 and 2)
        bitmap = np.ones((5, 3), dtype=np.float32)
        result = render(bitmap)

        # Should produce output (with padding)
        lines = result.split('\n')
        assert len(lines) == 2  # ceil(5/4) = 2
        assert all(len(line) == 2 for line in lines)  # ceil(3/2) = 2


class TestPublicAPI:
    """Tests for the public API exported from pixdot."""

    def test_render_function(self):
        """render() should work correctly."""
        bitmap = np.ones((4, 2), dtype=np.float32)
        assert render(bitmap) == '\u28ff'

    def test_render_with_threshold_none(self):
        """render() with threshold=None should auto-detect."""
        bitmap = np.ones((4, 2), dtype=np.float32) * 0.8
        result = render(bitmap, threshold=None)
        assert len(result) > 0


class TestAutoContrast:
    """Tests for auto_contrast preprocessing."""

    def test_stretches_to_full_range(self):
        """Should stretch values to 0-1 range."""
        bitmap = np.array([[0.2, 0.4], [0.6, 0.8]], dtype=np.float32)
        result = auto_contrast(bitmap)

        assert result.min() == pytest.approx(0.0)
        assert result.max() == pytest.approx(1.0)

    def test_preserves_relative_brightness(self):
        """Relative brightness should be preserved."""
        bitmap = np.array([[0.2, 0.4], [0.6, 0.8]], dtype=np.float32)
        result = auto_contrast(bitmap)

        # Corners should maintain relative order
        assert result[0, 0] < result[0, 1] < result[1, 0] < result[1, 1]

    def test_handles_constant_image(self):
        """Should handle constant images without division by zero."""
        bitmap = np.ones((4, 4), dtype=np.float32) * 0.5
        result = auto_contrast(bitmap)

        # Should return a constant image (no crash)
        assert result.shape == bitmap.shape
        assert np.allclose(result, 0.5)

    def test_already_full_range(self):
        """Should be idempotent when already full range."""
        bitmap = np.array([[0.0, 0.5], [0.5, 1.0]], dtype=np.float32)
        result = auto_contrast(bitmap)

        assert np.allclose(result, bitmap)


class TestFloydSteinberg:
    """Tests for Floyd-Steinberg dithering."""

    def test_produces_binary_output(self):
        """Output should only contain 0.0 and 1.0."""
        bitmap = np.random.rand(16, 16).astype(np.float32)
        result = floyd_steinberg(bitmap)

        unique_values = np.unique(result)
        assert all(v in [0.0, 1.0] for v in unique_values)

    def test_preserves_mean_brightness_approximately(self):
        """Mean brightness should be roughly preserved."""
        np.random.seed(42)  # For reproducibility
        bitmap = np.random.rand(32, 32).astype(np.float32) * 0.5 + 0.25  # Mean ~0.5
        result = floyd_steinberg(bitmap)

        # The mean of the dithered output should be somewhat close to original
        # (not exact due to boundary effects and quantization)
        assert abs(result.mean() - bitmap.mean()) < 0.15

    def test_custom_threshold(self):
        """Custom threshold should affect output."""
        bitmap = np.ones((8, 8), dtype=np.float32) * 0.6

        # With threshold 0.5, most pixels should be on
        result_low = floyd_steinberg(bitmap, threshold=0.5)
        # With threshold 0.7, most pixels should be off
        result_high = floyd_steinberg(bitmap, threshold=0.7)

        assert result_low.mean() > result_high.mean()

    def test_does_not_modify_input(self):
        """Should not modify the input array."""
        bitmap = np.random.rand(8, 8).astype(np.float32)
        original = bitmap.copy()
        _ = floyd_steinberg(bitmap)

        assert np.allclose(bitmap, original)

    def test_black_stays_black(self):
        """All-black image should stay black."""
        bitmap = np.zeros((8, 8), dtype=np.float32)
        result = floyd_steinberg(bitmap)

        assert np.allclose(result, 0.0)

    def test_white_stays_white(self):
        """All-white image should stay white."""
        bitmap = np.ones((8, 8), dtype=np.float32)
        result = floyd_steinberg(bitmap)

        assert np.allclose(result, 1.0)
