"""Tests for chop CLI with lazy pipeline architecture."""

from __future__ import annotations

import io
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

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
    op_pad,
    op_border,
    op_fit,
    op_fill,
    op_hstack,
    op_vstack,
    op_overlay,
    op_tile,
    op_grid,
    apply_operation,
    OPERATIONS,
)
from chop.pipeline import (
    PipelineState,
    load_image,
    image_to_arrays,
)
from chop.render import auto_detect_renderer, RENDERERS
from chop.output import handle_output
from chop.dsl import parse_program, parse_operation, parse_value, load_program


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

    def test_pad_uniform(self, test_image: Image.Image):
        """Test uniform padding (1 value)."""
        result = op_pad(test_image, 10)
        assert result.size == (120, 100)  # 100+10+10, 80+10+10

    def test_pad_vertical_horizontal(self, test_image: Image.Image):
        """Test vertical/horizontal padding (2 values)."""
        result = op_pad(test_image, 10, 20)  # 10 top/bottom, 20 left/right
        assert result.size == (140, 100)  # 100+20+20, 80+10+10

    def test_pad_all_sides(self, test_image: Image.Image):
        """Test all-sides padding (4 values, CSS order)."""
        result = op_pad(test_image, 10, 20, 30, 40)  # top, right, bottom, left
        assert result.size == (160, 120)  # 100+20+40, 80+10+30

    def test_pad_with_color(self, test_image: Image.Image):
        """Test padding with specific color."""
        result = op_pad(test_image, 10, color="red")
        assert result.size == (120, 100)
        # Check corner pixel is red
        pixel = result.getpixel((0, 0))
        assert pixel[:3] == (255, 0, 0)

    def test_pad_transparent(self, test_image: Image.Image):
        """Test transparent padding (default)."""
        result = op_pad(test_image, 10)
        pixel = result.getpixel((0, 0))
        assert pixel[3] == 0  # Alpha = 0 (transparent)

    def test_border(self, test_image: Image.Image):
        """Test border adds uniform border."""
        result = op_border(test_image, 5)
        assert result.size == (110, 90)  # 100+5+5, 80+5+5

    def test_border_with_color(self, test_image: Image.Image):
        """Test border with specific color."""
        result = op_border(test_image, 5, color="#00ff00")
        pixel = result.getpixel((0, 0))
        assert pixel[:3] == (0, 255, 0)  # Green

    def test_fit_landscape_to_square(self, test_image: Image.Image):
        """Test fit scales to fit within bounds."""
        # test_image is 100x80, fit to 50x50 should give 50x40 (landscape fits width)
        result = op_fit(test_image, "50x50")
        assert result.size == (50, 40)

    def test_fit_preserves_aspect(self, test_image: Image.Image):
        """Test fit preserves aspect ratio."""
        result = op_fit(test_image, "200x100")
        # 100x80 image, fitting to 200x100
        # Scale by width: 200/100 = 2.0 → 200x160 (too tall)
        # Scale by height: 100/80 = 1.25 → 125x100 (fits)
        assert result.size == (125, 100)

    def test_fill_crops_to_exact_size(self, test_image: Image.Image):
        """Test fill gives exact target size."""
        result = op_fill(test_image, "50x50")
        assert result.size == (50, 50)  # Exact target

    def test_fill_center_crops(self, test_image: Image.Image):
        """Test fill scales and center-crops."""
        # 100x80 → fill 80x80
        # Scale to fill: max(80/100, 80/80) = 1.0 → 100x80
        # Center crop to 80x80
        result = op_fill(test_image, "80x80")
        assert result.size == (80, 80)


