"""Claude Code integration commands.

Provides commands for installing pixdot as a Claude Code skill,
making it easy for Claude to render visualizations in the terminal.

Usage:
    pixdot claude install-skill    Install skill to ~/.claude/skills/pixdot/
    pixdot claude show-skill       Print skill content to stdout
"""

from __future__ import annotations

import sys
from pathlib import Path

# The skill content that teaches Claude Code how to use pixdot
SKILL_CONTENT = '''# pixdot - Terminal Visualization for AI Assistants

pixdot renders graphics in the terminal using Unicode braille characters.
Each braille character encodes a 2x4 dot pattern, giving 8x the resolution
of regular characters.

## When to Use pixdot

- Visualize mathematical functions and data
- Display charts, plots, and histograms
- Show images in the terminal
- Quick data exploration without leaving the terminal

## Quick Reference

### Pattern 1: Matplotlib Figure to Terminal

```python
from pixdot.adapters import figure_to_braille
import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
x = np.linspace(0, 10, 200)
ax.plot(x, np.sin(x), 'k-', linewidth=3)
ax.set_title("sin(x)")
ax.grid(True)
print(figure_to_braille(fig, "dark_terminal"))
plt.close()
```

### Pattern 2: Direct Array Rendering

```python
from pixdot.adapters import array_to_braille
import numpy as np

# Any 2D array with values 0.0-1.0
data = np.random.rand(100, 200).astype(np.float32)
print(array_to_braille(data, "dark_terminal"))
```

### Pattern 3: Load and Display Image

```python
from pixdot.adapters import load_and_render

print(load_and_render("image.png", "dark_terminal"))
# For color output:
print(load_and_render("image.png", "truecolor"))
```

## Available Presets

| Preset | Description |
|--------|-------------|
| `dark_terminal` | Inverted for dark backgrounds (default) |
| `light_terminal` | No inversion for light backgrounds |
| `high_detail` | 120 chars wide, more detail |
| `compact` | 40 chars wide, smaller output |
| `grayscale` | 24-level ANSI grayscale |
| `truecolor` | Full 24-bit RGB color |

## Common Patterns

### Plot a Function

```python
from pixdot.adapters import figure_to_braille
import matplotlib.pyplot as plt
import numpy as np

def plot_function(func, domain=(-10, 10), title=None):
    """Plot a mathematical function.

    Args:
        func: Callable that takes numpy array x and returns y values.
        domain: Tuple of (x_min, x_max).
        title: Optional plot title.
    """
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    x = np.linspace(domain[0], domain[1], 500)
    y = func(x)
    ax.plot(x, y, 'k-', linewidth=3)
    if title:
        ax.set_title(title, fontweight='bold')
    ax.grid(True, alpha=0.5)
    ax.axhline(0, color='k', lw=0.5)
    ax.axvline(0, color='k', lw=0.5)
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result

# Examples using lambda for concise function definitions:
print(plot_function(np.sin, title="Sine Wave"))
print(plot_function(lambda x: x**2 - 4, domain=(-5, 5), title="Parabola"))
print(plot_function(lambda x: np.exp(-x**2), domain=(-3, 3), title="Gaussian"))
```

### Histogram

```python
from pixdot.adapters import figure_to_braille
import matplotlib.pyplot as plt
import numpy as np

def histogram(data, bins=30, title="Distribution"):
    """Render histogram of data."""
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.hist(data, bins=bins, color='black', edgecolor='white')
    ax.set_title(title, fontweight='bold')
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result

# Example:
data = np.random.normal(0, 1, 1000)
print(histogram(data, title="Normal Distribution"))
```

### Scatter Plot with Trend Line

```python
from pixdot.adapters import figure_to_braille
import matplotlib.pyplot as plt
import numpy as np

def scatter_with_fit(x, y, title=""):
    """Scatter plot with linear regression line."""
    fig, ax = plt.subplots(figsize=(10, 5), dpi=150)
    ax.scatter(x, y, c='black', s=40, alpha=0.6)

    # Add trend line
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    ax.plot(x, p(x), 'k-', linewidth=2, label=f'y = {z[0]:.2f}x + {z[1]:.2f}')

    ax.legend()
    if title:
        ax.set_title(title, fontweight='bold')
    ax.grid(True, alpha=0.3)
    result = figure_to_braille(fig, "dark_terminal")
    plt.close()
    return result

# Example:
x = np.random.rand(50) * 10
y = 2 * x + 3 + np.random.randn(50) * 2
print(scatter_with_fit(x, y, "Linear Correlation"))
```

### Multiple Subplots

```python
from pixdot.adapters import figure_to_braille
import matplotlib.pyplot as plt
import numpy as np

fig, axes = plt.subplots(1, 3, figsize=(15, 4), dpi=150)

x = np.linspace(0, 2*np.pi, 200)
for ax, (func, name) in zip(axes, [(np.sin, 'sin'), (np.cos, 'cos'), (np.tan, 'tan')]):
    y = func(x)
    if name == 'tan':
        y = np.clip(y, -5, 5)  # Clip tan to avoid extremes
    ax.plot(x, y, 'k-', linewidth=3)
    ax.set_title(name, fontweight='bold')
    ax.grid(True)

plt.tight_layout()
print(figure_to_braille(fig, "dark_terminal"))
plt.close()
```

## Best Practices

1. **Use thick lines**: `linewidth=3` or higher for visibility
2. **High DPI**: Use `dpi=150` or higher to preserve detail
3. **Strong contrast**: Black lines on white background work best
4. **Appropriate figure size**: `figsize=(10, 5)` is a good default
5. **Grid lines help**: `ax.grid(True)` adds reference structure
6. **Close figures**: Always `plt.close()` after rendering to free memory

## CLI Usage

```bash
# Render an image
pixdot image.jpg

# With options
pixdot image.jpg -w 100 --dither --invert

# Color modes
pixdot image.jpg --color truecolor
pixdot image.jpg --color grayscale

# Adjust aspect ratio for your terminal
pixdot image.jpg --cell-aspect 0.45
```
'''


