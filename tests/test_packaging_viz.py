"""Tests for Review Gate 3 Item 4 — packaging visualization.

Targets the pure, deterministic diagram model (no plotting dependency required).
The Plotly renderer is exercised only when plotly is importable.
"""

import pytest

from haen import visualization as viz
from haen.governance import check_text
from haen.packaging import Box, Component
from haen.sample_data import build_sample_components, build_sample_fleet


def _box(cx, cy, cz, s=100):
    return Box(cx=cx, cy=cy, cz=cz, size_x=s, size_y=s, size_z=s)


# --------------------------------------------------------------------------- #
# Deterministic diagram model
# --------------------------------------------------------------------------- #
def test_topview_rect_coordinates():
    comps = [Component(name="A", box=Box(cx=0, cy=0, cz=0, size_x=200, size_y=100, size_z=50))]
    d = viz.packaging_diagram(comps, view="top")
    assert d.view == "top"
    r = d.rects[0]
    assert (r.x0, r.x1, r.y0, r.y1) == (-100, 100, -50, 50)


def test_sideview_uses_z_axis():
    comps = [Component(name="A", box=Box(cx=0, cy=0, cz=300, size_x=200, size_y=100, size_z=60))]
    d = viz.packaging_diagram(comps, view="side")
    r = d.rects[0]
    assert (r.y0, r.y1) == (270, 330)  # z bounds


def test_deterministic():
    comps = build_sample_components()
    a = viz.packaging_diagram(comps, view="top")
    b = viz.packaging_diagram(comps, view="top")
    assert a == b


def test_envelope_added_with_vehicle_and_absent_without():
    comps = build_sample_components()
    v = build_sample_fleet()[0]
    with_env = viz.packaging_diagram(comps, v, view="top")
    without_env = viz.packaging_diagram(comps, view="top")
    assert any(r.kind == "envelope" for r in with_env.rects)
    assert not any(r.kind == "envelope" for r in without_env.rects)


def test_sample_components_have_no_conflicts():
    d = viz.packaging_diagram(build_sample_components(), view="top")
    assert d.conflicts == ()


def test_conflict_visualization_includes_conflicts():
    comps = [
        Component(name="A", box=_box(0, 0, 0, s=100)),
        Component(name="B", box=_box(40, 0, 0, s=100)),  # overlaps A
    ]
    d = viz.packaging_diagram(comps, view="top")
    assert len(d.conflicts) == 1
    c = d.conflicts[0]
    assert c.kind == "conflict"
    assert c.x1 > c.x0 and c.y1 > c.y0  # a real intersection rectangle


def test_graceful_empty_and_bad_view():
    assert viz.packaging_diagram([], view="top").rects == ()
    with pytest.raises(ValueError):
        viz.packaging_diagram(build_sample_components(), view="oblique")


def test_internal_only_caption_clean():
    d = viz.packaging_diagram(build_sample_components(), view="top")
    assert d.internal_only is True
    assert "Internal-only" in d.caption
    assert check_text(d.caption) == []


# --------------------------------------------------------------------------- #
# Renderer (only if plotly is available)
# --------------------------------------------------------------------------- #
def test_renderer_builds_figure_if_plotly_available():
    pytest.importorskip("plotly")
    comps = [
        Component(name="A", box=_box(0, 0, 0, s=100)),
        Component(name="B", box=_box(40, 0, 0, s=100)),
    ]
    fig = viz.packaging_topview(comps, build_sample_fleet()[0])
    # shapes include components, envelope and the conflict rectangle
    assert len(fig.layout.shapes) >= 3
    side = viz.packaging_sideview(comps)
    assert side is not None
