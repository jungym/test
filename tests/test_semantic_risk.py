"""Tests for Review Gate 5 Item 7 — advisory semantic claim-risk layer."""

from haen.governance import check_text, semantic_risk_scan
from haen.report_builder import build_dossier
from haen.sample_data import build_sample_fleet

FIXED_TS = "2026-01-01T00:00:00+00:00"


def test_flags_risky_paraphrase_the_lexical_gate_misses():
    text = "Vehicle performance is guaranteed across the range."
    # lexical hard gate does not catch this paraphrase...
    assert check_text(text) == []
    # ...but the advisory semantic layer flags it.
    findings = semantic_risk_scan(text)
    assert findings
    assert findings[0].severity == "advisory"


def test_negation_is_not_flagged():
    assert semantic_risk_scan("performance is not guaranteed") == []
    assert semantic_risk_scan("this is not a validated digital twin") == []


def test_korean_risk_flagged_and_negation_safe():
    assert semantic_risk_scan("성능 보장")          # guaranteed
    assert semantic_risk_scan("성능 보장 안 됨") == []  # negated


def test_hard_gate_remains_authoritative():
    # A real forbidden claim is still caught by the hard lexical gate,
    # independent of the advisory layer.
    hard = "This vehicle is road legal."
    assert check_text(hard)  # hard gate fires
    # advisory layer may also flag it, but never replaces the hard gate
    assert isinstance(semantic_risk_scan(hard), list)


def test_advisory_is_warning_only():
    # semantic_risk_scan returns findings but never raises.
    findings = semantic_risk_scan("certified and finalized")
    assert isinstance(findings, list) and findings


def test_clean_internal_dossier_has_no_semantic_flags():
    text = build_dossier(programme="HAEN GT-1", branch="GT-1",
                         vehicles=build_sample_fleet(), generated_at=FIXED_TS)
    assert check_text(text) == []          # hard gate clean
    assert semantic_risk_scan(text) == []  # advisory layer also clean
