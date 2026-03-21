# Citations Format Reference

## Key Naming Convention

Format: `AuthorYearKeyword`

- **Author**: First author's surname only
- **Year**: 4-digit publication year
- **Keyword**: First significant word from title (skip "The", "A", "An", "On")

Examples: `Wardle2025Evolving`, `FernandezPichel2025Evaluating`, `Sun2024TrustingSearch`

Special cases: Hyphenated surnames → remove hyphen; Accents → remove; "et al." → first author only; Duplicate keys → append lowercase letter (e.g., `Author2024Keywordb`)

## `citations.json` Schema

Location: `{repo_root}/synthesis/citations.json`

```json
{
  "Smith2023Finding": {
    "title": "A Study of Things",
    "authors": "Smith, John and Doe, Alice",
    "year": "2023",
    "venue": "Journal of Examples",
    "doi": "10.1234/example",
    "url": "https://doi.org/10.1234/example",
    "type": "article",
    "pdf": "/absolute/path/to/documents/smith.pdf",
    "summary": "/absolute/path/to/summaries/Smith2023Finding.md"
  }
}
```

Fields:
- `title`, `authors`, `year` — required; empty string if unavailable
- `venue` — first of: journal > booktitle > howpublished
- `doi` — bare DOI number only (no `https://doi.org/` prefix); `""` if unavailable
- `url` — full URL (typically `https://doi.org/{doi}`); `""` if unavailable
- `type` — BibTeX entry type string (e.g., `"article"`, `"inproceedings"`, `"misc"`); `""` if unavailable
- `pdf` — absolute filesystem path to the source PDF; `""` if not yet known
- `summary` — absolute filesystem path to the summary `.md` file; `""` if not yet known

## Upsert Semantics

When `/summarize-documents` processes a PDF, its `citations.json` entry is written or overwritten in full. When a PDF is skipped (summary already exists), its entry is left unchanged.

## Venue Field Priority

1. `journal` field (for @article)
2. `booktitle` field (for @inproceedings)
3. `howpublished` field (for @misc)

## Source Metadata

Use `fbib "{doi}"` or `fbib "Full Paper Title"` to fetch BibTeX from which to extract fields. Extract: `title`, `author` → `authors`, `year`, venue (per priority above), `doi`, `url`, entry type.

## Authors Format

`Lastname, Firstname and Lastname2, Firstname2` — preserve as returned by `fbib`.
