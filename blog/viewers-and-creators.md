# Viewers and Creators

You have a PDF, a video, a scatter plot, and a photograph. You are in an SSH session. Here is how you look at all four without leaving the terminal.

```bash
pdfcat report.pdf                          # PDF pages as terminal art
vidcat demo.mp4                            # Video as terminal animation
fplot "sin(x)" -j | fplot "cos(x)" -l     # Scatter plot from functions
imgcat photo.jpg --dither --contrast       # Photo with preprocessing
```

Four formats, four tools, one interface pattern: file in, terminal graphics out. Same flags, same renderers, same preprocessing options. The tools split into two categories: **viewers** bring existing content into the terminal, and **creators** produce new visual output through Unix composition.

## Viewers: Bringing the World In

The viewer tools share a common structure: parse a file format, produce a bitmap, render it through dapple. They share CLI conventions — `-r` for renderer, `-w` for width, `--dither` and `--contrast` for preprocessing — so learning one teaches you all of them.

### imgcat

The simplest viewer. Load an image, render it.

```bash
imgcat photo.jpg                     # Default renderer (auto-detect)
imgcat photo.jpg -r braille          # Force braille
imgcat photo.jpg -r quadrants        # Color blocks
imgcat photo.jpg -r sixel            # True pixels (if supported)
imgcat photo.jpg --dither --contrast # Preprocessing for better output
imgcat photo.jpg -w 120              # Scale to 120 columns wide
```

imgcat handles the common case: you have an image file and want to see it. JPEG, PNG, WebP, BMP, TIFF — anything Pillow can load. The renderer auto-detects your terminal when possible, or defaults to braille for maximum compatibility.

Multiple files work as expected:

```bash
imgcat *.png                         # All PNGs in directory
imgcat photos/**/*.jpg               # Recursive glob
```

Pipe from stdin works too:

```bash
curl -s https://example.com/logo.png | imgcat -
```

### vidcat

Video is a sequence of images. vidcat renders each frame, plays the sequence as terminal animation, and optionally exports to asciinema format.

```bash
vidcat demo.mp4                      # Play in terminal
vidcat demo.mp4 -r braille           # Force braille renderer
vidcat demo.mp4 --fps 15             # Override framerate
vidcat demo.mp4 -o demo.cast         # Export to asciinema
```

The asciinema export is the interesting part. asciinema recordings are JSON: timestamped sequences of terminal output. vidcat converts video frames to terminal art frames and writes the sequence as a `.cast` file. The result is a "video" that plays in any terminal via `asciinema play`, embeds on web pages via the asciinema player, and weighs a fraction of the original video file.

vidcat uses ffmpeg for decoding, so it handles anything ffmpeg handles: MP4, WebM, GIF, AVI, MOV, and every other format ffmpeg supports.

### pdfcat

PDF pages rendered as terminal art.

```bash
pdfcat report.pdf                    # All pages
pdfcat report.pdf -p 3               # Page 3 only
pdfcat report.pdf -p 1-5             # Pages 1 through 5
pdfcat report.pdf -r quadrants       # Color blocks for diagrams
pdfcat report.pdf --contrast         # Improve readability
```

pdfcat uses pypdfium2 for rendering, which produces high-quality bitmaps from PDF pages. Text-heavy PDFs render well in braille (structure is clear). Diagrams and figures benefit from quadrants or sextants for color. The `-w` flag controls resolution — wider means more detail, at the cost of a larger terminal output.

### mdcat

Markdown rendered with inline images.

```bash
mdcat README.md                      # Render markdown
mdcat README.md -r sixel             # With sixel images
```

mdcat renders markdown text normally (formatting, headers, code blocks) and renders embedded images using dapple. Images appear inline, at the point where they're referenced in the markdown. In a sixel- or kitty-capable terminal, images render at full fidelity. In a basic terminal, they render as braille.

This makes `mdcat README.md` a viable alternative to opening a browser for markdown preview — especially over SSH, where opening a browser isn't an option.

## Creators: Unix Composition for Graphics

Viewers consume files. Creators produce output — and they do it through pipelines. The composition model is the same as Unix text tools: each stage reads input, transforms it, and writes output for the next stage.

### fplot

fplot plots mathematical functions. The core interface:

```bash
fplot "sin(x)"                       # Plot sin(x)
fplot "sin(x)" --xmin -10 --xmax 10  # Custom x range
fplot "x**2 - 3*x + 1"              # Any expression
```

The power is in composition. The `-j` flag outputs JSON instead of rendering:

```bash
fplot "sin(x)" -j | fplot "cos(x)" -l
```

The first invocation evaluates sin(x) and outputs JSON describing the plot state: function data, axis ranges, colors. The second invocation reads that state from stdin, adds cos(x), and renders the combined plot. The `-l` flag means "last stage — render now."

