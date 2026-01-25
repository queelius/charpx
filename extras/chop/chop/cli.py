#!/usr/bin/env python3
"""chop - Unix-philosophy image manipulation CLI.

Supports chaining operations via JSON piping:
    chop load photo.jpg -j | chop resize 50% -j | chop dither -r braille
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chop.operations import (
    op_resize,
    op_crop,
    op_rotate,
    op_flip,
    op_dither,
    op_invert,
    op_sharpen,
    op_contrast,
    op_gamma,
    op_threshold,
    parse_crop,
)
from chop.pipeline import (
    PipelineState,
    load_image,
    read_pipeline_input,
    write_pipeline_output,
)
from chop.render import render_to_terminal, RENDERERS


def cmd_load(args: argparse.Namespace) -> PipelineState:
    """Load image from file, URL, or stdin."""
    # Check for piped input first
    prev_state = read_pipeline_input()
    if prev_state:
        # Continue from previous state (re-load from stdin ANSI not supported yet)
        prev_state.add_operation("load", [args.source])
        return prev_state

    image = load_image(args.source)

    state = PipelineState(
        image=image,
        metadata={
            "original_path": args.source if args.source != "-" else "<stdin>",
            "original_size": list(image.size),
        },
    )
    state.add_operation("load", [args.source])
    return state


def cmd_resize(args: argparse.Namespace) -> PipelineState:
    """Resize image."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("resize requires piped input (use: chop load img.png -j | chop resize ...)")

    state.image = op_resize(state.image, args.size)
    state.add_operation("resize", [args.size])
    return state


def cmd_crop(args: argparse.Namespace) -> PipelineState:
    """Crop image."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("crop requires piped input")

    x, y, w, h = parse_crop([args.x, args.y, args.width, args.height], state.image.size)
    state.image = op_crop(state.image, x, y, w, h)
    state.add_operation("crop", [args.x, args.y, args.width, args.height])
    return state


def cmd_rotate(args: argparse.Namespace) -> PipelineState:
    """Rotate image."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("rotate requires piped input")

    state.image = op_rotate(state.image, args.degrees)
    state.add_operation("rotate", [args.degrees])
    return state


def cmd_flip(args: argparse.Namespace) -> PipelineState:
    """Flip image."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("flip requires piped input")

    state.image = op_flip(state.image, args.direction)
    state.add_operation("flip", [args.direction])
    return state


def cmd_dither(args: argparse.Namespace) -> PipelineState:
    """Apply Floyd-Steinberg dithering."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("dither requires piped input")

    state.image = op_dither(state.image, threshold=args.threshold)
    state.add_operation("dither", [f"--threshold={args.threshold}"])
    return state


def cmd_invert(args: argparse.Namespace) -> PipelineState:
    """Invert image."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("invert requires piped input")

    state.image = op_invert(state.image)
    state.add_operation("invert", [])
    return state


def cmd_sharpen(args: argparse.Namespace) -> PipelineState:
    """Sharpen image."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("sharpen requires piped input")

    state.image = op_sharpen(state.image, strength=args.strength)
    state.add_operation("sharpen", [f"--strength={args.strength}"])
    return state


def cmd_contrast(args: argparse.Namespace) -> PipelineState:
    """Auto-contrast image."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("contrast requires piped input")

    state.image = op_contrast(state.image)
    state.add_operation("contrast", [])
    return state


def cmd_gamma(args: argparse.Namespace) -> PipelineState:
    """Apply gamma correction."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("gamma requires piped input")

    state.image = op_gamma(state.image, gamma=args.value)
    state.add_operation("gamma", [args.value])
    return state


