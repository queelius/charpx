"""chop - Unix-philosophy image manipulation CLI with JSON piping.

Supports chaining operations via JSON piping:
    chop load photo.jpg -j | chop resize 50% -j | chop dither -r braille
"""

from chop.cli import main

__version__ = "0.1.0"
__all__ = ["main"]
