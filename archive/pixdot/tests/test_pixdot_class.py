"""Tests for PixDot class."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from pixdot import PixDot


class TestConstruction:
    """Tests for PixDot construction."""

    def test_basic_construction(self):
        """PixDot can be created from a 2D bitmap."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        dot = PixDot(bitmap)
        assert dot.pixel_width == 80
        assert dot.pixel_height == 40

    def test_construction_with_threshold(self):
        """PixDot accepts custom threshold."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap, threshold=0.3)
        assert dot.threshold == 0.3

    def test_construction_with_none_threshold(self):
        """PixDot accepts None threshold for auto-detection."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap, threshold=None)
        assert dot.threshold is None

    def test_construction_with_color_mode(self):
        """PixDot accepts color mode parameter."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap, color_mode="grayscale")
        assert dot.color_mode == "grayscale"

    def test_construction_with_colors(self):
        """PixDot accepts RGB colors array."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        colors = np.random.rand(20, 40, 3).astype(np.float32)
        dot = PixDot(bitmap, color_mode="truecolor", colors=colors)
        assert dot.colors is not None
        assert dot.colors.shape == (20, 40, 3)

    def test_rejects_1d_array(self):
        """PixDot rejects 1D arrays."""
        with pytest.raises(ValueError, match="must be 2D"):
            PixDot(np.array([1, 2, 3]))

    def test_rejects_3d_array(self):
        """PixDot rejects 3D arrays for bitmap."""
        with pytest.raises(ValueError, match="must be 2D"):
            PixDot(np.random.rand(10, 20, 3))

    def test_rejects_mismatched_colors_shape(self):
        """PixDot rejects colors with wrong spatial dimensions."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        colors = np.random.rand(10, 20, 3).astype(np.float32)  # Wrong size
        with pytest.raises(ValueError, match="must match bitmap shape"):
            PixDot(bitmap, colors=colors)

    def test_rejects_colors_without_3_channels(self):
        """PixDot rejects colors that aren't (H, W, 3)."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        colors = np.random.rand(20, 40, 4).astype(np.float32)  # 4 channels
        with pytest.raises(ValueError, match="must be \\(H, W, 3\\)"):
            PixDot(bitmap, colors=colors)

    def test_converts_to_float32(self):
        """PixDot converts bitmap to float32."""
        bitmap = np.random.rand(20, 40).astype(np.float64)
        dot = PixDot(bitmap)
        assert dot.bitmap.dtype == np.float32


