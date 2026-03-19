# cc-synthesizer Design Spec

**Date:** 2026-03-19
**Status:** Approved

---

## Overview

`cc-synthesizer` is a template GitHub repository that provides a Claude Code skill pipeline for ingesting any collection of PDF documents and helping a user understand them as quickly and accurately as possible. The output is an interactive HTML synthesis page with citation-linked prose and Claude Code integration for in-context querying.

The system is designed to be general-purpose (any document type, any topic), locally-run (no deployment, no persistent server), and shareable (clone the repo, drop in PDFs, run one command).

---

## Goals

- **Speed of understanding:** A user should be able to go from a folder of PDFs to a citable, cross-cutting synthesis in a single session.
- **Accuracy and traceability:** Every factual claim in the synthesis is tied to a specific source via a BibTeX-style citation key. Users can always trace a claim back to its origin.
- **Interactivity:** The HTML output lets users hover citations for metadata, open source documents, and query Claude Code about specific passages with full context pre-loaded.
- **Portability:** Works on any local machine with Claude Code and `pdftotext` installed. No server, no API key configuration beyond what Claude Code already uses.
- **Generality:** Works for academic papers, industry reports, white papers, technical documentation, book chapters, and any other PDF content.

---

## Phased Approach

### Phase 1 (this spec)
Complete, immediately useful pipeline: cleanup → summarize → synthesize → static interactive HTML. Claude integration via clipboard prompt builder (copy to paste into Claude Code).

### Phase 2 (future extension)
Local Python server (FastAPI) that intercepts the HTML interactions and handles them in-page with streaming Claude API responses. Defined extension point (`PHASE2_SERVER_HOOK`) is embedded in the Phase 1 HTML so Phase 2 requires no structural rework.

---

## Repository Structure

```
cc-synthesizer/
├── .claude/
│   ├── skills/
│   │   ├── cleanup-pdf-names/       # Reused from cc-research-project-template
│   │   ├── pdf-extraction/          # Reused from cc-research-project-template (internal)
│   │   ├── summarize-documents/     # Generalized from create-paper-summary
│   │   ├── create-synthesis/        # NEW: cross-cutting synthesis from summaries
│   │   └── build-html/              # NEW: renders synthesis.md → interactive HTML
│   └── reference/
│       ├── summary-format.md        # Generalized summary templates by document type
│       ├── synthesis-format.md      # Structure and conventions for synthesis documents
│       ├── bibtex-format.md         # BibTeX key naming and formatting rules (reused)
│       └── html-template-notes.md   # Spec for HTML output: structure, data attrs, JS contract
│
├── documents/                       # User drops PDFs here; subdirectories allowed
│   └── README.md
├── summaries/                       # Auto-generated per-document markdown summaries
│   └── README.md
├── synthesis/                       # Auto-generated synthesis.md + synthesis.html
│   └── README.md
├── server/                          # Phase 2 stub (README only in Phase 1)
│   └── README.md
├── docs/
│   ├── getting-started.md
│   ├── skills-reference.md
│   └── superpowers/specs/           # Design specs
├── synthesis-guidance.md            # Optional: user-authored framing doc for /create-synthesis
├── references.bib                   # Auto-generated BibTeX bibliography
├── README.md
└── CLAUDE.md
```

---

## End-to-End Pipeline

```
1. User drops PDFs into documents/ (flat or in subdirectories)
         ↓
2. /cleanup-pdf-names documents/
   Sanitizes filenames: spaces → underscores, em/en dashes → hyphens, etc.
         ↓
3. /summarize-documents documents/ ["optional context"]
   Extracts content from each PDF (token-efficient, targeted extraction)
   Detects document type and adapts summary structure accordingly
   Fetches citation entries via DOI/title lookup; falls back to manual extraction
   Appends new entries to references.bib
   Writes one .md summary per document to summaries/ (mirrors documents/ structure)
   Idempotent: skips documents that already have summaries
         ↓
4. /create-synthesis ["optional context" or path/to/guidance-doc]
   Reads all summaries + references.bib
   Reads synthesis-guidance.md if present (or file path provided as argument)
   Identifies themes, tensions, consensus, gaps across the corpus
   Writes synthesis/synthesis.md with inline citations ([BibKey])
   Every factual claim tied to at least one citation
         ↓
5. /build-html ["optional title or audience note"]
   Converts synthesis.md → synthesis/synthesis.html
   Embeds citation metadata as data attributes on <cite> elements
   Embeds Phase 1 interaction JavaScript (clipboard prompt builder)
   Embeds PHASE2_SERVER_HOOK comment for future extension
         ↓
6. User opens synthesis/synthesis.html in browser
```

