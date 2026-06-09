"""The detector: scan text and return non-overlapping :class:`Finding`s.

This is the first stage of the pipeline and is intentionally pure (no I/O):
given a string it returns findings, which the risk/policy/masking stages
consume. Keep it deterministic and fast — the spec targets <300ms end-to-end
paste latency.
"""

from __future__ import annotations

from .patterns import PATTERNS
from .types import Finding


def detect(text: str) -> list[Finding]:
    """Return all sensitive-data findings in ``text``, sorted by position.

    Findings are guaranteed non-overlapping: when two patterns match the same
    span, the one listed earlier in :data:`PATTERNS` (higher-risk / more
    specific) wins. This invariant lets the masking engine splice tokens by
    offset without bookkeeping.
    """
    claimed: list[tuple[int, int]] = []
    findings: list[Finding] = []

    for pattern in PATTERNS:
        for match in pattern.regex.finditer(text):
            start, end = match.start(), match.end()
            if _overlaps(start, end, claimed):
                continue
            claimed.append((start, end))
            findings.append(
                Finding(
                    data_type=pattern.data_type,
                    text=match.group(),
                    start=start,
                    end=end,
                    risk=pattern.risk,
                )
            )

    findings.sort(key=lambda f: f.start)
    return findings


def _overlaps(start: int, end: int, claimed: list[tuple[int, int]]) -> bool:
    return any(start < c_end and c_start < end for c_start, c_end in claimed)
