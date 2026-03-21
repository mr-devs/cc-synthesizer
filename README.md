# cc-synthesizer

A Claude Code skill pipeline that turns a folder of PDFs into an interactive synthesis.

Drop documents about any topic into `documents/`, run one command, and get:

- A structured markdown summary of each document
- A cross-cutting synthesis with thematic analysis, tensions, consensus, and gaps — every claim tied to an inline citation
- An interactive HTML page where you can hover citations for metadata, open source PDFs, and highlight any passage to **ask Claude about it** in a streaming side panel

Works with academic papers, industry reports, white papers, technical docs — any PDF content.

---

## Quick Start

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [`pdftotext`](https://poppler.freedesktop.org/) (`brew install poppler`), [`fbib`](https://github.com/mr-devs/fetchbib) (`uv tool install fetchbib`)

```bash
# 1. Clone the repo
git clone https://github.com/mr-devs/cc-synthesizer
cd cc-synthesizer
```

**2.** Drop your PDFs into the `documents/` folder.

**3.** Start Claude Code in the project directory and run the full pipeline:

```
/create-synthesis
```

Claude Code will generate a structured summary for each document, then synthesize them into a single cross-cutting analysis. This will take some time depending on the number of documents. Once complete...

**4.** Still in Claude Code, launch the interactive HTML page:

```
/launch-synthesis
```

Note: you may want to run `/clear` first to reset your context window before this step.

**5.** In a new terminal window, start the local server to enable the "Ask Claude" side panel. The proper command will be printed by the `/launch-synthesis` skill for you to copy and paste.

`/launch-synthesis` builds the HTML and opens the page in your browser. The "Ask Claude" side panel requires the local server running in step 5 — closing that terminal stops the server.

No separate API key needed — the Ask Claude feature uses your existing Claude Code subscription.

**6.** (Optional) Export your synthesis as a shareable ZIP:

```
/export-synthesis
```

This packages the HTML, all source PDFs, summaries, and citations into a self-contained file anyone can open — no server required.

**7.** (Optional) Start fresh with a new batch of PDFs:

```
/pipeline-reset
```

`/pipeline-reset` will "reset" the pipeline by deleting PDFs, summary files, etc. It will check if you have already exported your synthesis and, if you haven't, do it for you. It will also confirm with you the files to delete before deleting them.

---

## How It Works

### Pipeline

```
documents/          →   /cleanup-pdf-names
                    →   /summarize-documents     →   summaries/*.md
                                                     synthesis/citations.json
                    →   /create-synthesis        →   synthesis/synthesis.md
                    →   /launch-synthesis        →   synthesis/synthesis.html
                                                     (server: run manually, port 8000)
                    →   /export-synthesis        →   exports/*.zip
                    →   /pipeline-reset          →   (clean slate for a new batch)
```

`/create-synthesis` is the entry point for the full pipeline. If no summaries exist yet, it detects this and prompts you to confirm before running cleanup → summarize → synthesize automatically.

Once you have a synthesis, `/export-synthesis` packages the HTML, all source PDFs, summaries, and citations into a self-contained ZIP you can share with anyone — no server required. 

`/pipeline-reset` clears all generated files so you can start fresh with a new set of documents; it will offer to export first if a synthesis exists.

### Skills

| Command | What it does |
|---|---|
| `/cleanup-pdf-names <path>` | Sanitizes PDF filenames (spaces → underscores, dashes normalized) for consistent downstream processing |
| `/summarize-documents <path> ["context"]` | Generates a per-document summary for each PDF; detects document type and adapts the summary structure; fetches BibTeX entries via DOI/title lookup; skips already-summarized documents |
| `/create-synthesis ["context"]` | Reads all summaries and generates a cross-cutting synthesis with thematic sections, tensions, consensus, gaps, and inline citations; triggers the full pipeline if summaries are missing |
| `/launch-synthesis` | Builds the interactive HTML and opens the page in your browser (start the server separately to enable Ask Claude) |
| `/export-synthesis ["name"]` | Packages synthesis.html, all PDFs, summaries, and citations.json into a shareable ZIP in `exports/`; disables the Ask Claude button since it requires a local server |
| `/pipeline-reset` | Clears all generated files (PDFs, summaries, synthesis outputs) for a fresh start; offers to export first if a synthesis exists |

All skills accept optional freetext context to orient their output:

```
/summarize-documents documents/ "these are policy reports, focus on regulatory recommendations"
/create-synthesis "I'm trying to understand the debate about X — organize themes around competing positions"
```

### What summaries look like

Each document gets a structured summary adapted to its type:

| Document type | Summary sections |
|---|---|
| Academic paper | Main Takeaways · Methodological Approach · Limitations |
| Industry/gov report | Key Findings · Approach · Caveats |
| White paper / opinion | Core Arguments · Supporting Evidence · Assumptions & Weaknesses |
| Book chapter | Central Ideas · Argument Structure · Relationship to Broader Work |
| Technical documentation | What It Does · How It Works · Known Limitations |

All summaries share a consistent Metadata block (title, authors/org, year, publication/source, DOI, BibTeX key).

### What the synthesis looks like

`synthesis/synthesis.md` is structured as:

1. **Reading Guide** — recommended entry-point documents
2. **Overview** — orientation to the topic and corpus
3. **Major Themes** — thematic sections with inline citations
4. **Key Tensions & Debates** — where the literature disagrees
5. **Points of Consensus** — what sources agree on
6. **Methodological Patterns** — how documents approach the topic
7. **Notable Gaps** — what the corpus doesn't address
8. **Citation Index** — all cited keys with one-line descriptions

### The interactive HTML page

After `/launch-synthesis` opens the page:

- **Hover a citation** → tooltip with title, authors, year, venue, and links to open the source PDF and view the summary
- **Select any text → "Ask Claude"** → a side panel slides in with a streaming Claude response, pre-loaded with the selected passage, the relevant citations, and your synthesis memory context

The local server must be started manually in a separate terminal before using Ask Claude:

```bash
PYTHONPATH=. uv run uvicorn server.main:app --reload
```

Stop it with `Ctrl+C` in that terminal, or `pkill -f "uvicorn server.main:app"`.

---

## Advanced Usage

### Providing framing with synthesis-guidance.md

For detailed framing, edit `synthesis/synthesis-guidance.md` before running `/create-synthesis`. The skill reads it automatically. Use it to specify questions you want answered, an outline to follow, or audience context.

### Persistent context across sessions

`/create-synthesis` automatically creates `synthesis/synthesis-memory.md` after writing the synthesis. It's pre-populated with the topic, corpus, and key themes. Add your own conclusions and notes to the "Conclusions reached" and "User framing notes" sections — this file is included in every Ask Claude request so Claude has running context without re-explanation.

### Adding documents and re-running

After adding new PDFs or editing summaries:

```
/summarize-documents documents/    # only processes new PDFs
/create-synthesis                  # regenerates synthesis.md
/launch-synthesis                  # rebuilds HTML and reopens the page
```

`/summarize-documents` is idempotent — it skips documents that already have summaries.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Could not reach the local server" | Server not running | Run `/launch-synthesis` or `uv run uvicorn server.main:app --reload` |
| "claude CLI not found" | CC not installed or not on PATH | Install Claude Code; verify `claude auth status` shows logged in |
| Port 8000 already in use | Another process using the port | Run `uv run uvicorn server.main:app --reload --port 8001` and update the fetch URL in `scripts/templates/script.js` |

---

## Repository Layout

```
cc-synthesizer/
├── .claude/
│   ├── skills/           # Slash command implementations
│   └── reference/        # Format specs used by skills
├── documents/            # Drop your PDFs here (not version-controlled)
├── summaries/            # Auto-generated per-document summaries
├── synthesis/            # Auto-generated synthesis.md, synthesis.html, and guidance files
├── exports/              # Packaged synthesis ZIPs for sharing (not version-controlled)
├── server/               # FastAPI server for in-page Claude responses
└── scripts/              # build_html.py and HTML templates
```
