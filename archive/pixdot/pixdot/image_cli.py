#!/usr/bin/env python3
"""CLI for rendering images as braille.

Requires pillow for image loading. Install with:
    pip install pixdot[cli]

Usage:
    pixdot <image> [options]        Render image as braille (default)
    pixdot image <image> [options]  Explicit image command
    pixdot claude <command>         Claude Code integration
    pixdot --help                   Show help

Examples:
    pixdot photo.jpg              # Render with default settings
    pixdot photo.jpg -w 80        # Set width to 80 characters
    pixdot photo.jpg -t 0.4       # Adjust threshold
    pixdot photo.jpg --invert     # Invert for light terminals
    pixdot photo.jpg --dither     # Apply Floyd-Steinberg dithering
    pixdot photo.jpg --color grayscale  # 24-level grayscale
    pixdot photo.jpg --color truecolor  # Full 24-bit RGB color
    pixdot photo.jpg --cell-aspect 0.45 # Adjust for terminal cell ratio
    pixdot claude install-skill   # Install Claude Code skill
    pixdot claude show-skill      # Print skill content
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from pixdot import auto_contrast, floyd_steinberg, render, render_ansi

# Graceful PIL import - provide helpful error if missing
try:
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None  # type: ignore[misc,assignment]


def _check_pil() -> None:
    """Check if PIL is available, exit with helpful message if not."""
    if not PIL_AVAILABLE:
        print(
            "Error: Pillow is required for image loading.\n\n"
            "Install it with:\n"
            "    pip install pixdot[cli]\n"
            "or:\n"
            "    pip install pillow",
            file=sys.stderr,
        )
        sys.exit(1)


def _compute_braille_dimensions(
    orig_w: int,
    orig_h: int,
    width_chars: int,
    cell_aspect: float = 0.5,
) -> tuple[int, int]:
    """Compute braille-compatible target dimensions for image resizing.

    Args:
        orig_w: Original image width.
        orig_h: Original image height.
        width_chars: Target width in terminal characters.
        cell_aspect: Width/height ratio of terminal cell (typically 0.5).

    Returns:
        Tuple of (target_pixel_w, target_pixel_h) where height is divisible by 4.
    """
    aspect_ratio = orig_w / orig_h

    # For braille: each char is 2 pixels wide, 4 pixels tall
    pixels_per_char_w = 2
    target_pixel_w = width_chars * pixels_per_char_w
    target_pixel_h = int(target_pixel_w / aspect_ratio * cell_aspect)

    # Make height a multiple of 4 for braille
    target_pixel_h = max(4, (target_pixel_h // 4) * 4)

    return target_pixel_w, target_pixel_h


def load_image(
    path: str,
    width: int,
    cell_aspect: float = 0.5,
) -> np.ndarray:
    """Load image and convert to grayscale bitmap sized for terminal.

    Args:
        path: Path to image file
        width: Target width in terminal characters
        cell_aspect: Width/height ratio of terminal cell (typically 0.5)

    Returns:
        2D numpy array of shape (H, W), values 0.0-1.0
    """
    _check_pil()

    img = Image.open(path)
    img = img.convert('L')

    target_pixel_w, target_pixel_h = _compute_braille_dimensions(
        img.size[0], img.size[1], width, cell_aspect
    )

    img = img.resize((target_pixel_w, target_pixel_h), resample=Image.Resampling.LANCZOS)
    return np.array(img, dtype=np.float32) / 255.0


def load_image_with_color(
    path: str,
    width: int,
    cell_aspect: float = 0.5,
) -> tuple[np.ndarray, np.ndarray]:
    """Load image and return both grayscale and RGB bitmaps sized for terminal.

    Args:
        path: Path to image file
        width: Target width in terminal characters
        cell_aspect: Width/height ratio of terminal cell (typically 0.5)

    Returns:
        Tuple of (grayscale, colors):
        - grayscale: 2D numpy array of shape (H, W), values 0.0-1.0
        - colors: 3D numpy array of shape (H, W, 3), values 0.0-1.0 (RGB)
    """
    _check_pil()

    img = Image.open(path)
    rgb_img = img.convert('RGB')
    gray_img = img.convert('L')

    target_pixel_w, target_pixel_h = _compute_braille_dimensions(
        img.size[0], img.size[1], width, cell_aspect
    )

    gray_img = gray_img.resize(
        (target_pixel_w, target_pixel_h), resample=Image.Resampling.LANCZOS
    )
    rgb_img = rgb_img.resize(
        (target_pixel_w, target_pixel_h), resample=Image.Resampling.LANCZOS
    )

    grayscale = np.array(gray_img, dtype=np.float32) / 255.0
    colors = np.array(rgb_img, dtype=np.float32) / 255.0

    return grayscale, colors


def image_main(argv: list[str] | None = None) -> int:
    """Entry point for image rendering command."""
    parser = argparse.ArgumentParser(
        prog="pixdot",
        description="Convert images to Unicode braille art",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pixdot photo.jpg              # Render with default settings
  pixdot photo.jpg -w 80        # Set width to 80 characters
  pixdot photo.jpg -t 0.4       # Adjust threshold
  pixdot photo.jpg --invert     # Invert for light terminals
  pixdot photo.jpg --dither     # Apply Floyd-Steinberg dithering
  pixdot photo.jpg -o out.txt   # Save to file
  pixdot photo.jpg -c grayscale # 24-level grayscale color
  pixdot photo.jpg -c truecolor # Full 24-bit RGB color
  pixdot photo.jpg -c truecolor --invert  # Inverted for dark terminals
""",
    )

    parser.add_argument("image", help="Path to image file")
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=80,
        help="Output width in characters (default: 80)",
    )
    parser.add_argument(
        "-t", "--threshold",
        type=float,
        default=None,
        help="Brightness threshold for dots (default: auto-detect)",
    )
    parser.add_argument(
        "--dither",
        action="store_true",
        help="Apply Floyd-Steinberg dithering for better grayscale representation",
    )
    parser.add_argument(
        "--contrast",
        action="store_true",
        help="Apply auto-contrast before rendering",
    )
    parser.add_argument(
        "--invert",
        action="store_true",
        help="Invert image (for light terminal backgrounds)",
    )
    parser.add_argument(
        "-c", "--color",
        choices=["grayscale", "truecolor", "none"],
        default="none",
        help="Color mode: grayscale (24-level), truecolor (24-bit RGB), or none",
    )
    parser.add_argument(
        "--invert-colors",
        action="store_true",
        help="Invert colors only (photographic negative). For truecolor mode.",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file (default: stdout)",
    )
    parser.add_argument(
        "--cell-aspect",
        type=float,
        default=0.5,
        help="Terminal cell width/height ratio (default: 0.5 for 2:1 tall cells)",
    )

    args = parser.parse_args(argv)

    # Check PIL before doing anything with images
    _check_pil()

    if not Path(args.image).exists():
        print(f"Error: Image not found: {args.image}", file=sys.stderr)
        return 1

    # Load image with color if color mode is enabled
    colors = None
    if args.color != "none":
        try:
            bitmap, colors = load_image_with_color(
                args.image, args.width, cell_aspect=args.cell_aspect
            )
        except (OSError, IOError, ValueError) as e:
            print(f"Error loading image: {e}", file=sys.stderr)
            return 1
    else:
        try:
            bitmap = load_image(args.image, args.width, cell_aspect=args.cell_aspect)
        except (OSError, IOError, ValueError) as e:
            print(f"Error loading image: {e}", file=sys.stderr)
            return 1

    # Apply preprocessing
    if args.contrast:
        bitmap = auto_contrast(bitmap)

    # Handle inversion
    # --invert inverts both dots and colors when in color mode
    # --invert-colors inverts colors only (photographic negative)
    if args.invert:
        bitmap = 1.0 - bitmap

    invert_colors = args.invert_colors or args.invert
    if invert_colors and colors is not None and args.color == "truecolor":
        colors = 1.0 - colors

    # Render output
    if args.color != "none":
        # Color mode: skip dithering (color conveys intensity)
        result = render_ansi(
            bitmap,
            threshold=args.threshold,
            color_mode=args.color,
            colors=colors,
        )
    elif args.dither:
        # When dithering, use threshold=0.5 for the dithering step
        # then render with threshold=0.5 (dithered output is binary)
        dither_threshold = args.threshold if args.threshold is not None else 0.5
        bitmap = floyd_steinberg(bitmap, threshold=dither_threshold)
        # Dithered bitmap is already binary, use 0.5 threshold
        result = render(bitmap, threshold=0.5)
    else:
        # Without dithering, use None for auto-detect if not specified
        result = render(bitmap, threshold=args.threshold)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(result)
            f.write('\n')
        print(f"Output written to {args.output}")
    else:
        print(result)

    return 0


