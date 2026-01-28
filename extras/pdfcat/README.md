# pdfcat

Terminal PDF viewer built on [dapple](https://github.com/spinoza/dapple).

## Installation

```bash
pip install dapple[pdfcat]
# or standalone
pip install pdfcat
```

## Usage

### Command Line

```bash
# View a PDF (auto-detects best renderer)
pdfcat document.pdf

# View specific pages
pdfcat --pages 1-3 document.pdf
pdfcat --pages "1,3,5" document.pdf

# Force a specific renderer
pdfcat -r braille document.pdf
pdfcat -r quadrants document.pdf
pdfcat -r sixel document.pdf
pdfcat -r kitty document.pdf

# Image processing options
pdfcat --dither document.pdf      # Floyd-Steinberg dithering
pdfcat --contrast document.pdf    # Auto-contrast
pdfcat --invert document.pdf      # Invert colors

# Control quality
pdfcat --dpi 300 document.pdf     # Higher resolution
pdfcat -w 60 document.pdf         # Limit width

# Output options
pdfcat --grayscale document.pdf   # Force grayscale
pdfcat --no-color document.pdf    # Pure ASCII
pdfcat -o output.txt document.pdf # Save to file
```

### Claude Code Skill

Install the skill to help Claude Code use pdfcat:

```bash
# Install to current project
pdfcat --skill-install --local

# Install globally
pdfcat --skill-install --global

# Show skill content
pdfcat --skill-show
```

### Python API

```python
from pdfcat import view, pdfcat

# Quick view with defaults
view("document.pdf")

# With options
pdfcat("document.pdf", pages="1-3", renderer="braille", dither=True)

# Custom DPI
pdfcat("document.pdf", dpi=300, contrast=True)
```

## Requirements

- Python 3.10+
- dapple
- pillow
- pypdfium2

## License

MIT
