"""00_governance — guardrails for the design support system.

Two responsibilities:

1. **Forbidden claim checker** — scans any generated text for claims the system
   is contractually forbidden from making (road legal, homologation ready,
   crash safe, production feasible, supplier confirmed, design complete).
2. **Assumption ledger** — a persisted register of every engineering assumption
   used to produce an output, with its source and confidence, so that humans can
   review and challenge the basis of any result.
"""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml

_DATA_DIR = Path(__file__).resolve().parent / "data"
_FORBIDDEN_FILE = _DATA_DIR / "forbidden_claims.yaml"


# --------------------------------------------------------------------------- #
# Forbidden claim checker
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ClaimRule:
    """A single forbidden-claim rule."""

    id: str
    label: str
    pattern: re.Pattern
    explanation: str


@dataclass(frozen=True)
class ClaimFinding:
    """A detected forbidden claim within scanned text."""

    rule_id: str
    label: str
    matched_text: str
    line: int
    column: int
    explanation: str

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return (
            f"[{self.rule_id}] line {self.line}:{self.column} "
            f"'{self.matched_text}' -> {self.explanation}"
        )


def _load_rules() -> list[ClaimRule]:
    """Load forbidden-claim rules from the bundled YAML file."""
    raw = yaml.safe_load(_FORBIDDEN_FILE.read_text(encoding="utf-8"))
    rules: list[ClaimRule] = []
    for entry in raw["forbidden_claims"]:
        patterns = entry["patterns"]
        # Combine alternatives into a single, case-insensitive regex.
        combined = "|".join(f"(?:{p})" for p in patterns)
        rules.append(
            ClaimRule(
                id=entry["id"],
                label=entry["label"],
                pattern=re.compile(combined, re.IGNORECASE),
                explanation=entry["explanation"],
            )
        )
    return rules


_RULES_CACHE: list[ClaimRule] | None = None


def get_rules() -> list[ClaimRule]:
    """Return cached forbidden-claim rules."""
    global _RULES_CACHE
    if _RULES_CACHE is None:
        _RULES_CACHE = _load_rules()
    return _RULES_CACHE


