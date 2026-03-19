# cc-synthesizer Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Claude Code skill pipeline that ingests any folder of PDFs, generates per-document summaries, produces a cross-cutting synthesis, and renders it as an interactive HTML page with citation hover and "Ask Claude" clipboard integration.

**Architecture:** A set of Claude Code skills backed by reference files. Skills are Markdown instruction files (`SKILL.md`) that Claude follows when invoked via slash commands. Two skills (`cleanup-pdf-names`, `pdf-extraction`) are copied verbatim from `cc-research-project-template`; three are new (`summarize-documents`, `create-synthesis`, `build-html`). A `summaries/manifest.json` file serves as the key-to-path index consumed by `build-html`.

**Tech Stack:** Claude Code skills (Markdown), Bash scripts, `pdftotext` (poppler), `fbib` (fetchbib), JSON, HTML/CSS/JS (embedded, no external deps)

**Spec:** `docs/superpowers/specs/2026-03-19-pdf-synthesizer-design.md`

---

## File Map

**Created:**
- `.claude/skills/cleanup-pdf-names/SKILL.md` — copied from research template
- `.claude/skills/cleanup-pdf-names/scripts/cleanup_pdf_names.sh` — copied from research template
- `.claude/skills/pdf-extraction/SKILL.md` — copied from research template
- `.claude/skills/pdf-extraction/scripts/pdf_extract.sh` — copied from research template
- `.claude/skills/summarize-documents/SKILL.md` — new, generalized summarizer
- `.claude/skills/create-synthesis/SKILL.md` — new, corpus-level synthesis
- `.claude/skills/build-html/SKILL.md` — new, HTML renderer
- `.claude/reference/bibtex-format.md` — copied from research template
- `.claude/reference/summary-format.md` — new, generalized by document type
- `.claude/reference/synthesis-format.md` — new, synthesis structure spec
- `.claude/reference/html-template-notes.md` — new, HTML output contract
- `documents/README.md` — directory purpose
- `summaries/README.md` — directory purpose
- `synthesis/README.md` — directory purpose
- `server/README.md` — Phase 2 stub
- `docs/getting-started.md` — user onboarding
- `docs/skills-reference.md` — quick-reference table for all skills
- `synthesis-guidance.md` — annotated template for user framing
- `README.md` — repo root
- `CLAUDE.md` — Claude Code instructions
- `.gitignore` — excludes PDFs, generated outputs

**Not created (auto-generated at runtime):**
- `references.bib` — written by `summarize-documents`
- `summaries/manifest.json` — written by `summarize-documents`
- `synthesis/synthesis.md` — written by `create-synthesis`
- `synthesis/synthesis-memory.md` — stub written by `create-synthesis`
- `synthesis/synthesis.html` — written by `build-html`

---

## Setup: Add a Test PDF

Before starting, drop one real PDF into `documents/` (any academic paper or report works). Name it using the convention `Author_-_YYYY_-_Title.pdf` or any name with spaces/dashes to exercise the cleanup step. This PDF is referenced in smoke tests throughout the plan.

```bash
# Verify the PDF is there
ls /Users/mdeverna/Documents/Projects/cc-synthesizer/documents/
```

---

## Task 1: Repo Scaffolding

**Files:**
- Create: `README.md`
- Create: `CLAUDE.md`
- Create: `.gitignore`
- Create: `documents/README.md`
- Create: `summaries/README.md`
- Create: `synthesis/README.md`
- Create: `server/README.md`
- Create: `synthesis-guidance.md`

- [ ] **Step 1: Create directory structure**

```bash
cd /Users/mdeverna/Documents/Projects/cc-synthesizer
mkdir -p .claude/skills/cleanup-pdf-names/scripts
mkdir -p .claude/skills/pdf-extraction/scripts
mkdir -p .claude/skills/summarize-documents
mkdir -p .claude/skills/create-synthesis
mkdir -p .claude/skills/build-html
mkdir -p .claude/reference
mkdir -p documents summaries synthesis server docs
```

- [ ] **Step 2: Write `.gitignore`**

```
# PDFs (user-provided, not version-controlled)
documents/**/*.pdf
documents/*.pdf

# Generated outputs
summaries/
synthesis/synthesis.md
synthesis/synthesis-memory.md
synthesis/synthesis.html
references.bib

# Keep directory stubs
!documents/README.md
!summaries/README.md
!synthesis/README.md

# Python / environment
.venv/
__pycache__/
*.pyc
.env
```

- [ ] **Step 3: Write `CLAUDE.md`**

```markdown
# cc-synthesizer

A Claude Code skill pipeline for ingesting PDF documents and generating an interactive synthesis.

## How to use

1. Drop PDFs into `documents/` (subdirectories allowed)
2. Run `/create-synthesis` — this runs the full pipeline and creates `synthesis/synthesis.md`
3. Run `/build-html` — generates `synthesis/synthesis.html`
4. Open `synthesis/synthesis.html` in a browser

Or run individual steps: `/cleanup-pdf-names`, `/summarize-documents`, `/create-synthesis`, `/build-html`

See `docs/getting-started.md` for full instructions.

## Notes

- PDFs in `documents/` are not version-controlled (see `.gitignore`)
- `references.bib`, `summaries/`, and `synthesis/` outputs are also gitignored by default
- `synthesis-guidance.md` at the repo root is an optional framing document read by `/create-synthesis`
```

- [ ] **Step 4: Write `README.md`**

