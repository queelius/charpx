# Character Encodings

This guide explains how each of dapple's seven renderers encodes bitmap pixels into terminal output. Understanding the encoding helps you choose the right renderer and tune its parameters.

## Braille Encoding

**Range:** U+2800--U+28FF (256 codepoints)
**Cell:** 2 wide x 4 tall = 8 binary pixels per character

Unicode braille characters encode a 2x4 dot grid directly into the codepoint. The base character is U+2800 (blank braille pattern). Each of the 8 dots corresponds to one bit:

```
Position:       Bit index:
col 0  col 1   col 0  col 1
 [0]    [3]     bit 0   bit 3
 [1]    [4]     bit 1   bit 4
 [2]    [5]     bit 2   bit 5
 [6]    [7]     bit 6   bit 7
```

The codepoint is `U+2800 + (sum of set bits)`. For example, dots 1 and 4 set bits 0 and 3, giving `U+2800 + 1 + 8 = U+2809`.

### The algorithm

```python
BRAILLE_BASE = 0x2800

# Mapping: (row, col) -> bit index
DOT_MAP = [
    (0, 0, 0), (1, 0, 1), (2, 0, 2), (3, 0, 6),
    (0, 1, 3), (1, 1, 4), (2, 1, 5), (3, 1, 7),
]

def region_to_braille(region_4x2, threshold=0.5):
    """Convert a 4x2 pixel region to a braille character."""
    code = 0
    for row, col, bit in DOT_MAP:
        if region_4x2[row, col] > threshold:
            code |= 1 << bit
    return chr(BRAILLE_BASE + code)
```

Each pixel is a binary decision: above threshold = dot on, below = dot off. This means braille output is inherently binary. To encode grayscale information, use preprocessing (dithering) before rendering, or use braille's color modes to tint each character.

### Color modes

- **`"none"`**: plain Unicode characters, no escape codes. Works everywhere.
- **`"grayscale"`**: 256-color ANSI foreground (codes 232--255, 24 gray levels). The average brightness of the 2x4 region sets the gray level.
- **`"truecolor"`**: 24-bit ANSI foreground. If RGB colors are available, the average color of the region is used. Otherwise, falls back to gray.

---

## Quadrants and Sextants

### The two-color problem

Block characters split each cell into sub-regions. A 2x2 cell has 4 sub-pixels, giving 2^4 = 16 possible patterns. A 2x3 cell has 6 sub-pixels, giving 2^3 = 64 possible patterns. But each character position can display at most two colors: foreground and background.

The renderer must decide which pixels are "foreground" and which are "background," then pick the two colors that best represent the region.

### Quadrants: 16 patterns

The 16 quadrant block characters use bit positions TL=8, TR=4, BL=2, BR=1:

```
Pattern 0b0000: " "  (empty)       Pattern 0b1000: "▘" (top-left)
Pattern 0b0001: "▗"  (bottom-right) Pattern 0b1001: "▚" (diagonal)
Pattern 0b0010: "▖"  (bottom-left)  Pattern 0b1010: "▌" (left half)
Pattern 0b0011: "▄"  (lower half)   Pattern 0b1011: "▙" (missing TR)
Pattern 0b0100: "▝"  (top-right)    Pattern 0b1100: "▀" (upper half)
Pattern 0b0101: "▐"  (right half)   Pattern 0b1101: "▜" (missing BL)
Pattern 0b0110: "▞"  (diagonal)     Pattern 0b1110: "▛" (missing BR)
Pattern 0b0111: "▟"  (missing TL)   Pattern 0b1111: "█" (full block)
```

### Sextants: 64 patterns

Sextant characters (U+1FB00--U+1FB3B) encode a 2x3 grid. Three special patterns use existing block characters:

| Pattern | Character | Description |
|---------|-----------|-------------|
| 0 (empty) | ` ` (space) | All cells off |
| 21 (left half) | `▌` (U+258C) | Cells 0, 2, 4 |
| 42 (right half) | `▐` (U+2590) | Cells 1, 3, 5 |
| 63 (full) | `█` (U+2588) | All cells on |

The remaining 60 patterns are assigned to U+1FB00 through U+1FB3B, skipping the two special values.

### Foreground/background color selection

The algorithm for both quadrants and sextants is the same:

