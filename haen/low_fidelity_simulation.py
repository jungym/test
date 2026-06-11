"""05_low_fidelity_simulation — first-order longitudinal performance model.

A deliberately simple point-mass model for early comparison only. It estimates
top speed, a coarse 0-100 km/h time and indicative range from aerodynamic drag,
rolling resistance, mass, power and usable energy.

LOW FIDELITY: results ignore traction limits, gearing, thermal limits, transient
behaviour, real drive cycles and many other effects. They are not predictions of
real-world performance and must not be used for any certification purpose.
"""

from __future__ import annotations

from dataclasses import dataclass


from .governance import Confidence, DataLabel
from .vehicle_definition import VehicleDefinition

RHO_AIR = 1.225      # kg/m^3, sea-level standard
G = 9.81             # m/s^2


# Above this speed (km/h) the point-mass top-speed result is treated as a pure
# model artifact: real vehicles are limited by gearing, tyres, stability and
# safety long before this. Used only to attach a louder screening warning.
TOP_SPEED_PLAUSIBILITY_KPH = 400.0


@dataclass(frozen=True)
class SimResult:
    vehicle_id: str
    top_speed_kph: float
    zero_to_100_s: float
    estimated_range_km: float
    avg_consumption_kwh_per_100km: float
    drivetrain_efficiency: float
    notes: str = "Low-fidelity point-mass estimate; not a real-world prediction."
    warnings: tuple[str, ...] = ()

    @property
    def top_speed_is_artifact(self) -> bool:
        """True when the top-speed estimate exceeds the plausibility bound."""
        return self.top_speed_kph > TOP_SPEED_PLAUSIBILITY_KPH


def _resistive_power_w(v_ms: float, vehicle: VehicleDefinition) -> float:
    """Aerodynamic + rolling resistance power demand at speed v (W)."""
    drag = 0.5 * RHO_AIR * vehicle.aero_cd * vehicle.frontal_area_m2 * v_ms**3
    rolling = vehicle.rolling_resistance_coeff * vehicle.curb_mass_kg * G * v_ms
    return drag + rolling


def estimate_top_speed_kph(vehicle: VehicleDefinition, *, drivetrain_eff: float = 0.9) -> float:
    """Top speed where available wheel power equals resistive demand."""
    p_avail = vehicle.powerplant.peak_power_kw * 1000.0 * drivetrain_eff
    # Solve resistive_power(v) == p_avail by bisection on a monotonic function.
    lo, hi = 0.0, 200.0  # m/s upper bound (720 km/h) — generous
    for _ in range(100):
        mid = (lo + hi) / 2
        if _resistive_power_w(mid, vehicle) < p_avail:
            lo = mid
        else:
            hi = mid
    return lo * 3.6


def estimate_zero_to_100(vehicle: VehicleDefinition, *, drivetrain_eff: float = 0.9,
                         dt: float = 0.01) -> float:
    """Coarse 0-100 km/h time via forward integration of a power-limited model.

    Below a base speed, acceleration is capped to a traction-limited value to
    avoid the unphysical infinite force of a pure constant-power model at v=0.
    """
    target = 100 / 3.6  # m/s
    mass = vehicle.curb_mass_kg
    p_wheel = vehicle.powerplant.peak_power_kw * 1000.0 * drivetrain_eff
    # Assume a generous traction-limited acceleration cap (g-based) for launch.
    a_traction = 1.1 * G  # ~1.1 g launch assumption
    v, t = 0.1, 0.0       # small non-zero start to avoid divide-by-zero
    while v < target and t < 60:
        f_power = p_wheel / v
        f_resist = _resistive_power_w(v, vehicle) / v
        a = min(f_power / mass, a_traction) - f_resist / mass
        if a <= 0:
            break
        v += a * dt
        t += dt
    return round(t, 2)