class TestOperationsRegistry:
    """Tests for the operations registry and apply_operation."""

    def test_registry_contains_basic_ops(self):
        """Test that basic operations are in the registry."""
        assert "resize" in OPERATIONS
        assert "crop" in OPERATIONS
        assert "rotate" in OPERATIONS
        assert "flip" in OPERATIONS
        assert "pad" in OPERATIONS
        assert "border" in OPERATIONS
        assert "fit" in OPERATIONS
        assert "fill" in OPERATIONS

    def test_registry_excludes_removed_ops(self):
        """Test that image processing ops were removed."""
        assert "dither" not in OPERATIONS
        assert "invert" not in OPERATIONS
        assert "sharpen" not in OPERATIONS
        assert "contrast" not in OPERATIONS
        assert "gamma" not in OPERATIONS
        assert "threshold" not in OPERATIONS

    def test_apply_operation_resize(self, test_image: Image.Image):
        """Test apply_operation for resize."""
        result = apply_operation(test_image, "resize", "50%")
        assert result.size == (50, 40)

    def test_apply_operation_rotate(self, test_image: Image.Image):
        """Test apply_operation for rotate."""
        result = apply_operation(test_image, "rotate", 90)
        assert result.size[0] == test_image.size[1]

    def test_apply_operation_pad(self, test_image: Image.Image):
        """Test apply_operation for pad with kwargs."""
        result = apply_operation(test_image, "pad", 10, color="red")
        assert result.size == (120, 100)

    def test_apply_operation_border(self, test_image: Image.Image):
        """Test apply_operation for border."""
        result = apply_operation(test_image, "border", 5, color="blue")
        assert result.size == (110, 90)

    def test_apply_operation_fit(self, test_image: Image.Image):
        """Test apply_operation for fit."""
        result = apply_operation(test_image, "fit", "50x50")
        assert result.size == (50, 40)

    def test_apply_operation_fill(self, test_image: Image.Image):
        """Test apply_operation for fill."""
        result = apply_operation(test_image, "fill", "50x50")
        assert result.size == (50, 50)

    def test_apply_operation_unknown(self, test_image: Image.Image):
        """Test apply_operation raises for unknown op."""
        with pytest.raises(ValueError, match="Unknown operation"):
            apply_operation(test_image, "unknown_op")


class TestPipeline:
    """Tests for lazy pipeline utilities."""

    def test_state_creation(self, test_image_file: str):
        """Test creating a PipelineState with path."""
        state = PipelineState(path=test_image_file)
        assert state.path == test_image_file
        assert state.ops == []
        assert state.metadata == {}

    def test_add_op(self, test_image_file: str):
        """Test adding operations to state."""
        state = PipelineState(path=test_image_file)
        state.add_op("resize", "50%")
        state.add_op("pad", 10, color="red")

        assert len(state.ops) == 2
        assert state.ops[0] == ("resize", ("50%",), {})
        assert state.ops[1] == ("pad", (10,), {"color": "red"})

    def test_state_to_json_and_back(self, test_image_file: str):
        """Test JSON serialization roundtrip."""
        state = PipelineState(
            path=test_image_file,
            metadata={"test": "value"},
        )
        state.add_op("resize", "50%")
        state.add_op("pad", 10, color="red")

        json_str = state.to_json()
        restored = PipelineState.from_json(json_str)

        assert restored.path == test_image_file
        assert restored.metadata["test"] == "value"
        assert len(restored.ops) == 2
        assert restored.ops[0] == ("resize", ("50%",), {})
        assert restored.ops[1] == ("pad", (10,), {"color": "red"})

    def test_json_format_is_compact(self, test_image_file: str):
        """Test that JSON format is compact (no image data)."""
        state = PipelineState(path=test_image_file)
        state.add_op("resize", "50%")

        json_str = state.to_json()
        data = json.loads(json_str)

        # Verify version 2 format
        assert data["version"] == 2
        assert data["path"] == test_image_file
        assert "image" not in data  # No image data
        assert len(json_str) < 1000  # Should be very small

    def test_materialize_loads_and_applies(self, test_image_file: str):
        """Test that materialize loads image and applies ops."""
        state = PipelineState(path=test_image_file)
        state.add_op("resize", "50%")

        image = state.materialize()

        assert isinstance(image, Image.Image)
        assert image.size == (50, 40)  # 100x80 * 50% = 50x40

    def test_materialize_multiple_ops(self, test_image_file: str):
        """Test materializing with multiple operations."""
        state = PipelineState(path=test_image_file)
        state.add_op("resize", "50%")
        state.add_op("rotate", 90)

        image = state.materialize()

        # After resize: 50x40, after 90° rotate: 40x50
        assert image.size == (40, 50)

    def test_from_json_rejects_v1(self):
        """Test that version 1 format is rejected."""
        v1_json = '{"version": 1, "image": {}, "history": []}'
        with pytest.raises(ValueError, match="Only version 2"):
            PipelineState.from_json(v1_json)

    def test_load_image_file(self, test_image_file: str):
        """Test load_image with file path."""
        image = load_image(test_image_file)
        assert image.mode == "RGBA"
        assert image.size == (100, 80)

    def test_image_to_arrays(self, test_image: Image.Image):
        """Test image_to_arrays conversion."""
        bitmap, colors = image_to_arrays(test_image)

        assert bitmap.shape == (80, 100)
        assert colors.shape == (80, 100, 3)
        assert bitmap.dtype == np.float32
        assert colors.dtype == np.float32
        assert 0 <= bitmap.min() <= bitmap.max() <= 1
        assert 0 <= colors.min() <= colors.max() <= 1


