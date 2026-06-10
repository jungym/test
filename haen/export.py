"""Internal artifact export for HAEN dossiers (Review Gate 4).

Writes a dossier and a metadata sidecar to an internal output directory. Every
export is INTERNAL and human-review-required by default; a forbidden-claim scan
runs before anything is written, and exports never set external-release approval.

Nothing here performs or implies engineering validation, certification,
production, supplier confirmation, or road-legality.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from . import visualization as viz
from .governance import ReportMetadata, check_text
from .packaging import Component
from .vehicle_definition import VehicleDefinition

REPORT_VERSION = "1"


def sha256_text(text: str) -> str:
    """Deterministic SHA-256 of a unicode string (utf-8)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class ExportResult:
    out_dir: Path
    dossier_path: Path
    metadata_path: Path
    files: dict[str, str] = field(default_factory=dict)  # filename -> sha256
    metadata: dict = field(default_factory=dict)
    image_paths: dict[str, Path] = field(default_factory=dict)  # view -> path


def export_packaging_svgs(
    components: list[Component],
    vehicle: VehicleDefinition | None,
    out_dir: str | Path,
) -> dict[str, Path]:
    """Write deterministic, dependency-free SVG packaging diagrams (top + side).

    Returns a mapping of view name -> written path. No plotting library is
    required (SVG is generated from the pure diagram model), so this works even
    when Plotly/Matplotlib are absent. Internal-only, low-fidelity.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for view in ("top", "side"):
        diagram = viz.packaging_diagram(components, vehicle, view=view)
        svg = viz.diagram_to_svg(diagram)
        path = out / f"packaging_{view}.svg"
        path.write_text(svg, encoding="utf-8")
        written[view] = path
    return written


def _image_reference_block(image_files: dict[str, Path]) -> str:
    lines = [
        "",
        "## Packaging diagrams (internal — concept visualization, low-fidelity)",
        "",
        "_Generated SVG concept diagrams (axis-aligned bounding boxes). Not CAD, "
        "and not geometric or packaging validation._",
        "",
    ]
    for view, path in image_files.items():
        lines.append(f"- {view} view: `{path.name}`")
        lines.append(f"  ![packaging {view} view]({path.name})")
    lines.append("")
    return "\n".join(lines)


def export_dossier(
    dossier_text: str,
    out_dir: str | Path,
    *,
    programme: str,
    branch: str,
    commit: str | None = None,
    report_version: str = REPORT_VERSION,
    generated_at: str | None = None,
    metadata: ReportMetadata | None = None,
    components: list[Component] | None = None,
    vehicle: VehicleDefinition | None = None,
) -> ExportResult:
    """Export ``dossier_text`` to ``out_dir`` as an internal artifact.

    Writes ``dossier.md`` and ``dossier.meta.json``. When ``components`` are
    supplied, also writes deterministic SVG packaging diagrams and embeds image
    references in the exported dossier. Refuses (raises ``ValueError``) if the
    dossier contains any forbidden claim — nothing is written in that case. Pass
    ``generated_at`` (ISO string) for reproducible output.
    """
    meta_obj = metadata or ReportMetadata(programme=programme)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    image_paths: dict[str, Path] = {}
    final_text = dossier_text
    if components:
        image_paths = export_packaging_svgs(components, vehicle, out)
        final_text = dossier_text + "\n" + _image_reference_block(image_paths)

    # Governance gate runs on the FINAL text (including any embedded references).
    findings = check_text(final_text)
    if findings:
        raise ValueError(
            f"refusing to export dossier with forbidden claim(s): "
            f"{[f.matched_text for f in findings]}"
        )

    dossier_path = out / "dossier.md"
    dossier_path.write_text(final_text, encoding="utf-8")
    dossier_sha = sha256_text(final_text)

    meta = {
        "programme": programme,
        "branch": branch,
        "commit": commit,
        "report_version": report_version,
        "tool_version": __version__,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "human_review_required": meta_obj.human_review_required,
        "external_release_allowed": meta_obj.external_release_allowed,
        "internal_only": meta_obj.internal_only,
        "classification": meta_obj.classification,
        "dossier_sha256": dossier_sha,
    }
    files = {dossier_path.name: dossier_sha}
    for view, path in image_paths.items():
        files[path.name] = sha256_text(path.read_text(encoding="utf-8"))

    metadata_text = json.dumps(meta, indent=2, sort_keys=True)
    metadata_path = out / "dossier.meta.json"
    metadata_path.write_text(metadata_text, encoding="utf-8")
    files[metadata_path.name] = sha256_text(metadata_text)

    return ExportResult(
        out_dir=out,
        dossier_path=dossier_path,
        metadata_path=metadata_path,
        files=files,
        metadata=meta,
        image_paths=image_paths,
    )
