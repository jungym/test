"""Gate 6 Item 5 — end-to-end internal release-candidate acceptance test.

Runs the full pipeline via the CLI and asserts every required package element is
present, internal-only, governance-clean, validated, and reproducible. Reuses the
canonical reproducibility mechanism (no separate path) per the Gate 6 addendum.
"""

import json
import zipfile

from haen.cli import main
from haen.export import validate_release, validate_release_archive
from haen.governance import check_text

FIXED_TS = "2026-01-01T00:00:00+00:00"

REQUIRED_FILES = [
    "dossier.md",
    "dossier.meta.json",
    "rfi.md",
    "manifest.json",
    "packaging_top.svg",
    "packaging_side.svg",
    "validation_report.json",
    "readiness.md",
]


def _build(out_dir):
    return main(["release-candidate", "--out", str(out_dir), "--generated-at", FIXED_TS])


def test_end_to_end_release_candidate(tmp_path):
    pkg = tmp_path / "internal_review"
    assert _build(pkg) == 0

    # 1. Every required element exists, plus archive + sidecar.
    for name in REQUIRED_FILES:
        assert (pkg / name).exists(), f"missing {name}"
    archive = tmp_path / "internal_review.zip"
    sidecar = tmp_path / "internal_review.zip.sha256"
    assert archive.exists() and sidecar.exists()

    # 2. Package and archive validate (per-file checksums, bundle hash,
    #    sidecar hash, internal-only flags, forbidden-claim re-scan).
    assert validate_release(pkg) == []
    assert validate_release_archive(archive) == []

    # 3. Internal-only governance metadata throughout.
    manifest = json.loads((pkg / "manifest.json").read_text())
    assert manifest["internal_only"] is True
    assert manifest["human_review_required"] is True
    assert manifest["external_release_allowed"] is False
    report = json.loads((pkg / "validation_report.json").read_text())
    assert report["valid"] is True and report["external_release_allowed"] is False

    # 4. Generated prose artifacts are governance-clean (hard gate) and carry
    #    the advisory semantic-risk and readiness consolidation sections.
    dossier = (pkg / "dossier.md").read_text()
    readiness = (pkg / "readiness.md").read_text()
    rfi = (pkg / "rfi.md").read_text()
    for text in (dossier, readiness, rfi):
        assert check_text(text) == []
    assert "Advisory semantic-risk review" in dossier
    assert "Advisory semantic-risk" in readiness
    assert "human_review_required:** true" in dossier

    # 5. Reproducibility: a second build is byte-identical (package + archive).
    pkg2 = tmp_path / "second"
    assert _build(pkg2) == 0
    for name in REQUIRED_FILES:
        assert (pkg / name).read_bytes() == (pkg2 / name).read_bytes(), name
    assert archive.read_bytes() == (tmp_path / "second.zip").read_bytes()

    # 6. Archive contains the package files with normalized timestamps and
    #    never contains itself or its sidecar.
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        stamps = {i.date_time for i in zf.infolist()}
    assert set(REQUIRED_FILES) <= names
    assert archive.name not in names and sidecar.name not in names
    assert stamps == {(2026, 1, 1, 0, 0, 0)}

    # 7. Reproducible mode recorded; deterministic core excludes raster output.
    assert manifest["reproducible"] is True
    assert manifest["archive_determinism_status"] == "deterministic"
    assert manifest["optional_non_deterministic_artifacts"] == []
