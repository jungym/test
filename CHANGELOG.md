# Changelog

All notable changes to HAEN Hypercar Design Support AI. This is a human-reviewed
AI-assisted concept engineering support system — internal-only, not an
autonomous design, certification, production, or external-release system.

## [0.1.0] — internal release candidate

First internal release candidate. Built and verified across review gates 1–7.

### Added
- **Governance & claim control**: hard forbidden-claim checker (English +
  Korean), assumption ledger, advisory semantic-risk layer (warning-only, never
  weakens the hard gate), `DataLabel`/`ReportMetadata`, docs-only safe-section
  mechanism, internal-only / `human_review_required` / `external_release_allowed=false`
  defaults.
- **Vehicle definition core**: Pydantic schemas, three branches
  (GT-1 BEV / GT-1H 700bar / GT-1H LH2 watch), structured gate-status,
  chassis geometry, per-line mass/energy metadata.
- **Screening**: parametric packaging + overlap/envelope detection,
  mass & energy comparison + scenario tables, low-fidelity simulation, and
  braking / load-transfer / CG-sensitivity dynamics screening (clearly labelled
  `low_fidelity_screening`).
- **Supplier evidence & RFI**: evidence register, partner registry
  (Hylium L1 RFI candidate; Cryos/DALIM/Parity watch; KIMM observation), RFI
  generator with metadata-completeness prompts.
- **Reporting & export**: entry-validation dossier, internal release package
  (`export` / `release-candidate`), SVG packaging artifacts (optional PNG),
  checksummed manifest + bundle hash, zip archive with `.sha256` sidecar,
  reproducible mode, release-readiness checklist, archive validation.
- **Project I/O**: `haen.io` loads vehicles/components/evidence/partners/
  assumptions from YAML/JSON; `--project` flag and dashboard project loading;
  optional file-backed assumption ledger. Bundled sample remains the default.
- **CLI**: `compare`, `simulate`, `screen`, `check`, `rfi`, `dossier`,
  `export`, `validate`, `readiness`, `release-candidate`.
- **Dashboard**: Streamlit app with project loading.
- **Docs**: README, operator guide, architecture, scope & governance, Korean
  governance reference, gate review trail.
- **CI**: ruff lint, byte-compile, pytest (+coverage) on Python 3.11 and 3.12.

### Not included (by design)
Production CAD; CFD/crash/thermal/FEA validation; certification, homologation,
road-legality, production-feasibility, supplier-confirmation, or real-world
performance claims; external release; supplier outreach / NDA / contract
workflows; external manifest signing (hash-based integrity only).
