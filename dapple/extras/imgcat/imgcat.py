"""imgcat - Terminal image viewer.

Core implementation for rendering images to the terminal using dapple.
"""

from __future__ import annotations

import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from dapple.renderers import Renderer


@dataclass
class ImgcatOptions:
    """Options for image rendering.

    Attributes:
        renderer: Renderer name or instance ("auto", "braille", "quadrants", etc.)
        width: Output width in characters (None = terminal width)
        height: Output height in characters (None = auto)
        dither: Apply Floyd-Steinberg dithering
        contrast: Apply auto-contrast
        invert: Invert colors
        grayscale: Force grayscale output
        no_color: Disable color output entirely
    """
    renderer: str = "auto"
    width: int | None = None
    height: int | None = None
    dither: bool = False
    contrast: bool = False
    invert: bool = False
    grayscale: bool = False
    no_color: bool = False


def get_renderer(name: str, options: ImgcatOptions) -> Renderer:
    """Get a renderer by name with appropriate configuration.

    Args:
        name: Renderer name ("auto", "braille", "quadrants", etc.)
        options: ImgcatOptions for configuration

    Returns:
        Configured Renderer instance
    """
    from dapple import (
        ascii,
        braille,
        fingerprint,
        kitty,
        quadrants,
        sextants,
        sixel,
    )
    from dapple.auto import auto_renderer

    if name == "auto":
        return auto_renderer(
            prefer_color=not options.grayscale,
            plain=options.no_color,
        )

    # Base renderers
    renderers = {
        "braille": braille,
        "quadrants": quadrants,
        "sextants": sextants,
        "ascii": ascii,
        "sixel": sixel,
        "kitty": kitty,
        "fingerprint": fingerprint,
    }

    renderer = renderers.get(name)
    if renderer is None:
        raise ValueError(f"Unknown renderer: {name}")

    # Configure renderer based on options
    if name == "braille":
        if options.no_color:
            renderer = braille(color_mode="none")
        elif options.grayscale:
            renderer = braille(color_mode="grayscale")
        else:
            renderer = braille(color_mode="truecolor")
    elif name in ("quadrants", "sextants"):
        if options.grayscale:
            if name == "quadrants":
                renderer = quadrants(grayscale=True)
            else:
                renderer = sextants(grayscale=True)

    return renderer


def imgcat(
    image_path: str | Path,
    *,
    renderer: str = "auto",
    width: int | None = None,
    height: int | None = None,
    dither: bool = False,
    contrast: bool = False,
    invert: bool = False,
    grayscale: bool = False,
    no_color: bool = False,
    dest: TextIO | None = None,
) -> None:
    """Render an image to the terminal.

    Args:
        image_path: Path to the image file.
        renderer: Renderer name ("auto", "braille", "quadrants", etc.)
        width: Output width in characters (None = terminal width)
        height: Output height in characters (None = auto)
        dither: Apply Floyd-Steinberg dithering
        contrast: Apply auto-contrast
        invert: Invert colors
        grayscale: Force grayscale output
        no_color: Disable color output entirely
        dest: Output stream (default: stdout)

    Example:
        >>> imgcat("photo.jpg")  # Auto-detect and render
        >>> imgcat("photo.jpg", renderer="braille", dither=True)
    """
    try:
        from PIL import Image
        from dapple.adapters.pil import from_pil, load_image
    except ImportError:
        raise ImportError(
            "PIL is required for imgcat. Install with: pip install dapple[imgcat]"
        )

    from dapple import auto_contrast as ac, floyd_steinberg, invert as inv
    from dapple.canvas import Canvas

    options = ImgcatOptions(
        renderer=renderer,
        width=width,
        height=height,
        dither=dither,
        contrast=contrast,
        invert=invert,
        grayscale=grayscale,
        no_color=no_color,
    )

    # Get renderer
    rend = get_renderer(renderer, options)

    # Determine output width
    if width:
        char_width = width
    else:
        terminal_size = shutil.get_terminal_size(fallback=(80, 24))
        char_width = terminal_size.columns

    # Calculate pixel dimensions
    CELL_PIXEL_WIDTH = 8
    if renderer in ("sixel", "kitty"):
        pixel_width = char_width * CELL_PIXEL_WIDTH
    else:
        pixel_width = char_width * rend.cell_width
    pixel_height = height * rend.cell_height if height else None

    # Load image
    path = Path(image_path)
    canvas = load_image(path, width=pixel_width, height=pixel_height)

    # Correct aspect ratio for character-based renderers
    TERMINAL_CELL_RATIO = 0.5
    if renderer not in ("sixel", "kitty", "auto"):
        cell_aspect = (rend.cell_height / rend.cell_width) * TERMINAL_CELL_RATIO
        pil_img = canvas.to_pil()
        w, h = pil_img.size
        new_h = int(h * cell_aspect)
        if new_h > 0:
            pil_img = pil_img.resize((w, new_h), Image.Resampling.LANCZOS)
            canvas = from_pil(pil_img)
    elif renderer == "auto":
        # For auto, we need to check the actual renderer type
        from dapple.auto import detect_terminal, Protocol
        info = detect_terminal()
        if info.protocol not in (Protocol.KITTY, Protocol.SIXEL):
            cell_aspect = (rend.cell_height / rend.cell_width) * TERMINAL_CELL_RATIO
            pil_img = canvas.to_pil()
            w, h = pil_img.size
            new_h = int(h * cell_aspect)
            if new_h > 0:
                pil_img = pil_img.resize((w, new_h), Image.Resampling.LANCZOS)
                canvas = from_pil(pil_img)

    # Apply preprocessing
    bitmap = canvas.bitmap.copy()
    bitmap.flags.writeable = True

    if contrast:
        bitmap = ac(bitmap)
    if dither:
        bitmap = floyd_steinberg(bitmap)
    if invert:
        bitmap = inv(bitmap)

    # Recreate canvas if preprocessing was applied
    if contrast or dither or invert:
        canvas = Canvas(bitmap, colors=canvas.colors)

    # Output
    output = dest if dest is not None else sys.stdout
    colors_to_use = None if no_color else canvas._colors
    rend.render(canvas._bitmap, colors_to_use, dest=output)
    output.write("\n")