def estimate_range_km(vehicle: VehicleDefinition, *, cruise_kph: float = 100.0,
                      drivetrain_eff: float = 0.9, aux_load_kw: float = 1.0) -> tuple[float, float]:
    """Indicative steady-cruise range and consumption.

    Returns ``(range_km, consumption_kwh_per_100km)``. Uses constant-speed cruise
    power plus an auxiliary load. No drive cycle, no regen modelling.
    """
    v = cruise_kph / 3.6
    p_wheel_w = _resistive_power_w(v, vehicle)
    p_battery_kw = p_wheel_w / 1000.0 / drivetrain_eff + aux_load_kw
    hours = vehicle.energy_storage.usable_energy_kwh / p_battery_kw
    range_km = hours * cruise_kph
    consumption = vehicle.energy_storage.usable_energy_kwh / range_km * 100.0
    return round(range_km, 1), round(consumption, 1)


def simulate(vehicle: VehicleDefinition, *, drivetrain_eff: float | None = None,
             cruise_kph: float = 100.0) -> SimResult:
    """Run the full low-fidelity estimate for one vehicle."""
    # Fuel-cell branches carry conversion losses; use a lower default efficiency.
    if drivetrain_eff is None:
        drivetrain_eff = 0.55 if vehicle.powertrain.value.startswith("h2") else 0.90
    top = estimate_top_speed_kph(vehicle, drivetrain_eff=drivetrain_eff)
    zero = estimate_zero_to_100(vehicle, drivetrain_eff=drivetrain_eff)
    rng, cons = estimate_range_km(vehicle, cruise_kph=cruise_kph, drivetrain_eff=drivetrain_eff)

    warnings: list[str] = []
    if round(top, 1) > TOP_SPEED_PLAUSIBILITY_KPH:
        warnings.append(
            f"Top-speed estimate {top:.0f} km/h exceeds the {TOP_SPEED_PLAUSIBILITY_KPH:.0f} "
            "km/h plausibility bound: this is a point-mass MODEL ARTIFACT (no gearing, "
            "tyre, stability or safety limits modelled), NOT a real-world prediction."
        )
    return SimResult(
        vehicle_id=vehicle.id,
        top_speed_kph=round(top, 1),
        zero_to_100_s=zero,
        estimated_range_km=rng,
        avg_consumption_kwh_per_100km=cons,
        drivetrain_efficiency=drivetrain_eff,
        warnings=tuple(warnings),
    )


def simulate_all(vehicles: list[VehicleDefinition], **kwargs) -> list[SimResult]:
    return [simulate(v, **kwargs) for v in vehicles]


# --------------------------------------------------------------------------- #
# Braking screening (Review Gate 2, Item 2)
# --------------------------------------------------------------------------- #
# Default screening assumptions — clearly assumptions, overridable by the caller.
DEFAULT_BRAKING_INITIAL_SPEED_KPH = 100.0
DEFAULT_TYRE_FRICTION_COEFFICIENT = 1.0  # assumption: dry high-performance tyre


@dataclass(frozen=True)
class BrakingScreening:
    """A low-fidelity braking *screening* estimate (idealized point model).

    This is a screening comparison aid only. It is **not** brake-system design,
    ABS/tyre validation, road testing, or homologation evidence. The stopping
    distance is an idealized estimate from a single constant-friction assumption;
    it is not measured and must not be read as a confirmed figure. Provenance is
    declared via ``source_type``/``confidence``/``label`` (governance metadata).
    """

    vehicle_id: str
    initial_speed_kph: float
    tyre_friction_coefficient: float
    gravity_mps2: float
    deceleration_mps2: float
    stopping_distance_m: float
    source_type: str = "screening_assumption"
    confidence: Confidence = Confidence.LOW
    label: DataLabel = DataLabel.LOW_FIDELITY_SCREENING
    notes: str = (
        "Low-fidelity braking screening (deceleration = mu*g; stopping distance "
        "= v^2/(2*mu*g)). Idealized constant-friction point model: ignores "
        "aerodynamics, ABS, brake bias, load transfer, downforce, regen, fade "
        "and tyre-temperature effects. Not brake-system design; the figures are "
        "screening estimates, neither measured nor a guarantee of performance."
    )

    @property
    def assumptions(self) -> dict[str, float]:
        """The labelled input assumptions behind this screening estimate."""
        return {
            "initial_speed_kph": self.initial_speed_kph,
            "tyre_friction_coefficient": self.tyre_friction_coefficient,
            "gravity_mps2": self.gravity_mps2,
        }


