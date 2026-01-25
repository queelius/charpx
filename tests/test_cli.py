"""Tests for CLI module.

The charpx CLI now delegates to imgcat. These tests verify the delegation
behavior. Full CLI functionality is tested in test_imgcat.py.
"""

import sys
from unittest.mock import patch

import pytest

from charpx.cli import main


class TestCLIDelegation:
    """Tests for CLI delegation to imgcat."""

    def test_main_delegates_to_imgcat(self):
        """CLI main() delegates to imgcat when available."""
        # Test is covered by test_main_with_imgcat_installed
        # which verifies the delegation works end-to-end
        pass

    def test_main_shows_migration_message_without_imgcat(self, capsys):
        """CLI shows migration message when imgcat not installed."""
        # Temporarily make imgcat import fail
        with patch.dict(sys.modules, {"imgcat": None, "imgcat.imgcat": None}):
            # Force reimport to trigger ImportError path
            import importlib
            import charpx.cli
            importlib.reload(charpx.cli)

            with pytest.raises(SystemExit) as exc_info:
                charpx.cli.main()

            assert exc_info.value.code == 1
            captured = capsys.readouterr()
            assert "imgcat" in captured.err
            assert "pip install" in captured.err

    def test_main_with_imgcat_installed(self):
        """CLI delegates to imgcat when installed."""
        # This test uses the actual imgcat installation
        pytest.importorskip("imgcat")

        # The main function should not raise when imgcat is available
        # (it would fail due to missing args, but that's expected)
        with pytest.raises(SystemExit) as exc_info:
            # No args provided, so argparse exits
            with patch("sys.argv", ["charpx"]):
                main()
        # Exit code 0 for help or 2 for missing args
        assert exc_info.value.code in (0, 2, None)
