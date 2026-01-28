# Terminal Graphics in the Age of AI Agents

## The Resurgence of the Terminal

The terminal is having a moment. Not because of nostalgia, but necessity.

- AI coding assistants (Claude Code, Cursor, Copilot) live in terminals
- SSH sessions, containers, headless CI—no X server, no browser
- The terminal as universal interface: works everywhere, over anything

The irony: we built graphical IDEs for decades, and now the most advanced coding tools run in monospace text.

## Why Terminal Graphics Matter Now

AI assistants need to "see" things:

- Render a quick preview of a diagram or chart
- Show diffs visually, not just textually
- Display thumbnails, plots, architecture diagrams
- Debug image processing pipelines

The alternatives are clunky:
- Open a browser tab (context switch)
- Write to file, then open (more steps)
- Describe the image in words (lossy)

What if the AI could just... show you?

## cel: Simple Over Clever

cel takes a different approach than tools like chafa or libsixel:

- ~240 lines of numpy (core rasterizer)
- Pure API: `numpy array -> ANSI string`
- No image I/O, no protocol negotiation
- Fast enough for real-time preview

We're not competing on quality. We're optimizing for:
- Speed of implementation
- Speed of execution
- Composability

## The Design Philosophy

**Unix**: Do one thing well. cel rasterizes. That's it.

**Composition over features**: Want to load an image? Use PIL. Want to resize? Use scipy. cel just converts.

**numpy as universal bitmap**: The lingua franca of numerical computing. Every image library can produce a numpy array.

## How It Works

### The Core Insight

A terminal character cell can display 4 "pixels" using Unicode quadrant block characters:

```
┌───┬───┐
│ ▘ │ ▝ │
├───┼───┤
│ ▖ │ ▗ │
└───┴───┘
```

Combined with ANSI colors (foreground + background), each cell can represent a 2x2 pixel block with 2 colors.

### Vectorized Processing

The key optimization: process all blocks at once with numpy.

```python
# Reshape image into blocks: (H, W) -> (H//2, W//2, 4)
blocks = bitmap.reshape(rows, 2, cols, 2).transpose(0, 2, 1, 3).reshape(rows, cols, 4)

# Min/max per block = background/foreground colors
fg = blocks.max(axis=2)  # brightest pixel
bg = blocks.min(axis=2)  # darkest pixel

# Threshold at midpoint -> pattern
thresh = (fg + bg) / 2
patterns = (blocks > thresh) @ [8, 4, 2, 1]  # bit pattern
```

This replaces per-block Python loops with bulk numpy operations for pattern and color calculation. The final string assembly still uses Python loops, but the computationally expensive work is vectorized.

### Simplified 2-Color Selection

Previous version: k-means clustering per block (2 iterations each).

New version: min/max split with midpoint threshold.

Is it worse? Technically yes. Does it matter? Not at terminal resolution.

## Benchmark

```
Grayscale (200x400): ~36ms per render
RGB (200x400):       ~72ms per render
```

*Benchmarks measured on an Apple M1 using Python 3.11. Performance will vary based on CPU and numpy build.*

That's 500k+ blocks per second for grayscale. Fast enough for:
- Real-time video preview (with downscaling)
- Interactive plot updates
- Quick visual feedback in AI workflows

## CLI: Unix Pipes and Globs

The CLI follows Unix conventions: stdin, stdout, globs, multiple files.

```bash
# Basic usage
cel photo.jpg                   # 24-bit true color (default)
cel photo.jpg --grayscale       # Grayscale mode
cel photo.jpg --256-color       # 256-color for older terminals

# Multiple files
cel *.png                       # Process all PNGs
cel photos/**/*.jpg             # Recursive glob

# Pipes
cat image.jpg | cel             # Pipe from stdin
curl -s https://example.com/img.png | cel -
convert -size 100x100 gradient: png:- | cel -
```

The API is the foundation; the CLI is just one composition of it.

## When to Use cel

Use cel when:
- You need quick visual feedback in a terminal
- You're already working with numpy arrays
- You want something simple you can understand and modify

Don't use cel when:
- You need high-quality rendering (use chafa, libsixel)
- You're rendering to a file (just save the image)
- Terminal doesn't support Unicode (rare these days)

## Standing on Shoulders

Terminal graphics has deep roots. Nick Black's [notcurses](https://github.com/dankamongmen/notcurses) library is the definitive reference—it handles everything from sixel protocols to Kitty graphics to Unicode block characters with proper terminal detection and optimization.

cel doesn't try to compete. It solves a narrower problem: fast, pure-numpy rasterization for when you already have a bitmap and just want ANSI output. The composition `your_vector_library → bitmap → cel → terminal` is simple and sufficient for quick previews.

For production-quality terminal graphics, notcurses is the right choice.

## The Bigger Picture

Terminal graphics aren't a step backward. They're meeting users where they are: in SSH sessions, in containers, in AI coding workflows.

The best interface is the one that's already there.

---

*cel is available on PyPI: `pip install cel`*
