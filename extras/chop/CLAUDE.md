# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

chop is a Unix-philosophy image manipulation CLI with **lazy evaluation**. It enables chaining image operations via shell pipes, where JSON carries only the file path and operation list - the image is loaded and processed only at render/save time.

```bash
chop load photo.jpg | chop resize 50% | chop pad 10 | chop render
     ↓                    ↓                 ↓              ↓
  {path}            +resize op          +pad op     LOAD → APPLY → RENDER
```

The JSON is tiny and human-readable:
```json
{"version": 2, "path": "photo.jpg", "ops": [["resize", ["50%"], {}], ["pad", [10], {}]]}
```

chop is part of the dapple ecosystem and uses dapple renderers for terminal output.

## Commands

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Run tests with coverage
pytest --cov=chop --cov-report=term-missing

# Run a single test
pytest tests/test_chop.py::TestOperations::test_resize -v

# Verify installation
chop load photo.jpg -r braille
```

## Architecture

### Lazy Pipeline Architecture

The key design is **lazy evaluation**:
- `PipelineState` stores path + ops list, not image data
- Each command just appends to the ops list (instant, no I/O)
- `materialize()` is called only at render/save time
- JSON is tiny (just path + ops), no base64 encoding

### Module Structure

- **`chop/cli.py`**: Entry point and argument parsing
  - `main()` - CLI entry point
  - `create_parser()` - argparse setup with subcommands
  - `cmd_*` functions - Command handlers that append to ops list

- **`chop/pipeline.py`**: Lazy pipeline state
  - `PipelineState` - Dataclass holding path, ops list, and metadata
  - `add_op()` - Append operation to list
  - `materialize()` - Load image and apply all ops (called at render/save)
  - `to_json()` / `from_json()` - Version 2 format serialization
  - `read_pipeline_input()` / `write_pipeline_output()` - stdin/stdout handling
  - `load_image()` - Load from file, URL, or stdin
  - `image_to_arrays()` - Convert PIL Image to numpy arrays for dapple

- **`chop/operations.py`**: Image transformation functions
  - `op_*` functions - Each takes PIL Image, returns PIL Image
  - `OPERATIONS` dict - Registry mapping op names to functions
  - `apply_operation()` - Dispatch function for materializing ops
  - `parse_size()` / `parse_crop()` - Argument parsing helpers

- **`chop/output.py`**: Centralized output handling
  - `handle_output()` - Decides output based on flags and TTY detection
  - Calls `materialize()` when rendering or saving

- **`chop/render.py`**: Terminal rendering via dapple
  - `RENDERERS` dict - Maps names to dapple renderer instances
  - `render_to_terminal()` - Auto-fits image to terminal size and renders
  - `auto_detect_renderer()` - Detects kitty/sixel/sextants

### Data Flow

1. `load` command creates `PipelineState` with path (no image loaded)
2. Operations append to ops list via `add_op()` (instant)
3. `-j` flag outputs JSON (just path + ops, tiny)
4. TTY detection or explicit flags trigger `materialize()` → render/save

### Output Decision Logic

```
if -j flag:           → JSON output (path + ops)
elif -r RENDERER:     → materialize + render
elif -o FILE:         → materialize + save
elif stdout is TTY:   → materialize + auto-render
else (piped):         → JSON output (path + ops)
```

### Key Design Decisions

- **Lazy evaluation**: No image I/O until final command
- **Tiny JSON**: Just path + ops list, no base64/temp files
- **Inspectable pipeline**: Can `cat` the JSON to see what ops will be applied
- **Composable**: Operations are data, can be stored/replayed
- **PIL Images at materialize time**: Operations work with PIL Images in RGBA mode
- **Conversion at render time**: `image_to_arrays()` converts to numpy only for dapple

## Available Operations

### Geometric Operations
- `resize SIZE` - Resize image (50%, 800x600, w800, h600)
- `crop X Y W H` - Crop region (pixels or percentages)
- `rotate DEGREES` - Rotate counter-clockwise
- `flip h|v` - Flip horizontal or vertical
- `fit WxH` - Fit within bounds, preserve aspect ratio
- `fill WxH` - Fill bounds completely, crop excess (center)

### Padding/Border Operations
- `pad N` - Uniform padding
- `pad V H` - Vertical and horizontal padding
- `pad T R B L` - CSS-style padding (top, right, bottom, left)
- `border WIDTH --color COLOR` - Add colored border

### Composition Operations
- `hstack PATH --align top|center|bottom` - Stack horizontally
- `vstack PATH --align left|center|right` - Stack vertically
- `overlay PATH X Y --opacity 0.5` - Overlay image at position
- `tile COLS ROWS` - Tile image NxM times
- `grid PATHS --cols N` - Arrange images in grid

### Control Operations
- `load SOURCE` - Load image from file, URL, or stdin
- `apply PROGRAM` - Apply program (file or inline "op1; op2")
- `render [RENDERER]` - Render to terminal
- `save PATH` - Save to file

## Dependencies

- numpy>=1.20
- pillow>=9.0
- dapple>=0.1.0 (parent library)
