# Preprocessing: The Invisible Art

You ran `imgcat photo.jpg -r braille` and got a rectangle of white dots. The renderer is not broken. Your image needs preprocessing.

The gap between "raw bitmap rendered to braille" and "good-looking braille output" is almost entirely preprocessing. The renderer itself is a fixed encoding — pixels above a threshold become dots, pixels below don't. The quality comes from what happens before that threshold is applied: contrast stretching, dithering, gamma correction, sharpening. These transforms are invisible in the output — you see good braille, not the preprocessing steps — but they determine whether the output is legible or garbage.

## Why Raw Bitmaps Look Terrible

Most photographs, naively thresholded at 0.5, produce nearly all-white or all-black output. Three problems conspire:

**Wrong dynamic range.** A typical JPEG photograph might use pixel values from 0.15 to 0.85. Thresholding at 0.5 works, but barely — the effective contrast between "just above 0.5" and "just below 0.5" is minimal. A dark photograph (values 0.1 to 0.5) becomes entirely black. A bright photograph (values 0.5 to 0.95) becomes entirely white. The threshold falls outside the image's actual dynamic range.

**Wrong gamma.** Image files store values in gamma-corrected space (typically gamma 2.2). Human perception is nonlinear — we're more sensitive to differences in dark tones than light tones — and gamma encoding allocates more precision where perception is most sensitive. But threshold-based rendering assumes linear values: 0.5 should mean "half brightness." In gamma-encoded space, 0.5 corresponds to about 0.22 in linear light. Thresholding a gamma-encoded image at 0.5 produces output that's too bright.

**Too much spatial detail.** A 4000x3000 photograph rendered at terminal resolution (maybe 160x80 braille dots) is downsampled 25:1 in each dimension. Naive downsampling aliases: fine textures become noise, thin lines disappear, and the braille dots flicker between on and off at random-seeming boundaries. The image needs spatial filtering — blur or averaging — before downsampling to prevent aliasing.

Each problem has a solution in dapple's preprocessing toolkit. The art is knowing which solutions to combine for which content.

## The Toolkit

All preprocessing functions in `dapple.preprocess` follow the same signature: take a 2D numpy array (values 0.0-1.0), return a 2D numpy array (values 0.0-1.0). They compose by sequencing:

```python
from dapple.preprocess import auto_contrast, floyd_steinberg, gamma_correct, sharpen

bitmap = auto_contrast(bitmap)
bitmap = gamma_correct(bitmap, gamma=0.5)
bitmap = sharpen(bitmap, strength=1.0)
bitmap = floyd_steinberg(bitmap)
```

### auto_contrast

```python
def auto_contrast(bitmap):
    min_val = bitmap.min()
    max_val = bitmap.max()
    return (bitmap - min_val) / (max_val - min_val)
```

Histogram stretch. The darkest pixel becomes 0.0, the brightest becomes 1.0, everything else scales linearly. This fixes the dynamic range problem: regardless of the original exposure, the threshold now bisects the image's actual tonal range.

auto_contrast is the single most impactful preprocessing step. For most images, adding `--contrast` to an imgcat command transforms the output from "barely visible" to "clearly legible."

### floyd_steinberg

Floyd-Steinberg dithering is error diffusion. When a pixel is thresholded (rounded to 0 or 1), the rounding error is distributed to neighboring pixels that haven't been processed yet:

```
     X   7/16
3/16 5/16 1/16
```

The pixel at X is quantized. 7/16 of the error goes right, 5/16 goes below, 3/16 goes below-left, 1/16 goes below-right.

The effect: areas of intermediate brightness produce a mix of on and off dots whose spatial density encodes the original brightness. A region at 0.75 brightness produces roughly 75% on-dots and 25% off-dots, distributed in a pattern that the eye reads as gray.

This is the essential technique for braille rendering. Without dithering, braille is binary — on or off, black or white. With dithering, braille can express continuous tones through dot density. The improvement is dramatic: photographs that were unrecognizable as binary thresholds become recognizable portraits after dithering.

