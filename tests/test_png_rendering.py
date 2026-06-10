"""Tests for Review Gate 5 Item 2 — optional PNG artifact rendering.

SVG is the dependency-free baseline (always present); PNG is an optional
convenience artifact that degrades gracefully when matplotlib is absent.
"""

import json

import pytest

from haen import visualization as viz
from haen.export import export_dossier, export_packaging_images
from haen.governance import check_text
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_components, build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def test_svg_always_written(tmp_path):
    index = export_packaging_images(build_sample_components(), build_sample_fleet()[0], tmp_path)
    for view in ("top", "side"):
        assert index[view]["svg"].exists()
        assert index[view]["svg"].read_text().startswith("<svg")


def test_png_optional_and_graceful(tmp_path):
    index = export_packaging_images(build_sample_components(), build_sample_fleet()[0], tmp_path)
    have_mpl = True
    try:  # pragma: no cover - environment dependent
        import matplotlib  # noqa: F401
    except Exception:
        have_mpl = False
    for view in ("top", "side"):
        png = index[view]["png"]
        if have_mpl:
            assert png is not None and png.exists()
        else:
            assert png is None  # graceful fallback, no hard failure


def test_prefer_png_false_skips_png(tmp_path):
    index = export_packaging_images(
        build_sample_components(), build_sample_fleet()[0], tmp_path, prefer_png=False
    )
    assert all(fmts["png"] is None for fmts in index.values())
    assert all(fmts["svg"].exists() for fmts in index.values())


def test_export_references_svg_and_records_png_state(tmp_path):
    text = build_dossier(
        programme="HAEN GT-1", branch="GT-1", vehicles=build_sample_fleet(),
        components=build_sample_components(), generated_at=FIXED_TS,
    )
    res = export_dossier(
        text, tmp_path, programme="HAEN GT-1", branch="GT-1", generated_at=FIXED_TS,
        components=build_sample_components(), vehicle=build_sample_fleet()[0],
    )
    body = res.dossier_path.read_text()
    # SVG always referenced + hashed
    assert "packaging_top.svg" in body
    assert "packaging_top.svg" in res.files
    # PNG state recorded in metadata; PNGs never enter the hashed files map
    meta = json.loads(res.metadata_path.read_text())
    assert "png_rendered" in meta and "png_artifacts" in meta
    assert not any(name.endswith(".png") for name in res.files)
    assert check_text(body) == []


def test_render_png_returns_bool(tmp_path):
    diagram = viz.packaging_diagram(build_sample_components(), view="top")
    result = viz.render_diagram_png(diagram, tmp_path / "x.png")
    assert isinstance(result, bool)
