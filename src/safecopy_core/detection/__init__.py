"""Detection stage: text -> list[Finding]."""

from .detector import detect
from .types import DataType, Finding, RiskLevel

__all__ = ["DataType", "Finding", "RiskLevel", "detect"]
