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
- **Citation Key:** `{AuthorYearKeyword}`
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
