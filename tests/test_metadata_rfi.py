"""Tests for Review Gate 4 Item 6 — metadata-completeness-driven RFI prompts."""

from haen.governance import check_text
from haen.rfi_builder import build_rfi
from haen.sample_data import build_sample_fleet
from haen.vehicle_definition import MassItem


def test_incomplete_metadata_creates_rfi_prompt():
    bev = build_sample_fleet()[0]
    # default-metadata item has empty assumption_notes -> incomplete
    bev.mass_breakdown.append(MassItem(name="Mystery ballast", mass_kg=5))
    rfi = build_rfi(title="t", branch="all", vehicles=[bev])
    m_items = [i for i in rfi.items if i.ref.startswith("M-")]
    assert m_items
    assert any("Mystery ballast" in i.topic for i in m_items)
    assert all(i.priority == "low" for i in m_items)


def test_complete_metadata_creates_no_prompts():
    # Sample fleet: BEV mass items enriched; energy line items always labelled.
    rfi = build_rfi(title="t", branch="all", vehicles=build_sample_fleet())
    m_items = [i for i in rfi.items if i.ref.startswith("M-")]
    assert m_items == []


def test_prompt_names_missing_fields():
    bev = build_sample_fleet()[0]
    bev.mass_breakdown.append(MassItem(name="Unlabelled bracket", mass_kg=3))
    rfi = build_rfi(title="t", branch="all", vehicles=[bev])
    m = next(i for i in rfi.items if "Unlabelled bracket" in i.topic)
    assert "assumption_notes" in m.question or "source_type" in m.question


def test_metadata_rfi_markdown_is_governance_clean():
    bev = build_sample_fleet()[0]
    bev.mass_breakdown.append(MassItem(name="TBD part", mass_kg=2))
    rfi = build_rfi(title="t", branch="all", vehicles=[bev])
    md = rfi.to_markdown()
    assert check_text(md) == []
    # never asserts a supplier is confirmed
    assert "supplier confirmed" not in md.lower()
