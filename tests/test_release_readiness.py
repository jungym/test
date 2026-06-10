"""Tests for Review Gate 5 Item 9 — internal release-readiness checklist."""

from haen.governance import check_text
from haen.report_builder import build_release_readiness, release_readiness_md
from haen.sample_data import build_sample_fleet
from haen.report_builder import build_dossier

FIXED_TS = "2026-01-01T00:00:00+00:00"


def test_required_fields_present():
    c = build_release_readiness()
    for key in ["gates", "ci_status", "artifact_validation", "forbidden_claim_status",
                "human_review_required", "external_release_allowed", "internal_only", "notes"]:
        assert key in c
    assert set(c["gates"]) == {"gate_1", "gate_2", "gate_3", "gate_4", "gate_5"}


def test_defaults_internal_only():
    c = build_release_readiness()
    assert c["human_review_required"] is True
    assert c["external_release_allowed"] is False
    assert c["internal_only"] is True


def test_forbidden_status_reflects_dossier():
    clean = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet(),
                          generated_at=FIXED_TS)
    assert build_release_readiness(dossier_text=clean)["forbidden_claim_status"] == "clean"
    bad = build_release_readiness(dossier_text="This is road legal.")
    assert "finding" in bad["forbidden_claim_status"]


def test_validation_status_reflected():
    assert build_release_readiness(validation_problems=[])["artifact_validation"] == "ok"
    assert "problem" in build_release_readiness(
        validation_problems=["checksum mismatch: x"])["artifact_validation"]
    assert build_release_readiness()["artifact_validation"] == "not_run"


def test_markdown_is_governance_clean_and_deterministic():
    c = build_release_readiness()
    md = release_readiness_md(c)
    assert check_text(md) == []
    assert "INTERNAL" in md
    assert release_readiness_md(c) == md
