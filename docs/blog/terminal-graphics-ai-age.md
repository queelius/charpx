# Terminal Graphics in the AI Age

The terminal is having a renaissance.

Not because we're nostalgic for green phosphor screens, but because the most powerful development tools of 2025 are text-native. Claude Code runs in your terminal. Copilot CLI streams its work as prose. Developers SSH into remote machines, pair through tmux, and live in the command line more than ever before.

In this world, there's a curious gap: we want to *see* things -- charts, images, diagrams -- without leaving the terminal.

## The Problem

AI assistants are remarkable at generating code, but they struggle to show you what they've created. Ask Claude to plot a function and it writes the matplotlib code. But you can't *see* the plot without switching to a GUI, opening a window, breaking your flow.

This context-switching tax compounds. Remote sessions can't spawn windows. Containers don't have displays. Screen sharing in pair programming shows terminals fine, but not the matplotlib figures one participant has open.

We need graphics that are *text*.

## Unicode to the Rescue

Unicode braille characters (U+2800-U+28FF) encode 2x4 dot patterns:

```
+---+---+
| 1 | 4 |
+---+---+
| 2 | 5 |
+---+---+
| 3 | 6 |
+---+---+
| 7 | 8 |
+---+---+
```

Each character represents 8 binary pixels. A 160x80 pixel image becomes just 80x20 characters -- compact enough for a terminal, detailed enough to recognize faces, read charts, debug visualizations.

The encoding is elegant: each dot corresponds to a bit in the codepoint offset (0-255). Dot 1 is bit 0, dot 2 is bit 1, and so on. To render a 2x4 region, threshold each pixel, set the corresponding bits, add to U+2800. That's it.

```python
# The entire core algorithm
def region_to_braille(pixels):
    code = 0
    for i, (dy, dx) in enumerate(DOT_POSITIONS):
        if pixels[dy, dx] > threshold:
            code |= (1 << i)
    return chr(0x2800 + code)
```

Fifty lines of code. No dependencies beyond numpy. A pure function: `bitmap -> braille string`.

## Why Now?

This isn't new technology. Braille Unicode has existed since 1999. Terminal graphics libraries have existed for decades. What's changed is the *use case*.

When your primary interface to a codebase is a text-streaming AI assistant, graphics must be text-compatible. When your development environment is a remote container accessed via SSH, graphics must survive the connection. When you're pair-programming through tmux, graphics must render in the shared terminal.

The AI assistant era demands graphics that are:
- **Pipe-friendly**: Output that flows through Unix pipelines
- **Serializable**: Text that can be logged, diffed, version-controlled
- **Universal**: Characters that render in any terminal, any font, any platform

Braille characters satisfy all three. They're just text.

## The Framebuffer Pattern

The real power isn't in rendering images (though that's useful). It's in treating the terminal as a *framebuffer target*.

Higher-level libraries -- plotting, drawing, game graphics -- can render to a bitmap and hand it off for display:

```python
import matplotlib.pyplot as plt
import numpy as np
from dapple.adapters.matplotlib import MatplotlibAdapter

# Your normal matplotlib code
fig, ax = plt.subplots()
x = np.linspace(0, 2*np.pi, 100)
ax.plot(x, np.sin(x), linewidth=3)
ax.set_title("sin(x)")

# Render to terminal instead of window
adapter = MatplotlibAdapter()
canvas = adapter.to_canvas(fig)
canvas.out(braille)
plt.close()
```

The plotting code doesn't know or care that its output becomes braille. The abstraction boundary is clean: matplotlib produces pixels, dapple produces text.

This pattern enables AI assistants to *show their work*:

```
Claude: Here's the distribution of response times:






The p99 latency is 245ms, which suggests...
```

The assistant doesn't spawn a window. It doesn't save a file. It *says* the picture, inline with its explanation.

## Design Philosophy

Good tools are composable. dapple follows Unix philosophy: do one thing well, play nicely with others.

The library has clear layers:

```
Layer 0: Pixels      bitmap array            Pure data
Layer 1: Preprocess  contrast, dithering     Transformations
Layer 2: Render      bitmap -> string        Output
```

Each layer is independent. You can:
- Use your own preprocessing and just call render
- Swap [renderers](../guide/renderers.md) (braille, block characters, color modes)
- Build higher-level abstractions on top

The SICP influence is deliberate. Primitive expressions (pixels, thresholds), means of combination (preprocessing pipelines), means of abstraction (the adapter pattern). Simple parts that compose into complex wholes.

## What About Color?

Braille is binary -- dots are either on or off. This captures structure beautifully: edges, outlines, the skeleton of an image. But it loses tone and texture.

For photographs and gradients, ANSI color codes paired with block characters work better. dapple provides both: braille for structure, quadrants for tone, and five more renderers spanning the spectrum. Match the representation to the content. Braille for structure, blocks for tone. Sometimes you want both -- render the same data two ways and compare.

## Looking Forward

Terminal-native graphics won't replace GUIs. But they fill a gap that's grown wider as development becomes more text-centric.

When your AI pair programmer lives in the terminal, when your dev environment is a remote container, when your workflow is SSH and tmux and pipes -- you need graphics that are text.

Unicode gave us the alphabet. Now we're learning to draw with it.
