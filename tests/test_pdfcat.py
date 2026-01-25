"""Tests for pdfcat extra."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Skip all tests if pypdfium2 not available
pytest.importorskip("pypdfium2")
pytest.importorskip("PIL")
pdfcat_mod = pytest.importorskip("pdfcat")


class TestPageRangeParsing:
    """Tests for page range parsing."""

    def test_single_page(self):
        from pdfcat.pdfcat import parse_page_range

        assert parse_page_range("1", 10) == [1]
        assert parse_page_range("5", 10) == [5]

    def test_page_range(self):
        from pdfcat.pdfcat import parse_page_range

        assert parse_page_range("1-3", 10) == [1, 2, 3]
        assert parse_page_range("5-7", 10) == [5, 6, 7]

    def test_multiple_pages(self):
        from pdfcat.pdfcat import parse_page_range

        assert parse_page_range("1,3,5", 10) == [1, 3, 5]

    def test_mixed_ranges(self):
        from pdfcat.pdfcat import parse_page_range

        assert parse_page_range("1-3,7,9-10", 10) == [1, 2, 3, 7, 9, 10]

    def test_open_ended_range(self):
        from pdfcat.pdfcat import parse_page_range

        assert parse_page_range("-3", 10) == [1, 2, 3]
        assert parse_page_range("8-", 10) == [8, 9, 10]

    def test_out_of_bounds_ignored(self):
        from pdfcat.pdfcat import parse_page_range

        # Page 15 is beyond the 10-page document
        assert parse_page_range("1,15", 10) == [1]


class TestPdfcatOptions:
    """Tests for PdfcatOptions dataclass."""

    def test_default_options(self):
        from pdfcat import PdfcatOptions

        opts = PdfcatOptions()
        assert opts.renderer == "auto"
        assert opts.width is None
        assert opts.pages is None
        assert opts.dpi == 150
        assert opts.dither is False


class TestSkillInstall:
    """Tests for skill installation."""

    def test_skill_install_local(self):
        from pdfcat.pdfcat import skill_install

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pdfcat.pdfcat.Path.cwd", return_value=Path(tmpdir)):
                result = skill_install(local=True)
                assert result is True
                skill_file = Path(tmpdir) / ".claude" / "skills" / "pdfcat.md"
                assert skill_file.exists()

    def test_skill_install_requires_flag(self, capsys):
        from pdfcat.pdfcat import skill_install

        result = skill_install()
        assert result is False
        captured = capsys.readouterr()
        assert "Specify --local or --global" in captured.err


class TestGetRenderer:
    """Tests for get_renderer function."""

    def test_auto_renderer(self):
        from pdfcat.pdfcat import get_renderer, PdfcatOptions

        opts = PdfcatOptions()
        renderer = get_renderer("auto", opts)
        assert hasattr(renderer, "render")

    def test_braille_renderer(self):
        from pdfcat.pdfcat import get_renderer, PdfcatOptions

        opts = PdfcatOptions()
        renderer = get_renderer("braille", opts)
        assert hasattr(renderer, "render")