def install_skill(force: bool = False, path: str | None = None) -> int:
    """Install pixdot skill to ~/.claude/skills/pixdot/.

    Args:
        force: Overwrite existing skill file if present.
        path: Custom installation path. Defaults to ~/.claude/skills/pixdot/.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if path:
        skill_dir = Path(path)
    else:
        skill_dir = Path.home() / ".claude" / "skills" / "pixdot"

    skill_file = skill_dir / "SKILL.md"

    if skill_file.exists() and not force:
        print(f"Skill already installed at {skill_file}", file=sys.stderr)
        print("Use --force to overwrite.", file=sys.stderr)
        return 1

    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file.write_text(SKILL_CONTENT)
        print(f"Installed pixdot skill to {skill_file}")
        return 0
    except OSError as e:
        print(f"Error installing skill: {e}", file=sys.stderr)
        return 1


def show_skill() -> int:
    """Print skill content to stdout.

    Returns:
        Exit code (always 0).
    """
    print(SKILL_CONTENT)
    return 0


def uninstall_skill(path: str | None = None) -> int:
    """Uninstall pixdot skill from ~/.claude/skills/pixdot/.

    Args:
        path: Custom installation path. Defaults to ~/.claude/skills/pixdot/.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    if path:
        skill_dir = Path(path)
    else:
        skill_dir = Path.home() / ".claude" / "skills" / "pixdot"

    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        print(f"Skill not installed at {skill_file}", file=sys.stderr)
        return 1

    try:
        skill_file.unlink()
        # Try to remove the directory if empty
        try:
            skill_dir.rmdir()
        except OSError:
            pass  # Directory not empty, that's fine
        print(f"Uninstalled pixdot skill from {skill_file}")
        return 0
    except OSError as e:
        print(f"Error uninstalling skill: {e}", file=sys.stderr)
        return 1


def claude_main(argv: list[str] | None = None) -> int:
    """Main entry point for the claude subcommand."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="pixdot claude",
        description="Claude Code integration commands",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # install-skill command
    install_parser = subparsers.add_parser(
        "install-skill",
        help="Install pixdot skill to ~/.claude/skills/pixdot/",
    )
    install_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing skill file",
    )
    install_parser.add_argument(
        "--path",
        help="Custom installation path",
    )

    # show-skill command
    subparsers.add_parser(
        "show-skill",
        help="Print skill content to stdout",
    )

    # uninstall-skill command
    uninstall_parser = subparsers.add_parser(
        "uninstall-skill",
        help="Uninstall pixdot skill",
    )
    uninstall_parser.add_argument(
        "--path",
        help="Custom installation path",
    )

    args = parser.parse_args(argv)

    if args.command == "install-skill":
        return install_skill(force=args.force, path=args.path)
    elif args.command == "show-skill":
        return show_skill()
    elif args.command == "uninstall-skill":
        return uninstall_skill(path=args.path)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(claude_main())
