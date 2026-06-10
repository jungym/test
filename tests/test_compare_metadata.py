"""Tests for Review Gate 5 Item 3 — per-line metadata in the compare table."""

from haen import mass_energy
from haen.governance import check_text
from haen.sample_data import build_sample_fleet
from haen.vehicle_definition import MassItem


def test_metadata_columns_present():
    df = mass_energy.compare_with_metadata(build_sample_fleet())
    for col in ["value", "unit", "label", "source_type", "confidence",
                "assumption_notes", "metadata_complete"]:
        assert col in df.columns


def test_includes_mass_and_energy_rows():
    df = mass_energy.compare_with_metadata(build_sample_fleet())
    kinds = set(df["kind"])
    assert "mass" in kinds and "energy" in kinds


def test_deterministic():
    fleet = build_sample_fleet()
    assert mass_energy.compare_with_metadata(fleet).equals(
        mass_energy.compare_with_metadata(fleet)
    )


def test_incomplete_metadata_flagged():
    bev = build_sample_fleet()[0]
    bev.mass_breakdown.append(MassItem(name="Unlabelled part", mass_kg=4))
    df = mass_energy.compare_with_metadata([bev])
    row = df[df["name"] == "Unlabelled part"].iloc[0]
    assert row["metadata_complete"] is False or row["metadata_complete"] == False  # noqa: E712


def test_existing_compare_unchanged():
    # The summary compare() keeps its original (no per-line metadata) shape.
    df = mass_energy.compare(build_sample_fleet())
    assert "assumption_notes" not in df.columns
    assert "curb_mass_kg" in df.columns


def test_governance_clean():
    text = mass_energy.compare_with_metadata(build_sample_fleet()).to_string()
    assert check_text(text) == []
