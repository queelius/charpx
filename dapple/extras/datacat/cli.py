"""CLI entry point for datacat — terminal JSON/JSONL viewer."""

from __future__ import annotations

import argparse
import sys

from dapple.extras.datacat.datacat import (
    dot_path_query,
    extract_field_categories,
    extract_field_values,
    flatten_to_table,
    format_json,
    format_tree,
    read_json,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="datacat",
        description="Terminal JSON/JSONL viewer with visualization modes.",
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="JSON/JSONL file to display (reads stdin if omitted)",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Dot-path query (e.g. .database.host)",
    )

    # Display mode options
    display_group = parser.add_argument_group("display options")
    display_group.add_argument(
        "--table",
        action="store_true",
        help="Flatten JSONL records to a table",
    )
    display_group.add_argument(
        "--tree",
        action="store_true",
        help="Show tree view with box-drawing characters (default)",
    )
    display_group.add_argument(
        "--json",
        action="store_true",
        help="Show syntax-colored JSON instead of tree",
    )
    display_group.add_argument(
        "--no-color",
        action="store_true",
        help="Disable syntax coloring",
    )
    display_group.add_argument(
        "--cycle-color",
        action="store_true",
        help="Color each column with a rotating palette instead of type-based coloring (table mode)",
    )
    display_group.add_argument(
        "--head",
        type=int,
        metavar="N",
        dest="head_n",
        help="Show first N records (JSONL)",
    )
    display_group.add_argument(
        "--tail",
        type=int,
        metavar="N",
        dest="tail_n",
        help="Show last N records (JSONL)",
    )

    # Plot mode (mutually exclusive)
    plot_group = parser.add_argument_group("plot modes (mutually exclusive)")
    plot_mx = plot_group.add_mutually_exclusive_group()
    plot_mx.add_argument(
        "--plot",
        metavar="PATH",
        help="Line plot of a numeric field (dot-path)",
    )
    plot_mx.add_argument(
        "--spark",
        metavar="PATH",
        help="Sparkline of a numeric field (dot-path)",
    )
    plot_mx.add_argument(
        "--bar",
        metavar="PATH",
        help="Bar chart of category counts (dot-path)",
    )
    plot_mx.add_argument(
        "--histogram",
        metavar="PATH",
        help="Histogram of a numeric field (dot-path)",
    )

    # Plot options
    plot_opts = parser.add_argument_group("plot options")
    plot_opts.add_argument(
        "-r", "--renderer",
        default="braille",
        help="Renderer: braille (default), quadrants, sextants, ascii, sixel, kitty",
    )
    plot_opts.add_argument(
        "-w", "--width",
        type=int,
        help="Chart width in terminal characters",
    )
    plot_opts.add_argument(
        "-H", "--height",
        type=int,
        help="Chart height in terminal characters",
    )
    plot_opts.add_argument(
        "-o", "--output",
        metavar="FILE",
        help="Write output to file instead of stdout",
    )
    plot_opts.add_argument(
        "--color",
        type=str,
        help="Chart color (name or #hex, e.g. green, #ff0000)",
    )

    return parser


def _get_input(args: argparse.Namespace) -> str:
    """Read input text from file or stdin."""
    if args.file:
        with open(args.file, "r") as f:
            return f.read()
    if not sys.stdin.isatty():
        return sys.stdin.read()
    print("datacat: no input (provide a file or pipe data via stdin)", file=sys.stderr)
    sys.exit(1)


def _is_plot_mode(args: argparse.Namespace) -> bool:
    return any([args.plot, args.spark, args.bar, args.histogram])


_BOOL_STRINGS = {"true", "false"}
_NULL_STRINGS = {"", "null", "none"}

_COLUMN_COLORS = [
    "\033[36m",   # cyan
    "\033[32m",   # green
    "\033[33m",   # yellow
    "\033[35m",   # magenta
    "\033[34m",   # blue
    "\033[91m",   # bright red
    "\033[96m",   # bright cyan
    "\033[93m",   # bright yellow
]


def _type_color(val: str) -> str:
    """Return ANSI color code based on value type."""
    CYAN = "\033[36m"
    YELLOW = "\033[33m"
    DIM = "\033[2m"

    low = val.strip().lower()
    if low in _NULL_STRINGS:
        return DIM
    if low in _BOOL_STRINGS:
        return YELLOW
    try:
        float(val)
        return CYAN
    except (ValueError, TypeError):
        return ""