```markdown
# cc-synthesizer

A Claude Code skill pipeline that turns a folder of PDFs into an interactive synthesis.
Drop in documents about any topic, run one command, and get a citable, cross-cutting synthesis
with an interactive HTML page that lets you query Claude about specific passages.

## Quick Start

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code), [`pdftotext`](https://poppler.freedesktop.org/) (`brew install poppler`), [`fbib`](https://github.com/mr-devs/fetchbib) (`uv tool install fetchbib`)

```bash
# 1. Clone the repo
git clone https://github.com/your-username/cc-synthesizer
cd cc-synthesizer

# 2. Drop PDFs into documents/
cp ~/papers/*.pdf documents/

# 3. Open Claude Code and run:
# /create-synthesis
# /build-html

# 4. Open synthesis/synthesis.html in your browser
```

See [`docs/getting-started.md`](docs/getting-started.md) for full instructions.

## Contents

- [`.claude/`](.claude/) — Claude Code skills and reference files
- [`documents/`](documents/) — Drop your PDFs here
- [`summaries/`](summaries/) — Auto-generated per-document summaries
- [`synthesis/`](synthesis/) — Auto-generated synthesis and HTML
- [`server/`](server/) — Phase 2: local server for in-page Claude interaction
- [`docs/`](docs/) — Documentation
```

- [ ] **Step 5: Write directory READMEs**

`documents/README.md`:
```markdown
# documents/

Drop PDF files here. Subdirectories are allowed and their structure will be mirrored in `summaries/`.

Use the naming convention `Author_-_YYYY_-_Title.pdf` when possible, or run `/cleanup-pdf-names documents/` to sanitize filenames automatically.

PDFs in this directory are not version-controlled.
```

`summaries/README.md`:
```markdown
# summaries/

Auto-generated markdown summaries, one per PDF in `documents/`. Directory structure mirrors `documents/`.

Also contains `manifest.json`, which maps each BibTeX key to the absolute paths of its source PDF and summary file. This file is consumed by `/build-html`.

Do not edit files here manually — regenerate by re-running `/summarize-documents`.
```

`synthesis/README.md`:
```markdown
# synthesis/

Auto-generated files produced by `/create-synthesis` and `/build-html`:

- `synthesis.md` — Markdown synthesis document with inline citations
- `synthesis-memory.md` — Persistent context for Claude Code sessions (edit and maintain this)
- `synthesis.html` — Interactive HTML page (open in browser)

`synthesis-memory.md` is the one file here you should actively maintain: add conclusions you've reached and notes about your framing. It is included automatically in every "Ask Claude" prompt from the HTML page.
```

`server/README.md`:
```markdown
# server/

**Phase 2 — not yet implemented.**

This directory will contain a lightweight FastAPI server that enables in-page Claude interaction
from `synthesis/synthesis.html`, replacing the Phase 1 clipboard prompt builder.

See the design spec at `docs/superpowers/specs/2026-03-19-pdf-synthesizer-design.md` for details.
```

- [ ] **Step 6: Write `synthesis-guidance.md` template**

```markdown
# Synthesis Guidance

This file is optional. If present, `/create-synthesis` reads it as framing before generating the synthesis.
Edit or replace this content with your own goals. The format is flexible — use whatever is most useful.

## Topic

[What is this corpus about? One sentence.]

## My goal

[What do I want to understand? What question am I trying to answer?]

## Suggested structure

[Optional: suggest how to organize the synthesis — by theme, by method, chronologically, etc.]

## Specific things to look for

[Optional: specific concepts, debates, or patterns you want the synthesis to highlight]

## Audience

[Optional: who will read this? A newcomer? An expert? Yourself in 6 months?]
```

- [ ] **Step 7: Commit scaffolding**

```bash
cd /Users/mdeverna/Documents/Projects/cc-synthesizer
git add README.md CLAUDE.md .gitignore synthesis-guidance.md
git add documents/README.md summaries/README.md synthesis/README.md server/README.md
git commit -m "feat: initial repo scaffolding"
```

---

## Task 2: Copy Reused Skills

**Files:**
- Create: `.claude/skills/cleanup-pdf-names/SKILL.md`
- Create: `.claude/skills/cleanup-pdf-names/scripts/cleanup_pdf_names.sh`
- Create: `.claude/skills/pdf-extraction/SKILL.md`
- Create: `.claude/skills/pdf-extraction/scripts/pdf_extract.sh`

**Source:** `/Users/mdeverna/Documents/Projects/cc-research-project-template/.claude/skills/`

- [ ] **Step 1: Copy cleanup-pdf-names**

```bash
cp /Users/mdeverna/Documents/Projects/cc-research-project-template/.claude/skills/cleanup-pdf-names/SKILL.md \
   /Users/mdeverna/Documents/Projects/cc-synthesizer/.claude/skills/cleanup-pdf-names/SKILL.md

cp /Users/mdeverna/Documents/Projects/cc-research-project-template/.claude/skills/cleanup-pdf-names/scripts/cleanup_pdf_names.sh \
   /Users/mdeverna/Documents/Projects/cc-synthesizer/.claude/skills/cleanup-pdf-names/scripts/cleanup_pdf_names.sh

chmod +x /Users/mdeverna/Documents/Projects/cc-synthesizer/.claude/skills/cleanup-pdf-names/scripts/cleanup_pdf_names.sh
```

- [ ] **Step 2: Copy pdf-extraction**

```bash
cp /Users/mdeverna/Documents/Projects/cc-research-project-template/.claude/skills/pdf-extraction/SKILL.md \
   /Users/mdeverna/Documents/Projects/cc-synthesizer/.claude/skills/pdf-extraction/SKILL.md

cp /Users/mdeverna/Documents/Projects/cc-research-project-template/.claude/skills/pdf-extraction/scripts/pdf_extract.sh \
   /Users/mdeverna/Documents/Projects/cc-synthesizer/.claude/skills/pdf-extraction/scripts/pdf_extract.sh

chmod +x /Users/mdeverna/Documents/Projects/cc-synthesizer/.claude/skills/pdf-extraction/scripts/pdf_extract.sh
```

- [ ] **Step 3: Smoke test cleanup-pdf-names**

In a Claude Code session in `/Users/mdeverna/Documents/Projects/cc-synthesizer`:
```
/cleanup-pdf-names documents/
```
Expected: skill lists PDFs, renames any with spaces/special chars, reports results. If PDF filenames are already clean, it reports "0 files renamed."

- [ ] **Step 4: Smoke test pdf-extraction**

```bash
# Verify the script works directly
.claude/skills/pdf-extraction/scripts/pdf_extract.sh first "documents/your-test.pdf" 2
```
Expected: First 2 pages of text printed to stdout.

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/cleanup-pdf-names/ .claude/skills/pdf-extraction/
git commit -m "feat: copy reused skills from research template"
```

---

## Task 3: Reference Files

**Files:**
- Create: `.claude/reference/bibtex-format.md`
- Create: `.claude/reference/summary-format.md`
- Create: `.claude/reference/synthesis-format.md`
- Create: `.claude/reference/html-template-notes.md`

- [ ] **Step 1: Copy bibtex-format.md**

```bash
cp /Users/mdeverna/Documents/Projects/cc-research-project-template/.claude/reference/bibtex-format.md \
   /Users/mdeverna/Documents/Projects/cc-synthesizer/.claude/reference/bibtex-format.md
```

- [ ] **Step 2: Write `summary-format.md`**

```markdown
# Summary Format Reference

## File Naming

- Filename = BibTeX key exactly: `{BibTeXKey}.md`
- BibTeX entry must exist in `references.bib` before summary is written

## Directory Structure

Summaries mirror the `documents/` subdirectory structure:

| Source PDF | Summary |
|------------|---------|
| `documents/topic/file.pdf` | `summaries/topic/{BibKey}.md` |
| `documents/file.pdf` | `summaries/{BibKey}.md` |

## Metadata Block (All Types)

```markdown
# {Document Title}

## Metadata
- **Authors/Organization:** {Author1, Author2 — or organization name}
- **Year:** {YYYY}
- **Source:** {Journal / Conference / Publisher / Organization / arXiv [Preprint]}
- **DOI/URL:** [{DOI or URL}]({link}) — or "Not available"
- **BibTeX Key:** `{AuthorYearKeyword}`
- **Document type:** {Academic paper | Industry report | White paper | Book chapter | Technical documentation | Other}
```

## Section Templates by Document Type

### Academic Paper
```markdown
## Main Takeaways
- {Most important finding or contribution — include specific numbers when available}
- {Second key finding}
- {Third key finding}
- {Fourth — if applicable}
- {Fifth — if applicable, max 5}

## Methodological Approach
- {Study design or primary method}
- {Data sources or sample size}
- {Key analytical approach}
- {Additional methods — if applicable, max 4}

## Limitations
- {Primary limitation acknowledged by authors}
- {Second limitation}
- {Third — if applicable, max 4}
```

### Industry / Government Report
```markdown
## Key Findings
- {Most significant finding}
- {Second finding}
- {Additional findings as needed}

## Approach
- {Methodology or data sources used}
- {Scope and coverage}

## Caveats
- {Limitations, conflicts of interest, or scope restrictions}
- {Additional caveats as needed}
```

### White Paper / Opinion Piece
```markdown
## Core Arguments
- {Primary claim or recommendation}
- {Supporting arguments}

## Supporting Evidence
- {Data, case studies, or references cited}

## Assumptions & Weaknesses
- {Unstated assumptions the argument depends on}
- {Counterarguments not addressed}
```

### Book Chapter
```markdown
## Central Ideas
- {Main thesis or contribution of this chapter}
- {Key concepts introduced}

## Argument Structure
- {How the chapter builds its case}

## Relationship to Broader Work
- {How this chapter fits into the book's overall argument}
```

### Technical Documentation
```markdown
## What It Does
- {Primary function or capability}
- {Key features}

## How It Works
- {Architecture or mechanism overview}
- {Key implementation details}

## Known Limitations
- {Constraints, known bugs, or unsupported cases}
```

## Edge Cases

### Missing DOI
Use `- **DOI/URL:** Not available` or provide URL if known.

### Non-peer-reviewed documents
Add a note in Caveats/Limitations: "This work has not been peer-reviewed."

### Very short documents (<3 pages)
If sections are absent: describe general content; note "Not explicitly addressed" where applicable.

### Unknown document type
Default to Academic Paper template; note actual type in the Metadata block.
```

- [ ] **Step 3: Write `synthesis-format.md`**

```markdown
# Synthesis Format Reference

## File Location

`synthesis/synthesis.md`

## Citation Syntax

Inline citations use BibTeX key notation: `[Author2024Keyword]`

- Every factual claim must be tied to at least one citation
- Multiple citations: `[Jones2022Debate, Lee2024Review]`
- Keys must match entries in `references.bib`

## Document Structure

```markdown
# {Topic Title}

*Synthesis of {N} documents. Generated {YYYY-MM-DD}.*

## Reading Guide

Recommended entry points for newcomers:

1. **[BibKey]** — {One sentence on why to read this first}
2. **[BibKey]** — {Rationale}
3-5 entries max.

## Overview

1–2 paragraphs orienting the reader to the topic and the corpus. What is this field/topic about? What kinds of documents make up this corpus? What is the scope?

## Major Themes

### {Theme Name}

Prose synthesis of what the corpus says about this theme. Every claim tied to a citation. [BibKey]

### {Theme Name}

...

## Key Tensions & Debates

What do sources disagree on? Why? What are the stakes of each position? [BibKey, BibKey]

## Points of Consensus

What do most or all sources agree on? [BibKey]

## Methodological Patterns

*(Omit or adapt for non-academic corpora)*

How do documents in this corpus approach the topic methodologically? What patterns emerge?

## Notable Gaps

What does this corpus not address? What questions remain unanswered?

## Citation Index

| BibTeX Key | One-line description |
|---|---|
| Smith2023Finding | Smith et al. study of X using Y method |
| Jones2022Debate | Jones critique of the X framework |
```

## Adaptation Rules

### Small corpus (<5 documents)
Merge "Major Themes" and "Key Tensions" into a single "Key Ideas" section. Omit "Points of Consensus" and "Methodological Patterns" if they would be trivial.

### Non-academic corpus
Replace "Methodological Patterns" with "How Sources Approach the Topic." Adapt language throughout to suit the document types present.

### User-provided guidance
If `synthesis-guidance.md` or a freetext argument is provided, it takes priority over default section structure. Honor the user's framing first, then fill in standard sections that the guidance doesn't cover.
```

- [ ] **Step 4: Write `html-template-notes.md`**

```markdown
# HTML Template Notes

Instructions for the `build-html` skill on generating `synthesis/synthesis.html`.

## Output Requirements

- Single self-contained file: all CSS and JS embedded inline
- No external CDN calls, no external fonts, no external scripts
- Must open correctly from `file://` (no server required)

## Page Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{H1 of synthesis.md}</title>  <!-- used as synthesisTopic in Phase 2 payload -->
  <style>/* all CSS inline */</style>
