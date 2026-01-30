# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

dapple is a unified terminal graphics library. It provides a single Canvas API with multiple pluggable renderers (braille, quadrants, sextants, ASCII, sixel, kitty, fingerprint) for displaying bitmaps in the terminal.

The library addresses the fragmentation in terminal graphics: instead of separate libraries for braille (pixdot), color blocks (cel), sixel, and kitty protocols, dapple provides a consistent interface. Load a bitmap once, output to any format.

**Relationship to other libraries:**
- **pixdot** (../pixdot): Focused braille renderer. dapple's `braille` renderer provides equivalent output.
- **cel** (../cel): Focused quadrant block renderer. dapple's `quadrants` renderer provides equivalent output.
- **chop** (../chop): Standalone image manipulation CLI (extracted from dapple extras). Pure PIL/numpy, no dapple dependency. Designed for piping: `chop load img.png | chop resize 50% | chop save out.png`
- **dapple**: The unified library combining all approaches.

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=dapple --cov-report=term-missing

# Run a single test
pytest tests/test_renderers.py::TestBrailleRenderer::test_render_basic -v

# Verify imports work
python -c "from dapple import Canvas, braille; print('OK')"
```

## Architecture

The codebase has a modular structure:

### Core Modules (numpy only)

- **`dapple/canvas.py`**: Core Canvas class
  - `Canvas(bitmap, colors, renderer)` - Main container for bitmap data
  - `out(renderer, dest)` - Stream-based output to stdout, files, or TextIO
  - Composition methods: `hstack`, `vstack`, `overlay`, `crop`
  - Factory functions `from_array` and `from_pil` live in adapters, re-exported via `__init__.py`

- **`dapple/color.py`**: Shared color utilities
  - `LUM_R, LUM_G, LUM_B` - ITU-R BT.601 luminance coefficients (0.299, 0.587, 0.114)
  - `luminance(rgb)` - Compute perceptual luminance from RGB arrays (any shape with last dim 3)

- **`dapple/renderers/__init__.py`**: Renderer protocol and exports
  - `Renderer` - Protocol defining `render(bitmap, colors, dest)` and cell dimensions
  - Each renderer is a frozen dataclass with callable `__call__` for options

- **`dapple/renderers/braille.py`**: Unicode braille (2x4 dots)
  - Binary threshold with optional grayscale/truecolor ANSI
  - Cell: 2 wide x 4 tall pixels per character

- **`dapple/renderers/quadrants.py`**: Block characters (2x2)
  - ANSI foreground/background colors
  - 256-color or 24-bit true color modes

- **`dapple/renderers/sextants.py`**: Block characters (2x3)
  - Higher vertical resolution than quadrants
  - Same color modes as quadrants

- **`dapple/renderers/ascii.py`**: Classic ASCII art (1x2)
  - Configurable charset (default: ` .:-=+*#%@`)
  - Universal compatibility, no Unicode required

- **`dapple/renderers/sixel.py`**: DEC Sixel protocol (1x1)
  - True pixel output for xterm, mlterm, foot
  - Palette-based color quantization

- **`dapple/renderers/kitty.py`**: Kitty graphics protocol (1x1)
  - True pixel output for kitty, wezterm
  - PNG or raw RGB formats

- **`dapple/renderers/fingerprint.py`**: Glyph matching (8x16)
  - Correlates image regions with font glyph bitmaps
  - Artistic/experimental output

- **`dapple/preprocess.py`**: Preprocessing utilities
  - `auto_contrast(bitmap)` - Stretch histogram to full 0-1 range
  - `floyd_steinberg(bitmap, threshold)` - Floyd-Steinberg dithering
  - `invert(bitmap)` - Flip brightness values
  - `gamma_correct(bitmap, gamma)` - Gamma correction
  - `sharpen(bitmap, strength)` - Edge enhancement
  - `threshold(bitmap, level)` - Binary threshold
  - `resize(bitmap, height, width)` - Bilinear interpolation
  - `crop(bitmap, x, y, width, height)` - Extract rectangular region
  - `flip(bitmap, direction)` - Mirror horizontally ("h") or vertically ("v")
  - `rotate(bitmap, degrees)` - Rotate counter-clockwise

- **`dapple/auto.py`**: Terminal capability detection and renderer auto-selection
  - `detect_terminal()` - Returns `TerminalInfo` with detected protocol and capabilities
  - `auto_renderer()` - Returns best `Renderer` for the current terminal (kitty > sixel > quadrants > braille > ascii)
  - `render_image(path)` - Convenience: load image, auto-detect terminal, render
  - `Protocol` enum: KITTY, SIXEL, QUADRANTS, BRAILLE, ASCII

