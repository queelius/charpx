# Preprocessing

Raw bitmaps usually look terrible when rendered to terminal characters. The dynamic range is wrong, the gamma is wrong, and there is too much spatial detail for the low resolution of a character grid. Preprocessing fixes these problems.

All preprocessing functions in `dapple.preprocess` share the same signature: they take a 2D numpy array `(H, W)` with float values in 0.0--1.0 and return an array of the same shape and range. This makes them composable -- pipe the output of one into the next.

```python
from dapple.preprocess import auto_contrast, floyd_steinberg, sharpen

bitmap = auto_contrast(bitmap)
bitmap = sharpen(bitmap, strength=0.5)
bitmap = floyd_steinberg(bitmap)
```

## Functions Reference

### `auto_contrast(bitmap)`

Stretches the histogram so the darkest pixel becomes 0.0 and the brightest becomes 1.0. This is the single most impactful preprocessing step.

```python
from dapple.preprocess import auto_contrast

stretched = auto_contrast(bitmap)
# stretched.min() == 0.0
# stretched.max() == 1.0
```

**When to use:** Almost always. Most images do not use the full 0--1 range, which wastes the limited tonal resolution of character-based renderers.

**How it works:**

```python
def auto_contrast(bitmap):
    min_val = bitmap.min()
    max_val = bitmap.max()
    if max_val - min_val < 1e-6:
        return np.full_like(bitmap, 0.5)  # constant image
    return (bitmap - min_val) / (max_val - min_val)
```

For constant images (all pixels identical), returns a uniform 0.5 to avoid division by zero.

---

### `floyd_steinberg(bitmap, threshold=0.5)`

Applies Floyd-Steinberg error diffusion dithering. Converts the image to binary (0.0 or 1.0 only) while preserving the appearance of grayscale through varying dot density.

```python
from dapple.preprocess import floyd_steinberg

dithered = floyd_steinberg(bitmap, threshold=0.5)
# np.unique(dithered) == [0.0, 1.0]
```

| Parameter   | Type    | Default | Description                    |
|-------------|---------|---------|--------------------------------|
| `threshold` | `float` | `0.5`   | Quantization threshold         |

**When to use:** Before binary renderers (braille). Dithering is the single most effective improvement for braille output of photographic images. It converts continuous tones into dot patterns that the eye perceives as shading.

**How it works:**

For each pixel, left-to-right, top-to-bottom:
1. Quantize the pixel to 0 or 1 based on the threshold.
2. Compute the quantization error (original value minus quantized value).
3. Distribute the error to neighboring pixels using the Floyd-Steinberg coefficients:

```
         X    7/16
  3/16  5/16  1/16
```

The error distribution causes neighboring pixels to compensate, creating the characteristic dithered dot pattern.

---

### `gamma_correct(bitmap, gamma=2.2)`

Applies a power-law gamma curve to adjust brightness distribution.

```python
from dapple.preprocess import gamma_correct

brightened = gamma_correct(bitmap, gamma=0.5)   # gamma < 1 brightens
darkened = gamma_correct(bitmap, gamma=2.2)     # gamma > 1 darkens
```

| Parameter | Type    | Default | Description                             |
|-----------|---------|---------|-----------------------------------------|
| `gamma`   | `float` | `2.2`   | Gamma exponent. < 1 brightens, > 1 darkens |

**When to use:** Dark images that lose detail after thresholding. A gamma less than 1.0 pulls up shadow detail. Standard monitor gamma is 2.2, so applying `gamma=1/2.2` (approximately 0.45) linearizes a standard image.

**How it works:**

```python
def gamma_correct(bitmap, gamma=2.2):
    clamped = np.clip(bitmap, 0.0, 1.0)
    return np.power(clamped, gamma)
```

Values are clamped before the power operation to avoid NaN from negative inputs.

---

### `sharpen(bitmap, strength=1.0)`

Enhances edges using a Laplacian kernel (unsharp mask).

