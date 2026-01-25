"""Tests for the image CLI and example scripts."""

import pytest

pytest.importorskip("PIL", reason="PIL required for CLI tests")


class TestImageCLI:
    """Tests for the pixdot.image_cli module."""

    def test_main_no_args_shows_help(self, capsys):
        """Running with no args should show help."""
        from pixdot.image_cli import main

        # No args should show help and return 0
        result = main([])
        assert result == 0
        captured = capsys.readouterr()
        assert "pixdot" in captured.out
        assert "Usage" in captured.out

    def test_render_missing_file(self, capsys):
        """Render with missing file should return error."""
        from pixdot.image_cli import main

        result = main(["nonexistent.jpg"])
        assert result == 1

        captured = capsys.readouterr()
        assert "Error" in captured.err or "not found" in captured.err.lower()

    def test_render_with_image(self, tmp_path, capsys):
        """Render should work with valid image."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a test image
        img = Image.new('L', (100, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20"])
        assert result == 0

        captured = capsys.readouterr()
        # Should have braille output
        assert len(captured.out) > 0

    def test_render_with_invert(self, tmp_path, capsys):
        """Render with --invert flag."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a black image
        img = Image.new('L', (100, 100), color=0)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        # Without invert - should be mostly blank braille
        result1 = main([str(img_path), "-w", "20"])
        assert result1 == 0
        out1 = capsys.readouterr().out

        # With invert - should be mostly full braille
        result2 = main([str(img_path), "-w", "20", "--invert"])
        assert result2 == 0
        out2 = capsys.readouterr().out

        # Outputs should be different
        assert out1 != out2

    def test_render_with_threshold_none(self, tmp_path, capsys):
        """Render with auto-detect threshold (default)."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a test image
        img = Image.new('L', (100, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20"])
        assert result == 0

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_render_with_dither(self, tmp_path, capsys):
        """Render with --dither flag."""
        from PIL import Image
        import numpy as np

        from pixdot.image_cli import main

        # Create a gradient image
        arr = np.linspace(0, 255, 100 * 100).reshape(100, 100).astype('uint8')
        img = Image.fromarray(arr, mode='L')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--dither"])
        assert result == 0

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_render_with_contrast(self, tmp_path, capsys):
        """Render with --contrast flag."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a low-contrast image
        img = Image.new('L', (100, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--contrast"])
        assert result == 0

        captured = capsys.readouterr()
        assert len(captured.out) > 0

    def test_render_to_file(self, tmp_path, capsys):
        """Render to output file."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a test image
        img = Image.new('L', (100, 100), color=128)
        img_path = tmp_path / "test.png"
        out_path = tmp_path / "output.txt"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "-o", str(out_path)])
        assert result == 0

        assert out_path.exists()
        content = out_path.read_text()
        assert len(content) > 0

    def test_load_image(self, tmp_path):
        """Test image loading helper."""
        from PIL import Image

        from pixdot.image_cli import load_image

        # Create a test image
        img = Image.new('L', (200, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        bitmap = load_image(str(img_path), width=40)

        # Should be normalized 0-1
        assert bitmap.min() >= 0.0
        assert bitmap.max() <= 1.0
        # Width should be 40 * 2 = 80 pixels
        assert bitmap.shape[1] == 80

    def test_load_image_with_color(self, tmp_path):
        """Test color image loading helper."""
        from PIL import Image

        from pixdot.image_cli import load_image_with_color

        # Create a test RGB image
        img = Image.new('RGB', (200, 100), color=(255, 128, 64))
        img_path = tmp_path / "test.png"
        img.save(img_path)

        grayscale, colors = load_image_with_color(str(img_path), width=40)

        # Grayscale should be 2D, normalized 0-1
        assert grayscale.ndim == 2
        assert grayscale.min() >= 0.0
        assert grayscale.max() <= 1.0
        assert grayscale.shape[1] == 80

        # Colors should be 3D with 3 channels
        assert colors.ndim == 3
        assert colors.shape[2] == 3
        assert colors.min() >= 0.0
        assert colors.max() <= 1.0
        assert colors.shape[:2] == grayscale.shape

    def test_render_with_grayscale_color(self, tmp_path, capsys):
        """Render with --color grayscale produces ANSI codes."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a test image with varied brightness
        import numpy as np
        arr = np.linspace(0, 255, 100 * 100).reshape(100, 100).astype('uint8')
        img = Image.fromarray(arr, mode='L')
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--color", "grayscale"])
        assert result == 0

        captured = capsys.readouterr()
        # Should have ANSI escape codes for grayscale (256-color codes 232-255)
        assert "\033[38;5;" in captured.out
        # Should have reset code
        assert "\033[0m" in captured.out

    def test_render_with_truecolor(self, tmp_path, capsys):
        """Render with --color truecolor produces ANSI codes."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a colorful test image
        img = Image.new('RGB', (100, 100), color=(255, 128, 64))
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--color", "truecolor"])
        assert result == 0

        captured = capsys.readouterr()
        # Should have ANSI truecolor escape codes
        assert "\033[38;2;" in captured.out
        # Should have reset code
        assert "\033[0m" in captured.out

    def test_render_with_color_none(self, tmp_path, capsys):
        """Render with --color none produces plain braille."""
        from PIL import Image

        from pixdot.image_cli import main

        img = Image.new('L', (100, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--color", "none"])
        assert result == 0

        captured = capsys.readouterr()
        # Should NOT have ANSI escape codes
        assert "\033[" not in captured.out
        # Should have braille characters
        assert len(captured.out) > 0

    def test_render_color_with_invert(self, tmp_path, capsys):
        """Render with --color truecolor --invert inverts both dots and colors."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a test image
        img = Image.new('RGB', (100, 100), color=(255, 0, 0))  # Pure red
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--color", "truecolor", "--invert"])
        assert result == 0

        captured = capsys.readouterr()
        # Should have ANSI truecolor codes
        assert "\033[38;2;" in captured.out
        # The inverted red (255, 0, 0) should be cyan (0, 255, 255)
        # Check that we have some color codes in the output
        assert len(captured.out) > 0

    def test_render_color_with_invert_colors_only(self, tmp_path, capsys):
        """Render with --invert-colors inverts colors only, not dots."""
        from PIL import Image

        from pixdot.image_cli import main

        img = Image.new('RGB', (100, 100), color=(255, 0, 0))
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--color", "truecolor", "--invert-colors"])
        assert result == 0

        captured = capsys.readouterr()
        assert "\033[38;2;" in captured.out

    def test_render_color_with_contrast(self, tmp_path, capsys):
        """Render with --color and --contrast flags."""
        from PIL import Image

        from pixdot.image_cli import main

        # Create a low-contrast image
        img = Image.new('RGB', (100, 100), color=(128, 128, 128))
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "20", "--color", "truecolor", "--contrast"])
        assert result == 0

        captured = capsys.readouterr()
        assert "\033[38;2;" in captured.out


