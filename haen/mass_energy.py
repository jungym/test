"""04_mass_energy — mass and energy comparison across branches.

Aggregates vehicle mass breakdowns and energy-storage figures and produces
side-by-side comparison tables. All figures derive from the planning assumptions
in the vehicle definitions and are intended for human review.
"""

from __future__ import annotations

import pandas as pd

from .governance import Confidence, DataLabel
from .vehicle_definition import EnergyItem, VehicleDefinition


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
    cols = ["name", "group", "mass_kg", "unit", "pct_of_curb",
            "label", "source_type", "confidence", "assumption_notes", "metadata_complete"]
    if not vehicle.mass_breakdown:
        return pd.DataFrame(columns=cols)
    total = vehicle.curb_mass_kg
    rows = [
        {
            "name": item.name,
            "group": item.group,
            "mass_kg": round(item.mass_kg, 1),
            "unit": item.unit,
            "pct_of_curb": round(100.0 * item.mass_kg / total, 1) if total else 0.0,
            "label": item.label.value,
            "source_type": item.source_type,
            "confidence": item.confidence.value,
            "assumption_notes": item.assumption_notes,
            "metadata_complete": item.metadata_complete(),
        }
        for item in vehicle.mass_breakdown
    ]
    return pd.DataFrame(rows)


def energy_line_items(vehicle: VehicleDefinition) -> list[EnergyItem]:
    """Derive labelled energy line items from a vehicle's energy storage.

    Each item carries value/unit and governance metadata (label/source_type/
    confidence/assumption_notes). These are planning assumptions, not validated
    figures.
    """
    es = vehicle.energy_storage
    return [
        EnergyItem(
            name="usable_energy",
            value=round(es.usable_energy_kwh, 2),
            unit="kWh",
            label=DataLabel.ASSUMPTION,
            source_type="branch_assumption",
            confidence=Confidence.LOW,
            assumption_notes=f"Usable energy for {es.storage_type} (planning assumption).",
        ),
        EnergyItem(
            name="gravimetric_energy_density",
            value=round(es.gravimetric_density_wh_per_kg, 2),
            unit="Wh/kg",
            label=DataLabel.ASSUMPTION,
            source_type="branch_assumption",
            confidence=Confidence.LOW,
            assumption_notes="System-level gravimetric density (planning assumption).",
        ),
        EnergyItem(
            name="implied_storage_mass",
            value=round(es.storage_mass_kg, 1),
            unit="kg",
            label=DataLabel.CALCULATED,
            source_type="calculated",
            confidence=Confidence.LOW,
            assumption_notes="Derived = usable_energy / gravimetric_density.",
        ),
        EnergyItem(
            name="refill_time",
            value=round(es.refill_time_min, 1),
            unit="min",
            label=DataLabel.ASSUMPTION,
            source_type="branch_assumption",
            confidence=Confidence.LOW,
            assumption_notes="Refill/recharge time (planning assumption).",
        ),
    ]


def energy_line_items_table(vehicle: VehicleDefinition) -> pd.DataFrame:
    """Labelled energy line items for a single vehicle as a DataFrame."""
    rows = [
        {
            "name": it.name,
            "value": it.value,
            "unit": it.unit,
            "label": it.label.value,
            "source_type": it.source_type,
            "confidence": it.confidence.value,
            "assumption_notes": it.assumption_notes,
            "metadata_complete": it.metadata_complete(),
        }
        for it in energy_line_items(vehicle)
    ]
    return pd.DataFrame(rows)


def metadata_completeness(vehicle: VehicleDefinition) -> dict[str, int]:
    """Count complete vs incomplete metadata across mass + energy line items."""
    items = list(vehicle.mass_breakdown) + energy_line_items(vehicle)
    complete = sum(1 for it in items if it.metadata_complete())
    return {"total": len(items), "complete": complete, "incomplete": len(items) - complete}


def energy_scenario_comparison(vehicles: list[VehicleDefinition]) -> pd.DataFrame:
    """Internal energy-scenario comparison across branches (comparison only).

    Compares stored-energy and energy-mass figures for the BEV / 700bar H2 / LH2
    branches. These are planning assumptions and derived (calculated) values — NOT
    performance, range, road or supplier claims. For human review only.
    """
    rows = []
    for v in vehicles:
        es = v.energy_storage
        rows.append(
            {
                "id": v.id,
                "branch": v.branch_id,
                "branch_status": v.branch_status.value,
                "storage_type": es.storage_type,
                "usable_energy_kwh": round(es.usable_energy_kwh, 1),
                "energy_density_wh_per_kg": round(es.gravimetric_density_wh_per_kg, 1),
                "implied_storage_mass_kg": round(es.storage_mass_kg, 1),
                "refill_time_min": round(es.refill_time_min, 1),
                "specific_energy_kwh_per_t_vehicle": round(
                    es.usable_energy_kwh / (v.curb_mass_kg / 1000.0), 2
                ),
                "energy_mass_fraction_pct": round(
                    100.0 * es.storage_mass_kg / v.curb_mass_kg, 1
                ),
            }
        )
    return pd.DataFrame(rows).set_index("id")


def energy_scenario_line_items(vehicles: list[VehicleDefinition]) -> pd.DataFrame:
    """Long-form, fully-labelled energy line items across branches (metadata-rich)."""
    rows = []
    for v in vehicles:
        for it in energy_line_items(v):
            rows.append(
                {
                    "id": v.id,
                    "branch": v.branch_id,
                    "name": it.name,
                    "value": it.value,
                    "unit": it.unit,
                    "label": it.label.value,
                    "source_type": it.source_type,
                    "confidence": it.confidence.value,
                    "assumption_notes": it.assumption_notes,
                }
            )
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
