"""Tests for Review Gate 4 Item 3 — embedded packaging artifacts (SVG)."""

from haen import visualization as viz
from haen.export import export_dossier, export_packaging_svgs
from haen.governance import check_text
from haen.packaging import Box, Component
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_components, build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


# --------------------------------------------------------------------------- #
# Dependency-free SVG generation
# --------------------------------------------------------------------------- #
def test_svg_is_deterministic_and_wellformed():
    d = viz.packaging_diagram(build_sample_components(), build_sample_fleet()[0], view="top")
    a = viz.diagram_to_svg(d)
    b = viz.diagram_to_svg(d)
    assert a == b  # deterministic
    assert a.startswith("<svg") and a.rstrip().endswith("</svg>")
    assert "INTERNAL" in a


def test_svg_handles_empty_diagram():
    d = viz.packaging_diagram([], view="top")
    svg = viz.diagram_to_svg(d)
    assert svg.startswith("<svg") and "empty" in svg


def test_svg_marks_conflicts():
    comps = [
        Component(name="A", box=Box(cx=0, cy=0, cz=0, size_x=100, size_y=100, size_z=100)),
        Component(name="B", box=Box(cx=40, cy=0, cz=0, size_x=100, size_y=100, size_z=100)),
    ]
    d = viz.packaging_diagram(comps, view="top")
    svg = viz.diagram_to_svg(d)
    assert 'fill="red"' in svg  # conflict rectangle rendered


# --------------------------------------------------------------------------- #
# Export writes SVGs and embeds references (no plotting dependency needed)
# --------------------------------------------------------------------------- #
def test_export_packaging_svgs(tmp_path):
    files = export_packaging_svgs(build_sample_components(), build_sample_fleet()[0], tmp_path)
    assert set(files) == {"top", "side"}
    for p in files.values():
        assert p.exists()
        assert p.read_text().startswith("<svg")


def test_export_dossier_embeds_image_references(tmp_path):
    text = build_dossier(
        programme="HAEN GT-1", branch="GT-1", vehicles=build_sample_fleet(),
        components=build_sample_components(), generated_at=FIXED_TS,
    )
    res = export_dossier(
        text, tmp_path, programme="HAEN GT-1", branch="GT-1", generated_at=FIXED_TS,
        components=build_sample_components(), vehicle=build_sample_fleet()[0],
    )
    body = res.dossier_path.read_text()
    assert "Packaging diagrams (internal" in body
    assert "packaging_top.svg" in body and "packaging_side.svg" in body
    assert (tmp_path / "packaging_top.svg").exists()
    assert "packaging_top.svg" in res.files and "packaging_side.svg" in res.files
    assert check_text(body) == []


def test_export_without_components_writes_no_images(tmp_path):
    text = build_dossier(programme="P", branch="GT-1", vehicles=build_sample_fleet(),
                         generated_at=FIXED_TS)
    res = export_dossier(text, tmp_path, programme="P", branch="GT-1", generated_at=FIXED_TS)
    assert res.image_paths == {}
    assert not (tmp_path / "packaging_top.svg").exists()
