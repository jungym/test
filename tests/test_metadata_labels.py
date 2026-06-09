"""Tests for Review Gate 3 Item 2 — per-line-item mass/energy metadata labels."""

import pytest
from pydantic import ValidationError

from haen import mass_energy
from haen.governance import Confidence, DataLabel, check_text
from haen.sample_data import build_sample_fleet
from haen.vehicle_definition import EnergyItem, MassItem


# --------------------------------------------------------------------------- #
# Complete metadata passes
# --------------------------------------------------------------------------- #
def test_mass_item_complete_metadata():
    m = MassItem(
        name="x", mass_kg=100, group="structure", unit="kg",
        label=DataLabel.ASSUMPTION, source_type="engineering_assumption",
        confidence=Confidence.LOW, assumption_notes="note",
    )
    assert m.value == 100
    assert m.unit == "kg"
    assert m.metadata_complete() is True


def test_energy_item_complete_metadata():
    e = EnergyItem(
        name="usable_energy", value=95, unit="kWh",
        label=DataLabel.ASSUMPTION, source_type="branch_assumption",
        confidence=Confidence.LOW, assumption_notes="note",
    )
    assert e.value == 95
    assert e.metadata_complete() is True


# --------------------------------------------------------------------------- #
# Deterministic defaults for missing metadata
# --------------------------------------------------------------------------- #
def test_mass_item_defaults_deterministic():
    m = MassItem(name="x", mass_kg=100)
    assert m.unit == "kg"
    assert m.label is DataLabel.ASSUMPTION
    assert m.source_type == "assumption"
    assert m.confidence is Confidence.LOW
    assert m.assumption_notes == ""
    # missing assumption_notes -> not "complete" (surfaced as a gap, deterministically)
    assert m.metadata_complete() is False


# --------------------------------------------------------------------------- #
# Invalid metadata fails
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("kw", [
    {"label": "not_a_label"},
    {"confidence": "super_high"},
])
def test_invalid_metadata_rejected(kw):
    base = dict(name="x", mass_kg=100)
    base.update(kw)
    with pytest.raises(ValidationError):
        MassItem(**base)


def test_negative_value_rejected():
    with pytest.raises(ValidationError):
        EnergyItem(name="e", value=-1, unit="kWh")


# --------------------------------------------------------------------------- #
# Serialization + comparison output preserve metadata
# --------------------------------------------------------------------------- #
def test_serialization_includes_metadata():
    m = MassItem(name="x", mass_kg=100, source_type="calc", assumption_notes="n")
    d = m.model_dump(mode="json")
    for key in ["unit", "label", "source_type", "confidence", "assumption_notes"]:
        assert key in d


def test_mass_breakdown_table_has_metadata_columns():
    bev = build_sample_fleet()[0]
    df = mass_energy.mass_breakdown_table(bev)
    for col in ["label", "source_type", "confidence", "assumption_notes", "metadata_complete"]:
        assert col in df.columns
    # sample BEV items were enriched -> all complete
    assert df["metadata_complete"].all()


def test_energy_line_items_have_metadata():
    bev = build_sample_fleet()[0]
    items = mass_energy.energy_line_items(bev)
    assert len(items) >= 3
    for it in items:
        assert it.unit
        assert it.source_type
        assert it.assumption_notes
        assert it.metadata_complete() is True
    df = mass_energy.energy_line_items_table(bev)
    assert "label" in df.columns and "confidence" in df.columns


def test_metadata_completeness_counts():
    bev = build_sample_fleet()[0]
    summary = mass_energy.metadata_completeness(bev)
    assert summary["total"] == summary["complete"] + summary["incomplete"]
    assert summary["complete"] >= 1


# --------------------------------------------------------------------------- #
# Governance
# --------------------------------------------------------------------------- #
def test_metadata_text_is_governance_clean():
    bev = build_sample_fleet()[0]
    text = mass_energy.mass_breakdown_table(bev).to_string() + \
        mass_energy.energy_line_items_table(bev).to_string()
    assert check_text(text) == []
