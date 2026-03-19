import subprocess
import sys
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
