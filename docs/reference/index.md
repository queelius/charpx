# API Reference

Manual API surface listing for the dapple terminal graphics library.

## Core

### `dapple.Canvas`

```python
Canvas(bitmap, *, colors=None, renderer=None)
```

Main container for bitmap data. Holds a 2D grayscale bitmap (values 0.0-1.0) and optional RGB color array.

**Parameters:**
- `bitmap` (`NDArray[np.floating]`) -- 2D array of shape `(H, W)` with values 0.0-1.0. Higher values = brighter.
- `colors` (`NDArray[np.floating] | None`) -- Optional 3D array of shape `(H, W, 3)` with RGB values 0.0-1.0.
- `renderer` (`Renderer | None`) -- Default renderer for `__str__` / `print()`. If None, uses braille.

**Properties:**
- `bitmap` -- Read-only view of the grayscale bitmap `(H, W)`.
- `colors` -- Read-only view of the RGB colors `(H, W, 3)`, or None.
- `pixel_width` -- Width in pixels.
- `pixel_height` -- Height in pixels.
- `shape` -- `(H, W)` tuple (numpy convention).
- `size` -- `(W, H)` tuple (PIL convention).

### `Canvas.out`

```python
Canvas.out(renderer, dest=None)
```

Render the canvas to a stream or file.

**Parameters:**
- `renderer` (`Renderer`) -- The renderer to use (e.g. `braille`, `quadrants`, `sixel`).
- `dest` (`str | TextIO | None`) -- File path (str), file-like object, or None for stdout.

### `from_array`

```python
from dapple import from_array

canvas = from_array(array, *, renderer=None)
```

Module-level factory. Create a Canvas from a numpy array. Accepts 2D grayscale or 3D RGB `(H, W, 3)` arrays. RGB arrays auto-compute luminance for the bitmap using ITU-R BT.601 coefficients.

### `from_pil`

```python
from dapple import from_pil

canvas = from_pil(image, *, width=None, height=None, renderer=None)
```

Module-level factory. Create a Canvas from a PIL Image. Handles L, RGB, and RGBA modes. Optionally resizes on load — specify `width`, `height`, or both. When only one dimension is given, the other scales proportionally.

### `Canvas.hstack` / `Canvas.vstack`

```python
Canvas.hstack(other) -> Canvas
Canvas.vstack(other) -> Canvas
```

Composition. Horizontally or vertically stack two canvases. Heights must match for hstack; widths must match for vstack. Also available as the `+` operator (hstack).

### `Canvas.overlay`

```python
Canvas.overlay(other, x, y) -> Canvas
```

Overlay another canvas at pixel position `(x, y)`. The overlay region is clipped to bounds.

### `Canvas.crop`

```python
Canvas.crop(x1, y1, x2, y2) -> Canvas
```

Crop to a rectangular region. Coordinates are in pixels; `x2` and `y2` are exclusive.

### `Canvas.with_invert`

```python
Canvas.with_invert() -> Canvas
```

Return a new Canvas with inverted brightness (0 becomes 1, 1 becomes 0).

### `Canvas.with_renderer`

```python
Canvas.with_renderer(renderer) -> Canvas
```

Return a new Canvas with a different default renderer.

---

## Renderers

All renderers implement the `Renderer` protocol and are frozen dataclasses. Default instances are available as module-level singletons. Use `__call__` to create variants with custom options.

### Renderer Protocol

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

- `cell_width` / `cell_height` -- How many pixels each terminal character cell encodes.
- `render(bitmap, colors, *, dest)` -- Write rendered output to `dest` stream.

### `dapple.braille`

```python
braille(threshold=0.5, color_mode="none")
```

Unicode braille renderer. Cell: 2x4 pixels per character.

**Parameters:**
- `threshold` (`float`) -- Brightness cutoff for dot activation (0.0-1.0).
- `color_mode` (`str`) -- One of `"none"`, `"grayscale"`, `"truecolor"`.

