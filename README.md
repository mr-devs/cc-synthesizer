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
git clone https://github.com/your-username/cc-synthesizer
cd cc-synthesizer
```

**2.** Drop your PDFs into the `documents/` folder.

**3.** Start Claude Code in the project directory and run the full pipeline:

```
/create-synthesis
```

**4.** Still in Claude Code, launch the interactive HTML page:

```
/launch-synthesis
```

**5.** In a new terminal window, start the local server:

```bash
uv run uvicorn server.main:app --reload
```

`/launch-synthesis` builds the HTML and opens the page in your browser. Start the local server in a new terminal (step 5) to enable the "Ask Claude" side panel — closing that terminal stops the server.

No separate API key needed — the Ask Claude feature uses your existing Claude Code subscription.

---

## How It Works

### Pipeline

```
documents/          →   /cleanup-pdf-names
                    →   /summarize-documents     →   summaries/*.md
                                                     references.bib
                    →   /create-synthesis        →   synthesis/synthesis.md
                    →   /launch-synthesis        →   synthesis/synthesis.html
                                                     local server (port 8000)
```

`/create-synthesis` is the entry point for the full pipeline. If no summaries exist yet, it detects this and prompts you to confirm before running cleanup → summarize → synthesize automatically.

### Skills

| Command | What it does |
|---|---|
| `/cleanup-pdf-names <path>` | Sanitizes PDF filenames (spaces → underscores, dashes normalized) for consistent downstream processing |
| `/summarize-documents <path> ["context"]` | Generates a per-document summary for each PDF; detects document type and adapts the summary structure; fetches BibTeX entries via DOI/title lookup; skips already-summarized documents |
| `/create-synthesis ["context"]` | Reads all summaries and generates a cross-cutting synthesis with thematic sections, tensions, consensus, gaps, and inline citations; triggers the full pipeline if summaries are missing |
| `/launch-synthesis` | Builds the interactive HTML, starts the local FastAPI server, and opens the page in your browser |

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

The local server must be running for the "Ask Claude" side panel to work. `/launch-synthesis` opens the HTML page and then prompts you to start the server yourself in a **new terminal window**:

```bash
uv run uvicorn server.main:app --reload
```

Closing that terminal window automatically stops the server — no cleanup needed.

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
├── server/               # FastAPI server for in-page Claude responses
└── scripts/              # build_html.py and HTML templates
```
