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
@.claude/reference/citations-format.md

## Instructions

### Step 1: Parse Arguments

If $ARGUMENTS is provided:
- If the argument resolves to a readable file path on disk → treat as a guidance document, read its contents as framing
- Otherwise → treat as freetext context orienting the synthesis structure

Also check for `synthesis-guidance.md` in the `synthesis/` directory. If it exists and no argument was provided, read it as the default guidance document. If the file contains only the template placeholder text (i.e., it has not been customized), treat it as if it were absent.

---

### Step 2: Check Pipeline State

1. Check for summary files in `summaries/` (look for `*.md` files)
2. **If summaries found:** proceed to Step 3
3. **If no summaries found, but PDFs exist in `documents/`:**
   - Use AskUserQuestion: *"No summaries found. I can run the full pipeline (cleanup → summarize → synthesize). Should I proceed? If yes, is there any context you'd like to pass to the summarization step? (This is separate from any synthesis guidance you've already provided.)"*
   - If user confirms: invoke the `cleanup-pdf-names` skill with `documents/` as the path argument, then invoke the `summarize-documents` skill with `documents/` as the path argument and the summarize-step context from the user's answer (if any)
   - If `summarize-documents` completes with zero summaries: halt with error "No summaries could be created. Check that PDFs are readable and that pdftotext is installed."
   - If `summarize-documents` completes but some PDFs failed: use AskUserQuestion to ask "Summarization completed with some failures. Proceed with the {N} summaries that were created, or abort?" — proceed or abort per user response
   - After successful summarization, reload the summary list and continue to Step 3 using the synthesis context from the original $ARGUMENTS (not the summarize-step context)
4. **If no PDFs found either:** inform user "No PDFs found in documents/. Please add PDF files before running /create-synthesis." and stop.

---

### Step 3: Load All Summaries

1. Find all `*.md` files in `summaries/` recursively
2. Read each summary file fully
3. Read `synthesis/citations.json` (single `json.load()`)

**Large corpus handling (>30 summaries):**
Inform the user: "This corpus has {N} summaries. Processing in thematic passes to manage context. For best results, run this in a fresh Claude Code context."
Process summaries in thematic passes: first pass reads all Metadata blocks and the first section of each summary (Takeaways/Key Findings/Core Arguments) to identify themes; subsequent passes read full summaries for specific themes as needed. Use `/compact` between passes.

---

### Step 4: Generate Synthesis

Using the loaded summaries, guidance (if any), and `synthesis/citations.json`:

1. Identify 3–7 major themes (fewer for small corpora)
2. Identify key tensions and debates across documents
3. Identify points of consensus
4. Identify methodological patterns (if predominantly academic corpus)
5. Identify notable gaps
6. Select 3–5 recommended entry points for the Reading Guide

Write `synthesis/synthesis.md` per @.claude/reference/synthesis-format.md:
- Every factual claim tied to a citation `[@CitKey]`
- Keys must match entries in `citations.json`
- Structure adapts to corpus size and type per adaptation rules in synthesis-format.md
- If guidance was provided (file or freetext), honor it first, then fill in standard sections

---

### Step 5: Write Synthesis Memory Stub

Create `synthesis/synthesis-memory.md` with this structure:

```markdown
# Synthesis Memory

*Auto-generated stub by /create-synthesis on {YYYY-MM-DD}. Edit and maintain this file across sessions.*

## Topic
{Derived from the H1 title of synthesis.md}

## Corpus
{N} documents. Citation keys: {comma-separated list of all keys cited in synthesis.md}

## Key themes
{Bullet list derived from the Major Themes section headers of synthesis.md}

## Conclusions reached
*(Add notes here as you work through the synthesis)*

## User framing notes
*(Add context about your goals, audience, or open questions)*
```

**Important:** If `synthesis/synthesis-memory.md` already exists, do NOT overwrite it. The user may have added notes. Instead, check whether the Topic, Corpus, or Key themes sections are out of date and update only those specific fields. Leave "Conclusions reached" and "User framing notes" untouched.

---

### Step 6: Report Results

```
Create Synthesis — Results
===========================
Summaries read:       {N}
Citations used:       {M distinct citation keys}
Output:               synthesis/synthesis.md
Memory stub:          synthesis/synthesis-memory.md ({created|already exists — updated topic/corpus/themes only})

Run /launch-synthesis to build the interactive HTML page and open it in the browser.
```
