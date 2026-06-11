# Operator Guide — HAEN Hypercar Design Support AI

HAEN Hypercar Design Support AI is a human-reviewed AI-assisted concept
engineering support system, not an autonomous vehicle design, certification,
production CAD, or external-release system. **Every output is internal-only and
requires human review.** Nothing it produces is a road-legality, homologation,
crashworthiness, production-feasibility, supplier-confirmation, or real-world
performance claim.

This guide covers day-to-day use. For scope/governance see
`docs/scope_and_governance.md`; for architecture see `docs/architecture.md`.

## 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"     # or: pip install -r requirements.txt
```

Requires Python 3.11+. The `haen` command becomes available.

## 2. Run on the bundled sample (no input needed)

```bash
haen compare        # branch comparison + advisory trade-off ranking
haen simulate       # low-fidelity performance screening (NOT predictions)
haen screen         # braking + load-transfer dynamics screening
haen rfi            # Request-For-Information (incl. metadata-completeness gaps)
haen dossier        # entry-validation dossier (Markdown, to stdout)
haen readiness      # internal release-readiness checklist
```

## 3. Run on your own project

Define a **project manifest** that points at your data files. Start from the
worked example in `examples/project/`:

```
examples/project/
  haen-project.yaml   # manifest (programme, branch, and the paths below)
  vehicles.yaml       # one or more vehicle definitions (required)
  components.yaml     # packaging components (axis-aligned bounding boxes)
  evidence.yaml       # supplier evidence records (nothing is "confirmed")
  partners.yaml       # partner registry (RFI candidate / watch / observation)
  assumptions.yaml    # assumption-ledger entries
```

Then pass `--project`:

```bash
haen compare  --project examples/project/haen-project.yaml
haen dossier  --project examples/project/haen-project.yaml
```

Every command accepts `--project`; without it the bundled sample is used.

### Authoring data files

- All files validate against the schemas in `haen/vehicle_definition.py`,
  `haen/packaging.py`, and `haen/supplier_evidence.py`. Malformed data fails
  fast with a clear error.
- Each file is `{key: [ ... ]}` (e.g. `vehicles:`), or a bare list.
- To get a correct starting template, dump the sample:
  `python -c "from haen import io; from haen.sample_data import build_sample_fleet as f; io.dump_models(f(),'vehicles.yaml',key='vehicles')"`.
- Numeric/technical fields carry governance metadata (`value, unit, label,
  source_type, confidence, assumption_notes`). Fill these in — incomplete
  provenance is surfaced as RFI prompts, not hidden.

### Persistent assumption ledger (optional)

Set `ledger_db: ledger.db` in the manifest to use a file-backed SQLite ledger
that persists across runs (otherwise an in-memory ledger is rebuilt each run).

## 4. Build the internal review package

One command produces the complete internal package:

```bash
haen release-candidate \
  --project examples/project/haen-project.yaml \
  --out dist/internal_review \
  --generated-at 2026-01-01T00:00:00+00:00      # fixed timestamp => reproducible
```

It writes (into `dist/internal_review/`): `dossier.md`, `dossier.meta.json`,
`rfi.md`, `readiness.md`, `manifest.json`, `validation_report.json`,
`packaging_top.svg`, `packaging_side.svg`; plus an archive
`dist/internal_review.zip` and its integrity sidecar
`dist/internal_review.zip.sha256`.

- **Reproducible mode**: pass a fixed `--generated-at` to get a byte-stable
  package and archive (optional PNGs are suppressed; SVG/text are the
  deterministic baseline). Omit it for a wall-clock, non-deterministic build.

Validate a package or archive:

```bash
haen validate dist/internal_review           # directory
haen validate dist/internal_review.zip       # archive (checks the sidecar hash)
```

## 5. Reading the outputs

- **Dossier** — assembles vehicle definition, mass/energy (with per-line
  provenance), low-fidelity simulation + dynamics screening, branch trade-off,
  packaging check, supplier evidence, assumptions, RFI summary, an **advisory
  semantic-risk** section (warning-only), and a sign-off block. The header
  declares `human_review_required: true`, `external_release_allowed: false`.
- **Readiness checklist** — gate status, CI status field, artifact-validation,
  forbidden-claim status, advisory semantic-risk count, metadata completeness.
- **RFI** — questions for open low-confidence assumptions, unverified evidence,
  components lacking evidence, RFI-candidate partners, and metadata gaps.

## 6. Governance you must respect

- The **hard forbidden-claim checker** is authoritative; the report/RFI/export
  builders refuse to emit text containing a forbidden claim. Run it on any text:
  `haen check path/to/file.md`.
- The **semantic-risk layer is advisory only** — it raises human-review
  candidates and never relaxes the hard gate.
- Korean governance reference: `docs/claim_governance_ko.md`.
- Do **not** represent any output as an external-release approval, a
  certification, a road-legality clearance, a production-readiness sign-off, a
  supplier confirmation, or a real-world validation — it is none of these.

## 7. Branch model

- **GT-1 BEV** — baseline, first digital package; primary for packaging/mass/
  energy/dossier outputs.
- **GT-1H 700bar H2** — hydrogen halo; screening/comparison only.
- **GT-1H LH2** — liquid-hydrogen watch branch (Hylium = Level 1 RFI candidate;
  Cryos/DALIM/Parity = watch; KIMM = technology observation). Not baseline; no
  supplier confirmation.
