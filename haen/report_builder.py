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
from .governance import (
    AssumptionLedger,
    ReportMetadata,
    assert_clean,
    check_text,
    semantic_risk_scan,
)
from .packaging import Component, check_envelope, detect_overlaps
from .rfi_builder import RFI
from .supplier_evidence import SupplierEvidenceTable
from .vehicle_definition import VehicleDefinition, load_branches

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
                "top_speed_kph": f"{r.top_speed_kph} [!]" if r.top_speed_is_artifact
                else r.top_speed_kph,
                "0-100_s": r.zero_to_100_s,
                "range_km": r.estimated_range_km,
                "kwh/100km": r.avg_consumption_kwh_per_100km,
            }
            for r in results
        ]
    ).set_index("id")
    note = (
        "\n\n_Low-fidelity point-mass screening estimates; not real-world predictions "
        "and not for certification use. Acceleration, range and top speed ignore "
        "gearing, traction, thermal, transient and drive-cycle effects. Braking, "
        "load-transfer and CG-sensitivity are provided separately as low-fidelity "
        "screening (section 4a), not vehicle-dynamics validation._"
    )
    artifacts = [w for r in results for w in r.warnings]
    if artifacts:
        note += "\n\n**Screening artifacts flagged ([!]):**\n" + "\n".join(
            f"- {w}" for w in artifacts
        )
    return _df_to_md(df) + note


def _dynamics_screening_md(vehicles: list[VehicleDefinition]) -> str:
    """Braking + load-transfer screening per vehicle (low-fidelity only)."""
    rows = []
    for v in vehicles:
        b = sim.screen_braking(vehicle_id=v.id)
        lt = sim.screen_load_transfer_for(v)
        rows.append(
            {
                "id": v.id,
                "brake_decel_mps2": b.deceleration_mps2,
                "stopping_dist_m@100kph": b.stopping_distance_m,
                "long_load_transfer_N": lt.longitudinal_load_transfer_n,
                "lat_load_transfer_N": lt.lateral_load_transfer_n,
            }
        )
    df = pd.DataFrame(rows).set_index("id")
    note = (
        "\n\n_All values are **low_fidelity_screening** (label), source_type "
        "`screening_assumption`, confidence `low`. Braking uses mu=1.0 @ 100 km/h; "
        "load transfer uses ~1 g assumptions and the chassis CG-height/track "
        "assumptions. Idealized rigid-body models — not brake-system design, tyre "
        "models, suspension kinematics, aero/downforce, or vehicle-dynamics "
        "validation. Figures are neither measured nor a guarantee of behaviour._"
    )
    return _df_to_md(df) + note


def _packaging_md(components: list[Component] | None, vehicle: VehicleDefinition) -> str:
    """Internal packaging section: AABB extents, conflict summary, diagram refs."""
    if not components:
        return (
            "_No packaging components supplied; packaging check not included in "
            "this dossier build._"
        )
    comp_df = pd.DataFrame(
        [
            {
                "component": c.name,
                "group": c.group,
                "x_mm": f"{c.box.min_x:.0f}..{c.box.max_x:.0f}",
                "y_mm": f"{c.box.min_y:.0f}..{c.box.max_y:.0f}",
                "z_mm": f"{c.box.min_z:.0f}..{c.box.max_z:.0f}",
            }
            for c in components
        ]
    ).set_index("component")

    parts = ["**Components (axis-aligned bounding boxes, mm):**", "", _df_to_md(comp_df)]

    overlaps = detect_overlaps(components)
    if overlaps:
        conf_df = pd.DataFrame(
            [
                {"a": o.a, "b": o.b, "overlap_volume_m3": round(o.overlap_volume_m3, 4)}
                for o in overlaps
            ]
        )
        parts += ["", f"**Conflicts (interferences) detected: {len(overlaps)}**", "",
                  _df_to_md(conf_df, index=False)]
    else:
        parts += ["", "_No rigid-body interferences detected (low-fidelity AABB check)._"]

    violations = check_envelope(components, vehicle)
    if violations:
        parts += ["", f"**Envelope violations: {len(violations)}** "
                  "(component(s) protrude beyond the external envelope; see packaging module)."]
    else:
        parts += ["", "_All components fit within the external envelope (approximate)._"]

    parts += [
        "",
        "_Internal-only, low-fidelity packaging (axis-aligned bounding boxes). "
        "Interactive top/side diagrams are available via "
        "`visualization.packaging_topview` / `packaging_sideview` and the "
        "dashboard. Not CAD, and not geometric or packaging validation._",
    ]
    return "\n".join(parts)


