# 01_vehicle_definition

**Implemented in:** [`haen/vehicle_definition.py`](../haen/vehicle_definition.py)

Canonical, validated data model (Pydantic v2).

- `VehicleDefinition`, `Dimensions`, `EnergyStorage`, `Powerplant`,
  `PerformanceTargets`, `MassItem` — schemas with physical-sanity validation
  (positive masses, plausible ranges, wheelbase < length, capped performance).
- `Branch` and `load_branches()` — load and validate the three core architecture
  branches from [`haen/data/branches.yaml`](../haen/data/branches.yaml).
- `GateStatus` + `Branch.gate_status` (S-1) — enumerated, structured per-branch
  lifecycle/review-gate status (`not_started`, `in_progress`, `blocked`,
  `watch_branch`, `rfi_candidate`, `review_required`, `gated`, `passed`,
  `closed`, `superseded`). Defaults to `not_started` when absent. This is
  **governance metadata only** — it records review-gate state and carries no
  engineering-validation meaning (no road-legality, certification, etc.).
- `vehicle_from_branch(...)` — seed a concept from a branch's powertrain/energy.

Derived properties: `curb_mass_kg`, `mass_by_group`, `power_to_weight_kw_per_t()`.