The cost: Floyd-Steinberg is inherently sequential (each pixel's error affects its neighbors), so it runs as a Python double loop. This makes it slower than the vectorized preprocessing steps. For interactive use, the latency is acceptable. For batch processing, consider the tradeoff.

### gamma_correct

```python
def gamma_correct(bitmap, gamma=2.2):
    return np.power(np.clip(bitmap, 0.0, 1.0), gamma)
```

Gamma correction adjusts the brightness curve. A gamma value of 2.2 is the standard encoding gamma — applying it linearizes the values. But for terminal graphics, you often want the opposite: gamma < 1 brightens the image, which is useful for dark photographs that look muddy after thresholding.

The rule of thumb: if the output is too dark, try `gamma_correct(bitmap, 0.5)`. If it's too bright, try `gamma_correct(bitmap, 2.0)`. The value is exponential — small changes have visible effects.

### sharpen

```python
def sharpen(bitmap, strength=1.0):
    laplacian = 4 * center - top - bottom - left - right
    return bitmap + strength * laplacian
```

Unsharp mask sharpening via a 3x3 Laplacian kernel. The Laplacian detects edges (regions where brightness changes rapidly), and adding it back to the original image amplifies those edges.

At terminal resolution, sharpening makes a significant difference. Downsampling smooths edges, and braille dots are binary — a slightly soft edge becomes invisible. Sharpening restores edge contrast so that structural boundaries survive the threshold.

Strength controls aggressiveness: 0.0 = no effect, 1.0 = standard sharpening, values above 1.0 create halos around edges (sometimes desirable for high-contrast output, usually not).

### threshold

```python
def threshold(bitmap, level=0.5):
    return (bitmap > level).astype(np.float32)
```

Manual binary threshold. Everything above the level becomes 1.0, everything below becomes 0.0. Use this when you want explicit control over the cutoff — for instance, converting a scanned document where the background is known to be below a specific brightness.

Most of the time, you'll use auto_contrast + dithering instead of a manual threshold. But for line art, diagrams, and other inherently binary content, a clean threshold produces sharper output than dithering.

### resize

Bilinear interpolation resizing. This is dapple's built-in resize — it works without PIL, using only numpy. For higher-quality resizing (Lanczos, bicubic), use the PIL adapter.

The main use: reducing image dimensions before rendering, so the renderer doesn't have to process a massive bitmap only to discard most of the detail. Resizing to approximately terminal resolution before rendering is faster and can produce better results (the resize itself acts as an anti-aliasing filter).

### invert

```python
def invert(bitmap):
    return 1.0 - bitmap
```

Flip brightness. Black becomes white, white becomes black. Essential for dark-background terminals: if your image is dark content on light background (like a scanned document), inverting it produces light dots on dark background, matching the terminal's color scheme.

## Recipes

The right preprocessing pipeline depends on the content. Here are the combinations that work well in practice.

### Photographs

```bash
imgcat photo.jpg --contrast --dither -r braille
```

```python
bitmap = auto_contrast(bitmap)
bitmap = floyd_steinberg(bitmap)
canvas = Canvas(bitmap)
canvas.out(braille)
```

auto_contrast stretches the histogram; dithering encodes continuous tones as dot density patterns. This combination handles the vast majority of photographs. For quadrant or sextant output, skip the dithering — those renderers use their own color-based tone reproduction.

### Charts and diagrams

```bash
imgcat diagram.png --sharpen --contrast -r braille
```

```python
bitmap = auto_contrast(bitmap)
bitmap = sharpen(bitmap, strength=1.5)
canvas = Canvas(bitmap)
canvas.out(braille)
```

Charts have clean edges and solid fills. Sharpening preserves edge detail at terminal resolution. Dithering is usually unnecessary — chart regions are either clearly bright or clearly dark. Higher sharpening strength (1.5) is appropriate because chart edges should be crisp.

### Dark images

```bash
imgcat night.jpg --gamma 0.5 --contrast --dither -r braille
```

```python
bitmap = gamma_correct(bitmap, gamma=0.5)
bitmap = auto_contrast(bitmap)
bitmap = floyd_steinberg(bitmap)
canvas = Canvas(bitmap)
canvas.out(braille)
```

Gamma correction first to brighten, then auto_contrast to stretch, then dithering. The order matters: gamma before contrast expands the dark tones before the histogram stretch, preserving shadow detail.

### Dark terminal with light content

```bash
imgcat document.png --invert --contrast -r braille
```

```python
bitmap = invert(bitmap)
bitmap = auto_contrast(bitmap)
canvas = Canvas(bitmap)
canvas.out(braille)
```

A scanned document (dark text on white background) renders as a white rectangle with dark spots — unreadable on a dark terminal. Inverting first produces bright dots on the terminal's dark background. Then auto_contrast maximizes the distinction.

### Maximum quality (braille)

```python
bitmap = gamma_correct(bitmap, gamma=0.5)
bitmap = auto_contrast(bitmap)
bitmap = sharpen(bitmap, strength=0.5)
bitmap = floyd_steinberg(bitmap)
canvas = Canvas(bitmap)
canvas.out(braille)
```

All four steps: gamma to expand tones, contrast to normalize, light sharpening to preserve edges, dithering for tonal reproduction. This produces the best braille output for most photographic content. An AI assistant running `imgcat --gamma 0.5 --contrast --sharpen --dither photo.jpg` produces good output because it follows this recipe — the flags encode the knowledge, not the visual judgment.

---

*Further reading: [How Terminal Characters Encode Pixels](how-terminal-characters-encode-pixels.md) explains the rendering algorithms that follow preprocessing. [One Canvas, Seven Renderers](one-canvas-seven-renderers.md) covers the library architecture.*
