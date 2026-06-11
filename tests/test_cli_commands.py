"""Gate 7 B1 — CLI end-to-end smoke tests for the read/print commands."""

from haen.cli import main
from haen.governance import check_text


def test_compare(capsys):
    assert main(["compare"]) == 0
    out = capsys.readouterr().out
    assert "Trade-off ranking" in out
    assert "GT-1-c01" in out


def test_simulate(capsys):
    assert main(["simulate"]) == 0
    out = capsys.readouterr().out
    assert "kph" in out and "not real-world predictions" in out


def test_screen(capsys):
    assert main(["screen"]) == 0
    out = capsys.readouterr().out
    assert "brake_decel" in out and "not vehicle-dynamics validation" in out


def test_readiness(capsys):
    assert main(["readiness"]) == 0
    out = capsys.readouterr().out
    assert "Internal Release-Readiness Checklist" in out
    assert "external_release_allowed: **false**" in out
    assert check_text(out) == []


def test_check_clean(tmp_path, capsys):
    f = tmp_path / "clean.md"
    f.write_text("Road-legality not assessed. Design exploration in progress.\n", encoding="utf-8")
    assert main(["check", str(f)]) == 0
    assert "no forbidden claims" in capsys.readouterr().out


def test_check_dirty(tmp_path, capsys):
    f = tmp_path / "dirty.md"
    f.write_text("This car is road legal and crash safe.\n", encoding="utf-8")
    assert main(["check", str(f)]) == 1
    assert "FOUND" in capsys.readouterr().out


def test_dossier_stdout(capsys):
    assert main(["dossier", "--branch", "GT-1"]) == 0
    out = capsys.readouterr().out
    assert "Entry Validation Dossier" in out
    assert check_text(out) == []