```python
from dapple.preprocess import sharpen

sharpened = sharpen(bitmap, strength=1.0)
```

| Parameter  | Type    | Default | Description                                  |
|------------|---------|---------|----------------------------------------------|
| `strength` | `float` | `1.0`   | Sharpening intensity. 0 = none, 1 = normal, > 1 = aggressive |

**When to use:** Before any character-based renderer. Terminal rendering discards fine spatial detail due to the large cell size. Sharpening before rendering restores edge contrast that would otherwise be averaged away.

**How it works:**

```python
def sharpen(bitmap, strength=1.0):
    # Pad with edge values
    padded = np.pad(bitmap, 1, mode="edge")

    # 3x3 Laplacian kernel (center minus neighbors)
    laplacian = (
        4 * padded[1:-1, 1:-1]
        - padded[:-2, 1:-1]   # top
        - padded[2:, 1:-1]    # bottom
        - padded[1:-1, :-2]   # left
        - padded[1:-1, 2:]    # right
    )

    sharpened = bitmap + strength * laplacian
    return np.clip(sharpened, 0.0, 1.0)
```

Output is clamped to 0.0--1.0 to prevent overflow artifacts.

---

### `threshold(bitmap, level=0.5)`

Simple binary threshold. Every pixel above `level` becomes 1.0; everything else becomes 0.0.

```python
from dapple.preprocess import threshold

binary = threshold(bitmap, level=0.5)
```

| Parameter | Type    | Default | Description          |
|-----------|---------|---------|----------------------|
| `level`   | `float` | `0.5`   | Cutoff value         |

**When to use:** When you want a hard binary image without the error diffusion of dithering. Useful for diagrams, text, or images that are already mostly black and white.

---

### `resize(bitmap, new_height, new_width)`

Resizes the bitmap using bilinear interpolation. This is a basic numpy-only implementation. For higher quality resizing, use the PIL adapter which uses Lanczos resampling.

```python
from dapple.preprocess import resize

small = resize(bitmap, new_height=40, new_width=80)
```

| Parameter    | Type  | Description        |
|--------------|-------|--------------------|
| `new_height` | `int` | Target height      |
| `new_width`  | `int` | Target width       |

---

### `invert(bitmap)`

Flips all values: 0.0 becomes 1.0, 1.0 becomes 0.0.

```python
from dapple.preprocess import invert

inverted = invert(bitmap)
```

**When to use:** When content is light-on-dark (e.g., screenshots of dark-themed terminals) and the renderer expects dark-on-light, or vice versa.

---

### `crop(bitmap, x, y, width, height)`

Extracts a rectangular region from the bitmap.

```python
from dapple.preprocess import crop

region = crop(bitmap, x=10, y=20, width=100, height=50)
```

| Parameter | Type  | Description                       |
|-----------|-------|-----------------------------------|
| `x`       | `int` | Left edge (pixels from left)      |
| `y`       | `int` | Top edge (pixels from top)        |
| `width`   | `int` | Width of crop region              |
| `height`  | `int` | Height of crop region             |

Raises `ValueError` if the crop region extends beyond bitmap bounds or has zero/negative dimensions.

---

### `flip(bitmap, direction)`

Flips the bitmap horizontally or vertically.

```python
from dapple.preprocess import flip

flipped_h = flip(bitmap, "h")  # left-right mirror
flipped_v = flip(bitmap, "v")  # top-bottom mirror
```

| Parameter   | Type  | Description                        |
|-------------|-------|------------------------------------|
| `direction` | `str` | `"h"` for horizontal, `"v"` for vertical |

---

### `rotate(bitmap, degrees)`

Rotates the bitmap counter-clockwise. For 90/180/270 degrees, uses efficient numpy rotation. For arbitrary angles, requires scipy.

```python
from dapple.preprocess import rotate

rotated = rotate(bitmap, 90)    # 90 degrees CCW, pure numpy
rotated = rotate(bitmap, 45)    # arbitrary angle, requires scipy
```

