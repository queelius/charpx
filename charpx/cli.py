"""charpx CLI - terminal image viewer.

This CLI is deprecated in favor of imgcat. Install with: pip install charpx[imgcat]
"""

from __future__ import annotations

import sys


def main() -> None:
    """CLI entry point - delegates to imgcat if available."""
    try:
        from imgcat.imgcat import main as imgcat_main
        imgcat_main()
    except ImportError:
        # Fall back to basic implementation if imgcat not installed
        print(
            "The charpx CLI has moved to imgcat.\n"
            "Install with: pip install charpx[imgcat]\n"
            "Then run: imgcat image.jpg",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
