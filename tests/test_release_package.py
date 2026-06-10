"""Tests for Review Gate 4 Item 7 — release package, manifest, validation."""

import json

import pytest

from haen.export import export_release_package, validate_release
from haen.report_builder import build_dossier
from haen.rfi_builder import build_rfi
from haen.sample_data import (
    build_sample_components,
    build_sample_evidence,
    build_sample_fleet,
    build_sample_ledger,
)

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _package(out_dir):
    fleet = build_sample_fleet()
    text = build_dossier(
        programme="HAEN GT-1", branch="GT-1", vehicles=fleet,
        components=build_sample_components(), generated_at=FIXED_TS,
    )
    rfi = build_rfi(title="GT-1 RFI", branch="GT-1",
                    ledger=build_sample_ledger(), evidence=build_sample_evidence())
    return export_release_package(
        text, out_dir, programme="HAEN GT-1", branch="GT-1", commit="deadbee",
        generated_at=FIXED_TS, components=build_sample_components(),
        vehicle=fleet[0], rfi_markdown=rfi.to_markdown(),
    )


def test_package_contains_expected_files(tmp_path):
    pkg = _package(tmp_path)
    for name in ["dossier.md", "dossier.meta.json", "rfi.md", "manifest.json",
                 "packaging_top.svg", "packaging_side.svg"]:
        assert (tmp_path / name).exists(), name
    assert "dossier.md" in pkg.files and "rfi.md" in pkg.files


def test_manifest_checksums_match(tmp_path):
    _package(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["files"]  # non-empty
    # validate recomputes and compares
    assert validate_release(tmp_path) == []


def test_manifest_is_internal_only(tmp_path):
    _package(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["internal_only"] is True
    assert manifest["human_review_required"] is True
    assert manifest["external_release_allowed"] is False


def test_validate_detects_tamper(tmp_path):
    _package(tmp_path)
    (tmp_path / "dossier.md").write_text(
        (tmp_path / "dossier.md").read_text() + "\n\n(tampered)\n", encoding="utf-8"
    )
    problems = validate_release(tmp_path)
    assert any("checksum mismatch" in p for p in problems)


def test_validate_missing_manifest(tmp_path):
    assert validate_release(tmp_path) == ["manifest.json missing"]


def test_reproducible_with_fixed_timestamp(tmp_path):
    a = _package(tmp_path / "a")
    b = _package(tmp_path / "b")
    assert a.files == b.files  # identical checksums
    assert (tmp_path / "a" / "manifest.json").read_bytes() == \
        (tmp_path / "b" / "manifest.json").read_bytes()


def test_forbidden_claim_in_rfi_refused(tmp_path):
    fleet = build_sample_fleet()
    text = build_dossier(programme="P", branch="GT-1", vehicles=fleet, generated_at=FIXED_TS)
    with pytest.raises(ValueError):
        export_release_package(
            text, tmp_path, programme="P", branch="GT-1", generated_at=FIXED_TS,
            rfi_markdown="This design is road legal and production feasible.",
        )
