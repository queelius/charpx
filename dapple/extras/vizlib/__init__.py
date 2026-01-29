"""vizlib - Terminal chart primitives using dapple.

Provides sparklines, bar charts, line plots, histograms, and heatmaps
that render as dapple Canvas objects for display with any renderer.
"""

from dapple.extras.vizlib.charts import bar_chart, heatmap, histogram, line_plot, sparkline
from dapple.extras.vizlib.colors import COLOR_PALETTE, NAMED_COLORS, parse_color
from dapple.extras.vizlib.render import get_renderer, get_terminal_size, pixel_dimensions

__all__ = [
    "sparkline",
    "bar_chart",
    "line_plot",
    "histogram",
    "heatmap",
    "get_renderer",
    "get_terminal_size",
    "pixel_dimensions",
    "parse_color",
    "NAMED_COLORS",
    "COLOR_PALETTE",
]
