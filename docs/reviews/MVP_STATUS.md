# HAEN Hypercar Design Support AI — MVP Status

HAEN Hypercar Design Support AI is a human-reviewed AI-assisted concept
engineering support system, not an autonomous vehicle design or certification
system. All outputs are internal unless explicitly reviewed and approved; it does
not certify vehicles, complete production design, or confirm road-legality,
crashworthiness, production feasibility, supplier availability, homologation
readiness, or real-world performance.

Branch: `haen-standalone-extraction`.

## Module status

| Area | Module | Status |
|------|--------|--------|
| Governance & claim control | `governance.py` | forbidden-claim checker (EN+KO), assumption ledger, `DataLabel`, `ReportMetadata` (internal/human-review default) |
| Vehicle definition core | `vehicle_definition.py` | branch + vehicle schemas, `GateStatus`, `ChassisGeometry` |
| Design space / packaging | `design_space_explorer.py`, `packaging.py` | branch comparison, AABB overlap + envelope detection |
| Mass & energy | `mass_energy.py` | comparison tables, deltas, source/confidence-labelled assumptions |
| Low-fidelity dynamics | `low_fidelity_simulation.py` | longitudinal sim + braking, load-transfer, CG-sensitivity screening |
| Supplier evidence & RFI | `supplier_evidence.py`, `rfi_builder.py` | evidence register, `EngagementStatus`/`Partner`, RFI generator |
| Report builder | `report_builder.py` | entry-validation dossier with governance gate + metadata |
| Dashboard / CLI | `webapp/app.py`, `cli.py` | Streamlit pages + `haen` CLI (`compare/simulate/screen/rfi/dossier/check`) |

## Branch structure

- **GT-1 BEV** — baseline, first digital package, `gate_status: in_progress`.
- **GT-1H 700bar H2** — hydrogen halo, screening only, `gate_status: rfi_candidate`.
- **GT-1H LH2** — liquid-hydrogen watch branch, `gate_status: watch_branch`.
  Hylium = Level 1 RFI candidate; Cryos/DALIM/Parity = watch branch; KIMM =
  technology observation. None are confirmed or selected suppliers.

## Data governance

Every screening output carries `source_type`, `confidence`, and a `DataLabel`
(`low_fidelity_screening` for dynamics outputs). Reports default to
`human_review_required: true`, `external_release_allowed: false`, internal-only.

## Gates

- Gate 1: CLOSED (`docs/reviews/GATE_1_CLOSURE.md`).
- Gate 2 (Items 1–6): implemented (`docs/reviews/REVIEW_GATE_2_SCOPE.md`).

## Validation

`python -m compileall -q haen tests` and `python -m pytest` — see the final
status report for the current count.

## Explicit non-goals / parked

- High-fidelity CFD, crash/thermal/FEA, production CAD, full vehicle dynamics,
  tyre/ABS/aero/regen models — out of scope (later gates, if ever).
- External release, supplier outreach automation, contract/NDA workflow — out of
  scope.