class TestCompositionOperations:
    """Tests for image composition operations."""

    @pytest.fixture
    def small_image(self) -> Image.Image:
        """Create a small test image."""
        return Image.new("RGBA", (50, 40), color=(255, 0, 0, 255))

    @pytest.fixture
    def large_image(self) -> Image.Image:
        """Create a larger test image."""
        return Image.new("RGBA", (100, 80), color=(0, 255, 0, 255))

    def test_hstack_same_size(self, test_image: Image.Image):
        """Test horizontal stack with same-sized images."""
        result = op_hstack(test_image, test_image)
        assert result.size == (200, 80)  # 100+100, 80

    def test_hstack_different_heights(self, small_image: Image.Image, large_image: Image.Image):
        """Test horizontal stack with different heights."""
        result = op_hstack(small_image, large_image)
        # Width: 50 + 100 = 150, Height: max(40, 80) = 80
        assert result.size == (150, 80)

    def test_hstack_align_top(self, small_image: Image.Image, large_image: Image.Image):
        """Test horizontal stack with top alignment."""
        result = op_hstack(small_image, large_image, align="top")
        assert result.size == (150, 80)

    def test_hstack_align_bottom(self, small_image: Image.Image, large_image: Image.Image):
        """Test horizontal stack with bottom alignment."""
        result = op_hstack(small_image, large_image, align="bottom")
        assert result.size == (150, 80)

    def test_vstack_same_size(self, test_image: Image.Image):
        """Test vertical stack with same-sized images."""
        result = op_vstack(test_image, test_image)
        assert result.size == (100, 160)  # 100, 80+80

    def test_vstack_different_widths(self, small_image: Image.Image, large_image: Image.Image):
        """Test vertical stack with different widths."""
        result = op_vstack(small_image, large_image)
        # Width: max(50, 100) = 100, Height: 40 + 80 = 120
        assert result.size == (100, 120)

    def test_vstack_align_left(self, small_image: Image.Image, large_image: Image.Image):
        """Test vertical stack with left alignment."""
        result = op_vstack(small_image, large_image, align="left")
        assert result.size == (100, 120)

    def test_vstack_align_right(self, small_image: Image.Image, large_image: Image.Image):
        """Test vertical stack with right alignment."""
        result = op_vstack(small_image, large_image, align="right")
        assert result.size == (100, 120)

    def test_overlay_basic(self, large_image: Image.Image, small_image: Image.Image):
        """Test basic overlay."""
        result = op_overlay(large_image, small_image, x=10, y=10)
        assert result.size == large_image.size

    def test_overlay_with_opacity(self, large_image: Image.Image, small_image: Image.Image):
        """Test overlay with opacity."""
        result = op_overlay(large_image, small_image, x=10, y=10, opacity=0.5)
        assert result.size == large_image.size

    def test_overlay_paste_mode(self, large_image: Image.Image, small_image: Image.Image):
        """Test overlay with paste mode."""
        result = op_overlay(large_image, small_image, x=10, y=10, paste=True)
        assert result.size == large_image.size

    def test_tile(self, test_image: Image.Image):
        """Test tile operation."""
        result = op_tile(test_image, cols=3, rows=2)
        assert result.size == (300, 160)  # 100*3, 80*2

    def test_tile_1x1(self, test_image: Image.Image):
        """Test tile 1x1 (identity)."""
        result = op_tile(test_image, cols=1, rows=1)
        assert result.size == test_image.size

    def test_grid_same_size(self, test_image: Image.Image):
        """Test grid with same-sized images."""
        others = [test_image.copy(), test_image.copy(), test_image.copy()]
        result = op_grid(test_image, others, cols=2)
        # 4 images in 2 columns = 2 rows
        assert result.size == (200, 160)  # 100*2, 80*2

    def test_grid_uneven(self, test_image: Image.Image):
        """Test grid with odd number of images."""
        others = [test_image.copy(), test_image.copy()]
        result = op_grid(test_image, others, cols=2)
        # 3 images in 2 columns = 2 rows (last cell empty)
        assert result.size == (200, 160)

    def test_grid_resizes_images(self, large_image: Image.Image, small_image: Image.Image):
        """Test that grid resizes images to match first."""
        result = op_grid(large_image, [small_image], cols=2)
        # Cell size from large_image: 100x80
        # 2 images in 2 columns = 1 row
        assert result.size == (200, 80)


