"""Unit tests for the pixdot.ansi module."""

import numpy as np
import pytest

from pixdot import render_ansi, RESET, ColorMode
from pixdot.ansi import grayscale_fg, truecolor_fg


class TestGrayscaleFg:
    """Tests for grayscale foreground escape codes."""

    def test_darkest_level(self):
        """Level 0 should produce code 232."""
        assert grayscale_fg(0) == "\033[38;5;232m"

    def test_brightest_level(self):
        """Level 23 should produce code 255."""
        assert grayscale_fg(23) == "\033[38;5;255m"

    def test_mid_level(self):
        """Level 12 should produce code 244."""
        assert grayscale_fg(12) == "\033[38;5;244m"

    def test_clamps_negative(self):
        """Negative levels should clamp to 0 (code 232)."""
        assert grayscale_fg(-5) == "\033[38;5;232m"

    def test_clamps_over_max(self):
        """Levels over 23 should clamp to 23 (code 255)."""
        assert grayscale_fg(100) == "\033[38;5;255m"


class TestTruecolorFg:
    """Tests for truecolor foreground escape codes."""

    def test_black(self):
        """Black should produce (0, 0, 0)."""
        assert truecolor_fg(0, 0, 0) == "\033[38;2;0;0;0m"

    def test_white(self):
        """White should produce (255, 255, 255)."""
        assert truecolor_fg(255, 255, 255) == "\033[38;2;255;255;255m"

    def test_red(self):
        """Red should produce (255, 0, 0)."""
        assert truecolor_fg(255, 0, 0) == "\033[38;2;255;0;0m"

    def test_green(self):
        """Green should produce (0, 255, 0)."""
        assert truecolor_fg(0, 255, 0) == "\033[38;2;0;255;0m"

    def test_blue(self):
        """Blue should produce (0, 0, 255)."""
        assert truecolor_fg(0, 0, 255) == "\033[38;2;0;0;255m"

    def test_clamps_negative(self):
        """Negative values should clamp to 0."""
        assert truecolor_fg(-10, -20, -30) == "\033[38;2;0;0;0m"

    def test_clamps_over_max(self):
        """Values over 255 should clamp to 255."""
        assert truecolor_fg(300, 400, 500) == "\033[38;2;255;255;255m"


