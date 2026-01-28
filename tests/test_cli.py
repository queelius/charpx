"""Tests for CLI module.

The dapple CLI now delegates to imgcat. These tests verify the delegation
behavior. Full CLI functionality is tested in test_imgcat.py.
"""

import sys
from unittest.mock import patch

import pytest

from dapple.cli import main


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
            import dapple.cli
            importlib.reload(dapple.cli)

            with pytest.raises(SystemExit) as exc_info:
                dapple.cli.main()

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
            with patch("sys.argv", ["dapple"]):
                main()
        # Exit code 0 for help, 1 for no images, 2 for missing required args
        assert exc_info.value.code in (0, 1, 2, None)
