"""09_report_builder — entry validation dossier builder.

Assembles outputs from the other modules into a single Markdown "entry validation
dossier" using the template in ``templates/``. Every generated dossier is passed
through the governance forbidden-claim checker before it is returned, so the
system cannot emit a dossier containing a forbidden claim.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from . import DISCLAIMER
from . import design_space_explorer as dse
from . import low_fidelity_simulation as sim
from . import mass_energy
from .governance import AssumptionLedger, assert_clean, check_text
from .rfi_builder import RFI
from .supplier_evidence import SupplierEvidenceTable
from .vehicle_definition import VehicleDefinition

_TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "entry_validation_dossier.md.tmpl"


def _df_to_md(df: pd.DataFrame, *, index: bool = True) -> str:
    if df.empty:
        return "_No data._"
    try:
        return df.to_markdown(index=index)
    except ImportError:  # tabulate not installed — fall back to a plain table
        return "```\n" + df.to_string(index=index) + "\n```"


def _vehicle_md(v: VehicleDefinition) -> str:
    d = v.dimensions
    return "\n".join(
        [
            f"- **ID / name:** {v.id} — {v.name}",
            f"- **Branch:** {v.branch_id} ({v.branch_status.value})",
            f"- **Powertrain:** {v.powertrain.value}",
            f"- **Occupants:** {v.occupants}",
            f"- **Dimensions (L×W×H):** {d.length_mm:.0f} × {d.width_mm:.0f} × "
            f"{d.height_mm:.0f} mm, wheelbase {d.wheelbase_mm:.0f} mm",
            f"- **Curb mass (estimated):** {v.curb_mass_kg:.0f} kg",
            f"- **Peak power:** {v.powerplant.peak_power_kw:.0f} kW "
            f"({v.power_to_weight_kw_per_t():.0f} kW/t)",
            f"- **Usable energy:** {v.energy_storage.usable_energy_kwh:.0f} kWh "
            f"({v.energy_storage.storage_type})",
        ]
    )


def _sim_md(results: list[sim.SimResult]) -> str:
    df = pd.DataFrame(
        [
            {
                "id": r.vehicle_id,
                "top_speed_kph": r.top_speed_kph,
                "0-100_s": r.zero_to_100_s,
                "range_km": r.estimated_range_km,
                "kwh/100km": r.avg_consumption_kwh_per_100km,
            }
            for r in results
        ]
    ).set_index("id")
    note = (
        "\n\n_Low-fidelity point-mass estimates; not real-world predictions and "
        "not for certification use._"
    )
    return _df_to_md(df) + note


def build_dossier(
    *,
    programme: str,
    branch: str,
    vehicles: list[VehicleDefinition],
    primary_vehicle: VehicleDefinition | None = None,
    evidence: SupplierEvidenceTable | None = None,
    ledger: AssumptionLedger | None = None,
    rfi: RFI | None = None,
    template_path: Path | None = None,
) -> str:
    """Build the entry validation dossier as Markdown.

    Raises :class:`~haen.governance.ForbiddenClaimError` if the assembled text
    contains any forbidden claim (it should not, by construction).
    """
    primary = primary_vehicle or vehicles[0]
    tmpl = (template_path or _TEMPLATE).read_text(encoding="utf-8")

    me_df = mass_energy.compare(vehicles)
    sim_results = sim.simulate_all(vehicles)
    tradeoff = dse.score_branches(vehicles)
    rank_df = tradeoff.ranking.to_frame()

    supplier_md = (
        _df_to_md(evidence.to_dataframe()) if evidence is not None else "_No evidence on file._"
    )
    if ledger is not None:
        led_df = pd.DataFrame(ledger.to_records())
        assumptions_md = _df_to_md(led_df, index=False) if not led_df.empty else "_No assumptions recorded._"
    else:
        assumptions_md = "_No assumptions recorded._"

    if rfi is not None:
        rfi_md = f"{len(rfi.items)} open item(s). See generated RFI document for detail."
    else:
        rfi_md = "_No RFI generated._"

    packaging_md = (
        "_Packaging check not included in this dossier build; run the packaging "
        "module and attach results._"
    )

    text = tmpl.format(
        programme=programme,
        generated=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        branch=branch,
        disclaimer=DISCLAIMER,
        vehicle_definition=_vehicle_md(primary),
        mass_energy=_df_to_md(me_df),
        simulation=_sim_md(sim_results),
        tradeoff=_df_to_md(rank_df),
        packaging=packaging_md,
        supplier_evidence=supplier_md,
        assumptions=assumptions_md,
        rfi=rfi_md,
    )

    assert_clean(text)  # governance gate
    return text


def save_dossier(text: str, path: str | Path) -> Path:
    """Write a dossier to disk after a final governance check."""
    findings = check_text(text)
    if findings:
        raise ValueError(f"refusing to save dossier with forbidden claims: {findings}")
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    return out
