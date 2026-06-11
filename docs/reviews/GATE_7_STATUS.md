# Gate 7 — Status Note

**Status: IMPLEMENTED (pending final CI confirmation).**

Internal release candidate completion. The tool now runs on real, human-authored
project data (not only the bundled sample), has hardened tests/CI, and ships an
operator guide + release procedure. Human-reviewed AI-assisted concept
engineering support only — not autonomous design, certification, production CAD,
supplier confirmation, or external release.

## Workstreams

| WS | Item | Summary | Tests |
|----|------|---------|-------|
| A | A1 | `haen/io.py` loaders + `Project` aggregator | `test_io.py` |
| A | A2 | CLI `--project` (sample fallback) + richer reproducible dossier | `test_cli_project.py` |
| A | A3 | dashboard project loading; drop unused DuckDB | webapp smoke |
| B | B1 | webapp smoke, CLI e2e, design-space/viz/supplier units | several |
| B | B2 | CI: ruff lint + coverage; lint fixes | CI |
| C | C1 | example project, operator guide, CHANGELOG, release procedure | `test_example_project.py` |
| C | C2 | review trail + MVP/README updates | docs |

## Key capabilities added

- `haen <cmd> --project examples/project/haen-project.yaml` runs any command on
  user data; no flag → bundled sample (backward compatible).
- One-command internal package on user data:
  `haen release-candidate --project ... --out ... --generated-at <ISO>`.
- Dashboard loads a project manifest from the sidebar.
- File-backed assumption ledger via the manifest's `ledger_db`.

## Governance

- Hard forbidden-claim gate unchanged and authoritative; dossiers built from
  user data still pass it; advisory semantic layer unchanged.
- All artifacts internal-only, `human_review_required: true`,
  `external_release_allowed: false`.

## Quality

- ruff lint enforced in CI; pytest with coverage on Python 3.11 + 3.12.
- Local: ruff clean, ~85% line coverage (webapp + visualization rise in CI where
  Plotly is installed).

## Remaining risks

- Semantic layer is advisory/heuristic; human review is the final control.
- PNG non-deterministic (excluded from the hashed manifest; SVG is the baseline).
- Reproducibility relies on a fixed `generated_at`.

## Parked next items

- External manifest signing (approved key management required).
- Deterministic raster renderer.
- Wider example library / additional operator scenarios.

## Constraints honoured

No PR opened · SafeCopy base untouched · no previous commits amended or
force-pushed · hard forbidden-claim gate unchanged.
