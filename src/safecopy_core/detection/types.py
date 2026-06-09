"""Core value types shared across the detection -> policy pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum


class DataType(StrEnum):
    """A category of sensitive data the detector can recognize.

    Values are stable string identifiers — they appear in audit logs and in
    masking tokens (e.g. ``EMAIL`` -> ``[EMAIL_001]``), so do not rename them
    without a migration.
    """

    EMAIL = "EMAIL"
    PHONE = "PHONE"
    # 주민등록번호형 식별자 (Korean resident registration number pattern).
    RRN = "RRN"
    # 계좌번호/카드번호형 패턴.
    ACCOUNT_OR_CARD = "ACCOUNT_OR_CARD"
    API_KEY = "API_KEY"
    SSH_PRIVATE_KEY = "SSH_PRIVATE_KEY"
    # .env 파일 / DB 비밀번호 등 KEY=VALUE 형태의 비밀값.
    ENV_SECRET = "ENV_SECRET"


class RiskLevel(int, Enum):
    """Risk levels, ordered so they can be compared numerically.

    The policy engine selects an action from (data type + destination +
    user action + risk). Mapping a finding to a higher level pushes the
    default action toward BLOCK.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass(frozen=True)
class Finding:
    """A single sensitive-data match within a scanned text.

    ``start``/``end`` are character offsets into the original text and must
    be non-overlapping across the findings of one scan so the masking engine
    can splice in tokens deterministically.
    """

    data_type: DataType
    text: str
    start: int
    end: int
    risk: RiskLevel
