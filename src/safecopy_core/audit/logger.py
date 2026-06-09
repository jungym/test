"""Append-only audit log (감사 로그).

Records *what was attempted*, never the sensitive originals by default
(원문 저장 기본 비활성화). Each record is one JSON line so the log is easy to
tail, ship, or parse. Fields mirror spec 4.6: time, app, destination domain,
detected data types, action result, user choice, whether the original was
stored.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from ..detection.types import DataType
from ..policy.engine import Action


@dataclass(frozen=True)
class AuditRecord:
    timestamp: str
    app: str
    destination: str
    data_types: list[str]
    action: str
    user_choice: str | None = None
    original_stored: bool = False  # 원문 저장 여부 (default: not stored)
    extra: dict[str, str] = field(default_factory=dict)


class AuditLog:
    """Append-only JSON-lines audit log at a local path."""

    def __init__(self, path: Path):
        self._path = path

    def record(
        self,
        *,
        app: str,
        destination: str,
        data_types: set[DataType],
        action: Action,
        user_choice: str | None = None,
        original_stored: bool = False,
    ) -> AuditRecord:
        rec = AuditRecord(
            timestamp=datetime.now(UTC).isoformat(),
            app=app,
            destination=destination,
            data_types=sorted(dt.value for dt in data_types),
            action=action.name,
            user_choice=user_choice,
            original_stored=original_stored,
        )
        self._append(rec)
        return rec

    def _append(self, rec: AuditRecord) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(rec), ensure_ascii=False) + "\n")
