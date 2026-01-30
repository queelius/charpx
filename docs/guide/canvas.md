# Canvas API

The `Canvas` class is the central object in dapple. It holds a grayscale bitmap and optional RGB color data, and provides rendering to any of dapple's pluggable renderers.

## Creating a Canvas

### From a numpy array (direct)

The constructor takes a 2D numpy array of float values in the range 0.0--1.0, where higher values mean brighter pixels.

```python
import numpy as np
from dapple import Canvas

# Grayscale bitmap
bitmap = np.random.rand(40, 80).astype(np.float32)
canvas = Canvas(bitmap)

# With RGB color data
colors = np.random.rand(40, 80, 3).astype(np.float32)
canvas = Canvas(bitmap, colors=colors)
```

The bitmap must be 2D with shape `(H, W)`. If colors are provided, they must be 3D with shape `(H, W, 3)` and match the bitmap dimensions.

### Factory: `from_array`

For RGB arrays, `from_array` computes the grayscale bitmap automatically using ITU-R BT.601 luminance coefficients (0.299R + 0.587G + 0.114B).

```python
from dapple import from_array

# 2D grayscale
canvas = from_array(np.random.rand(40, 80))

# 3D RGB -- bitmap is derived from luminance
rgb = np.random.rand(40, 80, 3).astype(np.float32)
canvas = from_array(rgb)
```

### Factory: `from_pil`

Converts a PIL Image to a Canvas. Handles L, RGB, and RGBA modes. Other modes are converted to grayscale. Supports optional `width` and `height` parameters for resizing on load.

```python
from PIL import Image
from dapple import from_pil

img = Image.open("photo.jpg")
canvas = from_pil(img)                   # original size
canvas = from_pil(img, width=160)        # resize to width, keep aspect ratio
canvas = from_pil(img, height=80)        # resize to height, keep aspect ratio
canvas = from_pil(img, width=160, height=80)  # exact dimensions
```

> **Note:** `from_pil` requires pillow (`pip install pillow`).

### Using adapters

For integration with matplotlib or cairo, see the [Adapters guide](adapters.md). You can also use `load_image` to load directly from a path:

```python
from dapple.adapters.pil import load_image

canvas = load_image("photo.jpg", width=160)
```

## Output

### `canvas.out(renderer)`

The primary output method. Writes rendered output directly to a stream.

```python
from dapple import Canvas, braille, quadrants, sextants

bitmap = np.random.rand(40, 80).astype(np.float32)
canvas = Canvas(bitmap)

# To stdout (default)
canvas.out(braille)

# To a file path
canvas.out(quadrants, "art.txt")

# To any file-like object
import sys
canvas.out(sextants, sys.stderr)

from io import StringIO
buf = StringIO()
canvas.out(braille, buf)
text = buf.getvalue()
```

| Argument   | Type              | Default      | Description                          |
|------------|-------------------|--------------|--------------------------------------|
| `renderer` | `Renderer`        | *(required)* | Which renderer to use                |
| `dest`     | `str \| TextIO \| None` | `sys.stdout` | File path, stream, or None for stdout |

### `print(canvas)` with a default renderer

Set a default renderer at construction time. Then `str(canvas)` and `print(canvas)` use that renderer automatically.

```python
from dapple import Canvas, braille, quadrants

canvas = Canvas(bitmap, renderer=quadrants)
print(canvas)  # Uses quadrants

# Change the default renderer (returns a new Canvas)
canvas2 = canvas.with_renderer(braille)
print(canvas2)  # Uses braille
```

If no default renderer is set, `__str__` falls back to braille.

### Custom renderer options

Renderers are frozen dataclasses. Call them to create variants with different settings.

```python
canvas.out(braille(threshold=0.3, color_mode="truecolor"))
canvas.out(quadrants(true_color=False))
canvas.out(ascii(charset=" .oO@"))
```

## Properties

| Property       | Type            | Description                             |
|----------------|-----------------|-----------------------------------------|
| `bitmap`       | `NDArray`       | Read-only view of the (H, W) grayscale bitmap |
| `colors`       | `NDArray\|None` | Read-only view of the (H, W, 3) RGB colors    |
| `pixel_width`  | `int`           | Width in pixels (W)                     |
| `pixel_height` | `int`           | Height in pixels (H)                    |
| `shape`        | `(int, int)`    | `(H, W)` -- numpy convention            |
| `size`         | `(int, int)`    | `(W, H)` -- PIL convention              |

```python
>>> canvas = Canvas(np.zeros((40, 80), dtype=np.float32))
>>> canvas.shape
(40, 80)
>>> canvas.size
(80, 40)
>>> canvas.pixel_width, canvas.pixel_height
(80, 40)
```

## Composition

### `hstack` -- horizontal concatenation

