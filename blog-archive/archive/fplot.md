# Unix Composition for Terminal Graphics

## The Power of Pipes

Unix philosophy: small tools that do one thing well, composed via pipes.

```bash
cat file.txt | grep error | sort | uniq -c
```

Each tool transforms a text stream. The pipe is the universal interface. This works because text is the lowest common denominator—every tool speaks it.

Terminal graphics have been missing this composability. You get a library that renders braille, another for sixel, another for block characters. Each is a dead end: no piping, no composition.

## Text Streams as Universal Interface

The Unix insight: if your output is text, it can be piped. Terminals display text. Therefore terminal graphics *can* be text.

But raw terminal art—braille characters, ANSI escape codes—isn't easily composable. If I render a graph to braille, I can't easily add another layer on top. The text is the final form.

The solution: JSON as an intermediate format. Encode image data (base64) plus metadata. Pipe it. The final stage renders to your chosen format.

## Terminal as Canvas

When output IS visualization, the terminal becomes a canvas:

```bash
$ fplot "sin(x)"
x: [-6.28, 6.28]  y: [-1.00, 1.00]
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⣀⠔⠊⠉⠉⠉⠉⠢⢄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⠔⠊⠉⠉⠉⠑⠢⢄⠀
⠀⡠⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡠⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⢄
⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠢⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠔⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠑⢄
```

No display server. No browser. No IDE. Just text, rendered instantly where you're already working.

## fplot: Composing Functions

fplot plots mathematical functions. The `-j` flag outputs JSON for chaining:

```bash
# Single function
fplot "sin(x)"

# Multiple functions, different colors
fplot "sin(x)" -j | fplot "cos(x)" --color red -j | fplot "x/3" -l
```

Each invocation reads the previous state from stdin, adds its function, and either:
- Outputs JSON for the next stage (`-j`)
- Renders to terminal (default, or specify `-r`)

The JSON contains all accumulated functions, axis ranges, and styling. The final stage combines everything into one plot.

```bash
# Parametric curves compose too
fplot -p "cos(t),sin(t)" -j | fplot -p "2*cos(t),2*sin(t)" -l
```

## chop: Composing Image Operations

chop applies the same pattern to image manipulation:

```bash
# Load, process, render
chop load photo.jpg -j | chop resize 50% -j | chop dither -r braille

# Multiple operations
chop load photo.jpg -j | chop crop 10% 10% 80% 80% -j | chop rotate 45 -j | chop contrast -o final.png
```

Operations available:

| Operation | Example |
|-----------|---------|
| `load` | `chop load photo.jpg -j` |
| `resize` | `chop resize 50%` or `chop resize 800x600` |
| `crop` | `chop crop 100 100 500 400` |
| `rotate` | `chop rotate 90` |
| `flip` | `chop flip h` |
| `dither` | `chop dither --threshold 0.5` |
| `invert` | `chop invert` |
| `sharpen` | `chop sharpen --strength 1.5` |
| `contrast` | `chop contrast` |
| `gamma` | `chop gamma 2.2` |
| `threshold` | `chop threshold 0.5` |

Each operation reads JSON from stdin, applies the transform, outputs JSON. Chain as many as needed.

## The `-o` Escape Hatch

Sometimes you need a real file. Both tools support `-o`:

```bash
# fplot to PNG (via dapple's sixel, captured)
fplot "sin(x)" -r sixel -o plot.png

# chop save processed image
chop load input.jpg -j | chop resize 50% -j | chop sharpen -o output.jpg
```

The pipe-based workflow and file-based workflow are complementary. Use pipes for exploration, files for persistence.

## ANSI as First-Class Format

Terminal art isn't just output—it can be input too.

dapple includes an ANSI adapter that parses terminal art back into bitmaps:

```python
from dapple.adapters.ansi import from_ansi

# Parse braille art
canvas = from_ansi("⠿⠿⠿⠿⠿")

# Auto-detects format (braille, quadrants, sextants, ASCII)
canvas = from_ansi(terminal_output)

# Force specific format
canvas = from_ansi(colored_blocks, format="quadrants")
```

This enables roundtripping: render to terminal, capture output, parse back, render differently.

The parser handles:
- **Braille** (U+2800-U+28FF): Reverses the 8-bit dot encoding
- **Quadrants** (▀▄▌▐▖▗▘▝▚▞▙▛▜▟█): 16 patterns to 2x2 bitmap
- **Sextants** (U+1FB00-U+1FB3B): 64 patterns to 2x3 bitmap
- **ASCII**: Character density to grayscale

ANSI color codes (24-bit, 256-color, basic 16) are parsed and preserved.

## Renderers: Same Data, Different Output

Both fplot and chop use dapple's renderer system. Same image data, different terminal output:

```bash
# Braille - 2x4 dots per character, highest density
chop load photo.jpg -r braille

# Quadrants - 2x2 blocks with fg/bg colors
chop load photo.jpg -r quadrants

# Sextants - 2x3 blocks, more vertical resolution
chop load photo.jpg -r sextants

# ASCII - works everywhere
chop load photo.jpg -r ascii

# Sixel - true pixels (xterm, foot, mlterm)
chop load photo.jpg -r sixel

# Kitty - true pixels (kitty, wezterm)
chop load photo.jpg -r kitty
```

The choice depends on your terminal and use case. Braille for universal compatibility and density. Sixel/Kitty for pixel-perfect output. ASCII when you need guaranteed portability.

## Philosophy

These tools embody Unix composition:

1. **Small, focused operations** - each does one thing
2. **Text-based interface** - JSON for structured data
3. **Pipes for composition** - build complex workflows from simple parts
4. **Escape to files when needed** - but prefer streaming

The terminal is not a second-class citizen for visualization. It's a capable canvas with its own aesthetic, and these tools let you work with it the Unix way.

## Installation

```bash
pip install fplot chop
```

Both are built on [dapple](./dapple.md), the unified terminal graphics library.

---

*Quick examples to try:*

```bash
# Explore a function
fplot "sin(x)*exp(-x/10)" --xmin 0 --xmax 15

# Process an image
chop load photo.jpg -j | chop resize 800x600 -j | chop dither -r braille

# Multiple functions with legend
fplot "sin(x)" -j | fplot "cos(x)" --color red -l

# Parametric heart
fplot -p "16*sin(t)**3,13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t)"
```
