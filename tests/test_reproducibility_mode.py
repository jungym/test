"""Tests for Gate 6 Item 3 — explicit reproducibility mode + addendum archive rules."""

import json
import zipfile

import pytest

from haen.export import archive_release, export_release_package, sha256_bytes
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_components, build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _package(out_dir, reproducible=True):
    fleet = build_sample_fleet()
    text = build_dossier(programme="HAEN GT-1", branch="GT-1", vehicles=fleet,
                         components=build_sample_components(), generated_at=FIXED_TS)
    return export_release_package(
        text, out_dir, programme="HAEN GT-1", branch="GT-1", generated_at=FIXED_TS,
        components=build_sample_components(), vehicle=fleet[0], reproducible=reproducible,
    )


def test_reproducible_requires_generated_at(tmp_path):
    with pytest.raises(ValueError):
        export_release_package("# x", tmp_path, programme="P", branch="GT-1",
                               reproducible=True)


def test_reproducible_mode_suppresses_png(tmp_path):
    pkg = _package(tmp_path, reproducible=True)
    assert pkg.manifest["optional_non_deterministic_artifacts"] == []
    assert not list(tmp_path.glob("*.png"))
    assert pkg.manifest["archive_determinism_status"] == "deterministic"
    assert pkg.manifest["reproducible"] is True


def test_manifest_determinism_fields_present(tmp_path):
    pkg = _package(tmp_path, reproducible=False)
    m = pkg.manifest
    for key in ["deterministic_core_artifacts", "optional_non_deterministic_artifacts",
                "archive_determinism_status", "archive_hash_sidecar", "reproducible"]:
        assert key in m
    assert m["archive_determinism_status"] == "non_deterministic"
    # hashed files are exactly the deterministic core
    assert sorted(m["files"]) == m["deterministic_core_artifacts"]
    assert not any(n.endswith(".png") for n in m["files"])


def test_archive_sidecar_written_outside_archive(tmp_path):
    pkgdir = tmp_path / "pkg"
    _package(pkgdir)
    archive = archive_release(pkgdir, generated_at=FIXED_TS)
    sidecar = archive.with_name(archive.name + ".sha256")
    assert sidecar.exists()
    # sidecar hash matches archive bytes
    assert sidecar.read_text().strip() == sha256_bytes(archive.read_bytes())
    # sidecar and archive live OUTSIDE the package dir; archive does not contain them
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
    assert sidecar.name not in names and archive.name not in names
    # manifest inside archive carries no hash of the archive itself
    manifest = json.loads((pkgdir / "manifest.json").read_text())
    assert "archive_sha256" not in manifest  # archive hash only in sidecar


def test_reproducible_archives_byte_equal(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _package(a)
    _package(b)
    za = archive_release(a, generated_at=FIXED_TS)
    zb = archive_release(b, generated_at=FIXED_TS)
    assert za.read_bytes() == zb.read_bytes()
    assert (za.with_name(za.name + ".sha256").read_text()
            == zb.with_name(zb.name + ".sha256").read_text())


def test_archive_timestamps_normalized_to_generated_at(tmp_path):
    pkgdir = tmp_path / "pkg"
    _package(pkgdir)
    archive = archive_release(pkgdir, generated_at=FIXED_TS)
    with zipfile.ZipFile(archive) as zf:
        stamps = {i.date_time for i in zf.infolist()}
    assert stamps == {(2026, 1, 1, 0, 0, 0)}
