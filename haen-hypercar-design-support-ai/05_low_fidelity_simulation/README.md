# 05_low_fidelity_simulation

**Implemented in:** [`haen/low_fidelity_simulation.py`](../haen/low_fidelity_simulation.py)

First-order longitudinal point-mass performance model.

- `estimate_top_speed_kph(v)` — power vs. (aero + rolling) resistance balance.
- `estimate_zero_to_100(v)` — forward integration with a traction-limited launch cap.
- `estimate_range_km(v)` — steady-cruise range and consumption.
- `simulate(v)` / `simulate_all(vehicles)` — full `SimResult`.

**LOW FIDELITY.** Ignores gearing, traction/thermal limits, transients, real
drive cycles and regen. Not a real-world prediction; not for certification.