# Known subcommands for dispatch
SUBCOMMANDS = {"claude", "image"}


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI with subcommand support.

    Supports:
        pixdot <image>              # Backward compatible - render image
        pixdot image <image>        # Explicit image command
        pixdot claude <command>     # Claude Code integration

    The first argument is checked against known subcommands. If it doesn't
    match, it's treated as an image path (backward compatible behavior).
    """
    if argv is None:
        argv = sys.argv[1:]

    # Handle empty args or help
    if not argv or argv[0] in ("-h", "--help"):
        # Show combined help
        print("pixdot - Terminal graphics with Unicode braille")
        print()
        print("Usage:")
        print("  pixdot <image> [options]        Render image as braille")
        print("  pixdot image <image> [options]  Explicit image command")
        print("  pixdot claude <command>         Claude Code integration")
        print()
        print("Commands:")
        print("  image     Render an image as braille (default)")
        print("  claude    Claude Code skill management")
        print()
        print("Run 'pixdot <command> --help' for command-specific help.")
        print()
        print("Examples:")
        print("  pixdot photo.jpg                  Render image")
        print("  pixdot photo.jpg -w 100 --dither  With options")
        print("  pixdot claude install-skill       Install Claude skill")
        print("  pixdot claude show-skill          Show skill content")
        return 0

    first_arg = argv[0]

    # Check for subcommand dispatch
    if first_arg == "claude":
        from pixdot.claude_cli import claude_main
        return claude_main(argv[1:])
    elif first_arg == "image":
        # Explicit image command
        return image_main(argv[1:])
    else:
        # Backward compatible: treat first arg as image path
        return image_main(argv)


if __name__ == "__main__":
    sys.exit(main())
