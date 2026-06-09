"""04_mass_energy — mass and energy comparison across branches.

Aggregates vehicle mass breakdowns and energy-storage figures and produces
side-by-side comparison tables. All figures derive from the planning assumptions
in the vehicle definitions and are intended for human review.
"""

from __future__ import annotations

import pandas as pd

from .vehicle_definition import VehicleDefinition


def mass_summary(vehicle: VehicleDefinition) -> dict[str, float]:
    """Return key mass metrics for a single vehicle (kg unless noted)."""
    by_group = vehicle.mass_by_group
    return {
        "curb_mass_kg": round(vehicle.curb_mass_kg, 1),
        "energy_storage_mass_kg": round(vehicle.energy_storage.storage_mass_kg, 1),
        "structure_mass_kg": round(by_group.get("structure", 0.0), 1),
        "powertrain_mass_kg": round(by_group.get("powertrain", 0.0), 1),
        "power_to_weight_kw_per_t": round(vehicle.power_to_weight_kw_per_t(), 1),
    }


def energy_summary(vehicle: VehicleDefinition) -> dict[str, float]:
    """Return key energy metrics for a single vehicle."""
    es = vehicle.energy_storage
    return {
        "usable_energy_kwh": round(es.usable_energy_kwh, 1),
        "energy_density_wh_per_kg": round(es.gravimetric_density_wh_per_kg, 1),
        "refill_time_min": round(es.refill_time_min, 1),
        "specific_energy_kwh_per_t_vehicle": round(
            es.usable_energy_kwh / (vehicle.curb_mass_kg / 1000.0), 2
        ),
    }


def compare(vehicles: list[VehicleDefinition]) -> pd.DataFrame:
    """Build a mass + energy comparison table across vehicles (one row each)."""
    rows = []
    for v in vehicles:
        row = {
            "id": v.id,
            "name": v.name,
            "branch": v.branch_id,
            "branch_status": v.branch_status.value,
            "powertrain": v.powertrain.value,
            **mass_summary(v),
            **energy_summary(v),
        }
        rows.append(row)
    df = pd.DataFrame(rows).set_index("id")
    return df


def mass_breakdown_table(vehicle: VehicleDefinition) -> pd.DataFrame:
    """Mass breakdown for a single vehicle, with percentage of curb mass."""
    if not vehicle.mass_breakdown:
        return pd.DataFrame(columns=["name", "group", "mass_kg", "pct_of_curb"])
    total = vehicle.curb_mass_kg
    rows = [
        {
            "name": item.name,
            "group": item.group,
            "mass_kg": round(item.mass_kg, 1),
            "pct_of_curb": round(100.0 * item.mass_kg / total, 1) if total else 0.0,
        }
        for item in vehicle.mass_breakdown
    ]
    return pd.DataFrame(rows)


def delta_vs_baseline(vehicles: list[VehicleDefinition], baseline_id: str) -> pd.DataFrame:
    """Mass/energy deltas of each vehicle relative to a chosen baseline."""
    df = compare(vehicles)
    if baseline_id not in df.index:
        raise KeyError(f"baseline_id '{baseline_id}' not found among vehicles")
    numeric = df.select_dtypes("number")
    base = numeric.loc[baseline_id]
    delta = numeric.subtract(base)
    delta = delta.add_suffix("_delta")
    return df.join(delta)