</head>
<body>
  <header>
    <h1>{synthesis title}</h1>
    <p class="meta">{date generated}</p>
  </header>
  <div class="layout">
    <nav class="sidebar"><!-- section links --></nav>
    <main class="content"><!-- synthesis body --></main>
  </div>
  <div id="tooltip" class="tooltip hidden"></div>
  <div id="ask-claude-btn" class="ask-btn hidden">Ask Claude</div>
  <div id="toast" class="toast hidden"></div>
  <script>/* all JS inline */</script>
</body>
</html>
```

## `<cite>` Element Requirements

Every `[BibKey]` in synthesis.md becomes a `<cite>` element. Required data attributes:

```html
<cite
  data-key="{BibTeX key}"
  data-title="{full title from references.bib}"
  data-authors="{authors from references.bib}"
  data-year="{year}"
  data-venue="{journal/conference/publisher — empty string if absent}"
  data-doi="{bare DOI string — empty string if absent}"
  data-pdf="{absolute file:// path to PDF from manifest.json}"
  data-summary="{absolute file:// path to summary .md from manifest.json}"
>
  [{BibKey}]
</cite>
```

Path resolution: paths in `data-pdf` and `data-summary` come from `manifest.json` and are already absolute. The `file://` prefix must be prepended if not already present.