class TestImageCLIMissingPIL:
    """Tests for graceful PIL import handling."""

    def test_check_pil_raises_when_missing(self, monkeypatch):
        """Test _check_pil exits gracefully when PIL unavailable."""
        import pixdot.image_cli as cli_module

        # Simulate PIL being unavailable
        monkeypatch.setattr(cli_module, 'PIL_AVAILABLE', False)

        with pytest.raises(SystemExit) as exc_info:
            cli_module._check_pil()
        assert exc_info.value.code == 1


class TestFramebufferDemo:
    """Tests for the framebuffer demo example."""

    def test_draw_functions_exist(self):
        """Verify drawing functions can be imported."""
        import sys
        from pathlib import Path

        # Add examples to path
        examples_path = Path(__file__).parent.parent / "examples"
        sys.path.insert(0, str(examples_path))

        from framebuffer_demo import draw_circle, draw_line, draw_rect
        import numpy as np

        # Test basic functionality
        fb = np.zeros((40, 80), dtype=np.float32)

        draw_circle(fb, 40, 20, 10, filled=True)
        assert fb.sum() > 0  # Something was drawn

        fb2 = np.zeros((40, 80), dtype=np.float32)
        draw_line(fb2, 0, 0, 79, 39)
        assert fb2.sum() > 0

        fb3 = np.zeros((40, 80), dtype=np.float32)
        draw_rect(fb3, 10, 10, 20, 10, filled=True)
        assert fb3.sum() > 0

    def test_main_runs(self, capsys):
        """Test that main() executes without error."""
        import sys
        from pathlib import Path

        examples_path = Path(__file__).parent.parent / "examples"
        sys.path.insert(0, str(examples_path))

        from framebuffer_demo import main

        main()
        captured = capsys.readouterr()
        assert "Framebuffer Demo" in captured.out
        assert len(captured.out) > 100  # Should have substantial output


