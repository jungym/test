"""Tests for Gate 7 Item A1 — haen.io loaders and Project aggregator."""

import pytest

from haen import io
from haen.governance import check_text
from haen.packaging import Component
from haen.report_builder import build_dossier
from haen.sample_data import (
    build_sample_components,
    build_sample_evidence,
    build_sample_fleet,
    build_sample_partners,
    build_sample_project,
)
from haen.supplier_evidence import Partner, SupplierEvidenceTable
from haen.vehicle_definition import VehicleDefinition


# --------------------------------------------------------------------------- #
# Round-trip via dump_models + loaders
# --------------------------------------------------------------------------- #
def test_vehicles_round_trip(tmp_path):
    fleet = build_sample_fleet()
    path = io.dump_models(fleet, tmp_path / "vehicles.yaml", key="vehicles")
    loaded = io.load_vehicles(path)
    assert [v.id for v in loaded] == [v.id for v in fleet]
    assert isinstance(loaded[0], VehicleDefinition)
    assert loaded[0].curb_mass_kg == pytest.approx(fleet[0].curb_mass_kg)


def test_components_round_trip(tmp_path):
    comps = build_sample_components()
    path = io.dump_models(comps, tmp_path / "c.json", key="components")  # JSON path too
    loaded = io.load_components(path)
    assert [c.name for c in loaded] == [c.name for c in comps]
    assert isinstance(loaded[0], Component)


def test_partners_and_evidence_round_trip(tmp_path):
    pp = io.dump_models(build_sample_partners(), tmp_path / "partners.yaml", key="partners")
    partners = io.load_partners(pp)
    assert any(isinstance(p, Partner) and p.name == "Hylium" for p in partners)

    records = build_sample_evidence().all()
    ep = io.dump_models(records, tmp_path / "evidence.yaml", key="evidence")
    table = io.load_evidence(ep)
    assert isinstance(table, SupplierEvidenceTable)
    assert len(table.all()) == len(records)


# --------------------------------------------------------------------------- #
# Validation / error handling
# --------------------------------------------------------------------------- #
def test_invalid_vehicle_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("vehicles:\n  - id: x\n", encoding="utf-8")  # missing required fields
    with pytest.raises(Exception):
        io.load_vehicles(bad)


def test_non_list_rejected(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("vehicles: not-a-list\n", encoding="utf-8")
    with pytest.raises(ValueError):
        io.load_vehicles(bad)


# --------------------------------------------------------------------------- #
# Project manifest
# --------------------------------------------------------------------------- #
def _write_project(tmp_path):
    io.dump_models(build_sample_fleet(), tmp_path / "vehicles.yaml", key="vehicles")
    io.dump_models(build_sample_components(), tmp_path / "components.yaml", key="components")
    io.dump_models(build_sample_partners(), tmp_path / "partners.yaml", key="partners")
    io.dump_models(build_sample_evidence().all(), tmp_path / "evidence.yaml", key="evidence")
    (tmp_path / "assumptions.yaml").write_text(
        "assumptions:\n"
        "  - key: bev.pack_density\n"
        "    statement: BEV pack density\n"
        "    value: 180\n"
        "    unit: Wh/kg\n"
        "    confidence: low\n"
        "    status: open\n"
        "    branch: GT-1\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "haen-project.yaml"
    manifest.write_text(
        "programme: HAEN GT-1\nbranch: GT-1\n"
        "vehicles: vehicles.yaml\ncomponents: components.yaml\n"
        "partners: partners.yaml\nevidence: evidence.yaml\nassumptions: assumptions.yaml\n",
        encoding="utf-8",
    )
    return manifest


def test_load_project(tmp_path):
    proj = io.load_project(_write_project(tmp_path))
    assert proj.programme == "HAEN GT-1" and proj.branch == "GT-1"
    assert len(proj.vehicles) == 3
    assert len(proj.components) == 4
    assert proj.evidence is not None and len(proj.evidence.all()) == 3
    assert any(p.name == "Hylium" for p in proj.partners)
    assert proj.ledger is not None and len(proj.ledger.all()) >= 1


def test_load_project_requires_a_vehicle(tmp_path):
    manifest = tmp_path / "haen-project.yaml"
    manifest.write_text("programme: P\nbranch: GT-1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least one vehicle"):
        io.load_project(manifest)


def test_project_relative_paths_resolved(tmp_path):
    sub = tmp_path / "data"
    sub.mkdir()
    io.dump_models(build_sample_fleet(), sub / "vehicles.yaml", key="vehicles")
    manifest = tmp_path / "haen-project.yaml"
    manifest.write_text("vehicles: data/vehicles.yaml\n", encoding="utf-8")
    proj = io.load_project(manifest)
    assert len(proj.vehicles) == 3


# --------------------------------------------------------------------------- #
# Sample project parity + governance unaffected
# --------------------------------------------------------------------------- #
def test_build_sample_project_parity():
    proj = build_sample_project()
    assert [v.id for v in proj.vehicles] == [v.id for v in build_sample_fleet()]
    assert len(proj.components) == len(build_sample_components())


def test_dossier_from_loaded_project_is_governance_clean(tmp_path):
    proj = io.load_project(_write_project(tmp_path))
    text = build_dossier(
        programme=proj.programme, branch=proj.branch, vehicles=proj.vehicles,
        components=proj.components, evidence=proj.evidence, ledger=proj.ledger,
        generated_at="2026-01-01T00:00:00+00:00",
    )
    assert check_text(text) == []