Joins two canvases side by side. Heights must match.

```python
left = Canvas(np.zeros((40, 40), dtype=np.float32))
right = Canvas(np.ones((40, 40), dtype=np.float32))
combined = left.hstack(right)
# combined.shape == (40, 80)
```

### Operator `+` -- shorthand for hstack

```python
combined = left + right  # Same as left.hstack(right)
```

### `vstack` -- vertical concatenation

Joins two canvases top to bottom. Widths must match.

```python
top = Canvas(np.zeros((20, 80), dtype=np.float32))
bottom = Canvas(np.ones((20, 80), dtype=np.float32))
combined = top.vstack(bottom)
# combined.shape == (40, 80)
```

### `overlay` -- compositing at a position

Places one canvas on top of another at pixel coordinates `(x, y)`.

```python
background = Canvas(np.zeros((100, 200), dtype=np.float32))
foreground = Canvas(np.ones((20, 40), dtype=np.float32))

# Place foreground at position (10, 5)
result = background.overlay(foreground, x=10, y=5)
```

The overlay is clipped to the background bounds. Out-of-bounds portions are silently discarded.

### `crop` -- extract a region

Extracts a rectangular region. Coordinates are `(x1, y1, x2, y2)` where `(x1, y1)` is inclusive and `(x2, y2)` is exclusive.

```python
canvas = Canvas(np.random.rand(100, 200).astype(np.float32))
cropped = canvas.crop(x1=10, y1=20, x2=90, y2=80)
# cropped.shape == (60, 80)
```

Raises `ValueError` if coordinates are out of bounds or invalid.

### Color handling in composition

When composing canvases where one has colors and the other does not, dapple promotes the grayscale canvas to a three-channel grayscale representation so the operation can proceed. Both canvases having colors, or neither having colors, works without conversion.

## Transforms

### `with_invert`

Returns a new Canvas with inverted brightness (0 becomes 1, 1 becomes 0). Colors are preserved unchanged.

```python
inverted = canvas.with_invert()
canvas.out(braille)           # Original
inverted.out(braille)         # Inverted
```

### `with_renderer`

Returns a new Canvas with a different default renderer.

```python
canvas_braille = canvas.with_renderer(braille)
canvas_quads = canvas.with_renderer(quadrants)
print(canvas_braille)  # braille output
print(canvas_quads)    # quadrant output
```

## Pixel Access

Canvas supports numpy-style indexing on the bitmap.

```python
# Single pixel
value = canvas[10, 20]

# Slice
region = canvas[0:10, 0:20]  # Returns a numpy array, not a Canvas
```

## Conversion

### `to_bitmap()`

Returns a copy of the grayscale bitmap array.

```python
arr = canvas.to_bitmap()  # (H, W) float32 array
```

### `to_pil()`

Converts to a PIL Image. Returns RGB if the canvas has colors, grayscale otherwise.

```python
img = canvas.to_pil()
img.save("output.png")
```

### `save(path)`

Shorthand for `to_pil().save(path)`. File format is determined by extension.

```python
canvas.save("output.png")
canvas.save("output.jpg")
```

Both `to_pil()` and `save()` require pillow.

## Color Model

Canvas separates grayscale luminance from color information:

- **`bitmap`** -- 2D array `(H, W)`, values 0.0--1.0. Represents brightness/luminance. Used by renderers for thresholding decisions (which dots to activate, which quadrants are foreground vs background).

- **`colors`** -- 3D array `(H, W, 3)`, values 0.0--1.0, or `None`. Represents RGB color. Used by renderers that support color output (quadrants, sextants, braille in truecolor mode). Ignored by renderers that do not (ascii, fingerprint).

This separation lets each renderer pick the right data for its needs. Binary renderers (braille) threshold on the bitmap. Color renderers (quadrants) use colors for foreground/background ANSI codes. Pixel renderers (sixel, kitty) use whichever is available.

```python
# Grayscale only -- renderers use bitmap for everything
canvas = Canvas(bitmap)

# With color -- renderers that support color will use it
canvas = Canvas(bitmap, colors=rgb_array)
```

## Complete Example

```python
import numpy as np
from dapple import Canvas, braille, quadrants, from_array

# Create a gradient
x = np.linspace(0, 1, 160)
y = np.linspace(0, 1, 80)
bitmap = np.outer(y, x).astype(np.float32)

canvas = Canvas(bitmap, renderer=braille)

# Print with default renderer
print(canvas)

# Output with explicit renderer
canvas.out(quadrants)

# Compose two views
left = canvas.crop(0, 0, 80, 80)
right = canvas.crop(80, 0, 160, 80)
side_by_side = left + right
side_by_side.out(braille)

# Save as image
canvas.save("gradient.png")
```
