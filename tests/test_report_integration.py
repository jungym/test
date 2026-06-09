"""Tests for Review Gate 2 Item 5 — report/gate integration + report governance.

Verifies the dossier now carries governance report metadata
(human_review_required / external_release_allowed=false / internal-only), the
per-branch gate status, and the dynamics screening section — all governance-clean.
"""

from haen.governance import ReportMetadata, check_text
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_fleet


def test_report_metadata_defaults_conservative():
    m = ReportMetadata()
    assert m.human_review_required is True
    assert m.external_release_allowed is False
    assert m.internal_only is True
    banner = m.banner()
    assert "human_review_required:** true" in banner
    assert "external_release_allowed:** false" in banner


def test_dossier_includes_governance_metadata():
    text = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet())
    assert check_text(text) == []
    assert "human_review_required:** true" in text
    assert "external_release_allowed:** false" in text
    assert "INTERNAL" in text


def test_dossier_includes_gate_status():
    text = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet())
    assert "Branch gate status" in text
    # Seed gate statuses surface in the dossier.
    assert "watch_branch" in text
    assert "in_progress" in text


def test_dossier_includes_dynamics_screening():
    text = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet())
    assert "Dynamics screening" in text
    assert "stopping_dist_m@100kph" in text
    assert "long_load_transfer_N" in text
    assert "low_fidelity_screening" in text
    assert check_text(text) == []


def test_external_release_flag_can_be_overridden_but_default_false():
    # Even if a caller sets it true, the default remains false and the model
    # records the choice explicitly (human decision, not the tool's default).
    default = ReportMetadata()
    assert default.external_release_allowed is False
    overridden = ReportMetadata(external_release_allowed=True)
    assert overridden.external_release_allowed is True
