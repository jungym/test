"""Tests for Review Gate 5 Item 5 — stronger artifact integrity (bundle hash)."""

import json

from haen.export import export_release_package, validate_release
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


def test_manifest_has_bundle_hash(tmp_path):
    pkg = _package(tmp_path)
    assert "bundle_sha256" in pkg.manifest
    assert validate_release(tmp_path) == []


def test_bundle_hash_deterministic(tmp_path):
    a = _package(tmp_path / "a")
    b = _package(tmp_path / "b")
    assert a.manifest["bundle_sha256"] == b.manifest["bundle_sha256"]


def test_validate_detects_file_tamper(tmp_path):
    _package(tmp_path)
    (tmp_path / "dossier.md").write_text(
        (tmp_path / "dossier.md").read_text() + "\nx\n", encoding="utf-8"
    )
    assert any("checksum mismatch" in p for p in validate_release(tmp_path))


def test_validate_detects_manifest_filelist_tamper(tmp_path):
    _package(tmp_path)
    mpath = tmp_path / "manifest.json"
    manifest = json.loads(mpath.read_text())
    # Tamper a declared checksum without updating the bundle hash.
    first = next(iter(manifest["files"]))
    manifest["files"][first] = "0" * 64
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    problems = validate_release(tmp_path)
    assert any("bundle hash mismatch" in p for p in problems)


def test_internal_only_metadata_preserved(tmp_path):
    pkg = _package(tmp_path)
    assert pkg.manifest["internal_only"] is True
    assert pkg.manifest["external_release_allowed"] is False
    assert pkg.manifest["human_review_required"] is True
