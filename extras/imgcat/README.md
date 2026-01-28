# imgcat

Terminal image viewer built on [dapple](https://github.com/spinoza/dapple).

## Installation

```bash
pip install dapple[imgcat]
# or standalone
pip install imgcat
```

## Usage

### Command Line

```bash
# Auto-detect best renderer for your terminal
imgcat photo.jpg

# Force a specific renderer
imgcat -r braille photo.jpg
imgcat -r quadrants photo.jpg
imgcat -r sixel photo.jpg      # If your terminal supports sixel
imgcat -r kitty photo.jpg      # For Kitty/Ghostty terminals

# Image processing options
imgcat --dither photo.jpg      # Apply Floyd-Steinberg dithering
imgcat --contrast photo.jpg    # Apply auto-contrast
imgcat --invert photo.jpg      # Invert colors

# Size control
imgcat -w 60 photo.jpg         # Set width to 60 characters
imgcat -H 30 photo.jpg         # Set height to 30 characters

# Output options
imgcat --grayscale photo.jpg   # Force grayscale
imgcat --no-color photo.jpg    # Pure ASCII (for pipes)
imgcat -o output.txt photo.jpg # Save to file
```

### Available Renderers

| Renderer | Description | Best For |
|----------|-------------|----------|
| `auto` | Auto-detect best renderer | Default |
| `kitty` | Kitty graphics protocol | Kitty, Ghostty terminals |
| `sixel` | Sixel graphics | mlterm, foot, wezterm |
| `quadrants` | Unicode blocks (color) | Most modern terminals |
| `sextants` | Unicode sextants | Higher resolution text |
| `braille` | Braille patterns | Monochrome, high detail |
| `ascii` | Pure ASCII | Universal compatibility |
| `fingerprint` | Glyph matching | Artistic output |

### Python API

```python
from imgcat import view, imgcat

# Quick view with defaults
view("photo.jpg")

# With options
imgcat("photo.jpg", renderer="braille", dither=True)

# Custom width
imgcat("photo.jpg", width=80, contrast=True)
```

## Terminal Support

imgcat auto-detects your terminal's capabilities:

- **Kitty/Ghostty**: Uses native Kitty graphics protocol
- **Sixel terminals**: Uses sixel graphics (mlterm, foot, wezterm)
- **Other terminals**: Falls back to Unicode quadrants or braille

## License

MIT
