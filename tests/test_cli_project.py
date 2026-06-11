"""Tests for Gate 7 A2 — CLI runs on a user --project (and sample fallback)."""

import json

from haen import io
from haen.cli import main
from haen.sample_data import (
    build_sample_components,
    build_sample_fleet,
    build_sample_partners,
)

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _make_project(tmp_path):
    io.dump_models(build_sample_fleet(), tmp_path / "vehicles.yaml", key="vehicles")
    io.dump_models(build_sample_components(), tmp_path / "components.yaml", key="components")
    io.dump_models(build_sample_partners(), tmp_path / "partners.yaml", key="partners")
    manifest = tmp_path / "haen-project.yaml"
    manifest.write_text(
        "programme: HAEN GT-1\nbranch: GT-1\n"
        "vehicles: vehicles.yaml\ncomponents: components.yaml\npartners: partners.yaml\n",
        encoding="utf-8",
    )
    return manifest


def test_compare_with_project(tmp_path, capsys):
    manifest = _make_project(tmp_path)
    rc = main(["compare", "--project", str(manifest)])
    assert rc == 0
    assert "GT-1-c01" in capsys.readouterr().out


def test_release_candidate_with_project(tmp_path):
    manifest = _make_project(tmp_path)
    rc = main(["release-candidate", "--out", str(tmp_path / "pkg"),
               "--generated-at", FIXED_TS, "--project", str(manifest)])
    assert rc == 0
    assert (tmp_path / "pkg" / "dossier.md").exists()
    assert (tmp_path / "pkg.zip").exists()
    manifest_json = json.loads((tmp_path / "pkg" / "manifest.json").read_text())
    assert manifest_json["programme"] == "HAEN GT-1"
    assert manifest_json["external_release_allowed"] is False


def test_sample_fallback_without_project(capsys):
    # No --project -> bundled sample still works (backward compatible).
    assert main(["simulate"]) == 0
    assert "GT-1-c01" in capsys.readouterr().out


def test_project_with_distinct_data_flows_through(tmp_path, capsys):
    # A single-vehicle project with a custom id proves real data is used.
    fleet = build_sample_fleet()[:1]
    fleet[0] = fleet[0].model_copy(update={"id": "CUSTOM-X1", "name": "Custom concept"})
    io.dump_models(fleet, tmp_path / "v.yaml", key="vehicles")
    manifest = tmp_path / "haen-project.yaml"
    manifest.write_text("programme: My Programme\nbranch: GT-1\nvehicles: v.yaml\n",
                        encoding="utf-8")
    rc = main(["simulate", "--project", str(manifest)])
    assert rc == 0
    assert "CUSTOM-X1" in capsys.readouterr().out
