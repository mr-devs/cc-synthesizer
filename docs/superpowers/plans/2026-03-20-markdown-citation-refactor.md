# Markdown Library + Citation Store Consolidation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hand-rolled markdown parser with `markdown-it-py`, change citation syntax from `[BibKey]` to `[@CitKey]`, and consolidate `references.bib` + `summaries/manifest.json` into a single `citations.json`.

**Architecture:** `build_html.py` gains a custom `markdown-it-py` inline rule that intercepts `[@CitKey]` tokens before the link parser sees them, emitting `<cite>` elements. `citations.json` replaces two separate data stores. Skills and reference files are updated to match. No HTML output changes.

**Tech Stack:** Python 3.9+, `markdown-it-py>=3.0` (already in `pyproject.toml`), `uv` for running scripts/tests.

---

## File Map

| Action | File |
|---|---|
| Modify | `tests/test_build_html.py` |
| Modify | `scripts/build_html.py` |
| Delete | `.claude/reference/bibtex-format.md` |
| Create | `.claude/reference/citations-format.md` |
| Modify | `.claude/reference/summary-format.md` |
| Modify | `.claude/reference/synthesis-format.md` |
| Modify | `.claude/skills/summarize-documents/SKILL.md` |
| Modify | `.claude/skills/create-synthesis/SKILL.md` |

---

## Task 1: Update the test file

The test file is updated first (TDD). Most tests are unchanged. The changes are: remove the `BIB_SAMPLE` constant and the 3 `test_parse_bib_*` tests, add `CITATIONS_SAMPLE`, update 6 tests.

**Files:**
- Modify: `tests/test_build_html.py`

- [ ] **Step 1: Replace `BIB_SAMPLE` with `CITATIONS_SAMPLE`**

Remove `BIB_SAMPLE` (lines 9–31) and replace with:

```python
CITATIONS_SAMPLE = {
    "Smith2023Finding": {
        "title": "A Study of Things",
        "authors": "Smith, John and Doe, Alice",
        "year": "2023",
        "venue": "Journal of Examples",
        "doi": "10.1234/example",
        "url": "https://doi.org/10.1234/example",
        "type": "article",
        "pdf": "",
        "summary": "",
    },
    "Lee2024Review": {
        "title": "Conference Paper Title",
        "authors": "Lee, Bob",
        "year": "2024",
        "venue": "Proceedings of Something",
        "doi": "",
        "url": "",
        "type": "inproceedings",
        "pdf": "",
        "summary": "",
    },
    "Jones2022Debate": {
        "title": "Opinion Piece",
        "authors": "Jones, Carol",
        "year": "2022",
        "venue": "Policy Report",
        "doi": "",
        "url": "",
        "type": "misc",
        "pdf": "",
        "summary": "",
    },
}
```

- [ ] **Step 2: Remove the 3 `test_parse_bib_*` tests**

Delete `test_parse_bib_article`, `test_parse_bib_inproceedings`, and `test_parse_bib_misc_howpublished` entirely (they test a function that will be deleted).

- [ ] **Step 3: Update `test_render_headings` to add `####` regression**

Replace the existing `test_render_headings` function with:

```python
def test_render_headings():
    mod = _load_script()
    html, title, headings, _ = mod.render_markdown(
        "# My Title\n\n## Section One\n\n### Sub-section\n\n#### Deep\n"
    )
    assert title == "My Title"
    assert "<h1>My Title</h1>" not in html
    assert 'id="section-one"' in html
    assert 'id="sub-section"' in html
    assert 'id="deep"' in html
    assert headings == [
        (2, "Section One", "section-one"),
        (3, "Sub-section", "sub-section"),
        (4, "Deep", "deep"),
    ]
```

- [ ] **Step 4: Update `test_render_citation_placeholder` input to use `[@Key]` syntax**

Change only the input string in `test_render_citation_placeholder`:

```python
def test_render_citation_placeholder():
    mod = _load_script()
    html, _, _, _ = mod.render_markdown(
        "Found X [@Smith2023Finding] and Y [@Lee2024Review].\n"
    )
    assert 'data-key="Smith2023Finding"' in html
    assert 'data-key="Lee2024Review"' in html
    # Bracket text must be preserved as visible content inside <cite>
    assert '<cite data-key="Smith2023Finding">[Smith2023Finding]</cite>' in html
    assert '<cite data-key="Lee2024Review">[Lee2024Review]</cite>' in html
```

