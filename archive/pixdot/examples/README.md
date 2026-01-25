# pixdot Examples

Example scripts demonstrating pixdot usage patterns for AI assistants and terminal-based development.

## CLI Tool

The `pixdot` command is the recommended way to render images:

```bash
pip install pixdot[cli]

# Basic usage
pixdot photo.jpg

# With options
pixdot photo.jpg -w 120 --dither --contrast

# Adjust for terminal cell aspect ratio
pixdot photo.jpg --cell-aspect 0.45

# Color modes
pixdot photo.jpg --color truecolor
pixdot photo.jpg --color grayscale
```

### Claude Code Integration

The `pixdot claude` subcommand manages a skill file that teaches Claude Code
how to use pixdot for visualizations. When installed, Claude Code can
automatically render matplotlib plots, numpy arrays, and images as braille
in the terminal.

```bash
# Install skill to ~/.claude/skills/pixdot/SKILL.md
pixdot claude install-skill

# View skill content (useful for customization)
pixdot claude show-skill

# Remove the skill
pixdot claude uninstall-skill
```

See `pixdot --help` for all options.

## Example Scripts

### graphing_calculator.py

Terminal graphing calculator for plotting mathematical functions.

**Requirements:** matplotlib

```bash
pip install matplotlib
python graphing_calculator.py
```

Functions available:
- `plot_function(expr, domain)` - Plot any expression using 'x'
- `plot_multiple(expressions)` - Compare multiple functions
- `plot_parametric(x_expr, y_expr)` - Parametric curves
- `quick_plot(expr)` - One-liner for instant plots

Example:
```python
from examples.graphing_calculator import plot_function
print(plot_function("np.sin(x) * np.exp(-x/10)", domain=(0, 30)))
```

### stats_dashboard.py

Statistical visualization toolkit for data analysis.

**Requirements:** matplotlib

```bash
pip install matplotlib
python stats_dashboard.py
```

Functions available:
- `histogram(data)` - Distribution visualization
- `boxplot_compare(datasets)` - Compare distributions
- `scatter_with_fit(x, y)` - Scatter with regression
- `correlation_matrix(data)` - Correlation heatmap
- `time_series(data)` - Time series with trend
- `quick_stats(data)` - Summary stats + histogram

Example:
```python
from examples.stats_dashboard import histogram
import numpy as np
print(histogram(np.random.normal(0, 1, 1000)))
```

### ai_recipes.py

Ready-to-copy recipes for Claude Code sessions. Each recipe is self-contained and produces immediate output.

**Requirements:** matplotlib (for most recipes)

```bash
python ai_recipes.py              # Run all demos
python ai_recipes.py --list       # List available recipes
python ai_recipes.py --recipe 1   # Run specific recipe
```

Recipes include:
1. Function plotting
2. Histograms
3. Scatter with regression
4. Bar charts
5. Time series
6. Multiple lines
7. Subplot grids
8. Heatmaps
9. Box-and-whisker plots
10. Direct array rendering (no matplotlib)
11. Image display
12. Sparklines

### realtime_monitor.py

Live data visualization and monitoring with sparklines.

**Requirements:** matplotlib

```bash
python realtime_monitor.py
python realtime_monitor.py --demo sparkline
python realtime_monitor.py --demo animated --duration 30
```

Functions available:
- `sparkline(data)` - Compact inline charts
- `sparkline_row(data, label)` - Labeled sparkline with value
- `live_chart(data)` - Full chart for streaming data
- `multi_metric_dashboard(metrics)` - Multiple metrics view

### framebuffer_demo.py

Using pixdot as a framebuffer target with pure numpy drawing primitives.

**Requirements:** None (uses only pixdot core)

```bash
python framebuffer_demo.py
```

Drawing functions:
- `draw_circle(fb, cx, cy, r)` - Circles (filled or outline)
- `draw_line(fb, x0, y0, x1, y1)` - Lines (Bresenham's algorithm)
- `draw_rect(fb, x, y, w, h)` - Rectangles

## Quick Start for Claude Code

### Plot a Function

```python
from pixdot.adapters import figure_to_braille
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
x = np.linspace(-10, 10, 500)
ax.plot(x, np.sin(x), 'k-', linewidth=3)
ax.grid(True)
print(figure_to_braille(fig, "dark_terminal"))
plt.close()
```

### Visualize Data

```python
from pixdot.adapters import figure_to_braille
import matplotlib.pyplot as plt
import numpy as np

data = np.random.normal(0, 1, 1000)
fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
ax.hist(data, bins=30, color='black')
print(figure_to_braille(fig, "dark_terminal"))
plt.close()
```

### Direct Array to Braille

```python
from pixdot import render
import numpy as np

bitmap = np.zeros((80, 160), dtype=np.float32)
# Draw something...
y, x = np.ogrid[:80, :160]
bitmap[(x - 80)**2 + (y - 40)**2 < 900] = 1.0
print(render(bitmap))
```

## Tips

- **Use thick lines**: `linewidth=3` or higher for visibility in braille
- **High DPI**: Use `dpi=150` or higher to preserve detail
- **Strong contrast**: Black lines on white background work best
- **Dithering**: Use `--dither` or `floyd_steinberg()` for photographs
- **Cell aspect**: If images look stretched, adjust `--cell-aspect` (default: 0.5)
- **Presets**: Use `"dark_terminal"` for dark backgrounds, `"light_terminal"` for light
