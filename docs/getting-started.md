# Getting Started

## What this is

`cc-synthesizer` is a Claude Code skill pipeline. You drop PDF documents into `documents/`, run a few slash commands, and get:

1. A structured markdown summary of each document (`summaries/`)
2. A cross-cutting synthesis of the whole corpus (`synthesis/synthesis.md`)
3. An interactive HTML page with citation hover and "Ask Claude" integration (`synthesis/synthesis.html`)

It works with any document type — academic papers, industry reports, white papers, technical docs.

## Prerequisites

| Tool | Purpose | Install |
|---|---|---|
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Runs all skills | See Anthropic docs |
| `pdftotext` | Extract text from PDFs | `brew install poppler` |
| `fbib` | Fetch BibTeX from DOI or title | `uv tool install fetchbib` |

Verify your setup:
```bash
pdftotext -v
fbib --help
```

## Workflow

### Option A: Single command

Drop PDFs into `documents/`, then in Claude Code:

```
/create-synthesis
```

Claude will confirm, then run cleanup → summarize → synthesize automatically. Afterwards:

```
/build-html
```

Open `synthesis/synthesis.html` in your browser.

### Option B: Step by step

```
/cleanup-pdf-names documents/
/summarize-documents documents/
/create-synthesis
/build-html
```

### Providing context

Most skills accept optional context to orient their output:

```
/summarize-documents documents/ "these are industry reports, focus on policy recommendations"
/create-synthesis "I'm trying to understand the debate about X — organize themes around competing positions"
```

### Using synthesis-guidance.md

For detailed framing, create or edit `synthesis-guidance.md` at the repo root. `/create-synthesis` reads it automatically. See the template already in this repo for structure.

## Using the HTML page

Open `synthesis/synthesis.html` in any browser (no server required):

- **Hover a citation** → see title, authors, year, and links to the source PDF and summary
- **Select text → "Ask Claude"** → a context-rich prompt is copied to clipboard. Paste it into a Claude Code session to ask questions about the passage.

## Persistent context across sessions

Edit `synthesis/synthesis-memory.md` to record conclusions you've reached and framing notes. This file is automatically included in every "Ask Claude" clipboard prompt, so Claude has running context without re-explanation.

## Updating the synthesis

After adding new PDFs or editing summaries, re-run:
```
/summarize-documents documents/    # only processes new PDFs
/create-synthesis                  # regenerates synthesis.md
/build-html                        # regenerates synthesis.html
```
