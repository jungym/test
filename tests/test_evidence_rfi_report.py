"""Tests for 07_supplier_evidence, 08_rfi_builder, 09_report_builder."""

from haen.governance import check_text
from haen.report_builder import build_dossier, save_dossier
from haen.rfi_builder import build_rfi
from haen.sample_data import (
    build_sample_evidence,
    build_sample_fleet,
    build_sample_ledger,
)
from haen.supplier_evidence import VerificationState


def test_evidence_table_basic():
    ev = build_sample_evidence()
    df = ev.to_dataframe()
    assert len(df) == 3
    assert "supplier" in df.columns


def test_nothing_is_confirmed():
    ev = build_sample_evidence()
    for r in ev.all():
        assert r.verification != VerificationState.VERIFIED


def test_components_without_evidence():
    ev = build_sample_evidence()
    missing = ev.components_without_evidence(
        ["Battery pack", "Brakes", "700 bar H2 tanks"]
    )
    assert "Brakes" in missing
    assert "Battery pack" not in missing


def test_coverage_summary_counts():
    ev = build_sample_evidence()
    summary = ev.coverage_summary()
    assert summary["total"] == 3
    assert summary["unverified"] >= 1


def test_rfi_includes_open_assumptions_and_gaps():
    rfi = build_rfi(
        title="t",
        branch="all",
        ledger=build_sample_ledger(),
        evidence=build_sample_evidence(),
        expected_components=["Battery pack", "Brakes"],
    )
    refs = [i.ref for i in rfi.items]
    # at least one assumption item, one evidence item, one missing-component item
    assert any(r.startswith("A-") for r in refs)
    assert any(r.startswith("E-") for r in refs)
    assert any(r.startswith("C-") for r in refs)


def test_rfi_markdown_is_clean():
    rfi = build_rfi(title="t", branch="all", ledger=build_sample_ledger(),
                    evidence=build_sample_evidence())
    md = rfi.to_markdown()
    assert check_text(md) == []
    assert "Request for Information" in md


def test_dossier_builds_and_is_clean():
    fleet = build_sample_fleet()
    ledger = build_sample_ledger()
    evidence = build_sample_evidence()
    rfi = build_rfi(title="t", branch="GT-1", ledger=ledger, evidence=evidence)
    text = build_dossier(
        programme="HAEN GT-1",
        branch="GT-1",
        vehicles=fleet,
        evidence=evidence,
        ledger=ledger,
        rfi=rfi,
    )
    assert check_text(text) == []
    assert "Entry Validation Dossier" in text
    assert "not assessed" in text


def test_save_dossier_writes_file(tmp_path):
    fleet = build_sample_fleet()
    text = build_dossier(programme="P", branch="GT-1", vehicles=fleet)
    out = save_dossier(text, tmp_path / "dossier.md")
    assert out.exists()
    assert out.read_text(encoding="utf-8").startswith("# Entry Validation Dossier")
