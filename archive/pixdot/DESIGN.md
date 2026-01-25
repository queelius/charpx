# Design Philosophy

> **Note:** This document describes a **higher-level drawing library** that could be built on top of pixdot—not pixdot itself. pixdot is simply `render(bitmap) → braille string`. The Canvas, drawing primitives, and multiple renderers described below are ideas for a future library (perhaps "pixcanvas") that would use pixdot as one of its output backends.

---

This document defines what such a library would be, its guiding principles, and how to extend it.

## What This Library Is

**A sparse raster canvas for terminal pseudo-pixels with immediate-mode drawing.**

| Term | Definition |
|------|------------|
| **Sparse raster** | Stores only "on" pixels as `Set[(x, y)]`, not a dense grid |
| **Pseudo-pixels** | Logical points that map to sub-character positions (not true screen pixels) |
| **Immediate mode** | Drawing commands mutate canvas state directly; no retained scene graph |
| **Terminal-bound** | Output is Unicode text strings for terminal display |

## Core Data Model

```
Pixels:   Set[Tuple[int, int]]     # sparse storage of lit coordinates
Canvas:   Pixels + Colors + Size   # mutable container with per-cell colors
Renderer: Pixels → str             # maps pixel regions to Unicode characters
```

The fundamental data is just a set of (x, y) coordinates. Everything else—colors, dimensions, rendering—builds on top of this.

## Principles (SICP-inspired)

### Primitive Expressions

The atomic building blocks:

```python
Point  = Tuple[int, int]           # a single coordinate
Pixels = Set[Point]                # collection of lit coordinates
Cell   = (width, height, mapping)  # renderer's atomic unit
```

### Means of Combination

How we build complex things from simple things:

| Combination | How It Works |
|-------------|--------------|
| **Sequential drawing** | `canvas.circle(); canvas.line()` — implicit union |
| **Pixel set operations** | Repeated `set()` calls accumulate pixels |
| **Color layering** | Per-cell foreground/background colors |
| **Renderer swap** | Same pixels, different visual output |

### Means of Abstraction

How we name and reuse compound things:

```python
# Functions that draw (primary abstraction mechanism)
def draw_logo(canvas):
    canvas.rectangle(5, 5, 75, 35, filled=True)
    canvas.circle(40, 20, 12)
    canvas.text(30, 18, "HI")

# Canvas as portable state
def draw_border(canvas):
    w, h = canvas.width, canvas.height
    canvas.rectangle(0, 0, w-1, h-1)

# Reuse across different renderers
for renderer in [RendererType.BRAILLE, RendererType.QUADRANT]:
    c = Canvas(80, 40, renderer=renderer)
    draw_logo(c)
    print(c.render_to_string())
```

## Design Decisions

### Why Imperative Over Functional?

We chose mutable `Canvas` over pure `Shape` values because:

1. **Terminal graphics are fire-and-forget** — draw once, print, done
2. **Mutation is natural for animation** — clear and redraw loops
3. **Simpler mental model** — no need to thread state or compose transforms
4. **Functions-that-draw suffice** — reuse via `def draw_thing(canvas)`

A functional layer (`circle() -> Set[Point]`, `union()`, etc.) could be added on top if needed, but adds ceremony for common cases.

### Why Sparse Pixel Storage?

```python
_pixels: Set[Tuple[int, int]]  # not: List[List[bool]]
```

1. **Most terminal graphics are sparse** — lines, outlines, text
2. **O(1) membership test** — useful for hit detection, collision
3. **Memory efficient** — 1000x1000 canvas with 100 pixels uses ~100 entries, not 1M

Trade-off: filled rectangles are less efficient than dense storage. Acceptable for terminal graphics scale.

### Why Decouple Rendering?

```
Canvas → Renderer.render(pixels) → Unicode string
              ↑
    BrailleRenderer (2×4 dots)
    QuadrantRenderer (2×2 blocks)
    SextantRenderer (2×3 blocks)
```

1. **Same drawing code, different styles** — switch look without rewriting
2. **Renderer is presentation, not logic** — separation of concerns
3. **Extensible** — add new Unicode glyph sets without changing Canvas

## Layering

```
Layer 0: Pixels      Set[Tuple[int, int]]    Pure data, no behavior
Layer 1: Canvas      Mutable container       State + colors + bounds
Layer 2: Primitives  line(), circle()        Algorithms (Bresenham, etc.)
Layer 3: Rendering   Renderer → str          Presentation
```

Each layer depends only on layers below. You can:
- Use Layer 0 directly for custom algorithms
- Swap Layer 3 without touching Layers 0-2
- Add new Layer 2 primitives without modifying Canvas

## What This Library Is NOT

Explicit non-goals (build separately if needed):

| Feature | Why Not Here |
|---------|--------------|
| **Scene graph** | Adds complexity; functions-that-draw are simpler |
| **Transformations** | Rotate/scale belong in a higher-level library |
| **Anti-aliasing** | Sub-pixel smoothing doesn't map to discrete glyphs |
| **Image I/O** | Use `chafa` or `PIL` for image conversion |
| **Animation loop** | Use `time.sleep()` or `asyncio`; not our concern |
| **Widget toolkit** | Build on top if needed; we're just pixels |

## Extension Points

### Custom Renderers

Implement the `Renderer` protocol:

```python
class MyRenderer(Renderer):
    @property
    def cell_width(self) -> int: return 2

    @property
    def cell_height(self) -> int: return 2

    def render_cell(self, pixels, px_base, py_base) -> str:
        # Map 2×2 pixel region to a character
        ...
```

### Reusable Shapes

Define functions that accept a canvas:

```python
def star(canvas, cx, cy, outer_r, inner_r, points=5, **kwargs):
    """Draw a star shape."""
    import math
    vertices = []
    for i in range(points * 2):
        r = outer_r if i % 2 == 0 else inner_r
        angle = math.pi * i / points - math.pi / 2
        vertices.append((
            int(cx + r * math.cos(angle)),
            int(cy + r * math.sin(angle))
        ))
    canvas.polygon(vertices, **kwargs)
```

### Higher-Level Libraries

Build on top for more sophisticated needs:

```python
# Hypothetical scene graph library
from braille_scene import Scene, Circle, Rectangle

scene = Scene()
scene.add(Circle(40, 20, 15, color=RED))
scene.add(Rectangle(10, 10, 30, 30, color=BLUE))

canvas = scene.render(width=80, height=40)
print(canvas.render_to_string())
```

This library provides the foundation; compose upward for richer abstractions.
