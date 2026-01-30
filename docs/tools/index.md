# CLI Tools

dapple ships a suite of terminal-native CLI tools as extras. Each tool is
installed individually or all at once, and each one renders output through
dapple's pluggable renderer system.

## Installation

Install all tools:

```bash
pip install dapple[all-tools]
```

Or install individually:

```bash
pip install dapple[imgcat]
pip install dapple[vidcat]
pip install dapple[pdfcat]
pip install dapple[mdcat]
pip install dapple[funcat]
pip install dapple[csvcat]
pip install dapple[datacat]
pip install dapple[vizlib]
```

## Shared Conventions

All CLI tools that produce graphical output share a common set of flags for
renderer selection and image preprocessing:

| Flag | Meaning |
|------|---------|
| `-r` / `--renderer` | Output format: `braille`, `quadrants`, `sextants`, `ascii`, `sixel`, `kitty`, `fingerprint`, or `auto` |
| `-w` / `--width` | Output width in terminal columns |
| `-H` / `--height` | Output height in terminal rows |
| `--dither` | Apply Floyd-Steinberg dithering |
| `--contrast` | Apply auto-contrast stretching |
| `--invert` | Invert brightness values |
| `--grayscale` | Force grayscale output |
| `--no-color` | Disable color output entirely |
| `-o` / `--output` | Write output to a file instead of stdout |

When `-r auto` is specified (the default for most tools), dapple detects the
terminal's capabilities and selects the best available renderer in this order:
kitty > sixel > quadrants > braille > ascii.

## Tools by Category

### Viewers

These tools bring existing content into the terminal:

- **[imgcat](imgcat.md)** -- Display images (JPEG, PNG, WebP, BMP, TIFF, etc.)
  in the terminal with automatic renderer detection.

- **[vidcat](vidcat.md)** -- Extract and display video frames as terminal art.
  Supports asciinema export for sharing recordings.

- **[pdfcat](pdfcat.md)** -- Render PDF pages in the terminal. Page selection,
  DPI control, and all standard preprocessing flags.

- **[mdcat](mdcat.md)** -- Render markdown documents with Rich formatting and
  inline image rendering via dapple.

### Creators

These tools produce new visual output from data or expressions:

- **[funcat](funcat.md)** -- Plot mathematical functions (`sin(x)`, `x**2`,
  parametric curves) in the terminal. Supports pipeline chaining via JSON.

### Data Visualization

These tools visualize structured data:

- **[csvcat](csvcat.md)** -- View and chart CSV/TSV files. Table display with
  sorting and filtering, plus sparkline, bar chart, histogram, and heatmap
  modes.

- **[datacat](datacat.md)** -- View JSON/JSONL data with tree, table, and
  colored-JSON display modes. Includes chart visualization for numeric fields.

- **[vizlib](vizlib.md)** -- Programmatic chart primitives (sparkline, bar
  chart, histogram, heatmap, line plot) as a Python library. Used internally
  by csvcat and datacat.
