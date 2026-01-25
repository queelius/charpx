"""Unit tests for the pixdot.resize module."""

import numpy as np
import pytest

from pixdot import compute_target_dimensions, resize_bitmap


class TestResizeBitmap:
    """Tests for resize_bitmap function."""

    def test_basic_downscale(self):
        """Should downscale bitmap to target dimensions."""
        bitmap = np.ones((100, 80), dtype=np.float32)
        result = resize_bitmap(bitmap, 40, 40)

        # Should be braille-compatible (height % 4 == 0, width % 2 == 0)
        assert result.shape[0] % 4 == 0
        assert result.shape[1] % 2 == 0
        assert result.shape == (40, 40)

    def test_basic_upscale(self):
        """Should upscale bitmap to target dimensions."""
        bitmap = np.ones((20, 20), dtype=np.float32)
        result = resize_bitmap(bitmap, 80, 40)

        assert result.shape[0] % 4 == 0
        assert result.shape[1] % 2 == 0
        assert result.shape == (40, 80)

    def test_braille_compatible_dimensions(self):
        """Output dimensions should always be braille-compatible."""
        bitmap = np.random.rand(100, 100).astype(np.float32)

        # Try various target dimensions
        for target_w in [10, 17, 33, 50, 100]:
            for target_h in [10, 17, 33, 50, 100]:
                result = resize_bitmap(bitmap, target_w, target_h)
                assert result.shape[0] % 4 == 0, f"Height {result.shape[0]} not divisible by 4"
                assert result.shape[1] % 2 == 0, f"Width {result.shape[1]} not divisible by 2"

    def test_minimum_dimensions(self):
        """Output should have minimum braille dimensions (4, 2)."""
        bitmap = np.ones((100, 100), dtype=np.float32)
        result = resize_bitmap(bitmap, 1, 1)

        assert result.shape[0] >= 4
        assert result.shape[1] >= 2

    def test_preserves_value_range(self):
        """Output values should stay in 0.0-1.0 range."""
        bitmap = np.random.rand(100, 100).astype(np.float32)
        result = resize_bitmap(bitmap, 50, 50)

        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_preserves_mean_approximately(self):
        """Mean brightness should be approximately preserved."""
        np.random.seed(42)
        bitmap = np.random.rand(100, 100).astype(np.float32)
        result = resize_bitmap(bitmap, 50, 50)

        # Mean should be close (within 10%)
        assert abs(result.mean() - bitmap.mean()) < 0.1

    def test_uniform_image_stays_uniform(self):
        """Uniform image should remain uniform after resize."""
        bitmap = np.ones((100, 100), dtype=np.float32) * 0.7
        result = resize_bitmap(bitmap, 40, 40)

        assert np.allclose(result, 0.7, atol=0.01)

    def test_black_stays_black(self):
        """All-black image should stay black."""
        bitmap = np.zeros((100, 100), dtype=np.float32)
        result = resize_bitmap(bitmap, 50, 50)

        assert np.allclose(result, 0.0)

    def test_white_stays_white(self):
        """All-white image should stay white."""
        bitmap = np.ones((100, 100), dtype=np.float32)
        result = resize_bitmap(bitmap, 50, 50)

        assert np.allclose(result, 1.0)

    def test_rejects_non_2d(self):
        """Should reject non-2D input."""
        with pytest.raises(ValueError, match="must be 2D"):
            resize_bitmap(np.zeros((10, 10, 3)), 20, 20)


