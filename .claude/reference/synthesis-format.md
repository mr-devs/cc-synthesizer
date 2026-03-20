# Synthesis Format Reference

## File Location

`synthesis/synthesis.md`

## Citation Syntax

Inline citations use `[@CitKey]` notation: `[@Author2024Keyword]`

- Every factual claim must be tied to at least one citation
- Multiple citations: `[@Jones2022Debate, @Lee2024Review]`
- Keys must match entries in `citations.json`

## Document Structure

```markdown
# {Topic Title}

*Synthesis of {N} documents. Generated {YYYY-MM-DD}.*

## Reading Guide

Recommended entry points for newcomers:

1. **[@BibKey]** — {One sentence on why to read this first}
2. **[@BibKey]** — {Rationale}
3-5 entries max.

## Overview

1–2 paragraphs orienting the reader to the topic and the corpus. What is this field/topic about? What kinds of documents make up this corpus? What is the scope?

## Major Themes

### {Theme Name}

Prose synthesis of what the corpus says about this theme. Every claim tied to a citation. [@BibKey]

### {Theme Name}

...

## Key Tensions & Debates

What do sources disagree on? Why? What are the stakes of each position? [@BibKey, @BibKey]

## Points of Consensus

What do most or all sources agree on? [@BibKey]

## Methodological Patterns

*(Omit or adapt for non-academic corpora)*

How do documents in this corpus approach the topic methodologically? What patterns emerge?

## Notable Gaps

What does this corpus not address? What questions remain unanswered?

## Citation Index

| Citation Key | One-line description |
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