If a BibKey has no entry in `references.bib`: render `<cite data-key="{key}">[{key}]</cite>` with no other attributes. List missing keys in a warning comment at the bottom of the HTML.

If a BibKey has a `references.bib` entry but no `manifest.json` entry: populate metadata attributes from `references.bib`; leave `data-pdf` and `data-summary` as empty strings.

## Citation Tooltip

Shown on `mouseenter` on any `<cite>` element. Structure:

```html
<div class="tooltip">
  <strong>{data-title}</strong>
  <p>{data-authors} ({data-year})</p>
  <p>{data-venue}</p>
  <div class="tooltip-links">
    <!-- "Open source": if data-doi non-empty, href = "https://doi.org/{data-doi}"
         else if data-pdf non-empty, href = data-pdf
         else omit link -->
    <a href="{source-url}" target="_blank">Open source</a>
    <!-- "View summary": only if data-summary non-empty -->
    <a href="{data-summary}" target="_blank">View summary</a>
  </div>
</div>
```

Tooltip must close on `mouseleave` and be positioned near the citation element.

## Text Highlight → Ask Claude Button

1. Listen for `selectionchange` or `mouseup` events
2. When text is selected (non-empty `window.getSelection()`):
   - Show the `#ask-claude-btn` button positioned near the selection
3. When button is clicked:
   - Collect citations: any `<cite>` element whose text range overlaps the selection range, PLUS any `<cite>` elements that are siblings within the same block-level parent (paragraph or list item) as the selection
   - Call `handleAskClaude(payload)` with the assembled payload

## Clipboard Prompt Format

Built by `buildPrompt(payload)`:

```
## Context
You are helping me understand a synthesis about {synthesisTopic}.

## Selected text
"{selectedText}"

## Relevant citations in this passage
{for each citation:}
- BibKey: {key}
  Title: {title}
  Authors: {authors}
  Summary: {summary path}
  PDF: {pdf path}

## Synthesis memory
{memoryDoc contents, or omit this section if memoryDoc is null}

## My question
[Fill in your question here]
```