def _format_table_output(
    headers: list[str],
    rows: list[list[str]],
    cycle_colors: bool = False,
) -> str:
    """Format headers + rows as an aligned text table with ANSI styling."""
    if not headers:
        return ""

    BOLD = "\033[1m"
    CYAN = "\033[36m"
    DIM = "\033[2m"
    RESET = "\033[0m"

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    lines: list[str] = []

    header_cells = []
    for i, h in enumerate(headers):
        if cycle_colors:
            color = _COLUMN_COLORS[i % len(_COLUMN_COLORS)]
            header_cells.append(f"{BOLD}{color}{h:<{widths[i]}}{RESET}")
        else:
            header_cells.append(f"{BOLD}{CYAN}{h:<{widths[i]}}{RESET}")
    lines.append("  ".join(header_cells))

    sep_cells = [DIM + "─" * w + RESET for w in widths]
    lines.append("  ".join(sep_cells))

    for row in rows:
        cells = []
        for i in range(len(headers)):
            w = widths[i]
            val = row[i] if i < len(row) else ""

            if cycle_colors:
                color = _COLUMN_COLORS[i % len(_COLUMN_COLORS)]
            else:
                color = _type_color(val)

            try:
                float(val)
                formatted = f"{val:>{w}}"
            except (ValueError, TypeError):
                formatted = f"{val:<{w}}"

            if color:
                cells.append(f"{color}{formatted}{RESET}")
            else:
                cells.append(formatted)
        lines.append("  ".join(cells))

    return "\n".join(lines)


def _run_display_mode(data, args: argparse.Namespace) -> None:
    """Handle display/query mode output."""
    # Apply head/tail for list data
    if isinstance(data, list):
        if args.head_n is not None:
            data = data[:args.head_n]
        elif args.tail_n is not None:
            data = data[-args.tail_n:]

    # Apply dot-path query
    if args.query:
        data = dot_path_query(data, args.query)

    # Choose display format (default: tree)
    if args.table and isinstance(data, list):
        headers, rows = flatten_to_table(data)
        output = _format_table_output(headers, rows, cycle_colors=args.cycle_color)
    elif args.json:
        output = format_json(data, colorize=not args.no_color)
    else:
        output = format_tree(data)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output + "\n")
    else:
        print(output)


def _run_plot_mode(data, args: argparse.Namespace) -> None:
    """Render a chart from JSON data using vizlib."""
    from dapple.extras.vizlib import get_renderer, get_terminal_size, pixel_dimensions
    from dapple.extras.vizlib.charts import bar_chart, histogram, line_plot, sparkline
    from dapple.extras.vizlib.colors import parse_color

    if not isinstance(data, list):
        print("datacat: plot mode requires JSONL input (array of records)", file=sys.stderr)
        sys.exit(1)

    # Parse --color if provided
    color = None
    if args.color:
        try:
            color = parse_color(args.color)
        except ValueError as e:
            print(f"datacat: {e}", file=sys.stderr)
            sys.exit(1)

    renderer = get_renderer(args.renderer)
    term_cols, term_lines = get_terminal_size()
    char_w = args.width or term_cols
    char_h = args.height or max(10, term_lines // 3)
    px_w, px_h = pixel_dimensions(renderer, char_w, char_h)

    dest = open(args.output, "w") if args.output else sys.stdout

    try:
        if args.spark:
            values = extract_field_values(data, args.spark)
            canvas = sparkline(values, width=px_w, height=px_h, color=color)
        elif args.plot:
            values = extract_field_values(data, args.plot)
            canvas = line_plot(values, width=px_w, height=px_h, color=color)
        elif args.bar:
            labels, counts = extract_field_categories(data, args.bar)
            canvas = bar_chart(labels, counts, width=px_w, height=px_h, color=color)
        elif args.histogram:
            values = extract_field_values(data, args.histogram)
            canvas = histogram(values, width=px_w, height=px_h, color=color)
        else:
            return

        canvas.out(renderer, dest=dest)
    except ValueError as e:
        print(f"datacat: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if args.output and dest is not sys.stdout:
            dest.close()


def main() -> None:
    """CLI entry point."""
    parser = _build_parser()
    args = parser.parse_args()

    text = _get_input(args)

    try:
        data = read_json(text)
    except Exception as e:
        print(f"datacat: parse error: {e}", file=sys.stderr)
        sys.exit(1)

    if _is_plot_mode(args):
        _run_plot_mode(data, args)
    else:
        _run_display_mode(data, args)


if __name__ == "__main__":
    main()
