"""Tests for Review Gate 2 Item 2 — braking screening output.

Screening calculation only (idealized constant-friction point model). These
tests verify deterministic outputs, input validation, the governance label, and
that no forbidden claims are introduced. They also confirm Item 1 (gate-status)
remains intact.
"""


import pytest

from haen import low_fidelity_simulation as sim
from haen.governance import Confidence, DataLabel, check_text
from haen.low_fidelity_simulation import BrakingScreening, screen_braking
from haen.vehicle_definition import GateStatus, load_branches


# --------------------------------------------------------------------------- #
# Deterministic outputs
# --------------------------------------------------------------------------- #
def test_known_assumptions_deterministic():
    r = screen_braking(initial_speed_kph=100.0, tyre_friction_coefficient=1.0, gravity_mps2=9.81)
    # deceleration = mu * g = 9.81 m/s^2
    assert r.deceleration_mps2 == pytest.approx(9.81, abs=1e-3)
    # v = 100/3.6 = 27.7778 m/s; d = v^2 / (2*9.81) = 39.33 m
    expected = (100.0 / 3.6) ** 2 / (2 * 9.81)
    assert r.stopping_distance_m == pytest.approx(round(expected, 2), abs=1e-2)


def test_lower_friction_gives_longer_stopping_distance():
    high_mu = screen_braking(initial_speed_kph=100, tyre_friction_coefficient=1.0)
    low_mu = screen_braking(initial_speed_kph=100, tyre_friction_coefficient=0.8)
    assert low_mu.stopping_distance_m > high_mu.stopping_distance_m
    assert low_mu.deceleration_mps2 < high_mu.deceleration_mps2


def test_repeatable():
    a = screen_braking(initial_speed_kph=120, tyre_friction_coefficient=0.9)
    b = screen_braking(initial_speed_kph=120, tyre_friction_coefficient=0.9)
    assert a == b


def test_mass_independent_under_model():
    # Two "vehicles" with the same assumptions yield identical screening output.
    a = screen_braking(initial_speed_kph=100, tyre_friction_coefficient=1.0, vehicle_id="heavy")
    b = screen_braking(initial_speed_kph=100, tyre_friction_coefficient=1.0, vehicle_id="light")
    assert a.stopping_distance_m == b.stopping_distance_m


# --------------------------------------------------------------------------- #
# Input validation
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mu", [0.0, -0.1, -5])
def test_invalid_friction_fails(mu):
    with pytest.raises(ValueError):
        screen_braking(tyre_friction_coefficient=mu)


@pytest.mark.parametrize("speed", [0.0, -1, -100])
def test_zero_or_negative_speed_fails(speed):
    with pytest.raises(ValueError):
        screen_braking(initial_speed_kph=speed)


def test_non_positive_gravity_fails():
    with pytest.raises(ValueError):
        screen_braking(gravity_mps2=0)


# --------------------------------------------------------------------------- #
# Governance labelling
# --------------------------------------------------------------------------- #
def test_output_labelled_low_fidelity_screening():
    r = screen_braking()
    assert isinstance(r, BrakingScreening)
    assert r.label is DataLabel.LOW_FIDELITY_SCREENING
    assert r.label.value == "low_fidelity_screening"
    assert r.confidence is Confidence.LOW
    assert r.source_type  # non-empty source_type present


def test_assumptions_are_exposed():
    r = screen_braking(initial_speed_kph=80, tyre_friction_coefficient=0.95)
    assert r.assumptions == {
        "initial_speed_kph": 80.0,
        "tyre_friction_coefficient": 0.95,
        "gravity_mps2": sim.G,
    }


def test_data_label_allowed_values():
    expected = {
        "verified", "public_source", "calculated", "assumption",
        "target", "placeholder", "unknown", "low_fidelity_screening",
    }
    assert {m.value for m in DataLabel} == expected


# --------------------------------------------------------------------------- #
# No forbidden claims
# --------------------------------------------------------------------------- #
def test_braking_output_has_no_forbidden_claims():
    r = screen_braking()
    assert check_text(r.notes) == []
    rendered = (
        f"Braking screening for {r.vehicle_id or 'concept'}: "
        f"decel {r.deceleration_mps2} m/s^2, stopping {r.stopping_distance_m} m "
        f"[{r.label.value}, confidence={r.confidence.value}, "
        f"source={r.source_type}]. {r.notes}"
    )
    assert check_text(rendered) == []


def test_data_label_enum_is_governance_clean():
    for m in DataLabel:
        assert check_text(m.value) == []
    assert check_text(DataLabel.__doc__ or "") == []


# --------------------------------------------------------------------------- #
# Item 1 (gate-status) remains intact
# --------------------------------------------------------------------------- #
def test_gate_status_item1_still_intact():
    branches = load_branches()
    assert branches["GT-1"].gate_status is GateStatus.IN_PROGRESS
    assert branches["GT-1H"].gate_status is GateStatus.RFI_CANDIDATE
    assert branches["GT-1H-LH2"].gate_status is GateStatus.WATCH_BRANCH
