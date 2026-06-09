"""Masking / substitution engine.

Replaces each finding with a stable token and returns the (masked text,
mappings) pair. Tokens are numbered per data type within a single masking
call, e.g.::

    홍길동 ... 010-1234-5678 ... API_KEY=sk_live_xxx
    -> [PERSON_001] ... [PHONE_001] ... [API_KEY_BLOCKED]

CRITICAL secrets (API keys, SSH keys, .env values) are *blocked*, not
reversibly tokenized: their token is ``[<TYPE>_BLOCKED]`` and the mapping
records that the original must never be exported. Everything else gets a
reversible token whose original is stored in the Vault.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..detection.types import DataType, Finding, RiskLevel

# Marker stored as the Vault value for blocked secrets — 원문 반출 금지.
BLOCKED = "원문 반출 금지"


@dataclass(frozen=True)
class Mapping:
    """One token <-> original mapping produced by a masking pass.

    For blocked secrets ``original`` is :data:`BLOCKED` and ``reversible`` is
    False, so the Vault never persists the real secret.
    """

    token: str
    original: str
    data_type: DataType
    reversible: bool


@dataclass(frozen=True)
class MaskResult:
    masked_text: str
    mappings: list[Mapping]


def mask(text: str, findings: list[Finding]) -> MaskResult:
    """Return ``text`` with each finding replaced by a token, plus the mappings.

    ``findings`` must be non-overlapping (the detector guarantees this). They
    are spliced from right to left so earlier offsets stay valid.
    """
    counters: dict[DataType, int] = {}
    mappings: list[Mapping] = []
    out = text

    for finding in sorted(findings, key=lambda f: f.start, reverse=True):
        counters[finding.data_type] = counters.get(finding.data_type, 0) + 1
        token, mapping = _token_for(finding, counters[finding.data_type])
        out = out[: finding.start] + token + out[finding.end :]
        mappings.append(mapping)

    mappings.reverse()  # restore document order
    return MaskResult(masked_text=out, mappings=mappings)


def _token_for(finding: Finding, index: int) -> tuple[str, Mapping]:
    if finding.risk is RiskLevel.CRITICAL:
        token = f"[{finding.data_type.value}_BLOCKED]"
        return token, Mapping(
            token=token,
            original=BLOCKED,
            data_type=finding.data_type,
            reversible=False,
        )

    token = f"[{finding.data_type.value}_{index:03d}]"
    return token, Mapping(
        token=token,
        original=finding.text,
        data_type=finding.data_type,
        reversible=True,
    )
