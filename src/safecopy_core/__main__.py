"""CLI entry point: ``safecopy``.

A thin developer/demo front-end over the pipeline. The production product is a
Windows tray app with a policy-settings UI (MVP item 8); this CLI exists so the
core engine can be exercised without that UI.

Subcommands:
  scan   - read text from --text or stdin, print findings + the policy action
           for a given --destination, and the masked output.
"""

from __future__ import annotations

import argparse
import sys

from .audit import AuditLog
from .config import Settings
from .pipeline import Guard
from .policy import Action, Destination
from .vault import Vault


def _cmd_scan(args: argparse.Namespace) -> int:
    text = args.text if args.text is not None else sys.stdin.read()
    settings = Settings()
    vault = Vault.open(settings.vault_path, passphrase=args.passphrase)
    audit = AuditLog(settings.audit_path)
    guard = Guard(vault, audit, settings)

    result = guard.inspect(
        text,
        destination=Destination[args.destination],
        app=args.app,
        scope=args.scope,
    )

    print(f"action: {result.action.name}")
    print(f"destination: {result.decision.destination.value}")
    print("findings:")
    for f in result.findings:
        print(f"  - {f.data_type.value} (risk={f.risk.name}) {f.text!r}")
    if result.safe_text is not None:
        print("masked:")
        print(result.safe_text)
    return 0 if result.action is not Action.BLOCK else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="safecopy", description="SafeCopy Core engine CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan text and print findings + policy action")
    scan.add_argument("--text", default=None, help="text to scan (default: read stdin)")
    scan.add_argument(
        "--destination",
        default="AI",
        choices=[d.name for d in Destination],
        help="where the data is headed",
    )
    scan.add_argument("--app", default="cli", help="originating app name for the audit log")
    scan.add_argument("--scope", default="default", help="vault namespace (app/document)")
    scan.add_argument(
        "--passphrase",
        default="dev-passphrase",
        help="vault passphrase (demo only; real UI prompts securely)",
    )
    scan.set_defaults(func=_cmd_scan)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
