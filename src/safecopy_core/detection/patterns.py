"""Regex pattern registry for sensitive-data detection.

Each entry maps a :class:`DataType` to a compiled pattern and the *default*
risk level assigned to matches of that type. The detector walks this registry
in order; earlier (more specific / higher-risk) patterns win when ranges
overlap, so keep secrets ahead of generic identifiers.

MVP detection targets per the spec: API Key, email, phone, identifier
(RRN) patterns, plus SSH keys and .env secrets that share the same engine.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .types import DataType, RiskLevel


@dataclass(frozen=True)
class Pattern:
    data_type: DataType
    regex: re.Pattern[str]
    risk: RiskLevel


# Order matters: high-risk, structurally-specific secrets are listed first so
# they take precedence over generic patterns (e.g. an API key value should not
# be reclassified as an account number).
PATTERNS: list[Pattern] = [
    Pattern(
        DataType.SSH_PRIVATE_KEY,
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"
            r".*?-----END (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----",
            re.DOTALL,
        ),
        RiskLevel.CRITICAL,
    ),
    Pattern(
        DataType.API_KEY,
        re.compile(
            # Common provider key shapes + generic API_KEY=... assignments.
            r"\b(?:sk-[A-Za-z0-9]{20,}"
            r"|sk_live_[A-Za-z0-9]{16,}"
            r"|sk_test_[A-Za-z0-9]{16,}"
            r"|AKIA[0-9A-Z]{16}"
            r"|ghp_[A-Za-z0-9]{36}"
            r"|xox[baprs]-[A-Za-z0-9-]{10,})"
        ),
        RiskLevel.CRITICAL,
    ),
    Pattern(
        DataType.ENV_SECRET,
        re.compile(
            # KEY=VALUE assignments where the key name implies a secret.
            r"\b[A-Z0-9_]*"
            r"(?:API[_-]?KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|PRIVATE[_-]?KEY)"
            r"[A-Z0-9_]*\s*=\s*[^\s'\"]+",
            re.IGNORECASE,
        ),
        RiskLevel.CRITICAL,
    ),
    Pattern(
        DataType.RRN,
        re.compile(r"\b\d{6}-?[1-4]\d{6}\b"),
        RiskLevel.HIGH,
    ),
    Pattern(
        DataType.ACCOUNT_OR_CARD,
        # 13-16 digit runs, optionally grouped by spaces or hyphens (cards,
        # bank accounts). Kept after RRN so resident numbers win.
        re.compile(r"\b(?:\d[ -]?){12,18}\d\b"),
        RiskLevel.HIGH,
    ),
    Pattern(
        DataType.EMAIL,
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        RiskLevel.MEDIUM,
    ),
    Pattern(
        DataType.PHONE,
        # Korean mobile numbers, with or without separators.
        re.compile(r"\b01[016789][ -]?\d{3,4}[ -]?\d{4}\b"),
        RiskLevel.MEDIUM,
    ),
]
