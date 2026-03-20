# cc-synthesizer

A Claude Code skill pipeline for ingesting PDF documents and generating an interactive synthesis.

## How to use

1. Drop PDFs into `documents/` (subdirectories allowed)
2. Run `/create-synthesis` — this runs the full pipeline and creates `synthesis/synthesis.md`
3. Run `python scripts/build_html.py` — generates `synthesis/synthesis.html`
4. Open `synthesis/synthesis.html` in a browser

Or run individual steps: `/cleanup-pdf-names`, `/summarize-documents`, `/create-synthesis`, then `python scripts/build_html.py`

See `docs/getting-started.md` for full instructions.

## Notes

- PDFs in `documents/` are not version-controlled (see `.gitignore`)
- `references.bib`, `summaries/`, and `synthesis/` outputs are also gitignored by default
- `synthesis-guidance.md` at the repo root is an optional framing document read by `/create-synthesis`
