"""Tests for Review Gate 3 Item 5 — packaging-to-report integration."""

from haen.governance import check_text
from haen.packaging import Box, Component
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_components, build_sample_fleet


def _dossier_with_components(components):
    return build_dossier(
        programme="P", branch="GT-1", vehicles=build_sample_fleet(), components=components
    )


def test_packaging_section_present_and_clean():
    text = _dossier_with_components(build_sample_components())
    assert "## 6. Packaging check" in text
    assert "axis-aligned bounding boxes" in text
    assert "Internal-only" in text
    assert check_text(text) == []


def test_no_conflicts_for_sample_layout():
    text = _dossier_with_components(build_sample_components())
    assert "No rigid-body interferences detected" in text


def test_conflicts_reported_when_present():
    comps = [
        Component(name="A", box=Box(cx=0, cy=0, cz=0, size_x=100, size_y=100, size_z=100)),
        Component(name="B", box=Box(cx=40, cy=0, cz=0, size_x=100, size_y=100, size_z=100)),
    ]
    text = _dossier_with_components(comps)
    assert "Conflicts (interferences) detected" in text
    assert check_text(text) == []


def test_packaging_absent_message_when_no_components():
    text = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet())
    assert "packaging check not included" in text.lower()


def test_report_remains_internal_and_human_review_required():
    text = _dossier_with_components(build_sample_components())
    assert "human_review_required:** true" in text
    assert "external_release_allowed:** false" in text
    assert "INTERNAL" in text
