"""Tests for Gate 6 Items 2+6 — safe-section mechanism and Korean governance doc.

Safe sections are a docs-only mechanism (addendum §4): repository documentation
may quote verbatim forbidden examples inside markers; generated artifacts must
never contain the markers and remain fully hard-gated.
"""

from pathlib import Path

import pytest

from haen.cli import main
from haen.export import export_dossier
from haen.governance import (
    SAFE_SECTION_END,
    SAFE_SECTION_START,
    check_doc_text,
    check_text,
    contains_safe_section_markers,
    strip_safe_sections,
)
from haen.report_builder import build_dossier, build_release_readiness, release_readiness_md
from haen.rfi_builder import build_rfi
from haen.sample_data import build_sample_evidence, build_sample_fleet, build_sample_ledger

FIXED_TS = "2026-01-01T00:00:00+00:00"
KO_DOC = Path(__file__).resolve().parent.parent / "docs" / "claim_governance_ko.md"


# --------------------------------------------------------------------------- #
# Mechanism
# --------------------------------------------------------------------------- #
def test_strip_safe_sections_removes_marked_block():
    text = f"before\n{SAFE_SECTION_START}\n양산 가능\n{SAFE_SECTION_END}\nafter"
    stripped = strip_safe_sections(text)
    assert "양산 가능" not in stripped
    assert "before" in stripped and "after" in stripped


def test_check_doc_text_allows_safe_sections_only_when_enabled():
    text = f"{SAFE_SECTION_START}\nThis is road legal.\n{SAFE_SECTION_END}"
    assert check_doc_text(text, allow_safe_sections=True) == []
    assert check_doc_text(text, allow_safe_sections=False)  # still flagged
    assert check_text(text)  # hard gate unchanged


def test_unsafe_text_outside_safe_section_still_flagged():
    text = f"{SAFE_SECTION_START}\nexample\n{SAFE_SECTION_END}\nThis is crash safe."
    assert check_doc_text(text, allow_safe_sections=True)


# --------------------------------------------------------------------------- #
# Korean governance doc uses the mechanism correctly
# --------------------------------------------------------------------------- #
def test_korean_governance_doc_clean_via_safe_sections():
    text = KO_DOC.read_text(encoding="utf-8")
    # raw scan flags the quoted examples...
    assert check_text(text)
    # ...but the docs-only safe-section scan is clean
    assert check_doc_text(text, allow_safe_sections=True) == []
    # and the doc lives under docs/ (the only place safe sections are valid)
    assert "docs" in KO_DOC.parts


# --------------------------------------------------------------------------- #
# Generated artifacts contain no safe-section markers (addendum §4)
# --------------------------------------------------------------------------- #
def test_generated_outputs_have_no_safe_section_markers():
    fleet = build_sample_fleet()
    dossier = build_dossier(programme="P", branch="GT-1", vehicles=fleet,
                            generated_at=FIXED_TS)
    readiness = release_readiness_md(build_release_readiness(dossier_text=dossier))
    rfi = build_rfi(title="t", branch="all", ledger=build_sample_ledger(),
                    evidence=build_sample_evidence()).to_markdown()
    for text in (dossier, readiness, rfi):
        assert not contains_safe_section_markers(text)


def test_export_refuses_safe_section_markers(tmp_path):
    bad = f"# Dossier\n\nfine text\n{SAFE_SECTION_START}\nx\n{SAFE_SECTION_END}\n"
    with pytest.raises(ValueError, match="safe-section"):
        export_dossier(bad, tmp_path, programme="P", branch="GT-1", generated_at=FIXED_TS)
    assert not (tmp_path / "dossier.md").exists()


def test_release_candidate_package_marker_free(tmp_path):
    assert main(["release-candidate", "--out", str(tmp_path / "pkg"),
                 "--generated-at", FIXED_TS]) == 0
    for f in (tmp_path / "pkg").glob("*.md"):
        assert not contains_safe_section_markers(f.read_text(encoding="utf-8")), f.name