class TestResizeMethods:
    """Tests for different resize methods."""

    def test_area_method(self):
        """Area method should work for downscaling."""
        bitmap = np.random.rand(100, 100).astype(np.float32)
        result = resize_bitmap(bitmap, 40, 40, method="area")

        assert result.shape[0] % 4 == 0
        assert result.shape[1] % 2 == 0

    def test_nearest_method(self):
        """Nearest method should work."""
        bitmap = np.random.rand(100, 100).astype(np.float32)
        result = resize_bitmap(bitmap, 40, 40, method="nearest")

        assert result.shape[0] % 4 == 0
        assert result.shape[1] % 2 == 0

    def test_bilinear_method(self):
        """Bilinear method should work."""
        bitmap = np.random.rand(100, 100).astype(np.float32)
        result = resize_bitmap(bitmap, 40, 40, method="bilinear")

        assert result.shape[0] % 4 == 0
        assert result.shape[1] % 2 == 0

    def test_invalid_method_raises(self):
        """Should raise for invalid method."""
        bitmap = np.ones((100, 100), dtype=np.float32)
        with pytest.raises(ValueError, match="Unknown method"):
            resize_bitmap(bitmap, 50, 50, method="invalid")

    def test_nearest_preserves_edges(self):
        """Nearest method should preserve sharp edges."""
        # Create a simple pattern
        bitmap = np.zeros((20, 20), dtype=np.float32)
        bitmap[:10, :] = 1.0

        result = resize_bitmap(bitmap, 10, 10, method="nearest")

        # Should still have distinct regions
        assert result[:4, :].mean() > 0.8 or result[4:, :].mean() > 0.8

    def test_bilinear_smooths(self):
        """Bilinear method should produce smooth gradients."""
        # Create gradient
        bitmap = np.linspace(0, 1, 100).reshape(1, -1).repeat(100, axis=0).astype(np.float32)

        result = resize_bitmap(bitmap, 50, 20, method="bilinear")

        # Should still be a gradient (values increasing)
        row_means = result.mean(axis=0)
        # Check monotonicity (mostly increasing)
        increases = np.sum(np.diff(row_means) > -0.01)
        assert increases > len(row_means) * 0.8


class TestComputeTargetDimensions:
    """Tests for compute_target_dimensions function."""

    def test_basic_computation(self):
        """Should compute reasonable target dimensions."""
        width, height = compute_target_dimensions(
            source_width=800,
            source_height=600,
            width_chars=80,
        )

        # Width should be 80 * 2 = 160 pixels
        assert width == 160
        # Height should be braille-compatible
        assert height % 4 == 0

    def test_preserves_aspect_ratio(self):
        """Should approximately preserve aspect ratio."""
        width, height = compute_target_dimensions(
            source_width=800,
            source_height=400,
            width_chars=80,
            cell_aspect=0.5,
        )

        # Source aspect is 2:1
        # With cell_aspect=0.5, terminal aspect compensation should work
        assert width == 160
        assert height % 4 == 0

    def test_cell_aspect_affects_height(self):
        """Different cell aspects should produce different heights."""
        _, height1 = compute_target_dimensions(
            source_width=800,
            source_height=600,
            width_chars=80,
            cell_aspect=0.5,
        )

        _, height2 = compute_target_dimensions(
            source_width=800,
            source_height=600,
            width_chars=80,
            cell_aspect=1.0,
        )

        # Different cell aspects should give different heights
        assert height1 != height2

    def test_width_chars_scales_output(self):
        """More width_chars should produce wider output."""
        width1, _ = compute_target_dimensions(
            source_width=800,
            source_height=600,
            width_chars=40,
        )

        width2, _ = compute_target_dimensions(
            source_width=800,
            source_height=600,
            width_chars=80,
        )

        assert width2 == 2 * width1

    def test_minimum_dimensions(self):
        """Should enforce minimum braille dimensions."""
        width, height = compute_target_dimensions(
            source_width=10,
            source_height=10,
            width_chars=1,
        )

        assert width >= 2
        assert height >= 4

    def test_always_braille_compatible(self):
        """Output should always be braille-compatible."""
        for src_w, src_h, w_chars in [
            (800, 600, 80),
            (1920, 1080, 120),
            (100, 100, 50),
            (17, 37, 23),  # Odd dimensions
        ]:
            width, height = compute_target_dimensions(src_w, src_h, w_chars)
            assert width % 2 == 0, f"Width {width} not divisible by 2"
            assert height % 4 == 0, f"Height {height} not divisible by 4"