def check_text(text: str, *, rules: list[ClaimRule] | None = None) -> list[ClaimFinding]:
    """Scan ``text`` and return every forbidden-claim finding.

    The scan is line-aware so findings can be traced back to their location.
    """
    rules = rules if rules is not None else get_rules()
    findings: list[ClaimFinding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for rule in rules:
            for match in rule.pattern.finditer(line):
                findings.append(
                    ClaimFinding(
                        rule_id=rule.id,
                        label=rule.label,
                        matched_text=match.group(0),
                        line=line_no,
                        column=match.start() + 1,
                        explanation=rule.explanation,
                    )
                )
    return findings


def is_clean(text: str) -> bool:
    """Return ``True`` when ``text`` contains no forbidden claims."""
    return not check_text(text)


def assert_clean(text: str) -> None:
    """Raise :class:`ForbiddenClaimError` if ``text`` contains forbidden claims."""
    findings = check_text(text)
    if findings:
        raise ForbiddenClaimError(findings)


class ForbiddenClaimError(ValueError):
    """Raised when text contains one or more forbidden claims."""

    def __init__(self, findings: list[ClaimFinding]):
        self.findings = findings
        joined = "; ".join(f"{f.label} ('{f.matched_text}' @ line {f.line})" for f in findings)
        super().__init__(f"Forbidden claim(s) detected: {joined}")


# --------------------------------------------------------------------------- #
# Advisory semantic claim-risk layer (Review Gate 5, Item 7)
# --------------------------------------------------------------------------- #
# This layer is ADVISORY only. It surfaces phrasings that *resemble* a strong
# claim and merit human review. It NEVER relaxes the hard, authoritative lexical
# forbidden-claim gate (``check_text``/``assert_clean``) and is not exhaustive.
@dataclass(frozen=True)
class RiskFinding:
    category: str
    snippet: str
    line: int
    note: str
    severity: str = "advisory"


_SEM_CUES: list[tuple[str, re.Pattern]] = [
    ("validation-adjacent",
     re.compile(r"\b(validated|verified|proven|guaranteed|confirmed)\b", re.IGNORECASE)),
    ("certification-adjacent",
     re.compile(r"\b(certified|certifiable|homologat\w*|type[\s-]?approved|approved)\b", re.IGNORECASE)),
    ("production-adjacent",
     re.compile(r"\b(mass[\s-]?produc\w+|production[\s-]?ready|manufacturable)\b", re.IGNORECASE)),
    ("legality-adjacent",
     re.compile(r"\b(road[\s-]?legal\w*|street[\s-]?legal\w*|compliant)\b", re.IGNORECASE)),
    ("completion-adjacent",
     re.compile(r"\b(finali[sz]ed)\b", re.IGNORECASE)),
    ("ko-claim-adjacent",
     re.compile(r"(보장|입증|확정|인증\s*완료|양산\s*가능)")),
]

# Lines that are clearly disclaimers/negated-status are skipped wholesale — these
# are the project's own safe framings and must not raise advisory noise.
_DISCLAIMER_MARKERS = (
    "makes no assertion", "no assertion", "does not assert", "nor that",
    "not assessed", "not evaluated", "not performed", "not modelled",
    "not a validated", "not for certification", "not vehicle-dynamics",
)
_NEG_TOKENS_EN = ("not ", "no ", "never", "without", "nor ", "n't", "non-", "not-")
_NEG_TOKENS_KO = ("미", "안", "없", "않", "불가")


def _is_negated(text: str, start: int, end: int) -> bool:
    left = text[max(0, start - 25):start].lower()
    right = text[end:end + 20].lower()
    if any(tok in left or tok in right for tok in _NEG_TOKENS_EN):
        return True
    if any(tok in left or tok in right for tok in _NEG_TOKENS_KO):
        return True
    return False


def semantic_risk_scan(text: str) -> list[RiskFinding]:
    """Return ADVISORY semantic-risk findings (never authoritative).

    Flags strong-claim-adjacent phrasings (English + Korean) that a human should
    review against the forbidden-claim policy. Negation-aware to reduce noise on
    safe framings. This does NOT replace :func:`check_text`, which remains the
    hard gate.
    """
    findings: list[RiskFinding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        low = line.lower()
        if any(marker in low for marker in _DISCLAIMER_MARKERS):
            continue  # project's own disclaimer/negated-status wording
        for category, pattern in _SEM_CUES:
            for m in pattern.finditer(line):
                if _is_negated(line, m.start(), m.end()):
                    continue
                snippet = line.strip()[:120]
                findings.append(
                    RiskFinding(
                        category=category,
                        snippet=snippet,
                        line=line_no,
                        note=("strong-claim-adjacent phrasing; verify against the "
                              "forbidden-claim policy (advisory only)"),
                    )
                )
    return findings


# --------------------------------------------------------------------------- #
# Assumption ledger
# --------------------------------------------------------------------------- #
class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AssumptionStatus(str, Enum):
    OPEN = "open"           # assumed, not yet substantiated
    SUBSTANTIATED = "substantiated"  # backed by evidence/analysis
    RETIRED = "retired"     # superseded or no longer used


class DataLabel(str, Enum):
    """Provenance label for a data value (governance metadata).

    Records how a value was obtained so humans can judge how much to trust it.
    It carries **no engineering-validation meaning**. In particular
    ``LOW_FIDELITY_SCREENING`` marks a coarse screening estimate — not a
    measured, confirmed, or validated result — and ``VERIFIED`` means a human
    checked the data's provenance, not that any engineering performance was
    proven.
    """

    VERIFIED = "verified"
    PUBLIC_SOURCE = "public_source"
    CALCULATED = "calculated"
    ASSUMPTION = "assumption"
    TARGET = "target"
    PLACEHOLDER = "placeholder"
    UNKNOWN = "unknown"
    LOW_FIDELITY_SCREENING = "low_fidelity_screening"


@dataclass
class ReportMetadata:
    """Governance metadata attached to every generated report.

    Reports are **internal by default** and **require human review**. Nothing
    here authorizes external release or implies any engineering validation. The
    defaults are deliberately conservative: ``external_release_allowed`` is
    ``False`` and ``human_review_required`` is ``True``.
    """

    programme: str = ""
    human_review_required: bool = True
    external_release_allowed: bool = False
    internal_only: bool = True
    classification: str = "INTERNAL — human review required"

    def banner(self) -> str:
        """Render the metadata as a Markdown banner for report headers."""
        return (
            f"> **Classification:** {self.classification}  \n"
            f"> **human_review_required:** {str(self.human_review_required).lower()}  \n"
            f"> **external_release_allowed:** {str(self.external_release_allowed).lower()}  \n"
            f"> **internal_only:** {str(self.internal_only).lower()}"
        )


@dataclass
class Assumption:
    """A single engineering assumption used to produce an output."""

    key: str
    statement: str
    value: str
    unit: str = ""
    source: str = "engineering judgement"
    confidence: Confidence = Confidence.LOW
    status: AssumptionStatus = AssumptionStatus.OPEN
    branch: str = "all"
    owner: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AssumptionLedger:
    """A SQLite-backed register of assumptions.

    Use an in-memory ledger (``path=":memory:"``) for tests, or a file path to
    persist across sessions.
    """

    def __init__(self, path: str | Path = ":memory:"):
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS assumptions (
                key        TEXT PRIMARY KEY,
                statement  TEXT NOT NULL,
                value      TEXT NOT NULL,
                unit       TEXT NOT NULL DEFAULT '',
                source     TEXT NOT NULL DEFAULT '',
                confidence TEXT NOT NULL DEFAULT 'low',
                status     TEXT NOT NULL DEFAULT 'open',
                branch     TEXT NOT NULL DEFAULT 'all',
                owner      TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def add(self, assumption: Assumption) -> None:
        """Insert or replace an assumption (keyed by ``assumption.key``)."""
        self._conn.execute(
            """
            INSERT INTO assumptions
                (key, statement, value, unit, source, confidence, status, branch, owner, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                statement=excluded.statement,
                value=excluded.value,
                unit=excluded.unit,
                source=excluded.source,
                confidence=excluded.confidence,
                status=excluded.status,
                branch=excluded.branch,
                owner=excluded.owner
            """,
            (
                assumption.key,
                assumption.statement,
                assumption.value,
                assumption.unit,
                assumption.source,
                assumption.confidence.value,
                assumption.status.value,
                assumption.branch,
                assumption.owner,
                assumption.created_at,
            ),
        )
        self._conn.commit()

    def get(self, key: str) -> Assumption | None:
        row = self._conn.execute(
            "SELECT * FROM assumptions WHERE key = ?", (key,)
        ).fetchone()
        return _row_to_assumption(row) if row else None

    def all(self, *, branch: str | None = None) -> list[Assumption]:
        if branch is None:
            rows = self._conn.execute(
                "SELECT * FROM assumptions ORDER BY key"
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM assumptions WHERE branch IN (?, 'all') ORDER BY key",
                (branch,),
            ).fetchall()
        return [_row_to_assumption(r) for r in rows]

    def open_low_confidence(self) -> list[Assumption]:
        """Assumptions that are open AND low confidence — prime RFI candidates."""
        return [
            a
            for a in self.all()
            if a.status == AssumptionStatus.OPEN and a.confidence == Confidence.LOW
        ]

    def to_records(self) -> list[dict]:
        return [a.__dict__ | {"confidence": a.confidence.value, "status": a.status.value}
                for a in self.all()]

    def close(self) -> None:
        self._conn.close()


def _row_to_assumption(row: sqlite3.Row) -> Assumption:
    return Assumption(
        key=row["key"],
        statement=row["statement"],
        value=row["value"],
        unit=row["unit"],
        source=row["source"],
        confidence=Confidence(row["confidence"]),
        status=AssumptionStatus(row["status"]),
        branch=row["branch"],
        owner=row["owner"],
        created_at=row["created_at"],
    )
