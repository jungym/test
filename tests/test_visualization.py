"""Gate 7 B1 — visualization figure helpers (Plotly-guarded)."""

import pytest

from haen import mass_energy
from haen import visualization as viz
from haen.sample_data import build_sample_components, build_sample_fleet

pytest.importorskip("plotly")


def test_mass_energy_bar_returns_figure():
    df = mass_energy.compare(build_sample_fleet())
    fig = viz.mass_energy_bar(df, metric="curb_mass_kg")
    assert fig.data  # has at least one trace


def test_mass_energy_bar_unknown_metric_raises():
    df = mass_energy.compare(build_sample_fleet())
    with pytest.raises(KeyError):
        viz.mass_energy_bar(df, metric="nope")


def test_energy_scenario_chart():
    scenario = mass_energy.energy_scenario_comparison(build_sample_fleet())
    fig = viz.energy_scenario_chart(scenario)
    assert fig.data
    assert "INTERNAL" in fig.layout.title.text


def test_tradeoff_radar():
    table = dse_table()
    fig = viz.tradeoff_radar(table, ["estimated_range_km", "curb_mass_kg", "zero_to_100_s"])
    assert fig.data


def test_packaging_views_render():
    comps = build_sample_components()
    v = build_sample_fleet()[0]
    assert viz.packaging_topview(comps, v).layout is not None
    assert viz.packaging_sideview(comps, v).layout is not None


def dse_table():
    from haen import design_space_explorer as dse

    return dse.comparison_table(build_sample_fleet())
