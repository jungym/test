# 07_supplier_evidence

**Implemented in:** [`haen/supplier_evidence.py`](../haen/supplier_evidence.py)

Supplier evidence management.

- `EvidenceRecord` — component, supplier, claim, `EvidenceType`, document ref,
  `VerificationState` (unverified / in_review / verified / disputed), reviewer.
- `SupplierEvidenceTable` — collection with `to_dataframe()`, `unverified()`,
  `components_without_evidence()`, `coverage_summary()`.

Supplier figures are **never** treated as confirmed; verification is a human step,
and the governance layer forbids the phrase "supplier confirmed".
