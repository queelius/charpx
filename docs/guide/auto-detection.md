# Auto-Detection

dapple can detect the current terminal's graphics capabilities and select the best renderer automatically. This is useful for tools and scripts that should produce the highest-quality output the terminal supports, without requiring the user to specify a renderer.

## Quick Start

```python
from dapple import auto_renderer, render_image

# One-liner: load image, detect terminal, render
render_image("photo.jpg")

# Or: get the best renderer, use it with a Canvas
renderer = auto_renderer()
canvas.out(renderer)
```

## `detect_terminal()`

Returns a `TerminalInfo` dataclass with the detected protocol and capabilities.

```python
from dapple import detect_terminal

info = detect_terminal()
print(info.protocol)        # Protocol.KITTY, Protocol.SIXEL, etc.
print(info.terminal_name)   # "kitty", "xterm-256color", etc.
print(info.color_support)   # True or False
print(info.is_pixel_renderer)  # True for KITTY/SIXEL
```

### `TerminalInfo` fields

| Field             | Type       | Description                                        |
|-------------------|------------|----------------------------------------------------|
| `protocol`        | `Protocol` | Best detected graphics protocol                    |
| `terminal_name`   | `str\|None` | Terminal name from `TERM_PROGRAM` or `TERM`       |
| `color_support`   | `bool`     | Whether color output is supported                  |
| `is_pixel_renderer` | `bool`  | `True` if protocol is KITTY or SIXEL (property)   |

## `Protocol` Enum

The `Protocol` enum represents the five graphics capability tiers that dapple detects:

| Value               | Description                           | Renderer  |
|---------------------|---------------------------------------|-----------|
| `Protocol.KITTY`    | Kitty graphics protocol (PNG inline)  | `kitty`   |
| `Protocol.SIXEL`    | DEC Sixel graphics                    | `sixel`   |
| `Protocol.QUADRANTS`| Unicode quadrant blocks with color    | `quadrants` |
| `Protocol.BRAILLE`  | Unicode braille patterns              | `braille` |
| `Protocol.ASCII`    | Pure ASCII (universal fallback)       | `ascii`   |

```python
from dapple import Protocol

info = detect_terminal()
if info.protocol == Protocol.KITTY:
    print("True pixel output via Kitty protocol")
elif info.protocol == Protocol.SIXEL:
    print("True pixel output via Sixel protocol")
else:
    print(f"Character-based output: {info.protocol.value}")
```

## `auto_renderer()`

Returns the best `Renderer` instance for the current terminal. This is the primary function most code should use.

```python
from dapple import auto_renderer

renderer = auto_renderer()
canvas.out(renderer)
```

### Parameters

| Parameter      | Type   | Default | Description                                   |
|----------------|--------|---------|-----------------------------------------------|
| `prefer_color` | `bool` | `True`  | Prefer color-capable renderers                |
| `plain`        | `bool` | `False` | Force ASCII output (for pipes and redirects)  |

### Selection logic

The selection follows this priority:

```
1. If plain=True           --> ascii
2. If stdout is not a tty  --> braille (or ascii if prefer_color=False)
3. If Kitty detected       --> kitty
4. If Sixel detected       --> sixel
5. If color supported      --> quadrants (or braille if prefer_color=False)
6. Otherwise               --> ascii
```

### Forcing ASCII for pipes

When output is piped to another program or redirected to a file, pixel protocols and ANSI escape codes are usually unwanted. `auto_renderer()` detects this automatically by checking `sys.stdout.isatty()`:

```python
# Automatic: falls back to braille when piped
renderer = auto_renderer()

# Explicit: always use ASCII (no Unicode, no escape codes)
renderer = auto_renderer(plain=True)
```

### Monochrome mode

```python
# Prefer braille over quadrants even on color terminals
renderer = auto_renderer(prefer_color=False)
```

## `render_image(path)`

A convenience function that handles the entire pipeline: load an image from a file, auto-detect the terminal, and render to stdout.

```python
from dapple import render_image

# Simplest possible usage
render_image("photo.jpg")

# With resizing
render_image("photo.jpg", width=160)
render_image("photo.jpg", width=160, height=80)

# With explicit renderer (skips auto-detection)
from dapple import braille
render_image("photo.jpg", renderer=braille)
```

| Parameter  | Type       | Default | Description                                  |
|------------|------------|---------|----------------------------------------------|
| `image_path` | `str`   | *(required)* | Path to image file                      |
| `width`    | `int\|None` | `None` | Target width in pixels                       |
| `height`   | `int\|None` | `None` | Target height in pixels                      |
| `renderer` | `Renderer\|None` | `None` | Renderer to use (None = auto-detect)   |

> **Note:** `render_image()` requires pillow (`pip install pillow`) for image loading.

## How Detection Works

### Kitty protocol detection

dapple checks two environment variables:

| Variable              | Set by                  |
|-----------------------|-------------------------|
| `KITTY_WINDOW_ID`     | Kitty terminal          |
| `GHOSTTY_RESOURCES_DIR` | Ghostty terminal      |

If either is present, the terminal supports the Kitty graphics protocol.

### Sixel protocol detection

dapple checks `TERM` and `TERM_PROGRAM` against a list of known Sixel-capable terminals:

- mlterm
- yaft
- foot
- contour
- wezterm
- mintty
- xterm (when `XTERM_VERSION` is set)

### Color support detection

Color support is determined by:

1. **`NO_COLOR` environment variable**: if set, color is disabled (following the [no-color convention](https://no-color.org/)).
2. **`TERM` value**: checked for substrings like `color`, `256`, `direct`, `truecolor`, `kitty`, `xterm`.
3. **`COLORTERM` environment variable**: if set, indicates true color support.
4. **Default**: color is assumed to be supported.

### Fallback

If no pixel protocol is detected, the default is `Protocol.QUADRANTS` (Unicode block elements with ANSI colors). This provides a good balance of resolution and compatibility for modern terminals.

## When to Use Auto vs Explicit

### Use `auto_renderer()` when:

- Building CLI tools that should work across different terminals.
- Writing scripts that may run in various environments (local, SSH, CI).
- You do not know what terminal the user has.

### Use explicit renderers when:

- You know the target terminal (e.g., "this always runs in Kitty").
- You need deterministic output (e.g., tests, file generation).
- You want a specific aesthetic (e.g., braille art style regardless of terminal capability).
- You are rendering to a file, not a terminal.

```python
from dapple import braille, quadrants, auto_renderer

# Auto: best for the current terminal
canvas.out(auto_renderer())

# Explicit: always braille, regardless of terminal
canvas.out(braille)

# Explicit: always quadrants with specific settings
canvas.out(quadrants(true_color=False))
```

## Complete Example

```python
from dapple import Canvas, auto_renderer, detect_terminal, Protocol
from dapple.adapters.pil import load_image
from dapple.preprocess import auto_contrast

# Check what we are working with
info = detect_terminal()
print(f"Terminal: {info.terminal_name}")
print(f"Protocol: {info.protocol.value}")
print(f"Color: {info.color_support}")
print(f"Pixel: {info.is_pixel_renderer}")

# Load and preprocess
canvas = load_image("photo.jpg", width=160)

# Apply preprocessing only for character renderers
if not info.is_pixel_renderer:
    bitmap = auto_contrast(canvas.bitmap)
    canvas = Canvas(bitmap, colors=canvas.colors)

# Render with the best available renderer
renderer = auto_renderer()
canvas.out(renderer)
```