### Adapters (optional dependencies)

- **`dapple/adapters/`**: Library integrations
  - `numpy.py` - NumpyAdapter, from_array
  - `pil.py` - PILAdapter, from_pil, load_image
  - `matplotlib.py` - MatplotlibAdapter, from_matplotlib
  - `cairo.py` - CairoAdapter, from_cairo
  - `ansi.py` - ANSIAdapter, from_ansi (parse ANSI escape sequences into Canvas)

### Extras (`dapple/extras/`)

CLI tools and utilities built on dapple, shipped as part of the same package. Install tool dependencies with `pip install dapple[imgcat]`, `pip install dapple[all-tools]`, etc.

- **`dapple/extras/common.py`**: Shared utilities (renderer selection, `apply_preprocessing()`)
- **`dapple/extras/imgcat/`**: Terminal image viewer
- **`dapple/extras/funcat/`**: Function plotter
- **`dapple/extras/pdfcat/`**: Terminal PDF viewer
- **`dapple/extras/mdcat/`**: Terminal markdown viewer with inline images
- **`dapple/extras/vidcat/`**: Terminal video player
- **`dapple/extras/csvcat/`**: CSV/TSV viewer with charting
- **`dapple/extras/datacat/`**: JSON/JSONL viewer with tree/table/chart modes
- **`dapple/extras/vizlib/`**: Chart primitives (sparkline, bar, histogram, heatmap)

All extras use `dapple.extras.X` namespace for imports:
```python
from dapple.extras.imgcat import view, imgcat
from dapple.extras.vizlib import sparkline, bar_chart
```

## Renderer Protocol

All renderers implement the `Renderer` protocol:

```python
@runtime_checkable
class Renderer(Protocol):
    @property
    def cell_width(self) -> int: ...

    @property
    def cell_height(self) -> int: ...

    def render(
        self,
        bitmap: NDArray[np.floating],
        colors: NDArray[np.floating] | None = None,
        *,
        dest: TextIO,
    ) -> None: ...
```

Renderers write directly to streams (`dest`). This enables:
- Streaming output (no intermediate string allocation)
- Direct file writing
- Composable pipelines

Each renderer is a frozen dataclass. Use `__call__` to create variants:

```python
# Default instance
braille.render(bitmap, colors, dest=sys.stdout)

# Custom options via __call__
braille(threshold=0.3, color_mode="grayscale").render(...)
```

## Key Design Decisions

1. **Stream-based output**: Renderers write to `TextIO`, not return strings. More efficient for large outputs, supports streaming.

2. **Separate bitmap and colors**: Canvas holds both grayscale bitmap (for luminance/thresholding) and optional RGB colors. Renderers decide which to use.

3. **Frozen dataclasses**: Renderers are immutable. Use `__call__` to create new instances with different options.

4. **No image I/O in core**: Core library only depends on numpy. Image loading is in adapters with optional dependencies.

## Dependencies

- **Core library**: numpy only
- **Adapters** (`[adapters]`): pillow, matplotlib
- **Tools** (`[all-tools]`): all extras dependencies (pillow, pypdfium2, rich)
- **Individual tools**: `[imgcat]`, `[pdfcat]`, `[mdcat]`, `[vidcat]`, `[funcat]`, `[csvcat]`, `[datacat]`, `[vizlib]`
- **Dev** (`[dev]`): pytest, pytest-cov, all tools and adapters

## Test Structure

```
tests/
  test_canvas.py         # Canvas class, composition, conversion, factory functions
  test_color.py          # Luminance utility and BT.601 coefficients
  test_renderers.py      # All renderers, preprocessing functions
  test_adapters.py       # Numpy, PIL, Matplotlib, Cairo adapters
  test_auto.py           # Terminal detection and auto_renderer
  test_ansi_adapter.py   # ANSI escape sequence parsing
  test_extras_common.py  # Shared renderer selection and apply_preprocessing
  test_imgcat.py         # imgcat terminal image viewer
  test_funcat.py         # funcat function plotter
  test_pdfcat.py         # pdfcat PDF viewer
  test_mdcat.py          # mdcat markdown viewer
  test_vidcat.py         # vidcat video player
  test_csvcat.py         # csvcat CSV viewer
  test_datacat.py        # datacat JSON viewer
  test_vizlib.py         # vizlib chart primitives
```

Run with: `pytest tests/ -v`
