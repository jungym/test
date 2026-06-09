"""01_vehicle_definition — Pydantic schemas and validation.

Defines the canonical, validated data model for a vehicle concept and its
architecture branch. All numeric inputs are early-stage planning values; the
schema enforces physical sanity (positive masses, plausible ranges) but makes no
claim about correctness, feasibility or completeness of any concept.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, NonNegativeFloat, PositiveFloat, field_validator, model_validator

_DATA_DIR = Path(__file__).resolve().parent / "data"
_BRANCHES_FILE = _DATA_DIR / "branches.yaml"


class Powertrain(str, Enum):
    BEV = "bev"
    H2_FUEL_CELL = "h2_fuel_cell"
    H2_ICE = "h2_ice"


class BranchStatus(str, Enum):
    BASELINE = "baseline"
    HALO = "halo"
    WATCH = "watch"


class GateStatus(str, Enum):
    """Structured lifecycle / review-gate status for a branch (S-1).

    This is **governance metadata only** — it records where a branch sits in the
    human review/gate process. It carries **no engineering-validation meaning**
    and makes no assertion of road-legality, homologation readiness,
    crashworthiness, production feasibility, supplier confirmation, design
    completeness, certifiability, or real-world validation. ``passed``/``gated``
    refer strictly to a *review gate* being cleared in process terms, not to any
    engineering claim.
    """

    NOT_STARTED = "not_started"        # no gate activity yet (default)
    IN_PROGRESS = "in_progress"        # actively being worked
    BLOCKED = "blocked"                # progress blocked by a dependency
    WATCH_BRANCH = "watch_branch"      # monitored only, not actively developed
    RFI_CANDIDATE = "rfi_candidate"    # has open information gaps to resolve
    REVIEW_REQUIRED = "review_required"  # awaiting human review
    GATED = "gated"                    # held at a review gate pending decision
    PASSED = "passed"                  # cleared a review gate (process only)
    CLOSED = "closed"                  # no longer pursued
    SUPERSEDED = "superseded"          # replaced by another branch/item


class Dimensions(BaseModel):
    """External dimensions and key packaging hardpoints (millimetres)."""

    length_mm: PositiveFloat
    width_mm: PositiveFloat
    height_mm: PositiveFloat
    wheelbase_mm: PositiveFloat
    front_overhang_mm: NonNegativeFloat = 0.0
    rear_overhang_mm: NonNegativeFloat = 0.0
    ground_clearance_mm: PositiveFloat = 90.0

    @model_validator(mode="after")
    def _check_consistency(self) -> "Dimensions":
        if self.wheelbase_mm >= self.length_mm:
            raise ValueError("wheelbase_mm must be smaller than length_mm")
        if self.height_mm > self.length_mm:
            raise ValueError("height_mm must not exceed length_mm")
        return self


class EnergyStorage(BaseModel):
    """Usable energy and storage characteristics (planning assumptions)."""

    storage_type: str
    usable_energy_kwh: PositiveFloat
    gravimetric_density_wh_per_kg: PositiveFloat = Field(
        ..., description="System-level usable energy per kg of storage system."
    )
    refill_time_min: PositiveFloat

    @property
    def storage_mass_kg(self) -> float:
        """Implied storage-system mass from energy and gravimetric density."""
        return self.usable_energy_kwh * 1000.0 / self.gravimetric_density_wh_per_kg


class PerformanceTargets(BaseModel):
    """Aspirational performance *targets* (not guarantees)."""

    top_speed_kph: PositiveFloat = Field(..., le=550, description="Sanity-capped target.")
    zero_to_100_s_target: PositiveFloat = Field(..., le=20)
    target_range_km: PositiveFloat


class Powerplant(BaseModel):
    peak_power_kw: PositiveFloat = Field(..., le=2000)
    drivetrain: str = "awd"
    buffer_battery_kwh: NonNegativeFloat = 0.0


class ChassisGeometry(BaseModel):
    """Chassis geometry assumptions for low-fidelity dynamics screening.

    All values are planning **assumptions**, not measured data. They are consumed
    only by the low-fidelity load-transfer / CG-sensitivity screening and imply no
    vehicle-dynamics validation of any kind.
    """

    cg_height_mm: PositiveFloat = Field(400.0, le=2000, description="CG height above ground (assumption).")
    track_width_mm: PositiveFloat = Field(1700.0, le=2500, description="Average track width (assumption).")
    cg_longitudinal_bias: float = Field(
        0.47, gt=0, lt=1, description="Static fraction of weight on the front axle (assumption)."
    )


class MassItem(BaseModel):
    """A single mass contributor in the vehicle mass breakdown."""

    name: str
    mass_kg: NonNegativeFloat
    group: str = "other"  # e.g. structure, powertrain, energy, chassis, body, interior


class VehicleDefinition(BaseModel):
    """The validated definition of one vehicle concept on one branch."""

    id: str = Field(..., pattern=r"^[A-Za-z0-9._-]+$")
    name: str
    branch_id: str
    branch_status: BranchStatus
    powertrain: Powertrain
    occupants: int = Field(2, ge=1, le=4)

    dimensions: Dimensions
    energy_storage: EnergyStorage
    powerplant: Powerplant
    performance_targets: PerformanceTargets

    aero_cd: PositiveFloat = Field(0.35, le=1.2, description="Drag coefficient.")
    frontal_area_m2: PositiveFloat = Field(1.9, le=4.0)
    rolling_resistance_coeff: PositiveFloat = Field(0.011, le=0.05)

    # Chassis geometry assumptions for low-fidelity dynamics screening. Optional
    # with deterministic defaults so existing behaviour is preserved.
    chassis: ChassisGeometry = Field(default_factory=ChassisGeometry)

    mass_breakdown: list[MassItem] = Field(default_factory=list)
    glider_mass_kg: NonNegativeFloat = Field(
        900.0, description="Mass of everything except energy storage; fallback if no breakdown."
    )

    @field_validator("branch_id")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @property
    def curb_mass_kg(self) -> float:
        """Total curb mass.

        Uses the explicit mass breakdown when present; otherwise falls back to
        glider mass plus the implied energy-storage mass.
        """
        if self.mass_breakdown:
            return sum(item.mass_kg for item in self.mass_breakdown)
        return self.glider_mass_kg + self.energy_storage.storage_mass_kg

    @property
    def mass_by_group(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for item in self.mass_breakdown:
            out[item.group] = out.get(item.group, 0.0) + item.mass_kg
        return out

    def power_to_weight_kw_per_t(self) -> float:
        return self.powerplant.peak_power_kw / (self.curb_mass_kg / 1000.0)


class Branch(BaseModel):
    """An architecture branch loaded from the seed catalogue."""

    id: str
    name: str
    status: BranchStatus
    powertrain: Powertrain
    description: str
    energy: EnergyStorage
    peak_power_kw: PositiveFloat
    drivetrain: str
    buffer_battery_kwh: NonNegativeFloat = 0.0
    notes: str = ""
    # Governance metadata (S-1): lifecycle/review-gate status. Defaults to
    # NOT_STARTED when absent so behaviour is deterministic. Not an engineering
    # claim — see GateStatus docstring.
    gate_status: GateStatus = GateStatus.NOT_STARTED


def load_branches(path: str | Path | None = None) -> dict[str, Branch]:
    """Load and validate the seed architecture branches keyed by id."""
    file = Path(path) if path else _BRANCHES_FILE
    raw = yaml.safe_load(file.read_text(encoding="utf-8"))
    branches: dict[str, Branch] = {}
    for entry in raw["branches"]:
        energy = EnergyStorage(
            storage_type=entry["energy"]["storage_type"],
            usable_energy_kwh=entry["energy"]["usable_energy_kwh"],
            gravimetric_density_wh_per_kg=entry["energy"]["gravimetric_density_wh_per_kg"],
            refill_time_min=entry["energy"]["refill_time_min"],
        )
        pd = entry["powertrain_detail"]
        branch = Branch(
            id=entry["id"],
            name=entry["name"],
            status=BranchStatus(entry["status"]),
            powertrain=Powertrain(entry["powertrain"]),
            description=entry["description"],
            energy=energy,
            peak_power_kw=pd["peak_power_kw"],
            drivetrain=pd["drivetrain"],
            buffer_battery_kwh=pd.get("buffer_battery_kwh", 0.0),
            notes=entry.get("notes", ""),
            # Missing gate_status -> deterministic NOT_STARTED default.
            gate_status=GateStatus(entry.get("gate_status", GateStatus.NOT_STARTED.value)),
        )
        branches[branch.id] = branch
    return branches


def vehicle_from_branch(
    branch: Branch,
    *,
    id: str,
    name: str,
    dimensions: Dimensions,
    performance_targets: PerformanceTargets,
    glider_mass_kg: float = 900.0,
    **overrides,
) -> VehicleDefinition:
    """Construct a :class:`VehicleDefinition` seeded from a branch.

    A convenience that wires up a starting concept from a branch's powertrain and
    energy assumptions. The result is still just a starting point for human review.
    """
    return VehicleDefinition(
        id=id,
        name=name,
        branch_id=branch.id,
        branch_status=branch.status,
        powertrain=branch.powertrain,
        dimensions=dimensions,
        energy_storage=branch.energy,
        powerplant=Powerplant(
            peak_power_kw=branch.peak_power_kw,
            drivetrain=branch.drivetrain,
            buffer_battery_kwh=branch.buffer_battery_kwh,
        ),
        performance_targets=performance_targets,
        glider_mass_kg=glider_mass_kg,
        **overrides,
    )