Chain as many functions as you want:

```bash
fplot "sin(x)" -j | fplot "cos(x)" --color red -j | fplot "x/3" --color green -l
```

Three functions, three colors, one plot. Each stage is an independent command. The JSON carries accumulated state through the pipeline.

Parametric curves work the same way:

```bash
# Circle
fplot -p "cos(t),sin(t)"

# Two concentric circles
fplot -p "cos(t),sin(t)" -j | fplot -p "2*cos(t),2*sin(t)" -l

# Heart curve
fplot -p "16*sin(t)**3,13*cos(t)-5*cos(2*t)-2*cos(3*t)-cos(4*t)"
```

The `-p` flag switches to parametric mode: two comma-separated expressions for x(t) and y(t).

### chop

chop applies the pipeline pattern to image processing. Each operation reads JSON from stdin, applies a transform, and outputs JSON:

```bash
chop load photo.jpg -j | chop resize 50% -j | chop dither -r braille
```

Three stages: load the image, resize to half, dither and render as braille. The JSON carries the image path and accumulated operations — not the pixels themselves. This is lazy evaluation: operations are recorded, not executed, until the final rendering stage materializes the result.

Available operations:

```bash
chop load photo.jpg -j               # Load image into pipeline
chop resize 50% -j                   # Resize (percentage or WxH)
chop crop 100 100 500 400 -j         # Crop to region
chop rotate 45 -j                    # Rotate (degrees)
chop flip h -j                       # Flip horizontal or vertical
chop dither -j                       # Floyd-Steinberg dithering
chop contrast -j                     # Auto-contrast
chop sharpen -j                      # Edge enhancement
chop gamma 0.5 -j                    # Gamma correction
chop threshold 0.5 -j               # Binary threshold
chop invert -j                       # Invert brightness
```

The `-r` flag at any stage triggers rendering with the specified renderer. The `-o` flag saves to a file instead:

```bash
chop load input.jpg -j | chop resize 800x600 -j | chop sharpen -o output.jpg
```

Chains can be as long as needed:

```bash
chop load photo.jpg -j \
  | chop crop 10% 10% 80% 80% -j \
  | chop resize 50% -j \
  | chop contrast -j \
  | chop dither -j \
  | chop sharpen -r braille
```

## The `-j` Pattern

The `-j` flag — JSON output — is the connective tissue of the entire toolkit. It's a one-character switch between two modes:

- **Without `-j`:** The tool renders its output for a human. Terminal graphics appear on screen.
- **With `-j`:** The tool emits structured data for the next stage. No rendering, no terminal escape sequences — just a JSON object describing the current state.

This is the same idea as `curl -s url | jq .` versus `curl url`. The silent/structured mode exists for machines; the default mode exists for humans. But where curl's distinction is about verbosity, the `-j` pattern is about composability. JSON output means the result is inspectable, debuggable, and — critically — LLM-readable.

An AI agent constructing a multi-stage image pipeline reasons about JSON:

```json
{"path": "photo.jpg", "ops": ["resize:50%", "contrast", "dither"], "renderer": null}
```

This is structured data the agent can read, modify, and extend. It can add an operation by constructing another `chop` command that reads this JSON. It can inspect intermediate state by omitting the final render. It can branch the pipeline by duplicating the JSON to two different final stages.

The `-j` flag turns every tool into an API endpoint. The protocol is JSON-over-stdin/stdout. The transport is Unix pipes. No HTTP server, no socket management, no authentication — just text streams.

## Shared Foundations

All six tools — imgcat, vidcat, pdfcat, mdcat, fplot, chop — share common infrastructure:

- **dapple renderers.** The same seven renderers are available everywhere. `-r braille`, `-r quadrants`, `-r sixel` work identically across tools.

- **Consistent flags.** `-r` for renderer, `-w` for width, `-j` for JSON, `-o` for output file, `--dither`, `--contrast`, `--sharpen` for preprocessing. Learn once, use everywhere.

- **Auto-detection.** When no renderer is specified, the tools detect terminal capabilities and choose appropriately. Sixel-capable terminals get sixel. Kitty gets the kitty protocol. Unknown terminals get braille.

- **Claude Code skills.** Each tool ships as a Claude Code skill, providing discoverability and documentation directly to AI agents. `skill-install imgcat` makes the tool available in Claude Code sessions.

The consistency means that switching from one tool to another requires no relearning. And it means an LLM agent that knows how to use imgcat already knows how to use vidcat, pdfcat, and chop — the interface patterns are identical.

---

*Further reading: [The Command Line Is the LLM's Native Tongue](cli-native-tongue.md) argues why this Unix composition model is optimal for AI agents. [One Canvas, Seven Renderers](one-canvas-seven-renderers.md) explains the renderer abstraction these tools share.*
