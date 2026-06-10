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
from .governance import ReportMetadata, check_text

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
) -> ExportResult:
    """Export ``dossier_text`` to ``out_dir`` as an internal artifact.

    Writes ``dossier.md`` and ``dossier.meta.json``. Refuses (raises
    ``ValueError``) if the dossier contains any forbidden claim — nothing is
    written in that case. Pass ``generated_at`` (ISO string) for reproducible
    output.
    """
    findings = check_text(dossier_text)
    if findings:
        raise ValueError(
            f"refusing to export dossier with forbidden claim(s): "
            f"{[f.matched_text for f in findings]}"
        )

    meta_obj = metadata or ReportMetadata(programme=programme)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    dossier_path = out / "dossier.md"
    dossier_path.write_text(dossier_text, encoding="utf-8")
    dossier_sha = sha256_text(dossier_text)

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
    metadata_text = json.dumps(meta, indent=2, sort_keys=True)
    metadata_path = out / "dossier.meta.json"
    metadata_path.write_text(metadata_text, encoding="utf-8")

    return ExportResult(
        out_dir=out,
        dossier_path=dossier_path,
        metadata_path=metadata_path,
        files={
            dossier_path.name: dossier_sha,
            metadata_path.name: sha256_text(metadata_text),
        },
        metadata=meta,
    )