class TestCompositionViaApplyOperation:
    """Test composition operations through apply_operation."""

    @pytest.fixture
    def two_image_files(self, test_image: Image.Image) -> tuple[str, str]:
        """Create two temp image files."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f1:
            test_image.save(f1.name)
            path1 = f1.name

        small = Image.new("RGBA", (50, 40), color=(255, 0, 0, 255))
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f2:
            small.save(f2.name)
            path2 = f2.name

        yield path1, path2

        Path(path1).unlink()
        Path(path2).unlink()

    def test_apply_hstack(self, test_image: Image.Image, two_image_files: tuple[str, str]):
        """Test apply_operation for hstack."""
        _, other_path = two_image_files
        result = apply_operation(test_image, "hstack", other_path, align="center")
        # 100 + 50 = 150
        assert result.size[0] == 150

    def test_apply_vstack(self, test_image: Image.Image, two_image_files: tuple[str, str]):
        """Test apply_operation for vstack."""
        _, other_path = two_image_files
        result = apply_operation(test_image, "vstack", other_path, align="center")
        # 80 + 40 = 120
        assert result.size[1] == 120

    def test_apply_overlay(self, test_image: Image.Image, two_image_files: tuple[str, str]):
        """Test apply_operation for overlay."""
        _, other_path = two_image_files
        result = apply_operation(test_image, "overlay", other_path, 10, 10)
        assert result.size == test_image.size


class TestANSILoading:
    """Tests for ANSI file loading."""

    def test_load_ansi_file_braille(self):
        """Test loading braille ANSI art."""
        from chop.pipeline import load_ansi_file

        # Create temp file with braille art (no trailing newline)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".ans", delete=False, encoding="utf-8") as f:
            f.write("⠿⠿⠿\n⠿⠿⠿")  # 2 rows, no trailing newline
            temp_path = f.name

        try:
            image = load_ansi_file(temp_path)
            assert image.mode == "RGBA"
            # 3 braille chars x 2 rows
            # Each braille cell is 2 wide x 4 tall
            assert image.size == (6, 8)  # 3*2, 2*4
        finally:
            Path(temp_path).unlink()

    def test_load_image_detects_ans(self):
        """Test that load_image detects .ans extension."""
        from chop.pipeline import load_image

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ans", delete=False, encoding="utf-8") as f:
            f.write("⠿⠿")  # Single row, no trailing newline
            temp_path = f.name

        try:
            image = load_image(temp_path)
            assert image.mode == "RGBA"
            # 2 braille chars = 4 wide, 1 row = 4 tall
            assert image.size == (4, 4)  # 2*2, 1*4
        finally:
            Path(temp_path).unlink()

    def test_load_ansi_quadrants(self):
        """Test loading quadrant block art."""
        from chop.pipeline import load_ansi_file

        with tempfile.NamedTemporaryFile(mode="w", suffix=".ans", delete=False, encoding="utf-8") as f:
            f.write("█▀█\n▄▄▄")  # 2 rows, no trailing newline
            temp_path = f.name

        try:
            image = load_ansi_file(temp_path)
            assert image.mode == "RGBA"
            # 3 quadrant chars x 2 rows
            # Each quadrant cell is 2 wide x 2 tall
            assert image.size == (6, 4)  # 3*2, 2*2
        finally:
            Path(temp_path).unlink()


class TestAutoDetectRenderer:
    """Tests for auto_detect_renderer function."""

    def test_detects_kitty(self):
        """Test kitty detection via KITTY_WINDOW_ID."""
        with mock.patch.dict("os.environ", {"KITTY_WINDOW_ID": "1"}, clear=False):
            result = auto_detect_renderer()
            assert result == "kitty"

    def test_detects_ghostty(self):
        """Test ghostty detection (supports kitty protocol)."""
        with mock.patch.dict("os.environ", {"GHOSTTY_RESOURCES_DIR": "/tmp"}, clear=False):
            result = auto_detect_renderer()
            assert result == "kitty"

    def test_detects_sixel_mlterm(self):
        """Test sixel detection for mlterm."""
        env = {"TERM": "mlterm-256color"}
        with mock.patch.dict("os.environ", env, clear=True):
            result = auto_detect_renderer()
            assert result == "sixel"

    def test_detects_sixel_foot(self):
        """Test sixel detection for foot terminal."""
        env = {"TERM": "foot-direct"}
        with mock.patch.dict("os.environ", env, clear=True):
            result = auto_detect_renderer()
            assert result == "sixel"

    def test_fallback_to_sextants(self):
        """Test fallback to sextants for unknown terminals."""
        env = {"TERM": "xterm-256color"}
        with mock.patch.dict("os.environ", env, clear=True):
            result = auto_detect_renderer()
            assert result == "sextants"

    def test_result_is_valid_renderer(self):
        """Test that auto-detected renderer is valid."""
        result = auto_detect_renderer()
        assert result in RENDERERS


class TestOutputHandling:
    """Tests for centralized output handling with lazy pipeline."""

    @pytest.fixture
    def state(self, test_image_file: str) -> PipelineState:
        """Create a pipeline state for testing."""
        return PipelineState(path=test_image_file)

    def test_json_flag_forces_json(self, state: PipelineState):
        """Test -j flag forces JSON output even on TTY."""
        args = mock.Mock(json=True, output=None, renderer=None)

        with mock.patch("chop.pipeline.write_pipeline_output") as mock_write:
            with mock.patch("sys.stdout.isatty", return_value=True):
                handle_output(state, args)
                mock_write.assert_called_once_with(state)

    def test_output_flag_saves_file(self, state: PipelineState):
        """Test -o flag materializes and saves to file."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            args = mock.Mock(json=False, output=f.name, renderer=None)

            handle_output(state, args)

            # Verify file was created
            assert Path(f.name).exists()
            Path(f.name).unlink()

    def test_renderer_flag_materializes_and_renders(self, state: PipelineState):
        """Test -r flag materializes and uses specified renderer."""
        args = mock.Mock(json=False, output=None, renderer="braille", width=None, height=None)

        with mock.patch("chop.render.render_to_terminal") as mock_render:
            handle_output(state, args)
            mock_render.assert_called_once()
            # Verify first arg is an Image (materialized)
            call_args = mock_render.call_args
            assert isinstance(call_args[0][0], Image.Image)
            assert call_args[1]["renderer_name"] == "braille"

    def test_tty_auto_renders(self, state: PipelineState):
        """Test TTY output auto-renders."""
        args = mock.Mock(json=False, output=None, renderer=None, width=None, height=None)

        with mock.patch("sys.stdout.isatty", return_value=True):
            with mock.patch("chop.render.render_to_terminal") as mock_render:
                with mock.patch("chop.render.auto_detect_renderer", return_value="sextants"):
                    handle_output(state, args)
                    mock_render.assert_called_once()

    def test_piped_outputs_json(self, state: PipelineState):
        """Test piped output writes JSON (no materialization)."""
        args = mock.Mock(json=False, output=None, renderer=None)

        with mock.patch("sys.stdout.isatty", return_value=False):
            with mock.patch("chop.pipeline.write_pipeline_output") as mock_write:
                handle_output(state, args)
                mock_write.assert_called_once_with(state)


