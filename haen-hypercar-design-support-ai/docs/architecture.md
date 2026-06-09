# Architecture

## Layout

```
haen/                         importable Python package
  governance.py               00 — forbidden-claim checker + assumption ledger
  vehicle_definition.py       01 — Pydantic schemas + branch loader
  design_space_explorer.py    02 — branch & scenario comparison, trade-off scoring
  packaging.py                03 — AABB packaging + overlap/envelope detection
  mass_energy.py              04 — mass & energy comparison
  low_fidelity_simulation.py  05 — first-order performance model
  visualization.py            06 — Plotly/Matplotlib helpers
  supplier_evidence.py        07 — evidence register
  rfi_builder.py              08 — RFI generation
  report_builder.py           09 — entry validation dossier
  webapp/app.py               10 — Streamlit dashboard
  sample_data.py              seeded fleet / ledger / evidence
  cli.py                      `haen` command-line entry point
  data/                       branches.yaml, forbidden_claims.yaml
templates/                    Markdown report templates
00_governance/ … 10_webapp/   per-module documentation (README mapping)
tests/                        pytest suite
docs/                         this documentation
```

## Data flow

```
branches.yaml ──► vehicle_definition ──► VehicleDefinition(s)
                                            │
        ┌───────────────────────────────────┼───────────────────────────┐
        ▼                                   ▼                           ▼
   mass_energy                    low_fidelity_simulation           packaging
        │                                   │                           │
        └──────────────► design_space_explorer ◄──────────────────────┘
                                   │
   supplier_evidence ─────────────┤
   governance (ledger) ───────────┤
                                   ▼
                          rfi_builder  ──►  report_builder ──► dossier (Markdown)
                                   │                 │
                                   └──── governance forbidden-claim gate ───┘
```

## Design choices

- **Pydantic v2** for all external/validated data — fail fast on bad inputs.
- **SQLite (stdlib)** for the assumption ledger so it works with zero setup;
  DuckDB is a listed dependency for heavier analytical queries when needed.
- **Pandas** for comparison tables; **Plotly** for the interactive dashboard and
  **Matplotlib** for static report images.
- **Governance as a hard gate**: `report_builder` and `rfi_builder` call
  `governance.assert_clean` / `check_text` before emitting any document, so the
  forbidden-claim rule cannot be bypassed by normal use.
- **Numbered directories** mirror the requested module list and are kept as the
  human-facing map; runtime code is a clean, importable package (`haen`).
