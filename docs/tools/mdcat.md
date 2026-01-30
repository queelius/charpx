# mdcat -- Terminal Markdown Viewer

Render markdown documents in the terminal with Rich formatting and inline
image rendering via dapple.

## Installation

```bash
pip install dapple[mdcat]
```

This installs Pillow (for image rendering) and Rich (for markdown formatting)
as dependencies.

## Usage

### Basic

```bash
# View a markdown file with formatting
mdcat README.md

# View any markdown document
mdcat CHANGELOG.md
mdcat docs/guide.md
```

### Image Rendering

By default, mdcat renders inline images found in the markdown using dapple.
Images can be local files or URLs (downloaded and cached automatically).

```bash
# Render with a specific renderer for images
mdcat -r braille README.md
mdcat -r quadrants README.md
mdcat -r kitty README.md

# Control image width separately from console width
mdcat --image-width 60 README.md

# Disable image rendering (text-only)
mdcat --no-images README.md
```

Images referenced by URL are downloaded and cached in `~/.cache/mdcat/` using
SHA256 hashing to avoid re-downloading.

### Width Control

```bash
# Set console width
mdcat -w 100 README.md

# Narrow width for focused reading
mdcat -w 72 README.md
```

### Code Theme

mdcat uses Pygments for syntax highlighting in code blocks:

```bash
# Default theme (monokai)
mdcat README.md

# Use a different Pygments theme
mdcat --code-theme dracula README.md
mdcat --code-theme github-dark README.md
mdcat --code-theme solarized-dark README.md
```

### Hyperlinks

```bash
# Disable clickable hyperlinks
mdcat --no-hyperlinks README.md
```

### Output to File

```bash
mdcat -o rendered.txt README.md
```

## Use Cases

**SSH/Remote preview** -- When working on a remote server without a browser,
mdcat provides a formatted view of markdown documentation with images rendered
inline:

```bash
ssh server 'cat project/README.md' | mdcat
```

**Documentation review** -- Preview markdown files as they would appear with
formatting, without leaving the terminal:

```bash
mdcat docs/*.md
```

**Presentations** -- Markdown files with embedded images can serve as simple
terminal-based presentations:

```bash
mdcat slides.md -r kitty --image-width 80
```

## Skill Subcommand

mdcat includes a built-in Claude Code skill that can be installed for AI
assistant integration:

```bash
# Show the skill content
mdcat skill --show

# Install locally to the current project
mdcat skill --install --local

# Install globally
mdcat skill --install --global
```

## Python API

```python
from dapple.extras.mdcat import view, mdcat

# Quick view with defaults
view("README.md")

# Full control
mdcat(
    "README.md",
    renderer="quadrants",
    width=100,
    image_width=60,
    render_images=True,
    code_theme="dracula",
)

# Render to a file
with open("output.txt", "w") as f:
    mdcat("README.md", renderer="braille", dest=f)
```

## Entry Point

```
mdcat = dapple.extras.mdcat.mdcat:main
```

## Reference

```
usage: mdcat [-h] [-r {auto,braille,quadrants,sextants,ascii,sixel,kitty}]
             [-w WIDTH] [--image-width IMAGE_WIDTH] [--no-images]
             [--code-theme CODE_THEME] [--no-hyperlinks] [-o OUTPUT]
             [file]

Display markdown files in the terminal with inline images

positional arguments:
  file                  Markdown file to display

options:
  -r, --renderer        Renderer for inline images (default: auto)
  -w, --width           Console width in characters (default: terminal width)
  --image-width         Image width in characters (default: console width)
  --no-images           Skip rendering inline images
  --code-theme          Pygments theme for code blocks (default: monokai)
  --no-hyperlinks       Disable clickable hyperlinks
  -o, --output          Output file (default: stdout)
```