(The assertions are identical to the current ones — only the input line changes.)

- [ ] **Step 5: Update `test_enrich_citations_full`**

```python
def test_enrich_citations_full():
    mod = _load_script()
    html = '<p>See <cite data-key="Smith2023Finding">[Smith2023Finding]</cite>.</p>'
    citations = {
        "Smith2023Finding": {
            "title": "A Study of X",
            "authors": "Smith, J.",
            "year": "2023",
            "venue": "J. Example",
            "doi": "10.1234/x",
            "url": "https://doi.org/10.1234/x",
            "type": "article",
            "pdf": "/abs/path/doc.pdf",
            "summary": "/abs/path/summary.md",
        }
    }
    result, missing = mod.enrich_citations(html, citations)
    assert missing == []
    assert 'data-title="A Study of X"' in result
    assert 'data-year="2023"' in result
    assert 'data-doi="10.1234/x"' in result
    assert 'data-pdf="file:///abs/path/doc.pdf"' in result
    assert 'data-summary="file:///abs/path/summary.md"' in result
```

- [ ] **Step 6: Update `test_enrich_citations_missing_from_bib`**

```python
def test_enrich_citations_missing_from_bib():
    mod = _load_script()
    html = '<cite data-key="Ghost2000X">[Ghost2000X]</cite>'
    result, missing = mod.enrich_citations(html, {})
    assert "Ghost2000X" in missing
    assert 'data-key="Ghost2000X"' in result
```

- [ ] **Step 7: Update `test_enrich_citations_in_bib_not_in_manifest`**

```python
def test_enrich_citations_in_bib_not_in_manifest():
    mod = _load_script()
    html = '<cite data-key="Known2021Y">[Known2021Y]</cite>'
    citations = {
        "Known2021Y": {
            "title": "T",
            "authors": "A",
            "year": "2021",
            "venue": "V",
            "doi": "",
            "url": "",
            "type": "",
            "pdf": "",
            "summary": "",
        }
    }
    result, missing = mod.enrich_citations(html, citations)
    assert missing == []
    assert 'data-pdf=""' in result
    assert 'data-summary=""' in result
```

- [ ] **Step 8: Update `test_enrich_citations_already_file_url`**

```python
def test_enrich_citations_already_file_url():
    mod = _load_script()
    html = '<cite data-key="K">[K]</cite>'
    citations = {
        "K": {
            "title": "T",
            "authors": "A",
            "year": "2020",
            "venue": "V",
            "doi": "",
            "url": "",
            "type": "",
            "pdf": "file:///already/prefixed.pdf",
            "summary": "",
        }
    }
    result, _ = mod.enrich_citations(html, citations)
    assert 'data-pdf="file:///already/prefixed.pdf"' in result
    assert "file://file://" not in result
```

- [ ] **Step 9: Update `test_end_to_end`**

Replace the existing `test_end_to_end` function with:

