# 02_design_space_explorer

**Implemented in:** [`haen/design_space_explorer.py`](../haen/design_space_explorer.py)

Architecture branch and scenario comparison.

- `comparison_table(vehicles)` — merges mass/energy metrics with low-fidelity
  simulation metrics into one table.
- `score_branches(vehicles, criteria)` — weighted, normalised trade-off scoring.
  Returns a `TradeoffResult` with `.ranking`. **Advisory only** — branch selection
  is a human decision.
- `Criterion` / `DEFAULT_CRITERIA` — configurable scoring criteria with direction
  and weight.
