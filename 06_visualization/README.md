# 06_visualization

**Implemented in:** [`haen/visualization.py`](../haen/visualization.py)

Chart helpers returning figure objects (no rendering side effects).

- `mass_energy_bar(df, metric)` — Plotly bar chart.
- `tradeoff_radar(table, keys)` — Plotly radar of normalised criteria.
- `packaging_topview(components)` — Plotly 2-D top view of bounding boxes.
- `mass_breakdown_pie_mpl(breakdown)` — Matplotlib (Agg) pie for static reports.

Used by the Streamlit dashboard and report builder.
