# cc-synthesizer

A Claude Code skill pipeline for ingesting PDF documents and generating an interactive synthesis.

## How to use

1. Drop PDFs into `documents/` (subdirectories allowed)
2. Run `/create-synthesis` — runs the full pipeline and creates `synthesis/synthesis.md`
3. Run `/launch-synthesis` — builds the HTML and opens the page in the browser (start the server separately to enable Ask Claude)

Or run individual steps: `/cleanup-pdf-names`, `/summarize-documents`, `/create-synthesis`, `/launch-synthesis`

See `README.md` for full instructions.

## Python

Always use `uv run` when executing Python scripts or tools. Examples:
- `uv run python scripts/build_html.py`
- `uv run pytest`

Use `uv` for all package management. Examples:
- `uv add <package>` to add a dependency
- `uv remove <package>` to remove a dependency
- `uv sync` to install all dependencies from `pyproject.toml`

## Notes

- PDFs in `documents/` are not version-controlled (see `.gitignore`)
- `summaries/` and `synthesis/` outputs are also gitignored by default
- `synthesis/synthesis-guidance.md` is an optional framing document read by `/create-synthesis`