class TestRenderAndSaveCommands:
    """Tests for render and save command groups."""

    def test_render_command_handler(self, test_image_file: str):
        """Test cmd_render function materializes and renders."""
        from chop.cli import cmd_render

        state = PipelineState(path=test_image_file)
        args = mock.Mock(renderer_name="braille", width=None, height=None)

        with mock.patch("chop.cli.read_pipeline_input", return_value=state):
            with mock.patch("chop.cli.render_to_terminal") as mock_render:
                cmd_render(args)
                mock_render.assert_called_once()
                # Verify first arg is an Image (materialized)
                call_args = mock_render.call_args
                assert isinstance(call_args[0][0], Image.Image)

    def test_render_command_auto_detect(self, test_image_file: str):
        """Test cmd_render with auto-detection."""
        from chop.cli import cmd_render

        state = PipelineState(path=test_image_file)
        args = mock.Mock(renderer_name=None, width=None, height=None)

        with mock.patch("chop.cli.read_pipeline_input", return_value=state):
            with mock.patch("chop.cli.auto_detect_renderer", return_value="sextants"):
                with mock.patch("chop.cli.render_to_terminal") as mock_render:
                    cmd_render(args)
                    mock_render.assert_called_once()

    def test_render_requires_piped_input(self):
        """Test render command requires piped input."""
        from chop.cli import cmd_render

        args = mock.Mock(renderer_name="braille", width=None, height=None)

        with mock.patch("chop.cli.read_pipeline_input", return_value=None):
            with pytest.raises(ValueError, match="render requires piped input"):
                cmd_render(args)

    def test_save_command_handler(self, test_image_file: str):
        """Test cmd_save function materializes and saves."""
        from chop.cli import cmd_save

        state = PipelineState(path=test_image_file)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            args = mock.Mock(path=f.name)

            with mock.patch("chop.cli.read_pipeline_input", return_value=state):
                cmd_save(args)

            # Verify file was saved
            assert Path(f.name).exists()
            saved = Image.open(f.name)
            assert saved.size == (100, 80)  # Original test image size
            Path(f.name).unlink()

    def test_save_requires_piped_input(self):
        """Test save command requires piped input."""
        from chop.cli import cmd_save

        args = mock.Mock(path="out.png")

        with mock.patch("chop.cli.read_pipeline_input", return_value=None):
            with pytest.raises(ValueError, match="save requires piped input"):
                cmd_save(args)