class TestCellAspect:
    """Tests for the --cell-aspect flag."""

    def test_cell_aspect_default(self, tmp_path):
        """Default cell-aspect should be 0.5."""
        from PIL import Image

        from pixdot.image_cli import load_image

        img = Image.new('L', (200, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        # Default cell_aspect=0.5
        bitmap = load_image(str(img_path), width=40)
        default_height = bitmap.shape[0]

        # With cell_aspect=0.5, image should have specific dimensions
        assert bitmap.shape[1] == 80  # width * 2
        assert default_height > 0

    def test_cell_aspect_custom(self, tmp_path):
        """Custom cell-aspect should affect image dimensions."""
        from PIL import Image

        from pixdot.image_cli import load_image

        img = Image.new('L', (200, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        # Different cell_aspect values should produce different heights
        bitmap_05 = load_image(str(img_path), width=40, cell_aspect=0.5)
        bitmap_06 = load_image(str(img_path), width=40, cell_aspect=0.6)

        # Higher cell_aspect produces taller bitmap (compensates for wider cells)
        assert bitmap_06.shape[0] > bitmap_05.shape[0]

    def test_cell_aspect_cli_flag(self, tmp_path, capsys):
        """CLI should accept --cell-aspect flag."""
        from PIL import Image

        from pixdot.image_cli import main

        img = Image.new('L', (200, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main([str(img_path), "-w", "40", "--cell-aspect", "0.45"])
        assert result == 0

        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestClaudeCLI:
    """Tests for the claude subcommand."""

    def test_skill_content_python_syntax(self):
        """Verify all Python code blocks in SKILL_CONTENT are valid syntax."""
        import ast
        import re
        from pixdot.claude_cli import SKILL_CONTENT

        # Extract all Python code blocks from the markdown
        pattern = r'```python\n(.*?)```'
        code_blocks = re.findall(pattern, SKILL_CONTENT, re.DOTALL)

        assert len(code_blocks) > 0, "Expected at least one Python code block"

        for i, code in enumerate(code_blocks):
            try:
                ast.parse(code)
            except SyntaxError as e:
                pytest.fail(
                    f"Invalid Python syntax in code block {i + 1}:\n"
                    f"{code[:200]}...\n"
                    f"Error: {e}"
                )

    def test_skill_content_no_eval(self):
        """Verify SKILL_CONTENT does not use unsafe eval() pattern."""
        from pixdot.claude_cli import SKILL_CONTENT

        # Check that there's no eval() call on user-provided strings
        # The safe pattern uses lambdas or function references
        assert "y = eval(expr)" not in SKILL_CONTENT
        assert "eval(expr)" not in SKILL_CONTENT

    def test_claude_show_skill(self, capsys):
        """pixdot claude show-skill should print skill content."""
        from pixdot.claude_cli import show_skill, SKILL_CONTENT

        result = show_skill()
        assert result == 0

        captured = capsys.readouterr()
        assert "pixdot" in captured.out
        assert "figure_to_braille" in captured.out

    def test_claude_install_skill(self, tmp_path):
        """pixdot claude install-skill should create skill file."""
        from pixdot.claude_cli import install_skill, SKILL_CONTENT

        skill_dir = tmp_path / "skills" / "pixdot"
        skill_file = skill_dir / "SKILL.md"

        result = install_skill(path=str(skill_dir))
        assert result == 0

        assert skill_file.exists()
        content = skill_file.read_text()
        assert "pixdot" in content
        assert "figure_to_braille" in content

    def test_claude_install_skill_no_overwrite(self, tmp_path, capsys):
        """Should not overwrite existing skill without --force."""
        from pixdot.claude_cli import install_skill

        skill_dir = tmp_path / "skills" / "pixdot"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("existing content")

        result = install_skill(path=str(skill_dir))
        assert result == 1  # Should fail

        captured = capsys.readouterr()
        assert "already installed" in captured.err

        # Content should be unchanged
        assert skill_file.read_text() == "existing content"

    def test_claude_install_skill_force(self, tmp_path):
        """--force should overwrite existing skill."""
        from pixdot.claude_cli import install_skill

        skill_dir = tmp_path / "skills" / "pixdot"
        skill_dir.mkdir(parents=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text("existing content")

        result = install_skill(force=True, path=str(skill_dir))
        assert result == 0

        # Content should be new
        content = skill_file.read_text()
        assert "existing content" not in content
        assert "pixdot" in content

    def test_claude_uninstall_skill(self, tmp_path):
        """pixdot claude uninstall-skill should remove skill file."""
        from pixdot.claude_cli import install_skill, uninstall_skill

        skill_dir = tmp_path / "skills" / "pixdot"
        skill_file = skill_dir / "SKILL.md"

        # First install
        install_skill(path=str(skill_dir))
        assert skill_file.exists()

        # Then uninstall
        result = uninstall_skill(path=str(skill_dir))
        assert result == 0
        assert not skill_file.exists()

    def test_claude_main_dispatch(self, capsys):
        """Main should dispatch to claude subcommand."""
        from pixdot.image_cli import main

        # Should dispatch to claude show-skill
        result = main(["claude", "show-skill"])
        assert result == 0

        captured = capsys.readouterr()
        assert "pixdot" in captured.out

    def test_image_subcommand_explicit(self, tmp_path, capsys):
        """pixdot image <path> should work as explicit subcommand."""
        from PIL import Image

        from pixdot.image_cli import main

        img = Image.new('L', (100, 100), color=128)
        img_path = tmp_path / "test.png"
        img.save(img_path)

        result = main(["image", str(img_path), "-w", "20"])
        assert result == 0

        captured = capsys.readouterr()
        assert len(captured.out) > 0


class TestNewExamples:
    """Tests for the new example scripts."""

    @pytest.mark.skipif(
        not pytest.importorskip("matplotlib", reason="matplotlib required"),
        reason="matplotlib required"
    )
    def test_graphing_calculator_functions(self):
        """Test graphing_calculator functions can be imported."""
        import sys
        from pathlib import Path

        examples_path = Path(__file__).parent.parent / "examples"
        sys.path.insert(0, str(examples_path))

        from graphing_calculator import plot_function, plot_multiple

        # Just verify import works - actual plotting requires matplotlib
        assert callable(plot_function)
        assert callable(plot_multiple)

    @pytest.mark.skipif(
        not pytest.importorskip("matplotlib", reason="matplotlib required"),
        reason="matplotlib required"
    )
    def test_stats_dashboard_functions(self):
        """Test stats_dashboard functions can be imported."""
        import sys
        from pathlib import Path

        examples_path = Path(__file__).parent.parent / "examples"
        sys.path.insert(0, str(examples_path))

        from stats_dashboard import histogram, scatter_with_fit, boxplot_compare

        assert callable(histogram)
        assert callable(scatter_with_fit)
        assert callable(boxplot_compare)

    @pytest.mark.skipif(
        not pytest.importorskip("matplotlib", reason="matplotlib required"),
        reason="matplotlib required"
    )
    def test_ai_recipes_list(self, capsys):
        """Test ai_recipes --list works."""
        import sys
        from pathlib import Path

        examples_path = Path(__file__).parent.parent / "examples"
        sys.path.insert(0, str(examples_path))

        from ai_recipes import main

        result = main(["--list"])
        assert result == 0

        captured = capsys.readouterr()
        assert "Function Plot" in captured.out

    @pytest.mark.skipif(
        not pytest.importorskip("matplotlib", reason="matplotlib required"),
        reason="matplotlib required"
    )
    def test_realtime_monitor_functions(self):
        """Test realtime_monitor functions can be imported."""
        import sys
        from pathlib import Path

        examples_path = Path(__file__).parent.parent / "examples"
        sys.path.insert(0, str(examples_path))

        from realtime_monitor import sparkline, live_chart, multi_metric_dashboard

        assert callable(sparkline)
        assert callable(live_chart)
        assert callable(multi_metric_dashboard)
