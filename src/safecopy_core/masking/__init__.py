"""Masking stage: text + findings -> masked text + token mappings."""

from .engine import BLOCKED, Mapping, MaskResult, mask

__all__ = ["BLOCKED", "Mapping", "MaskResult", "mask"]
