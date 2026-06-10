# Review Gate 6 — Proposed Scope (PROPOSAL ONLY — not implemented)

**`GATE_6_EXECUTION_ADDENDUM.md` takes precedence for the execution-clarification
points it covers.**

**Status: DRAFT PROPOSAL.** Nothing here is implemented. It scopes the next safe
expansion for approval; implementation begins only on explicit instruction.

HAEN Hypercar Design Support AI is a human-reviewed AI-assisted concept
engineering support system, not an autonomous vehicle design, certification,
production CAD, or external-release system. Gate 6 finishes the **internal
release candidate**: end-to-end packaging, reproducibility, and operator
workflow — no new engineering analysis or validation.

## Baseline at proposal time

- Gate 1 closed; Gate 2 intact; Gate 3 closed; Gate 4 closed; Gate 5 closed
  (`docs/reviews/GATE_5_CLOSURE.md`).
- Final Gate 5 commit `19e48ff`; CI run #12 green (Python 3.11 + 3.12).
- 280 passed / 1 skipped. SafeCopy base untouched. No PR opened.

## Objective

Assemble the internal release candidate: a small set of CLI commands that
produce one complete, internal-only, reproducible, validated review package —
with semantic-risk findings surfaced, a deterministic reproducibility mode, and
an end-to-end acceptance test.

## Candidate items

| # | Item | Summary | Module(s) | Risk |
|---|------|---------|-----------|------|
| 1 | **Semantic-risk surfacing in outputs** | Include advisory `semantic_risk_scan` findings (read-only) in the dossier and readiness checklist, clearly labelled advisory. | `report_builder` | Low |
| 2 | **Deterministic raster renderer evaluation** | Evaluate whether a deterministic PNG is achievable (e.g. fixed matplotlib metadata); if not, keep PNG as non-hashed convenience and document the decision. | `visualization` | Medium |
| 3 | **Explicit reproducibility mode** | A documented "reproducible" path: fixed `generated_at`, stable ordering, SVG-only hashing; helper/flag to produce byte-stable packages. | `export`, `cli` | Low |
| 4 | **Final internal release-candidate command** | One CLI command that builds dossier + artifacts + manifest + validation report + readiness in a single internal package directory. | `cli`, `export` | Low |
| 5 | **End-to-end release acceptance test** | A test that runs the full pipeline and asserts every required package element is present, internal-only, governance-clean, and validates. | `tests/` | Low |
| 6 | **Korean governance documentation expansion** | Expand internal docs describing Korean claim coverage and safe framings (claim-clean). | docs | Low |
| 7 | **Archive validation UX** | `validate` accepts a zip archive (extract to temp, validate) in addition to a directory; clear messages. | `export`, `cli` | Low |
| 8 | **Release-readiness report consolidation** | Fold validation status, semantic-risk count, completeness, and gate status into one readiness output usable as the package summary. | `report_builder` | Low |

### Notes on key items
- **Item 1:** semantic findings are surfaced read-only and labelled advisory;
  they never gate output and never weaken the hard lexical check.
- **Item 2/3:** if deterministic raster is not low-risk, PNG stays a non-hashed
  convenience artifact and SVG remains the reproducible baseline (documented).
- **Item 4:** the release-candidate command sets internal-only,
  `human_review_required: true`, `external_release_allowed: false`; it performs
  no external action (no PR, no network, no supplier contact).

## Required data governance (carried forward)
Every numeric/technical output keeps value, unit, label, source_type, confidence,
assumption_notes. Hard forbidden-claim scan runs before any artifact write;
exports remain internal and human-review-required by default; the semantic layer
stays advisory.

## Required tests (proposed)
- Dossier/readiness include an advisory semantic-risk section (or "none").
- Reproducible mode produces byte-stable SVG/manifest across two runs.
- The release-candidate command produces every required package element.
- End-to-end acceptance: package validates, is internal-only, governance-clean.
- `validate` works on both a directory and a zip archive.
- Regression: Gate 1–5 outputs remain green.

## Hard prohibitions (Gate 6 must NOT do or claim)
- production CAD; real engineering validation
- CFD validation; crash validation; thermal validation; structural FEA certification
- certification claims; road-legality claims; homologation-readiness claims
- production-feasibility claims; supplier-confirmation claims; design-completion claims
- investor-ready / external marketing claims; external release approval
- PR creation without explicit instruction
- broad architecture rewrite; large new dependencies
- touching the SafeCopy base or archival PR #1; amending/force-pushing history
- weakening the hard forbidden-claim checker

## Proposed sequencing
1. Item 1 (semantic surfacing) and Item 8 (readiness consolidation).
2. Item 3 (reproducibility mode) → Item 4 (release-candidate command).
3. Item 7 (archive validation) → Item 5 (end-to-end acceptance test).
4. Item 2 (renderer evaluation) — dependency-sensitive.
5. Item 6 (Korean governance docs).
6. Tests alongside each item.

## Acceptance criteria (proposed)
- One command yields a complete, internal-only, validated, reproducible package.
- Semantic findings are advisory and visible; hard gate remains authoritative.
- Full suite green on Python 3.11 and 3.12; Gate 1–5 regression intact.

## Decision needed
Approve as-is, trim/reorder, or adjust the reproducibility and renderer
decisions. No work starts until approved.