```python
def test_end_to_end(tmp_path):
    """Full pipeline: real fixture files -> synthesis.html written and validated."""
    (tmp_path / "synthesis").mkdir()

    (tmp_path / "synthesis" / "synthesis.md").write_text(
        textwrap.dedent("""\
        # Test Synthesis

        ## Major Themes

        Research finds X [@Smith2023Finding] and Y [@Lee2024Review].

        - Point one
        - Point two
    """)
    )
    (tmp_path / "citations.json").write_text(
        json.dumps(
            {
                "Smith2023Finding": {
                    "title": "A Study of X",
                    "authors": "Smith, John",
                    "year": "2023",
                    "venue": "J. Example",
                    "doi": "10.1234/x",
                    "url": "https://doi.org/10.1234/x",
                    "type": "article",
                    "pdf": "/docs/smith.pdf",
                    "summary": "/summaries/smith.md",
                },
                "Lee2024Review": {
                    "title": "A Review of Y",
                    "authors": "Lee, Bob",
                    "year": "2024",
                    "venue": "Proc. Something",
                    "doi": "",
                    "url": "",
                    "type": "inproceedings",
                    "pdf": "",
                    "summary": "",
                },
            }
        )
    )

    result = subprocess.run(
        [sys.executable, "scripts/build_html.py", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout

    html = (tmp_path / "synthesis" / "synthesis.html").read_text()

    # Structure
    assert "<!DOCTYPE html>" in html
    assert "<title>Test Synthesis</title>" in html
    assert "style.css" in html
    assert "script.js" in html
    assert "SYNTHESIS_MEMORY" in html
    assert "SYNTHESIS_TOPIC" in html

    # Citations
    assert 'data-key="Smith2023Finding"' in html
    assert 'data-title="A Study of X"' in html
    assert 'data-doi="10.1234/x"' in html
    assert 'data-pdf="file:///docs/smith.pdf"' in html
    assert 'data-summary="file:///summaries/smith.md"' in html

    # Lee2024Review is in citations but has no paths -> metadata present, paths empty
    assert 'data-key="Lee2024Review"' in html
    assert 'data-title="A Review of Y"' in html

    # No CDN or external resources
    assert "cdn." not in html
    assert "fonts.googleapis" not in html
```

---

## Task 2: Run tests to verify failures

At this point the tests reference new function signatures that don't exist yet. Run them to confirm the expected failures.

**Files:** (none changed)

- [ ] **Step 1: Run the full test suite**

```bash
uv run pytest tests/test_build_html.py -v
```

Expected: several FAILED tests. Tests that call `mod.enrich_citations(html, citations)` (two args) will fail with `TypeError`. `test_render_headings` will fail because `####` causes an infinite loop in the old parser. `test_render_citation_placeholder` will fail because `[@Key]` is not parsed by the old code. `test_end_to_end` will fail because `citations.json` doesn't exist as an input. Unchanged tests (`test_cli_*`, `test_render_paragraph_and_lists`, `test_build_html_page_*`, etc.) will still pass.

---

## Task 3: Rewrite `scripts/build_html.py`

This is the core implementation task. Work through the file top-to-bottom.

**Files:**
- Modify: `scripts/build_html.py`

- [ ] **Step 1: Add `markdown-it-py` import and remove old imports no longer needed**

At the top of the file, after the existing imports, add:

```python
from markdown_it import MarkdownIt
```

The `html` standard library import stays (used by `escape = html.escape`). Remove nothing yet — clean up after implementation is verified.

- [ ] **Step 2: Delete `parse_bib` function**

Remove the entire `parse_bib` function (lines 27–55 in the current file). It is replaced by `json.load()` in `main()`.

- [ ] **Step 3: Write the citation inline rule function**

Add this new function before `render_markdown`. It handles `[@Key]` and `[@Key1, @Key2]`:

```python
def _citation_rule(state, silent: bool) -> bool:
    """markdown-it-py inline rule: convert [@CitKey] to <cite> placeholders."""
    pos = state.pos
    src = state.src

    # Must start with [@
    if src[pos : pos + 2] != "[@":
        return False

    # Find closing ]
    end = src.find("]", pos + 2)
    if end == -1:
        return False

    inner = src[pos + 2 : end]  # everything between [@ and ]
    keys = [k.strip().lstrip("@") for k in inner.split(",")]

    # Validate: every key must be non-empty and start with a letter
    if not all(k and k[0].isalpha() for k in keys):
        return False

    if silent:
        return True

    # Emit HTML
    if len(keys) == 1:
        k = escape(keys[0])
        html_out = f'<cite data-key="{k}">[{k}]</cite>'
    else:
        parts = ", ".join(
            f'<cite data-key="{escape(k)}">{escape(k)}</cite>' for k in keys
        )
        html_out = f"[{parts}]"

    token = state.push("html_inline", "", 0)
    token.content = html_out

    state.pos = end + 1
    return True
```

- [ ] **Step 4: Delete `_apply_inline` function**

Remove the entire `_apply_inline` function. It is replaced by the library.

- [ ] **Step 5: Rewrite `render_markdown`**

Replace the entire `render_markdown` function body with the following implementation. The function signature and return type are **unchanged**:

```python
def render_markdown(text: str) -> tuple[str, str, list[tuple[int, str, str]], str]:
    """Convert synthesis.md markdown subset to HTML using markdown-it-py.

    Returns:
        (html_body, title, nav_headings, doc_count)
        - html_body:    rendered HTML string (H1 suppressed)
        - title:        text of the first H1 (empty string if none)
        - nav_headings: list of (level, display_text, slug) for h2/h3/h4, in order
        - doc_count:    number of documents from metadata line (empty string if none)
    """
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    md.inline.ruler.before("link", "citation", _citation_rule)

    tokens = md.parse(text)

    # ── Extract and suppress the first H1 ───────────────────────────────────
    title = ""
    i = 0
    while i < len(tokens):
        if tokens[i].type == "heading_open" and tokens[i].tag == "h1":
            inline_tok = tokens[i + 1]  # always present after heading_open
            title = inline_tok.content
            # Remove the triplet: heading_open, inline, heading_close
            tokens.pop(i)  # heading_open
            tokens.pop(i)  # inline (shifted down)
            tokens.pop(i)  # heading_close (shifted down)
            break
        i += 1

    # ── Collect nav headings (h2, h3, h4) ───────────────────────────────────
    used_slugs: dict[str, int] = {}
    nav_headings: list[tuple[int, str, str]] = []
    for j, tok in enumerate(tokens):
        if tok.type == "heading_open" and tok.tag in ("h2", "h3", "h4"):
            level = int(tok.tag[1])
            inline_content = tokens[j + 1].content  # raw markdown source
            slug = _unique_slug(inline_content, used_slugs)
            nav_headings.append((level, inline_content, slug))
            # Inject id attribute on the heading_open token
            tok.attrSet("id", slug)

    # ── Render ───────────────────────────────────────────────────────────────
    body_html = md.renderer.render(tokens, md.options, {})

    # ── Extract and suppress doc-count metadata line ─────────────────────────
    doc_count = ""
    m = re.search(r"<p><em>Synthesis of (\d+) documents\.", body_html)
    if m:
        doc_count = m.group(1)
        body_html = re.sub(
            r"<p><em>Synthesis of \d+ documents\..*?</em></p>", "", body_html
        )

    return body_html, title, nav_headings, doc_count
```

- [ ] **Step 6: Update `enrich_citations` signature**

Change the function signature from `enrich_citations(html, bib, manifest)` to `enrich_citations(html, citations)`. Update the body: replace all `bib` references with `citations`, remove all `manifest` references, update path access, update the missing-key check. The complete updated function:

```python
def enrich_citations(html: str, citations: dict) -> tuple:
    """Replace <cite data-key="K">[K]</cite> placeholders with full data-* attribute sets.

    Args:
        html:      HTML body from render_markdown (contains bare cite placeholders)
        citations: {key: {title, authors, year, venue, doi, pdf, summary, ...}} from citations.json

    Returns:
        (enriched_html, missing_keys)
        - enriched_html: HTML with fully-attributed <cite> elements
        - missing_keys:  list of keys found in html but absent from citations
    """
    missing: list[str] = []

    def replace_cite(m: re.Match) -> str:
        key = m.group(1)
        if key not in citations:
            if key not in missing:
                missing.append(key)
            return m.group(0)  # leave as-is
        meta = citations[key]
        pdf_url = escape(_file_url(meta.get("pdf", "")))
        summ_url = escape(_file_url(meta.get("summary", "")))
        attrs = " ".join(
            [
                f'data-key="{escape(key)}"',
                f'data-title="{escape(meta.get("title", ""))}"',
                f'data-authors="{escape(meta.get("authors", ""))}"',
                f'data-year="{escape(meta.get("year", ""))}"',
                f'data-venue="{escape(meta.get("venue", ""))}"',
                f'data-doi="{escape(meta.get("doi", ""))}"',
                f'data-pdf="{pdf_url}"',
                f'data-summary="{summ_url}"',
            ]
        )
        return f"<cite {attrs}>[{escape(key)}]</cite>"

    pattern = r'<cite data-key="([^"]+)">\[?[^\]<]+\]?</cite>'
    enriched = re.sub(pattern, replace_cite, html)
    return enriched, missing
```

- [ ] **Step 7: Update `build_html_page` warning comment strings**