```python
def render_block(block_pixels, block_colors=None):
    """Render a single 2x2 or 2x3 block."""
    # 1. Compute per-pixel luminance
    if block_colors is not None:
        lum = 0.299 * R + 0.587 * G + 0.114 * B
    else:
        lum = block_pixels  # grayscale bitmap IS the luminance

    # 2. Find brightest and darkest pixels
    fg_lum = lum.max()
    bg_lum = lum.min()

    # 3. Threshold at the midpoint
    threshold = (fg_lum + bg_lum) / 2

    # 4. Build bit pattern
    pattern = 0
    for each pixel:
        if lum[pixel] > threshold:
            pattern |= bit_weight[pixel]

    # 5. Select foreground color from brightest pixel,
    #    background color from darkest pixel
    fg_color = color_of_brightest_pixel
    bg_color = color_of_darkest_pixel

    # 6. Emit ANSI: set fg, set bg, write character
    return f"{fg_escape}{bg_escape}{CHAR_TABLE[pattern]}"
```

### Vectorized rendering

In practice, dapple does not loop pixel-by-pixel. The bitmap is reshaped using numpy operations:

```python
# Reshape (H, W) into (rows, cols, pixels_per_cell)
# For quadrants: reshape to (rows, 2, cols, 2) then transpose
block_data = bitmap[:rows*2, :cols*2].reshape(rows, 2, cols, 2)
block_data = block_data.transpose(0, 2, 1, 3).reshape(rows, cols, 4)

# Vectorized max/min/threshold across all blocks simultaneously
fg = block_data.max(axis=2)
bg = block_data.min(axis=2)
thresh = (fg + bg) / 2
patterns = ((block_data > thresh[..., None]) * BIT_WEIGHTS).sum(axis=2)
```

This processes the entire image in a handful of numpy calls rather than a Python loop per pixel.

---

## ASCII

**Cell:** 1 wide x 2 tall = 2 pixels per character
**Character ramp:** ` .:-=+*#%@` (10 levels, dark to bright)

The simplest encoding. Two vertically adjacent pixels are averaged (for aspect ratio correction), and the resulting brightness is mapped to a character from the ramp.

```python
CHARSET = " .:-=+*#%@"

def brightness_to_char(brightness, charset=CHARSET):
    """Map a 0.0-1.0 brightness to a character."""
    index = int(brightness * (len(charset) - 0.001))
    return charset[index]
```

The 1x2 cell compensates for terminal characters being roughly twice as tall as they are wide. Without this, images would appear vertically stretched.

ASCII output uses no escape codes and works on any terminal, any font, any connection. This makes it the universal fallback.

### Available ramps

| Name            | Characters                                                | Levels |
|-----------------|-----------------------------------------------------------|--------|
| `CHARSET_STANDARD` | ` .:-=+*#%@`                                          | 10     |
| `CHARSET_DETAILED` | `` .'`^",:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$`` | 70     |
| `CHARSET_BLOCKS`   | ` ░▒▓█`                                                | 5      |
| `CHARSET_SIMPLE`   | ` .oO@`                                                | 5      |

More levels in the ramp means finer brightness gradations. The detailed ramp produces smoother gradients but requires a font where all 70 characters have distinguishable visual density.

---

## Sixel

**Protocol:** DEC VT340 (1984)
**Cell:** 1x1 (true pixel output)
**Color:** palette-based, up to 256 colors

Sixel encodes bitmaps as escape sequences that the terminal interprets as pixel data. The name comes from "six elements" -- each character encodes a column of 6 vertical pixels.

### Encoding

A sixel character is in the range 0x3F (`?`) to 0x7E (`~`). The character value minus 0x3F gives a 6-bit pattern where bit 0 is the top pixel and bit 5 is the bottom:

```
Character = chr(0x3F + pattern)

pattern bits:
  bit 0 = top pixel
  bit 1
  bit 2
  bit 3
  bit 4
  bit 5 = bottom pixel
```

### Per-color painting model

Sixel does not encode pixels left-to-right like a framebuffer. Instead, for each 6-pixel-tall band:

1. Select a color (`#n`).
2. Paint all columns that use that color in this band.
3. Carriage return (`$`) to go back to the start of the band.
4. Select the next color and repeat.
5. Line feed (`-`) to advance to the next 6-pixel band.

This per-color painting model means each band is painted multiple times, once per active color.

### Run-length encoding

Repeated sixel characters can be compressed:

```
!<count><character>

Example: !20?  means 20 repetitions of '?' (all blank column)
```

dapple uses RLE when a run exceeds 3 characters.

### Palette definition

Colors are defined at the start of the sequence:

```
#<index>;2;<r>;<g>;<b>

where r, g, b are percentages (0-100).
```

### Full sequence structure

```
ESC P q                          <- DCS start
#0;2;0;0;0                      <- define color 0 as black
#1;2;100;0;0                    <- define color 1 as red
...
#0 ?~?~?~ $                     <- paint color 0 in band, carriage return
#1 ~~~??? $                     <- paint color 1 in band, carriage return
-                                <- next 6-pixel band
...
ESC \                            <- string terminator
```

