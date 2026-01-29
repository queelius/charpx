"""datacat - Terminal JSON/JSONL viewer with visualization modes.

Pretty-prints JSON with syntax coloring, supports dot-path queries,
tree views, JSONL table flattening, and chart visualization via
vizlib/dapple renderers.
"""

from dapple.extras.datacat.cli import main

__all__ = ["main"]
