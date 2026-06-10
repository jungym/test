"""Tests for Gate 6 Items 1 + 8 — semantic-risk surfacing and readiness consolidation."""

from haen import mass_energy
from haen.governance import check_text
from haen.report_builder import (
    build_dossier,
    build_release_readiness,
    release_readiness_md,
)
from haen.sample_data import build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _dossier():
    return build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet(),
                         generated_at=FIXED_TS)


def test_dossier_has_advisory_semantic_section():
    text = _dossier()
    assert "Advisory semantic-risk review (warning-only)" in text
    # clean fleet -> no findings, explicitly stated
    assert "No advisory semantic-risk findings" in text
    assert "hard" in text and "authoritative" in text
    assert check_text(text) == []  # hard gate still clean


def test_dossier_semantic_section_deterministic():
    assert _dossier() == _dossier()


def test_readiness_consolidates_semantic_and_completeness():
    fleet = build_sample_fleet()
    c = build_release_readiness(
        dossier_text=_dossier(),
        validation_problems=[],
        completeness=mass_energy.metadata_completeness(fleet[0]),
    )
    assert c["semantic_risk_status"].startswith("none")
    assert "line items with full provenance" in c["metadata_completeness"]
    assert c["artifact_validation"] == "ok"
    md = release_readiness_md(c)
    assert "Advisory semantic-risk" in md
    assert "Metadata completeness" in md
    assert check_text(md) == []


def test_readiness_reports_advisory_count_when_present():
    c = build_release_readiness(semantic_findings=3)
    assert "3 advisory finding(s)" in c["semantic_risk_status"]
    c2 = build_release_readiness()
    assert c2["semantic_risk_status"] == "not_run"
    assert c2["metadata_completeness"] == "not_run"