class TestLazyPipelineIntegration:
    """Integration tests for lazy pipeline behavior."""

    def test_pipeline_json_is_human_readable(self, test_image_file: str):
        """Test that pipeline JSON is small and readable."""
        state = PipelineState(path=test_image_file)
        state.add_op("resize", "50%")
        state.add_op("pad", 10)
        state.add_op("border", 5, color="red")

        json_str = state.to_json()
        data = json.loads(json_str)

        # Should be version 2
        assert data["version"] == 2
        # Path should be present
        assert data["path"] == test_image_file
        # Ops should be a list
        assert len(data["ops"]) == 3
        # JSON should be small (no base64 image data)
        assert len(json_str) < 500

    def test_ops_are_recorded_not_applied(self, test_image_file: str):
        """Test that adding ops doesn't load/process the image."""
        state = PipelineState(path=test_image_file)

        # Add many operations - should be instant (no image processing)
        for _ in range(100):
            state.add_op("resize", "99%")
            state.add_op("pad", 1)

        # State should have 200 ops
        assert len(state.ops) == 200

        # But no image has been loaded or processed yet
        # (can't directly test this, but the fact that it's instant is evidence)

    def test_materialize_chains_operations(self, test_image_file: str):
        """Test that materialize correctly chains operations."""
        state = PipelineState(path=test_image_file)
        state.add_op("resize", "50%")  # 100x80 -> 50x40
        state.add_op("rotate", 90)  # 50x40 -> 40x50

        image = state.materialize()

        assert image.size == (40, 50)


