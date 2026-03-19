# Skills Reference

Quick reference for all available slash commands.

| Command | Description | Arguments |
|---|---|---|
| `/cleanup-pdf-names <path>` | Sanitizes PDF filenames: spaces → underscores, em/en dashes → hyphens | Path to file or directory |
| `/summarize-documents <path> ["context"]` | Generates per-document summaries, updates `references.bib` and `summaries/manifest.json` | Path + optional freetext context |
| `/create-synthesis ["context" or guidance-file]` | Generates cross-cutting synthesis from all summaries; triggers full pipeline if summaries are missing | Optional: freetext, file path, or omit (uses `synthesis-guidance.md` if present) |
| `/build-html ["title"]` | Converts `synthesis/synthesis.md` → `synthesis/synthesis.html` | Optional page title |

## Internal (not user-invocable)

| Skill | Purpose | Called by |
|---|---|---|
| `pdf-extraction` | Token-efficient PDF text extraction via `pdftotext` | `summarize-documents` |