In `build_html_page`, find the warning comment block and update two strings:
- `"not found in references.bib"` → `"not found in citations.json"`
- `f"[{k}]"` inside the `keys_str` join → `f"[@{k}]"`

The updated block:

```python
    warning_comment = ""
    if missing_keys:
        keys_str = ", ".join(f"[@{k}]" for k in missing_keys)
        warning_comment = (
            f"\n<!-- WARNING: The following citation keys were not found in citations.json:\n"
            f"     {keys_str}\n"
            f"     These <cite> elements have no metadata. "
            f"Re-run /summarize-documents if needed. -->"
        )
```

- [ ] **Step 8: Update `main()` — paths, prerequisite check, citation count regex, report strings**

In `main()`:

1. Replace the `references_bib` and `manifest_json` path variables with `citations_json`:
```python
    citations_json = root / "citations.json"
```

2. Replace the prerequisite checks block (currently checks `synthesis_md`, `references_bib`, `manifest_json`) with:
```python
    if not synthesis_md.exists():
        print(
            "ERROR: synthesis/synthesis.md not found. Run /create-synthesis first.",
            file=sys.stderr,
        )
        sys.exit(1)
    if not citations_json.exists():
        print(
            "ERROR: citations.json not found. Run /summarize-documents first.",
            file=sys.stderr,
        )
        sys.exit(1)
```

3. Replace the input-reading block for `bib_text` and `manifest` with:
```python
    citations = json.loads(citations_json.read_text(encoding="utf-8"))
```

4. Update the parse-and-render block to use the new signatures:
```python
    body_html, detected_title, nav_headings, doc_count = render_markdown(md_text)
    title = args.title or detected_title or "Synthesis"
    body_html, missing_keys = enrich_citations(body_html, citations)
```

5. Update the citation count regex:
```python
    total_refs = len(re.findall(r"@[A-Za-z][A-Za-z0-9]+", md_text))
```

6. Update the report string — change `"missing from references.bib"` to `"missing from citations.json"`.

7. Update the per-key display loop — change `f"  [{k}]"` to `f"  [@{k}]"`.

---

## Task 4: Run tests to verify all pass

- [ ] **Step 1: Run the full test suite**

```bash
uv run pytest tests/test_build_html.py -v
```

Expected: all tests pass. If any test fails:
- `test_render_headings` failure → check token removal loop and `heading_open` tag matching in `render_markdown`
- `test_render_citation_placeholder` failure → check `_citation_rule` key extraction and HTML emission
- `test_enrich_citations_*` failure → verify function signature is `enrich_citations(html, citations)` and all `meta.get(...)` calls use the right field names
- `test_end_to_end` failure → check `citations_json` path variable in `main()` and that `manifest_json` is fully removed

- [ ] **Step 2: Commit**

```bash
git add scripts/build_html.py tests/test_build_html.py
git commit -m "feat: replace hand-rolled parser with markdown-it-py, consolidate to citations.json"
```

---

## Task 5: Create `.claude/reference/citations-format.md`

This replaces `bibtex-format.md` as the reference for citation key naming and the `citations.json` schema.

**Files:**
- Create: `.claude/reference/citations-format.md`
- Delete: `.claude/reference/bibtex-format.md`

- [ ] **Step 1: Write `.claude/reference/citations-format.md`**

```markdown
# Citations Format Reference

## Key Naming Convention

Format: `AuthorYearKeyword`

- **Author**: First author's surname only
- **Year**: 4-digit publication year
- **Keyword**: First significant word from title (skip "The", "A", "An", "On")

Examples: `Wardle2025Evolving`, `FernandezPichel2025Evaluating`, `Sun2024TrustingSearch`

Special cases: Hyphenated surnames → remove hyphen; Accents → remove; "et al." → first author only; Duplicate keys → append lowercase letter (e.g., `Author2024Keywordb`)

## `citations.json` Schema

Location: `{repo_root}/citations.json`

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
```

- [ ] **Step 2: Delete the old `bibtex-format.md`**

```bash
git rm .claude/reference/bibtex-format.md
```

- [ ] **Step 3: Commit**

```bash
git add .claude/reference/citations-format.md
git commit -m "feat: replace bibtex-format.md with citations-format.md"
```

