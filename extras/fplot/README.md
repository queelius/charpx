# fplot: Terminal Function Plotter

A command-line tool for plotting mathematical functions directly in the terminal using [charpx](../../README.md) renderers.

## Why Terminal Graphics?

Claude Code and other terminal-based AI assistants run in terminals. Visualization without leaving the terminal enables:

- **Quick data exploration** during debugging sessions
- **Plotting in SSH sessions** without X11 forwarding
- **Integration with shell pipelines** for composable workflows
- **Instant feedback** without context switching to GUI tools

## Installation

```bash
cd extras/fplot
pip install -e .
```

## charpx: The Foundation

fplot is built on charpx, a unified terminal graphics library. It provides multiple renderers:

| Renderer | Resolution | Best For |
|----------|-----------|----------|
| `braille` | 2×4 dots/char | Highest text resolution, default |
| `quadrants` | 2×2 blocks/char | Color-rich displays |
| `sextants` | 2×3 blocks/char | Balance of resolution and color |
| `ascii` | 1×2 chars | Universal compatibility |
| `sixel` | 1×1 pixels | True pixels (xterm, mlterm, foot) |
| `kitty` | 1×1 pixels | True pixels (kitty, wezterm) |

## Quick Start

### Simple Functions

```bash
# Sine wave
fplot "sin(x)"

# Polynomial
fplot "x**2 - 2*x + 1"

# Gaussian
fplot "exp(-x**2)"

# With custom range
fplot "sin(x)" --xmin -10 --xmax 10
```

### Available Math Functions

| Category | Functions |
|----------|-----------|
| **Trigonometric** | `sin`, `cos`, `tan`, `asin`, `acos`, `atan` |
| **Hyperbolic** | `sinh`, `cosh`, `tanh` |
| **Exponential** | `exp`, `log`, `log10`, `log2` |
| **Other** | `sqrt`, `abs`, `floor`, `ceil` |
| **Constants** | `pi`, `e` |

### Custom Colors

```bash
fplot "sin(x)" --color red
fplot "cos(x)" --color "#ff6600"
fplot "tan(x)" --color cyan
```

Named colors: `cyan`, `red`, `green`, `yellow`, `magenta`, `orange`, `blue`, `pink`, `white`, `gray`

### Renderer Selection

```bash
fplot "sin(x)" -r braille     # Default, highest resolution
fplot "sin(x)" -r quadrants   # 2×2 blocks with color
fplot "sin(x)" -r sextants    # 2×3 blocks
fplot "sin(x)" -r ascii       # Universal ASCII
fplot "sin(x)" -r sixel       # True pixels (compatible terminals)
fplot "sin(x)" -r kitty       # True pixels (kitty/wezterm)
```

## Chaining Multiple Functions

fplot supports JSON chaining for composable pipelines:

```bash
# Plot sin and cos together
fplot "sin(x)" -j | fplot "cos(x)" -l

# Three functions with legend
fplot "sin(x)" -j | fplot "cos(x)" -j | fplot "tan(x)" -l --ymin -3 --ymax 3

# Custom colors in chain
fplot "x" --color red -j | fplot "x**2" --color blue -j | fplot "x**3" --color green -l
```

The `-j` flag outputs JSON state, allowing the next fplot to continue. The `-l` flag shows a colored legend.

## Parametric Curves

Parametric curves define both x and y as functions of parameter t:

```bash
# General syntax
fplot -p "x(t),y(t)"
```

### Circle

```bash
fplot -p "cos(t),sin(t)" -l -w 40 -H 20
```

### Spiral

```bash
fplot -p "t*cos(t),t*sin(t)" --tmin 0 --tmax 12.56 -l
```

### Lissajous Figures

```bash
fplot -p "sin(3*t),sin(2*t)" -l
fplot -p "sin(5*t),sin(4*t)" -l
```

### Heart Curve

```bash
fplot -p "16*sin(t)**3,13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t)" -l -w 40 -H 20
```

### Figure-8 (Lemniscate)

```bash
fplot -p "sin(t),sin(t)*cos(t)" -l
```

## Options Reference

| Option | Description |
|--------|-------------|
| `expression` | Function of x (e.g., `"sin(x)"`, `"x**2"`) |
| `-p`, `--parametric` | Parametric function: `"x(t),y(t)"` |
| `--xmin`, `--xmax` | X-axis range (default: -2π to 2π) |
| `--ymin`, `--ymax` | Y-axis range (auto-computed if omitted) |
| `--tmin`, `--tmax` | Parameter t range (default: 0 to 2π) |
| `-w`, `--width` | Width in characters (default: terminal width) |
| `-H`, `--height` | Height in characters (default: terminal height - 2) |
| `-r`, `--renderer` | Renderer: braille, quadrants, sextants, ascii, sixel, kitty |
| `--color` | Color for this function (name or #RRGGBB) |
| `-n`, `--nsamples` | Number of sampling points |
| `--axes` | Show coordinate axes |
| `-j`, `--json` | Output JSON for chaining |
| `-l`, `--legend` | Show legend (for multiple functions) |
| `--font-aspect` | Terminal font aspect ratio (default: 2.0) |

## Claude Code Integration

When using Claude Code, you can ask:

- "Plot sin(x) in the terminal"
- "Show me a parametric spiral"
- "Compare sin, cos, and tan on one graph"
- "Plot the heart curve parametric equation"
- "Visualize x² with different renderers"

Claude Code can invoke fplot directly to provide visual output without leaving the terminal session.

## Examples Gallery

### Damped Oscillation

```bash
fplot "exp(-x/5)*sin(x)" --xmin 0 --xmax 20 -l
```

### Sinc Function

```bash
fplot "sin(x)/x" --xmin -15 --xmax 15 -l
```

### Butterfly Curve

```bash
fplot -p "sin(t)*(exp(cos(t))-2*cos(4*t)-sin(t/12)**5),cos(t)*(exp(cos(t))-2*cos(4*t)-sin(t/12)**5)" --tmin 0 --tmax 62.83 -l -w 60 -H 30
```

### Hyperbolic Functions

```bash
fplot "sinh(x)" -j | fplot "cosh(x)" -j | fplot "tanh(x)" -l --xmin -3 --xmax 3
```

## Architecture

fplot follows a clean pipeline architecture:

1. **Expression evaluation** → Safe `eval()` with sandboxed namespace
2. **Mask generation** → Boolean array of where curve passes
3. **Rendering** → charpx renderer writes to stdout

This design is renderer-agnostic: the same mask works with any charpx renderer.

## Security

Expression evaluation uses a sandboxed `eval()`:
- Empty `__builtins__` prevents access to Python internals
- Explicit `SAFE_NAMESPACE` exposes only math functions
- No file system or network access possible

## License

MIT License - see the main charpx repository for details.