| Parameter | Type    | Description                    |
|-----------|---------|--------------------------------|
| `degrees` | `float` | Rotation angle (counter-clockwise) |

For non-right-angle rotations, the output is resized to contain the rotated content, with zero-padding in the corners.

---

## Recipes

### Photographs

Photographs have continuous tones. The key is to maximize contrast, then use dithering to convert the continuous values to the dot density that braille encodes.

```python
from dapple.preprocess import auto_contrast, floyd_steinberg

bitmap = auto_contrast(bitmap)
bitmap = floyd_steinberg(bitmap)
canvas.out(braille)
```

For color output, skip dithering and use quadrants or sextants, which handle continuous tones natively:

```python
bitmap = auto_contrast(bitmap)
canvas.out(quadrants)
```

### Charts and diagrams

Charts have sharp edges and large solid regions. Sharpening preserves the edges; dithering is unnecessary.

```python
from dapple.preprocess import auto_contrast, sharpen

bitmap = auto_contrast(bitmap)
bitmap = sharpen(bitmap, strength=0.5)
canvas.out(braille)
```

### Dark images

Images that are mostly dark lose all detail when thresholded. Gamma correction pulls up shadow detail before contrast stretching.

```python
from dapple.preprocess import gamma_correct, auto_contrast, floyd_steinberg

bitmap = gamma_correct(bitmap, gamma=0.5)   # brighten shadows
bitmap = auto_contrast(bitmap)
bitmap = floyd_steinberg(bitmap)
canvas.out(braille)
```

### Light content on dark terminal

When the source image has a white background (scanned documents, screenshots of light-themed apps) and the terminal background is dark, invert before processing.

```python
from dapple.preprocess import invert, auto_contrast

bitmap = invert(bitmap)
bitmap = auto_contrast(bitmap)
canvas.out(braille)
```

### Maximum quality braille

The full pipeline for the best possible braille output from a photographic image:

```python
from dapple.preprocess import gamma_correct, auto_contrast, sharpen, floyd_steinberg

bitmap = gamma_correct(bitmap, gamma=0.6)    # lift shadows
bitmap = auto_contrast(bitmap)                # fill dynamic range
bitmap = sharpen(bitmap, strength=0.5)        # restore edges
bitmap = floyd_steinberg(bitmap)              # dither for dot density
canvas.out(braille)
```

Order matters. Gamma and contrast first (fix the tonal range), then sharpen (restore edges at the target resolution), then dither (convert to binary for braille).

### Pipeline summary

| Use case              | Pipeline                                          | Renderer    |
|-----------------------|---------------------------------------------------|-------------|
| Photo, monochrome     | auto_contrast + floyd_steinberg                   | braille     |
| Photo, color          | auto_contrast                                     | quadrants   |
| Chart / diagram       | auto_contrast + sharpen                           | braille     |
| Dark image            | gamma_correct + auto_contrast + floyd_steinberg   | braille     |
| Light on dark term    | invert + auto_contrast                            | braille     |
| Maximum quality       | gamma + contrast + sharpen + dither               | braille     |
| True pixel output     | (none needed)                                     | sixel/kitty |

> **Note:** Sixel and kitty renderers handle raw pixel data directly. Preprocessing is most beneficial for character-based renderers (braille, quadrants, sextants, ascii, fingerprint) where the encoding discards spatial information.

## CLI Equivalents

The dapple extras (imgcat, funcat, etc.) expose preprocessing as command-line flags. The mapping between API calls and CLI options depends on the specific tool. For example, in imgcat:

```python
# API
bitmap = auto_contrast(bitmap)
bitmap = floyd_steinberg(bitmap)
canvas.out(braille)
```

is equivalent to:

```bash
# CLI
imgcat --renderer braille --contrast --dither photo.jpg
```

See each tool's `--help` for the full list of available preprocessing flags.
