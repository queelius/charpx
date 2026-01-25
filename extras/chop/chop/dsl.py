"""DSL parser for chop programs.

Programs are sequences of operations that can be applied to images.
They contain only operations (no load) - the image comes from the pipeline.

Syntax:
    # Comments start with #
    resize 50%              # Operations are words with arguments
    dither threshold=0.3    # Keyword arguments use =
    resize 50%; dither      # Semicolons separate operations on one line

Example program file (effects.chp):
    # Shrink and enhance
    resize 50%
    contrast
    sharpen strength=0.5
"""

from __future__ import annotations

import shlex
from pathlib import Path


def parse_program(text: str) -> list[tuple[str, tuple, dict]]:
    """Parse program text into operation list.

    Args:
        text: Program text with operations separated by semicolons or newlines.

    Returns:
        List of (name, args, kwargs) tuples.

    Examples:
        >>> parse_program("resize 50%; dither threshold=0.3")
        [('resize', ('50%',), {}), ('dither', (), {'threshold': 0.3})]

        >>> parse_program("# comment\\nresize 50%")
        [('resize', ('50%',), {})]
    """
    ops = []

    # First split by newlines, then by semicolons
    for line in text.split("\n"):
        # Handle semicolon-separated statements
        for statement in line.split(";"):
            # Remove comments (everything after #)
            if "#" in statement:
                statement = statement[: statement.index("#")]
            statement = statement.strip()
            if not statement:
                continue
            op = parse_operation(statement)
            ops.append(op)

    return ops


def parse_operation(line: str) -> tuple[str, tuple, dict]:
    """Parse single operation line.

    Args:
        line: Single operation line like "resize 50%" or "dither threshold=0.3"

    Returns:
        Tuple of (name, args, kwargs).

    Examples:
        >>> parse_operation("resize 50%")
        ('resize', ('50%',), {})

        >>> parse_operation("dither threshold=0.3")
        ('dither', (), {'threshold': 0.3})

        >>> parse_operation("overlay img.png 10 20 opacity=0.5")
        ('overlay', ('img.png', 10, 20), {'opacity': 0.5})
    """
    tokens = shlex.split(line)
    name = tokens[0]
    args = []
    kwargs = {}

    for token in tokens[1:]:
        if "=" in token:
            key, value = token.split("=", 1)
            kwargs[key] = parse_value(value)
        else:
            args.append(parse_value(token))

    return (name, tuple(args), kwargs)


def parse_value(s: str) -> str | int | float | bool:
    """Parse a value string into typed value.

    Args:
        s: String representation of value.

    Returns:
        Typed value (bool, int, float, or str).

    Examples:
        >>> parse_value("true")
        True
        >>> parse_value("42")
        42
        >>> parse_value("3.14")
        3.14
        >>> parse_value("50%")
        '50%'
    """
    # Boolean
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False

    # Integer
    try:
        return int(s)
    except ValueError:
        pass

    # Float
    try:
        return float(s)
    except ValueError:
        pass

    # String (path, percentage, etc.)
    return s


def load_program(source: str) -> str:
    """Load program from file or return inline string.

    Auto-detects: if file exists and is a file (not directory), read it;
    otherwise treat as inline program.

    Args:
        source: File path or inline program string.

    Returns:
        Program text.

    Examples:
        >>> load_program("resize 50%; dither")  # Inline (file doesn't exist)
        'resize 50%; dither'

        >>> # load_program("/path/to/effects.chp")  # From file (if exists)
    """
    if not source:
        return source
    path = Path(source)
    if path.is_file():
        return path.read_text()
    # Assume it's an inline program
    return source
