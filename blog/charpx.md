# Unified Terminal Graphics for the AI Era

## The Terminal Renaissance

The terminal is having a moment. Not nostalgia—necessity.

- AI coding assistants (Claude Code, Cursor, Copilot) run in terminals
- SSH sessions, containers, remote dev environments—no X server, no browser
- The terminal as universal interface: works everywhere, over anything

We built graphical IDEs for decades. Now the most advanced coding tools run in monospace text.

## The Fragmentation Problem

AI assistants need to "see" things: charts, diagrams, image previews, visual diffs. But the terminal graphics ecosystem is fragmented:

- **pixdot** does braille (2x4 dots, binary)
- **cel** does quadrant blocks (2x2, ANSI colors)
- **chafa** handles sixel with sophisticated rendering
- **libsixel** for the sixel protocol
- **kitty** has its own graphics protocol

Each has its own API. Each requires learning different conventions. Switching between them means rewriting code.

What if you're building a tool that needs to work across different environments? SSH session to a headless server? Sixel won't work—need braille. Local development in kitty? Use the native protocol for best quality. Creating accessible output? Braille renders to text screen readers can parse.

The fragmentation creates friction.

## charpx: One Canvas, Many Renderers

charpx solves this with a simple abstraction:

```python
from charpx import Canvas, braille, quadrants, sixel, kitty

# Load once
canvas = Canvas(bitmap, colors=rgb)

# Output anywhere
canvas.out(braille)      # Works everywhere
canvas.out(quadrants)    # Works in most terminals
canvas.out(sixel)        # Works in xterm, foot, mlterm
canvas.out(kitty)        # Works in kitty, wezterm
```

Same data, different renderers. Switch with one line.

## Design Philosophy

### Composition Over Features

Unix philosophy: do one thing well.

- Canvas holds the bitmap
- Renderers convert to terminal output
- Adapters load from external formats
- Preprocessing functions transform bitmaps

Each piece is independent. Chain them:

```python
bitmap = load_image("photo.jpg")
bitmap = auto_contrast(bitmap)
bitmap = floyd_steinberg(bitmap)
canvas = Canvas(bitmap)
canvas.out(braille)
```

### Stream-Based Output

Previous implementations often returned strings. This creates problems:

1. Large images allocate massive strings
2. Can't stream output progressively
3. Awkward to write directly to files

charpx renderers write to streams:

```python
# Direct to stdout
canvas.out(braille)

# Direct to file
canvas.out(braille, "output.txt")

# To any TextIO
canvas.out(braille, my_stringio)
```

The renderer never holds the full output in memory. It writes character by character, line by line.

### Immutable Renderers

Renderers are frozen dataclasses. Options create new instances:

```python
# Default
braille.render(bitmap, colors, dest=sys.stdout)

# Custom (returns new instance)
custom = braille(threshold=0.3, color_mode="grayscale")
custom.render(bitmap, colors, dest=sys.stdout)
```

No mutable state. No surprising side effects. Thread-safe by default.

## The Renderers

### Braille: The Universal Fallback

```
Cell size: 2x4 pixels
Output: Unicode braille (U+2800-U+28FF)
Colors: none, grayscale (24-level), truecolor (24-bit)
```

Each braille character encodes 8 dots. A 160x80 pixel image becomes 80x20 characters. The encoding is direct: threshold each pixel, map the 8-bit pattern to a Unicode codepoint.

Best for: SSH sessions, piping, accessibility, structure/edge visualization.

### Quadrants: Balanced Quality

```
Cell size: 2x2 pixels
Output: Unicode block characters (quadrants)
Colors: 256-color ANSI or 24-bit true color
```

Four pixels per character, with two colors (foreground + background). The renderer picks the best block character to represent each 2x2 region.

Best for: Photo previews, balanced resolution and color.

### Sextants: More Vertical Resolution

```
Cell size: 2x3 pixels
Output: Unicode sextant characters
Colors: 256-color ANSI or 24-bit true color
```

Six pixels per character. More vertical resolution than quadrants, which matters for typical terminal cells (taller than wide).

Best for: Text-heavy images, taller aspect ratios.

### ASCII: Universal Compatibility

```
Cell size: 1x2 pixels
Output: ASCII characters (configurable charset)
Colors: none
```

No Unicode required. Works in the most constrained environments. Configurable charset: ` .:-=+*#%@` by default.

Best for: Absolutely universal compatibility.

### Sixel: True Pixels (Classic)

```
Cell size: 1x1 pixels
Output: DEC Sixel escape sequences
Colors: Palette-based (up to 256)
```

True pixel output using the DEC Sixel protocol from 1984. Supported by xterm, mlterm, foot, and others.

Best for: High-quality local display in compatible terminals.

### Kitty: True Pixels (Modern)

```
Cell size: 1x1 pixels
Output: Kitty graphics protocol
Colors: 24-bit true color
```

Modern graphics protocol with PNG compression or raw RGB. Supported by kitty and wezterm.

Best for: High-quality local display in kitty/wezterm.

### Fingerprint: Artistic

```
Cell size: 8x16 pixels (configurable)
Output: Matched glyphs from font bitmap
Colors: none
```

Experimental renderer that correlates image regions with font glyph bitmaps. The output resembles the image using the font's character shapes.

Best for: Artistic effects, experimentation.

## When to Use What

| Environment | Renderer |
|-------------|----------|
| SSH/tmux/screen | braille, quadrants, ascii |
| Piping to files | braille, ascii |
| Screen readers | braille |
| Local xterm | sixel |
| Local kitty | kitty |
| Unknown terminal | braille (safest), ascii (most compatible) |

## The Bigger Picture

Terminal graphics aren't a step backward. They're meeting users where they are: in SSH sessions, in containers, in AI coding workflows.

The terminal is the universal interface. charpx makes graphics work there.

---

*charpx is available on PyPI: `pip install charpx`*
