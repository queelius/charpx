# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

pixdot is a bitmap-to-braille rasterizer for terminals, designed for the terminal-centric development era. As developers increasingly work through Claude Code, SSH sessions, and text-based AI assistants, there's growing need to display graphics without leaving the terminal. pixdot addresses this with the simplest possible approach: `bitmap → braille string`.

Each braille character (U+2800–U+28FF) encodes a 2×4 dot pattern, providing 8× the pseudo-pixel density of regular characters. The implementation is intentionally minimal (~50 lines core) and pedagogically clear—a direct 1:1 mapping from pixel regions to Unicode codepoints.

pixdot serves as a framebuffer target: higher-level libraries (vector drawing, plotting, game graphics) can render to a numpy bitmap and call pixdot for terminal display.

**pixdot vs pixblock:** pixdot outputs binary (on/off) braille patterns—conceptually pure but limited to structure and edges. pixblock (at ../pixblock) uses ANSI colors with block characters to capture tone, texture, and gradients. Use pixdot for simplicity, text piping, and accessibility; use pixblock for photographic images.

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=pixdot --cov-report=term-missing

# Run a single test
pytest tests/test_pixdot.py::TestRender::test_output_dimensions -v

# CLI usage (requires: pip install pixdot[cli])
pixdot <image> [-w WIDTH] [-t THRESHOLD] [--dither] [--contrast] [--invert] [-o OUTPUT]

# Run example scripts
python examples/framebuffer_demo.py         # Drawing primitives demo
python examples/graphing_calculator.py      # Terminal graphing calculator (requires matplotlib)
python examples/stats_dashboard.py          # Statistical visualizations (requires matplotlib)
python examples/ai_recipes.py --list        # List AI-ready visualization recipes
```

## Architecture

The codebase has a modular structure:

### Core Modules (numpy-only)
- **`pixdot/braille.py`**: Core braille rendering engine
  - `render(bitmap, threshold)` - Main API. Takes a 2D numpy array (H×W, values 0.0-1.0), returns multi-line string of braille characters
  - `threshold` can be a float (0.0-1.0) or `None` for auto-detection from bitmap mean
  - `_region_to_braille_code()` - Maps 2×4 pixel regions to braille Unicode codepoints

- **`pixdot/preprocess.py`**: Preprocessing utilities
  - `auto_contrast(bitmap)` - Stretch histogram to full 0-1 range
  - `floyd_steinberg(bitmap, threshold)` - Floyd-Steinberg dithering for binary output

- **`pixdot/ansi.py`**: ANSI color rendering
  - `render_ansi()` - Render with 24-level grayscale or 24-bit RGB color

- **`pixdot/config.py`**: Configuration and presets
  - `RenderConfig` - Dataclass with rendering options
  - `get_preset(name)` - Named presets (dark_terminal, high_detail, truecolor, etc.)

- **`pixdot/resize.py`**: Bitmap resizing utilities

### CLI Modules (require PIL via `[cli]` extra)
- **`pixdot/image_cli.py`**: Main CLI entry point
  - `load_image()` - Loads image via PIL, converts to grayscale, resizes
  - `main()` - argparse-based CLI with subcommand support

- **`pixdot/claude_cli.py`**: Claude Code skill management
  - `pixdot claude install-skill` - Install Claude Code skill
  - `pixdot claude show-skill` - Display skill content

### Adapters (optional dependencies)
- **`pixdot/adapters/`**: Library integrations
  - `matplotlib.py` - Matplotlib Figure → braille
  - `pil.py` - PIL Image → braille
  - `cairo.py` - Cairo Surface → braille
  - `base.py` - Abstract BitmapAdapter protocol

### Examples
- **`examples/`**: Demo scripts
  - `framebuffer_demo.py` - Drawing primitives in pure numpy
  - `graphing_calculator.py` - Terminal graphing calculator
  - `stats_dashboard.py` - Statistical visualizations
  - `ai_recipes.py` - Ready-to-copy recipes for AI assistants
  - `realtime_monitor.py` - Live data visualization

## Braille Encoding

Each braille character represents a 2×4 pixel region. The Unicode codepoint offset (0-255) encodes which of the 8 dots are active:

```
col 0   col 1
+---+---+
| 0 | 3 |  bits 0, 3
+---+---+
| 1 | 4 |  bits 1, 4
+---+---+
| 2 | 5 |  bits 2, 5
+---+---+
| 6 | 7 |  bits 6, 7
+---+---+
```

Codepoint = U+2800 + (sum of 2^bit for each active dot)

## Dependencies

- **Core library**: numpy only
- **CLI extra** (`[cli]`): pillow
- **Dev** (`[dev]`): pytest, pytest-cov, pillow
- **plot_to_braille.py example**: matplotlib
