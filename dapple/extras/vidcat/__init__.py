"""vidcat - Terminal video frame viewer.

Display video frames in the terminal using dapple renderers.
Requires ffmpeg to be installed.
"""

from dapple.extras.vidcat.vidcat import main, vidcat, view, to_asciinema

__version__ = "0.1.0"
__all__ = ["main", "vidcat", "view", "to_asciinema"]