class TestProperties:
    """Tests for PixDot properties."""

    def test_pixel_dimensions(self):
        """pixel_width and pixel_height match bitmap shape."""
        bitmap = np.random.rand(32, 64).astype(np.float32)
        dot = PixDot(bitmap)
        assert dot.pixel_width == 64
        assert dot.pixel_height == 32

    def test_char_dimensions(self):
        """width and height give character dimensions."""
        bitmap = np.random.rand(32, 64).astype(np.float32)
        dot = PixDot(bitmap)
        # 64 pixels / 2 = 32 chars wide
        # 32 pixels / 4 = 8 chars tall
        assert dot.width == 32
        assert dot.height == 8

    def test_char_dimensions_round_up(self):
        """Character dimensions round up for partial characters."""
        bitmap = np.random.rand(33, 65).astype(np.float32)
        dot = PixDot(bitmap)
        # 65 pixels -> (65 + 1) // 2 = 33 chars wide
        # 33 pixels -> (33 + 3) // 4 = 9 chars tall
        assert dot.width == 33
        assert dot.height == 9

    def test_shape_numpy_convention(self):
        """shape returns (height, width) like numpy."""
        bitmap = np.random.rand(32, 64).astype(np.float32)
        dot = PixDot(bitmap)
        assert dot.shape == (32, 64)

    def test_size_pil_convention(self):
        """size returns (width, height) like PIL."""
        bitmap = np.random.rand(32, 64).astype(np.float32)
        dot = PixDot(bitmap)
        assert dot.size == (64, 32)

    def test_bitmap_readonly(self):
        """bitmap property returns read-only view."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap)
        view = dot.bitmap
        with pytest.raises((ValueError, TypeError)):
            view[0, 0] = 999.0

    def test_colors_readonly(self):
        """colors property returns read-only view."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        colors = np.random.rand(20, 40, 3).astype(np.float32)
        dot = PixDot(bitmap, colors=colors)
        view = dot.colors
        with pytest.raises((ValueError, TypeError)):
            view[0, 0, 0] = 999.0

    def test_colors_none_when_not_set(self):
        """colors is None when not provided."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap)
        assert dot.colors is None


class TestStringRendering:
    """Tests for __str__ and __repr__."""

    def test_str_renders_braille(self):
        """__str__ produces braille characters."""
        bitmap = np.eye(8, dtype=np.float32)
        dot = PixDot(bitmap, threshold=0.5)
        result = str(dot)
        # Should contain braille characters
        assert any('\u2800' <= c <= '\u28FF' for c in result)

    def test_str_cached(self):
        """__str__ result is cached."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap)
        result1 = str(dot)
        result2 = str(dot)
        assert result1 is result2  # Same object, not just equal

    def test_repr_format(self):
        """__repr__ shows dimensions and color mode."""
        bitmap = np.random.rand(32, 64).astype(np.float32)
        dot = PixDot(bitmap, color_mode="grayscale")
        result = repr(dot)
        assert "PixDot" in result
        assert "64x32" in result
        assert "grayscale" in result

    def test_str_with_grayscale(self):
        """__str__ works with grayscale color mode."""
        bitmap = np.linspace(0, 1, 80).reshape(4, 20).astype(np.float32)
        dot = PixDot(bitmap, color_mode="grayscale")
        result = str(dot)
        # Should contain ANSI escape codes
        assert "\033[" in result

    def test_str_with_truecolor(self):
        """__str__ works with truecolor mode."""
        bitmap = np.random.rand(8, 16).astype(np.float32)
        colors = np.random.rand(8, 16, 3).astype(np.float32)
        dot = PixDot(bitmap, color_mode="truecolor", colors=colors)
        result = str(dot)
        # Should contain ANSI escape codes
        assert "\033[" in result


