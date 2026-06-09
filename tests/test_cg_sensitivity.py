"""Tests for Review Gate 2 Item 4 — CG-sensitivity screening sweep.

Low-fidelity screening only. Verifies deterministic, ordered sweep output,
monotonicity, validation, governance labelling, and no forbidden claims.
"""

import pytest

from haen.governance import Confidence, DataLabel, check_text
from haen.low_fidelity_simulation import (
    CgSensitivityScreening,
    screen_cg_sensitivity,
    screen_cg_sensitivity_for,
)
from haen.sample_data import build_sample_fleet


def test_sweep_is_sorted_and_deterministic():
    a = screen_cg_sensitivity(
        mass_kg=1500, wheelbase_mm=2750, track_width_mm=1700,
        cg_heights_mm=[500, 300, 400],
    )
    heights = [row.cg_height_mm for row in a.rows]
    assert heights == [300, 400, 500]  # sorted ascending
    b = screen_cg_sensitivity(
        mass_kg=1500, wheelbase_mm=2750, track_width_mm=1700,
        cg_heights_mm=[300, 400, 500],
    )
    assert a.rows == b.rows  # deterministic


def test_transfer_increases_with_cg_height():
    s = screen_cg_sensitivity(
        mass_kg=1500, wheelbase_mm=2750, track_width_mm=1700,
        cg_heights_mm=[300, 400, 500],
    )
    lon = [r.longitudinal_load_transfer_n for r in s.rows]
    lat = [r.lateral_load_transfer_n for r in s.rows]
    assert lon == sorted(lon)
    assert lat == sorted(lat)


def test_known_value_in_sweep():
    s = screen_cg_sensitivity(
        mass_kg=1500, wheelbase_mm=2750, track_width_mm=1700,
        cg_heights_mm=[400], longitudinal_decel_mps2=9.81, lateral_accel_mps2=9.81,
    )
    row = s.rows[0]
    assert row.longitudinal_load_transfer_n == pytest.approx(1500 * 9.81 * (400 / 2750), abs=0.5)


@pytest.mark.parametrize("kw", [
    {"cg_heights_mm": []},
    {"cg_heights_mm": [0, 400]},
    {"cg_heights_mm": [-100]},
    {"mass_kg": 0},
    {"wheelbase_mm": 0},
    {"track_width_mm": 0},
])
def test_invalid_inputs_fail(kw):
    base = dict(mass_kg=1500, wheelbase_mm=2750, track_width_mm=1700, cg_heights_mm=[400])
    base.update(kw)
    with pytest.raises(ValueError):
        screen_cg_sensitivity(**base)


def test_negative_acceleration_fails():
    with pytest.raises(ValueError):
        screen_cg_sensitivity(
            mass_kg=1500, wheelbase_mm=2750, track_width_mm=1700,
            cg_heights_mm=[400], lateral_accel_mps2=-1,
        )


def test_screen_for_vehicle_default_sweep():
    v = build_sample_fleet()[0]
    s = screen_cg_sensitivity_for(v)
    assert s.vehicle_id == v.id
    assert len(s.rows) >= 1
    base = v.chassis.cg_height_mm
    assert any(r.cg_height_mm == round(base, 1) for r in s.rows)


def test_output_labelled_and_clean():
    s = screen_cg_sensitivity(
        mass_kg=1500, wheelbase_mm=2750, track_width_mm=1700, cg_heights_mm=[400],
    )
    assert isinstance(s, CgSensitivityScreening)
    assert s.label is DataLabel.LOW_FIDELITY_SCREENING
    assert s.confidence is Confidence.LOW
    assert check_text(s.notes) == []