class TestDSLParseValue:
    """Tests for DSL parse_value function."""

    def test_parse_boolean_true(self):
        assert parse_value("true") is True
        assert parse_value("True") is True
        assert parse_value("TRUE") is True

    def test_parse_boolean_false(self):
        assert parse_value("false") is False
        assert parse_value("False") is False
        assert parse_value("FALSE") is False

    def test_parse_integer(self):
        assert parse_value("42") == 42
        assert parse_value("-10") == -10
        assert parse_value("0") == 0

    def test_parse_float(self):
        assert parse_value("3.14") == 3.14
        assert parse_value("-0.5") == -0.5
        assert parse_value("2.0") == 2.0

    def test_parse_string(self):
        assert parse_value("50%") == "50%"
        assert parse_value("photo.jpg") == "photo.jpg"
        assert parse_value("center") == "center"


class TestDSLParseOperation:
    """Tests for DSL parse_operation function."""

    def test_simple_operation(self):
        assert parse_operation("rotate 90") == ("rotate", (90,), {})

    def test_operation_with_arg(self):
        assert parse_operation("resize 50%") == ("resize", ("50%",), {})

    def test_operation_with_multiple_args(self):
        assert parse_operation("crop 10 20 50 40") == ("crop", (10, 20, 50, 40), {})

    def test_operation_with_kwarg(self):
        assert parse_operation("pad 10 color=red") == ("pad", (10,), {"color": "red"})

    def test_operation_with_args_and_kwargs(self):
        result = parse_operation("overlay img.png 10 20 opacity=0.5")
        assert result == ("overlay", ("img.png", 10, 20), {"opacity": 0.5})

    def test_operation_with_boolean_kwarg(self):
        result = parse_operation("overlay img.png 0 0 paste=true")
        assert result == ("overlay", ("img.png", 0, 0), {"paste": True})

    def test_operation_with_quoted_path(self):
        result = parse_operation('hstack "path with spaces.png"')
        assert result == ("hstack", ("path with spaces.png",), {})


class TestDSLParseProgram:
    """Tests for DSL parse_program function."""

    def test_single_operation(self):
        ops = parse_program("resize 50%")
        assert ops == [("resize", ("50%",), {})]

    def test_semicolon_separated(self):
        ops = parse_program("resize 50%; pad 10; rotate 90")
        assert ops == [
            ("resize", ("50%",), {}),
            ("pad", (10,), {}),
            ("rotate", (90,), {}),
        ]

    def test_newline_separated(self):
        ops = parse_program("resize 50%\npad 10\nrotate 90")
        assert ops == [
            ("resize", ("50%",), {}),
            ("pad", (10,), {}),
            ("rotate", (90,), {}),
        ]

    def test_mixed_separators(self):
        ops = parse_program("resize 50%; pad 10\nrotate 90")
        assert ops == [
            ("resize", ("50%",), {}),
            ("pad", (10,), {}),
            ("rotate", (90,), {}),
        ]

    def test_comments_ignored(self):
        ops = parse_program("# This is a comment\nresize 50%")
        assert ops == [("resize", ("50%",), {})]

    def test_inline_comments(self):
        ops = parse_program("resize 50%  # shrink it")
        assert ops == [("resize", ("50%",), {})]

    def test_empty_lines_ignored(self):
        ops = parse_program("\n\nresize 50%\n\n")
        assert ops == [("resize", ("50%",), {})]

    def test_empty_program(self):
        ops = parse_program("")
        assert ops == []

    def test_comment_only(self):
        ops = parse_program("# just a comment")
        assert ops == []

    def test_complex_program(self):
        program = """
        # Shrink and add border
        resize 50%
        fit 800x600
        pad 10 color=white
        border 5 color=black
        """
        ops = parse_program(program)
        assert len(ops) == 4
        assert ops[0] == ("resize", ("50%",), {})
        assert ops[1] == ("fit", ("800x600",), {})
        assert ops[2] == ("pad", (10,), {"color": "white"})
        assert ops[3] == ("border", (5,), {"color": "black"})


class TestDSLLoadProgram:
    """Tests for DSL load_program function."""

    def test_inline_program(self):
        """Test that non-existent path is treated as inline."""
        result = load_program("resize 50%; pad 10")
        assert result == "resize 50%; pad 10"

    def test_load_from_file(self):
        """Test loading program from file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".chp", delete=False) as f:
            f.write("resize 50%\npad 10\n")
            temp_path = f.name

        try:
            result = load_program(temp_path)
            assert "resize 50%" in result
            assert "pad 10" in result
        finally:
            Path(temp_path).unlink()

    def test_file_takes_precedence(self):
        """Test that existing file is read, not treated as inline."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".chp", delete=False) as f:
            f.write("rotate 90")
            temp_path = f.name

        try:
            result = load_program(temp_path)
            assert result == "rotate 90"
        finally:
            Path(temp_path).unlink()


