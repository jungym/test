# 04_mass_energy

**Implemented in:** [`haen/mass_energy.py`](../haen/mass_energy.py)

Mass and energy comparison across branches.

- `mass_summary(v)` / `energy_summary(v)` — per-vehicle metrics.
- `compare(vehicles)` — side-by-side comparison DataFrame.
- `mass_breakdown_table(v)` — mass contributors with % of curb mass.
- `delta_vs_baseline(vehicles, baseline_id)` — deltas relative to a chosen baseline.

All figures derive from the vehicle definitions' planning assumptions.
