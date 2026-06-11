# Review Gate 7 — Internal Release Candidate Completion

**Status: IMPLEMENTED.** Closes the gap between the gate-1–6 feature set (which
already met the MVP spec) and a genuinely usable, finished internal release
candidate. Three workstreams (A real-data input/persistence, B quality/tests/CI,
C release finalization/docs).

HAEN Hypercar Design Support AI is a human-reviewed AI-assisted concept
engineering support system, not an autonomous vehicle design, certification,
production CAD, or external-release system. Gate 7 adds no engineering analysis
or validation.

## Baseline at start
Gate 6 closed (`docs/reviews/GATE_6_CLOSURE.md`); final Gate 6 commit `3e3a42c`;
CI run #15 green; 308 passed / 1 skipped. SafeCopy base untouched. No PR.

## Workstream A — real data input / persistence
- **A1** `haen/io.py`: load/dump vehicles, components, evidence, partners and
  assumptions from YAML/JSON via the existing Pydantic models; `ProjectConfig`
  manifest + `load_project()`; `Project` aggregator;
  `sample_data.build_sample_project()` fallback. (`tests/test_io.py`)
- **A2** CLI `--project` on all data-consuming commands (sample fallback);
  dossier/export/release-candidate now include evidence/ledger/RFI; dropped the
  non-deterministic ledger `created_at` from the dossier so reproducible exports
  stay byte-stable. (`tests/test_cli_project.py`)
- **A3** dashboard project loading; removed the unused DuckDB dependency
  (SQLite is the chosen backend).

## Workstream B — quality / tests / CI
- **B1** webapp smoke test (Streamlit stubbed), CLI e2e tests, and dedicated
  unit tests for `design_space_explorer`, `visualization`, `supplier_evidence`.
- **B2** CI runs `ruff check .` and pytest with coverage on Python 3.11 + 3.12;
  fixed all lint findings; ruff added to dev extras.

## Workstream C — release finalization / docs
- **C1** `examples/project/` worked example; `docs/operator_guide.md`;
  `CHANGELOG.md` (0.1.0); `docs/release_procedure.md`;
  `tests/test_example_project.py`.
- **C2** this scope note, `GATE_7_STATUS.md`, `GATE_6_CLOSURE.md` (recorded),
  `MVP_STATUS.md` + `README.md` updates. Tagging only on explicit instruction.

## Constraints honoured
No PR opened; SafeCopy base untouched; no previous commits amended or
force-pushed; hard forbidden-claim gate unchanged and authoritative; all
generated artifacts internal-only / human-review-required /
`external_release_allowed=false`.

## Out of scope (parked)
External manifest signing (needs approved key management); deterministic raster
rendering; any external release, certification, production, supplier-confirmation,
road-legality, or real-world validation work.
