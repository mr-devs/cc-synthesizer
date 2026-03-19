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
**Directory:** Find all `.pdf` files recursively using `{path}/**/*.pdf` glob pattern.

Build a list of `{full_path, subdir}` pairs where `subdir` is the path segment between the root `documents/` directory and the file's parent directory (empty string if PDF is directly in `documents/`).

Report count. If zero, inform user and stop.

---

### Step 3: Load Existing State

1. Read `references.bib` if it exists; extract existing BibTeX keys for duplicate checking
2. Read `summaries/manifest.json` if it exists; load existing key→path mappings
3. For each PDF, determine expected BibTeX key by parsing filename (format: `Author_-_YYYY_-_Title.pdf` or `Author - YYYY - Title.pdf`):
   - First author surname: text before ` et al.`, ` and `, ` - `, or `_-_`
   - Year: 4-digit number after first ` - ` or `_-_`
   - Normalize surname: remove accents, remove hyphens
   - Check if `summaries/{subdir}/{BibKey}.md` already exists → mark as **skip** or **process**

Report: existing bib entries, existing summaries, to process, to skip.

---

### Step 4: Process Each PDF

For each PDF marked **process**:

#### 4a. Fetch Citation Entry

1. Search for DOI in the PDF:
   ```bash
   .claude/skills/pdf-extraction/scripts/pdf_extract.sh search "{pdf_path}" "doi"
   ```
2. If DOI found: run `fbib "{doi}"` — if successful, use this BibTeX entry (regenerate key per @.claude/reference/bibtex-format.md)
3. If no DOI or fbib fails: extract first page and try title-based search:
   ```bash
   .claude/skills/pdf-extraction/scripts/pdf_extract.sh first "{pdf_path}" 1
   ```
   Then run `fbib "Full Paper Title"`
4. If both fail: use the already-extracted first page to construct the entry manually per @.claude/reference/bibtex-format.md
5. Append new entry to `references.bib` (create file if absent); verify no duplicate key

#### 4b. Detect Document Type

If first page not yet extracted, extract it:
```bash
.claude/skills/pdf-extraction/scripts/pdf_extract.sh first "{pdf_path}" 1
```

Classify as one of: Academic paper, Industry/government report, White paper/opinion, Book chapter, Technical documentation, Other. Use title, abstract, and any venue/publisher info visible on the first page.

If context provided in $ARGUMENTS, it may override or inform this classification (e.g., "these are industry reports").

#### 4c. Extract Content (Token-Efficient)

For papers ≤8 pages: extract all content:
```bash
.claude/skills/pdf-extraction/scripts/pdf_extract.sh all "{pdf_path}"
```

For papers >8 pages: extract strategically:
1. First page (may already be done from 4a/4b — reuse it, do not re-extract)
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
   - Create the output directory if it does not exist
2. Write summary using the template for the detected document type per @.claude/reference/summary-format.md
3. If context was provided in $ARGUMENTS, use it to orient emphasis in the summary (e.g., "focus on methodology")

#### 4e. Update Manifest

Upsert an entry in `summaries/manifest.json` (create file if absent; add or overwrite the entry for this BibTeX key — do not remove existing entries for other keys):

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

After processing every 5 documents, run:
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
Report "Could not read PDF: {filename}", skip the file, continue with remaining PDFs.

### Non-standard filename
If filename doesn't match `Author - YYYY - Title` or `Author_-_YYYY_-_Title` format, extract first page to get metadata directly rather than parsing the filename.

### Missing venue or DOI
Per @.claude/reference/bibtex-format.md — omit the field; use `@misc` entry type if venue is unknown.
