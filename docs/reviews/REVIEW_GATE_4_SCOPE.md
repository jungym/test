# Review Gate 4 — Proposed Scope (PROPOSAL ONLY — not implemented)

**Status: IMPLEMENTED.** Originally a proposal; the items below are now
implemented on `haen-standalone-extraction`.

> **Implementation status:**
> - Item 1 baseline verify — done.
> - Item 2 dossier artifact export — done (`haen/export.py`, `tests/test_export.py`).
> - Item 3 embedded packaging artifacts (dependency-free SVG) — done
>   (`visualization.diagram_to_svg`, `export.export_packaging_svgs`,
>   `tests/test_packaging_artifacts.py`).
> - Item 4 mass/energy metadata reporting — done (`tests/test_metadata_reporting.py`).
> - Item 5 dashboard energy charts — done (`visualization.energy_scenario_chart`).
> - Item 6 metadata-completeness RFI prompts — done (`tests/test_metadata_rfi.py`).
> - Item 7 release package + manifest + validation + reproducibility — done
>   (`export.export_release_package`/`validate_release`, `haen export`/`validate`
>   CLI, `tests/test_release_package.py`).
> - Item 8 consolidation — this update.
>
> Exports are internal-only, human-review-required, governance-gated, and
> deterministic under a fixed `generated_at`. No CAD/CFD/crash/thermal/FEA/
> certification/production/supplier-confirmation/road-legality work.

HAEN Hypercar Design Support AI is a human-reviewed AI-assisted concept
engineering support system, not an autonomous vehicle design or certification
system. Gate 4 stays inside that boundary: it concerns packaging and
*distribution* of the existing internal outputs (exports, artifacts, surfacing),
not any new engineering analysis or validation.

## Baseline at proposal time

- Gate 1 closed; Gate 2 intact; Gate 3 closed (`docs/reviews/GATE_3_CLOSURE.md`).
- Final Gate 3 commit `b7fd629`; CI run #8 green (Python 3.11 + 3.12).
- 199 passed / 1 skipped. SafeCopy base untouched. No PR opened.

## Objective

Make the existing internal dossier and screening outputs easier to package,
review and reproduce — exported artifacts, embedded packaging images, richer
metadata surfacing, dashboard charts, completeness-driven RFI prompts, and a
defined internal-only release-package structure — all behind the existing
governance gate and internal/human-review-required defaults.

## Candidate items

| # | Item | Summary | Module(s) | Risk |
|---|------|---------|-----------|------|
| 1 | **Exported dossier artifact generation** | Write the dossier to a stable, internal artifact (e.g. Markdown + sidecar metadata) with a governance scan before write. | `report_builder` | Low |
| 2 | **Embedded packaging images in exports** | Render top/side packaging diagrams to image files and embed/reference them in the exported dossier. | `visualization`, `report_builder` | Medium |
| 3 | **Richer mass/energy table surfacing** | Surface per-line metadata (label/source_type/confidence/notes) in the dossier mass & energy tables, not just the breakdown helper. | `report_builder`, `mass_energy` | Low |
| 4 | **Dashboard energy-scenario charts** | Chart the energy-scenario comparison on the dashboard (existing Plotly pattern; no rewrite). | `webapp`, `visualization` | Low/Optional |
| 5 | **Metadata-completeness-driven RFI prompts** | Turn incomplete mass/energy line-item metadata into RFI items ("provide source/confidence for X"). | `rfi_builder`, `mass_energy` | Low |
| 6 | **Report export validation** | Validate an exported artifact: governance-clean, required sections present, metadata markers present, internal-only. | `report_builder` | Low |
| 7 | **Artifact reproducibility checks** | Deterministic export given fixed inputs (stable ordering; exclude/normalize timestamps) verified by hashing/equality. | `report_builder`, `tests` | Medium |
| 8 | **Internal-only release-package structure** | Define a folder layout for an internal review package (dossier + images + metadata + RFI), clearly marked internal-only. | `report_builder` | Low |

### Notes on key items
- **Item 2 / Item 7:** image rendering and timestamps are the main reproducibility
  hazards. Proposed rule — exports take an injectable clock (or omit/normalize the
  timestamp in the reproducibility check), and image generation is deterministic
  or content-hashed where feasible. Renderer tests stay `importorskip`-guarded.
- **Item 5:** completeness gaps become RFI items only; they never fabricate data.
- **Item 8:** the package is **internal-only**; no external/release-approval flag
  is set by default (carries `human_review_required: true`,
  `external_release_allowed: false`).

## Required data governance (carried forward)
Every numeric/technical output keeps value, unit, label, source_type, confidence,
assumption_notes. Exports run the forbidden-claim scan before write and remain
internal and human-review-required by default.

## Required tests (proposed)
- Export writes a governance-clean artifact; refuses to write on a forbidden claim.
- Embedded-image references resolve (or are gracefully omitted when deps absent).
- Mass/energy dossier tables include the metadata columns.
- Completeness-driven RFI items are generated only for incomplete line items.
- Export validation passes for a good artifact and fails for a tampered one.
- Reproducibility: two exports of fixed inputs are byte-equal after timestamp
  normalization.
- Regression: Gate 1, Gate 2, Gate 3 outputs remain green.

## Hard prohibitions (Gate 4 must NOT do or claim)
- production CAD; real engineering validation
- CFD validation; crash validation; thermal validation; structural FEA certification
- certification claims; road-legality claims; homologation-readiness claims
- production-feasibility claims; supplier-confirmation claims; design-completion claims
- investor-ready / external marketing claims; external release approval by default
- PR creation without explicit instruction
- broad architecture rewrite; large new dependencies
- touching the SafeCopy base or archival PR #1; amending/force-pushing history

## Proposed sequencing
1. Item 3 (table surfacing) — small, builds on Gate 3.
2. Item 1 (export) → Item 6 (export validation) → Item 7 (reproducibility).
3. Item 2 (embedded images) once export exists.
4. Item 5 (completeness RFI prompts).
5. Item 8 (release-package structure).
6. Item 4 (dashboard charts) optional, last.
7. Tests alongside each item.

## Acceptance criteria (proposed)
- Exports are governance-clean, internal-only, human-review-required, and
  deterministic under fixed inputs (timestamp normalized).
- New surfacing/RFI behaviour is covered by deterministic tests.
- Full suite green on Python 3.11 and 3.12; Gate 1–3 regression intact.

## Decision needed
Approve as-is, trim/reorder, or adjust the reproducibility/timestamp rule. No
work starts until approved.
