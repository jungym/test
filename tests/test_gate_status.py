"""Tests for S-1: structured per-branch gate-status field (governance metadata).

Covers valid/invalid enum handling, deterministic missing-field default,
serialization, and that no forbidden claims are introduced by the new field.
"""

import textwrap

import pytest
import yaml
from pydantic import ValidationError

from haen.governance import check_text
from haen.vehicle_definition import (
    Branch,
    EnergyStorage,
    GateStatus,
    load_branches,
)


def _branch(**kw) -> Branch:
    energy = EnergyStorage(
        storage_type="battery",
        usable_energy_kwh=50,
        gravimetric_density_wh_per_kg=150,
        refill_time_min=20,
    )
    defaults = dict(
        id="TEST-1",
        name="test branch",
        status="baseline",
        powertrain="bev",
        description="desc",
        energy=energy,
        peak_power_kw=300,
        drivetrain="awd",
    )
    defaults.update(kw)
    return Branch(**defaults)


_MINIMAL_YAML = textwrap.dedent(
    """
    branches:
      - id: TEST-1
        name: test branch
        status: baseline
        powertrain: bev
        description: desc
        energy:
          storage_type: battery
          usable_energy_kwh: 50
          gravimetric_density_wh_per_kg: 150
          refill_time_min: 20
        powertrain_detail:
          peak_power_kw: 300
          drivetrain: awd
        notes: ""
    """
)


# --------------------------------------------------------------------------- #
# Valid enum values
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("member", list(GateStatus))
def test_all_enum_values_accepted(member):
    b = _branch(gate_status=member)
    assert b.gate_status is member


def test_string_value_coerced_to_enum():
    b = _branch(gate_status="passed")
    assert b.gate_status is GateStatus.PASSED


def test_expected_enum_members_present():
    # The S-1 candidate set must exist.
    expected = {
        "not_started", "in_progress", "blocked", "watch_branch", "rfi_candidate",
        "review_required", "gated", "passed", "closed", "superseded",
    }
    assert {m.value for m in GateStatus} == expected


def test_seed_branches_have_expected_gate_status():
    branches = load_branches()
    assert branches["GT-1"].gate_status is GateStatus.IN_PROGRESS
    assert branches["GT-1H"].gate_status is GateStatus.RFI_CANDIDATE
    assert branches["GT-1H-LH2"].gate_status is GateStatus.WATCH_BRANCH


# --------------------------------------------------------------------------- #
# Invalid values
# --------------------------------------------------------------------------- #
def test_invalid_value_rejected_on_model():
    with pytest.raises(ValidationError):
        _branch(gate_status="not_a_real_status")


def test_invalid_value_rejected_on_load(tmp_path):
    bad = yaml.safe_load(_MINIMAL_YAML)
    bad["branches"][0]["gate_status"] = "bogus"
    f = tmp_path / "bad.yaml"
    f.write_text(yaml.safe_dump(bad), encoding="utf-8")
    with pytest.raises(ValueError):
        load_branches(f)


# --------------------------------------------------------------------------- #
# Deterministic missing-field behaviour
# --------------------------------------------------------------------------- #
def test_default_is_not_started_on_model():
    assert _branch().gate_status is GateStatus.NOT_STARTED


def test_missing_field_defaults_deterministically_on_load(tmp_path):
    f = tmp_path / "minimal.yaml"
    f.write_text(_MINIMAL_YAML, encoding="utf-8")
    branches = load_branches(f)
    assert branches["TEST-1"].gate_status is GateStatus.NOT_STARTED


# --------------------------------------------------------------------------- #
# Serialization
# --------------------------------------------------------------------------- #
def test_serialized_output_includes_gate_status():
    b = load_branches()["GT-1H-LH2"]
    dumped = b.model_dump()
    assert "gate_status" in dumped
    assert dumped["gate_status"] == GateStatus.WATCH_BRANCH

    json_dumped = b.model_dump(mode="json")
    assert json_dumped["gate_status"] == "watch_branch"


# --------------------------------------------------------------------------- #
# Governance: no forbidden claims introduced
# --------------------------------------------------------------------------- #
def test_gate_status_values_are_governance_clean():
    for m in GateStatus:
        assert check_text(m.value) == [], f"enum value {m.value!r} trips checker"
        assert check_text(m.name) == []


def test_gate_status_docstring_and_seed_yaml_clean():
    assert check_text(GateStatus.__doc__ or "") == []
    # The seed catalogue (including the new gate_status lines) stays clean.
    from haen.vehicle_definition import _BRANCHES_FILE

    assert check_text(_BRANCHES_FILE.read_text(encoding="utf-8")) == []
