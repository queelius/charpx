# How Terminal Characters Encode Pixels

Every Unicode braille character is a number. Specifically, 0x2800 plus an 8-bit integer where each bit represents one dot in a 2x4 grid. That is the entire algorithm.

The elegance of terminal graphics lies in their encodings. Each renderer maps pixel data to terminal output through a different strategy — some encode directly into Unicode codepoints, some split colors between foreground and background ANSI attributes, some bypass character cells entirely and stream raw pixel data. Understanding these encodings reveals how each renderer trades resolution, color fidelity, and compatibility.

## Braille: 8 Bits Per Character

Unicode braille characters span U+2800 to U+28FF — 256 codepoints. Each represents a unique pattern in a 2-column by 4-row dot grid:

```
col 0  col 1
+----+----+
| b0 | b3 |   row 0
+----+----+
| b1 | b4 |   row 1
+----+----+
| b2 | b5 |   row 2
+----+----+
| b6 | b7 |   row 3
+----+----+
```

Bit 0 is the top-left dot. Bit 7 is the bottom-right. The mapping is not sequential left-to-right, top-to-bottom — it follows the traditional braille numbering used by the writing system since the 1820s, adapted to include a fourth row (bits 6 and 7) that was added in Unicode 3.0.

To render a 2x4 pixel region:

```python
def region_to_braille(region, threshold=0.5):
    DOT_MAP = [
        (0, 0, 0), (1, 0, 1), (2, 0, 2), (3, 0, 6),  # left column
        (0, 1, 3), (1, 1, 4), (2, 1, 5), (3, 1, 7),  # right column
    ]
    code = 0
    for row, col, bit in DOT_MAP:
        if region[row, col] > threshold:
            code |= 1 << bit
    return chr(0x2800 + code)
```

Each pixel is binary: above threshold, the dot is on; below, it's off. The entire algorithm is a threshold, a bit-pack, and a lookup into Unicode. No color tables, no palette quantization, no compression.

This gives braille the highest character density of any text-based renderer: 8 pseudo-pixels per character. A 160x80 pixel image becomes 80x20 characters — compact enough for a terminal, detailed enough to recognize structure, edges, and shapes.

Color is optional and orthogonal. ANSI foreground codes tint the braille character without affecting the dot pattern:

```python
# 24-bit truecolor foreground
f"\033[38;2;{r};{g};{b}m{braille_char}\033[0m"

# 256-color grayscale (codes 232-255)
f"\033[38;5;{232 + level}m{braille_char}\033[0m"
```

The dot pattern encodes structure. The color encodes tone. Both are independent — you can render the same dot pattern in different colors, or the same color with different patterns. dapple's braille renderer supports three modes: `"none"` (plain white dots), `"grayscale"` (24-level gray tinting), and `"truecolor"` (full 24-bit RGB tinting per character).

## Quadrants and Sextants: The Two-Color Problem

Quadrant block characters divide each character cell into 4 pixels (2x2). Sextant characters divide it into 6 pixels (2x3). Both face the same fundamental constraint: a terminal character cell has exactly two color slots — foreground and background.

Sixteen quadrant patterns cover all combinations of four binary cells:

```
 ▗ ▖ ▄ ▝ ▐ ▞ ▟ ▘ ▚ ▌ ▙ ▀ ▜ ▛ █
```

(Plus space for the empty pattern.) Each character is indexed by a 4-bit pattern: top-left=8, top-right=4, bottom-left=2, bottom-right=1.

Sextants extend this to 64 patterns across a 2x3 grid, using Unicode codepoints at U+1FB00-U+1FB3B plus standard block elements (space, ▌, ▐, █) for the special cases.

The rendering algorithm for both is:

1. **Reshape the bitmap into blocks** — (rows, cols, 4) for quadrants, (rows, cols, 6) for sextants — using numpy's reshape and transpose.

2. **Determine foreground and background** — the brightest pixel in each block becomes the foreground color, the darkest becomes the background.

3. **Threshold at the midpoint** — each pixel above (fg + bg) / 2 is "on" (foreground), below is "off" (background).

4. **Pack the pattern** — the on/off decisions become a bit pattern that indexes into the character table.

5. **Emit character with ANSI colors** — foreground color, background color, block character, reset.

```python
# Vectorized for all blocks at once (quadrants)
blocks = bitmap.reshape(rows, 2, cols, 2).transpose(0, 2, 1, 3).reshape(rows, cols, 4)
fg = blocks.max(axis=2)
bg = blocks.min(axis=2)
thresh = ((fg + bg) / 2)[:, :, np.newaxis]
patterns = ((blocks > thresh).astype(np.uint8) * [8, 4, 2, 1]).sum(axis=2)
```

The min/max split for color selection is a simplification. The optimal approach would use k-means clustering to find the two most representative colors in each block. But at terminal resolution — where each block is 4 or 6 pixels — the difference is negligible, and min/max is vectorizable across the entire image in a single numpy operation. Fast beats precise when the output is 2x2 pixels per character.

For RGB images, the algorithm extends naturally: luminance determines the threshold pattern, and the actual RGB values of the brightest and darkest pixels become the ANSI foreground and background colors. The pattern encodes shape; the colors encode tone.

