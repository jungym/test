"""07_supplier_evidence — supplier evidence management.

Tracks evidence behind supplier-related figures (component claims, quotes,
datasheets, test reports). Crucially, the system NEVER treats supplier figures as
"confirmed"; every record carries a verification state that only a human can move
to ``verified``. Even then, the governance layer forbids the phrase
"supplier confirmed" in generated text.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

import pandas as pd
from pydantic import BaseModel, Field


class EvidenceType(str, Enum):
    DATASHEET = "datasheet"
    QUOTE = "quote"
    TEST_REPORT = "test_report"
    EMAIL = "email"
    VERBAL = "verbal"
    ESTIMATE = "estimate"  # internal estimate, not from a supplier


class VerificationState(str, Enum):
    UNVERIFIED = "unverified"     # received, not checked
    IN_REVIEW = "in_review"       # being checked by a human
    VERIFIED = "verified"         # human-verified evidence (still not a guarantee)
    DISPUTED = "disputed"         # contradicted by other evidence


class EvidenceRecord(BaseModel):
    """A single piece of supplier evidence."""

    id: str = Field(..., pattern=r"^[A-Za-z0-9._-]+$")
    component: str
    supplier: str
    claim: str = Field(..., description="The figure/claim the evidence supports, e.g. 'pack 180 Wh/kg'.")
    evidence_type: EvidenceType
    document_ref: str = ""          # URL, doc id, or filename
    received_date: date | None = None
    verification: VerificationState = VerificationState.UNVERIFIED
    reviewer: str = ""
    branch: str = "all"
    notes: str = ""


class SupplierEvidenceTable:
    """An in-memory collection of evidence records with a DataFrame view."""

    def __init__(self, records: list[EvidenceRecord] | None = None):
        self._records: dict[str, EvidenceRecord] = {}
        for r in records or []:
            self.add(r)

    def add(self, record: EvidenceRecord) -> None:
        self._records[record.id] = record

    def get(self, record_id: str) -> EvidenceRecord | None:
        return self._records.get(record_id)

    def all(self) -> list[EvidenceRecord]:
        return list(self._records.values())

    def for_component(self, component: str) -> list[EvidenceRecord]:
        return [r for r in self._records.values() if r.component == component]

    def unverified(self) -> list[EvidenceRecord]:
        return [
            r
            for r in self._records.values()
            if r.verification in (VerificationState.UNVERIFIED, VerificationState.IN_REVIEW)
        ]

    def components_without_evidence(self, components: list[str]) -> list[str]:
        """Return components that have no evidence record at all."""
        have = {r.component for r in self._records.values()}
        return [c for c in components if c not in have]

    def to_dataframe(self) -> pd.DataFrame:
        if not self._records:
            return pd.DataFrame(
                columns=[
                    "id", "component", "supplier", "claim", "evidence_type",
                    "document_ref", "received_date", "verification", "reviewer",
                    "branch", "notes",
                ]
            )
        rows = []
        for r in self._records.values():
            d = r.model_dump()
            d["evidence_type"] = r.evidence_type.value
            d["verification"] = r.verification.value
            d["received_date"] = r.received_date.isoformat() if r.received_date else ""
            rows.append(d)
        return pd.DataFrame(rows).set_index("id")

    def coverage_summary(self) -> dict[str, int]:
        """Counts by verification state."""
        out = {state.value: 0 for state in VerificationState}
        for r in self._records.values():
            out[r.verification.value] += 1
        out["total"] = len(self._records)
        return out