def _mass_energy_md(vehicles: list[VehicleDefinition], primary: VehicleDefinition) -> str:
    """Mass/energy comparison plus the primary vehicle's labelled line items."""
    parts = [_df_to_md(mass_energy.compare(vehicles))]

    breakdown = mass_energy.mass_breakdown_table(primary)
    if not breakdown.empty:
        parts += [
            "", f"**{primary.id} — mass line items (with provenance):**", "",
            _df_to_md(breakdown, index=False),
        ]

    parts += [
        "", f"**{primary.id} — energy line items (with provenance):**", "",
        _df_to_md(mass_energy.energy_line_items_table(primary), index=False),
    ]

    comp = mass_energy.metadata_completeness(primary)
    parts += [
        "",
        f"_Metadata completeness for {primary.id}: {comp['complete']}/{comp['total']} "
        f"line items have full provenance ({comp['incomplete']} incomplete). Every "
        "value carries label / source_type / confidence / assumption_notes._",
    ]
    return "\n".join(parts)


def _gate_status_md(vehicles: list[VehicleDefinition]) -> str:
    """Per-branch gate-status (governance metadata) for the vehicles' branches."""
    branches = load_branches()
    seen: dict[str, str] = {}
    for v in vehicles:
        b = branches.get(v.branch_id)
        if b is not None and b.id not in seen:
            seen[b.id] = b.gate_status.value
    if not seen:
        return "_No branch gate status available._"
    df = pd.DataFrame(
        [{"branch": bid, "gate_status": status} for bid, status in seen.items()]
    ).set_index("branch")
    return _df_to_md(df)


def build_dossier(
    *,
    programme: str,
    branch: str,
    vehicles: list[VehicleDefinition],
    primary_vehicle: VehicleDefinition | None = None,
    evidence: SupplierEvidenceTable | None = None,
    ledger: AssumptionLedger | None = None,
    rfi: RFI | None = None,
    components: list[Component] | None = None,
    metadata: ReportMetadata | None = None,
    generated_at: str | None = None,
    template_path: Path | None = None,
) -> str:
    """Build the entry validation dossier as Markdown.

    The dossier is INTERNAL and human-review-required by default (see
    ``metadata``). Pass ``generated_at`` (a pre-formatted timestamp string) for
    reproducible/deterministic output. Raises
    :class:`~haen.governance.ForbiddenClaimError` if the assembled text contains
    any forbidden claim (it should not, by construction).
    """
    primary = primary_vehicle or vehicles[0]
    meta = metadata or ReportMetadata(programme=programme)
    tmpl = (template_path or _TEMPLATE).read_text(encoding="utf-8")
    generated = generated_at or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    sim_results = sim.simulate_all(vehicles)
    tradeoff = dse.score_branches(vehicles)
    rank_df = tradeoff.ranking.to_frame()

    supplier_md = (
        _df_to_md(evidence.to_dataframe()) if evidence is not None else "_No evidence on file._"
    )
    if ledger is not None:
        led_df = pd.DataFrame(ledger.to_records())
        # Drop the per-entry created_at timestamp: it is non-deterministic and
        # noise for the dossier, so removing it keeps reproducible exports stable.
        if not led_df.empty:
            led_df = led_df.drop(columns=["created_at"], errors="ignore")
        assumptions_md = _df_to_md(led_df, index=False) if not led_df.empty else "_No assumptions recorded._"
    else:
        assumptions_md = "_No assumptions recorded._"

    if rfi is not None:
        rfi_md = f"{len(rfi.items)} open item(s). See generated RFI document for detail."
    else:
        rfi_md = "_No RFI generated._"

    packaging_md = _packaging_md(components, primary)

    fields = dict(
        programme=programme,
        generated=generated,
        branch=branch,
        report_metadata=meta.banner(),
        disclaimer=DISCLAIMER,
        vehicle_definition=_vehicle_md(primary),
        mass_energy=_mass_energy_md(vehicles, primary),
        simulation=_sim_md(sim_results),
        dynamics_screening=_dynamics_screening_md(vehicles),
        tradeoff=_df_to_md(rank_df),
        gate_status=_gate_status_md(vehicles),
        packaging=packaging_md,
        supplier_evidence=supplier_md,
        assumptions=assumptions_md,
        rfi=rfi_md,
    )

    # Advisory semantic-risk review (warning-only): scan a preliminary render of
    # the dossier body, then surface the findings read-only. This never gates
    # output — the hard lexical forbidden-claim check below stays authoritative.
    preliminary = tmpl.format(semantic_risk="(pending)", **fields)
    sem = semantic_risk_scan(preliminary)
    if not sem:
        semantic_md = (
            "_No advisory semantic-risk findings. (Advisory layer only; the hard "
            "forbidden-claim gate remains authoritative and is enforced below.)_"
        )
    else:
        rows = "\n".join(
            f"| {f.line} | {f.category} | {f.snippet.replace('|', '/')} |" for f in sem
        )
        semantic_md = (
            f"{len(sem)} advisory finding(s) for human review (warning-only; "
            "the hard forbidden-claim gate remains authoritative):\n\n"
            "| Line | Category | Snippet |\n|------|----------|---------|\n" + rows
        )

    text = tmpl.format(semantic_risk=semantic_md, **fields)

    assert_clean(text)  # governance gate (hard, authoritative)
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


