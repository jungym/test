# Gate 6 — Status Note

**Status: IMPLEMENTED (pending final CI confirmation).**

Internal release-candidate layer for the HAEN Hypercar Design Support AI.
Human-reviewed AI-assisted concept engineering support only — not autonomous
design, certification, production CAD, supplier confirmation, or external
release.

## Items 1–8

| Item | Summary | Tests |
|------|---------|-------|
| 1 | Advisory semantic-risk surfacing in dossier + readiness | `test_gate6_semantic_surfacing.py` |
| 2 | Deterministic raster evaluation (decision below) | covered by repro tests |
| 3 | Reproducibility mode (canonical shared mechanism) | `test_reproducibility_mode.py` |
| 4 | `haen release-candidate --out DIR [--generated-at ISO]` | `test_release_candidate.py` |
| 5 | End-to-end release acceptance test | `test_e2e_acceptance.py` |
| 6 | Safe-section mechanism + Korean governance doc | `test_safe_sections.py` |
| 7 | Archive validation UX (dir or .zip + sidecar) | `test_validate_archive.py` |
| 8 | Release-readiness consolidation | with Item 1 |

## Item 2 decision — deterministic raster rendering

Evaluated matplotlib(Agg) PNG output: PNG byte-stability across environments is
not assured (library/encoder metadata and version variance), and proving it
would add dependency risk for no review value. **Decision:** PNG remains an
optional, non-hashed convenience artifact (`optional_non_deterministic_artifacts`);
reproducible mode suppresses PNG entirely; SVG/text artifacts remain the
deterministic, hashed baseline. Revisit only if a deterministic renderer is
explicitly approved.

## Addendum compliance

- **No circular hashing:** the archive SHA-256 lives in a `<archive>.zip.sha256`
  sidecar outside the archive; `manifest.json`'s `bundle_sha256` hashes the
  artifact map only.
- **Determinism fields:** `reproducible`, `deterministic_core_artifacts`,
  `optional_non_deterministic_artifacts`, `archive_determinism_status`,
  `archive_hash_sidecar` recorded in the manifest.
- **Deterministic archives:** sorted entries, timestamps normalized to the fixed
  `generated_at`, stable permissions/compression; byte-equality proven by tests.
- **Safe sections:** docs-only (`docs/claim_governance_ko.md` uses them);
  generated artifacts are marker-free (enforced in export + tests).
- **One reproducibility path:** `release-candidate --generated-at` reuses
  `export_release_package(reproducible=True)`; tests assert shared
  `generated_at`/ordering and identical dossier hashes across flows.
- **Layout preserved:** existing Gate 4/5 package layout unchanged; only
  additive files (`readiness.md`, sidecar) and manifest fields.

## Target UX (works today)

```bash
python -m haen.cli release-candidate --out dist/internal_review --generated-at 2026-01-01T00:00:00+00:00
python -m haen.cli validate dist/internal_review          # directory
python -m haen.cli validate dist/internal_review.zip      # archive + sidecar
```

## Remaining risks

- Semantic layer remains heuristic/advisory; human review is the final control.
- Reproducibility depends on fixed `generated_at`; wall-clock builds are
  intentionally marked `non_deterministic`.
- Korean coverage broadened but pattern-based, not exhaustive.

## Parked next items

- External manifest signing (requires approved key management).
- Deterministic raster renderer (only if explicitly approved).
- Operator-workflow doc expansion beyond the README quickstart.

## Constraints honoured

No PR opened · SafeCopy base untouched · no previous commits amended or
force-pushed · no CI changes · hard forbidden-claim gate unchanged.
