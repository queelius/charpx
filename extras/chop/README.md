# chop

Unix-philosophy image manipulation CLI with JSON piping for terminal graphics.

## Installation

```bash
pip install chop
```

## Quick Start

```bash
# Display image in terminal
chop load photo.jpg

# Pipeline with operations
chop load photo.jpg -j | chop resize 50% -j | chop dither -r braille

# Save to file
chop load photo.jpg -j | chop rotate 90 -o rotated.png
```

## Operations

| Operation | Syntax | Description |
|-----------|--------|-------------|
| `load` | `chop load <path\|url\|->` | Load from file, URL, or stdin |
| `resize` | `chop resize <50%\|800x600\|w800\|h600>` | Resize image |
| `crop` | `chop crop <x> <y> <w> <h>` | Crop region (pixels or %) |
| `rotate` | `chop rotate <degrees>` | Rotate counter-clockwise |
| `flip` | `chop flip <h\|v>` | Flip horizontal or vertical |
| `dither` | `chop dither [--threshold N]` | Floyd-Steinberg dithering |
| `invert` | `chop invert` | Invert brightness |
| `sharpen` | `chop sharpen [--strength N]` | Edge enhancement |
| `contrast` | `chop contrast` | Auto-contrast |
| `gamma` | `chop gamma <value>` | Gamma correction |
| `threshold` | `chop threshold <level>` | Binary threshold |

## Global Flags

```
-j, --json       Output JSON for piping
-o, --output     Save to file (png, jpg, etc.)
-r, --renderer   Terminal renderer (braille, quadrants, sextants, ascii, sixel, kitty)
-w, --width      Output width in characters
-H, --height     Output height in characters
```

## Examples

```bash
# Basic display
chop load photo.jpg -r braille

# Resize and crop
chop load photo.jpg -j | chop resize 800x600 -j | chop crop 100 100 600 400 -r quadrants

# Image processing pipeline
chop load noisy.jpg -j | chop contrast -j | chop sharpen --strength 1.5 -j | chop dither -r braille

# Save processed image
chop load input.png -j | chop rotate 45 -j | chop resize 50% -o output.png

# Load from URL
chop load https://example.com/image.jpg -r sextants
```

## JSON Pipeline Format

When using `-j`, chop outputs JSON that preserves the image and processing history:

```json
{
  "version": 1,
  "image": {
    "type": "base64",
    "format": "png",
    "data": "<base64-encoded>"
  },
  "metadata": {
    "original_path": "photo.jpg",
    "original_size": [1920, 1080],
    "current_size": [960, 540]
  },
  "history": [
    {"op": "load", "args": ["photo.jpg"]},
    {"op": "resize", "args": ["50%"]}
  ]
}
```

## Built on dapple

chop uses [dapple](https://github.com/anthropics/dapple) for terminal rendering. All dapple renderers are supported.
