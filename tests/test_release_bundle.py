"""Tests for Review Gate 5 Item 6 — internal release bundle export."""

import zipfile

from haen.export import archive_release, export_release_package, validate_release
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_components, build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _package(out_dir):
    fleet = build_sample_fleet()
    text = build_dossier(programme="HAEN GT-1", branch="GT-1", vehicles=fleet,
                         components=build_sample_components(), generated_at=FIXED_TS)
    return export_release_package(
        text, out_dir, programme="HAEN GT-1", branch="GT-1", generated_at=FIXED_TS,
        components=build_sample_components(), vehicle=fleet[0],
    )


def test_archive_created_with_expected_files(tmp_path):
    pkgdir = tmp_path / "pkg"
    _package(pkgdir)
    archive = archive_release(pkgdir)
    assert archive.exists()
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
    for expected in ["dossier.md", "manifest.json", "packaging_top.svg",
                     "validation_report.json"]:
        assert expected in names


def test_manifest_validates_after_unpack(tmp_path):
    pkgdir = tmp_path / "pkg"
    _package(pkgdir)
    archive = archive_release(pkgdir)
    dest = tmp_path / "unpacked"
    with zipfile.ZipFile(archive) as zf:
        zf.extractall(dest)
    assert validate_release(dest) == []


def test_archive_namelist_is_deterministic(tmp_path):
    a_dir, b_dir = tmp_path / "a", tmp_path / "b"
    _package(a_dir)
    _package(b_dir)
    with zipfile.ZipFile(archive_release(a_dir)) as za:
        na = za.namelist()
    with zipfile.ZipFile(archive_release(b_dir)) as zb:
        nb = zb.namelist()
    assert na == nb  # sorted, stable ordering


def test_validation_report_is_internal_only(tmp_path):
    import json
    pkgdir = tmp_path / "pkg"
    _package(pkgdir)
    from haen.export import write_validation_report
    path = write_validation_report(pkgdir)
    report = json.loads(path.read_text())
    assert report["valid"] is True
    assert report["external_release_allowed"] is False
    assert report["internal_only"] is True
