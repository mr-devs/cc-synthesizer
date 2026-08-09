---
name: create-synthesis
description: Generate a cross-cutting synthesis document from all summaries in summaries/. Reads synthesis-guidance.md if present. Can trigger the full pipeline if summaries are missing.
argument-hint: ["optional context or guidance" | path/to/guidance-doc]
allowed-tools: Bash, Read, Write, Edit, Glob, AskUserQuestion, Skill, Agent
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
2. Read each summary file fully — **but only for corpora of 30 or fewer summaries**. Above that, use the large-corpus handling below instead.
3. Read `synthesis/citations.json` (single `json.load()`) — always do this here, in the main context

**Large corpus handling (>30 summaries):**

Do not read every summary into this context. Fan out to `corpus-scout` subagents instead:

1. Inform the user: "This corpus has {N} summaries. Dispatching {K} scout agents to digest them in parallel."
2. Split the summary list into chunks of ~10 files each.
3. Dispatch one subagent per chunk with `subagent_type: corpus-scout`, passing that chunk's file paths and any guidance-document framing. The agent definition at `.claude/agents/corpus-scout.md` carries the return schema and the size budget; the dispatch prompt only needs the file list and framing.
4. **Cap at 15 concurrent** (the session limit is 20). For more than 15 chunks, dispatch in waves.
5. Merge the returned digests here in the main context: collapse overlapping themes, pool the tension and consensus lines, union the gaps.
6. Read in full only the summaries flagged under `NOTABLE`, plus any others you need in order to state a specific claim precisely. Do not bulk-read the rest.

Write Step 4's synthesis yourself, in this context — the scouts supply raw material, not prose.

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

### Step 5: Verify Citations and Claims

Dispatch a single subagent with `subagent_type: synthesis-verifier`. It reads `synthesis/synthesis.md`, `synthesis/citations.json`, and the summary files, then reports any citation that does not resolve and any claim its cited summary does not support. The agent definition at `.claude/agents/synthesis-verifier.md` carries the full procedure and return format — the dispatch prompt needs no detail beyond "verify the synthesis just written."

The verifier is read-only. Apply any fixes yourself, here in the main context:

- **UNRESOLVED** — the citation key is wrong or its metadata is missing. Correct the key if it is a typo; otherwise drop the citation and note it for the report (this usually means `/summarize-documents` needs re-running).
- **UNSUPPORTED / OVERSTATED** — rewrite the claim so it matches what the summary actually says, or cite a source that does support it.
- **MISATTRIBUTED** — swap in the correct citation key.

If the verifier returns `CLEAN`, change nothing. Record the count of problems found and fixed for Step 7.

---

### Step 6: Write Synthesis Memory Stub

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

### Step 7: Report Results

```
Create Synthesis — Results
===========================
Summaries read:       {N} ({"via {K} scout agents" if fan-out was used})
Citations used:       {M distinct citation keys}
Verification:         {"clean" | "{P} problems found, {Q} fixed"}
Output:               synthesis/synthesis.md
Memory stub:          synthesis/synthesis-memory.md ({created|already exists — updated topic/corpus/themes only})

Run /launch-synthesis to build the interactive HTML page and open it in the browser.
```
