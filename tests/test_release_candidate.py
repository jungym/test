"""Tests for Gate 6 Item 4 — release-candidate command (shared reproducibility path)."""

import json

from haen.cli import main
from haen.export import export_release_package
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_components, build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _run_rc(out_dir):
    return main(["release-candidate", "--out", str(out_dir),
                 "--generated-at", FIXED_TS, "--branch", "GT-1"])


def test_release_candidate_builds_full_package(tmp_path, capsys):
    rc = _run_rc(tmp_path / "pkg")
    out = capsys.readouterr().out
    assert rc == 0
    assert "INTERNAL ONLY" in out
    d = tmp_path / "pkg"
    for name in ["dossier.md", "dossier.meta.json", "rfi.md", "manifest.json",
                 "packaging_top.svg", "packaging_side.svg",
                 "validation_report.json", "readiness.md"]:
        assert (d / name).exists(), name
    assert (tmp_path / "pkg.zip").exists()
    assert (tmp_path / "pkg.zip.sha256").exists()


def test_release_candidate_uses_shared_repro_mechanism(tmp_path):
    """Direct export mode and release-candidate mode share generated_at + ordering."""
    _run_rc(tmp_path / "rc")
    rc_manifest = json.loads((tmp_path / "rc" / "manifest.json").read_text())
    assert rc_manifest["reproducible"] is True
    assert rc_manifest["generated_at"] == FIXED_TS

    # Direct export with identical inputs through the same export function.
    fleet = build_sample_fleet()
    text = build_dossier(programme="HAEN GT-1", branch="GT-1", vehicles=fleet,
                         components=build_sample_components(), generated_at=FIXED_TS)
    direct = export_release_package(
        text, tmp_path / "direct", programme="HAEN GT-1", branch="GT-1",
        generated_at=FIXED_TS, components=build_sample_components(),
        vehicle=fleet[0], reproducible=True,
    )
    # Same generated_at propagation and the same stable file ordering behaviour.
    assert direct.manifest["generated_at"] == rc_manifest["generated_at"]
    assert sorted(direct.manifest["files"]) == direct.manifest["deterministic_core_artifacts"]
    assert sorted(rc_manifest["files"]) == rc_manifest["deterministic_core_artifacts"]
    # The dossier produced by both flows is byte-identical (same hash).
    assert (rc_manifest["files"]["dossier.md"]
            == direct.manifest["files"]["dossier.md"])


def test_release_candidate_reproducible_archives(tmp_path):
    _run_rc(tmp_path / "a")
    _run_rc(tmp_path / "b")
    assert (tmp_path / "a.zip").read_bytes() == (tmp_path / "b.zip").read_bytes()


def test_release_candidate_readiness_consolidated(tmp_path):
    _run_rc(tmp_path / "pkg")
    md = (tmp_path / "pkg" / "readiness.md").read_text()
    assert "Artifact validation: **ok**" in md
    assert "Advisory semantic-risk" in md
    assert "Metadata completeness" in md
    assert "external_release_allowed: **false**" in md


def test_release_candidate_non_repro_mode(tmp_path):
    rc = main(["release-candidate", "--out", str(tmp_path / "pkg")])
    assert rc == 0
    manifest = json.loads((tmp_path / "pkg" / "manifest.json").read_text())
    assert manifest["reproducible"] is False
    assert manifest["archive_determinism_status"] == "non_deterministic"
