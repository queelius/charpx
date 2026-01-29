"""Tests for mdcat extra."""

import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

# Skip all tests if rich not available
pytest.importorskip("rich")
pytest.importorskip("PIL")
mdcat_mod = pytest.importorskip("dapple.extras.mdcat")


class TestMdcatOptions:
    """Tests for MdcatOptions dataclass."""

    def test_default_options(self):
        from dapple.extras.mdcat import MdcatOptions

        opts = MdcatOptions()
        assert opts.renderer == "auto"
        assert opts.width is None
        assert opts.image_width is None
        assert opts.render_images is True
        assert opts.theme == "default"
        assert opts.code_theme == "monokai"
        assert opts.hyperlinks is True


class TestImageCache:
    """Tests for ImageCache class."""

    def test_cache_file(self):
        from dapple.extras.mdcat.mdcat import ImageCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ImageCache(cache_dir=Path(tmpdir))
            url = "https://example.com/image.png"
            data = b"fake image data"

            cached_path = cache.cache_file(url, data)
            assert cached_path.exists()
            assert cached_path.read_bytes() == data

    def test_get_cached_path_exists(self):
        from dapple.extras.mdcat.mdcat import ImageCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ImageCache(cache_dir=Path(tmpdir))
            url = "https://example.com/image.png"
            data = b"fake image data"

            cache.cache_file(url, data)
            cached = cache.get_cached_path(url)
            assert cached is not None
            assert cached.exists()

    def test_get_cached_path_not_exists(self):
        from dapple.extras.mdcat.mdcat import ImageCache

        with tempfile.TemporaryDirectory() as tmpdir:
            cache = ImageCache(cache_dir=Path(tmpdir))
            url = "https://example.com/nonexistent.png"
            cached = cache.get_cached_path(url)
            assert cached is None


class TestImageResolver:
    """Tests for ImageResolver class."""

    def test_resolve_local_absolute(self):
        from dapple.extras.mdcat.mdcat import ImageResolver

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.png"
            test_file.write_bytes(b"test")

            resolver = ImageResolver()
            result = resolver.resolve(str(test_file))
            assert result == test_file

    def test_resolve_local_relative(self):
        from dapple.extras.mdcat.mdcat import ImageResolver

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            base_file = Path(tmpdir) / "README.md"
            base_file.write_text("# Test")
            img_file = Path(tmpdir) / "image.png"
            img_file.write_bytes(b"test")

            resolver = ImageResolver(base_path=base_file)
            result = resolver.resolve("image.png")
            assert result == img_file

    def test_resolve_nonexistent(self):
        from dapple.extras.mdcat.mdcat import ImageResolver

        resolver = ImageResolver()
        result = resolver.resolve("/nonexistent/path/to/image.png")
        assert result is None


class TestSkillInstall:
    """Tests for skill installation."""

    def test_skill_install_local(self):
        from dapple.extras.mdcat.mdcat import skill_install

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("dapple.extras.mdcat.mdcat.Path.cwd", return_value=Path(tmpdir)):
                result = skill_install(local=True)
                assert result is True
                skill_file = Path(tmpdir) / ".claude" / "skills" / "mdcat.md"
                assert skill_file.exists()

    def test_skill_install_requires_flag(self, capsys):
        from dapple.extras.mdcat.mdcat import skill_install

        result = skill_install()
        assert result is False
        captured = capsys.readouterr()
        assert "Specify --local or --global" in captured.err


class TestMdcatFunction:
    """Tests for mdcat function."""

    def test_mdcat_simple_markdown(self):
        """Test mdcat with simple markdown content."""
        from dapple.extras.mdcat import mdcat

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a simple markdown file
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("# Hello World\n\nThis is a test.")

            # Render to string buffer
            output = StringIO()
            mdcat(md_path, render_images=False, dest=output)

            result = output.getvalue()
            assert "Hello World" in result

    def test_mdcat_with_code_block(self):
        """Test mdcat with code block."""
        from dapple.extras.mdcat import mdcat

        with tempfile.TemporaryDirectory() as tmpdir:
            md_path = Path(tmpdir) / "test.md"
            md_path.write_text("```python\nprint('hello')\n```")

            output = StringIO()
            mdcat(md_path, render_images=False, dest=output)

            result = output.getvalue()
            assert "print" in result


class TestGetRenderer:
    """Tests for get_renderer function."""

    def test_auto_renderer(self):
        from dapple.extras.mdcat.mdcat import get_renderer, MdcatOptions

        opts = MdcatOptions()
        renderer = get_renderer("auto", opts)
        assert hasattr(renderer, "render")

    def test_braille_renderer(self):
        from dapple.extras.mdcat.mdcat import get_renderer, MdcatOptions

        opts = MdcatOptions()
        renderer = get_renderer("braille", opts)
        assert hasattr(renderer, "render")