class TestPixelAccess:
    """Tests for __getitem__ pixel access."""

    def test_single_pixel_access(self):
        """Can access single pixel by (y, x)."""
        bitmap = np.array([[0.0, 1.0], [0.5, 0.25]], dtype=np.float32)
        dot = PixDot(bitmap)
        assert dot[0, 0] == 0.0
        assert dot[0, 1] == 1.0
        assert dot[1, 0] == 0.5
        assert dot[1, 1] == 0.25

    def test_slice_access(self):
        """Can slice to get new PixDot."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        dot = PixDot(bitmap)
        sliced = dot[10:30, 20:60]
        assert isinstance(sliced, PixDot)
        assert sliced.shape == (20, 40)

    def test_slice_preserves_config(self):
        """Slicing preserves threshold and color mode."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        dot = PixDot(bitmap, threshold=0.3, color_mode="grayscale")
        sliced = dot[0:20, 0:40]
        assert sliced.threshold == 0.3
        assert sliced.color_mode == "grayscale"

    def test_slice_with_colors(self):
        """Slicing includes color data."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        colors = np.random.rand(40, 80, 3).astype(np.float32)
        dot = PixDot(bitmap, colors=colors)
        sliced = dot[10:30, 20:60]
        assert sliced.colors is not None
        assert sliced.colors.shape == (20, 40, 3)


class TestFactoryMethods:
    """Tests for from_string and load."""

    def test_from_string_basic(self):
        """from_string parses braille back to bitmap."""
        # Create original
        bitmap = np.zeros((8, 4), dtype=np.float32)
        bitmap[0, 0] = 1.0  # Top-left dot
        bitmap[3, 1] = 1.0  # Bottom-left dot
        original = PixDot(bitmap, threshold=0.5)
        text = str(original)

        # Parse back
        reconstructed = PixDot.from_string(text)
        assert reconstructed.shape == original.shape
        assert reconstructed[0, 0] == 1.0
        assert reconstructed[3, 1] == 1.0

    def test_from_string_roundtrip(self):
        """from_string can reconstruct simple patterns."""
        # Create a checkerboard pattern
        bitmap = np.zeros((8, 8), dtype=np.float32)
        bitmap[::2, ::2] = 1.0
        bitmap[1::2, 1::2] = 1.0
        original = PixDot(bitmap, threshold=0.5)
        text = str(original)

        reconstructed = PixDot.from_string(text)
        np.testing.assert_array_equal(original.bitmap, reconstructed.bitmap)

    def test_from_string_strips_ansi(self):
        """from_string strips ANSI codes."""
        bitmap = np.random.rand(8, 16).astype(np.float32)
        dot = PixDot(bitmap, color_mode="grayscale")
        colored_text = str(dot)

        # Should parse without error
        reconstructed = PixDot.from_string(colored_text)
        assert reconstructed.shape[0] > 0

    def test_from_string_empty(self):
        """from_string handles empty string."""
        result = PixDot.from_string("")
        assert result.shape == (0, 0)

    def test_load_saves_and_loads(self):
        """load can read files written by write."""
        bitmap = np.eye(8, dtype=np.float32)
        original = PixDot(bitmap, threshold=0.5)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            path = f.name
            original.write(path)

        try:
            loaded = PixDot.load(path)
            # Compare rendered strings
            assert str(original) == str(loaded)
        finally:
            Path(path).unlink()


class TestBuilderMethods:
    """Tests for with_threshold, with_color, with_invert."""

    def test_with_threshold_returns_new_pixdot(self):
        """with_threshold returns a new PixDot."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        original = PixDot(bitmap, threshold=0.5)
        modified = original.with_threshold(0.3)

        assert modified is not original
        assert modified.threshold == 0.3
        assert original.threshold == 0.5

    def test_with_threshold_preserves_color_mode(self):
        """with_threshold preserves color mode."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        original = PixDot(bitmap, color_mode="grayscale")
        modified = original.with_threshold(0.3)
        assert modified.color_mode == "grayscale"

    def test_with_color_changes_mode(self):
        """with_color changes the color mode."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        original = PixDot(bitmap, color_mode="none")
        modified = original.with_color("grayscale")

        assert modified.color_mode == "grayscale"
        assert original.color_mode == "none"

    def test_with_color_adds_colors(self):
        """with_color can add color data."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        colors = np.random.rand(20, 40, 3).astype(np.float32)
        original = PixDot(bitmap)
        modified = original.with_color("truecolor", colors)

        assert modified.colors is not None
        assert original.colors is None

    def test_with_invert_inverts_bitmap(self):
        """with_invert inverts pixel values."""
        bitmap = np.array([[0.0, 1.0], [0.25, 0.75]], dtype=np.float32)
        original = PixDot(bitmap)
        inverted = original.with_invert()

        np.testing.assert_array_almost_equal(
            inverted.bitmap, [[1.0, 0.0], [0.75, 0.25]]
        )

    def test_with_invert_inverts_colors(self):
        """with_invert inverts color data too."""
        bitmap = np.array([[0.0, 1.0]], dtype=np.float32)
        colors = np.array([[[0.0, 0.5, 1.0], [1.0, 0.5, 0.0]]], dtype=np.float32)
        original = PixDot(bitmap, colors=colors)
        inverted = original.with_invert()

        expected_colors = np.array([[[1.0, 0.5, 0.0], [0.0, 0.5, 1.0]]])
        np.testing.assert_array_almost_equal(inverted.colors, expected_colors)

    def test_builders_dont_share_bitmap(self):
        """Builder methods create independent copies."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        original = PixDot(bitmap)
        modified = original.with_threshold(0.3)

        # Modify original's internal state (shouldn't affect modified)
        # Note: We can't modify directly due to read-only, but we verify independence
        assert not np.shares_memory(original._bitmap, modified._bitmap)


