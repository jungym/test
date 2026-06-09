"""Tests for 03_packaging: overlap and envelope detection."""

from haen.packaging import Box, Component, boxes_overlap, check_envelope, detect_overlaps
from haen.sample_data import build_sample_components, build_sample_fleet


def _box(cx, cy, cz, s=100):
    return Box(cx=cx, cy=cy, cz=cz, size_x=s, size_y=s, size_z=s)


def test_overlapping_boxes_detected():
    a = _box(0, 0, 0, s=100)
    b = _box(50, 0, 0, s=100)  # overlaps by 50 mm in x
    ov = boxes_overlap(a, b)
    assert ov is not None
    assert ov.overlap_x_mm > 0


def test_touching_boxes_within_tolerance_not_overlap():
    a = _box(0, 0, 0, s=100)
    b = _box(100, 0, 0, s=100)  # faces exactly touch at x=50
    assert boxes_overlap(a, b, tol_mm=1.0) is None


def test_separated_boxes_no_overlap():
    a = _box(0, 0, 0, s=100)
    b = _box(500, 0, 0, s=100)
    assert boxes_overlap(a, b) is None


def test_detect_overlaps_pairwise():
    comps = [
        Component(name="A", box=_box(0, 0, 0, s=100)),
        Component(name="B", box=_box(40, 0, 0, s=100)),   # overlaps A
        Component(name="C", box=_box(1000, 0, 0, s=100)),  # isolated
    ]
    overlaps = detect_overlaps(comps)
    assert len(overlaps) == 1
    assert {overlaps[0].a, overlaps[0].b} == {"A", "B"}


def test_rigid_only_skips_tolerant_zone():
    comps = [
        Component(name="rigid", box=_box(0, 0, 0, s=100), rigid=True),
        Component(name="zone", box=_box(40, 0, 0, s=100), rigid=False),
    ]
    assert detect_overlaps(comps, rigid_only=True) == []
    assert len(detect_overlaps(comps, rigid_only=False)) == 1


def test_sample_components_no_rigid_clash():
    # The seeded illustrative layout should be clash-free under the AABB check.
    assert detect_overlaps(build_sample_components()) == []


def test_envelope_violation_detected():
    fleet = build_sample_fleet()
    bev = fleet[0]
    huge = [Component(name="oversize", box=_box(0, 0, 0, s=9000))]
    violations = check_envelope(huge, bev)
    assert violations
