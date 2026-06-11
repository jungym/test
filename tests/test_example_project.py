"""Gate 7 C1 — the committed examples/project/ loads and exports cleanly.

Guards the operator-guide workflow against drift.
"""

import json
from pathlib import Path

from haen import io
from haen.cli import main
from haen.export import validate_release_archive
from haen.governance import check_text

EXAMPLE = Path(__file__).resolve().parent.parent / "examples" / "project" / "haen-project.yaml"
FIXED_TS = "2026-01-01T00:00:00+00:00"


def test_example_project_loads():
    proj = io.load_project(EXAMPLE)
    assert len(proj.vehicles) >= 1
    assert proj.components and proj.partners
    assert proj.evidence is not None and len(proj.evidence.all()) >= 1
    assert proj.ledger is not None and len(proj.ledger.all()) >= 1


def test_example_project_release_candidate(tmp_path):
    rc = main(["release-candidate", "--project", str(EXAMPLE),
               "--out", str(tmp_path / "rc"), "--generated-at", FIXED_TS])
    assert rc == 0
    archive = tmp_path / "rc.zip"
    assert archive.exists() and (tmp_path / "rc.zip.sha256").exists()
    assert validate_release_archive(archive) == []

    manifest = json.loads((tmp_path / "rc" / "manifest.json").read_text())
    assert manifest["external_release_allowed"] is False
    assert manifest["reproducible"] is True

    dossier = (tmp_path / "rc" / "dossier.md").read_text()
    assert check_text(dossier) == []
    assert "example project" in dossier


def test_example_project_reproducible(tmp_path):
    for sub in ("a", "b"):
        main(["release-candidate", "--project", str(EXAMPLE),
              "--out", str(tmp_path / sub), "--generated-at", FIXED_TS])
    assert (tmp_path / "a.zip").read_bytes() == (tmp_path / "b.zip").read_bytes()
