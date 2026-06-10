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
import zipfile
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


def export_packaging_images(
    components: list[Component],
    vehicle: VehicleDefinition | None,
    out_dir: str | Path,
    *,
    prefer_png: bool = True,
) -> dict[str, dict[str, Path]]:
    """Write SVG packaging diagrams (always) and optional PNGs (if matplotlib).

    Returns ``{view: {"svg": Path, "png": Path|None}}``. SVG is the
    dependency-free baseline; PNG is an optional convenience artifact and is
    omitted gracefully when the renderer is unavailable.
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    index: dict[str, dict[str, Path]] = {}
    for view in ("top", "side"):
        diagram = viz.packaging_diagram(components, vehicle, view=view)
        svg_path = out / f"packaging_{view}.svg"
        svg_path.write_text(viz.diagram_to_svg(diagram), encoding="utf-8")
        png_path: Path | None = None
        if prefer_png:
            candidate = out / f"packaging_{view}.png"
            if viz.render_diagram_png(diagram, candidate):
                png_path = candidate
        index[view] = {"svg": svg_path, "png": png_path}
    return index


def _image_reference_block(image_index: dict[str, dict[str, Path]]) -> str:
    lines = [
        "",
        "## Packaging diagrams (internal — concept visualization, low-fidelity)",
        "",
        "_Generated concept diagrams (axis-aligned bounding boxes). SVG is the "
        "dependency-free baseline; PNG is an optional convenience render. Not CAD, "
        "and not geometric or packaging validation._",
        "",
    ]
    for view, fmts in image_index.items():
        svg = fmts.get("svg")
        if svg is not None:
            lines.append(f"- {view} view (svg): `{svg.name}`")
            lines.append(f"  ![packaging {view} view (svg)]({svg.name})")
        png = fmts.get("png")
        if png is not None:
            lines.append(f"- {view} view (png): `{png.name}`")
            lines.append(f"  ![packaging {view} view (png)]({png.name})")
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

    image_paths: dict[str, Path] = {}      # view -> svg path (hashed baseline)
    png_artifacts: list[str] = []          # optional convenience renders (not hashed)
    final_text = dossier_text
    if components:
        image_index = export_packaging_images(components, vehicle, out)
        image_paths = {v: f["svg"] for v, f in image_index.items()}
        png_artifacts = sorted(f["png"].name for f in image_index.values() if f["png"])
        final_text = dossier_text + "\n" + _image_reference_block(image_index)

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
        # PNGs are optional, possibly non-deterministic convenience artifacts;
        # they are recorded by name but excluded from the hashed manifest.
        "png_rendered": bool(png_artifacts),
        "png_artifacts": png_artifacts,
    }
    # SVG baseline is deterministic and IS hashed; PNGs are intentionally not.
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


# --------------------------------------------------------------------------- #
# Release package + manifest + validation (Item 7)
# --------------------------------------------------------------------------- #
@dataclass
class ReleasePackage:
    out_dir: Path
    manifest_path: Path
    files: dict[str, str] = field(default_factory=dict)
    manifest: dict = field(default_factory=dict)


def export_release_package(
    dossier_text: str,
    out_dir: str | Path,
    *,
    programme: str,
    branch: str,
    commit: str | None = None,
    generated_at: str | None = None,
    components: list[Component] | None = None,
    vehicle: VehicleDefinition | None = None,
    rfi_markdown: str | None = None,
    metadata: ReportMetadata | None = None,
) -> ReleasePackage:
    """Build an internal-only review package with a checksummed manifest.

    Writes the dossier (+ optional packaging SVGs), an optional ``rfi.md``, and a
    ``manifest.json`` listing every file with its SHA-256 plus reproducibility
    metadata. All content is governance-scanned before writing. Deterministic when
    ``generated_at`` is fixed.
    """
    res = export_dossier(
        dossier_text, out_dir, programme=programme, branch=branch, commit=commit,
        generated_at=generated_at, metadata=metadata, components=components, vehicle=vehicle,
    )
    out = res.out_dir
    files = dict(res.files)

    if rfi_markdown is not None:
        findings = check_text(rfi_markdown)
        if findings:
            raise ValueError(
                f"refusing to export RFI with forbidden claim(s): "
                f"{[f.matched_text for f in findings]}"
            )
        rfi_path = out / "rfi.md"
        rfi_path.write_text(rfi_markdown, encoding="utf-8")
        files["rfi.md"] = sha256_text(rfi_markdown)

    manifest = {
        "programme": programme,
        "branch": branch,
        "commit": commit,
        "report_version": REPORT_VERSION,
        "tool_version": __version__,
        "generated_at": res.metadata["generated_at"],
        "internal_only": True,
        "human_review_required": True,
        "external_release_allowed": False,
        "files": dict(sorted(files.items())),
    }
    # Bundle integrity hash over the sorted (filename -> checksum) mapping. This
    # detects tampering with the manifest's file list/checksums as a whole.
    manifest["bundle_sha256"] = sha256_text(
        json.dumps(manifest["files"], sort_keys=True)
    )
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True)
    manifest_path = out / "manifest.json"
    manifest_path.write_text(manifest_text, encoding="utf-8")

    return ReleasePackage(out_dir=out, manifest_path=manifest_path, files=files, manifest=manifest)


def write_validation_report(out_dir: str | Path) -> Path:
    """Run validation and write an internal-only validation_report.json."""
    out = Path(out_dir)
    problems = validate_release(out)
    report = {
        "valid": not problems,
        "problems": problems,
        "internal_only": True,
        "human_review_required": True,
        "external_release_allowed": False,
    }
    path = out / "validation_report.json"
    path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return path


def archive_release(
    out_dir: str | Path,
    archive_path: str | Path | None = None,
    *,
    include_validation: bool = True,
) -> Path:
    """Bundle an internal release package into a single zip (stdlib only).

    Files are added in sorted order with a fixed timestamp so the archive's
    layout is reproducible. Internal-only; nothing here approves external release.
    Returns the archive path.
    """
    out = Path(out_dir)
    if include_validation:
        write_validation_report(out)
    archive = Path(archive_path) if archive_path else out.with_suffix(".zip")

    names = sorted(p.name for p in out.iterdir() if p.is_file())
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            info = zipfile.ZipInfo(filename=name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, (out / name).read_bytes())
    return archive


def validate_release(out_dir: str | Path) -> list[str]:
    """Validate an exported release package; return a list of problems ([] = OK).

    Checks: manifest present; every listed file exists with a matching checksum;
    the dossier is governance-clean; and the package is marked internal-only,
    human-review-required, and not externally releasable.
    """
    out = Path(out_dir)
    problems: list[str] = []

    manifest_path = out / "manifest.json"
    if not manifest_path.exists():
        return ["manifest.json missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    files_map = manifest.get("files", {})
    for name, expected in files_map.items():
        fp = out / name
        if not fp.exists():
            problems.append(f"missing file: {name}")
            continue
        actual = sha256_text(fp.read_text(encoding="utf-8"))
        if actual != expected:
            problems.append(f"checksum mismatch: {name}")

    # Bundle integrity: the recomputed hash of the file map must match the
    # declared bundle hash (detects manifest-level tampering).
    if "bundle_sha256" in manifest:
        recomputed = sha256_text(json.dumps(files_map, sort_keys=True))
        if recomputed != manifest["bundle_sha256"]:
            problems.append("bundle hash mismatch")

    dossier = out / "dossier.md"
    if dossier.exists():
        findings = check_text(dossier.read_text(encoding="utf-8"))
        if findings:
            problems.append(f"forbidden claim(s) in dossier: {[f.matched_text for f in findings]}")

    if manifest.get("external_release_allowed") is not False:
        problems.append("external_release_allowed must be false")
    if manifest.get("human_review_required") is not True:
        problems.append("human_review_required must be true")
    if manifest.get("internal_only") is not True:
        problems.append("internal_only must be true")

    return problems
