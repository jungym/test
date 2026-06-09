"""Runtime configuration and local storage paths.

All persistent state lives under a single local directory (no cloud). On
Windows 11 (the MVP target) this resolves under ``%LOCALAPPDATA%``; other
platforms fall back to ``~/.local/share`` so the engine and tests run anywhere.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_APP_DIR = "SafeCopyCore"


def default_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return Path(base) / _APP_DIR


@dataclass(frozen=True)
class Settings:
    """User-tunable settings. Defaults follow the spec's local-first stance."""

    data_dir: Path = default_data_dir()
    # 원문 로그 저장 기본 비활성화.
    store_originals_in_audit: bool = False
    # Target paste latency budget (ms); used by perf checks, not enforced here.
    latency_budget_ms: int = 300

    @property
    def vault_path(self) -> Path:
        return self.data_dir / "vault.json"

    @property
    def audit_path(self) -> Path:
        return self.data_dir / "audit.log"