### Quantization

dapple uses uniform color quantization: each RGB channel is divided into `cbrt(max_colors)` levels, producing a uniform color cube. For grayscale, up to 64 gray levels are used.

---

## Kitty

**Protocol:** Kitty graphics protocol (modern)
**Cell:** 1x1 (true pixel output)
**Color:** 24-bit RGB (or 8-bit grayscale via PNG)

The Kitty protocol transmits image data as base64-encoded payloads inside escape sequences. It supports PNG, raw RGB, and raw RGBA formats.

### Escape sequence structure

```
ESC _G <key>=<value>,... ; <base64 data> ESC \
```

Key parameters:

| Key | Value | Meaning                       |
|-----|-------|-------------------------------|
| `a` | `T`   | Action: transmit and display  |
| `f` | `100` | Format: PNG                   |
| `f` | `24`  | Format: raw RGB               |
| `f` | `32`  | Format: raw RGBA              |
| `o` | `z`   | Compression: zlib             |
| `s` | `W`   | Source width (for raw formats) |
| `v` | `H`   | Source height (for raw formats)|
| `c` | `N`   | Display width in columns      |
| `r` | `N`   | Display height in rows        |
| `m` | `1`   | More data chunks follow       |
| `m` | `0`   | Last (or only) chunk          |

### Chunking

Base64 data is split into chunks of up to 4096 bytes. The first chunk carries all parameters; continuation chunks only carry `m=<0|1>`:

```python
# First chunk
ESC_G a=T,f=100,m=1; <base64 chunk 1> ESC \
# Continuation
ESC_G m=1; <base64 chunk 2> ESC \
# Final chunk
ESC_G m=0; <base64 chunk N> ESC \
```

### PNG vs raw formats

- **PNG** (`f=100`): compressed, smallest payload. dapple uses PIL if available, otherwise a minimal built-in PNG encoder (zlib-compressed, no filtering).
- **RGB** (`f=24`): uncompressed pixel data, `W * H * 3` bytes. Can be zlib-compressed with `o=z`.
- **RGBA** (`f=32`): same as RGB but with alpha channel, `W * H * 4` bytes.

PNG is the default because it produces the smallest output and is universally supported by Kitty-compatible terminals.

---

## Fingerprint

**Cell:** configurable (default 8x16)
**Method:** glyph correlation matching
**Color:** none (grayscale only)

Fingerprint is an experimental renderer that finds the Unicode character whose rendered appearance most closely matches each region of the input bitmap.

### The algorithm

```python
def find_best_glyph(input_region, glyph_bitmaps, glyphs):
    """Find the glyph that best matches the input region."""
    # input_region: flattened (cell_width * cell_height,) vector
    # glyph_bitmaps: (N, cell_width * cell_height) array

    # Compute MSE between input and each glyph
    diff = input_region - glyph_bitmaps  # broadcasts to (N, pixels)
    distances = (diff ** 2).mean(axis=1)  # (N,) MSE per glyph

    # Pick the closest glyph
    best_idx = distances.argmin()
    return glyphs[best_idx]
```

### Glyph preparation

On first use, each candidate character is rendered to a small bitmap using PIL's `ImageDraw.text`. The glyph bitmap has white background with black text, inverted so ink = 1.0 and background = 0.0. All glyph bitmaps are stacked into a single numpy array for vectorized distance computation.

The glyph cache is keyed by `(glyph_set, cell_width, cell_height, font_path)` and persists for the process lifetime.

### Font dependence

The output is determined by how the font renders each character at the given cell size. Different fonts produce different "best match" selections for the same input. A monospace font with clean, distinct glyph shapes tends to produce better results than a proportional font.

dapple tries to load DejaVu Sans Mono or Consolas, falling back to PIL's built-in bitmap font.

### Distance metrics

- **MSE** (mean squared error): `mean((input - glyph)^2)`. Penalizes large differences heavily. Default.
- **MAE** (mean absolute error): `mean(|input - glyph|)`. More tolerant of outliers.

### Vectorized matching

Rather than looping over each cell, dapple extracts all cells at once via numpy reshape/transpose, then computes all distances in a single broadcast operation:

```python
# regions: (R, P) -- R cells, P pixels each
# glyph_bitmaps: (G, P) -- G glyphs, P pixels each
diff = regions[:, None, :] - glyph_bitmaps[None, :, :]  # (R, G, P)
distances = (diff ** 2).mean(axis=2)                      # (R, G)
best_indices = distances.argmin(axis=1)                    # (R,)
```

This makes fingerprint rendering practical even for large images and extended glyph sets.
