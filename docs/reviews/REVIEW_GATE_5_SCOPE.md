# Review Gate 5 — Proposed Scope (PROPOSAL ONLY — not implemented)

**Status: IMPLEMENTED.** Originally a proposal; Items 1–10 are now implemented on
`haen-standalone-extraction`.

> **Implementation status:**
> - Item 1 baseline verify — done.
> - Item 2 optional PNG rendering (matplotlib Agg, graceful; SVG baseline) — done
>   (`test_png_rendering.py`).
> - Item 3 per-line metadata in `compare_with_metadata()` — done
>   (`test_compare_metadata.py`).
> - Item 4 completeness-gap RFI prompts in default CLI RFI — done
>   (`test_cli_rfi_completeness.py`).
> - Item 5 bundle-hash artifact integrity — done (`test_artifact_integrity.py`).
> - Item 6 stdlib zip release bundle + validation report — done
>   (`test_release_bundle.py`).
> - Item 7 advisory semantic claim-risk layer — done (`test_semantic_risk.py`).
> - Item 8 expanded Korean coverage — done (`test_korean_claims.py`).
> - Item 9 internal release-readiness checklist — done (`test_release_readiness.py`).
> - Item 10 consolidation — this update.
>
> All artifacts internal-only, human-review-required, governance-gated. Semantic
> layer is advisory and never weakens the hard lexical gate. No CAD/CFD/crash/
> thermal/FEA/certification/production/supplier-confirmation/road-legality work.

HAEN Hypercar Design Support AI is a human-reviewed AI-assisted concept
engineering support system, not an autonomous vehicle design or certification
system. Gate 5 concerns artifact *fidelity, integrity and release-readiness* of
the existing internal outputs — not any new engineering analysis or validation.

## Baseline at proposal time

- Gate 1 closed; Gate 2 intact; Gate 3 closed; Gate 4 closed
  (`docs/reviews/GATE_4_CLOSURE.md`).
- Final Gate 4 commit `9e96828`; CI run #10 green (Python 3.11 + 3.12).
- 226 passed / 1 skipped. SafeCopy base untouched. No PR opened.

## Objective

Strengthen the internal review package: optional rendered raster images,
richer in-table metadata, completeness-driven prompts by default, stronger
artifact integrity, bundling, deeper claim-risk review, broader Korean coverage,
and a final internal release-readiness checklist — all internal-only and behind
the existing governance gate.

## Candidate items

| # | Item | Summary | Module(s) | Risk |
|---|------|---------|-----------|------|
| 1 | **Rendered PNG image support** | Optional PNG packaging images in exports, in addition to the dependency-free SVG. | `export`, `visualization` | Medium |
| 2 | **Approved headless renderer evaluation** | Evaluate a headless renderer (e.g. matplotlib Agg) for PNGs; degrade gracefully when absent; keep SVG as the default. | `visualization` | Medium |
| 3 | **Per-line metadata in `compare()`** | Surface label/source_type/confidence per metric in the main mass/energy comparison table (long-form option). | `mass_energy`, `report_builder` | Low |
| 4 | **Completeness-gap RFI in default CLI** | Wire metadata-completeness RFI prompts into the default `haen rfi` output. | `cli`, `rfi_builder` | Low |
| 5 | **Signed manifests / stronger integrity** | Add a stronger integrity mechanism (e.g. manifest signature/HMAC with an internal key, or a hash-tree) over the release package. | `export` | Medium |
| 6 | **Package archiving / release bundle** | Bundle the internal package into a single archive (e.g. zip) with the manifest, deterministically where feasible. | `export` | Low |
| 7 | **Semantic claim-risk review** | Add a heuristic, explainable risk layer above the lexical checker (e.g. negation-aware / proximity rules) that flags *candidates* for human review — never auto-approves. | `governance` | Medium |
| 8 | **Korean forbidden-claim coverage expansion** | Broaden Korean (한국어) patterns and add Korean false-positive guards / tests. | `governance`, `data/forbidden_claims.yaml` | Low |
| 9 | **Internal release-readiness checklist** | A structured, human-filled checklist artifact (internal-only) summarizing gate status, metadata completeness, open RFIs, and required sign-offs. | `report_builder`/docs | Low |

### Notes on key items
- **Items 1–2:** PNG rendering needs a headless backend; it must degrade to SVG
  when the dependency is absent, and PNG bytes may be non-deterministic — so
  reproducibility checks should hash the SVG (deterministic) and treat PNG as an
  optional convenience artifact.
- **Item 5:** any signing uses an internal key for *integrity*, not external
  attestation; it confers no certification or release approval.
- **Item 7:** the semantic layer is advisory — it raises review candidates and
  never relaxes the existing hard lexical gate.
- **Item 9:** the checklist is internal-only, `human_review_required: true`,
  `external_release_allowed: false`; "ready" means a human review gate is
  satisfied in process terms, never an engineering or certification claim.

## Required data governance (carried forward)
Every numeric/technical output keeps value, unit, label, source_type, confidence,
assumption_notes. Exports run the forbidden-claim scan before write and remain
internal and human-review-required by default.

## Required tests (proposed)
- PNG export produces a file when the renderer is present and degrades gracefully
  (SVG only) when absent.
- `compare()` long-form metadata columns present and deterministic.
- Default CLI RFI includes completeness prompts for incomplete metadata.
- Signed/strengthened manifest verifies and fails on tamper.
- Archive bundles the expected files; manifest still validates after unpack.
- Semantic risk layer flags crafted risky phrasings and passes safe framings;
  it never overrides the hard lexical gate.
- Expanded Korean patterns block new affirmative claims and leave negations clean.
- Regression: Gate 1–4 outputs remain green.

## Hard prohibitions (Gate 5 must NOT do or claim)
- production CAD; real engineering validation
- CFD validation; crash validation; thermal validation; structural FEA certification
- certification claims; road-legality claims; homologation-readiness claims
- production-feasibility claims; supplier-confirmation claims; design-completion claims
- investor-ready / external marketing claims; external release (of any kind)
- PR creation without explicit instruction
- broad architecture rewrite; large new dependencies without justification
- touching the SafeCopy base or archival PR #1; amending/force-pushing history

## Proposed sequencing
1. Item 3 (compare metadata) and Item 4 (default RFI prompts) — small.
2. Item 8 (Korean coverage) and Item 7 (semantic risk layer) — governance.
3. Item 5 (integrity) → Item 6 (archiving).
4. Item 2 (renderer eval) → Item 1 (PNG) — dependency-sensitive.
5. Item 9 (release-readiness checklist) last.
6. Tests alongside each item.

## Acceptance criteria (proposed)
- New artifacts/integrity are internal-only, human-review-required, and
  deterministic where feasible (SVG/manifest hashing).
- Semantic layer is advisory and never weakens the hard lexical gate.
- Full suite green on Python 3.11 and 3.12; Gate 1–4 regression intact.

## Decision needed
Approve as-is, trim/reorder, or adjust the renderer choice and integrity
mechanism. No work starts until approved.
