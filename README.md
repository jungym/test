# SafeCopy Core

**AI 시대의 개인·소규모 조직용 로컬 데이터 방화벽** — a local data firewall.

SafeCopy Core detects sensitive information *before* it leaves your machine
through external paths (AI prompt boxes, clipboard, browser uploads, messengers,
cloud, USB) and **masks, substitutes, blocks, approves, or logs** it — all
locally. Unlike antivirus/EDR, which hunt malware and suspicious processes,
SafeCopy Core prevents *normal apps and normal users* from accidentally
exporting sensitive data.

## What it does

When you copy or paste text, SafeCopy Core runs it through a local pipeline:

```
detect ─▶ policy ─▶ mask ─▶ vault + audit
```

1. **detect** — scan for emails, phone numbers, Korean RRNs, account/card
   numbers, API keys, SSH private keys, and `.env`/DB secrets.
2. **policy** — decide an action from *data type + destination + user action +
   risk*: `ALLOW` / `WARN` / `MASK` / `REQUIRE_APPROVAL` / `BLOCK`.
3. **mask** — replace findings with stable tokens (`[PHONE_001]`,
   `[API_KEY_BLOCKED]`). Critical secrets are blocked, never tokenized.
4. **vault + audit** — store reversible token↔original mappings in a local
   encrypted Vault, and append a no-originals-by-default audit record.

The MVP targets **Windows 11** and clipboard text. See
[`기능명세서.md`](기능명세서.md) for the full feature spec and
[`CLAUDE.md`](CLAUDE.md) for the architecture and developer workflow.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev,clipboard]"

# scan some text and see findings + the policy decision
echo "내 번호 010-1234-5678, API_KEY=sk_live_abcdef0123456789ABCD" | safecopy scan --destination AI
```

## Development

```bash
pytest            # run the test suite
ruff check .      # lint
black .           # format
mypy              # type-check
```

> **Status:** v0.1, pre-release. The core engine and a demo CLI are implemented;
> the Windows tray app and policy-settings UI (MVP item 8) are not yet built.
