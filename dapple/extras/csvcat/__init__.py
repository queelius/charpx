"""csvcat - Terminal CSV/TSV viewer with visualization modes.

Pretty-prints CSV and TSV files in the terminal with aligned columns,
and provides chart visualization via vizlib/dapple renderers.
"""

from dapple.extras.csvcat.cli import main

__all__ = ["main"]
