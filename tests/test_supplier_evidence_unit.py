"""Gate 7 B1 — dedicated unit tests for supplier_evidence."""

from datetime import date

import pytest
from pydantic import ValidationError

from haen.supplier_evidence import (
    EngagementStatus,
    EvidenceRecord,
    EvidenceType,
    Partner,
    SupplierEvidenceTable,
    VerificationState,
)


def _rec(rid, component="Battery pack", state=VerificationState.UNVERIFIED):
    return EvidenceRecord(
        id=rid, component=component, supplier="X", claim="c",
        evidence_type=EvidenceType.ESTIMATE, verification=state,
        received_date=date(2026, 1, 1),
    )


def test_table_add_get_and_for_component():
    t = SupplierEvidenceTable([_rec("E1"), _rec("E2", component="Brakes")])
    assert t.get("E1").id == "E1"
    assert {r.id for r in t.for_component("Battery pack")} == {"E1"}


def test_unverified_and_components_without_evidence():
    t = SupplierEvidenceTable([
        _rec("E1", state=VerificationState.VERIFIED),
        _rec("E2", state=VerificationState.IN_REVIEW),
    ])
    assert {r.id for r in t.unverified()} == {"E2"}  # in_review counts as unverified
    missing = t.components_without_evidence(["Battery pack", "Brakes", "Cooling"])
    assert "Brakes" in missing and "Cooling" in missing and "Battery pack" not in missing


def test_coverage_summary_and_dataframe():
    t = SupplierEvidenceTable([_rec("E1"), _rec("E2", state=VerificationState.VERIFIED)])
    s = t.coverage_summary()
    assert s["total"] == 2 and s["verified"] == 1 and s["unverified"] == 1
    df = t.to_dataframe()
    assert len(df) == 2 and "supplier" in df.columns


def test_empty_table_dataframe_has_columns():
    df = SupplierEvidenceTable([]).to_dataframe()
    assert "verification" in df.columns and len(df) == 0


def test_engagement_status_values():
    assert {s.value for s in EngagementStatus} == {
        "rfi_candidate", "watch_branch", "technology_observation", "none"
    }


def test_partner_validation():
    Partner(name="Hylium", engagement_status=EngagementStatus.RFI_CANDIDATE, rfi_level=1)
    with pytest.raises(ValidationError):
        Partner(name="X", engagement_status=EngagementStatus.RFI_CANDIDATE, rfi_level=0)
    with pytest.raises(ValidationError):
        Partner(name="X", engagement_status="bogus")
