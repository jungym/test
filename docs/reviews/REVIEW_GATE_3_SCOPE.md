# Review Gate 3 — Proposed Scope (PROPOSAL ONLY — not implemented)

**Status: IMPLEMENTED.** This document originally scoped Gate 3 as a proposal;
the items below have since been implemented on `haen-standalone-extraction`.

> **Implementation status:**
> - Item 1 (verify baseline) — done.
> - Item 2 (per-line-item mass/energy metadata) — done: `LabeledItem`/`MassItem`/
>   `EnergyItem`, `mass_energy` metadata columns + `metadata_completeness`
>   (`tests/test_metadata_labels.py`).
> - Item 3 (energy-scenario comparison) — done: `energy_scenario_comparison()` /
>   `energy_scenario_line_items()` (`tests/test_energy_scenario.py`).
> - Item 4 (packaging visualization) — done: pure `packaging_diagram()` model +
>   Plotly top/side renderers (`tests/test_packaging_viz.py`).
> - Item 5 (packaging-to-report integration) — done: dossier packaging section
>   with conflict summary + diagram references (`tests/test_packaging_report.py`).
> - Item 6 (dashboard expansion) — done: energy-scenario, metadata completeness,
>   side-view packaging.
> - Item 7 (consolidation) — this update.
>
> All outputs remain internal, human-review-required, governance-gated, and
> labelled low-fidelity / metadata-only. No CAD/CFD/crash/thermal/FEA/
> certification/production/supplier-confirmation/road-legality work.

HAEN Hypercar Design Support AI is a human-reviewed AI-assisted concept
engineering support system, not an autonomous vehicle design or certification
system. Gate 3 stays inside that boundary: visualization, labelling and
comparison aids only — no engineering validation of any kind.

## Baseline at proposal time

- Gate 1 closed; Gate 2 Items 1–6 complete.
- Final MVP commit: `785d72e`; CI run #6 green on Python 3.11 and 3.12.
- 169 tests passing. SafeCopy base untouched. No PR opened.

## Objective

Make the existing internal outputs more reviewable: visualize packaging, label
mass/energy data line-by-line, broaden the energy-scenario comparison, and fold
packaging + conflicts into the internal dossier — all behind the existing
governance gate and `low_fidelity_screening` / governance-metadata labelling.

## Candidate items

| # | Item | Summary | Module(s) | Risk |
|---|------|---------|-----------|------|
| 1 | **Packaging visualization** | Top-view + side-view package diagrams, component-envelope overlay, conflict (clash) visualization. Internal-only images/figures. | `visualization`, `packaging` | Medium |
| 2 | **Per-line-item mass/energy labelling** | Every mass and energy line item carries value, unit, `label` (`DataLabel`), `source_type`, `confidence`, `assumption_notes`. | `vehicle_definition`/`mass_energy`, `governance` | Medium |
| 3 | **Energy-scenario expansion** | BEV / 700bar H2 / LH2 watch energy comparison table (comparison only). | `mass_energy`, `design_space_explorer` | Low |
| 4 | **Packaging-to-report integration** | Embed packaging diagrams (or references) + conflict summary in the internal dossier, behind `human_review_required` and the forbidden-claim scan. | `report_builder`, template | Medium |
| 5 | **Dashboard visualization expansion** | OPTIONAL — surface item 1/3 visuals on existing pages only; no broad rewrite, only if deps stay low-risk. | `webapp` | Low/Optional |
| 6 | **Tests** | Deterministic plot/report generation where possible; metadata-completeness; forbidden-claim; Gate 1 & Gate 2 regression. | `tests/` | Low |

### Item 1 — Packaging visualization (detail)
- Top-view (x–y) and side-view (x–z) bounding-box diagrams of `Component`s.
- Component-envelope overlay vs. the vehicle external envelope (approximate).
- Conflict visualization: highlight detected AABB overlaps from `detect_overlaps`.
- Output is **internal-only**; figures carry a low-fidelity, not-CAD caption.
- **No production CAD, no CAD engineering validation, no geometric certification.**

### Item 2 — Per-line-item mass/energy labelling (detail)
- Extend mass items (and energy entries) so each carries:
  `value`, `unit`, `label` (reuse `DataLabel`), `source_type`, `confidence`
  (reuse `Confidence`), `assumption_notes`.
- **Missing/invalid metadata behaviour must be specified**: proposed rule —
  missing `label`/`source_type`/`confidence` defaults deterministically to
  `unknown`/`""`/`low` and is surfaced as a data-completeness gap (candidate for
  an RFI), OR fails validation if a strict mode is requested. Negative/zero
  values and bad units fail per existing schema conventions.
- Backward-compatible defaults so existing `MassItem` usage keeps working.

### Item 3 — Energy-scenario expansion (detail)
- Comparison-only table across GT-1 BEV / GT-1H 700bar / GT-1H LH2 watch.
- **No performance validation or real-world claim**; LH2 remains watch-only.

### Item 4 — Packaging-to-report integration (detail)
- Add a packaging section to the dossier: diagram(s) or stable references +
  conflict summary table.
- Must include the `human_review_required` marker and pass `assert_clean`
  (forbidden-claim scan) before output; remain internal-only by default.

## Required data governance (carried from Gate 2)
Every numeric/technical output includes value, unit, `label`, `source_type`,
`confidence`, `assumption_notes`. Reports remain internal and
`human_review_required` by default; `external_release_allowed` defaults `False`.

## Required tests (proposed)
- Packaging plots generate deterministically (e.g. figure object shape / saved
  artifact hash where feasible) without requiring a display.
- Metadata-completeness: every mass/energy line item exposes the six fields;
  missing-metadata behaviour matches the specified rule.
- Energy-scenario comparison is deterministic across the three branches.
- Forbidden-claim scan: all new report text passes `check_text`.
- Regression: Gate 1 hardening + Gate 2 (gate-status, braking, load-transfer,
  CG-sensitivity, report integration, partners) outputs remain green.

## Hard prohibitions (Gate 3 must NOT do or claim)
- production CAD; real CAD engineering validation
- CFD validation; crash validation; thermal validation; structural FEA certification
- road-legality claims; homologation-readiness claims; production-feasibility claims
- supplier-confirmation claims; design-completion claims
- investor-ready / external marketing claims
- PR creation without explicit instruction
- broad dashboard rewrite; large new dependencies
- touching the SafeCopy base or archival PR #1; amending/force-pushing history

## Proposed sequencing
1. Item 2 (line-item labelling) — unblocks richer report tables.
2. Item 3 (energy-scenario table) — small, builds on labelling.
3. Item 1 (packaging visualization) — figure helpers + tests.
4. Item 4 (packaging-to-report integration) once 1 lands.
5. Item 5 (dashboard) optional, last.
6. Item 6 runs alongside each item.

## Acceptance criteria (proposed)
- New fields validate, round-trip, and default deterministically.
- Packaging figures generate headlessly and deterministically where feasible.
- Dossier remains governance-clean and internal/human-review-required.
- Test count increases; full suite green on Python 3.11 and 3.12.

## Decision needed
Approve as-is, trim/reorder, or adjust the missing-metadata rule and defaults.
No work starts until approved.
