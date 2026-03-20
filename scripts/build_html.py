#!/usr/bin/env python3
"""
build_html.py — Convert synthesis/synthesis.md to a self-contained interactive HTML page.

Usage:
    python scripts/build_html.py [--title "Optional Title"] [--root /path/to/repo]

Phase 2 note:
    The PHASE2_SERVER_HOOK block in the embedded JS isolates handleAskClaude.
    Phase 2 replaces only that function to POST to localhost:8000 and render
    streaming responses in a side panel. All other structure is unchanged.
"""

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Optional

# Use html.escape() for safe HTML escaping
escape = html.escape


def parse_bib(text: str) -> dict:
    """Parse BibTeX text → {key: {title, authors, year, venue, doi}}.

    Handles @article, @inproceedings, @misc, and any other entry type.
    venue = first of: journal > booktitle > howpublished.
    doi   = bare DOI string (no https://doi.org/ prefix).
    """
    entries = {}
    for block in re.finditer(r"@\w+\{(\w+),(.*?)\n\}", text, re.DOTALL):
        key = block.group(1).strip()
        body = block.group(2)

        def field(name: str) -> str:
            m = re.search(
                rf"\b{name}\s*=\s*\{{(.*?)\}}",
                body,
                re.DOTALL | re.IGNORECASE,
            )
            return m.group(1).strip() if m else ""

        venue = field("journal") or field("booktitle") or field("howpublished")
        entries[key] = {
            "title": field("title"),
            "authors": field("author"),
            "year": field("year"),
            "venue": venue,
            "doi": field("doi"),
        }
    return entries


def _slugify(text: str) -> str:
    """Convert heading text to a URL-safe id slug."""
    slug = re.sub(r"[^a-z0-9-]", "", text.lower().replace(" ", "-"))
    return slug if slug else "section"


