# One Canvas, Seven Renderers

You are writing a tool that needs to show an image in a terminal. Which terminal? That is the problem.

Your user might be in an SSH session to a headless server -- braille characters are the safest option. Or running kitty locally -- the native graphics protocol gives pixel-perfect output. Or in a CI runner that logs to a file -- ASCII is the only thing that survives. Or they might not know, and want the tool to figure it out.

Without a common abstraction, you write adapter code for each case. Braille rendering has one API. Color block rendering has another. Sixel has a completely different output mechanism. Your tool accumulates terminal-specific branches, each with its own edge cases, and your actual domain logic -- the thing your tool does -- disappears under the rendering scaffolding.

dapple eliminates this scaffolding.

## The Abstraction

```python
from dapple import Canvas, braille, quadrants, sixel, kitty

# Load once
canvas = Canvas(bitmap, colors=rgb)

# Output to any format
canvas.out(braille)      # SSH, pipes, accessibility
canvas.out(quadrants)    # Color terminals
canvas.out(sixel)        # xterm, foot, mlterm
canvas.out(kitty)        # kitty, wezterm, ghostty
```

One Canvas. Pluggable renderers. The tool author writes domain logic. The renderer handles the terminal. Switching output format is one argument, not a rewrite.

## Design as Engineering

Three design decisions shape dapple. Each addresses a concrete failure mode.

### Stream-based output

Renderers write to `TextIO` streams, not return strings.

```python
# Direct to stdout
canvas.out(braille)

# Direct to file
canvas.out(braille, "output.txt")

# To any stream
canvas.out(braille, my_stringio)
```

The failure mode: a 4000x3000 photograph rendered as quadrant blocks produces a string with millions of ANSI escape sequences. Return-as-string means allocating the entire output in memory before writing a single character. Stream-based output writes incrementally -- the renderer never holds the full output.

This also means graphics flow through pipes naturally. A renderer writing to stdout is a data source in a Unix pipeline. An LLM agent capturing tool output sees a text stream, not a function return value. The stream model makes terminal graphics composable in the same way text tools have always been composable.

### Separate bitmap and colors

Canvas holds two arrays: a grayscale bitmap and optional RGB colors.

```python
# Grayscale only
canvas = Canvas(bitmap)

# With color
canvas = Canvas(bitmap, colors=rgb)
```

The failure mode: forcing renderers to handle both grayscale and color in a single data path. Braille is fundamentally binary -- dots are on or off. It uses the grayscale bitmap for thresholding and ignores colors (unless color mode is enabled, in which case it uses colors for ANSI foreground tinting). Quadrants and sextants use colors for foreground/background selection and the bitmap for luminance-based pattern decisions. Sixel and kitty use colors for direct pixel output.

Each renderer picks what it needs. The Canvas doesn't impose a data model that fits some renderers but not others.

### Frozen dataclass renderers

Renderers are immutable. Options create new instances via `__call__`:

```python
# Default instance
braille.render(bitmap, colors, dest=sys.stdout)

# Custom options (returns new instance)
custom = braille(threshold=0.3, color_mode="grayscale")
custom.render(bitmap, colors, dest=sys.stdout)
```

The failure mode: mutable renderer state that leaks between calls. A renderer configured for one image accidentally retains settings when used for the next. Frozen dataclasses make this impossible -- no instance is ever modified, so sharing renderers between threads or reusing them across calls is safe by construction.

The `__call__` pattern also reads naturally. `braille(threshold=0.3)` means "braille with these settings." The default instance `braille` with no parentheses is the common case.

## The Renderer Spectrum

Seven renderers span a spectrum from universally compatible to pixel-perfect:

| Renderer | Cell | Resolution | Color | Requires |
|----------|------|-----------|-------|----------|
| **ascii** | 1x2 | Lowest | None | Nothing |
| **braille** | 2x4 | High | Optional ANSI | Unicode |
| **quadrants** | 2x2 | Medium | fg/bg ANSI | Unicode |
| **sextants** | 2x3 | Medium-high | fg/bg ANSI | Unicode 13.0 |
| **fingerprint** | 8x16 | Low | None | Pillow (font rendering) |
| **sixel** | 1x1 | Pixel | Palette (256) | DEC sixel support |
| **kitty** | 1x1 | Pixel | 24-bit RGB | Kitty protocol |

The decision flowchart:

- **Will this run over SSH or in CI?** Use braille (best density) or ascii (guaranteed portability).
- **Does the terminal support color?** Quadrants or sextants give good color fidelity with reasonable resolution. Sextants have better vertical resolution -- a real advantage given that terminal cells are taller than wide.
- **Do you need true pixels?** Detect the terminal: sixel for xterm/foot/mlterm, kitty protocol for kitty/wezterm/ghostty.
- **Want something artistic?** Fingerprint matches image regions to font glyphs by visual similarity. It's experimental, but the output has a distinctive quality that other renderers can't produce.

All seven renderers implement the same protocol:

```python
@runtime_checkable
class Renderer(Protocol):
    @property
    def cell_width(self) -> int: ...
    @property
    def cell_height(self) -> int: ...
    def render(self, bitmap, colors, *, dest): ...
```

Tool authors code to the protocol. Users choose the renderer. The two decisions are independent.

## The Composition Boundary

dapple draws a clear line between what it does and what it doesn't.

**dapple does:** Convert a bitmap to terminal output. Preprocessing transforms (auto-contrast, dithering, sharpening). Canvas composition (hstack, vstack, overlay, crop).

**dapple does not:** Load images. Connect to terminals. Detect terminal capabilities. Manage windows or cursor positioning.

Image loading is in optional adapters (`from_pil`, `from_array`, `from_matplotlib`). Terminal detection is the tool author's concern. Window management is a different problem entirely.

This boundary keeps the core library dependency-free (numpy only) and makes each responsibility testable in isolation. A renderer can be tested with a synthetic bitmap and a StringIO -- no terminal required, no image files needed.

---

*See also: [Character Encodings](../guide/encodings.md) explains the encoding algorithms inside each renderer. [Preprocessing](../guide/preprocessing.md) covers the transforms that make raw bitmaps look good.*
