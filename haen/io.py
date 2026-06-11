"""haen.io — load/dump project data from YAML/JSON files.

Lets the tools run on real, human-authored data instead of only the bundled
sample. All inputs are validated through the existing Pydantic models, so
malformed data fails fast. Nothing here changes governance: generated outputs
still pass the hard forbidden-claim gate, remain internal-only, and require human
review.

A :class:`Project` bundles everything the CLI/dashboard need (fleet, packaging
components, supplier evidence, partners, assumption ledger) behind one object, so
sample and user-supplied data flow through the same code path.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel

from .governance import Assumption, AssumptionLedger, AssumptionStatus, Confidence
from .packaging import Component
from .supplier_evidence import EvidenceRecord, Partner, SupplierEvidenceTable
from .vehicle_definition import VehicleDefinition


# --------------------------------------------------------------------------- #
# Raw file helpers
# --------------------------------------------------------------------------- #
def _load_raw(path: str | Path) -> Any:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


def _as_list(data: Any, key: str) -> list:
    """Accept either a top-level list or a mapping ``{key: [...]}``."""
    if isinstance(data, dict):
        data = data.get(key, data)
    if not isinstance(data, list):
        raise ValueError(f"expected a list (or '{key}:' list), got {type(data).__name__}")
    return data


# --------------------------------------------------------------------------- #
# Loaders (validate through existing Pydantic models)
# --------------------------------------------------------------------------- #
def load_vehicles(path: str | Path) -> list[VehicleDefinition]:
    return [VehicleDefinition.model_validate(d) for d in _as_list(_load_raw(path), "vehicles")]


def load_components(path: str | Path) -> list[Component]:
    return [Component.model_validate(d) for d in _as_list(_load_raw(path), "components")]


def load_partners(path: str | Path) -> list[Partner]:
    return [Partner.model_validate(d) for d in _as_list(_load_raw(path), "partners")]


def load_evidence(path: str | Path) -> SupplierEvidenceTable:
    records = [EvidenceRecord.model_validate(d) for d in _as_list(_load_raw(path), "evidence")]
    return SupplierEvidenceTable(records)


def load_assumptions(path: str | Path, *, ledger: AssumptionLedger | None = None) -> AssumptionLedger:
    """Load assumption entries into a ledger (creates an in-memory one if none)."""
    led = ledger if ledger is not None else AssumptionLedger(":memory:")
    for d in _as_list(_load_raw(path), "assumptions"):
        led.add(
            Assumption(
                key=d["key"],
                statement=d["statement"],
                value=str(d["value"]),
                unit=d.get("unit", ""),
                source=d.get("source", "engineering judgement"),
                confidence=Confidence(d.get("confidence", "low")),
                status=AssumptionStatus(d.get("status", "open")),
                branch=d.get("branch", "all"),
                owner=d.get("owner", ""),
            )
        )
    return led


def dump_models(models: list[BaseModel], path: str | Path, *, key: str) -> Path:
    """Serialize a list of Pydantic models to YAML/JSON under ``{key: [...]}``."""
    payload = {key: [m.model_dump(mode="json") for m in models]}
    p = Path(path)
    if p.suffix.lower() == ".json":
        p.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    else:
        p.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return p


# --------------------------------------------------------------------------- #
# Project aggregator
# --------------------------------------------------------------------------- #
class ProjectConfig(BaseModel):
    """A project manifest pointing at the data files (paths relative to itself)."""

    programme: str = "HAEN GT-1"
    branch: str = "GT-1"
    vehicles: str | None = None
    components: str | None = None
    evidence: str | None = None
    partners: str | None = None
    assumptions: str | None = None
    ledger_db: str | None = None  # optional file-backed sqlite ledger


@dataclass
class Project:
    """Everything the CLI/dashboard consume, from sample or user data."""

    programme: str
    branch: str
    vehicles: list[VehicleDefinition]
    components: list[Component] = field(default_factory=list)
    evidence: SupplierEvidenceTable | None = None
    partners: list[Partner] = field(default_factory=list)
    ledger: AssumptionLedger | None = None


def load_project(path: str | Path) -> Project:
    """Load a :class:`Project` from a ``haen-project.yaml`` manifest.

    Paths in the manifest are resolved relative to the manifest's directory.
    A project must define at least one vehicle.
    """
    manifest = Path(path)
    base = manifest.parent
    cfg = ProjectConfig.model_validate(_load_raw(manifest))

    def _resolve(rel: str | None) -> Path | None:
        if not rel:
            return None
        rp = Path(rel)
        return rp if rp.is_absolute() else (base / rp)

    vpath = _resolve(cfg.vehicles)
    vehicles = load_vehicles(vpath) if vpath else []
    if not vehicles:
        raise ValueError("project must define at least one vehicle (vehicles: <path>)")

    cpath = _resolve(cfg.components)
    components = load_components(cpath) if cpath else []
    epath = _resolve(cfg.evidence)
    evidence = load_evidence(epath) if epath else SupplierEvidenceTable([])
    ppath = _resolve(cfg.partners)
    partners = load_partners(ppath) if ppath else []

    ledger = AssumptionLedger(cfg.ledger_db) if cfg.ledger_db else AssumptionLedger(":memory:")
    apath = _resolve(cfg.assumptions)
    if apath:
        load_assumptions(apath, ledger=ledger)

    return Project(
        programme=cfg.programme,
        branch=cfg.branch,
        vehicles=vehicles,
        components=components,
        evidence=evidence,
        partners=partners,
        ledger=ledger,
    )
