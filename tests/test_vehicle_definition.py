"""Tests for 01_vehicle_definition: schema validation and branch loading."""

import pytest
from pydantic import ValidationError

from haen.vehicle_definition import (
    BranchStatus,
    Dimensions,
    EnergyStorage,
    MassItem,
    Powertrain,
    load_branches,
    vehicle_from_branch,
)


def test_load_branches_has_three_core_branches():
    branches = load_branches()
    assert set(branches) == {"GT-1", "GT-1H", "GT-1H-LH2"}
    assert branches["GT-1"].status == BranchStatus.BASELINE
    assert branches["GT-1H"].status == BranchStatus.HALO
    assert branches["GT-1H-LH2"].status == BranchStatus.WATCH


def test_energy_storage_mass_derivation():
    es = EnergyStorage(
        storage_type="battery",
        usable_energy_kwh=100,
        gravimetric_density_wh_per_kg=200,
        refill_time_min=30,
    )
    # 100 kWh = 100_000 Wh / 200 Wh/kg = 500 kg
    assert es.storage_mass_kg == pytest.approx(500.0)


def test_dimensions_reject_wheelbase_ge_length():
    with pytest.raises(ValidationError):
        Dimensions(length_mm=4000, width_mm=2000, height_mm=1200, wheelbase_mm=4000)


def test_dimensions_reject_negative():
    with pytest.raises(ValidationError):
        Dimensions(length_mm=-1, width_mm=2000, height_mm=1200, wheelbase_mm=2700)


def test_vehicle_curb_mass_from_breakdown_overrides_glider():
    branches = load_branches()
    v = vehicle_from_branch(
        branches["GT-1"],
        id="t1",
        name="test",
        dimensions=Dimensions(length_mm=4600, width_mm=2000, height_mm=1180, wheelbase_mm=2750),
        performance_targets=_targets(),
        glider_mass_kg=900,
    )
    assert v.curb_mass_kg == pytest.approx(900 + v.energy_storage.storage_mass_kg)
    v.mass_breakdown = [
        MassItem(name="a", mass_kg=100, group="structure"),
        MassItem(name="b", mass_kg=200, group="powertrain"),
    ]
    assert v.curb_mass_kg == pytest.approx(300)
    assert v.mass_by_group == {"structure": 100, "powertrain": 200}


def test_vehicle_powertrain_matches_branch():
    branches = load_branches()
    v = vehicle_from_branch(
        branches["GT-1H"],
        id="h1",
        name="h",
        dimensions=Dimensions(length_mm=4600, width_mm=2000, height_mm=1180, wheelbase_mm=2750),
        performance_targets=_targets(),
    )
    assert v.powertrain == Powertrain.H2_FUEL_CELL
    assert v.power_to_weight_kw_per_t() > 0


def test_invalid_id_rejected():
    branches = load_branches()
    with pytest.raises(ValidationError):
        vehicle_from_branch(
            branches["GT-1"],
            id="bad id with spaces",
            name="x",
            dimensions=Dimensions(length_mm=4600, width_mm=2000, height_mm=1180, wheelbase_mm=2750),
            performance_targets=_targets(),
        )


def _targets():
    from haen.vehicle_definition import PerformanceTargets

    return PerformanceTargets(top_speed_kph=340, zero_to_100_s_target=2.7, target_range_km=450)
