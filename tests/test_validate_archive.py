"""Tests for Gate 6 Item 7 — archive validation UX."""

from haen.cli import main
from haen.export import validate_release_archive

FIXED_TS = "2026-01-01T00:00:00+00:00"


def _build(tmp_path):
    assert main(["release-candidate", "--out", str(tmp_path / "pkg"),
                 "--generated-at", FIXED_TS]) == 0
    return tmp_path / "pkg.zip"


def test_validate_archive_ok(tmp_path):
    archive = _build(tmp_path)
    assert validate_release_archive(archive) == []


def test_validate_archive_detects_tamper(tmp_path):
    archive = _build(tmp_path)
    archive.write_bytes(archive.read_bytes() + b"x")
    problems = validate_release_archive(archive)
    assert any("hash mismatch" in p for p in problems)


def test_validate_archive_missing_sidecar(tmp_path):
    archive = _build(tmp_path)
    archive.with_name(archive.name + ".sha256").unlink()
    problems = validate_release_archive(archive)
    assert any("sidecar missing" in p for p in problems)


def test_validate_archive_missing_file(tmp_path):
    problems = validate_release_archive(tmp_path / "nope.zip")
    assert problems and "not found" in problems[0]


def test_cli_validate_positional_dir_and_zip(tmp_path, capsys):
    archive = _build(tmp_path)
    capsys.readouterr()
    assert main(["validate", str(tmp_path / "pkg")]) == 0
    assert "OK" in capsys.readouterr().out
    assert main(["validate", str(archive)]) == 0
    assert "OK" in capsys.readouterr().out
    # legacy flag still works
    assert main(["validate", "--dir", str(tmp_path / "pkg")]) == 0
