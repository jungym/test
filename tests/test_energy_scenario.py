"""Tests for Review Gate 3 Item 3 — energy-scenario comparison (comparison only)."""

from haen import mass_energy
from haen.governance import check_text
from haen.sample_data import build_sample_fleet


def test_scenario_covers_three_branches():
    df = mass_energy.energy_scenario_comparison(build_sample_fleet())
    assert len(df) == 3
    branches = set(df["branch"])
    assert {"GT-1", "GT-1H", "GT-1H-LH2"} == branches


def test_scenario_has_expected_columns():
    df = mass_energy.energy_scenario_comparison(build_sample_fleet())
    for col in [
        "storage_type", "usable_energy_kwh", "energy_density_wh_per_kg",
        "implied_storage_mass_kg", "refill_time_min",
        "specific_energy_kwh_per_t_vehicle", "energy_mass_fraction_pct",
    ]:
        assert col in df.columns


def test_scenario_deterministic():
    fleet = build_sample_fleet()
    a = mass_energy.energy_scenario_comparison(fleet)
    b = mass_energy.energy_scenario_comparison(fleet)
    assert a.equals(b)


def test_lh2_remains_watch_branch():
    df = mass_energy.energy_scenario_comparison(build_sample_fleet())
    assert df.loc["GT-1H-LH2-c01", "branch_status"] == "watch"


def test_line_items_are_labelled():
    df = mass_energy.energy_scenario_line_items(build_sample_fleet())
    assert not df.empty
    for col in ["value", "unit", "label", "source_type", "confidence", "assumption_notes"]:
        assert col in df.columns
    # every row carries a label and unit
    assert df["label"].notna().all()
    assert (df["unit"] != "").all()


def test_scenario_outputs_governance_clean():
    fleet = build_sample_fleet()
    text = (
        mass_energy.energy_scenario_comparison(fleet).to_string()
        + mass_energy.energy_scenario_line_items(fleet).to_string()
    )
    assert check_text(text) == []