---

## Task 6: Update `.claude/reference/summary-format.md`

A single one-line change: `BibTeX Key` → `Citation Key` in the metadata block template.

**Files:**
- Modify: `.claude/reference/summary-format.md`

- [ ] **Step 1: Replace `BibTeX Key` label in the metadata block**

Find:
```
- **BibTeX Key:** `{AuthorYearKeyword}`
```

Replace with:
```
- **Citation Key:** `{AuthorYearKeyword}`
```

- [ ] **Step 2: Commit**

```bash
git add .claude/reference/summary-format.md
git commit -m "docs: rename BibTeX Key to Citation Key in summary-format.md"
```

---

## Task 7: Update `.claude/reference/synthesis-format.md`

Update citation syntax examples and references from `[BibKey]` to `[@BibKey]`, and update `references.bib` → `citations.json`.

**Files:**
- Modify: `.claude/reference/synthesis-format.md`

- [ ] **Step 1: Update the Citation Syntax section**

Find:
```
Inline citations use BibTeX key notation: `[Author2024Keyword]`

- Every factual claim must be tied to at least one citation
- Multiple citations: `[Jones2022Debate, Lee2024Review]`
- Keys must match entries in `references.bib`
```

Replace with:
```
Inline citations use `[@CitKey]` notation: `[@Author2024Keyword]`

- Every factual claim must be tied to at least one citation
- Multiple citations: `[@Jones2022Debate, @Lee2024Review]`
- Keys must match entries in `citations.json`
```

- [ ] **Step 2: Update the Document Structure template**

In the document structure code block, change all `[BibKey]` occurrences to `[@BibKey]`:

Find all of these and apply individually (3 occurrences in the template):
- `1. **[BibKey]**` → `1. **[@BibKey]**`
- `2. **[BibKey]**` → `2. **[@BibKey]**`
- `Prose synthesis of what the corpus says about this theme. Every claim tied to a citation. [BibKey]` → `... [@BibKey]`
- `What do sources disagree on? Why? What are the stakes of each position? [BibKey, BibKey]` → `... [@BibKey, @BibKey]`
- `What do most or all sources agree on? [BibKey]` → `... [@BibKey]`

- [ ] **Step 3: Update the Citation Index table header**

Find:
```
| BibTeX Key | One-line description |
```

Replace with:
```
| Citation Key | One-line description |
```

- [ ] **Step 4: Commit**

```bash
git add .claude/reference/synthesis-format.md
git commit -m "docs: update synthesis-format.md to use [@CitKey] syntax and citations.json"
```

---

## Task 8: Update `.claude/skills/summarize-documents/SKILL.md`

This is the most substantial skill update. Seven changes covering: frontmatter, reference pointer, steps 3/4a/4e/5, agent result block schema.

**Files:**
- Modify: `.claude/skills/summarize-documents/SKILL.md`

- [ ] **Step 1: Update the YAML frontmatter `description`**

Find:
```
description: Generate per-document markdown summaries from PDFs. Detects document type and adapts the summary structure accordingly. Updates references.bib and summaries/manifest.json.
```

Replace with:
```
description: Generate per-document markdown summaries from PDFs. Detects document type and adapts the summary structure accordingly. Updates citations.json.
```

- [ ] **Step 2: Replace `bibtex-format.md` reference with `citations-format.md`**

There are three occurrences in the file. Replace all three:

Find (all occurrences):
```
@.claude/reference/bibtex-format.md
```

Replace with:
```
@.claude/reference/citations-format.md
```

Use replace-all to hit all three at once.

- [ ] **Step 3: Update Step 3 (Load Existing State)**

Find:
```
1. Read `references.bib` if it exists; extract existing BibTeX keys for duplicate checking
2. Read `summaries/manifest.json` if it exists; load existing key→path mappings
```

Replace with:
```
1. Read `citations.json` if it exists; extract existing citation keys for duplicate checking
```

- [ ] **Step 4: Update Step 4a sub-step 5 — remove `references.bib` write**

Find and delete this sub-step from Step 4a:
```
5. Append new entry to `references.bib` (create file if absent); verify no duplicate key
```

