"""Tests for Review Gate 5 Item 4 — completeness-gap RFI prompts in default CLI RFI."""

from haen.cli import main
from haen.governance import check_text
from haen.rfi_builder import build_rfi
from haen.sample_data import build_sample_fleet
from haen.vehicle_definition import MassItem


def test_default_cli_rfi_runs_clean(capsys):
    rc = main(["rfi", "--branch", "all"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "Request for Information" in out
    assert check_text(out) == []
    # never asserts a confirmed supplier
    assert "supplier confirmed" not in out.lower()


def test_default_pipeline_surfaces_completeness_prompts():
    # The default RFI pipeline (vehicles wired in) yields M- prompts for gaps.
    fleet = build_sample_fleet()
    fleet[0].mass_breakdown.append(MassItem(name="Unlabelled gap part", mass_kg=3))
    rfi = build_rfi(title="t", branch="all", vehicles=fleet)
    m_items = [i for i in rfi.items if i.ref.startswith("M-")]
    assert any("Unlabelled gap part" in i.topic for i in m_items)


def test_complete_metadata_suppresses_prompts():
    # Stock sample fleet is fully labelled -> no completeness noise.
    rfi = build_rfi(title="t", branch="all", vehicles=build_sample_fleet())
    assert [i for i in rfi.items if i.ref.startswith("M-")] == []
