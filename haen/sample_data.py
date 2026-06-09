"""Sample data builders for the three core branches.

Provides a ready-to-use fleet (one vehicle concept per branch) plus a seeded
assumption ledger and supplier evidence table, so the webapp, CLI and tests have
a consistent, reviewable starting point. All values are planning assumptions.
"""

from __future__ import annotations

from datetime import date

from .governance import Assumption, AssumptionLedger, AssumptionStatus, Confidence
from .packaging import Box, Component
from .supplier_evidence import (
    EngagementStatus,
    EvidenceRecord,
    EvidenceType,
    Partner,
    SupplierEvidenceTable,
    VerificationState,
)
from .vehicle_definition import (
    Dimensions,
    MassItem,
    PerformanceTargets,
    VehicleDefinition,
    load_branches,
    vehicle_from_branch,
)

# A common GT-1 silhouette used as the starting envelope for all branches.
_DIMS = Dimensions(
    length_mm=4650,
    width_mm=2000,
    height_mm=1180,
    wheelbase_mm=2750,
    front_overhang_mm=950,
    rear_overhang_mm=950,
    ground_clearance_mm=95,
)


def build_sample_fleet() -> list[VehicleDefinition]:
    """Build one vehicle concept per core branch."""
    branches = load_branches()
    fleet: list[VehicleDefinition] = []

    # GT-1 BEV baseline — with an explicit illustrative mass breakdown.
    bev = vehicle_from_branch(
        branches["GT-1"],
        id="GT-1-c01",
        name="GT-1 BEV baseline concept",
        dimensions=_DIMS,
        performance_targets=PerformanceTargets(
            top_speed_kph=340, zero_to_100_s_target=2.6, target_range_km=450
        ),
        aero_cd=0.32,
        frontal_area_m2=1.92,
    )
    bev.mass_breakdown = [
        MassItem(name="Carbon monocoque", mass_kg=180, group="structure"),
        MassItem(name="Body panels & closures", mass_kg=120, group="body"),
        MassItem(name="Battery pack", mass_kg=bev.energy_storage.storage_mass_kg, group="energy"),
        MassItem(name="E-motors & inverters", mass_kg=190, group="powertrain"),
        MassItem(name="Suspension & wheels", mass_kg=240, group="chassis"),
        MassItem(name="Interior & occupants allowance", mass_kg=210, group="interior"),
    ]

    # GT-1H 700 bar H2 halo branch.
    h2 = vehicle_from_branch(
        branches["GT-1H"],
        id="GT-1H-c01",
        name="GT-1H 700bar H2 halo concept",
        dimensions=_DIMS,
        performance_targets=PerformanceTargets(
            top_speed_kph=340, zero_to_100_s_target=2.9, target_range_km=700
        ),
        aero_cd=0.33,
        frontal_area_m2=1.95,
        glider_mass_kg=1050.0,
    )

    # GT-1H LH2 watch branch.
    lh2 = vehicle_from_branch(
        branches["GT-1H-LH2"],
        id="GT-1H-LH2-c01",
        name="GT-1H LH2 watch concept",
        dimensions=_DIMS,
        performance_targets=PerformanceTargets(
            top_speed_kph=340, zero_to_100_s_target=2.9, target_range_km=850
        ),
        aero_cd=0.33,
        frontal_area_m2=1.95,
        glider_mass_kg=1100.0,
    )

    fleet.extend([bev, h2, lh2])
    return fleet


def build_sample_ledger() -> AssumptionLedger:
    """A seeded in-memory assumption ledger."""
    ledger = AssumptionLedger(":memory:")
    ledger.add(
        Assumption(
            key="bev.pack_density",
            statement="BEV pack-level gravimetric energy density",
            value="180",
            unit="Wh/kg",
            source="internal estimate from 2025 cell roadmap",
            confidence=Confidence.MEDIUM,
            status=AssumptionStatus.OPEN,
            branch="GT-1",
        )
    )
    ledger.add(
        Assumption(
            key="h2.tank_system_density",
            statement="700 bar H2 storage system-level energy density",
            value="95",
            unit="Wh/kg",
            source="engineering judgement",
            confidence=Confidence.LOW,
            status=AssumptionStatus.OPEN,
            branch="GT-1H",
        )
    )
    ledger.add(
        Assumption(
            key="lh2.boiloff_rate",
            statement="LH2 daily boil-off losses are acceptable for use case",
            value="unknown",
            unit="%/day",
            source="none",
            confidence=Confidence.LOW,
            status=AssumptionStatus.OPEN,
            branch="GT-1H-LH2",
        )
    )
    ledger.add(
        Assumption(
            key="fc.system_efficiency",
            statement="Fuel-cell tank-to-wheel efficiency",
            value="55",
            unit="%",
            source="literature range",
            confidence=Confidence.MEDIUM,
            status=AssumptionStatus.OPEN,
            branch="all",
        )
    )
    return ledger