class TestRenderAnsi:
    """Tests for render_ansi function."""

    def test_output_dimensions_grayscale(self):
        """Output should have correct dimensions (height/4 rows, width/2 cols)."""
        bitmap = np.zeros((16, 8), dtype=np.float32)
        result = render_ansi(bitmap, color_mode="grayscale")

        lines = result.split('\n')
        assert len(lines) == 4  # 16 / 4

    def test_output_dimensions_truecolor(self):
        """Output should have correct dimensions with truecolor."""
        bitmap = np.zeros((16, 8), dtype=np.float32)
        result = render_ansi(bitmap, color_mode="truecolor")

        lines = result.split('\n')
        assert len(lines) == 4  # 16 / 4

    def test_contains_escape_codes_grayscale(self):
        """Output should contain grayscale escape codes."""
        bitmap = np.ones((4, 2), dtype=np.float32) * 0.5
        result = render_ansi(bitmap, color_mode="grayscale")

        assert "\033[38;5;" in result  # Contains grayscale code
        assert RESET in result  # Contains reset

    def test_contains_escape_codes_truecolor(self):
        """Output should contain truecolor escape codes."""
        bitmap = np.ones((4, 2), dtype=np.float32) * 0.5
        result = render_ansi(bitmap, color_mode="truecolor")

        assert "\033[38;2;" in result  # Contains truecolor code
        assert RESET in result  # Contains reset

    def test_none_mode_delegates_to_plain_render(self):
        """color_mode='none' should produce plain braille without escape codes."""
        bitmap = np.ones((4, 2), dtype=np.float32)
        result = render_ansi(bitmap, color_mode="none")

        assert "\033" not in result  # No escape codes
        assert result == '\u28ff'  # Full braille character

    def test_grayscale_brightness_varies_color(self):
        """Different brightness values should produce different grayscale codes."""
        # Dark region
        dark_bitmap = np.zeros((4, 2), dtype=np.float32)
        dark_result = render_ansi(dark_bitmap, threshold=0.0, color_mode="grayscale")

        # Bright region
        bright_bitmap = np.ones((4, 2), dtype=np.float32)
        bright_result = render_ansi(bright_bitmap, color_mode="grayscale")

        # Should have different color codes
        assert dark_result != bright_result
        # Dark should have lower grayscale code (closer to 232)
        assert "232" in dark_result or "233" in dark_result
        # Bright should have higher grayscale code (closer to 255)
        assert "254" in bright_result or "255" in bright_result

    def test_with_colors_array(self):
        """Should use colors array when provided in truecolor mode."""
        bitmap = np.ones((4, 2), dtype=np.float32)
        # Pure red colors
        colors = np.zeros((4, 2, 3), dtype=np.float32)
        colors[:, :, 0] = 1.0  # Red channel

        result = render_ansi(bitmap, color_mode="truecolor", colors=colors)

        # Should contain red color code (255, 0, 0)
        assert "255;0;0" in result

    def test_rejects_non_2d_bitmap(self):
        """Should reject non-2D bitmap."""
        with pytest.raises(ValueError, match="must be 2D"):
            render_ansi(np.zeros((4, 2, 3)), color_mode="grayscale")

    def test_rejects_invalid_colors_shape(self):
        """Should reject colors with wrong shape."""
        bitmap = np.zeros((4, 2), dtype=np.float32)
        colors = np.zeros((4, 2), dtype=np.float32)  # 2D instead of 3D

        with pytest.raises(ValueError, match="colors must be"):
            render_ansi(bitmap, colors=colors, color_mode="truecolor")

    def test_rejects_mismatched_colors_dimensions(self):
        """Should reject colors with dimensions not matching bitmap."""
        bitmap = np.zeros((4, 2), dtype=np.float32)
        colors = np.zeros((8, 4, 3), dtype=np.float32)  # Different H, W

        with pytest.raises(ValueError, match="must match bitmap shape"):
            render_ansi(bitmap, colors=colors, color_mode="truecolor")

    def test_threshold_auto_detect(self):
        """threshold=None should auto-detect from bitmap mean."""
        bitmap = np.zeros((8, 4), dtype=np.float32)
        bitmap[0:4, :] = 1.0  # top half white

        result = render_ansi(bitmap, threshold=None, color_mode="grayscale")
        assert len(result) > 0

    def test_gradient_produces_varied_colors(self):
        """Horizontal gradient should produce varied grayscale levels."""
        # Create horizontal gradient from 0 to 1
        bitmap = np.linspace(0, 1, 80).reshape(1, -1).repeat(4, axis=0).astype(np.float32)
        result = render_ansi(bitmap, color_mode="grayscale")

        # Should have at least a few different grayscale codes
        # Count unique grayscale codes in the result
        import re
        codes = re.findall(r'\033\[38;5;(\d+)m', result)
        unique_codes = set(codes)
        assert len(unique_codes) >= 5  # Should have some variety

    def test_reset_at_end_of_each_line(self):
        """Each line should end with RESET code."""
        bitmap = np.ones((8, 4), dtype=np.float32)
        result = render_ansi(bitmap, color_mode="grayscale")

        lines = result.split('\n')
        for line in lines:
            assert line.endswith(RESET)


class TestRenderAnsiIntegration:
    """Integration tests for render_ansi with various inputs."""

    def test_single_cell(self):
        """Single 2x4 region should produce single colored character."""
        bitmap = np.ones((4, 2), dtype=np.float32)
        result = render_ansi(bitmap, color_mode="grayscale")

        # Should be: color_code + braille_char + reset
        assert result.count('\u28ff') == 1  # One full braille char
        assert result.count(RESET) == 1

    def test_multiple_cells_per_row(self):
        """Multiple cells in a row should each have their own color."""
        bitmap = np.zeros((4, 6), dtype=np.float32)
        bitmap[:, 0:2] = 0.2  # First cell dark
        bitmap[:, 2:4] = 0.5  # Second cell mid
        bitmap[:, 4:6] = 0.8  # Third cell bright

        result = render_ansi(bitmap, color_mode="grayscale")

        # Should have 3 color codes (one per cell)
        import re
        codes = re.findall(r'\033\[38;5;(\d+)m', result)
        assert len(codes) == 3

        # Codes should be in increasing order (darker to brighter)
        assert int(codes[0]) < int(codes[1]) < int(codes[2])

    def test_large_bitmap(self):
        """Should handle larger bitmaps correctly."""
        bitmap = np.random.rand(100, 80).astype(np.float32)
        result = render_ansi(bitmap, color_mode="grayscale")

        lines = result.split('\n')
        assert len(lines) == 25  # 100 / 4

    def test_odd_dimensions(self):
        """Should handle odd dimensions by padding."""
        bitmap = np.ones((5, 3), dtype=np.float32)
        result = render_ansi(bitmap, color_mode="grayscale")

        # Should produce output (with padding)
        lines = result.split('\n')
        assert len(lines) == 2  # ceil(5/4) = 2
