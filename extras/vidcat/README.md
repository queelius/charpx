# vidcat

Terminal video frame viewer built on [charpx](https://github.com/spinoza/charpx).

Extracts frames from video files and renders them to the terminal using various rendering methods (braille, quadrants, sixel, kitty, etc.).

## Installation

```bash
pip install charpx[vidcat]
# or standalone
pip install vidcat
```

**Requires:** ffmpeg must be installed and available in PATH.

## Usage

### Command Line

```bash
# View all frames (default: max 10)
vidcat animation.gif

# View specific frames
vidcat video.mp4 --frames 1-10        # Frames 1-10
vidcat video.mp4 --frames "1,5,10"    # Specific frames
vidcat video.mp4 --frames -5          # First 5 frames
vidcat video.mp4 --frames 100-        # Frame 100 onwards

# Frame interval/skip (extract 1 frame every N seconds/minutes)
vidcat video.mp4 --every 1s           # 1 frame per second
vidcat video.mp4 --every 30s          # 1 frame every 30 seconds
vidcat video.mp4 --every 1m           # 1 frame per minute

# Control max frames extracted
vidcat video.mp4 --max-frames 20

# Use specific renderer
vidcat animation.gif -r braille
vidcat animation.gif -r quadrants
vidcat animation.gif -r sixel
vidcat animation.gif -r kitty

# Image processing
vidcat video.mp4 --dither             # Floyd-Steinberg dithering
vidcat video.mp4 --contrast           # Auto-contrast
vidcat video.mp4 --invert             # Invert colors

# Size control
vidcat video.mp4 -w 60                # Limit width to 60 chars
vidcat video.mp4 -H 30                # Limit height

# Output options
vidcat video.mp4 --grayscale          # Force grayscale
vidcat video.mp4 --no-color           # Pure ASCII
vidcat video.mp4 -o frames.txt        # Save to file
```

### Supported Formats

- Video: mp4, webm, mkv, avi, mov
- Animation: gif, apng, webp (animated)

### Asciinema Export

Export video as an asciinema recording (.cast file):

```bash
# Basic export
vidcat video.mp4 --asciinema output.cast

# Control playback speed
vidcat video.mp4 --asciinema output.cast --fps 15

# With title
vidcat video.mp4 --asciinema output.cast --title "My Video"

# Play the recording
asciinema play output.cast
```

### Claude Code Skill

Install the skill to help Claude Code use vidcat:

```bash
# Install to current project
vidcat --skill-install --local

# Install globally
vidcat --skill-install --global

# Show skill content
vidcat --skill-show
```

### Python API

```python
from vidcat import view, vidcat, to_asciinema

# Quick view with defaults
view("animation.gif")

# With options
vidcat("video.mp4", frames="1-10", renderer="braille", max_frames=20)

# Extract every 30 seconds
vidcat("video.mp4", every="30s", renderer="quadrants")

# Export to asciinema format
to_asciinema("video.mp4", "output.cast", fps=15, renderer="braille")
```

## Requirements

- Python 3.10+
- charpx
- pillow
- ffmpeg (system dependency)

## License

MIT