# --------------------------------------------------------------------------- #
# Internal release-readiness checklist (Review Gate 5, Item 9)
# --------------------------------------------------------------------------- #
_DEFAULT_GATES = {
    "gate_1": "closed",
    "gate_2": "intact",
    "gate_3": "closed",
    "gate_4": "closed",
    "gate_5": "in_progress",
}


def build_release_readiness(
    *,
    gates: dict[str, str] | None = None,
    dossier_text: str | None = None,
    validation_problems: list[str] | None = None,
    semantic_findings: int | None = None,
    completeness: dict[str, int] | None = None,
    ci_status: str = "recorded-externally",
    metadata: ReportMetadata | None = None,
) -> dict:
    """Build an internal release-readiness checklist (structured).

    "Readiness" means review-gate/process state only — **never** an engineering,
    certification, production, or external-release claim. Defaults are internal-
    only and human-review-required.
    """
    meta = metadata or ReportMetadata()
    forbidden = [f.matched_text for f in check_text(dossier_text)] if dossier_text else []
    if validation_problems is None:
        artifact_validation = "not_run"
    elif not validation_problems:
        artifact_validation = "ok"
    else:
        artifact_validation = f"{len(validation_problems)} problem(s)"
    if semantic_findings is None and dossier_text is not None:
        semantic_findings = len(semantic_risk_scan(dossier_text))
    if semantic_findings is None:
        semantic_status = "not_run"
    elif semantic_findings == 0:
        semantic_status = "none (advisory layer; hard gate authoritative)"
    else:
        semantic_status = f"{semantic_findings} advisory finding(s) for human review"
    if completeness:
        completeness_status = (
            f"{completeness.get('complete', 0)}/{completeness.get('total', 0)} "
            f"line items with full provenance"
        )
    else:
        completeness_status = "not_run"
    return {
        "gates": dict(gates or _DEFAULT_GATES),
        "ci_status": ci_status,
        "artifact_validation": artifact_validation,
        "forbidden_claim_status": "clean" if not forbidden else f"{len(forbidden)} finding(s)",
        "semantic_risk_status": semantic_status,
        "metadata_completeness": completeness_status,
        "human_review_required": meta.human_review_required,
        "external_release_allowed": meta.external_release_allowed,
        "internal_only": meta.internal_only,
        "notes": ["SafeCopy base untouched", "PR not opened"],
    }


def release_readiness_md(checklist: dict) -> str:
    """Render the readiness checklist as governance-clean internal Markdown."""
    lines = [
        "# Internal Release-Readiness Checklist (INTERNAL)",
        "",
        "_Review-gate/process status only — not an engineering, certification, "
        "production, supplier, or external-release claim. Human review required._",
        "",
        "## Gates",
    ]
    for gate, status in checklist["gates"].items():
        lines.append(f"- {gate}: **{status}**")
    lines += [
        "",
        "## Controls",
        f"- CI status: **{checklist['ci_status']}**",
        f"- Artifact validation: **{checklist['artifact_validation']}**",
        f"- Forbidden-claim status: **{checklist['forbidden_claim_status']}**",
        f"- Advisory semantic-risk: **{checklist['semantic_risk_status']}**",
        f"- Metadata completeness: **{checklist['metadata_completeness']}**",
        f"- human_review_required: **{str(checklist['human_review_required']).lower()}**",
        f"- external_release_allowed: **{str(checklist['external_release_allowed']).lower()}**",
        f"- internal_only: **{str(checklist['internal_only']).lower()}**",
        "",
        "## Notes",
    ]
    lines += [f"- {n}" for n in checklist["notes"]]
    lines.append("")
    text = "\n".join(lines)
    assert_clean(text)  # governance gate
    return text
