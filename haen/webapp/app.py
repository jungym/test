"""10_webapp — Streamlit dashboard for the HAEN Hypercar Design Support AI.

Run with:

    streamlit run haen/webapp/app.py

This dashboard is a human-in-the-loop review surface. It surfaces comparisons,
simulations, packaging checks, evidence and RFIs for a person to assess. It does
not make decisions and does not certify anything.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running via `streamlit run haen/webapp/app.py` without installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pandas as pd
import streamlit as st

from haen import DISCLAIMER, __version__
from haen import design_space_explorer as dse
from haen import low_fidelity_simulation as sim
from haen import mass_energy, visualization
from haen.governance import check_text
from haen.packaging import check_envelope, detect_overlaps
from haen.rfi_builder import build_rfi
from haen.sample_data import (
    build_sample_components,
    build_sample_evidence,
    build_sample_fleet,
    build_sample_ledger,
    build_sample_partners,
)


@st.cache_data
def _load():
    fleet = build_sample_fleet()
    return fleet


def main() -> None:
    st.set_page_config(page_title="HAEN Hypercar Design Support AI", layout="wide")
    st.title("HAEN Hypercar Design Support AI")
    st.caption(f"MVP v{__version__} — human-reviewed AI-assisted design support")
    st.warning(DISCLAIMER)

    fleet = _load()
    by_id = {v.id: v for v in fleet}

    page = st.sidebar.radio(
        "Module",
        [
            "Overview",
            "Mass & energy",
            "Low-fidelity simulation",
            "Dynamics screening",
            "Branch trade-off",
            "Packaging",
            "Supplier evidence",
            "RFI builder",
            "Forbidden claim checker",
        ],
    )

    if page == "Overview":
        _page_overview(fleet)
    elif page == "Mass & energy":
        _page_mass_energy(fleet)
    elif page == "Low-fidelity simulation":
        _page_simulation(fleet)
    elif page == "Dynamics screening":
        _page_dynamics(fleet)
    elif page == "Branch trade-off":
        _page_tradeoff(fleet)
    elif page == "Packaging":
        _page_packaging(by_id)
    elif page == "Supplier evidence":
        _page_evidence()
    elif page == "RFI builder":
        _page_rfi()
    elif page == "Forbidden claim checker":
        _page_checker()


def _page_overview(fleet) -> None:
    st.header("Programme overview — GT-1 branches")
    st.write(
        "Three core architecture branches are tracked: a BEV baseline, a 700 bar "
        "hydrogen halo branch, and a liquid-hydrogen watch branch."
    )
    rows = [
        {
            "id": v.id,
            "name": v.name,
            "branch": v.branch_id,
            "status": v.branch_status.value,
            "powertrain": v.powertrain.value,
            "curb_mass_kg": round(v.curb_mass_kg),
            "usable_energy_kwh": v.energy_storage.usable_energy_kwh,
        }
        for v in fleet
    ]
    st.dataframe(pd.DataFrame(rows).set_index("id"), use_container_width=True)


def _page_mass_energy(fleet) -> None:
    st.header("Mass & energy comparison")
    df = mass_energy.compare(fleet)
    st.dataframe(df, use_container_width=True)
    metric = st.selectbox(
        "Metric to plot",
        ["curb_mass_kg", "usable_energy_kwh", "energy_storage_mass_kg",
         "power_to_weight_kw_per_t", "refill_time_min"],
    )
    st.plotly_chart(visualization.mass_energy_bar(df, metric=metric), use_container_width=True)


def _page_simulation(fleet) -> None:
    st.header("Low-fidelity simulation (indicative only)")
    st.info("Point-mass estimates. Not real-world predictions; not for certification.")
    cruise = st.slider("Cruise speed for range estimate (km/h)", 60, 160, 100, 10)
    results = sim.simulate_all(fleet, cruise_kph=cruise)
    df = pd.DataFrame(
        [
            {
                "id": r.vehicle_id,
                "top_speed_kph": r.top_speed_kph,
                "0-100 s": r.zero_to_100_s,
                "range_km": r.estimated_range_km,
                "kWh/100km": r.avg_consumption_kwh_per_100km,
                "drivetrain_eff": r.drivetrain_efficiency,
            }
            for r in results
        ]
    ).set_index("id")
    st.dataframe(df, use_container_width=True)
    for r in results:
        for w in r.warnings:
            st.warning(f"{r.vehicle_id}: {w}")


def _page_dynamics(fleet) -> None:
    st.header("Dynamics screening (low-fidelity)")
    st.info(
        "Braking + load-transfer screening only. Idealized rigid-body models — "
        "NOT brake-system design, tyre models, suspension kinematics, aero, or "
        "vehicle-dynamics validation. All values are low_fidelity_screening."
    )
    rows = []
    for v in fleet:
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
    st.dataframe(pd.DataFrame(rows).set_index("id"), use_container_width=True)

    st.subheader("CG-sensitivity sweep")
    vid = st.selectbox("Vehicle", [v.id for v in fleet])
    vehicle = {v.id: v for v in fleet}[vid]
    sweep = sim.screen_cg_sensitivity_for(vehicle)
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "cg_height_mm": r.cg_height_mm,
                    "long_load_transfer_N": r.longitudinal_load_transfer_n,
                    "lat_load_transfer_N": r.lateral_load_transfer_n,
                }
                for r in sweep.rows
            ]
        ).set_index("cg_height_mm"),
        use_container_width=True,
    )


def _page_tradeoff(fleet) -> None:
    st.header("Architecture branch trade-off (advisory)")
    result = dse.score_branches(fleet)
    st.subheader("Comparison table")
    st.dataframe(result.table, use_container_width=True)
    st.subheader("Weighted ranking")
    st.dataframe(result.ranking.to_frame(), use_container_width=True)
    st.caption(
        "Weights: " + ", ".join(f"{c.label} {c.weight:.0%} "
                                f"({'↑' if c.higher_is_better else '↓'})"
                                for c in result.criteria)
    )
    keys = ["estimated_range_km", "zero_to_100_s", "curb_mass_kg",
            "refill_time_min", "power_to_weight_kw_per_t"]
    st.plotly_chart(visualization.tradeoff_radar(result.table, keys), use_container_width=True)


def _page_packaging(by_id) -> None:
    st.header("Packaging check")
    vid = st.selectbox("Vehicle (for envelope)", list(by_id))
    components = build_sample_components()
    st.plotly_chart(visualization.packaging_topview(components), use_container_width=True)

    overlaps = detect_overlaps(components)
    st.subheader("Interference (overlap) detection")
    if overlaps:
        st.error(f"{len(overlaps)} interference(s) detected")
        st.dataframe(
            pd.DataFrame(
                [
                    {"a": o.a, "b": o.b, "overlap_volume_m3": round(o.overlap_volume_m3, 4)}
                    for o in overlaps
                ]
            ),
            use_container_width=True,
        )
    else:
        st.success("No rigid-body interferences detected (low-fidelity AABB check).")

    violations = check_envelope(components, by_id[vid])
    st.subheader("Envelope check")
    if violations:
        st.warning(f"{len(violations)} envelope violation(s)")
        st.dataframe(
            pd.DataFrame([{"component": v.component, "axis": v.axis,
                           "amount_mm": round(v.amount_mm, 1)} for v in violations]),
            use_container_width=True,
        )
    else:
        st.success("All components fit within the external envelope (approximate).")


def _page_evidence() -> None:
    st.header("Supplier evidence register")
    st.info("No supplier figure is treated as confirmed. Verification is a human step.")
    evidence = build_sample_evidence()
    st.dataframe(evidence.to_dataframe(), use_container_width=True)
    st.write("Coverage by verification state:")
    st.json(evidence.coverage_summary())

    st.subheader("Partner engagement registry")
    st.caption(
        "Engagement status is governance metadata only — not a confirmed or "
        "selected supplier."
    )
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "name": p.name,
                    "engagement_status": p.engagement_status.value,
                    "domain": p.domain,
                    "rfi_level": p.rfi_level,
                    "branch": p.branch,
                }
                for p in build_sample_partners()
            ]
        ).set_index("name"),
        use_container_width=True,
    )


def _page_rfi() -> None:
    st.header("RFI builder")
    branch = st.selectbox("Branch", ["all", "GT-1", "GT-1H", "GT-1H-LH2"])
    rfi = build_rfi(
        title="GT-1 programme RFI",
        branch=branch,
        ledger=build_sample_ledger(),
        evidence=build_sample_evidence(),
        expected_components=["Battery pack", "700 bar H2 tanks", "Fuel-cell stack", "Brakes"],
    )
    st.markdown(rfi.to_markdown())
    st.download_button("Download RFI (Markdown)", rfi.to_markdown(),
                       file_name=f"rfi_{branch}.md")


def _page_checker() -> None:
    st.header("Forbidden claim checker")
    st.write("Paste text (e.g. marketing copy or a report) to scan for forbidden claims.")
    text = st.text_area("Text to scan", height=200,
                        value="The GT-1 is road legal and crash safe.")
    if st.button("Scan"):
        findings = check_text(text)
        if not findings:
            st.success("No forbidden claims found.")
        else:
            st.error(f"{len(findings)} forbidden claim(s) found:")
            st.dataframe(
                pd.DataFrame(
                    [
                        {"rule": f.rule_id, "claim": f.label, "match": f.matched_text,
                         "line": f.line, "why": f.explanation}
                        for f in findings
                    ]
                ),
                use_container_width=True,
            )


# Streamlit runs this script with __name__ == "__main__".
if __name__ == "__main__":
    main()