Also update Step 4a prose to say agents return a `CITATION_ENTRY:` JSON block instead of `BIBTEX_ENTRY:` + `MANIFEST_ENTRY:`.

Find in Step 4a:
```
2. If DOI found: run `fbib "{doi}"` — if successful, use this BibTeX entry (regenerate key per @.claude/reference/bibtex-format.md)
```

Replace with:
```
2. If DOI found: run `fbib "{doi}"` — if successful, use this BibTeX entry (regenerate key per @.claude/reference/citations-format.md); extract fields (`title`, `authors`, `year`, `venue`, `doi`, `url`, `type`) for the `citations.json` entry
```

- [ ] **Step 5: Update the `---BEGIN_AGENT_RESULT---` block schema**

Find the entire schema block (from `---BEGIN_AGENT_RESULT---` to `---END_AGENT_RESULT---`):

```
---BEGIN_AGENT_RESULT---
STATUS: success | error
PDF: {pdf_path}
BIBKEY: {final_bib_key}
CITATION_METHOD: doi|title|manual
SUMMARY_PATH: {absolute_path}
BIBTEX_ENTRY:
```bibtex
{complete entry}
```
MANIFEST_ENTRY:
```json
{ "{BibKey}": { "pdf": "...", "summary": "..." } }
```
WARNINGS: {any warnings, or "none"}
---END_AGENT_RESULT---
```

Replace with:

```
---BEGIN_AGENT_RESULT---
STATUS: success | error
PDF: {pdf_path}
BIBKEY: {final_cit_key}
CITATION_METHOD: doi|title|manual
SUMMARY_PATH: {absolute_path}
CITATION_ENTRY:
```json
{ "Smith2023Finding": { "title": "...", "authors": "...", "year": "...", "venue": "...", "doi": "...", "url": "...", "type": "...", "pdf": "/abs/path/documents/subdir/Smith_-_2023_-_Title.pdf", "summary": "/abs/path/summaries/subdir/Smith2023Finding.md" } }
```
WARNINGS: {any warnings, or "none"}
---END_AGENT_RESULT---
```

- [ ] **Step 6: Update Step 4e (sequential mode write)**

Find:
```
When **not** using parallel agents, upsert an entry in `summaries/manifest.json` (create file if absent; add or overwrite the entry for this BibTeX key — do not remove existing entries for other keys):

```json
{
  "Smith2023Finding": {
    "pdf": "/absolute/path/to/documents/subdir/Smith_-_2023_-_Title.pdf",
    "summary": "/absolute/path/to/summaries/subdir/Smith2023Finding.md"
  }
}
```

Use the absolute filesystem path (not a relative path).
```

Replace with:
```
When **not** using parallel agents, upsert the entry into `citations.json` at the repo root (create file if absent; add or overwrite the entry for this citation key — do not remove existing entries for other keys). Include all fields: `title`, `authors`, `year`, `venue`, `doi`, `url`, `type`, `pdf`, `summary` (absolute filesystem paths).

Write atomically: write the full JSON to a temp file in the same directory, then rename to `citations.json`.
```

- [ ] **Step 7: Update Step 5 (parallel consolidation)**

Find the Step 5 header and content about writing `references.bib` and `manifest.json`. Replace the consolidation instructions with:

```
1. **Triage**: parse each `---BEGIN_AGENT_RESULT---` block; separate successes from errors (or unparseable output)
2. **Read existing `citations.json`** from disk first (or `{}` if absent)
3. **Deduplicate citation keys**: two collision cases:
   - **Same-batch collision**: two agents returned the same `CitKey` for different PDFs → rename the second with a letter suffix (`b`, `c`, …) and note it in warnings
   - **Reprocess collision**: a batch key matches a pre-existing on-disk key for the same PDF → overwrite (true upsert)
   - A batch key that collides with a pre-existing on-disk key for a *different* PDF is treated as a same-batch collision and renamed
4. **Write `citations.json`**: merge all new `CITATION_ENTRY` objects (parsed as JSON) into the existing dict; write atomically (temp file + rename)
```

- [ ] **Step 8: Remove any remaining `references.bib` / `manifest.json` references**

Search the file for `references.bib` and `manifest.json`. Remove or update any remaining occurrences.

- [ ] **Step 9: Commit**

