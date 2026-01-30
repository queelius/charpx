"""Tests for dapple.color module."""

import numpy as np
import pytest

from dapple.color import LUM_R, LUM_G, LUM_B, luminance


class TestLuminanceConstants:
    """Verify ITU-R BT.601 coefficients."""

    def test_coefficients_sum_to_one(self):
        assert abs(LUM_R + LUM_G + LUM_B - 1.0) < 1e-10

    def test_coefficient_values(self):
        assert LUM_R == 0.299
        assert LUM_G == 0.587
        assert LUM_B == 0.114


class TestLuminance:
    """Test luminance() function."""

    def test_pure_red(self):
        rgb = np.array([[[1.0, 0.0, 0.0]]], dtype=np.float32)
        result = luminance(rgb)
        np.testing.assert_allclose(result, [[0.299]], atol=1e-6)

    def test_pure_green(self):
        rgb = np.array([[[0.0, 1.0, 0.0]]], dtype=np.float32)
        result = luminance(rgb)
        np.testing.assert_allclose(result, [[0.587]], atol=1e-6)

    def test_pure_blue(self):
        rgb = np.array([[[0.0, 0.0, 1.0]]], dtype=np.float32)
        result = luminance(rgb)
        np.testing.assert_allclose(result, [[0.114]], atol=1e-6)

    def test_white(self):
        rgb = np.array([[[1.0, 1.0, 1.0]]], dtype=np.float32)
        result = luminance(rgb)
        np.testing.assert_allclose(result, [[1.0]], atol=1e-6)

    def test_black(self):
        rgb = np.array([[[0.0, 0.0, 0.0]]], dtype=np.float32)
        result = luminance(rgb)
        np.testing.assert_allclose(result, [[0.0]], atol=1e-6)

    def test_shape_2d_image(self):
        """luminance of (H, W, 3) -> (H, W)."""
        rgb = np.random.rand(10, 20, 3).astype(np.float32)
        result = luminance(rgb)
        assert result.shape == (10, 20)

    def test_shape_4d_blocks(self):
        """luminance of (rows, cols, cells, 3) -> (rows, cols, cells)."""
        rgb = np.random.rand(5, 10, 4, 3).astype(np.float32)
        result = luminance(rgb)
        assert result.shape == (5, 10, 4)

    def test_dtype_float32(self):
        rgb = np.random.rand(4, 4, 3).astype(np.float64)
        result = luminance(rgb)
        assert result.dtype == np.float32

    def test_matches_inline_formula(self):
        """Verify result matches the hardcoded formula."""
        rgb = np.random.rand(8, 12, 3).astype(np.float32)
        expected = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        result = luminance(rgb)
        np.testing.assert_allclose(result, expected, atol=1e-6)