The sextant renderer offers a meaningful advantage over quadrants for typical terminal use. Terminal character cells are roughly twice as tall as they are wide. A 2x3 pixel grid (sextants) better matches this aspect ratio than 2x2 (quadrants), giving sextants higher effective vertical resolution for the same number of character columns.

## Sixel: True Pixels, Vintage Protocol

Sixel is a bitmap graphics protocol created by DEC in 1984 for the VT240 and VT340 terminals. "Sixel" means "six elements" — each character in the protocol encodes a column of 6 vertical pixels.

The protocol is wrapped in a Device Control String:

```
ESC P q <palette> <sixel data> ESC \
```

Colors are defined as palette entries with RGB percentages:

```
#0;2;100;0;0    (color 0 = red, RGB percentages)
#1;2;0;100;0    (color 1 = green)
```

Pixel data uses characters from `?` (0x3F) to `~` (0x7E) — a range of 64 characters, each encoding a 6-bit vertical column. `?` means all 6 pixels off. `~` means all 6 pixels on. Bit 0 is the top pixel, bit 5 is the bottom.

Run-length encoding compresses repeated columns: `!10~` means "10 consecutive fully-lit columns."

The image is painted one color at a time: select a color, emit the sixel data for all pixels using that color, carriage return (`$`) to restart the row, select the next color, repeat. Line feed (`-`) advances to the next 6-pixel band.

This per-color painting model explains sixel's palette limitation. Each color requires a separate pass through each row. More colors means more passes, more data, more rendering time. Practical sixel output uses 64-256 colors, which means color quantization: the full RGB image is mapped to a limited palette before encoding.

dapple uses simple uniform quantization — dividing each channel into equal bins. More sophisticated quantization (median cut, octree) would produce better palettes, but the implementation stays simple and the output quality at typical terminal sizes is sufficient.

Sixel's advantage: true pixel output with no Unicode requirements. Its disadvantage: limited terminal support (xterm with `-ti vt340`, mlterm, foot, WezTerm) and palette-based color.

## Kitty: True Pixels, Modern Protocol

The Kitty graphics protocol takes the opposite approach from sixel. Instead of a custom encoding, it transmits images as base64-encoded PNG or raw RGB data:

```
ESC _ G a=T,f=100,m=0 ; <base64 PNG data> ESC \
```

Parameters specify format (`f=100` for PNG, `f=24` for RGB, `f=32` for RGBA), action (`a=T` for transmit and display), and chunking (`m=1` for "more data follows", `m=0` for last chunk).

The protocol handles arbitrarily large images by chunking the base64 data into 4096-byte pieces. The first chunk carries all parameters; continuation chunks carry only the `m` flag and data.

dapple prefers PNG format for kitty output: it tries PIL first for optimized compression, falling back to a minimal hand-built PNG encoder if PIL isn't available. The hand-built encoder writes valid PNG (signature, IHDR, IDAT with zlib compression, IEND) — functional but without PIL's optimization passes.

Kitty's advantages: 24-bit true color (no palette), PNG compression for reasonable data sizes, modern and well-documented protocol. Its disadvantages: limited terminal support (Kitty, WezTerm, Ghostty, partial Konsole).

Both sixel and kitty achieve 1:1 pixel output — the holy grail for terminal graphics. They differ in color model (palette vs true color), encoding (custom vs standard), and ecosystem (legacy DEC vs modern).

## Fingerprint: Glyph Correlation

The fingerprint renderer asks a different question from all the others. Instead of "how do I encode these pixels into a character?", it asks "which character looks most like these pixels?"

The algorithm:

1. **Pre-render candidate glyphs.** Using Pillow's font rendering, draw each character in the selected set (ASCII printable, block elements, braille patterns, or all combined) onto a small bitmap matching the cell size (default 8x16).

2. **Divide the input image into cell-sized regions.**

3. **For each region, compute the distance to every glyph bitmap** — mean squared error by default. The glyph with the lowest error is the best match.

```python
# Vectorized: all regions compared to all glyphs at once
# regions: (R, P) - R regions, P pixels each
# glyph_bitmaps: (G, P) - G glyphs, P pixels each
diff = regions[:, np.newaxis, :] - glyph_bitmaps[np.newaxis, :, :]
distances = (diff ** 2).mean(axis=2)  # (R, G) MSE matrix
best = distances.argmin(axis=1)       # (R,) best glyph per region
```

This is correlation-based matching, not encoding. The output depends on the font — different fonts produce different results for the same input image. The glyph cache is lazy-loaded and reused across renders, so the expensive font-rendering step happens only once.

Fingerprint produces a distinctive aesthetic. Where braille shows clean dots and quadrants show color blocks, fingerprint uses the visual texture of actual letter shapes to approximate the image. An `M` appears where the image has two vertical strokes. A `.` appears in empty areas. The output reads almost like text that happens to look like a picture — which is exactly what it is.

---

*Further reading: [One Canvas, Seven Renderers](one-canvas-seven-renderers.md) explains the library architecture that unifies these encodings. [Preprocessing: The Invisible Art](preprocessing.md) covers the transforms that prepare images for these renderers.*