### `dapple.quadrants`

```python
quadrants(true_color=True, grayscale=False)
```

Block character renderer using 2x2 quadrant characters with fg/bg ANSI colors.

**Parameters:**
- `true_color` (`bool`) -- Use 24-bit true color (vs 256-color).
- `grayscale` (`bool`) -- Force grayscale output.

### `dapple.sextants`

```python
sextants(true_color=True, grayscale=False)
```

Block character renderer using 2x3 sextant characters. Higher vertical resolution than quadrants. Requires Unicode 13.0+ font support.

**Parameters:**
- `true_color` (`bool`) -- Use 24-bit true color (vs 256-color).
- `grayscale` (`bool`) -- Force grayscale output.

### `dapple.ascii`

```python
ascii(charset=" .:-=+*#%@")
```

ASCII art renderer. Cell: 1x2 pixels per character. Universal compatibility.

**Parameters:**
- `charset` (`str`) -- Characters ordered from darkest to brightest.

### `dapple.sixel`

```python
sixel(max_colors=256, scale=1)
```

DEC Sixel protocol renderer. True pixel output (1:1). Requires sixel-capable terminal (xterm, foot, mlterm, WezTerm).

**Parameters:**
- `max_colors` (`int`) -- Maximum palette size for color quantization.
- `scale` (`int`) -- Pixel scaling factor.

### `dapple.kitty`

```python
kitty(format="png")
```

Kitty graphics protocol renderer. True pixel output with 24-bit color. Requires Kitty, WezTerm, or Ghostty.

**Parameters:**
- `format` (`str`) -- Image format: `"png"` or `"rgb"`.

### `dapple.fingerprint`

```python
fingerprint(glyph_set="ascii", cell_width=8, cell_height=16)
```

Glyph correlation renderer. Matches image regions to font glyphs by visual similarity. Requires Pillow for font rendering.

**Parameters:**
- `glyph_set` (`str`) -- Character set to match against: `"ascii"`, `"blocks"`, `"braille"`, `"all"`.
- `cell_width` (`int`) -- Width of each glyph cell in pixels.
- `cell_height` (`int`) -- Height of each glyph cell in pixels.

---

## Preprocessing

All functions in `dapple.preprocess` take a 2D numpy array (values 0.0-1.0) and return a 2D numpy array (values 0.0-1.0). They compose by sequencing.

### `auto_contrast`

```python
auto_contrast(bitmap: NDArray) -> NDArray
```

Histogram stretch. Maps the darkest pixel to 0.0 and the brightest to 1.0.

### `floyd_steinberg`

```python
floyd_steinberg(bitmap: NDArray, threshold: float = 0.5) -> NDArray
```

Floyd-Steinberg error diffusion dithering. Converts continuous tones to binary dot patterns that encode brightness through spatial density.

### `gamma_correct`

```python
gamma_correct(bitmap: NDArray, gamma: float = 2.2) -> NDArray
```

Gamma correction. Values < 1 brighten, values > 1 darken.

### `sharpen`

```python
sharpen(bitmap: NDArray, strength: float = 1.0) -> NDArray
```

Laplacian edge enhancement. Amplifies brightness transitions at edges.

### `threshold`

```python
threshold(bitmap: NDArray, level: float = 0.5) -> NDArray
```

Binary threshold. Everything above `level` becomes 1.0, below becomes 0.0.

### `resize`

```python
resize(bitmap: NDArray, height: int, width: int) -> NDArray
```

Bilinear interpolation resize. Numpy-only, no PIL required.

### `invert`

```python
invert(bitmap: NDArray) -> NDArray
```

Flip brightness values: `1.0 - bitmap`.

### `crop`

```python
crop(bitmap: NDArray, x: int, y: int, width: int, height: int) -> NDArray
```

Extract a rectangular region from the bitmap. Raises `ValueError` if the region is out of bounds.

### `flip`

```python
flip(bitmap: NDArray, direction: str) -> NDArray
```