**Single-command shortcut:** Running `/create-synthesis` on a fresh repo (no summaries yet) triggers `AskUserQuestion` to confirm, then executes the full pipeline automatically.

---

## Skills

### `cleanup-pdf-names`
Reused verbatim from `cc-research-project-template`. Sanitizes PDF filenames for consistent downstream processing. No user context input needed.

**Prerequisites:** PDFs in `documents/`

---

### `pdf-extraction` (internal)
Reused verbatim from `cc-research-project-template`. Provides targeted `pdftotext` extraction (first N pages, specific page, page range, search, full). Not user-invocable. Called by `summarize-documents`.

---

### `summarize-documents`

**Argument:** `<path/to/pdf-or-directory> ["optional freetext context"]`

**Optional context examples:**
- `"these are industry reports, not peer-reviewed papers"`
- `"focus on methodology and data sources"`
- `"I'm studying how organizations define AI risk — pay attention to definitions"`

**Behavior:**
1. Resolves target path; finds all PDFs recursively
2. If context provided, uses it to orient extraction focus and summary framing
3. For each unprocessed PDF:
   - Detects document type from content (academic paper, report, white paper, book chapter, technical doc)
   - Extracts content using `pdf-extraction` (token-efficient: targeted pages, not full text)
   - Attempts DOI search → `fbib` fetch for citation entry; falls back to title search, then manual extraction
   - Appends new entry to `references.bib`
   - Writes summary to `summaries/{subdir}/{BibKey}.md` using type-appropriate template. If the PDF is in `documents/` directly (no subdirectory), the summary is written to `summaries/{BibKey}.md` (no subdirectory prefix).
4. Skips documents with existing summaries (idempotent)
5. Compacts context after every 5 documents to manage token budget
6. Reports: processed, skipped, citation method used per document

**Large corpus handling:** For corpora >20 documents, the skill processes in batches of 10, compacting between batches. The user is advised to run `/create-synthesis` in a fresh Claude Code context when the corpus exceeds ~30 documents.

**Summary format adapts by document type:**

| Type | Sections |
|---|---|
| Academic paper | Main Takeaways · Methodological Approach · Limitations |
| Industry/gov report | Key Findings · Approach · Caveats |
| White paper / opinion | Core Arguments · Supporting Evidence · Assumptions & Weaknesses |
| Book chapter | Central Ideas · Argument Structure · Relationship to Broader Work |
| Technical documentation | What It Does · How It Works · Known Limitations |

All types share a consistent Metadata block (title, authors/org, year, publication/source, DOI or URL, BibTeX key).

---

### `create-synthesis`

**Argument:** `["optional freetext context" or path/to/guidance-doc]`

**Optional context examples:**
- `"I'm trying to understand the core debate about X"`
- `"organize themes around methodological approaches"`
- `"I'm a newcomer — prioritize foundational concepts first"`
- `path/to/my-outline.md` (a file with detailed goals, questions, or a rough outline)

**Guidance document:** If a file path is provided, the skill reads that file as framing before doing anything else. The format is flexible — an outline, a paragraph of goals, a list of questions to answer. Not required. The skill also checks for `synthesis-guidance.md` at the repo root as a default (no argument needed if that file exists).