class TestApplyCommand:
    """Tests for the apply command."""

    def test_apply_inline_program(self, test_image_file: str):
        """Test apply with inline program string."""
        from chop.cli import cmd_apply

        state = PipelineState(path=test_image_file)
        args = mock.Mock(program="resize 50%; pad 10")

        with mock.patch("chop.cli.read_pipeline_input", return_value=state):
            result = cmd_apply(args)

        assert len(result.ops) == 2
        assert result.ops[0] == ("resize", ("50%",), {})
        assert result.ops[1] == ("pad", (10,), {})

    def test_apply_from_file(self, test_image_file: str):
        """Test apply with program file."""
        from chop.cli import cmd_apply

        # Create program file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".chp", delete=False) as f:
            f.write("resize 50%\nborder 5 color=red\n")
            prog_path = f.name

        state = PipelineState(path=test_image_file)
        args = mock.Mock(program=prog_path)

        try:
            with mock.patch("chop.cli.read_pipeline_input", return_value=state):
                result = cmd_apply(args)

            assert len(result.ops) == 2
            assert result.ops[0] == ("resize", ("50%",), {})
            assert result.ops[1] == ("border", (5,), {"color": "red"})
        finally:
            Path(prog_path).unlink()

    def test_apply_requires_piped_input(self):
        """Test apply command requires piped input."""
        from chop.cli import cmd_apply

        args = mock.Mock(program="resize 50%")

        with mock.patch("chop.cli.read_pipeline_input", return_value=None):
            with pytest.raises(ValueError, match="apply requires piped input"):
                cmd_apply(args)

    def test_apply_appends_to_existing_ops(self, test_image_file: str):
        """Test that apply appends ops to existing pipeline ops."""
        from chop.cli import cmd_apply

        state = PipelineState(path=test_image_file)
        state.add_op("rotate", 90)  # Pre-existing op

        args = mock.Mock(program="resize 50%")

        with mock.patch("chop.cli.read_pipeline_input", return_value=state):
            result = cmd_apply(args)

        assert len(result.ops) == 2
        assert result.ops[0] == ("rotate", (90,), {})
        assert result.ops[1] == ("resize", ("50%",), {})

    def test_apply_integration_materialize(self, test_image_file: str):
        """Test that applied ops actually work when materialized."""
        state = PipelineState(path=test_image_file)

        # Apply resize program
        from chop.dsl import parse_program

        ops = parse_program("resize 50%")
        for name, op_args, kwargs in ops:
            state.add_op(name, *op_args, **kwargs)

        # Materialize and check
        image = state.materialize()
        assert image.size == (50, 40)  # 100x80 * 50%

    def test_apply_complex_program_materialize(self, test_image_file: str):
        """Test complex program materializes correctly."""
        state = PipelineState(path=test_image_file)

        from chop.dsl import parse_program

        ops = parse_program("resize 50%; rotate 90")
        for name, op_args, kwargs in ops:
            state.add_op(name, *op_args, **kwargs)

        image = state.materialize()
        # resize 50%: 100x80 -> 50x40
        # rotate 90: 50x40 -> 40x50
        assert image.size == (40, 50)

    def test_apply_empty_program(self, test_image_file: str):
        """Test applying empty program doesn't change state."""
        from chop.cli import cmd_apply

        state = PipelineState(path=test_image_file)
        args = mock.Mock(program="")

        with mock.patch("chop.cli.read_pipeline_input", return_value=state):
            result = cmd_apply(args)

        assert len(result.ops) == 0

    def test_apply_comment_only_program(self, test_image_file: str):
        """Test applying comments-only program doesn't change state."""
        from chop.cli import cmd_apply

        state = PipelineState(path=test_image_file)
        args = mock.Mock(program="# just a comment\n# another comment")

        with mock.patch("chop.cli.read_pipeline_input", return_value=state):
            result = cmd_apply(args)

        assert len(result.ops) == 0
