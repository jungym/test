"""Tests for Review Gate 4 Item 4 — mass/energy metadata in the dossier."""

from haen.governance import check_text
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _dossier():
    return build_dossier(
        programme="HAEN GT-1", branch="GT-1", vehicles=build_sample_fleet(),
        generated_at=FIXED_TS,
    )


def test_dossier_shows_mass_line_item_provenance():
    text = _dossier()
    assert "mass line items (with provenance)" in text
    # metadata columns surfaced
    for col in ["label", "source_type", "confidence", "assumption_notes"]:
        assert col in text


def test_dossier_shows_energy_line_items():
    text = _dossier()
    assert "energy line items (with provenance)" in text
    assert "gravimetric_energy_density" in text or "usable_energy" in text


def test_dossier_reports_metadata_completeness():
    text = _dossier()
    assert "Metadata completeness for" in text


def test_dossier_remains_governance_clean():
    assert check_text(_dossier()) == []


def test_deterministic_with_fixed_timestamp():
    assert _dossier() == _dossier()