def view(image_path: str | Path, **kwargs) -> None:
    """Quick view of an image with default settings.

    Alias for imgcat() with default options.

    Args:
        image_path: Path to the image file.
        **kwargs: Additional options passed to imgcat().

    Example:
        >>> view("photo.jpg")
    """
    imgcat(image_path, **kwargs)


# Claude Code skill content
SKILL_CONTENT = '''# imgcat - Terminal Image Viewer

imgcat displays images in the terminal using dapple renderers.

## Usage

```bash
# View an image (auto-detects best renderer)
imgcat photo.jpg

# View multiple images
imgcat *.png

# Use a specific renderer
imgcat -r braille photo.jpg    # High detail, works everywhere
imgcat -r quadrants photo.jpg  # Color blocks
imgcat -r sixel photo.jpg      # True pixels (if supported)
imgcat -r kitty photo.jpg      # For Kitty/Ghostty

# Image processing
imgcat --dither photo.jpg      # Dithering for better gradients
imgcat --contrast photo.jpg    # Enhance contrast
imgcat --invert photo.jpg      # Invert colors

# Size control
imgcat -w 60 photo.jpg         # Limit width to 60 chars
imgcat -H 30 photo.jpg         # Limit height
```

## When to Use

Use imgcat when you need to:
- Show images to the user in the terminal
- Preview image files visually
- Display generated plots or diagrams
- Verify image content

## Python API

```python
from dapple.extras.imgcat import view, imgcat

# Quick view
view("photo.jpg")

# With options
imgcat("photo.jpg", renderer="braille", dither=True, width=80)
```

## Renderers

| Renderer | Best For |
|----------|----------|
| auto | Auto-detect best for terminal |
| kitty | Kitty/Ghostty terminals |
| sixel | mlterm, foot, wezterm |
| quadrants | Color output, most terminals |
| braille | Detailed monochrome |
| ascii | Universal compatibility |
'''


def skill_install(local: bool = False, global_: bool = False) -> bool:
    """Install the imgcat skill for Claude Code.

    Args:
        local: Install to current project (.claude/skills/)
        global_: Install globally (~/.claude/skills/)

    Returns:
        True if successful
    """
    if local:
        skill_dir = Path.cwd() / ".claude" / "skills"
    elif global_:
        skill_dir = Path.home() / ".claude" / "skills"
    else:
        print("Error: Specify --local or --global", file=sys.stderr)
        return False

    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skill_dir / "imgcat.md"
    skill_file.write_text(SKILL_CONTENT)
    print(f"Installed skill to: {skill_file}")
    return True


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="imgcat",
        description="Display images in the terminal using dapple",
    )

    # Main arguments first
    parser.add_argument(
        "images", type=Path, nargs="*", help="Image file(s) to display"
    )
    parser.add_argument(
        "-r",
        "--renderer",
        choices=[
            "auto",
            "braille",
            "quadrants",
            "sextants",
            "ascii",
            "sixel",
            "kitty",
            "fingerprint",
        ],
        default="auto",
        help="Renderer to use (default: auto)",
    )
    parser.add_argument(
        "-w", "--width", type=int,
        help="Output width in characters (default: terminal width)"
    )
    parser.add_argument("-H", "--height", type=int, help="Output height in characters")
    parser.add_argument(
        "--dither", action="store_true", help="Apply Floyd-Steinberg dithering"
    )
    parser.add_argument(
        "--contrast", action="store_true", help="Apply auto-contrast"
    )
    parser.add_argument("--invert", action="store_true", help="Invert colors")
    parser.add_argument(
        "-o", "--output", type=Path, help="Output file (default: stdout)"
    )
    parser.add_argument(
        "--grayscale", action="store_true",
        help="Force grayscale output"
    )
    parser.add_argument(
        "--no-color", action="store_true",
        help="Disable color output"
    )

    # Skill management options (as flags instead of subcommand)
    parser.add_argument(
        "--skill-install", action="store_true",
        help="Install Claude Code skill"
    )
    parser.add_argument(
        "--skill-show", action="store_true",
        help="Show Claude Code skill content"
    )
    parser.add_argument(
        "--local", action="store_true",
        help="Install skill to current project (use with --skill-install)"
    )
    parser.add_argument(
        "--global", dest="global_", action="store_true",
        help="Install skill globally (use with --skill-install)"
    )

    args = parser.parse_args()

    # Handle skill options
    if args.skill_show:
        print(SKILL_CONTENT)
        return
    if args.skill_install:
        success = skill_install(local=args.local, global_=args.global_)
        sys.exit(0 if success else 1)

    # Main command
    if not args.images:
        parser.print_help()
        sys.exit(1)

    # Determine output destination
    if args.output:
        dest = open(args.output, "w", encoding="utf-8")
    else:
        dest = sys.stdout

    try:
        for image_path in args.images:
            if not image_path.exists():
                print(f"Error: File not found: {image_path}", file=sys.stderr)
                sys.exit(1)

            imgcat(
                image_path,
                renderer=args.renderer,
                width=args.width,
                height=args.height,
                dither=args.dither,
                contrast=args.contrast,
                invert=args.invert,
                grayscale=args.grayscale,
                no_color=args.no_color,
                dest=dest,
            )
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
    finally:
        if args.output:
            dest.close()


if __name__ == "__main__":
    main()
