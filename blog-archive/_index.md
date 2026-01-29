# Terminal-First Tools for the AI Era

These tools share a conviction: the command line is not a legacy interface. It is the natural interface for an era where intelligence — human and artificial — operates through text.

Text is the universal substrate. Pipes compose. JSON structures. The terminal works everywhere — SSH sessions, containers, CI runners, AI coding assistants. Every tool described here starts from that premise and builds outward.

## The Ecosystem

### Graphics

| Tool | Purpose |
|------|---------|
| **dapple** | Canvas API with pluggable renderers (braille, quadrants, sextants, ascii, sixel, kitty, fingerprint) |
| **imgcat** | Display images in the terminal |
| **vidcat** | Play video as terminal animation, export to asciinema |
| **pdfcat** | Render PDF pages to terminal |
| **mdcat** | Render markdown with inline images |
| **fplot** | Plot mathematical functions (composable via JSON pipes) |
| **chop** | Image processing pipeline (load, resize, crop, dither, sharpen — all chainable) |

### Knowledge

| Tool | Purpose |
|------|---------|
| **ctk** | Browse and search Claude Code conversations |
| **btk** | Bookmark manager with hierarchical tags and query DSL |
| **ebk** | Ebook library browser |
| **jot** | Daily journal and personal knowledge base |

### Infrastructure

| Tool | Purpose |
|------|---------|
| **repoindex** | Index and query a collection of git repositories |
| **crier** | Cross-post blog content to social platforms |

## Design Patterns

These tools share more than philosophy. They share concrete engineering patterns:

- **JSONL by default, `--pretty` for humans.** Machine-readable output is the default. Human-readable output is one flag away. An LLM agent reads the default; a human adds `--pretty`.

- **VFS shells for exploration.** btk, ctk, and ebk each provide a virtual filesystem shell. `cd tags/python && ls` feels like navigating a directory tree, but you're querying a SQLite database. Exploration before precision.

- **Claude Code skills and MCP servers.** Each tool ships as a Claude Code skill for direct integration, and several expose MCP servers for richer tool use.

- **SQLite + full-text search.** Bookmarks, conversations, ebooks, journals — all stored in SQLite with FTS5 indexes. Fast, portable, queryable.

- **Graceful degradation.** Active terminal with sixel support? Use pixel-perfect rendering. Plain SSH session? Fall back to braille. Piping to a file? ASCII. The right output for the right context, automatically.

- **Unix pipes as composition.** `fplot "sin(x)" -j | fplot "cos(x)" -l` chains two function plots. `chop load photo.jpg -j | chop resize 50% -j | chop dither -r braille` chains three image operations. JSON flows through pipes; the final stage renders.

## The Posts

1. **[The Command Line Is the LLM's Native Tongue](cli-native-tongue.md)** — Why CLIs are the optimal interface for AI agents, and why tools built on Unix philosophy become LLM-native by default.

2. **[One Canvas, Seven Renderers](one-canvas-seven-renderers.md)** — The engineering problem dapple solves: terminal graphics fragmentation, and the design decisions that address it.

3. **[Viewers and Creators](viewers-and-creators.md)** — A tour of the graphics toolkit, grouped by what they do: bring content into the terminal (imgcat, vidcat, pdfcat, mdcat) or create visual output through composition (fplot, chop).

4. **[How Terminal Characters Encode Pixels](how-terminal-characters-encode-pixels.md)** — The elegant encodings behind braille dots, quadrant blocks, sextants, sixel bands, and glyph matching.

5. **[Preprocessing: The Invisible Art](preprocessing.md)** — Why raw bitmaps look terrible in terminals, and how auto-contrast, dithering, gamma correction, and sharpening transform the output.

---

*All tools are open source and available on PyPI.*
