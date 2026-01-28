# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

pdfcat is a terminal PDF viewer built on dapple. It renders PDF pages as images in the terminal using various dapple renderers (braille, quadrants, sixel, kitty, etc.).

This is a small CLI tool in the `extras/` directory of the dapple project. For dapple-specific details (renderers, canvas API, preprocessing), see the parent project's CLAUDE.md at `/home/spinoza/github/beta/dapple/CLAUDE.md`.

## Commands

```bash
# Install in development mode
pip install -e "."

# Run the CLI
pdfcat document.pdf
pdfcat -r braille --pages 1-3 document.pdf

# Use Python API
python -c "from pdfcat import view; view('document.pdf')"

# Install Claude Code skill
pdfcat --skill-install --global
pdfcat --skill-install --local   # Project-local
pdfcat --skill-show              # Display skill content
```

## Architecture

Single-module design in `pdfcat/pdfcat.py`:

- **`PdfcatOptions`**: Dataclass holding all rendering options
- **`render_pdf_to_images()`**: Uses pypdfium2 to convert PDF pages to temporary PNG files
- **`pdfcat()`**: Main function that orchestrates the full pipeline
- **`get_renderer()`**: Maps renderer names to dapple renderer instances with appropriate options
- **`parse_page_range()`**: Parses page range strings like "1-3,5,7-9"

The flow is:
```
PDF → pypdfium2 → PIL Image → resize/aspect correction
    → dapple Canvas → preprocessing (contrast/dither/invert)
    → renderer → stdout
```

The kitty renderer is handled specially: it uses the `columns` parameter for display scaling rather than pre-resizing the image.

## Dependencies

- **dapple**: Parent library providing Canvas and all renderers
- **pypdfium2**: PDF rendering to images
- **pillow**: Image manipulation

## Key Notes

- No tests currently exist for this module
- The `SKILL_CONTENT` constant contains a Claude Code skill for terminal PDF viewing
- Temporary files are managed via `RenderResult` and cleaned up in a `finally` block