## Phase 2 Hook

The `handleAskClaude` function must be isolated in a clearly-commented block:

```javascript
/* =========================================================
   PHASE2_SERVER_HOOK
   Phase 1: copies assembled prompt to clipboard.
   Phase 2: replace this function to POST to localhost:8000
   and render streaming response in the side panel.

   Payload contract:
   {
     selectedText:  string,
     citations:     Array<{ key, title, authors, year, venue, doi, pdf, summary }>,
     synthesisTopic: string,          // document.title (= synthesis.md H1)
     memoryDoc:      string | null,   // synthesis-memory.md contents or null
     pdfPaths:       string[],        // convenience alias from citations[*].pdf
     summaryPaths:   string[]         // convenience alias from citations[*].summary
   }
   ========================================================= */
function handleAskClaude(payload) {
  const prompt = buildPrompt(payload);
  navigator.clipboard.writeText(prompt);
  showToast('Prompt copied — paste into Claude Code.');
}
```

## Design Notes

- Clean, readable typography (system font stack is fine)
- Sidebar has section links generated from synthesis.md headings
- Mobile-friendly is a nice-to-have, not required
- No dark mode required
```

- [ ] **Step 5: Commit reference files**

```bash
git add .claude/reference/
git commit -m "feat: add reference files for all skills"
```

---

## Task 4: summarize-documents Skill

**Files:**
- Create: `.claude/skills/summarize-documents/SKILL.md`

- [ ] **Step 1: Write `summarize-documents/SKILL.md`**

```markdown
---
name: summarize-documents
description: Generate per-document markdown summaries from PDFs. Detects document type and adapts the summary structure accordingly. Updates references.bib and summaries/manifest.json.
argument-hint: <path/to/pdf-or-directory> ["optional context"]
allowed-tools: Bash, Read, Write, Edit, Glob
---

# Summarize Documents

Generate structured markdown summaries from PDF files.

## Input

$ARGUMENTS

## Reference

@.claude/reference/summary-format.md
@.claude/reference/bibtex-format.md

## Instructions

### Step 1: Parse Arguments

Split $ARGUMENTS into:
- **Path** (required): first token — file or directory path; resolve relative paths from project root
- **Context** (optional): remaining text after the path, used to orient extraction and framing

If path is empty, ask the user for a path.

---

### Step 2: Identify PDFs

**Single file:** Verify it exists and ends in `.pdf`.
**Directory:** Find all `.pdf` files recursively using `documents/**/*.pdf` or `{path}/**/*.pdf`.

Build a list of `{full_path, subdir}` pairs where `subdir` is the path segment between the root `documents/` directory and the file (empty string if PDF is directly in `documents/`).

Report count. If zero, inform user and stop.

---

### Step 3: Load Existing State

1. Read `references.bib` if it exists; extract existing BibTeX keys for duplicate checking
2. Read `summaries/manifest.json` if it exists; load existing key→path mappings
3. For each PDF, check if `summaries/{subdir}/{BibKey}.md` already exists → mark as **skip** or **process**

Report: existing bib entries, existing summaries, to process, to skip.

---

### Step 4: Process Each PDF

For each PDF marked **process**:

#### 4a. Fetch Citation Entry

1. Search for DOI in the PDF:
   ```bash
   .claude/skills/pdf-extraction/scripts/pdf_extract.sh search "{pdf_path}" "doi"
   ```
2. If DOI found: `fbib "{doi}"` — if successful, use this BibTeX entry (regenerate key per bibtex-format.md)
3. If no DOI or fbib fails: extract first page and try title-based search: `fbib "Full Paper Title"`
4. If both fail: extract first 2 pages manually and construct entry per @.claude/reference/bibtex-format.md
5. Append new entry to `references.bib` (create file if absent); verify no duplicate key

#### 4b. Detect Document Type

Extract first page:
```bash
.claude/skills/pdf-extraction/scripts/pdf_extract.sh first "{pdf_path}" 1
```

Classify as one of: Academic paper, Industry/government report, White paper/opinion, Book chapter, Technical documentation, Other. Use title, abstract, and any venue/publisher info visible on the first page.

If context provided in $ARGUMENTS, it may override or inform this classification (e.g., "these are industry reports").

#### 4c. Extract Content (Token-Efficient)

For papers ≤8 pages: extract all:
```bash
.claude/skills/pdf-extraction/scripts/pdf_extract.sh all "{pdf_path}"
```

For papers >8 pages: extract strategically:
1. First page (already done in 4b)
2. Locate key sections:
   ```bash
   .claude/skills/pdf-extraction/scripts/pdf_extract.sh search-pages "{pdf_path}" "Method"
   .claude/skills/pdf-extraction/scripts/pdf_extract.sh search-pages "{pdf_path}" "Result"
   .claude/skills/pdf-extraction/scripts/pdf_extract.sh search-pages "{pdf_path}" "Limitation"
   .claude/skills/pdf-extraction/scripts/pdf_extract.sh search-pages "{pdf_path}" "Conclusion"
   ```
3. Extract only those pages. Target 4–6 pages maximum.

#### 4d. Write Summary

1. Determine output path:
   - Subdir present: `summaries/{subdir}/{BibKey}.md`
   - Flat (no subdir): `summaries/{BibKey}.md`
   - Create directory if needed
