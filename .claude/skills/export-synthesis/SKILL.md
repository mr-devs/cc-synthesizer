---
name: export-synthesis
description: Package the synthesis into a shareable ZIP for distribution. Use when the user wants to share, export, or distribute their synthesis to others. Creates a self-contained directory (synthesis-export/) with the HTML, CSS, JS, all source PDFs, and all summary files, then zips it. The "Ask Claude" functionality is automatically removed (button hidden via CSS) since it requires a local server to work. Invoke when the user says things like "export", "share", "package", "zip up", "distribute", or "send the synthesis to someone".
argument-hint: [output-name]
allowed-tools: Bash
disable-model-invocation: false
---

## What this skill does

Creates a new directory containing everything a recipient needs to read the synthesis in their browser, then packages it as a ZIP. The "Ask Claude" button is hidden via CSS since it requires the local FastAPI server.

Output name defaults to `synthesis-export` but can be customized: `/export-synthesis my-topic` produces `exports/my-topic/` and `exports/my-topic.zip`.

**Output structure:**
```
exports/
├── <name>/
│   ├── synthesis.html      ← open this in any browser
│   ├── assets/
│   │   ├── style.css       ← Ask Claude button hidden
│   │   └── script.js
│   ├── documents/          ← all source PDFs (subdirectory structure preserved)
│   ├── summaries/          ← all summary .md files (subdirectory structure preserved)
│   └── citations.json      ← citation metadata (for reference)
└── <name>.zip              ← the shareable archive
```

## Steps

### 1. Ensure synthesis.html is up to date

If `synthesis/synthesis.html` doesn't exist or the user wants a fresh build, run it first:

```bash
uv run python scripts/build_html.py
```

### 2. Run the export script

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/export_synthesis.py
```

If the user passed a custom name via `$ARGUMENTS`, pass it with `--name`:

```bash
uv run python ${CLAUDE_SKILL_DIR}/scripts/export_synthesis.py --name $ARGUMENTS
```

**What the script changes**

**synthesis.html** — the two asset paths are updated from relative paths pointing into the repo (`../scripts/templates/...`) to local paths (`assets/...`). No other changes.

**assets/style.css** — two rules are appended at the end:
```css
.ask-btn { display: none !important; }
#response-panel { display: none !important; }
```
That's the only modification. Everything else — tooltips, sidebar navigation, citation links — works as normal.

### 3. Report to the user

Tell the user:
- The path to the ZIP file
- How many PDFs and summaries were included
- That recipients just unzip and open `synthesis.html` — no server or software needed
- That citation tooltips work offline; only the "Ask Claude" chat panel is disabled

Generate this report exactly as follows, filling in the placeholders:

```
- Created ZIP: exports/<name>.zip
- Unzipped directory: exports/<name>/
- Included PDFs: <count>
- Included summaries: <count>
- Test by opening: exports/<name>/synthesis.html

If you have tested the file works and would like me to delete the unzipped directory, just let me know!
```
