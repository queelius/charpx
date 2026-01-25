# mdcat

Terminal markdown viewer with inline images built on [charpx](https://github.com/spinoza/charpx) and [Rich](https://github.com/Textualize/rich).

## Installation

```bash
pip install charpx[mdcat]
# or standalone
pip install mdcat
```

## Usage

### Command Line

```bash
# View a markdown file
mdcat README.md

# Control image rendering
mdcat README.md                  # With inline images
mdcat --no-images README.md      # Skip images

# Use specific renderer for images
mdcat -r braille README.md
mdcat -r quadrants README.md
mdcat -r sixel README.md
mdcat -r kitty README.md

# Control width
mdcat -w 80 README.md            # Console width
mdcat --image-width 60 README.md # Image width

# Code highlighting
mdcat --code-theme dracula README.md
mdcat --code-theme monokai README.md

# Output options
mdcat --no-hyperlinks README.md  # Disable links
mdcat -o output.txt README.md    # Save to file
```

### Claude Code Skill

Install the skill to help Claude Code use mdcat:

```bash
# Install to current project
mdcat skill --install --local

# Install globally
mdcat skill --install --global

# Show skill content
mdcat skill --show
```

### Python API

```python
from mdcat import view, mdcat

# Quick view with defaults
view("README.md")

# With options
mdcat("README.md", renderer="braille", render_images=True)

# Custom theme
mdcat("README.md", code_theme="dracula", width=100)
```

## Features

- **Rich markdown rendering**: Headers, lists, code blocks, tables
- **Inline images**: Renders images using charpx (braille, quadrants, sixel, kitty)
- **Syntax highlighting**: Code blocks with Pygments themes
- **Hyperlinks**: Clickable links in supported terminals
- **Image caching**: Downloads cached for faster re-rendering

## Requirements

- Python 3.10+
- charpx
- pillow
- rich

## License

MIT