def cmd_threshold(args: argparse.Namespace) -> PipelineState:
    """Apply binary threshold."""
    state = read_pipeline_input()
    if not state:
        raise ValueError("threshold requires piped input")

    state.image = op_threshold(state.image, level=args.level)
    state.add_operation("threshold", [args.level])
    return state


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser with subcommands."""
    parser = argparse.ArgumentParser(
        prog="chop",
        description="Unix-philosophy image manipulation CLI with JSON piping",
        epilog=(
            "Examples:\n"
            "  chop load photo.jpg -j | chop resize 50%% -j | chop dither -r braille\n"
            "  chop load photo.jpg -j | chop crop 10%% 10%% 80%% 80%% -o cropped.png\n"
            "  chop load photo.jpg -r braille  # Direct render\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global flags
    parser.add_argument("-j", "--json", action="store_true", help="Output JSON for piping")
    parser.add_argument("-o", "--output", type=str, help="Save to file (png, jpg, etc.)")
    parser.add_argument(
        "-r",
        "--renderer",
        choices=list(RENDERERS.keys()),
        help="Render to terminal using specified renderer",
    )
    parser.add_argument("-w", "--width", type=int, help="Output width in characters")
    parser.add_argument("-H", "--height", type=int, help="Output height in characters")

    subparsers = parser.add_subparsers(dest="command", help="Operation to perform")

    # load
    load_parser = subparsers.add_parser("load", help="Load image from file, URL, or stdin")
    load_parser.add_argument("source", help="File path, URL, or '-' for stdin")

    # resize
    resize_parser = subparsers.add_parser("resize", help="Resize image")
    resize_parser.add_argument("size", help="Size: 50%%, 800x600, w800, h600")

    # crop
    crop_parser = subparsers.add_parser("crop", help="Crop image")
    crop_parser.add_argument("x", help="Left edge (pixels or %%)")
    crop_parser.add_argument("y", help="Top edge (pixels or %%)")
    crop_parser.add_argument("width", help="Width (pixels or %%)")
    crop_parser.add_argument("height", help="Height (pixels or %%)")

    # rotate
    rotate_parser = subparsers.add_parser("rotate", help="Rotate image")
    rotate_parser.add_argument("degrees", type=float, help="Rotation angle (counter-clockwise)")

    # flip
    flip_parser = subparsers.add_parser("flip", help="Flip image")
    flip_parser.add_argument("direction", choices=["h", "v"], help="h=horizontal, v=vertical")

    # dither
    dither_parser = subparsers.add_parser("dither", help="Apply Floyd-Steinberg dithering")
    dither_parser.add_argument(
        "--threshold", type=float, default=0.5, help="Threshold (0.0-1.0, default: 0.5)"
    )

    # invert
    subparsers.add_parser("invert", help="Invert image")

    # sharpen
    sharpen_parser = subparsers.add_parser("sharpen", help="Sharpen image")
    sharpen_parser.add_argument(
        "--strength", type=float, default=1.0, help="Strength (default: 1.0)"
    )

    # contrast
    subparsers.add_parser("contrast", help="Auto-contrast image")

    # gamma
    gamma_parser = subparsers.add_parser("gamma", help="Apply gamma correction")
    gamma_parser.add_argument("value", type=float, help="Gamma value (>1 darkens, <1 brightens)")

    # threshold
    threshold_parser = subparsers.add_parser("threshold", help="Apply binary threshold")
    threshold_parser.add_argument("level", type=float, help="Threshold level (0.0-1.0)")

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Map commands to handlers
    handlers = {
        "load": cmd_load,
        "resize": cmd_resize,
        "crop": cmd_crop,
        "rotate": cmd_rotate,
        "flip": cmd_flip,
        "dither": cmd_dither,
        "invert": cmd_invert,
        "sharpen": cmd_sharpen,
        "contrast": cmd_contrast,
        "gamma": cmd_gamma,
        "threshold": cmd_threshold,
    }

    if not args.command:
        # No command - check for piped input for direct render
        state = read_pipeline_input()
        if state:
            if args.output:
                state.image.save(args.output)
                print(f"Saved to {args.output}", file=sys.stderr)
            elif args.renderer:
                render_to_terminal(
                    state.image,
                    renderer_name=args.renderer,
                    width=args.width,
                    height=args.height,
                )
            elif args.json:
                write_pipeline_output(state)
            else:
                # Default to braille render
                render_to_terminal(
                    state.image,
                    renderer_name="braille",
                    width=args.width,
                    height=args.height,
                )
        else:
            parser.print_help()
        return

    try:
        handler = handlers.get(args.command)
        if not handler:
            print(f"Unknown command: {args.command}", file=sys.stderr)
            sys.exit(1)

        state = handler(args)

        # Handle output
        if args.output:
            state.image.save(args.output)
            print(f"Saved to {args.output}", file=sys.stderr)
        elif args.json:
            write_pipeline_output(state)
        elif args.renderer:
            render_to_terminal(
                state.image,
                renderer_name=args.renderer,
                width=args.width,
                height=args.height,
            )
        else:
            # Default: output JSON if load, otherwise render
            if args.command == "load":
                # For load without flags, render to terminal
                render_to_terminal(
                    state.image,
                    renderer_name="braille",
                    width=args.width,
                    height=args.height,
                )
            else:
                # Intermediate operations default to JSON
                write_pipeline_output(state)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
