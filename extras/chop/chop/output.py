"""Centralized output handling for chop CLI.

Implements Unix-philosophy output behavior with lazy evaluation:
- Auto-render to TTY (detect best renderer)
- JSON output when piped (just path + ops, no image data)
- Explicit flags override auto-detection
- Image is only loaded/processed (materialized) at render/save time
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse
    from chop.pipeline import PipelineState


def handle_output(state: PipelineState, args: argparse.Namespace) -> None:
    """Decide output based on flags and TTY detection.

    Decision logic (in order):
        1. -j/--json flag → JSON output (force even on TTY)
        2. -o/--output FILE → Materialize and save to file
        3. -r/--renderer NAME → Materialize and render with specified renderer
        4. stdout is TTY → Materialize, auto-detect best renderer, and render
        5. stdout is piped → JSON output (lazy, no materialization)

    Args:
        state: Pipeline state with path and operations.
        args: Parsed command-line arguments.
    """
    from chop.pipeline import write_pipeline_output
    from chop.render import render_to_terminal, auto_detect_renderer

    # 1. Explicit JSON flag (force JSON even on TTY)
    if getattr(args, "json", False):
        write_pipeline_output(state)
        return

    # 2. Save to file (materialize first)
    if getattr(args, "output", None):
        image = state.materialize()
        image.save(args.output)
        print(f"Saved to {args.output}", file=sys.stderr)
        return

    # 3. Explicit renderer (materialize first)
    if getattr(args, "renderer", None):
        image = state.materialize()
        render_to_terminal(
            image,
            renderer_name=args.renderer,
            width=getattr(args, "width", None),
            height=getattr(args, "height", None),
        )
        return

    # 4. TTY detection: render if interactive, JSON if piped
    if sys.stdout.isatty():
        # Materialize and render
        image = state.materialize()
        renderer = auto_detect_renderer()
        render_to_terminal(
            image,
            renderer_name=renderer,
            width=getattr(args, "width", None),
            height=getattr(args, "height", None),
        )
    else:
        # 5. Piped - output JSON for chaining (no materialization)
        write_pipeline_output(state)