**Pipeline check behavior:**
1. Checks `summaries/` for existing summaries
2. If none found but PDFs exist in `documents/`:
   - Uses `AskUserQuestion`: *"No summaries found. I can run the full pipeline (cleanup → summarize → synthesize). Should I proceed? Any context to pass to the summarize step?"*
   - If confirmed: invokes `cleanup-pdf-names` then `summarize-documents` via Skill tool (passing only the summarize-step context from the user's response), then continues to synthesis using the argument originally passed to `create-synthesis`
   - The summarize-step context and the synthesis-step context are kept separate: the former orients document extraction and summary framing; the latter orients the cross-cutting synthesis structure
3. If no PDFs found either: informs user and stops

**Synthesis output (`synthesis/synthesis.md`) structure:**

1. **Reading Guide** — 3–5 recommended entry-point documents with one-line rationale each
2. **Overview** — 1–2 paragraph orientation to the topic and corpus
3. **Major Themes** — thematic sections with descriptive headers, synthesis prose, inline citations
4. **Key Tensions & Debates** — where the literature disagrees and why
5. **Points of Consensus** — what sources agree on
6. **Methodological Patterns** — how documents approach the topic (omitted/adapted for non-academic corpora)
7. **Notable Gaps** — what the corpus does not address
8. **Citation Index** — all bib keys used with one-line descriptions

Citation syntax: `[Author2024Keyword]` inline. Every factual claim tied to at least one citation.

Structure adapts when corpus is small (<5 documents) or non-academic.

**Large corpus handling:** For corpora >30 summaries, `create-synthesis` reads summaries incrementally (in thematic passes rather than all at once) and compacts between passes. The skill notes when a fresh Claude Code context is recommended.

**Synthesis memory stub:** After writing `synthesis.md`, `create-synthesis` creates `synthesis/synthesis-memory.md` as a stub with the following sections pre-populated from the synthesis itself:
- **Topic:** (derived from synthesis title/overview)
- **Corpus:** (count and list of BibTeX keys)
- **Key themes:** (bullet list from Major Themes section)
- **Conclusions reached:** (empty — user fills this in over time)
- **User framing notes:** (empty — user fills this in)

The user maintains this file across sessions. It is included verbatim in every clipboard prompt generated by `build-html`.

---

### `build-html`

**Argument:** `["optional page title or audience note"]`

**Behavior:**
1. Reads `synthesis/synthesis.md` and `references.bib`
2. Renders a self-contained HTML file (all CSS/JS embedded inline, no external dependencies)
3. Replaces `[BibKey]` citations with interactive `<cite>` elements
4. Embeds Phase 1 interaction JavaScript
5. Writes `synthesis/synthesis.html`

---

## HTML Design

### Page Layout

```
┌─────────────────────────────────────────────────────┐
│  [Page title]                    [date generated]   │
├──────────────┬──────────────────────────────────────┤
│              │                                       │
│  Contents    │   Synthesis body with inline          │
│  (floating   │   citations                           │
│   sidebar)   │                                       │
│              │   ...research consistently finds      │
│  • Theme 1   │   X [Smith2023Finding] though Y       │
│  • Theme 2   │   remains contested                   │
│  • Tensions  │   [Jones2022Debate, Lee2024Review].   │
│  • Consensus │                                       │
│  • Gaps      │                                       │
└──────────────┴──────────────────────────────────────┘
```

Clean, readable typography. Single self-contained file. No external CDN calls.

### Citation Element Structure

All paths in `data-pdf` and `data-summary` are written as absolute `file://` paths at HTML generation time by `build-html`, using the repo root resolved at build time. This ensures "Open source" and "View summary" links work regardless of where the HTML file is opened.

```html
<cite data-key="Smith2023Finding"
      data-title="Full paper title"
      data-authors="Smith, J. and Doe, A."
      data-year="2023"
      data-venue="Journal of Example Research"
      data-doi="10.xxxx/xxxxx"
      data-pdf="file:///Users/username/projects/cc-synthesizer/documents/subdir/Smith_-_2023_-_Title.pdf"
      data-summary="file:///Users/username/projects/cc-synthesizer/summaries/subdir/Smith2023Finding.md">
  [Smith2023Finding]
</cite>
```

For flat placement (PDF directly in `documents/`, no subdirectory), paths omit the subdirectory:
- `data-pdf="file:///…/documents/Smith_-_2023_-_Title.pdf"`
- `data-summary="file:///…/summaries/Smith2023Finding.md"`

### Citation Hover Tooltip

Appears on hover, contains:
- Title, authors, year, venue
- "Open source" link → DOI URL if available, else `file://` path to local PDF
- "View summary" link → `file://` path to local `.md` summary

### Text Highlight → Ask Claude

When the user selects text anywhere on the page, a small floating **"Ask Claude"** button appears near the selection.

**Citation association rule:** When the user selects text, the JS collects all `<cite>` elements whose text range overlaps with the selection range, plus any `<cite>` elements that are siblings within the same block-level parent element (paragraph or list item) as the selection. This is the definition of "citations in/near the selection" used throughout.

**Clicking it assembles a context prompt:**

```
## Context
You are helping me understand a synthesis about [topic].

## Selected text
"[the highlighted passage]"

## Relevant citations in this passage
- BibKey: Smith2023Finding
  Title: Full paper title
  Authors: Smith, J. and Doe, A.
  Summary: file:///…/summaries/subdir/Smith2023Finding.md
  PDF: file:///…/documents/subdir/Smith_-_2023_-_Title.pdf

[Additional citations if multiple in/near selection]

## Synthesis memory
[Contents of synthesis/synthesis-memory.md if it exists]

## My question
[User fills this in after pasting]
```

Prompt is copied to clipboard. A toast notification confirms: *"Prompt copied — paste into Claude Code."*

### Synthesis Memory Document

`synthesis/synthesis-memory.md` is created after the first Claude Code conversation about this synthesis. It captures: the topic, corpus summary, key conclusions reached, and any user-specific framing. It is included automatically in every subsequent clipboard prompt, giving Claude running context across sessions without re-explanation.

### Phase 2 Hook

The clipboard behavior is isolated in a single clearly-commented JS block:

```javascript
/* =========================================================
   PHASE2_SERVER_HOOK
   Phase 1: copies assembled prompt to clipboard.
   Phase 2: replace this function to POST to localhost:8000
   and render streaming response in the side panel.

   Payload contract:
   {
     selectedText:  string,          // the highlighted text
     citations:     Array<{          // <cite> elements in/near selection
       key, title, authors, year,
       venue, doi, pdf, summary      // all as stored in data-* attrs
     }>,
     synthesisTopic: string,         // contents of the HTML <title> element
     memoryDoc:      string | null,  // full text of synthesis-memory.md, or null if absent
     pdfPaths:       string[],       // data-pdf values from citations (absolute file:// paths)
     summaryPaths:   string[]        // data-summary values from citations (absolute file:// paths)
   }
   ========================================================= */
function handleAskClaude(payload) {
  const prompt = buildPrompt(payload);
  navigator.clipboard.writeText(prompt);
  showToast("Prompt copied — paste into Claude Code.");
}
```

Phase 2 replaces only this function. All citation data, selection detection, and prompt assembly remain unchanged.

---

## Reference Files

### `summary-format.md`
Defines metadata block structure, section templates for each document type, formatting rules, and edge cases (missing DOI, non-research documents, very short documents).

### `synthesis-format.md`
Defines the full synthesis document structure, section-by-section guidance, citation syntax rules, rules for tying every claim to a source, and adaptation guidance for small or non-academic corpora.

### `bibtex-format.md`
Reused verbatim from `cc-research-project-template`. BibTeX key naming convention (`AuthorYearKeyword`), formatting rules, entry type examples.

### `html-template-notes.md`
Instructs `build-html` on: required `<cite>` data attributes, CSS/JS requirements, the `PHASE2_SERVER_HOOK` comment location and interface contract, tooltip structure, and clipboard prompt format.

---

## Prerequisites (for README/getting-started)

| Tool | Purpose | Install |
|---|---|---|
| `pdftotext` | Extract text from PDFs | `brew install poppler` |
| `fbib` (via [`fetchbib`](https://github.com/mr-devs/fetchbib)) | Fetch BibTeX from DOI or title | `uv tool install fetchbib` |

Claude Code handles all AI-powered steps. No separate API key configuration required.

---

## CLAUDE.md

Minimal — this repo is a tool, not a research project. Contains:
- Brief description of what the repo does
- Pointer to `docs/getting-started.md`
- Note that skills should be invoked via slash commands
- Note that `documents/` PDFs are not version-controlled (add to `.gitignore`)