def build_sample_evidence() -> SupplierEvidenceTable:
    """A seeded supplier evidence table (nothing 'confirmed')."""
    return SupplierEvidenceTable(
        [
            EvidenceRecord(
                id="EV-001",
                component="Battery pack",
                supplier="CellCo (placeholder)",
                claim="pack-level 180 Wh/kg",
                evidence_type=EvidenceType.ESTIMATE,
                document_ref="internal-roadmap-2025",
                received_date=date(2025, 11, 1),
                verification=VerificationState.UNVERIFIED,
                branch="GT-1",
            ),
            EvidenceRecord(
                id="EV-002",
                component="700 bar H2 tanks",
                supplier="TankCo (placeholder)",
                claim="type IV tank gravimetric efficiency 6.5 wt% H2",
                evidence_type=EvidenceType.DATASHEET,
                document_ref="tankco-ds-rev-a",
                received_date=date(2025, 12, 10),
                verification=VerificationState.IN_REVIEW,
                branch="GT-1H",
            ),
            EvidenceRecord(
                id="EV-003",
                component="Fuel-cell stack",
                supplier="StackCo (placeholder)",
                claim="continuous 120 kW net output",
                evidence_type=EvidenceType.QUOTE,
                document_ref="stackco-q-0042",
                received_date=date(2026, 1, 15),
                verification=VerificationState.UNVERIFIED,
                branch="GT-1H",
            ),
        ]
    )


def build_sample_components() -> list[Component]:
    """An illustrative packaging layout for the BEV baseline (mm frame)."""
    # Skateboard battery floor with motors mounted outboard of the pack and the
    # cockpit stacked above it — laid out to be clash-free under the AABB check.
    return [
        Component(
            name="Battery pack",
            group="energy",
            box=Box(cx=0, cy=0, cz=150, size_x=2400, size_y=1400, size_z=180),
        ),
        Component(
            name="Front motor",
            group="powertrain",
            box=Box(cx=1400, cy=0, cz=300, size_x=300, size_y=600, size_z=400),
        ),
        Component(
            name="Rear motor",
            group="powertrain",
            box=Box(cx=-1400, cy=0, cz=300, size_x=300, size_y=600, size_z=400),
        ),
        Component(
            name="Cockpit",
            group="interior",
            box=Box(cx=0, cy=0, cz=720, size_x=1500, size_y=1400, size_z=900),
        ),
    ]


def build_sample_partners() -> list[Partner]:
    """Seed the HAEN partner/awareness registry.

    None of these are confirmed or selected suppliers. Engagement status is
    governance metadata only:
      - Hylium  : Level 1 RFI candidate (LH2 storage) — may receive an RFI.
      - Cryos / DALIM / Parity : watch branch (monitored only).
      - KIMM    : technology observation (tracked for awareness).
    """
    return [
        Partner(
            name="Hylium",
            engagement_status=EngagementStatus.RFI_CANDIDATE,
            domain="LH2 cryogenic storage",
            rfi_level=1,
            branch="GT-1H-LH2",
            notes="Level 1 RFI candidate; not a selected or confirmed supplier.",
        ),
        Partner(
            name="Cryos",
            engagement_status=EngagementStatus.WATCH_BRANCH,
            domain="cryogenic systems",
            branch="GT-1H-LH2",
            notes="Watch branch — monitored only.",
        ),
        Partner(
            name="DALIM",
            engagement_status=EngagementStatus.WATCH_BRANCH,
            domain="hydrogen systems",
            branch="GT-1H-LH2",
            notes="Watch branch — monitored only.",
        ),
        Partner(
            name="Parity",
            engagement_status=EngagementStatus.WATCH_BRANCH,
            domain="energy systems",
            branch="GT-1H-LH2",
            notes="Watch branch — monitored only.",
        ),
        Partner(
            name="KIMM",
            engagement_status=EngagementStatus.TECHNOLOGY_OBSERVATION,
            domain="research institute",
            branch="all",
            notes="Technology observation — tracked for awareness only.",
        ),
    ]
