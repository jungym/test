# Gate 5 — Status Note

**Status: IMPLEMENTED (pending final CI confirmation).**

Artifact-fidelity, integrity and release-readiness layer for the HAEN Hypercar
Design Support AI. Human-reviewed AI-assisted concept engineering support only —
not autonomous design, certification, production, supplier confirmation, or
real-world validation.

## Items 1–10

| Item | Summary | Tests |
|------|---------|-------|
| 1 | Baseline verification | — |
| 2 | Optional PNG rendering (matplotlib Agg; SVG dependency-free baseline) | `test_png_rendering.py` |
| 3 | Per-line metadata in `compare_with_metadata()` | `test_compare_metadata.py` |
| 4 | Completeness-gap RFI prompts in default `haen rfi` | `test_cli_rfi_completeness.py` |
| 5 | Bundle-hash artifact integrity (`validate_release`) | `test_artifact_integrity.py` |
| 6 | Stdlib zip release bundle + validation report | `test_release_bundle.py` |
| 7 | Advisory semantic claim-risk layer (warning-only) | `test_semantic_risk.py` |
| 8 | Expanded Korean forbidden-claim coverage | `test_korean_claims.py` |
| 9 | Internal release-readiness checklist | `test_release_readiness.py` |
| 10 | Documentation consolidation | this note |

## Key capabilities

- `haen.export.export_release_package` / `validate_release` / `archive_release`.
- `haen export` / `haen validate` / `haen readiness` CLI commands.
- `haen.governance.semantic_risk_scan` (advisory, never weakens the hard gate).
- Optional PNG via `visualization.render_diagram_png` (SVG remains the baseline).

## Governance

- Exports/bundles internal-only, `human_review_required: true`,
  `external_release_allowed: false`.
- Hard lexical forbidden-claim gate (`check_text`) remains authoritative; the
  semantic layer is advisory only.
- Forbidden-claim scan runs before any artifact write; `validate_release`
  re-scans and verifies per-file + bundle checksums + internal-only flags.

## Remaining risks

- Semantic layer is heuristic and non-exhaustive (advisory candidates only).
- PNG bytes may be non-deterministic; PNGs are convenience artifacts excluded
  from the hashed/reproducible manifest (SVG is the deterministic baseline).
- Reproducibility relies on injecting a fixed `generated_at`.
- Korean coverage is broadened but still pattern-based, not exhaustive.

## Parked next items

- External signing / key management for manifests (currently hash-based only).
- Renderer evaluation for deterministic raster output.
- Semantic-risk surfacing inside the dossier/readiness outputs.

## Constraints honoured

No PR opened · SafeCopy base untouched · no previous commits amended or
force-pushed · no CI changes.
