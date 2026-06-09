"""02_design_space_explorer — architecture branch & scenario comparison.

Combines the validated vehicle definitions, the mass/energy module and the
low-fidelity simulation into unified comparison tables and a simple weighted
trade-off score. Scores are decision *support* only; branch selection is a human
decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from . import low_fidelity_simulation as sim
from . import mass_energy
from .vehicle_definition import VehicleDefinition


@dataclass
class Criterion:
    """A scoring criterion for trade-off analysis.

    ``higher_is_better`` controls the direction of normalisation. ``weight`` is
    relative; weights are normalised to sum to 1 before scoring.
    """

    key: str
    weight: float
    higher_is_better: bool
    label: str = ""

    def __post_init__(self):
        if not self.label:
            self.label = self.key


DEFAULT_CRITERIA: list[Criterion] = [
    Criterion("estimated_range_km", 0.30, higher_is_better=True, label="Range"),
    Criterion("zero_to_100_s", 0.20, higher_is_better=False, label="0-100 time"),
    Criterion("curb_mass_kg", 0.20, higher_is_better=False, label="Curb mass"),
    Criterion("refill_time_min", 0.15, higher_is_better=False, label="Refill time"),
    Criterion("power_to_weight_kw_per_t", 0.15, higher_is_better=True, label="Power/weight"),
]


def comparison_table(vehicles: list[VehicleDefinition], *, cruise_kph: float = 100.0) -> pd.DataFrame:
    """Merge mass/energy metrics with simulation metrics, one row per vehicle."""
    me = mass_energy.compare(vehicles)
    sim_rows = {r.vehicle_id: r for r in sim.simulate_all(vehicles, cruise_kph=cruise_kph)}
    sim_df = pd.DataFrame(
        {
            vid: {
                "top_speed_kph": r.top_speed_kph,
                "zero_to_100_s": r.zero_to_100_s,
                "estimated_range_km": r.estimated_range_km,
                "avg_consumption_kwh_per_100km": r.avg_consumption_kwh_per_100km,
            }
            for vid, r in sim_rows.items()
        }
    ).T
    return me.join(sim_df)


def _normalise(series: pd.Series, higher_is_better: bool) -> pd.Series:
    """Min-max normalise a series to [0, 1] respecting direction."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(1.0, index=series.index)
    norm = (series - lo) / (hi - lo)
    return norm if higher_is_better else 1.0 - norm


@dataclass
class TradeoffResult:
    table: pd.DataFrame
    criteria: list[Criterion]
    scores: pd.Series = field(default_factory=pd.Series)

    @property
    def ranking(self) -> pd.Series:
        return self.scores.sort_values(ascending=False)


def score_branches(
    vehicles: list[VehicleDefinition],
    criteria: list[Criterion] | None = None,
    *,
    cruise_kph: float = 100.0,
) -> TradeoffResult:
    """Compute weighted trade-off scores across vehicles.

    Returns a :class:`TradeoffResult`; ``.ranking`` gives the ordered scores.
    Higher score = better on the chosen weighted criteria. This is advisory.
    """
    criteria = criteria or DEFAULT_CRITERIA
    table = comparison_table(vehicles, cruise_kph=cruise_kph)

    total_weight = sum(c.weight for c in criteria)
    if total_weight <= 0:
        raise ValueError("criteria weights must sum to a positive value")

    score = pd.Series(0.0, index=table.index)
    for c in criteria:
        if c.key not in table.columns:
            raise KeyError(f"criterion '{c.key}' not present in comparison table")
        norm = _normalise(table[c.key], c.higher_is_better)
        score += norm * (c.weight / total_weight)

    score = (score * 100).round(1)
    score.name = "tradeoff_score"
    return TradeoffResult(table=table, criteria=criteria, scores=score)
