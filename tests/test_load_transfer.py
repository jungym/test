"""Tests for Review Gate 2 Item 3 — load-transfer screening output.

Low-fidelity rigid-body load-transfer screening only. Verifies deterministic
output, validation, governance labelling, no forbidden claims, and the new
ChassisGeometry schema defaults/validation.
"""

import pytest
from pydantic import ValidationError

from haen import low_fidelity_simulation as sim
from haen.governance import Confidence, DataLabel, check_text
from haen.low_fidelity_simulation import (
    LoadTransferScreening,
    screen_load_transfer,
    screen_load_transfer_for,
)
from haen.sample_data import build_sample_fleet
from haen.vehicle_definition import ChassisGeometry


# --------------------------------------------------------------------------- #
# ChassisGeometry schema
# --------------------------------------------------------------------------- #
def test_chassis_defaults_deterministic():
    c = ChassisGeometry()
    assert c.cg_height_mm == 400.0
    assert c.track_width_mm == 1700.0
    assert 0 < c.cg_longitudinal_bias < 1


@pytest.mark.parametrize("kw", [
    {"cg_height_mm": 0},
    {"cg_height_mm": -1},
    {"track_width_mm": 0},
    {"cg_longitudinal_bias": 0},
    {"cg_longitudinal_bias": 1},
])
def test_chassis_invalid_values_rejected(kw):
    with pytest.raises(ValidationError):
        ChassisGeometry(**kw)


def test_vehicle_has_default_chassis():
    v = build_sample_fleet()[0]
    assert isinstance(v.chassis, ChassisGeometry)


# --------------------------------------------------------------------------- #
# Deterministic load-transfer output
# --------------------------------------------------------------------------- #
def test_load_transfer_known_values():
    r = screen_load_transfer(
        mass_kg=1500, cg_height_mm=400, wheelbase_mm=2750, track_width_mm=1700,
        longitudinal_decel_mps2=9.81, lateral_accel_mps2=9.81,
    )
    # long = 1500 * 9.81 * (400/2750) = 2140.4 N
    assert r.longitudinal_load_transfer_n == pytest.approx(1500 * 9.81 * (400 / 2750), abs=0.5)
    # lat = 1500 * 9.81 * (400/1700) = 3462.4 N
    assert r.lateral_load_transfer_n == pytest.approx(1500 * 9.81 * (400 / 1700), abs=0.5)


def test_higher_cg_increases_transfer():
    low = screen_load_transfer(mass_kg=1500, cg_height_mm=350, wheelbase_mm=2750, track_width_mm=1700)
    high = screen_load_transfer(mass_kg=1500, cg_height_mm=500, wheelbase_mm=2750, track_width_mm=1700)
    assert high.longitudinal_load_transfer_n > low.longitudinal_load_transfer_n
    assert high.lateral_load_transfer_n > low.lateral_load_transfer_n


def test_repeatable():
    a = screen_load_transfer(mass_kg=1500, cg_height_mm=400, wheelbase_mm=2750, track_width_mm=1700)
    b = screen_load_transfer(mass_kg=1500, cg_height_mm=400, wheelbase_mm=2750, track_width_mm=1700)
    assert a == b


def test_screen_for_vehicle():
    v = build_sample_fleet()[0]
    r = screen_load_transfer_for(v)
    assert r.vehicle_id == v.id
    assert r.mass_kg == pytest.approx(round(v.curb_mass_kg, 1))
    assert r.longitudinal_load_transfer_n > 0


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("kw", [
    {"mass_kg": 0},
    {"mass_kg": -10},
    {"cg_height_mm": 0},
    {"wheelbase_mm": 0},
    {"track_width_mm": -5},
])
def test_invalid_geometry_fails(kw):
    base = dict(mass_kg=1500, cg_height_mm=400, wheelbase_mm=2750, track_width_mm=1700)
    base.update(kw)
    with pytest.raises(ValueError):
        screen_load_transfer(**base)


def test_negative_acceleration_fails():
    with pytest.raises(ValueError):
        screen_load_transfer(
            mass_kg=1500, cg_height_mm=400, wheelbase_mm=2750, track_width_mm=1700,
            longitudinal_decel_mps2=-1,
        )


# --------------------------------------------------------------------------- #
# Governance
# --------------------------------------------------------------------------- #
def test_output_labelled_and_clean():
    r = screen_load_transfer(mass_kg=1500, cg_height_mm=400, wheelbase_mm=2750, track_width_mm=1700)
    assert isinstance(r, LoadTransferScreening)
    assert r.label is DataLabel.LOW_FIDELITY_SCREENING
    assert r.confidence is Confidence.LOW
    assert r.source_type
    assert check_text(r.notes) == []
    assert "longitudinal_decel_mps2" in r.assumptions


def test_defaults_use_assumed_accelerations():
    r = screen_load_transfer(mass_kg=1500, cg_height_mm=400, wheelbase_mm=2750, track_width_mm=1700)
    assert r.longitudinal_decel_mps2 == pytest.approx(sim.DEFAULT_LONGITUDINAL_DECEL_MPS2, abs=1e-3)
    assert r.lateral_accel_mps2 == pytest.approx(sim.DEFAULT_LATERAL_ACCEL_MPS2, abs=1e-3)
