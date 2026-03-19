---
name: build-html
description: Convert synthesis/synthesis.md into a self-contained interactive HTML page with citation hover tooltips and an "Ask Claude" clipboard prompt builder.
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
3. Check for `summaries/manifest.json` — if missing, warn: "manifest.json not found; citation file paths will be empty. Re-running /summarize-documents will fix this." Continue anyway.
4. Check for `synthesis/synthesis-memory.md` — if present, read its full contents (used as `memoryDoc` in the clipboard prompt). If absent, `memoryDoc = null`.

---

### Step 2: Parse Inputs

1. Read `synthesis/synthesis.md` fully
2. Extract the H1 heading (first `# ` line) → use as both `<title>` and `synthesisTopic`
3. If $ARGUMENTS provided, use it as the page title instead of the H1
4. Parse `references.bib` → build a lookup map: BibTeX key → `{title, authors, year, venue, doi}`
   - `venue` = journal name, booktitle, or howpublished field (whichever is present)
   - `doi` = bare DOI string (without `https://doi.org/` prefix)
5. Parse `summaries/manifest.json` → build a lookup map: BibTeX key → `{pdf, summary}`
   - If `manifest.json` is absent, use empty map (paths will be empty strings)
6. Find all `[BibKey]` patterns in synthesis.md
7. For each key:
   - Look up in references.bib map → metadata (or mark as "missing from bib" if not found)
   - Look up in manifest map → absolute paths (or empty strings if not found)
8. Collect all keys missing from references.bib — these will be listed as warnings

---

### Step 3: Render HTML

Build a complete, self-contained HTML file per @.claude/reference/html-template-notes.md.

**Key rendering rules:**

1. Set `<title>` to `synthesisTopic`
2. Convert synthesis.md Markdown to HTML:
   - `# Heading` → `<h1>`; `## Heading` → `<h2 id="slug">` (slug = heading text lowercased, spaces → hyphens); `### Heading` → `<h3>`
   - Paragraphs → `<p>`
   - Bullet lists → `<ul><li>`
   - Bold `**text**` → `<strong>text</strong>`
   - Italic `*text*` → `<em>text</em>`
3. Replace every `[BibKey]` with a `<cite>` element populated from the reference and manifest maps. Use absolute `file://` paths in `data-pdf` and `data-summary`:
   - If the path in manifest.json already starts with `/`, prepend `file://`
   - If the path already starts with `file://`, use as-is
   - If no path (absent from manifest), use empty string for that attribute
4. Generate sidebar navigation from all `<h2>` elements (use their `id` attribute)
5. Embed the synthesis memory as a JS const at the top of the inline script:
   ```javascript
   const SYNTHESIS_MEMORY = {JSON.stringify(memoryDoc)};  // null if absent
   ```
6. Embed all CSS inline (no external stylesheets)
7. Embed all JS inline including the full citation tooltip logic, text-selection / Ask Claude button, and the PHASE2_SERVER_HOOK block (per html-template-notes.md)

**The inline JavaScript must implement:**
- Citation tooltip: show on `mouseenter`, hide on `mouseleave`; position near the element; populate from `data-*` attributes; "Open source" link = `https://doi.org/{data-doi}` if `data-doi` non-empty, else `data-pdf` if non-empty, else omit link; "View summary" link = `data-summary` if non-empty, else omit
- Text selection → Ask Claude button: listen for `mouseup`; show `#ask-claude-btn` near selection when text is selected; on click, collect citations (overlapping selection range OR in same block-level parent element), call `handleAskClaude(payload)` with `{selectedText, citations[], synthesisTopic, memoryDoc: SYNTHESIS_MEMORY, pdfPaths, summaryPaths}`
- `buildPrompt(payload)` builds the clipboard prompt string per html-template-notes.md format
- `showToast(message)` briefly shows then hides the `#toast` element
- The isolated `handleAskClaude(payload)` function with the `PHASE2_SERVER_HOOK` comment block

---

### Step 4: Write Output

Write the complete HTML to `synthesis/synthesis.html`.

If any BibTeX keys were found in synthesis.md but not in references.bib, append a warning HTML comment at the end of the file:
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
Citations:  {M resolved} / {M+W total} ({W} missing from references.bib)

Open synthesis/synthesis.html in your browser to view the interactive synthesis.
```

List any missing citation keys as warnings below the summary.
