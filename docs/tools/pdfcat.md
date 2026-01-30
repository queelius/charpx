# pdfcat -- Terminal PDF Viewer

Render PDF pages as terminal graphics using dapple renderers.

## Installation

```bash
pip install dapple[pdfcat]
```

This installs Pillow and pypdfium2 as dependencies. pypdfium2 provides fast,
high-quality PDF rendering without requiring external tools like Ghostscript
or poppler.

## Usage

### Basic

```bash
# View all pages of a PDF
pdfcat document.pdf

# Output includes a header with filename and page count
```

### Page Selection

```bash
# View a specific page
pdfcat -p 3 document.pdf

# View a page range
pdfcat -p 1-5 document.pdf

# View specific pages
pdfcat -p "1,3,7" document.pdf

# Combine ranges and individual pages
pdfcat -p "1-3,7,10-12" document.pdf
```

### Renderer Selection

```bash
pdfcat -r braille document.pdf        # High detail, works everywhere
pdfcat -r quadrants document.pdf      # Color blocks
pdfcat -r sextants document.pdf       # Higher resolution blocks
pdfcat -r ascii document.pdf          # Universal ASCII art
pdfcat -r sixel document.pdf          # True pixel (xterm, mlterm, foot)
pdfcat -r kitty document.pdf          # True pixel (Kitty, WezTerm, Ghostty)
pdfcat -r fingerprint document.pdf    # Glyph matching
```

### DPI Control

```bash
# Higher DPI for finer detail (default: 150)
pdfcat --dpi 300 document.pdf

# Lower DPI for faster rendering
pdfcat --dpi 72 document.pdf
```

### Preprocessing

```bash
pdfcat --contrast document.pdf        # Auto-contrast enhancement
pdfcat --dither document.pdf          # Floyd-Steinberg dithering
pdfcat --invert document.pdf          # Invert brightness (dark mode)

# Combine for best results on text-heavy PDFs
pdfcat --contrast --dither document.pdf
```

### Size and Color Control

```bash
# Set output width
pdfcat -w 120 document.pdf

# Set output height per page
pdfcat -H 50 document.pdf

# Grayscale or monochrome output
pdfcat --grayscale document.pdf
pdfcat --no-color document.pdf
```

### Output to File

```bash
pdfcat -o output.txt document.pdf
```

## Tips

**Text-heavy documents** render best with `braille` or `sextants` and
`--contrast`, which provide the detail needed to distinguish individual
characters at terminal scale:

```bash
pdfcat -r braille --contrast --dpi 200 paper.pdf
```

**Diagrams and figures** come through well with `quadrants` or `sextants`,
which preserve color information:

```bash
pdfcat -r quadrants slides.pdf
```

**Presentations and slides** work well at higher DPI with sixel or kitty
if your terminal supports them:

```bash
pdfcat -r sixel --dpi 200 slides.pdf
```

## Python API

```python
from dapple.extras.pdfcat import view, pdfcat

# Quick view
view("document.pdf")

# Full control
pdfcat(
    "document.pdf",
    renderer="braille",
    pages="1-3",
    dpi=200,
    contrast=True,
    dither=True,
    width=120,
)

# Render to a file
with open("output.txt", "w") as f:
    pdfcat("document.pdf", renderer="quadrants", dest=f)
```

## Entry Point

```
pdfcat = dapple.extras.pdfcat.pdfcat:main
```

## Reference

```
usage: pdfcat [-h] [-r {auto,braille,quadrants,sextants,ascii,sixel,kitty,fingerprint}]
              [-w WIDTH] [-H HEIGHT] [-p PAGES] [--dpi DPI] [--dither]
              [--contrast] [--invert] [-o OUTPUT] [--grayscale] [--no-color]
              [pdf]

Display PDF pages in the terminal using dapple

positional arguments:
  pdf                   PDF file to display

options:
  -r, --renderer        Renderer to use (default: auto)
  -w, --width           Output width in characters (default: terminal width)
  -H, --height          Output height in characters
  -p, --pages           Page range (e.g., "1-3", "5", "1,3,5")
  --dpi                 DPI for PDF rendering (default: 150)
  --dither              Apply Floyd-Steinberg dithering
  --contrast            Apply auto-contrast
  --invert              Invert colors
  -o, --output          Output file (default: stdout)
  --grayscale           Force grayscale output
  --no-color            Disable color output
```
