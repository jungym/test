# 03_packaging

**Implemented in:** [`haen/packaging.py`](../haen/packaging.py)

Parametric packaging with axis-aligned bounding boxes (AABB) in a simple vehicle
frame (x longitudinal, y lateral, z vertical; mm).

- `Box`, `Component` — geometry primitives.
- `boxes_overlap(a, b, tol_mm)` / `detect_overlaps(components)` — interference
  (clash) detection with tolerance and rigid/tolerant handling.
- `check_envelope(components, vehicle)` — approximate fit check against external
  dimensions.

Low-fidelity geometric aid, not CAD clash detection.
