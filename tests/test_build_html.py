import json
import subprocess
import sys
import textwrap
import importlib.util


# ── constants ────────────────────────────────────────────────────────────────
BIB_SAMPLE = r"""
@article{Smith2023Finding,
  author    = {Smith, John and Doe, Alice},
  title     = {A Study of Things},
  journal   = {Journal of Examples},
  year      = {2023},
  doi       = {10.1234/example},
}

@inproceedings{Lee2024Review,
  author    = {Lee, Bob},
  title     = {Conference Paper Title},
  booktitle = {Proceedings of Something},
  year      = {2024},
}

@misc{Jones2022Debate,
  author       = {Jones, Carol},
  title        = {Opinion Piece},
  howpublished = {Policy Report},
  year         = {2022},
}
"""


# ── helper ──────────────────────────────────────────────────────────────────
def _load_script():
    """Import scripts/build_html.py as a module without executing main()."""
    spec = importlib.util.spec_from_file_location("build_html", "scripts/build_html.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── CLI tests ────────────────────────────────────────────────────────────────
def test_cli_help():
    result = subprocess.run(
        [sys.executable, "scripts/build_html.py", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "synthesis" in result.stdout.lower()


def test_cli_missing_synthesis(tmp_path):
    result = subprocess.run(
        [sys.executable, "scripts/build_html.py", "--root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    output = result.stdout + result.stderr
    assert "synthesis" in output.lower()


# ── BibTeX parser tests ──────────────────────────────────────────────────────
def test_parse_bib_article():
    mod = _load_script()
    result = mod.parse_bib(BIB_SAMPLE)
    assert "Smith2023Finding" in result
    entry = result["Smith2023Finding"]
    assert entry["title"] == "A Study of Things"
    assert "Smith, John" in entry["authors"]
    assert entry["year"] == "2023"
    assert entry["venue"] == "Journal of Examples"
    assert entry["doi"] == "10.1234/example"


def test_parse_bib_inproceedings():
    mod = _load_script()
    result = mod.parse_bib(BIB_SAMPLE)
    entry = result["Lee2024Review"]
    assert entry["venue"] == "Proceedings of Something"
    assert entry["doi"] == ""


def test_parse_bib_misc_howpublished():
    mod = _load_script()
    result = mod.parse_bib(BIB_SAMPLE)
    entry = result["Jones2022Debate"]
    assert entry["venue"] == "Policy Report"
    assert entry["doi"] == ""


# ── Markdown renderer tests ──────────────────────────────────────────────────
def test_render_headings():
    mod = _load_script()
    html, title, headings = mod.render_markdown(
        "# My Title\n\n## Section One\n\n### Sub-section\n"
    )
    assert title == "My Title"
    assert "<h1>My Title</h1>" in html
    assert 'id="section-one"' in html
    assert "<h3>Sub-section</h3>" in html
    assert headings == [("Section One", "section-one")]


def test_render_paragraph_and_lists():
    mod = _load_script()
    html, _, _ = mod.render_markdown("A paragraph.\n\n- Item one\n- Item two\n")
    assert "<p>A paragraph.</p>" in html
    assert "<ul>" in html
    assert "<li>Item one</li>" in html


def test_render_inline_formatting():
    mod = _load_script()
    html, _, _ = mod.render_markdown("Some **bold** and *italic* text.\n")
    assert "<strong>bold</strong>" in html
    assert "<em>italic</em>" in html


def test_render_citation_placeholder():
    mod = _load_script()
    html, _, _ = mod.render_markdown(
        "Found X [Smith2023Finding] and Y [Lee2024Review].\n"
    )
    assert 'data-key="Smith2023Finding"' in html
    assert 'data-key="Lee2024Review"' in html
    # Bracket text must be preserved as visible content inside <cite>
    assert '<cite data-key="Smith2023Finding">[Smith2023Finding]</cite>' in html
    assert '<cite data-key="Lee2024Review">[Lee2024Review]</cite>' in html


def test_render_html_escaping():
    mod = _load_script()
    html, _, _ = mod.render_markdown("A paragraph with <script>evil</script>.\n")
    assert "<script>" not in html
    assert "&lt;script&gt;" in html


def test_render_heading_inline_formatting():
    mod = _load_script()
    html, _, _ = mod.render_markdown("## **Bold** Section\n")
    assert "<strong>Bold</strong>" in html


def test_render_slug_collision():
    mod = _load_script()
    html, _, headings = mod.render_markdown("## Intro\n\n## Intro\n")
    assert headings[0][1] == "intro"
    assert headings[1][1] == "intro-2"
    assert 'id="intro"' in html
    assert 'id="intro-2"' in html


# ── Citation enrichment tests ────────────────────────────────────────────────────
def test_enrich_citations_full():
    mod = _load_script()
    html = '<p>See <cite data-key="Smith2023Finding">[Smith2023Finding]</cite>.</p>'
    bib = {
        "Smith2023Finding": {
            "title": "A Study of X",
            "authors": "Smith, J.",
            "year": "2023",
            "venue": "J. Example",
            "doi": "10.1234/x",
        }
    }
    manifest = {
        "Smith2023Finding": {
            "pdf": "/abs/path/doc.pdf",
            "summary": "/abs/path/summary.md",
        }
    }
    result, missing = mod.enrich_citations(html, bib, manifest)
    assert missing == []
    assert 'data-title="A Study of X"' in result
    assert 'data-year="2023"' in result
    assert 'data-doi="10.1234/x"' in result
    assert 'data-pdf="file:///abs/path/doc.pdf"' in result
    assert 'data-summary="file:///abs/path/summary.md"' in result


def test_enrich_citations_missing_from_bib():
    mod = _load_script()
    html = '<cite data-key="Ghost2000X">[Ghost2000X]</cite>'
    result, missing = mod.enrich_citations(html, {}, {})
    assert "Ghost2000X" in missing
    assert 'data-key="Ghost2000X"' in result


def test_enrich_citations_in_bib_not_in_manifest():
    mod = _load_script()
    html = '<cite data-key="Known2021Y">[Known2021Y]</cite>'
    bib = {
        "Known2021Y": {
            "title": "T",
            "authors": "A",
            "year": "2021",
            "venue": "V",
            "doi": "",
        }
    }
    result, missing = mod.enrich_citations(html, bib, {})
    assert missing == []
    assert 'data-pdf=""' in result
    assert 'data-summary=""' in result


def test_enrich_citations_already_file_url():
    mod = _load_script()
    html = '<cite data-key="K">[K]</cite>'
    bib = {"K": {"title": "T", "authors": "A", "year": "2020", "venue": "V", "doi": ""}}
    manifest = {"K": {"pdf": "file:///already/prefixed.pdf", "summary": ""}}
    result, _ = mod.enrich_citations(html, bib, manifest)
    assert 'data-pdf="file:///already/prefixed.pdf"' in result
    assert "file://file://" not in result


# ── build_html_page tests ────────────────────────────────────────────────────
def test_build_html_page_structure():
    mod = _load_script()
    page = mod.build_html_page(
        title="Test Synthesis",
        body_html='<h2 id="s1">Section One</h2><p>Body text.</p>',
        h2_headings=[("Section One", "s1")],
        memory_doc=None,
        generated_date="2026-03-19",
        missing_keys=[],
    )
    assert "<!DOCTYPE html>" in page
    assert "<title>Test Synthesis</title>" in page
    assert 'href="#s1"' in page  # sidebar link
    assert "Section One" in page
    assert "style.css" in page  # CSS linked
    assert "script.js" in page  # JS linked
    assert "Ask Claude" in page  # button div present
    assert "SYNTHESIS_MEMORY = null" in page  # inline const
    assert "SYNTHESIS_TOPIC" in page  # inline const
    assert "cdn." not in page
    assert "fonts.googleapis" not in page


def test_build_html_page_missing_keys_warning():
    mod = _load_script()
    page = mod.build_html_page(
        title="T",
        body_html="",
        h2_headings=[],
        memory_doc=None,
        generated_date="2026-03-19",
        missing_keys=["Ghost2020X", "Missing2021Y"],
    )
    assert "WARNING" in page
    assert "Ghost2020X" in page
    assert "Missing2021Y" in page


def test_build_html_page_memory_doc_embedded():
    mod = _load_script()
    page = mod.build_html_page(
        title="T",
        body_html="",
        h2_headings=[],
        memory_doc="## Topic\nAI risk research\n",
        generated_date="2026-03-19",
        missing_keys=[],
    )
    assert "AI risk research" in page


def test_build_html_page_memory_null_when_absent():
    mod = _load_script()
    page = mod.build_html_page(
        title="T",
        body_html="",
        h2_headings=[],
        memory_doc=None,
        generated_date="2026-03-19",
        missing_keys=[],
    )
    assert "SYNTHESIS_MEMORY = null" in page


# ── Integration tests ───────────────────────────────────────────────────────
def test_end_to_end(tmp_path):
    """Full pipeline: real fixture files -> synthesis.html written and validated."""
    (tmp_path / "synthesis").mkdir()
    (tmp_path / "summaries").mkdir()

    (tmp_path / "synthesis" / "synthesis.md").write_text(
        textwrap.dedent("""\
        # Test Synthesis

        ## Major Themes

        Research finds X [Smith2023Finding] and Y [Lee2024Review].

        - Point one
        - Point two
    """)
    )
    (tmp_path / "references.bib").write_text(
        textwrap.dedent(r"""
        @article{Smith2023Finding,
          author  = {Smith, John},
          title   = {A Study of X},
          journal = {J. Example},
          year    = {2023},
          doi     = {10.1234/x},
        }
        @inproceedings{Lee2024Review,
          author    = {Lee, Bob},
          title     = {A Review of Y},
          booktitle = {Proc. Something},
          year      = {2024},
        }
    """)
    )
    (tmp_path / "summaries" / "manifest.json").write_text(
        json.dumps(
            {
                "Smith2023Finding": {
                    "pdf": "/docs/smith.pdf",
                    "summary": "/summaries/smith.md",
                }
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
    assert "style.css" in html  # CSS linked
    assert "script.js" in html  # JS linked
    assert "SYNTHESIS_MEMORY" in html  # inline const block present
    assert "SYNTHESIS_TOPIC" in html  # inline const block present

    # Citations
    assert 'data-key="Smith2023Finding"' in html
    assert 'data-title="A Study of X"' in html
    assert 'data-doi="10.1234/x"' in html
    assert 'data-pdf="file:///docs/smith.pdf"' in html
    assert 'data-summary="file:///summaries/smith.md"' in html

    # Lee2024Review is in bib but not manifest -> metadata present, paths empty
    assert 'data-key="Lee2024Review"' in html
    assert 'data-title="A Review of Y"' in html

    # No CDN or external resources
    assert "cdn." not in html
    assert "fonts.googleapis" not in html
