# 00_governance

**Implemented in:** [`haen/governance.py`](../haen/governance.py)

Guardrails for the whole system.

- **Forbidden claim checker** — `check_text`, `is_clean`, `assert_clean`. Scans any
  generated text against the rules in [`haen/data/forbidden_claims.yaml`](../haen/data/forbidden_claims.yaml)
  and reports the rule, matched text and location. The report builder and RFI
  builder call this as a hard gate before emitting any document.
- **Assumption ledger** — `AssumptionLedger` (SQLite-backed). Records every
  engineering assumption with its value, source, confidence and status so humans
  can review the basis of any result. `open_low_confidence()` feeds the RFI builder.

Forbidden claims enforced: road legal, homologation ready, crash safe,
production feasible, supplier confirmed, design complete.
