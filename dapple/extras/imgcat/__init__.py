"""imgcat - Terminal image viewer built on dapple.

A specialized tool for viewing images in the terminal using various
rendering methods (braille, quadrants, sixel, kitty, etc.).

Example:
    $ imgcat photo.jpg               # View with auto-detected renderer
    $ imgcat -r braille image.png    # Force braille renderer
    $ imgcat --width 60 photo.jpg    # Custom width
    $ imgcat --dither photo.jpg      # Apply dithering

As a library:
    >>> from dapple.extras.imgcat import view, imgcat
    >>> view("photo.jpg")           # Quick view
    >>> imgcat("photo.jpg", renderer="quadrants", width=80)
"""

from __future__ import annotations

__version__ = "0.1.0"

from dapple.extras.imgcat.imgcat import view, imgcat, ImgcatOptions

__all__ = ["view", "imgcat", "ImgcatOptions", "__version__"]
