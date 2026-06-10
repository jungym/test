# HAEN Hypercar Design Support AI

A **human-reviewed, AI-assisted design _support_ system** (MVP).

> **This is not an autonomous hypercar design system.** Every output is an
> engineering aid that requires human review. The system never claims a design to
> be **road legal**, **homologation ready**, **crash safe**, **production
> feasible**, **supplier confirmed**, or **design complete** — and a governance
> layer actively blocks any generated document that contains such claims.

## What it does

| # | Module | Capability |
|---|--------|-----------|
| 00 | [`governance`](00_governance/) | Forbidden-claim checker + assumption ledger |
| 01 | [`vehicle_definition`](01_vehicle_definition/) | Pydantic vehicle/branch schema validation |
| 02 | [`design_space_explorer`](02_design_space_explorer/) | Architecture branch & scenario comparison |
| 03 | [`packaging`](03_packaging/) | Parametric packaging + overlap detection |
| 04 | [`mass_energy`](04_mass_energy/) | Mass & energy comparison |
| 05 | [`low_fidelity_simulation`](05_low_fidelity_simulation/) | First-order performance/range estimates |
| 06 | [`visualization`](06_visualization/) | Plotly / Matplotlib charts |
| 07 | [`supplier_evidence`](07_supplier_evidence/) | Supplier evidence register |
| 08 | [`rfi_builder`](08_rfi_builder/) | RFI generation from gaps |
| 09 | [`report_builder`](09_report_builder/) | Entry validation dossier builder |
| 10 | [`webapp`](10_webapp/) | Streamlit dashboard |

The numbered directories document each module; the importable code lives in the
[`haen/`](haen/) Python package (e.g. `00_governance` → `haen.governance`).

## Core architecture branches

| Branch | Status | Powertrain | Energy storage |
|--------|--------|-----------|----------------|
| **GT-1** | baseline | BEV | Li-ion battery pack |
| **GT-1H** | halo | H2 fuel cell | 700 bar compressed H2 |
| **GT-1H-LH2** | watch | H2 fuel cell | Cryogenic liquid H2 |

Defined in [`haen/data/branches.yaml`](haen/data/branches.yaml).

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"        # or: pip install -r requirements.txt
```

Requires Python 3.11+.

## Use

```bash
# CLI
haen compare                   # branch comparison + trade-off ranking
haen simulate                  # low-fidelity performance estimates
haen screen                    # braking + load-transfer dynamics screening
haen rfi --branch GT-1H        # generate an RFI from open gaps (incl. partners)
haen dossier --branch GT-1 --out out/dossier.md
haen export --branch GT-1 --out out/pkg   # internal review package (dossier+images+manifest)
haen release-candidate --out out/rc --generated-at 2026-01-01T00:00:00+00:00
                                          # full internal release candidate (reproducible)
haen validate out/rc                      # validate a package directory
haen validate out/rc.zip                  # validate the archive (+ .sha256 sidecar)
haen readiness                            # internal release-readiness checklist
haen check path/to/text.md     # forbidden-claim check

# Dashboard
streamlit run haen/webapp/app.py
```

```python
# Library
from haen.sample_data import build_sample_fleet
from haen import design_space_explorer as dse

fleet = build_sample_fleet()
print(dse.score_branches(fleet).ranking)   # advisory trade-off ranking
```

## Test

```bash
pytest
```

## Scope and limitations

See [`docs/scope_and_governance.md`](docs/scope_and_governance.md). In short: this
is an **early-stage exploration** aid. Simulation is low fidelity. Supplier
figures are evidence to be verified by humans, never confirmations. Nothing here
constitutes certification of any kind.