def screen_braking(
    *,
    initial_speed_kph: float = DEFAULT_BRAKING_INITIAL_SPEED_KPH,
    tyre_friction_coefficient: float = DEFAULT_TYRE_FRICTION_COEFFICIENT,
    gravity_mps2: float = G,
    vehicle_id: str = "",
) -> BrakingScreening:
    """Compute a low-fidelity braking screening estimate from labelled assumptions.

    Uses the idealized constant-friction model only::

        deceleration_mps2 = tyre_friction_coefficient * gravity_mps2
        stopping_distance_m = (initial_speed_mps ** 2) / (2 * deceleration_mps2)

    The result is mass-independent under this model. Raises ``ValueError`` for
    non-positive speed, friction or gravity (mirrors the positive-value
    conventions used by the schema). Screening only — see :class:`BrakingScreening`.
    """
    if initial_speed_kph <= 0:
        raise ValueError("initial_speed_kph must be positive")
    if tyre_friction_coefficient <= 0:
        raise ValueError("tyre_friction_coefficient must be positive")
    if gravity_mps2 <= 0:
        raise ValueError("gravity_mps2 must be positive")

    v_mps = initial_speed_kph / 3.6
    deceleration = tyre_friction_coefficient * gravity_mps2
    stopping_distance = v_mps**2 / (2.0 * deceleration)
    return BrakingScreening(
        vehicle_id=vehicle_id,
        initial_speed_kph=round(initial_speed_kph, 1),
        tyre_friction_coefficient=tyre_friction_coefficient,
        gravity_mps2=gravity_mps2,
        deceleration_mps2=round(deceleration, 3),
        stopping_distance_m=round(stopping_distance, 2),
    )


# --------------------------------------------------------------------------- #
# Load-transfer screening (Review Gate 2, Item 3)
# --------------------------------------------------------------------------- #
# Default screening accelerations (assumptions, overridable).
DEFAULT_LONGITUDINAL_DECEL_MPS2 = DEFAULT_TYRE_FRICTION_COEFFICIENT * G  # ~9.81
DEFAULT_LATERAL_ACCEL_MPS2 = 1.0 * G  # assumption: ~1.0 g cornering


@dataclass(frozen=True)
class LoadTransferScreening:
    """Low-fidelity static load-transfer *screening* estimate.

    Rigid-body weight-transfer magnitudes from mass, acceleration and CG height::

        longitudinal_load_transfer_n = mass * a_long * cg_height / wheelbase
        lateral_load_transfer_n      = mass * a_lat  * cg_height / track_width

    Screening only — **not** vehicle-dynamics validation, suspension kinematics,
    a tyre model, or downforce/aero. The figures are estimates, neither measured
    nor a guarantee of behaviour. Provenance is declared via
    ``source_type``/``confidence``/``label``.
    """

    vehicle_id: str
    mass_kg: float
    cg_height_mm: float
    wheelbase_mm: float
    track_width_mm: float
    longitudinal_decel_mps2: float
    lateral_accel_mps2: float
    longitudinal_load_transfer_n: float
    lateral_load_transfer_n: float
    source_type: str = "screening_assumption"
    confidence: Confidence = Confidence.LOW
    label: DataLabel = DataLabel.LOW_FIDELITY_SCREENING
    notes: str = (
        "Low-fidelity rigid-body load-transfer screening (dW = m*a*h/base). "
        "Ignores suspension kinematics, tyre behaviour, downforce, aero and "
        "transient response. Not vehicle-dynamics validation; figures are "
        "screening estimates, neither measured nor a guarantee."
    )

    @property
    def assumptions(self) -> dict[str, float]:
        return {
            "mass_kg": self.mass_kg,
            "cg_height_mm": self.cg_height_mm,
            "wheelbase_mm": self.wheelbase_mm,
            "track_width_mm": self.track_width_mm,
            "longitudinal_decel_mps2": self.longitudinal_decel_mps2,
            "lateral_accel_mps2": self.lateral_accel_mps2,
        }


