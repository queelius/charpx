# pixdot

Terminal-centric development has become mainstream. Claude Code runs in your terminal. AI assistants stream their work as text. Developers SSH into remote machines, pair with tmux, and live in the command line. In this world, there's a gap: we want to see graphics—images, charts, diagrams—without leaving the terminal.

pixdot fills this gap with the simplest possible approach: convert a bitmap to Unicode braille characters.

## Why Terminal Graphics?

Modern development increasingly happens in terminals:

- **AI-assisted coding** — Claude Code, Copilot CLI, and other assistants work through text
- **Remote workflows** — SSH sessions, tmux, containerized dev environments
- **Composability** — pipe-friendly tools that work together

We want to view images, render plots, preview diagrams—all without context-switching to a GUI. Unicode art lets us do this using the terminal's native medium: text.

## What is pixdot?

pixdot is a pure function: `bitmap → braille string`

```python
from pixdot import render
import numpy as np

bitmap = np.random.rand(32, 64).astype(np.float32)
print(render(bitmap))
```

Each braille character (U+2800–U+28FF) encodes a 2×4 dot pattern, giving you **8× the pseudo-pixel density** of regular characters. A 160×80 pixel image becomes 80×20 characters—compact enough to fit in a terminal, detailed enough to be recognizable.

The implementation is direct: threshold each pixel, map each 2×4 region to its corresponding braille codepoint. No magic, no dependencies beyond numpy. The entire core is ~50 lines.

## Installation

```bash
# Core library only (numpy)
pip install pixdot

# With CLI for image rendering (includes pillow)
pip install pixdot[cli]
```

## Usage

### Basic Rendering

```python
import numpy as np
from pixdot import render

# Create or load a bitmap (2D array, values 0.0-1.0)
bitmap = np.random.rand(64, 128).astype(np.float32)

# Render as braille
print(render(bitmap))

# With custom threshold
print(render(bitmap, threshold=0.4))

# Auto-detect threshold from bitmap mean
print(render(bitmap, threshold=None))
```

### Preprocessing for Better Results

pixdot includes preprocessing utilities for improved output:

```python
from pixdot import render, auto_contrast, floyd_steinberg
import numpy as np

# Load your bitmap (0.0-1.0 grayscale)
bitmap = ...  # your image data

# Apply auto-contrast to stretch histogram
bitmap = auto_contrast(bitmap)

# Apply Floyd-Steinberg dithering for grayscale illusion
bitmap = floyd_steinberg(bitmap)

# Render the preprocessed bitmap
print(render(bitmap))
```

**Floyd-Steinberg dithering** is the single most effective improvement for binary output. It distributes quantization error to create the illusion of grayscale through varying dot density.

### Loading images manually

```python
from PIL import Image
import numpy as np
from pixdot import render, auto_contrast, floyd_steinberg

# Load and convert to grayscale
img = Image.open("photo.jpg").convert("L")
img = img.resize((160, 80))  # 2x4 pixels per braille char

# Convert to numpy array (0.0-1.0)
bitmap = np.array(img, dtype=np.float32) / 255.0

# Optional: preprocess for better results
bitmap = auto_contrast(bitmap)
bitmap = floyd_steinberg(bitmap)

print(render(bitmap))
```

### CLI

With `pip install pixdot[cli]`, you get the `pixdot` command:

```bash
# Basic usage
pixdot photo.jpg

# With dithering (recommended for photos)
pixdot photo.jpg --dither

# All options
pixdot photo.jpg -w 120 --contrast --dither --invert

# Save to file
pixdot photo.jpg -o output.txt
```

Run `pixdot --help` for all options.

## As a Framebuffer

pixdot is designed as an output target. Higher-level libraries—vector drawing, plotting, game graphics—can render to a bitmap and call pixdot for display:

```python
import numpy as np
from pixdot import render

# Create a framebuffer
width, height = 160, 80
fb = np.zeros((height, width), dtype=np.float32)

# Draw a circle (your drawing code here)
cy, cx, r = height // 2, width // 2, 20
for y in range(height):
    for x in range(width):
        if (x - cx)**2 + (y - cy)**2 <= r**2:
            fb[y, x] = 1.0

# Output to terminal
print(render(fb))
```

This pattern—framebuffer abstraction with swappable renderers—enables building rich graphics libraries that can target terminals as easily as GUI windows.

## How it works

Each braille character (U+2800–U+28FF) encodes a 2×4 dot pattern:

```
+---+---+
| 1 | 4 |
+---+---+
| 2 | 5 |
+---+---+
| 3 | 6 |
+---+---+
| 7 | 8 |
+---+---+
```

The algorithm maps 2×4 pixel regions directly to braille codepoints, bypassing font rendering entirely. Each of the 8 dots corresponds to a bit in the codepoint offset (0–255), giving 256 possible patterns.

## API Reference

### `render(bitmap, threshold=0.5)`

Rasterize a bitmap to Unicode braille.

- **bitmap**: 2D numpy array (H×W), values 0.0-1.0 (brightness)
- **threshold**: Float (0.0-1.0) or None for auto-detect from bitmap mean
- **Returns**: Multi-line string of braille characters

### `auto_contrast(bitmap)`

Stretch histogram to full 0-1 range.

- **bitmap**: 2D numpy array
- **Returns**: Contrast-stretched bitmap

### `floyd_steinberg(bitmap, threshold=0.5)`

Apply Floyd-Steinberg dithering for binary output.

- **bitmap**: 2D numpy array
- **threshold**: Quantization threshold (default 0.5)
- **Returns**: Dithered bitmap (values are 0.0 or 1.0 only)

## pixdot vs pixblock

Both libraries convert images to terminal output, but with different trade-offs:

| | pixdot | pixblock |
|---|--------|----------|
| **Output** | Binary (on/off dots) | ANSI greyscale/color |
| **Encoding** | 256 braille glyphs | Block characters + color codes |
| **Captures** | Structure, edges, outlines | Tone, texture, gradients |
| **Complexity** | Minimal (~50 lines core) | More sophisticated |

**Use pixdot when:**
- You want pedagogical clarity and simplicity
- Output will be piped, saved, or processed as text
- Terminal lacks color support
- Accessibility tools need to parse the output

**Use pixblock when:**
- You're displaying photographs or artwork
- Gradients and tonal range matter
- Your terminal supports 256 or true color

## License

MIT