2. Write summary using the template for the detected document type per @.claude/reference/summary-format.md
3. If context was provided in $ARGUMENTS, use it to orient emphasis (e.g., "focus on methodology")

#### 4e. Update Manifest

Upsert an entry in `summaries/manifest.json` (create file if absent; add or overwrite the entry for this BibTeX key):

```json
{
  "Smith2023Finding": {
    "pdf": "/absolute/path/to/documents/subdir/Smith_-_2023_-_Title.pdf",
    "summary": "/absolute/path/to/summaries/subdir/Smith2023Finding.md"
  }
}
```

Use the absolute filesystem path (not a relative path).

---

### Step 5: Compact (Every 5 Documents)

After every 5 documents:
```
/compact Compacting after 5 summaries. PRESERVE: (1) task: summarize-documents, (2) documents processed with output paths, (3) documents remaining, (4) warnings/errors, (5) manifest and bib state. DISCARD: all extracted PDF text. Replace PDF extractions with: "Summarized: [filename] → [output path]".
```

---

### Step 6: Report Results

```
Summarize Documents — Results
==============================
PDFs found:           {total}
Skipped (exists):     {skipped}
New summaries:        {created}
  Via fbib (DOI):       {doi_count}
  Via fbib (title):     {title_count}
  Via manual extract:   {manual_count}

New summaries written:
- {path1}
- {path2}

Warnings (if any):
- {filename}: {warning}
```

---

## Edge Cases

### Unreadable PDF
Report "Could not read PDF: {filename}", skip, continue.

### Non-standard filename
If filename doesn't match `Author - YYYY - Title` or `Author_-_YYYY_-_Title`, extract first page to get metadata rather than parsing filename.

### Missing venue or DOI
Per @.claude/reference/bibtex-format.md — omit the field; use `@misc` if venue unknown.
```

- [ ] **Step 2: Smoke test summarize-documents**

In a Claude Code session in `/Users/mdeverna/Documents/Projects/cc-synthesizer`:
```
/summarize-documents documents/
```

Expected:
- `summaries/{BibKey}.md` created with correct metadata block and type-appropriate sections
- `references.bib` created with a valid BibTeX entry
- `summaries/manifest.json` created with an entry mapping the BibTeX key to absolute paths
- Summary output report printed

Verify manually:
```bash
cat summaries/manifest.json
cat references.bib
ls summaries/
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/summarize-documents/
git commit -m "feat: add summarize-documents skill"
```

---

## Task 5: create-synthesis Skill

**Files:**
- Create: `.claude/skills/create-synthesis/SKILL.md`

- [ ] **Step 1: Add a second test PDF and regenerate summaries**

Add at least one more PDF to `documents/` (the synthesis is more meaningful with 2+ documents). Run `/summarize-documents documents/` to generate summaries for both.

- [ ] **Step 2: Write `create-synthesis/SKILL.md`**

```markdown
---
name: create-synthesis
description: Generate a cross-cutting synthesis document from all summaries in summaries/. Reads synthesis-guidance.md if present. Can trigger the full pipeline if summaries are missing.
argument-hint: ["optional context or guidance" | path/to/guidance-doc]
allowed-tools: Bash, Read, Write, Edit, Glob, AskUserQuestion, Skill
---

# Create Synthesis

Generate a cross-cutting synthesis from all per-document summaries.

## Input

$ARGUMENTS

## Reference

@.claude/reference/synthesis-format.md
@.claude/reference/bibtex-format.md

## Instructions

### Step 1: Parse Arguments

If $ARGUMENTS is provided:
- If it resolves to a readable file path on disk → treat as a guidance document, read its contents as framing
- Otherwise → treat as freetext context orienting the synthesis structure

Also check for `synthesis-guidance.md` at the repo root. If it exists and no argument was provided, read it as the default guidance document.

---

### Step 2: Check Pipeline State

1. Check for summaries in `summaries/` (look for `*.md` files excluding `manifest.json`)
2. **If summaries found:** proceed to Step 3
3. **If no summaries found, but PDFs exist in `documents/`:**
   - Use AskUserQuestion: *"No summaries found. I can run the full pipeline (cleanup → summarize → synthesize). Should I proceed? If yes, is there any context you'd like to pass to the summarization step? (This is separate from any synthesis guidance you've already provided.)"*
   - If user confirms: invoke `cleanup-pdf-names` skill with `documents/` as argument, then invoke `summarize-documents` skill with `documents/` and the summarize-step context from the user's answer
   - If `summarize-documents` completes with zero summaries: halt with error "No summaries could be created. Check that PDFs are readable."
   - If `summarize-documents` completes with partial summaries (some PDFs failed): use AskUserQuestion to ask whether to proceed with the partial set or abort
   - After successful summarization, continue to Step 3 using the synthesis context from the original $ARGUMENTS
4. **If no PDFs found:** inform user "No PDFs found in documents/. Please add PDFs before running /create-synthesis." and stop.

---

### Step 3: Load All Summaries

1. Find all `*.md` files in `summaries/` recursively (exclude `manifest.json`)
2. Read each summary file
3. Read `references.bib`

**Large corpus handling (>30 summaries):**
Inform the user: "This corpus has {N} summaries. For best results, run /create-synthesis in a fresh Claude Code context. Processing in thematic passes to manage token budget."
Process summaries in thematic passes: first pass reads all metadata blocks and Main Takeaways to identify themes; subsequent passes read full summaries for specific themes. Compact between passes.

