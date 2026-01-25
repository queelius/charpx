"""Tests for imgcat extra."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Skip all tests if extras not importable
pytest.importorskip("PIL")
imgcat_mod = pytest.importorskip("imgcat")


class TestImgcatOptions:
    """Tests for ImgcatOptions dataclass."""

    def test_default_options(self):
        from imgcat import ImgcatOptions

        opts = ImgcatOptions()
        assert opts.renderer == "auto"
        assert opts.width is None
        assert opts.height is None
        assert opts.dither is False
        assert opts.contrast is False
        assert opts.invert is False
        assert opts.grayscale is False
        assert opts.no_color is False


class TestGetRenderer:
    """Tests for get_renderer function."""

    def test_auto_renderer(self):
        from imgcat.imgcat import get_renderer, ImgcatOptions

        opts = ImgcatOptions()
        renderer = get_renderer("auto", opts)
        assert hasattr(renderer, "render")

    def test_braille_renderer(self):
        from imgcat.imgcat import get_renderer, ImgcatOptions

        opts = ImgcatOptions()
        renderer = get_renderer("braille", opts)
        assert hasattr(renderer, "render")
        assert renderer.cell_width == 2
        assert renderer.cell_height == 4

    def test_quadrants_renderer(self):
        from imgcat.imgcat import get_renderer, ImgcatOptions

        opts = ImgcatOptions()
        renderer = get_renderer("quadrants", opts)
        assert hasattr(renderer, "render")
        assert renderer.cell_width == 2
        assert renderer.cell_height == 2

    def test_unknown_renderer_raises(self):
        from imgcat.imgcat import get_renderer, ImgcatOptions

        opts = ImgcatOptions()
        with pytest.raises(ValueError, match="Unknown renderer"):
            get_renderer("unknown", opts)


class TestSkillInstall:
    """Tests for skill installation."""

    def test_skill_install_local(self):
        from imgcat.imgcat import skill_install

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("imgcat.imgcat.Path.cwd", return_value=Path(tmpdir)):
                result = skill_install(local=True)
                assert result is True
                skill_file = Path(tmpdir) / ".claude" / "skills" / "imgcat.md"
                assert skill_file.exists()

    def test_skill_install_requires_flag(self, capsys):
        from imgcat.imgcat import skill_install

        result = skill_install()
        assert result is False
        captured = capsys.readouterr()
        assert "Specify --local or --global" in captured.err


class TestImgcatFunction:
    """Tests for imgcat function."""

    def test_imgcat_with_test_image(self):
        """Test imgcat with a simple generated image."""
        from imgcat import imgcat
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple test image
            img = Image.new("RGB", (10, 10), color="red")
            img_path = Path(tmpdir) / "test.png"
            img.save(img_path)

            # Render to string buffer
            output = StringIO()
            imgcat(img_path, renderer="braille", width=20, dest=output)

            result = output.getvalue()
            assert len(result) > 0  # Should have some output