class TestComposition:
    """Tests for hstack, vstack, overlay, crop."""

    def test_hstack_combines_horizontally(self):
        """hstack combines two PixDots horizontally."""
        left = PixDot(np.ones((20, 10), dtype=np.float32))
        right = PixDot(np.zeros((20, 10), dtype=np.float32))
        combined = left.hstack(right)

        assert combined.shape == (20, 20)
        assert combined[0, 0] == 1.0  # From left
        assert combined[0, 10] == 0.0  # From right

    def test_hstack_pads_shorter_height(self):
        """hstack pads the shorter PixDot with zeros."""
        tall = PixDot(np.ones((30, 10), dtype=np.float32))
        short = PixDot(np.ones((20, 10), dtype=np.float32))
        combined = tall.hstack(short)

        assert combined.shape == (30, 20)
        # Bottom of short side should be zeros
        assert combined[25, 15] == 0.0

    def test_add_operator_is_hstack(self):
        """+ operator is equivalent to hstack."""
        left = PixDot(np.ones((20, 10), dtype=np.float32))
        right = PixDot(np.zeros((20, 10), dtype=np.float32))
        combined = left + right

        assert combined.shape == (20, 20)

    def test_vstack_combines_vertically(self):
        """vstack combines two PixDots vertically."""
        top = PixDot(np.ones((10, 20), dtype=np.float32))
        bottom = PixDot(np.zeros((10, 20), dtype=np.float32))
        combined = top.vstack(bottom)

        assert combined.shape == (20, 20)
        assert combined[0, 0] == 1.0  # From top
        assert combined[10, 0] == 0.0  # From bottom

    def test_vstack_pads_narrower_width(self):
        """vstack pads the narrower PixDot with zeros."""
        wide = PixDot(np.ones((10, 30), dtype=np.float32))
        narrow = PixDot(np.ones((10, 20), dtype=np.float32))
        combined = wide.vstack(narrow)

        assert combined.shape == (20, 30)
        # Right side of narrow should be zeros
        assert combined[15, 25] == 0.0

    def test_overlay_places_at_position(self):
        """overlay places another PixDot at specified position."""
        base = PixDot(np.zeros((20, 20), dtype=np.float32))
        stamp = PixDot(np.ones((5, 5), dtype=np.float32))
        result = base.overlay(stamp, x=10, y=10)

        assert result.shape == (20, 20)
        assert result[5, 5] == 0.0  # Outside stamp
        assert result[12, 12] == 1.0  # Inside stamp

    def test_overlay_extends_if_needed(self):
        """overlay extends bitmap if stamp goes beyond."""
        base = PixDot(np.zeros((10, 10), dtype=np.float32))
        stamp = PixDot(np.ones((5, 5), dtype=np.float32))
        result = base.overlay(stamp, x=8, y=8)

        assert result.shape == (13, 13)  # Extended to fit stamp

    def test_crop_extracts_region(self):
        """crop extracts a rectangular region."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        dot = PixDot(bitmap)
        cropped = dot.crop(10, 5, 50, 25)

        assert cropped.shape == (20, 40)
        np.testing.assert_array_equal(cropped.bitmap, bitmap[5:25, 10:50])

    def test_crop_chars_uses_character_coords(self):
        """crop_chars uses character coordinates."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        dot = PixDot(bitmap)
        # 1 char = 2x4 pixels
        cropped = dot.crop_chars(5, 2, 20, 8)

        # x: 5*2=10 to 20*2=40, y: 2*4=8 to 8*4=32
        assert cropped.shape == (24, 30)

    def test_hstack_with_colors(self):
        """hstack handles color data."""
        bitmap1 = np.ones((20, 10), dtype=np.float32)
        colors1 = np.ones((20, 10, 3), dtype=np.float32) * 0.5
        bitmap2 = np.zeros((20, 10), dtype=np.float32)
        colors2 = np.zeros((20, 10, 3), dtype=np.float32)

        left = PixDot(bitmap1, colors=colors1)
        right = PixDot(bitmap2, colors=colors2)
        combined = left.hstack(right)

        assert combined.colors is not None
        assert combined.colors.shape == (20, 20, 3)
        np.testing.assert_array_almost_equal(combined.colors[0, 0], [0.5, 0.5, 0.5])
        np.testing.assert_array_almost_equal(combined.colors[0, 10], [0.0, 0.0, 0.0])