---

### Step 4: Generate Synthesis

Using the loaded summaries, guidance (if any), and `references.bib`:

1. Identify 3–7 major themes (fewer for small corpora)
2. Identify key tensions and debates
3. Identify points of consensus
4. Identify methodological patterns (if academic corpus)
5. Identify notable gaps
6. Select 3–5 recommended entry points for the Reading Guide

Write `synthesis/synthesis.md` per @.claude/reference/synthesis-format.md:
- Every factual claim tied to a citation `[BibKey]`
- Keys must match entries in `references.bib`
- Structure adapts to corpus size and type (see adaptation rules in synthesis-format.md)
- If guidance was provided, honor it first, then fill in standard sections

---

### Step 5: Write Synthesis Memory Stub

Create `synthesis/synthesis-memory.md` with the following structure:

```markdown
# Synthesis Memory

*Auto-generated stub by /create-synthesis on {date}. Edit and maintain this file across sessions.*

## Topic
{Derived from the synthesis title / overview}

## Corpus
{N} documents. BibTeX keys: {comma-separated list of all keys used in synthesis}

## Key themes
{Bullet list from Major Themes section of synthesis.md}

## Conclusions reached
*(Add notes here as you work through the synthesis)*

## User framing notes
*(Add context about your goals, audience, or open questions)*
```

If `synthesis/synthesis-memory.md` already exists, do NOT overwrite it — the user may have added notes. Instead, update only the "Topic", "Corpus", and "Key themes" sections if they differ.

---

### Step 6: Report Results

```
Create Synthesis — Results
===========================
Summaries read:       {N}
Citations used:       {M}
Output:               synthesis/synthesis.md
Memory stub:          synthesis/synthesis-memory.md ({created|already exists, not overwritten})

Run /build-html to generate the interactive HTML page.
```
```

- [ ] **Step 3: Smoke test create-synthesis**

In a Claude Code session in `/Users/mdeverna/Documents/Projects/cc-synthesizer`:
```
/create-synthesis "focus on key findings and methodological approaches"
```

Expected:
- `synthesis/synthesis.md` created with all sections from synthesis-format.md
- All citations in synthesis.md are valid BibTeX keys present in `references.bib`
- `synthesis/synthesis-memory.md` created as a stub
- Report printed

Verify:
```bash
cat synthesis/synthesis.md
cat synthesis/synthesis-memory.md
```

Also test the full-pipeline trigger by temporarily moving summaries aside:
```bash
mv summaries summaries_backup
# Run /create-synthesis in Claude Code — should ask to run full pipeline
mv summaries_backup summaries
```

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/create-synthesis/
git commit -m "feat: add create-synthesis skill"
```

---

## Task 6: build-html Skill

**Files:**
- Create: `.claude/skills/build-html/SKILL.md`

- [ ] **Step 1: Write `build-html/SKILL.md`**

```markdown
---
name: build-html
description: Convert synthesis/synthesis.md into an interactive HTML page with citation hover tooltips and an "Ask Claude" clipboard prompt builder.
argument-hint: ["optional page title or audience note"]
allowed-tools: Bash, Read, Write, Glob
---

# Build HTML

Convert `synthesis/synthesis.md` into a self-contained interactive HTML page.

## Input

$ARGUMENTS (optional: page title or audience note)

## Reference

@.claude/reference/html-template-notes.md

## Instructions

### Step 1: Check Prerequisites

1. Verify `synthesis/synthesis.md` exists — if not, halt: "Run /create-synthesis first."
2. Verify `references.bib` exists — if not, halt: "references.bib not found. Run /summarize-documents first."
3. Check for `summaries/manifest.json` — if missing, warn: "manifest.json not found; citation file paths will be empty. Consider re-running /summarize-documents." Continue anyway.
4. Check for `synthesis/synthesis-memory.md` — if present, read its full contents (used in clipboard prompts). If absent, memoryDoc = null.

---

### Step 2: Parse Inputs

1. Read `synthesis/synthesis.md` fully
2. Extract H1 heading → use as `<title>` and `synthesisTopic`
3. If $ARGUMENTS provided, use as page title instead of H1
4. Parse `references.bib` → build a map of BibTeX key → `{title, authors, year, venue, doi}`
5. Parse `summaries/manifest.json` → build a map of BibTeX key → `{pdf, summary}`
6. Find all `[BibKey]` patterns in synthesis.md; for each:
   - Look up in references.bib map → metadata (or empty if missing)
   - Look up in manifest map → paths (or empty strings if missing)
   - Record any keys missing from references.bib → will be listed as warnings

---

### Step 3: Render HTML

Build a complete, self-contained HTML file per @.claude/reference/html-template-notes.md.

Key rendering rules:
- Replace all `[BibKey]` occurrences with `<cite data-key="..." ...>[BibKey]</cite>` elements
- All paths in `data-pdf` and `data-summary`: prepend `file://` if the path is absolute but lacks the prefix; leave empty string as empty string
- Set `<title>` to `synthesisTopic`
- Convert Markdown headings, paragraphs, and lists to HTML
- Generate sidebar navigation links from the H2 headings
- Embed all CSS inline (no `<link>` tags)
- Embed all JS inline (no `<script src>` tags)
- Embed `synthesisMemory` as a JS const at the top of the inline script:
  ```javascript
  const SYNTHESIS_MEMORY = {memoryDoc contents as a JSON string, or null};
  ```
