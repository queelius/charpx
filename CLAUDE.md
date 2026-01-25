# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

charpx is a unified terminal graphics library. It provides a single Canvas API with multiple pluggable renderers (braille, quadrants, sextants, ASCII, sixel, kitty, fingerprint) for displaying bitmaps in the terminal.

The library addresses the fragmentation in terminal graphics: instead of separate libraries for braille (pixdot), color blocks (cel), sixel, and kitty protocols, charpx provides a consistent interface. Load a bitmap once, output to any format.

**Relationship to other libraries:**
- **pixdot** (../pixdot): Focused braille renderer. charpx's `braille` renderer provides equivalent output.
- **cel** (../cel): Focused quadrant block renderer. charpx's `quadrants` renderer provides equivalent output.
- **charpx**: The unified library combining all approaches.

## Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=charpx --cov-report=term-missing

# Run a single test
pytest tests/test_renderers.py::TestBrailleRenderer::test_render_basic -v

# Verify imports work
python -c "from charpx import Canvas, braille; print('OK')"
```

## Architecture

The codebase has a modular structure:

### Core Modules (numpy only)

- **`charpx/canvas.py`**: Core Canvas class
  - `Canvas(bitmap, colors, renderer)` - Main container for bitmap data
  - `out(renderer, dest)` - Stream-based output to stdout, files, or TextIO
  - `from_array(array)` - Factory from numpy arrays (2D grayscale or 3D RGB)
  - `from_pil(image)` - Factory from PIL Images
  - Composition methods: `hstack`, `vstack`, `overlay`, `crop`

- **`charpx/renderers/__init__.py`**: Renderer protocol and exports
  - `Renderer` - Protocol defining `render(bitmap, colors, dest)` and cell dimensions
  - Each renderer is a frozen dataclass with callable `__call__` for options

- **`charpx/renderers/braille.py`**: Unicode braille (2x4 dots)
  - Binary threshold with optional grayscale/truecolor ANSI
  - Cell: 2 wide x 4 tall pixels per character

- **`charpx/renderers/quadrants.py`**: Block characters (2x2)
  - ANSI foreground/background colors
  - 256-color or 24-bit true color modes

- **`charpx/renderers/sextants.py`**: Block characters (2x3)
  - Higher vertical resolution than quadrants
  - Same color modes as quadrants

- **`charpx/renderers/ascii.py`**: Classic ASCII art (1x2)
  - Configurable charset (default: ` .:-=+*#%@`)
  - Universal compatibility, no Unicode required

- **`charpx/renderers/sixel.py`**: DEC Sixel protocol (1x1)
  - True pixel output for xterm, mlterm, foot
  - Palette-based color quantization

- **`charpx/renderers/kitty.py`**: Kitty graphics protocol (1x1)
  - True pixel output for kitty, wezterm
  - PNG or raw RGB formats

- **`charpx/renderers/fingerprint.py`**: Glyph matching (8x16)
  - Correlates image regions with font glyph bitmaps
  - Artistic/experimental output

- **`charpx/preprocess.py`**: Preprocessing utilities
  - `auto_contrast(bitmap)` - Stretch histogram to full 0-1 range
  - `floyd_steinberg(bitmap, threshold)` - Floyd-Steinberg dithering
  - `invert(bitmap)` - Flip brightness values
  - `gamma_correct(bitmap, gamma)` - Gamma correction
  - `sharpen(bitmap, strength)` - Edge enhancement
  - `threshold(bitmap, level)` - Binary threshold
  - `resize(bitmap, height, width)` - Bilinear interpolation

### Adapters (optional dependencies)

- **`charpx/adapters/`**: Library integrations
  - `numpy.py` - NumpyAdapter, from_array
  - `pil.py` - PILAdapter, from_pil, load_image
  - `matplotlib.py` - MatplotlibAdapter, from_matplotlib
  - `cairo.py` - CairoAdapter, from_cairo

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
- **CLI** (`[cli]`): pillow
- **Adapters** (`[adapters]`): pillow, matplotlib
- **Dev** (`[dev]`): pytest, pytest-cov, pillow, matplotlib

## Test Structure

```
tests/
  test_canvas.py     # Canvas class, composition, conversion
  test_renderers.py  # All renderers, preprocessing functions
```

Run with: `pytest tests/ -v`
