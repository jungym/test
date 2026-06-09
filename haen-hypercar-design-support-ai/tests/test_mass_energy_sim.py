"""Tests for 04_mass_energy, 05_low_fidelity_simulation, 02_design_space_explorer."""

import pytest

from haen import design_space_explorer as dse
from haen import low_fidelity_simulation as sim
from haen import mass_energy
from haen.sample_data import build_sample_fleet


def test_compare_table_shape():
    fleet = build_sample_fleet()
    df = mass_energy.compare(fleet)
    assert len(df) == 3
    assert "curb_mass_kg" in df.columns
    assert "usable_energy_kwh" in df.columns


def test_delta_vs_baseline():
    fleet = build_sample_fleet()
    df = mass_energy.delta_vs_baseline(fleet, baseline_id="GT-1-c01")
    # baseline row delta against itself is zero
    assert df.loc["GT-1-c01", "curb_mass_kg_delta"] == pytest.approx(0.0)


def test_delta_unknown_baseline_raises():
    with pytest.raises(KeyError):
        mass_energy.delta_vs_baseline(build_sample_fleet(), baseline_id="nope")


def test_simulation_results_are_physical():
    for r in sim.simulate_all(build_sample_fleet()):
        assert r.top_speed_kph > 100
        assert 0 < r.zero_to_100_s < 20
        assert r.estimated_range_km > 0
        assert r.avg_consumption_kwh_per_100km > 0


def test_h2_branches_use_lower_efficiency():
    fleet = {v.id: v for v in build_sample_fleet()}
    bev = sim.simulate(fleet["GT-1-c01"])
    h2 = sim.simulate(fleet["GT-1H-c01"])
    assert bev.drivetrain_efficiency > h2.drivetrain_efficiency


def test_tradeoff_scoring_ranks_all():
    fleet = build_sample_fleet()
    result = dse.score_branches(fleet)
    assert len(result.ranking) == 3
    # scores are in 0..100
    assert result.scores.max() <= 100
    assert result.scores.min() >= 0


def test_tradeoff_weights_must_be_positive():
    fleet = build_sample_fleet()
    with pytest.raises(ValueError):
        dse.score_branches(fleet, criteria=[dse.Criterion("curb_mass_kg", 0.0, False)])


def test_comparison_table_merges_sim_and_mass():
    fleet = build_sample_fleet()
    table = dse.comparison_table(fleet)
    assert "estimated_range_km" in table.columns
    assert "curb_mass_kg" in table.columns