```bash
git add .claude/skills/summarize-documents/SKILL.md
git commit -m "feat: update summarize-documents skill to write citations.json"
```

---

## Task 9: Update `.claude/skills/create-synthesis/SKILL.md`

Five targeted changes: reference pointer, Step 2 prerequisite, Step 3 read, Step 4 citation syntax, Step 6 report string.

**Files:**
- Modify: `.claude/skills/create-synthesis/SKILL.md`

- [ ] **Step 1: Replace `bibtex-format.md` reference in `## Reference` block**

Find:
```
@.claude/reference/bibtex-format.md
```

Replace with:
```
@.claude/reference/citations-format.md
```

- [ ] **Step 2: Update Step 2 prerequisite check**

Find in Step 2:
```
1. Check for summary files in `summaries/` (look for `*.md` files; exclude `manifest.json` — it is not a summary)
```

Replace with:
```
1. Check for summary files in `summaries/` (look for `*.md` files)
```

- [ ] **Step 3: Update Step 3 — read `citations.json` instead of `references.bib`**

Find:
```
3. Read `references.bib`
```

Replace with:
```
3. Read `citations.json` (single `json.load()`)
```

- [ ] **Step 4: Update Step 4 — citation syntax and file reference**

Find:
```
- Every factual claim tied to a citation `[BibKey]`
- Keys must match entries in `references.bib`
```

Replace with:
```
- Every factual claim tied to a citation `[@CitKey]`
- Keys must match entries in `citations.json`
```

- [ ] **Step 5: Update Step 6 report string**

Find in the report template:
```
Citations used:       {M distinct BibTeX keys}
```

Replace with:
```
Citations used:       {M distinct citation keys}
```

Also update any remaining `references.bib` reference in the report or elsewhere in the file.

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/create-synthesis/SKILL.md
git commit -m "feat: update create-synthesis skill to use [@CitKey] syntax and citations.json"
```

---

## Task 10: Final verification

- [ ] **Step 1: Run the full test suite one more time**

```bash
uv run pytest tests/test_build_html.py -v
```

Expected: all tests pass, no warnings.

- [ ] **Step 2: Verify `markdown-it-py` is importable**

```bash
uv run python -c "from markdown_it import MarkdownIt; print('ok')"
```

Expected: `ok`

- [ ] **Step 3: Smoke-test the build script**

Create a minimal test run:

```bash
cd /tmp && mkdir smoke_test && cd smoke_test && \
  mkdir synthesis && \
  echo '# My Topic

*Synthesis of 3 documents. Generated 2026-03-20.*

## Key Findings

Researchers found X [@Smith2023Finding].

#### Deep Subsection

More detail here.
' > synthesis/synthesis.md && \
  echo '{"Smith2023Finding": {"title": "A Study", "authors": "Smith, J.", "year": "2023", "venue": "J. Example", "doi": "10.1/x", "url": "", "type": "article", "pdf": "", "summary": ""}}' > citations.json && \
  uv run --project /path/to/cc-synthesizer python /path/to/cc-synthesizer/scripts/build_html.py --root .
```

Or from the project root with a temp directory:

```bash
TMPDIR=$(mktemp -d) && \
  mkdir -p "$TMPDIR/synthesis" && \
  printf '# My Topic\n\n*Synthesis of 3 documents. Generated 2026-03-20.*\n\n## Key Findings\n\nX [@Smith2023Finding].\n\n#### Deep Subsection\n\nMore detail here.\n' > "$TMPDIR/synthesis/synthesis.md" && \
  printf '{"Smith2023Finding":{"title":"T","authors":"A","year":"2023","venue":"V","doi":"","url":"","type":"article","pdf":"","summary":""}}' > "$TMPDIR/citations.json" && \
  uv run python scripts/build_html.py --root "$TMPDIR" && \
  grep 'id="deep-subsection"' "$TMPDIR/synthesis/synthesis.html" && \
  grep 'data-key="Smith2023Finding"' "$TMPDIR/synthesis/synthesis.html" && \
  echo "Smoke test passed"
```

Expected: `Smoke test passed`. If `id="deep-subsection"` is missing, the H4 slug injection is broken — check the `tok.attrSet("id", slug)` call in `render_markdown`.
