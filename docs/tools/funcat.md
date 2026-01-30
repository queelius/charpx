# funcat -- Function Plotter

Plot mathematical functions in the terminal using dapple renderers.

Supports standard functions of `x`, parametric curves with parameter `t`,
pipeline composition via JSON for overlaying multiple functions, and
configurable colors and axis ranges.

> **Note:** This tool was previously called "fplot" in earlier versions and
> blog posts. The command and package name is now **funcat**.

## Installation

```bash
pip install dapple[funcat]
```

No additional dependencies are needed beyond dapple's core numpy requirement.

## Usage

### Basic Function Plotting

```bash
# Plot a function of x
funcat "sin(x)"
funcat "x**2 - 3*x + 1"
funcat "exp(-x**2)"
funcat "log(abs(x))"
```

### Custom Ranges

```bash
# Set x-axis range (default: -2pi to 2pi)
funcat "sin(x)" --xmin -10 --xmax 10

# Set y-axis range (default: auto-computed)
funcat "tan(x)" --ymin -5 --ymax 5

# Combine both
funcat "x**3" --xmin -3 --xmax 3 --ymin -10 --ymax 10
```

### Renderer Selection

```bash
# Default is braille (best for line plots)
funcat "sin(x)"

# Use other renderers
funcat -r quadrants "sin(x)"
funcat -r sextants "sin(x)"
funcat -r ascii "sin(x)"
funcat -r sixel "sin(x)"
funcat -r kitty "sin(x)"
```

### Axes and Legends

```bash
# Show axes (drawn at x=0 and y=0)
funcat "sin(x)" --axes

# Show legend (useful with multiple functions)
funcat "sin(x)" -j | funcat "cos(x)" --axes --legend
```

### Color Control

```bash
# Specify a named color
funcat "sin(x)" --color red
funcat "sin(x)" --color cyan

# Specify a hex color
funcat "sin(x)" --color "#ff6600"
```

Available named colors: `cyan`, `red`, `green`, `yellow`, `magenta`, `orange`,
`blue`, `pink`, `white`, `gray`.

When no color is specified, functions cycle through a built-in palette
automatically.

### Size Control

```bash
# Set width and height in terminal characters
funcat "sin(x)" -w 100
funcat "sin(x)" -H 30
funcat "sin(x)" -w 100 -H 30
```

### Sampling Control

```bash
# Control number of sample points (default: pixel width)
funcat "sin(100*x)" -n 5000
```

### Font Aspect Ratio

Terminal characters are typically twice as tall as they are wide. funcat
compensates for this automatically. If your font has a different aspect ratio,
adjust it:

```bash
# Default font aspect ratio is 2.0 (height/width)
funcat "sin(x)" --font-aspect 1.8
```

## Pipeline Composition

funcat supports chaining multiple functions together using JSON piping. Use
`-j` (or `--json`) to output intermediate state as JSON, and omit it on the
final command in the chain to render.

### Overlay Multiple Functions

```bash
# Chain two functions
funcat "sin(x)" -j | funcat "cos(x)"

# Chain with colors
funcat "sin(x)" --color cyan -j | funcat "cos(x)" --color red

# Chain three functions with legend
funcat "sin(x)" -j | funcat "cos(x)" -j | funcat "sin(x)*cos(x)" --legend

# Use -l as shorthand for --legend on the final render
funcat "sin(x)" -j | funcat "cos(x)" -l
```

The JSON intermediate format preserves all expression definitions and axis
ranges, so functions share a common coordinate system.

### Mixed Regular and Parametric

```bash
funcat "sin(x)" -j | funcat -p "cos(t),sin(t)" --legend
```

## Parametric Curves

Plot parametric curves defined as `x(t),y(t)` using the `-p` flag:

```bash
# Circle
funcat -p "cos(t),sin(t)"

# Lissajous figure
funcat -p "sin(3*t),sin(2*t)"

# Spiral
funcat -p "t*cos(t),t*sin(t)" --tmin 0 --tmax 20

# Custom t range (default: 0 to 2pi)
funcat -p "cos(t),sin(t)" --tmin 0 --tmax 6.28
```

## Available Math Functions

The expression evaluator provides these functions and constants:

| Function | Description |
|----------|-------------|
| `sin`, `cos`, `tan` | Trigonometric |
| `asin`, `acos`, `atan` | Inverse trigonometric |
| `sinh`, `cosh`, `tanh` | Hyperbolic |
| `exp` | Exponential |
| `log`, `log10`, `log2` | Logarithms |
| `sqrt` | Square root |
| `abs` | Absolute value |
| `floor`, `ceil` | Rounding |
| `pi`, `e` | Constants |

Standard Python operators work: `+`, `-`, `*`, `/`, `**` (power), `%` (modulo).

### Expressions Starting with a Minus Sign

If your expression starts with `-`, use `--` to prevent it from being parsed
as a flag:

```bash
funcat -- "-2*x + 1"
```

## Python API

funcat is primarily a CLI tool. For programmatic plotting, use the underlying
dapple Canvas API directly or call `main()`:

```python
from dapple.extras.funcat.funcat import main
```

For custom plotting in Python, the dapple canvas and renderer system provides
full control:

```python
import numpy as np
from dapple.canvas import Canvas
from dapple import braille

# Create a plot manually
width, height = 160, 80
bitmap = np.zeros((height, width), dtype=np.float32)
colors = np.zeros((height, width, 3), dtype=np.float32)

x = np.linspace(-2 * np.pi, 2 * np.pi, width)
y = np.sin(x)

# Map to pixel coordinates
y_norm = (y - y.min()) / (y.max() - y.min())
rows = ((1 - y_norm) * (height - 1)).astype(int)
cols = np.arange(width)

for col, row in zip(cols, rows):
    bitmap[row, col] = 1.0
    colors[row, col] = (0.0, 0.8, 1.0)  # cyan

canvas = Canvas(bitmap, colors=colors)
canvas.out(braille(threshold=0.2, color_mode="truecolor"))
```

## Entry Point

```
funcat = dapple.extras.funcat.funcat:main
```

## Reference

```
usage: funcat [-h] [-p X,Y] [--xmin XMIN] [--xmax XMAX] [--ymin YMIN]
              [--ymax YMAX] [--tmin TMIN] [--tmax TMAX]
              [--font-aspect FONT_ASPECT] [-w WIDTH] [-H HEIGHT]
              [--axes] [-j] [-l] [--color COLOR] [-n SAMPLES]
              [-r {braille,quadrants,sextants,ascii,sixel,kitty}]
              [expression]

Plot mathematical functions in the terminal with selectable renderers

positional arguments:
  expression            Function of x (e.g., "sin(x)", "x**2")

options:
  -p, --parametric      Parametric function: "x(t),y(t)"
  --xmin                X-axis minimum (default: -2pi)
  --xmax                X-axis maximum (default: 2pi)
  --ymin                Y-axis minimum (default: auto)
  --ymax                Y-axis maximum (default: auto)
  --tmin                Parameter t minimum (default: 0)
  --tmax                Parameter t maximum (default: 2pi)
  --font-aspect         Terminal font aspect ratio, height/width (default: 2.0)
  -w, --width           Width in characters
  -H, --height          Height in characters
  --axes                Show axes
  -j, --json            Output JSON for chaining
  -l, --legend          Show legend for multiple functions
  --color               Color for this function (name or #RRGGBB)
  -n, --nsamples        Sampling points for this function
  -r, --renderer        Renderer (default: braille)
```
