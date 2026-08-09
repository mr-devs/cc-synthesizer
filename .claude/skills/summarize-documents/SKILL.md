---
name: summarize-documents
description: Generate per-document markdown summaries from PDFs. Detects document type and adapts the summary structure accordingly. Updates citations.json.
argument-hint: <path/to/pdf-or-directory> ["optional context"]
allowed-tools: Bash, Read, Write, Edit, Glob, Agent
---

# Summarize Documents

Generate structured markdown summaries from PDF files.

## Input

$ARGUMENTS

## Reference

@.claude/reference/citations-format.md

`@.claude/reference/summary-format.md` is deliberately *not* included here — in parallel mode the summaries are written by `pdf-summarizer` agents, which read it themselves. Read it on demand only in single-PDF sequential mode.

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

1. Read `synthesis/citations.json` if it exists; extract existing citation keys for duplicate checking
2. For each PDF, determine expected citation key by parsing filename (format: `Author_-_YYYY_-_Title.pdf` or `Author - YYYY - Title.pdf`):
   - First author surname: text before ` et al.`, ` and `, ` - `, or `_-_`
   - Year: 4-digit number after first ` - ` or `_-_`
   - Normalize surname: remove accents, remove hyphens
   - Check if `summaries/{subdir}/{BibKey}.md` already exists → mark as **skip** or **process**

Report: existing bib entries, existing summaries, to process, to skip.

---

### Step 4: Process Each PDF

**When processing multiple PDFs**, dispatch one `pdf-summarizer` subagent per PDF using the Agent tool with `subagent_type: pdf-summarizer`.

The agent definition at `.claude/agents/pdf-summarizer.md` carries the full per-PDF procedure — citation lookup, document-type detection, token-efficient extraction, and summary writing — along with the structured result contract. Each dispatch prompt only needs to supply:

- `pdf_path` — path to the PDF
- `subdir` — the subdirectory segment computed in Step 2 (empty string if none)
- `context` — the optional context parsed from $ARGUMENTS, if any

The agent's tool list (`Bash, Read, Write, Glob`) is enforced by its definition, and it is instructed never to touch `synthesis/citations.json` — that shared file is written once, in Step 5.

**Dispatch in waves of 15.** The concurrent subagent limit is 20 per session, so dispatching more than that in a single message fails with `Concurrent subagent limit reached`. Send at most 15 agents per message, collect that wave's result blocks, then dispatch the next wave. All waves are consolidated together in Step 5.

Each agent returns a `---BEGIN_AGENT_RESULT---` … `---END_AGENT_RESULT---` block. On success it carries `STATUS`, `PDF`, `BIBKEY`, `CITATION_METHOD`, `SUMMARY_PATH`, `CITATION_ENTRY` (a JSON object keyed by the citation key), and `WARNINGS`; on failure, `STATUS: error` with `PDF` and `ERROR`. The exact field formats live in `.claude/agents/pdf-summarizer.md` — Step 5 parses these fields.

**When processing a single PDF**, agents are optional. You may handle it directly in the main context by following the procedure in `.claude/agents/pdf-summarizer.md` — citation lookup, type detection, extraction, summary writing — reading `.claude/reference/summary-format.md` yourself for the templates, then doing 4a below. Skip Step 5 in that case.

#### 4a. Update Citations (sequential mode only)

When **not** using parallel agents, upsert the entry into `synthesis/citations.json` at the repo root (create file if absent; add or overwrite the entry for this citation key — do not remove existing entries for other keys). Include all fields: `title`, `authors`, `year`, `venue`, `doi`, `url`, `type`, `pdf`, `summary` (absolute filesystem paths).

Write atomically: write the full JSON to a temp file in the same directory, then rename to `synthesis/citations.json`.

---

### Step 5: Consolidate Agent Results (parallel mode only)

After every wave has returned, collect all structured result blocks together and consolidate once.

1. **Triage**: parse each `---BEGIN_AGENT_RESULT---` block; separate successes from errors (or unparseable output)
2. **Read existing `synthesis/citations.json`** from disk first (or `{}` if absent)
3. **Deduplicate citation keys**: two collision cases:
   - **Same-batch collision**: two agents returned the same `CitKey` for different PDFs → rename the second with a letter suffix (`b`, `c`, …) and note it in warnings
   - **Reprocess collision**: a batch key matches a pre-existing on-disk key for the same PDF → overwrite (true upsert)
   - A batch key that collides with a pre-existing on-disk key for a *different* PDF is treated as a same-batch collision and renamed
4. **Write `synthesis/citations.json`**: merge all new `CITATION_ENTRY` objects (parsed as JSON) into the existing dict; write atomically (temp file + rename)

---

### Step 6: Report Results

```
Summarize Documents — Results
==============================
PDFs found:           {total}
Skipped (exists):     {skipped}
Agents dispatched:    {dispatched}
  Succeeded:            {success_count}
  Failed:               {failed_count}

Citation methods (successful):
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

In parallel mode these are handled inside `pdf-summarizer`; the cases below apply to single-PDF sequential mode and to how you report agent failures.

### Unreadable PDF
Report "Could not read PDF: {filename}", skip the file, continue with remaining PDFs. An agent returning `STATUS: error` is counted in the Step 6 report and does not abort the batch.

### Non-standard filename
If filename doesn't match `Author - YYYY - Title` or `Author_-_YYYY_-_Title` format, extract first page to get metadata directly rather than parsing the filename.

### Missing venue or DOI
Per @.claude/reference/citations-format.md — omit the field; use `@misc` entry type if venue is unknown.