- Include the `PHASE2_SERVER_HOOK` comment block around `handleAskClaude`

---

### Step 4: Write Output

Write to `synthesis/synthesis.html`.

If any BibTeX keys were found in synthesis.md but not in references.bib, append a warning comment at the end of the HTML:
```html
<!-- WARNING: The following citation keys were not found in references.bib:
     [Key1], [Key2]
     These <cite> elements have no metadata. Re-run /summarize-documents if needed. -->
```

---

### Step 5: Report Results

```
Build HTML — Results
=====================
Input:      synthesis/synthesis.md
Output:     synthesis/synthesis.html
Citations:  {M} resolved, {W} missing from references.bib

Open synthesis/synthesis.html in your browser to view the interactive synthesis.
```

List any missing citation keys as warnings.
```

- [ ] **Step 2: Smoke test build-html**

In a Claude Code session:
```
/build-html
```

Expected:
- `synthesis/synthesis.html` created
- Report printed, any missing citations listed

Verify the HTML interactively:
```bash
open synthesis/synthesis.html   # macOS
```

Check:
1. Page loads without errors (check browser console)
2. Sidebar links are present and jump to correct sections
3. Hover over a `[BibKey]` citation → tooltip appears with title, authors, year
4. "Open source" link in tooltip opens DOI URL or local PDF
5. Select any text on the page → "Ask Claude" button appears
6. Click "Ask Claude" → toast appears, clipboard contains a well-formed prompt with the selected text and any nearby citations

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/build-html/
git commit -m "feat: add build-html skill"
```

---

## Task 7: Documentation

**Files:**
- Create: `docs/getting-started.md`
- Create: `docs/skills-reference.md`

- [ ] **Step 1: Write `docs/getting-started.md`**

```markdown
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

Verify:
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

For detailed framing, create a `synthesis-guidance.md` file at the repo root. `/create-synthesis` reads it automatically. See the template in this repo for structure.

## Using the HTML page

Open `synthesis/synthesis.html` in any browser (no server required):

- **Hover a citation** → see title, authors, year, and links to the source PDF and summary
- **Select text → "Ask Claude"** → a context-rich prompt is copied to clipboard. Paste it into a Claude Code session to ask questions about the passage

## Persistent context across sessions

Edit `synthesis/synthesis-memory.md` to record conclusions you've reached and framing notes. This file is automatically included in every "Ask Claude" clipboard prompt, so Claude has running context without re-explanation.

## Updating the synthesis

After adding new PDFs or editing summaries, re-run:
```
/summarize-documents documents/    # only processes new PDFs
/create-synthesis                  # regenerates synthesis.md
/build-html                        # regenerates synthesis.html
```
```

- [ ] **Step 2: Write `docs/skills-reference.md`**

```markdown
# Skills Reference

Quick reference for all available slash commands.

| Command | Description | Arguments |
|---|---|---|
| `/cleanup-pdf-names <path>` | Sanitizes PDF filenames: spaces → underscores, em/en dashes → hyphens | Path to file or directory |
| `/summarize-documents <path> ["context"]` | Generates per-document summaries, updates `references.bib` and `summaries/manifest.json` | Path + optional freetext context |
| `/create-synthesis ["context" or guidance-file]` | Generates cross-cutting synthesis from all summaries; triggers full pipeline if summaries are missing | Optional: freetext, file path, or omit (uses `synthesis-guidance.md` if present) |
| `/build-html ["title"]` | Converts `synthesis/synthesis.md` → `synthesis/synthesis.html` | Optional page title |

## Internal (not user-invocable)

| Skill | Purpose | Called by |
|---|---|---|
| `pdf-extraction` | Token-efficient PDF text extraction via `pdftotext` | `summarize-documents` |
```

- [ ] **Step 3: Commit documentation**

```bash
git add docs/getting-started.md docs/skills-reference.md
git commit -m "docs: add getting-started and skills-reference"
```

---

## Task 8: End-to-End Verification

- [ ] **Step 1: Clean state test**

```bash
cd /Users/mdeverna/Documents/Projects/cc-synthesizer
# Remove all generated files for a true clean-state test
rm -f references.bib
rm -rf summaries/ && mkdir -p summaries
rm -f synthesis/synthesis.md synthesis/synthesis-memory.md synthesis/synthesis.html
# (keep documents/ with test PDFs)

# Verify prerequisites are installed before proceeding
pdftotext -v
fbib --help
```

- [ ] **Step 2: Run full pipeline via single command**

In a Claude Code session:
```
/create-synthesis "focus on key methodologies and findings"
```

Confirm when prompted. Verify:
- `summaries/*.md` created for each PDF
- `summaries/manifest.json` populated
- `references.bib` populated
- `synthesis/synthesis.md` created with all 8 sections
- `synthesis/synthesis-memory.md` stub created
- All `[BibKey]` citations in synthesis.md match keys in `references.bib`

- [ ] **Step 3: Build HTML and verify interactivity**

```
/build-html
```

```bash
open synthesis/synthesis.html
```

Verify:
1. No console errors
2. Sidebar navigation works
3. Citation tooltip appears on hover with correct metadata
4. "Open source" link opens DOI URL
5. Text selection shows "Ask Claude" button
6. Clicking "Ask Claude" copies a valid, well-structured prompt to clipboard
7. Pasting the prompt into Claude Code gives Claude correct context (synthesis topic, selected text, citations)

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "feat: complete Phase 1 pipeline — all skills and docs"
```
