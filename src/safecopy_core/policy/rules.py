"""Default policy rule table.

These encode the worked examples from the spec, e.g.:

  - API Key -> AI 입력창: 차단 (BLOCK)
  - 전화번호 포함 문장 -> AI: 마스킹 후 허용 (MASK)
  - 계약서 -> 외부 사이트 업로드: 경고/승인 (WARN/REQUIRE_APPROVAL)
  - .env 내용 -> 메신저: 차단 (BLOCK)
  - 고객명단 -> USB: 관리자 승인 또는 차단 (REQUIRE_APPROVAL/BLOCK)

The table is data, not code, so the policy-settings UI (MVP item 8) can edit
it without touching the engine. ``DEFAULT_BY_RISK`` is the fallback when no
(type, destination) specific rule applies.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from ..detection.types import DataType, RiskLevel

if TYPE_CHECKING:
    from .engine import Action


class Destination(StrEnum):
    """The external path data is heading toward."""

    AI = "AI"  # ChatGPT, Claude, Gemini, Copilot, Notion AI ...
    BROWSER = "BROWSER"  # generic web upload / form
    MESSENGER = "MESSENGER"
    EMAIL = "EMAIL"
    CLOUD = "CLOUD"
    USB = "USB"
    UNKNOWN = "UNKNOWN"


def _action() -> type[Action]:
    # Imported lazily to avoid a cycle: engine imports this module for Destination.
    from .engine import Action

    return Action


# Fallback action keyed purely on risk, used when no specific override matches.
def default_by_risk(risk: RiskLevel) -> Action:
    a = _action()
    return {
        RiskLevel.LOW: a.ALLOW,
        RiskLevel.MEDIUM: a.WARN,
        RiskLevel.HIGH: a.REQUIRE_APPROVAL,
        RiskLevel.CRITICAL: a.BLOCK,
    }[risk]


# Specific overrides: (data_type, destination) -> Action. Anything not listed
# falls through to default_by_risk().
def _overrides() -> dict[tuple[DataType, Destination], Action]:
    a = _action()
    return {
        (DataType.API_KEY, Destination.AI): a.BLOCK,
        (DataType.SSH_PRIVATE_KEY, Destination.AI): a.BLOCK,
        (DataType.ENV_SECRET, Destination.MESSENGER): a.BLOCK,
        (DataType.ENV_SECRET, Destination.AI): a.BLOCK,
        (DataType.PHONE, Destination.AI): a.MASK,
        (DataType.EMAIL, Destination.AI): a.MASK,
        (DataType.RRN, Destination.AI): a.MASK,
    }


def lookup_action(data_type: DataType, risk: RiskLevel, destination: Destination) -> Action:
    """Resolve the action for one finding, override first then risk fallback."""
    override = _overrides().get((data_type, destination))
    if override is not None:
        return override
    return default_by_risk(risk)