def screen_load_transfer(
    *,
    mass_kg: float,
    cg_height_mm: float,
    wheelbase_mm: float,
    track_width_mm: float,
    longitudinal_decel_mps2: float = DEFAULT_LONGITUDINAL_DECEL_MPS2,
    lateral_accel_mps2: float = DEFAULT_LATERAL_ACCEL_MPS2,
    vehicle_id: str = "",
) -> LoadTransferScreening:
    """Compute low-fidelity longitudinal and lateral load transfer.

    Raises ``ValueError`` for non-positive mass/geometry or negative
    accelerations. Screening only — see :class:`LoadTransferScreening`.
    """
    if mass_kg <= 0:
        raise ValueError("mass_kg must be positive")
    if cg_height_mm <= 0:
        raise ValueError("cg_height_mm must be positive")
    if wheelbase_mm <= 0:
        raise ValueError("wheelbase_mm must be positive")
    if track_width_mm <= 0:
        raise ValueError("track_width_mm must be positive")
    if longitudinal_decel_mps2 < 0 or lateral_accel_mps2 < 0:
        raise ValueError("accelerations must be non-negative")

    long_transfer = mass_kg * longitudinal_decel_mps2 * (cg_height_mm / wheelbase_mm)
    lat_transfer = mass_kg * lateral_accel_mps2 * (cg_height_mm / track_width_mm)
    return LoadTransferScreening(
        vehicle_id=vehicle_id,
        mass_kg=round(mass_kg, 1),
        cg_height_mm=round(cg_height_mm, 1),
        wheelbase_mm=round(wheelbase_mm, 1),
        track_width_mm=round(track_width_mm, 1),
        longitudinal_decel_mps2=round(longitudinal_decel_mps2, 3),
        lateral_accel_mps2=round(lateral_accel_mps2, 3),
        longitudinal_load_transfer_n=round(long_transfer, 1),
        lateral_load_transfer_n=round(lat_transfer, 1),
    )


def screen_load_transfer_for(vehicle: VehicleDefinition, **kwargs) -> LoadTransferScreening:
    """Load-transfer screening seeded from a vehicle's mass and chassis geometry."""
    return screen_load_transfer(
        mass_kg=vehicle.curb_mass_kg,
        cg_height_mm=vehicle.chassis.cg_height_mm,
        wheelbase_mm=vehicle.dimensions.wheelbase_mm,
        track_width_mm=vehicle.chassis.track_width_mm,
        vehicle_id=vehicle.id,
        **kwargs,
    )


# --------------------------------------------------------------------------- #
# CG-sensitivity screening (Review Gate 2, Item 4)
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class CgSensitivityRow:
    """One CG-height sample in a sensitivity sweep."""

    cg_height_mm: float
    longitudinal_load_transfer_n: float
    lateral_load_transfer_n: float


