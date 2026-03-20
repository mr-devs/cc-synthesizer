# Skills Reference

Quick reference for all available slash commands.

| Command | Description | Arguments |
|---|---|---|
| `/cleanup-pdf-names <path>` | Sanitizes PDF filenames: spaces → underscores, em/en dashes → hyphens | Path to file or directory |
| `/summarize-documents <path> ["context"]` | Generates per-document summaries, updates `references.bib` and `summaries/manifest.json` | Path + optional freetext context |
| `/create-synthesis ["context" or guidance-file]` | Generates cross-cutting synthesis from all summaries; triggers full pipeline if summaries are missing | Optional: freetext, file path, or omit (uses `synthesis-guidance.md` if present) |

## Internal (not user-invocable)

| Skill | Purpose | Called by |
|---|---|---|
| `pdf-extraction` | Token-efficient PDF text extraction via `pdftotext` | `summarize-documents` |

## Script commands

| Command | Description |
|---|---|
| `python scripts/build_html.py` | Convert `synthesis/synthesis.md` to `synthesis/synthesis.html` |
| `python scripts/build_html.py --title "Title"` | Same, with a custom page title override |
