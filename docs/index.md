# dapple

**Unified terminal graphics — one Canvas API, seven renderers.**

Terminal-centric development is now mainstream. Claude Code runs in your terminal. AI assistants stream their work as text. Developers SSH into remote machines, pair with tmux, and live in the command line. In this world, there's a gap: we want to see graphics without leaving the terminal.

dapple fills that gap. Load a bitmap once, output to any format — braille, quadrants, sextants, ASCII, sixel, kitty, or fingerprint. Choose the renderer that matches your terminal's capabilities and your visual needs.

## Why a Unified Library?

Terminal graphics tools are fragmented. One library does braille. Another does quadrant blocks. A third handles sixel. Each has its own API, its own conventions.

dapple unifies these approaches:

- **Single Canvas class** — Load your bitmap once, output anywhere
- **Pluggable renderers** — Switch formats with one line: `canvas.out(braille)` or `canvas.out(quadrants)`
- **Consistent options** — Same preprocessing, same color modes, predictable behavior
- **Stream-based output** — Write to stdout, files, or any text stream

## Quick Example

```python
import numpy as np
from dapple import Canvas, braille, quadrants

bitmap = np.random.rand(40, 80).astype(np.float32)
canvas = Canvas(bitmap)

canvas.out(braille)      # Unicode braille (2x4 dots)
canvas.out(quadrants)    # Block chars with ANSI color
```

## Seven Renderers

| Renderer | Cell Size | Colors | Best For |
|----------|-----------|--------|----------|
| `braille` | 2x4 | mono/gray/true | Structure, edges, piping, accessibility |
| `quadrants` | 2x2 | ANSI 256/true | Photos, balanced resolution and color |
| `sextants` | 2x3 | ANSI 256/true | Higher vertical resolution |
| `ascii` | 1x2 | none | Universal compatibility, classic look |
| `sixel` | 1x1 | palette | True pixels (xterm, mlterm, foot) |
| `kitty` | 1x1 | true | True pixels (kitty, wezterm) |
| `fingerprint` | 8x16 | none | Artistic glyph matching |

## CLI Tools

dapple ships command-line tools for viewing images, video, PDFs, markdown, and more:

```bash
imgcat photo.jpg                    # view image in terminal
pdfcat document.pdf                 # view PDF pages
vidcat video.mp4                    # play video in terminal
mdcat README.md                     # render markdown with images
funcat "sin(x)"                     # plot a function
csvcat data.csv --bar revenue       # chart CSV columns
datacat data.jsonl --spark value    # sparkline from JSONL
```

## What's Next

- [Getting Started](getting-started.md) — Installation and first steps
- [Canvas Guide](guide/canvas.md) — The core Canvas API
- [Renderers Guide](guide/renderers.md) — Choosing and configuring renderers
- [CLI Tools](tools/index.md) — Terminal viewers and creators
