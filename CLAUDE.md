# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

**SafeCopy Core** — a local **data firewall** (로컬 데이터 방화벽). It detects
sensitive information *before* it leaves the machine through external paths (AI
prompt boxes, clipboard, browser uploads, messengers, cloud, USB) and masks,
substitutes, blocks, requires approval, or logs it — entirely locally.

The framing matters and should guide every change: this is **not** antivirus or
EDR. It does not hunt malware or suspicious processes. It guards against *normal
apps and normal users* accidentally exporting sensitive data (e.g. pasting an
API key into ChatGPT). When in doubt about a feature, ask "does this reduce
accidental sensitive-data egress?" — if not, it's probably out of scope.

The full product spec is [`기능명세서.md`](기능명세서.md); the user-facing intro is
[`README.md`](README.md). This file is the engineering view.

## Project status

v0.1, pre-release. The **core engine and a demo CLI are implemented and tested**.
The production product is a Windows 11 tray app with a policy-settings UI — that
GUI layer (MVP item 8) and real clipboard hooks are **not yet built**. The CLI
(`safecopy scan`) exists purely so the engine can run without the GUI. Tech
stack is Python 3.11+ (chosen over a native Windows stack for prototyping speed).

## Commands

Setup (one time):

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"            # add ,clipboard for the pyperclip backend
```

Day-to-day:

```bash
pytest                              # full suite
pytest tests/test_policy.py         # one file
pytest tests/test_policy.py::test_api_key_to_ai_is_blocked   # one test
pytest -k masking                   # by keyword

ruff check . && ruff check --fix .  # lint (autofix)
black .                             # format (line length 100)
mypy                                # type-check (strict)

echo "010-1234-5678" | safecopy scan --destination AI   # exercise the engine
```

Run **ruff, black, mypy, and pytest** before committing — all four are expected
to pass clean, and mypy runs in `strict` mode.

## Architecture: the pipeline

The whole product is one linear pipeline. Understanding it is understanding the
codebase:

```
detect ─▶ evaluate (policy) ─▶ mask ─▶ vault.store + audit.record
```

`pipeline.py::Guard.inspect()` is the **single orchestrator** that runs all
stages for one copy/paste interception. Everything it depends on (Vault, AuditLog,
Settings) is injected — there is no global state — so it stays unit-testable.
The clipboard monitor and (future) UI are the only callers of `Guard`.

Each stage is its own package under `src/safecopy_core/` and the stages only
depend *forward*, never backward:

| Stage | Package | Responsibility |
|-------|---------|----------------|
| detect | `detection/` | Pure function `detect(text) -> list[Finding]`. Regex registry in `patterns.py`; `detector.py` enforces **non-overlapping, position-sorted** findings. |
| risk | `detection/types.py` | `RiskLevel` (LOW→CRITICAL). Each pattern carries a default risk. |
| policy | `policy/` | `evaluate(findings, destination) -> Decision`. Rule **table** in `rules.py` (data, editable by the future UI), engine in `engine.py`. |
| mask | `masking/` | `mask(text, findings) -> MaskResult`. Tokenizes findings; **blocks** CRITICAL secrets instead of tokenizing them. |
| vault | `vault/` | Encrypted local token↔original store. |
| audit | `audit/` | Append-only JSON-lines log of *attempts*. |

Platform edges are deliberately kept thin and dumb, isolating OS-specific code:
`clipboard/monitor.py` (poll loop + pluggable backends) and `__main__.py` (CLI).

### Key invariants — do not break these

These encode product guarantees from the spec. Tests enforce them; treat them as
load-bearing:

- **Findings are non-overlapping and position-sorted.** The masking engine
  splices tokens by character offset and relies on this. When two patterns match
  the same span, the one listed **earlier** in `patterns.PATTERNS` wins, so order
  that list high-risk/specific → low-risk/generic (secrets before generic digit
  runs before email/phone).
- **CRITICAL secrets are never stored.** API keys, SSH private keys, and `.env`
  secrets are masked to `[<TYPE>_BLOCKED]` with a non-reversible mapping whose
  Vault value is the `BLOCKED` marker (`원문 반출 금지`), never the real secret.
  Only lower-risk findings (email/phone/RRN) get reversible tokens.
- **A payload is only as safe as its most sensitive token.** The policy
  `Decision` is the **most restrictive** action across all findings (`Action` is
  an ordered `IntEnum`, `ALLOW=0 … BLOCK=4`, so the engine takes the max).
- **Everything stays local.** No network calls anywhere in the pipeline. The
  Vault is a local encrypted file; do not add cloud sync.
- **Originals are not written to the audit log by default**
  (`Settings.store_originals_in_audit=False`). The audit log records *what was
  attempted* (types, action, destination) — not the sensitive text.

### How the policy decision is made

`데이터 유형 + 목적지 앱 + 사용자 행위 + 위험도 = 조치`. Concretely:
`rules.lookup_action` checks the `_overrides()` table for a specific
`(DataType, Destination)` rule first (e.g. API_KEY→AI = BLOCK, PHONE→AI = MASK),
and falls back to `default_by_risk()` otherwise. To change product behavior,
edit the **rule table in `rules.py`**, not the engine. Keep rules as data so the
policy-settings UI can eventually own them.

### Conventions specific to this codebase

- **Enum value strings are stable identifiers.** `DataType` values appear in
  masking tokens (`EMAIL` → `[EMAIL_001]`) and audit logs. Renaming one is a
  data migration, not a refactor — don't do it casually.
- **`rules.py` imports `Action` lazily** (inside functions) to avoid a circular
  import with `engine.py`, which imports `Destination` from `rules.py`. Keep that
  shape if you touch either file.
- **Latency budget: 300ms** end-to-end paste (spec success criterion). The detect
  stage is the hot path and must stay pure and allocation-light; don't add I/O or
  network there.
- Clipboard backends implement the `ClipboardBackend` Protocol. Tests and the demo
  use `InMemoryBackend`; never make the engine depend on a real OS clipboard.

## Adding a new detector (the most common change)

1. Add a `DataType` member in `detection/types.py` (stable string value).
2. Add a `Pattern(data_type, regex, default_risk)` to `patterns.PATTERNS`, placed
   correctly by specificity/risk (earlier = higher precedence on overlap).
3. Add any non-default policy overrides in `policy/rules.py`.
4. Add tests covering detection, masking (reversible vs blocked), and the policy
   action — mirror the existing `tests/test_*.py` structure.

## Out of scope (per the spec — don't build these)

Kernel drivers, a full EDR, mobile-wide control, wireless/RF features, monitoring
other people's devices, and any offensive/intrusion capability. SafeCopy is
defensive and local-only.