class TestConversion:
    """Tests for to_bitmap, to_pil, save, write."""

    def test_to_bitmap_returns_copy(self):
        """to_bitmap returns a copy, not the original."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap)
        result = dot.to_bitmap()

        assert not np.shares_memory(result, dot._bitmap)
        np.testing.assert_array_equal(result, bitmap)

    def test_to_pil_grayscale(self):
        """to_pil creates grayscale PIL Image."""
        pytest.importorskip("PIL")
        from PIL import Image

        bitmap = np.array([[0.0, 0.5], [0.5, 1.0]], dtype=np.float32)
        dot = PixDot(bitmap)
        img = dot.to_pil()

        assert isinstance(img, Image.Image)
        assert img.mode == "L"
        assert img.size == (2, 2)

    def test_to_pil_rgb(self):
        """to_pil creates RGB PIL Image when colors set."""
        pytest.importorskip("PIL")
        from PIL import Image

        bitmap = np.array([[0.5, 0.5]], dtype=np.float32)
        colors = np.array([[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]], dtype=np.float32)
        dot = PixDot(bitmap, colors=colors)
        img = dot.to_pil()

        assert isinstance(img, Image.Image)
        assert img.mode == "RGB"
        assert img.getpixel((0, 0)) == (255, 0, 0)

    def test_save_creates_file(self):
        """save creates an image file."""
        pytest.importorskip("PIL")

        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap)

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            path = f.name
            dot.save(path)

        try:
            assert Path(path).exists()
            assert Path(path).stat().st_size > 0
        finally:
            Path(path).unlink()

    def test_write_creates_text_file(self):
        """write creates a text file with braille."""
        bitmap = np.eye(8, dtype=np.float32)
        dot = PixDot(bitmap)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            path = f.name
            dot.write(path)

        try:
            content = Path(path).read_text(encoding='utf-8')
            assert content == str(dot)
        finally:
            Path(path).unlink()


class TestRoundtrip:
    """Tests for roundtrip conversions."""

    def test_string_roundtrip(self):
        """String roundtrip preserves pattern."""
        # Simple pattern that survives encoding/decoding
        bitmap = np.zeros((8, 4), dtype=np.float32)
        bitmap[0, 0] = 1.0
        bitmap[1, 1] = 1.0
        bitmap[2, 0] = 1.0
        bitmap[3, 1] = 1.0

        original = PixDot(bitmap, threshold=0.5)
        text = str(original)
        reconstructed = PixDot.from_string(text)

        np.testing.assert_array_equal(original.bitmap, reconstructed.bitmap)

    def test_file_roundtrip(self):
        """File roundtrip preserves pattern."""
        bitmap = np.eye(8, dtype=np.float32)
        original = PixDot(bitmap, threshold=0.5)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            path = f.name
            original.write(path)

        try:
            loaded = PixDot.load(path)
            np.testing.assert_array_equal(original.bitmap, loaded.bitmap)
        finally:
            Path(path).unlink()


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_bitmap(self):
        """Empty bitmap works correctly."""
        bitmap = np.zeros((0, 0), dtype=np.float32)
        dot = PixDot(bitmap)
        assert str(dot) == ""

    def test_single_pixel(self):
        """Single pixel bitmap works."""
        bitmap = np.array([[1.0]], dtype=np.float32)
        dot = PixDot(bitmap)
        result = str(dot)
        assert len(result) == 1
        assert '\u2800' <= result <= '\u28FF'

    def test_single_row(self):
        """Single row bitmap works."""
        bitmap = np.ones((1, 10), dtype=np.float32)
        dot = PixDot(bitmap)
        result = str(dot)
        assert '\n' not in result

    def test_single_column(self):
        """Single column bitmap works."""
        bitmap = np.ones((10, 1), dtype=np.float32)
        dot = PixDot(bitmap)
        result = str(dot)
        lines = result.split('\n')
        assert all(len(line) == 1 for line in lines)

    def test_non_divisible_dimensions(self):
        """Non-divisible dimensions work correctly."""
        # 7x5 doesn't divide evenly by 4x2
        bitmap = np.random.rand(7, 5).astype(np.float32)
        dot = PixDot(bitmap)
        result = str(dot)
        lines = result.split('\n')
        # Should have (7 + 3) // 4 = 2 rows
        assert len(lines) == 2
        # Should have (5 + 1) // 2 = 3 columns
        assert all(len(line) == 3 for line in lines)

    def test_overlay_negative_position(self):
        """Overlay handles negative positions."""
        base = PixDot(np.zeros((10, 10), dtype=np.float32))
        stamp = PixDot(np.ones((5, 5), dtype=np.float32))
        result = base.overlay(stamp, x=-2, y=-2)

        # Only the visible part of stamp should appear
        assert result[0, 0] == 1.0
        assert result[0, 2] == 1.0
        assert result[2, 0] == 1.0

    def test_crop_with_copy(self):
        """Crop returns independent copy."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        dot = PixDot(bitmap)
        cropped = dot.crop(10, 10, 30, 30)

        # Verify they don't share memory
        assert not np.shares_memory(cropped._bitmap, dot._bitmap)


