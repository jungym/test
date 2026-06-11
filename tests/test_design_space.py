"""Gate 7 B1 — dedicated unit tests for design_space_explorer scoring."""

import pytest

from haen import design_space_explorer as dse
from haen.sample_data import build_sample_fleet


def test_comparison_table_merges_mass_and_sim():
    table = dse.comparison_table(build_sample_fleet())
    assert {"curb_mass_kg", "usable_energy_kwh", "estimated_range_km", "zero_to_100_s"} <= set(
        table.columns
    )
    assert len(table) == 3


def test_score_branches_ranks_all_in_0_100():
    res = dse.score_branches(build_sample_fleet())
    assert len(res.ranking) == 3
    assert res.scores.max() <= 100 and res.scores.min() >= 0
    # ranking is sorted descending
    vals = list(res.ranking.values)
    assert vals == sorted(vals, reverse=True)


def test_weight_direction_changes_ranking():
    fleet = build_sample_fleet()
    favor_range = dse.score_branches(
        fleet, criteria=[dse.Criterion("estimated_range_km", 1.0, higher_is_better=True)]
    )
    favor_mass = dse.score_branches(
        fleet, criteria=[dse.Criterion("curb_mass_kg", 1.0, higher_is_better=False)]
    )
    # Different single-criterion weightings produce different top entries or scores.
    assert list(favor_range.ranking.index) != list(favor_mass.ranking.index) or \
        not favor_range.scores.equals(favor_mass.scores)


def test_zero_total_weight_rejected():
    with pytest.raises(ValueError):
        dse.score_branches(
            build_sample_fleet(),
            criteria=[dse.Criterion("curb_mass_kg", 0.0, higher_is_better=False)],
        )


def test_unknown_criterion_key_rejected():
    with pytest.raises(KeyError):
        dse.score_branches(
            build_sample_fleet(),
            criteria=[dse.Criterion("does_not_exist", 1.0, higher_is_better=True)],
        )
