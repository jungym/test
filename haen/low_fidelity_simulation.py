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

import numpy as np

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
