"""Tests for 00_governance: forbidden claim checker and assumption ledger."""

import pytest

from haen.governance import (
    Assumption,
    AssumptionLedger,
    AssumptionStatus,
    Confidence,
    ForbiddenClaimError,
    assert_clean,
    check_text,
    is_clean,
)


@pytest.mark.parametrize(
    "text",
    [
        "This vehicle is road legal.",
        "The design is street-legal in the EU.",
        "Now homologation ready for racing.",
        "Independent testing shows it is crash safe.",
        "The concept is production feasible at scale.",
        "These numbers are supplier confirmed.",
        "The design is complete and finalized.",
    ],
)
def test_forbidden_claims_detected(text):
    findings = check_text(text)
    assert findings, f"expected a forbidden claim in: {text!r}"
    assert not is_clean(text)


def test_clean_text_passes():
    text = (
        "Road-legality not assessed. Homologation status: not assessed. "
        "Crashworthiness not evaluated. Design exploration in progress."
    )
    assert is_clean(text)
    assert check_text(text) == []
    assert_clean(text)  # must not raise


def test_assert_clean_raises_with_findings():
    with pytest.raises(ForbiddenClaimError) as exc:
        assert_clean("totally road legal and crash safe")
    assert len(exc.value.findings) >= 2


def test_finding_has_location():
    text = "line one is fine\nthis line is road legal though"
    findings = check_text(text)
    assert findings[0].line == 2
    assert findings[0].column > 0


def test_ledger_roundtrip():
    ledger = AssumptionLedger(":memory:")
    a = Assumption(
        key="x.y",
        statement="some assumption",
        value="42",
        unit="kg",
        confidence=Confidence.HIGH,
        status=AssumptionStatus.SUBSTANTIATED,
        branch="GT-1",
    )
    ledger.add(a)
    got = ledger.get("x.y")
    assert got is not None
    assert got.value == "42"
    assert got.confidence == Confidence.HIGH
    assert got.status == AssumptionStatus.SUBSTANTIATED


def test_ledger_upsert():
    ledger = AssumptionLedger(":memory:")
    ledger.add(Assumption(key="k", statement="s", value="1"))
    ledger.add(Assumption(key="k", statement="s", value="2"))
    assert ledger.get("k").value == "2"
    assert len(ledger.all()) == 1


def test_open_low_confidence_filter():
    ledger = AssumptionLedger(":memory:")
    ledger.add(Assumption(key="a", statement="s", value="1",
                          confidence=Confidence.LOW, status=AssumptionStatus.OPEN))
    ledger.add(Assumption(key="b", statement="s", value="1",
                          confidence=Confidence.HIGH, status=AssumptionStatus.OPEN))
    ledger.add(Assumption(key="c", statement="s", value="1",
                          confidence=Confidence.LOW, status=AssumptionStatus.SUBSTANTIATED))
    keys = {a.key for a in ledger.open_low_confidence()}
    assert keys == {"a"}


def test_branch_filter_includes_all():
    ledger = AssumptionLedger(":memory:")
    ledger.add(Assumption(key="g", statement="s", value="1", branch="GT-1"))
    ledger.add(Assumption(key="x", statement="s", value="1", branch="all"))
    ledger.add(Assumption(key="h", statement="s", value="1", branch="GT-1H"))
    keys = {a.key for a in ledger.all(branch="GT-1")}
    assert keys == {"g", "x"}