class TestIntegration:
    """Integration tests combining multiple features."""

    def test_chain_builders(self):
        """Can chain multiple builder calls."""
        bitmap = np.random.rand(20, 40).astype(np.float32)
        dot = PixDot(bitmap)
        result = dot.with_threshold(0.3).with_color("grayscale").with_invert()

        assert result.threshold == 0.3
        assert result.color_mode == "grayscale"

    def test_compose_then_render(self):
        """Can compose multiple PixDots then render."""
        left = PixDot(np.ones((20, 20), dtype=np.float32))
        right = PixDot(np.zeros((20, 20), dtype=np.float32))
        combined = left + right
        result = str(combined)

        # Should be able to render
        assert len(result) > 0

    def test_slice_crop_roundtrip(self):
        """Slicing and cropping give same results."""
        bitmap = np.random.rand(40, 80).astype(np.float32)
        dot = PixDot(bitmap)

        sliced = dot[10:30, 20:60]
        cropped = dot.crop(20, 10, 60, 30)

        np.testing.assert_array_equal(sliced.bitmap, cropped.bitmap)

    def test_multiple_overlays(self):
        """Can apply multiple overlays."""
        base = PixDot(np.zeros((40, 40), dtype=np.float32))
        stamp1 = PixDot(np.ones((10, 10), dtype=np.float32))
        stamp2 = PixDot(np.ones((10, 10), dtype=np.float32) * 0.5)

        result = base.overlay(stamp1, 5, 5).overlay(stamp2, 20, 20)

        assert result[10, 10] == 1.0  # stamp1
        assert result[25, 25] == 0.5  # stamp2
        assert result[0, 0] == 0.0   # background