@dataclass(frozen=True)
class CgSensitivityScreening:
    """Low-fidelity CG-height sensitivity *screening* sweep.

    Recomputes the rigid-body load-transfer magnitudes across a set of CG-height
    assumptions to show sensitivity. Screening only — **not** vehicle-dynamics
    validation, suspension kinematics, a tyre model, or aero/downforce.
    """

    vehicle_id: str
    mass_kg: float
    wheelbase_mm: float
    track_width_mm: float
    longitudinal_decel_mps2: float
    lateral_accel_mps2: float
    rows: tuple[CgSensitivityRow, ...]
    source_type: str = "screening_assumption"
    confidence: Confidence = Confidence.LOW
    label: DataLabel = DataLabel.LOW_FIDELITY_SCREENING
    notes: str = (
        "Low-fidelity CG-sensitivity screening: rigid-body load transfer "
        "(dW = m*a*h/base) swept over CG-height assumptions. Ignores suspension "
        "kinematics, tyre behaviour, downforce and aero. Not vehicle-dynamics "
        "validation; figures are screening estimates, neither measured nor a "
        "guarantee."
    )

    @property
    def assumptions(self) -> dict[str, float]:
        return {
            "mass_kg": self.mass_kg,
            "wheelbase_mm": self.wheelbase_mm,
            "track_width_mm": self.track_width_mm,
            "longitudinal_decel_mps2": self.longitudinal_decel_mps2,
            "lateral_accel_mps2": self.lateral_accel_mps2,
        }


def screen_cg_sensitivity(
    *,
    mass_kg: float,
    wheelbase_mm: float,
    track_width_mm: float,
    cg_heights_mm: list[float],
    longitudinal_decel_mps2: float = DEFAULT_LONGITUDINAL_DECEL_MPS2,
    lateral_accel_mps2: float = DEFAULT_LATERAL_ACCEL_MPS2,
    vehicle_id: str = "",
) -> CgSensitivityScreening:
    """Sweep CG height and report load-transfer sensitivity (screening only).

    ``cg_heights_mm`` is sorted ascending for deterministic output. Raises
    ``ValueError`` for an empty sweep, non-positive mass/geometry/CG, or negative
    accelerations.
    """
    if not cg_heights_mm:
        raise ValueError("cg_heights_mm must be a non-empty list")
    if mass_kg <= 0:
        raise ValueError("mass_kg must be positive")
    if wheelbase_mm <= 0 or track_width_mm <= 0:
        raise ValueError("wheelbase_mm and track_width_mm must be positive")
    if any(h <= 0 for h in cg_heights_mm):
        raise ValueError("all cg_heights_mm must be positive")
    if longitudinal_decel_mps2 < 0 or lateral_accel_mps2 < 0:
        raise ValueError("accelerations must be non-negative")

    rows = tuple(
        CgSensitivityRow(
            cg_height_mm=round(h, 1),
            longitudinal_load_transfer_n=round(
                mass_kg * longitudinal_decel_mps2 * (h / wheelbase_mm), 1
            ),
            lateral_load_transfer_n=round(
                mass_kg * lateral_accel_mps2 * (h / track_width_mm), 1
            ),
        )
        for h in sorted(cg_heights_mm)
    )
    return CgSensitivityScreening(
        vehicle_id=vehicle_id,
        mass_kg=round(mass_kg, 1),
        wheelbase_mm=round(wheelbase_mm, 1),
        track_width_mm=round(track_width_mm, 1),
        longitudinal_decel_mps2=round(longitudinal_decel_mps2, 3),
        lateral_accel_mps2=round(lateral_accel_mps2, 3),
        rows=rows,
    )


def screen_cg_sensitivity_for(
    vehicle: VehicleDefinition,
    *,
    cg_heights_mm: list[float] | None = None,
    deltas_mm: tuple[float, ...] = (-100, -50, 0, 50, 100),
    **kwargs,
) -> CgSensitivityScreening:
    """CG-sensitivity sweep seeded from a vehicle.

    When ``cg_heights_mm`` is not given, sweeps the vehicle's assumed CG height by
    ``deltas_mm`` (dropping any non-positive result).
    """
    base = vehicle.chassis.cg_height_mm
    if cg_heights_mm is None:
        cg_heights_mm = [base + d for d in deltas_mm if base + d > 0]
    return screen_cg_sensitivity(
        mass_kg=vehicle.curb_mass_kg,
        wheelbase_mm=vehicle.dimensions.wheelbase_mm,
        track_width_mm=vehicle.chassis.track_width_mm,
        cg_heights_mm=cg_heights_mm,
        vehicle_id=vehicle.id,
        **kwargs,
    )