Mirror the bitmap. `direction` is `"h"` (horizontal / left-right) or `"v"` (vertical / top-bottom).

### `rotate`

```python
rotate(bitmap: NDArray, degrees: float) -> NDArray
```

Rotate counter-clockwise. For 90/180/270 degrees, uses efficient numpy rotation. Arbitrary angles require scipy.

---

## Color Utilities

Shared color constants and functions in `dapple.color`.

### `luminance`

```python
from dapple.color import luminance

gray = luminance(rgb)
```

Compute perceptual luminance from RGB data using ITU-R BT.601 coefficients (0.299R + 0.587G + 0.114B). Accepts any array with shape `(..., 3)` — works on 2D images `(H, W, 3)`, 4D renderer blocks `(rows, cols, cells, 3)`, etc.

### Constants

```python
from dapple.color import LUM_R, LUM_G, LUM_B
# LUM_R = 0.299, LUM_G = 0.587, LUM_B = 0.114
```

---

## Auto-Detection

Terminal capability detection and automatic renderer selection, in `dapple.auto`.

### `detect_terminal`

```python
detect_terminal() -> TerminalInfo
```

Detect the current terminal's graphics capabilities. Returns a `TerminalInfo` dataclass with the detected protocol and terminal name.

### `auto_renderer`

```python
auto_renderer(plain: bool = False) -> Renderer
```

Return the best renderer for the current terminal. Selection order: kitty > sixel > quadrants > braille > ascii. If `plain=True`, returns ascii.

### `render_image`

```python
render_image(path: str, width: int | None = None) -> None
```

Convenience one-liner: load an image, auto-detect terminal, render to stdout.

### `Protocol`

```python
class Protocol(Enum):
    KITTY = "kitty"
    SIXEL = "sixel"
    QUADRANTS = "quadrants"
    BRAILLE = "braille"
    ASCII = "ascii"
```

Enum of terminal graphics protocols supported by dapple.

### `TerminalInfo`

```python
@dataclass
class TerminalInfo:
    protocol: Protocol
    terminal_name: str | None = None
    color_support: bool = True
```

Detected terminal capabilities. The `is_pixel_renderer` property returns True for kitty and sixel.

---

## Adapters

Optional integrations for loading data from external libraries. Located in `dapple.adapters`.

### `NumpyAdapter` / `from_array`

```python
from dapple.adapters.numpy import NumpyAdapter, from_array

adapter = NumpyAdapter()
canvas = adapter.to_canvas(array)

# Or use the convenience function:
canvas = from_array(array)
```

Create a Canvas from a numpy array. Accepts 2D grayscale or 3D RGB `(H, W, 3)`.

### `PILAdapter` / `from_pil` / `load_image`

```python
from dapple.adapters.pil import PILAdapter, from_pil, load_image

canvas = from_pil(pil_image)
canvas = load_image("photo.jpg")
```

Create a Canvas from a PIL Image or load one from a file path. Requires `pillow`.

### `MatplotlibAdapter` / `from_matplotlib`

```python
from dapple.adapters.matplotlib import MatplotlibAdapter, from_matplotlib

canvas = from_matplotlib(fig)
```

Render a matplotlib Figure to a Canvas. Rasterizes the figure at a configurable DPI. Requires `matplotlib`.

### `CairoAdapter` / `from_cairo`

```python
from dapple.adapters.cairo import CairoAdapter, from_cairo

canvas = from_cairo(surface)
```

Create a Canvas from a Cairo ImageSurface. Requires `pycairo`.

### `ANSIAdapter` / `from_ansi`

```python
from dapple.adapters.ansi import ANSIAdapter, from_ansi

canvas = from_ansi(ansi_text)
```

Parse ANSI escape sequences (braille, quadrant, sextant, or ASCII art) back into a Canvas. Reconstructs bitmap and color data from rendered terminal output. Useful for round-tripping or converting between renderer formats.