def _apply_inline(text: str) -> str:
    """Apply bold, italic, and citation substitutions to already-HTML-escaped text.

    Safe because *, [ are not HTML special characters and survive html.escape().
    Citation keys (AuthorYearKeyword) also contain no special HTML chars.
    """
    # [BibKey] -> bare <cite> placeholder (metadata filled in by enrich_citations)
    text = re.sub(
        r"\[([A-Za-z][A-Za-z0-9]+)\]",
        lambda m: f'<cite data-key="{m.group(1)}">[{m.group(1)}]</cite>',
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


def _file_url(path: str) -> str:
    """Ensure path has a file:// prefix. Returns empty string if path is empty."""
    if not path:
        return ""
    if path.startswith("file://"):
        return path
    return "file://" + path


def enrich_citations(html: str, bib: dict, manifest: dict) -> tuple:
    """Replace <cite data-key="K">[K]</cite> placeholders with full data-* attribute sets.

    Args:
        html:     HTML body from render_markdown (contains bare cite placeholders)
        bib:      {key: {title, authors, year, venue, doi}} from parse_bib
        manifest: {key: {pdf, summary}} from manifest.json

    Returns:
        (enriched_html, missing_keys)
        - enriched_html: HTML with fully-attributed <cite> elements
        - missing_keys:  list of keys found in html but absent from bib
    """
    missing: list[str] = []

    def replace_cite(m: re.Match) -> str:
        key = m.group(1)
        if key not in bib:
            if key not in missing:
                missing.append(key)
            return m.group(0)  # leave as-is
        meta = bib[key]
        paths = manifest.get(key, {})
        attrs = " ".join(
            [
                f'data-key="{escape(key)}"',
                f'data-title="{escape(meta["title"])}"',
                f'data-authors="{escape(meta["authors"])}"',
                f'data-year="{escape(meta["year"])}"',
                f'data-venue="{escape(meta["venue"])}"',
                f'data-doi="{escape(meta["doi"])}"',
                f'data-pdf="{escape(_file_url(paths.get("pdf", "")))}"',
                f'data-summary="{escape(_file_url(paths.get("summary", "")))}"',
            ]
        )
        return f"<cite {attrs}>[{escape(key)}]</cite>"

    pattern = r'<cite data-key="([^"]+)">\[[^\]]+\]</cite>'
    enriched = re.sub(pattern, replace_cite, html)
    return enriched, missing


def render_markdown(text: str) -> tuple:
    """Convert synthesis.md markdown subset to HTML.

    Returns:
        (html_body, title, h2_headings)
        - html_body:    rendered HTML string
        - title:        text of the first H1 (empty string if none)
        - h2_headings:  list of (display_text, slug) tuples, in document order
    """
    lines = text.splitlines()
    html_parts: list[str] = []
    h2_headings: list[tuple[str, str]] = []
    title = ""
    i = 0
    used_slugs: dict[str, int] = {}  # slug -> count of uses so far

    while i < len(lines):
        line = lines[i]

        if line.startswith("# "):
            content = line[2:].strip()
            if not title:
                title = content
            html_parts.append(f"<h1>{_apply_inline(escape(content))}</h1>")
            i += 1

        elif line.startswith("## "):
            content = line[3:].strip()
            raw_slug = _slugify(content)
            if raw_slug not in used_slugs:
                used_slugs[raw_slug] = 1
                slug = raw_slug
            else:
                used_slugs[raw_slug] += 1
                slug = f"{raw_slug}-{used_slugs[raw_slug]}"
            h2_headings.append((content, slug))
            html_parts.append(f'<h2 id="{slug}">{_apply_inline(escape(content))}</h2>')
            i += 1

        elif line.startswith("### "):
            content = line[4:].strip()
            html_parts.append(f"<h3>{_apply_inline(escape(content))}</h3>")
            i += 1

        elif line.startswith("- "):
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                item_text = _apply_inline(escape(lines[i][2:].strip()))
                items.append(f"<li>{item_text}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")

        elif line.strip() == "":
            i += 1

        else:
            # Accumulate a paragraph (stop at blank line, heading, or list item)
            para_lines = []
            while (
                i < len(lines)
                and lines[i].strip() != ""
                and not lines[i].startswith("#")
                and not lines[i].startswith("- ")
            ):
                para_lines.append(lines[i])
                i += 1
            para_text = " ".join(para_lines)
            html_parts.append(f"<p>{_apply_inline(escape(para_text))}</p>")

    return "\n".join(html_parts), title, h2_headings


def build_html_page(
    title: str,
    body_html: str,
    h2_headings: list[tuple[str, str]],
    memory_doc: Optional[str],
    generated_date: str,
    missing_keys: list[str],
) -> str:
    """Generate the synthesis HTML page.

    Links to scripts/templates/style.css and scripts/templates/script.js
    via relative paths from synthesis/synthesis.html.
    Injects SYNTHESIS_MEMORY and SYNTHESIS_TOPIC as an inline script block.
    """
    sidebar_links = "\n".join(
        f'      <li><a href="#{slug}">{escape(text)}</a></li>'
        for text, slug in h2_headings
    )

    memory_js = json.dumps(memory_doc)  # "null" if None, else a JSON string

    warning_comment = ""
    if missing_keys:
        keys_str = ", ".join(f"[{k}]" for k in missing_keys)
        warning_comment = (
            f"\n<!-- WARNING: The following citation keys were not found in references.bib:\n"
            f"     {keys_str}\n"
            f"     These <cite> elements have no metadata. "
            f"Re-run /summarize-documents if needed. -->"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{escape(title)}</title>
  <link rel="stylesheet" href="../scripts/templates/style.css">
</head>
<body>
  <header>
    <h1>{escape(title)}</h1>
    <p class="meta">Generated {generated_date}</p>
  </header>
  <div class="layout">
    <nav class="sidebar">
      <ul>
{sidebar_links}
      </ul>
    </nav>
    <main class="content">
{body_html}
    </main>
  </div>
  <div id="tooltip" class="tooltip hidden"></div>
  <div id="ask-claude-btn" class="ask-btn hidden">Ask Claude</div>
  <div id="toast" class="toast hidden"></div>
  <script>
    const SYNTHESIS_MEMORY = {memory_js};
    const SYNTHESIS_TOPIC  = {json.dumps(title)};
  </script>
  <script src="../scripts/templates/script.js"></script>
</body>
</html>{warning_comment}"""


def main():
    parser = argparse.ArgumentParser(
        description="Build interactive HTML synthesis page from synthesis/synthesis.md"
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Override page title (default: H1 of synthesis.md)",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repo root directory (default: current working directory)",
    )
    args = parser.parse_args()

    root = Path(args.root) if args.root else Path.cwd()
    synthesis_md = root / "synthesis" / "synthesis.md"
    references_bib = root / "references.bib"
    manifest_json = root / "summaries" / "manifest.json"
    memory_md = root / "synthesis" / "synthesis-memory.md"
    output_html = root / "synthesis" / "synthesis.html"

    # Prerequisite checks
    if not synthesis_md.exists():
        print(
            "ERROR: synthesis/synthesis.md not found. Run /create-synthesis first.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not references_bib.exists():
        print(
            "ERROR: references.bib not found. Run /summarize-documents first.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not manifest_json.exists():
        print(
            "WARNING: summaries/manifest.json not found; "
            "citation file paths will be empty. "
            "Re-running /summarize-documents will fix this.",
            file=sys.stderr,
        )

    # Read inputs
    md_text = synthesis_md.read_text()
    bib_text = references_bib.read_text()
    manifest = json.loads(manifest_json.read_text()) if manifest_json.exists() else {}
    memory_doc = memory_md.read_text() if memory_md.exists() else None

    # Parse and render
    body_html, detected_title, h2_headings = render_markdown(md_text)
    title = args.title or detected_title or "Synthesis"
    bib = parse_bib(bib_text)
    body_html, missing_keys = enrich_citations(body_html, bib, manifest)

    # Count citations in source (for report)
    total_refs = len(re.findall(r"\[[A-Za-z][A-Za-z0-9]+\]", md_text))
    resolved = total_refs - len(missing_keys)

    # Assemble and write
    page = build_html_page(
        title=title,
        body_html=body_html,
        h2_headings=h2_headings,
        memory_doc=memory_doc,
        generated_date=date.today().isoformat(),
        missing_keys=missing_keys,
    )
    output_html.write_text(page)

    # Report
    print(
        f"Build HTML — Results\n"
        f"=====================\n"
        f"Input:      synthesis/synthesis.md\n"
        f"Output:     synthesis/synthesis.html\n"
        f"Citations:  {resolved} / {total_refs} "
        f"({len(missing_keys)} missing from references.bib)\n\n"
        f"Open synthesis/synthesis.html in your browser to view the interactive synthesis."
    )
    if missing_keys:
        print("\nMissing citation keys:")
        for k in missing_keys:
            print(f"  [{k}]")


if __name__ == "__main__":
    main()
