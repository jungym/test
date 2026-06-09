# Review Gate 2 — Proposed Scope (PROPOSAL ONLY — not implemented)

**Status: DRAFT PROPOSAL.** Nothing in this document has been implemented. It
exists to scope the next gate for approval. Implementation begins only on
explicit instruction.

## Objective

Extend the design-support model with a small set of additional screening outputs
and a structured gate-status field, keeping the same hard rules: low-fidelity
screening only, human-reviewed, no certification, production, road-legality,
supplier-confirmation, or real-world-prediction claims.

> **Progress (all Gate 2 items implemented):**
> - Item 1 — gate-status field: `GateStatus` + `Branch.gate_status`
>   (`tests/test_gate_status.py`). **Done.**
> - Item 2 — braking screening: `screen_braking()`/`BrakingScreening` +
>   `DataLabel` (`tests/test_braking_screening.py`). **Done.**
> - Item 3 — load-transfer screening: `ChassisGeometry` +
>   `screen_load_transfer()` (`tests/test_load_transfer.py`). **Done.**
> - Item 4 — CG-sensitivity sweep: `screen_cg_sensitivity()`
>   (`tests/test_cg_sensitivity.py`). **Done.**
> - Item 5 — report/gate integration: `ReportMetadata`, dossier dynamics-screening
>   section, per-branch gate-status table, CLI `screen`, dashboard page
>   (`tests/test_report_integration.py`). **Done.**
> - Item 6 — tests for all of the above. **Done.**
>
> All screening outputs are idealized rigid-body models (no drag/ABS/tyre/
> suspension/aero/regen) and labelled `low_fidelity_screening`.

## Candidate items

| # | Item | Summary | Module(s) | Risk |
|---|------|---------|-----------|------|
| 1 | **S-1 per-branch gate-status field** | Add an explicit, enumerated gate/phase status per branch (e.g. `concept / screening / gate-1-passed / on-hold / watch`) instead of inferring it from `branch_status`. | `vehicle_definition`, `data/branches.yaml` | Low |
| 2 | **Braking screening output** | First-order stopping-distance / decel estimate from a friction-limit assumption. Screening only. | `low_fidelity_simulation` | Medium |
| 3 | **Load-transfer screening output** | Static longitudinal/lateral load transfer from mass, wheelbase, track, CG height under an assumed g. | `low_fidelity_simulation`, `vehicle_definition` (needs CG height, track) | Medium |
| 4 | **CG-sensitivity screening output** | Sweep CG height/position and report sensitivity of load transfer / balance metrics. | `low_fidelity_simulation` | Medium |
| 5 | **Report / gate output integration** | Surface items 1–4 in the dossier and CLI/dashboard, each behind the existing low-fidelity disclaimers and governance gate. | `report_builder`, `cli`, `webapp`, template | Low |
| 6 | **Tests for all added fields/outputs** | Schema-validation tests for new fields; numeric sanity + monotonicity tests for new screening outputs; governance-clean assertions for new report text. | `tests/` | Low |

## Required schema additions (for items 2–4)

These inputs do not exist yet and would be added as **assumptions** (clearly
labelled, with sane defaults) to `VehicleDefinition`:

- `cg_height_mm` (CG height above ground)
- `cg_longitudinal_bias` (front/rear weight split, e.g. 0.45 = 45% front)
- `track_width_mm` (for lateral load transfer)
- `tyre_friction_coefficient` (assumption for braking/load-transfer)

## Guardrails that MUST carry into every Gate 2 output

- Every new output labelled a **low-fidelity screening estimate**, not a
  prediction; braking/load-transfer/CG outputs explicitly **not** a substitute
  for vehicle-dynamics simulation or testing.
- All new report text passes the forbidden-claim checker (governance gate).
- No new forbidden territory: no CFD, no crash/thermal/high-fidelity dynamics, no
  certification, production, road-legality, or supplier-confirmation claims.
- Existing behaviour and all existing tests must remain green.

## Proposed sequencing

1. Item 1 (gate-status field) — smallest, unblocks gate reporting.
2. Items 2 → 3 → 4 (screening outputs) — each with its tests, in order.
3. Item 5 (integration) once 2–4 land.
4. Item 6 runs alongside each item, not at the end.

## Acceptance criteria (proposed)

- New fields validate and round-trip; defaults documented as assumptions.
- New screening outputs produce physically-ordered results on the sample fleet
  (e.g. heavier vehicle → longer stopping distance under equal friction).
- Dossier/CLI/dashboard show the new outputs with disclaimers; dossier stays
  governance-clean.
- Test count increases; full suite green on Python 3.11 and 3.12.

## Out of scope for Gate 2

High-fidelity CFD, crash simulation, thermal simulation, real-world performance
claims, certification, production, road-legality and supplier-confirmation
claims, autonomy.

## Decision needed

Approve scope as-is, trim/reorder items, or adjust assumptions/defaults. No work
starts until approved.
