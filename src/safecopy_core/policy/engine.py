"""Policy engine: decide an :class:`Action` for a set of findings.

The spec's decision model is:

    데이터 유형 + 목적지 앱 + 사용자 행위 + 위험도 = 조치
    (data type + destination app + user action + risk = action)

The engine evaluates each finding against the rule table and the overall
decision is the *most restrictive* action across all findings (a clipboard
payload is only as safe as its most sensitive token).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from ..detection.types import DataType, Finding, RiskLevel
from .rules import Destination, lookup_action


class Action(IntEnum):
    """What SafeCopy should do, ordered least -> most restrictive.

    Ordering lets the engine pick the max action across findings.
    """

    ALLOW = 0
    WARN = 1
    MASK = 2
    REQUIRE_APPROVAL = 3
    BLOCK = 4


@dataclass(frozen=True)
class Decision:
    action: Action
    findings: list[Finding]
    destination: Destination

    @property
    def data_types(self) -> set[DataType]:
        return {f.data_type for f in self.findings}

    @property
    def max_risk(self) -> RiskLevel:
        return max((f.risk for f in self.findings), default=RiskLevel.LOW)


def evaluate(findings: list[Finding], destination: Destination) -> Decision:
    """Return the policy :class:`Decision` for ``findings`` going to ``destination``."""
    action = Action.ALLOW
    for finding in findings:
        action = max(action, lookup_action(finding.data_type, finding.risk, destination))
    return Decision(action=action, findings=findings, destination=destination)
