"""Command-line entry point for common HAEN design-support tasks.

Usage:
    haen compare                 # print branch comparison table
    haen simulate                # print low-fidelity simulation results
    haen check <file>            # run forbidden-claim check on a text file
    haen rfi [--branch ID]       # generate an RFI from sample gaps
    haen dossier [--out PATH]    # build the entry validation dossier
"""

from __future__ import annotations

import argparse
import sys

from . import DISCLAIMER, __version__


def _cmd_compare(args) -> int:
    from . import design_space_explorer as dse
    from .sample_data import build_sample_fleet

    fleet = build_sample_fleet()
    result = dse.score_branches(fleet)
    print(result.table.to_string())
    print("\nTrade-off ranking (advisory):")
    print(result.ranking.to_string())
    return 0


def _cmd_simulate(args) -> int:
    from . import low_fidelity_simulation as sim
    from .sample_data import build_sample_fleet

    for r in sim.simulate_all(build_sample_fleet()):
        print(
            f"{r.vehicle_id:16s} top={r.top_speed_kph:6.1f} kph  "
            f"0-100={r.zero_to_100_s:5.2f} s  range={r.estimated_range_km:6.1f} km  "
            f"({r.avg_consumption_kwh_per_100km} kWh/100km)"
        )
    print("\n[low-fidelity estimates; not real-world predictions]")
    return 0


def _cmd_check(args) -> int:
    from .governance import check_text

    text = open(args.file, encoding="utf-8").read()
    findings = check_text(text)
    if not findings:
        print(f"OK — no forbidden claims found in {args.file}")
        return 0
    print(f"FOUND {len(findings)} forbidden claim(s) in {args.file}:")
    for f in findings:
        print(f"  - {f}")
    return 1


def _cmd_rfi(args) -> int:
    from .rfi_builder import build_rfi
    from .sample_data import build_sample_evidence, build_sample_ledger

    rfi = build_rfi(
        title="GT-1 programme — sample RFI",
        branch=args.branch,
        ledger=build_sample_ledger(),
        evidence=build_sample_evidence(),
        expected_components=["Battery pack", "700 bar H2 tanks", "Fuel-cell stack", "Brakes"],
    )
    print(rfi.to_markdown())
    return 0


def _cmd_dossier(args) -> int:
    from .report_builder import build_dossier, save_dossier
    from .rfi_builder import build_rfi
    from .sample_data import build_sample_evidence, build_sample_fleet, build_sample_ledger

    fleet = build_sample_fleet()
    ledger = build_sample_ledger()
    evidence = build_sample_evidence()
    rfi = build_rfi(title="GT-1 RFI", branch=args.branch, ledger=ledger, evidence=evidence)
    text = build_dossier(
        programme="HAEN GT-1",
        branch=args.branch,
        vehicles=fleet,
        evidence=evidence,
        ledger=ledger,
        rfi=rfi,
    )
    if args.out:
        path = save_dossier(text, args.out)
        print(f"Dossier written to {path}")
    else:
        print(text)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="haen", description=DISCLAIMER)
    p.add_argument("--version", action="version", version=f"haen {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("compare", help="branch comparison table").set_defaults(func=_cmd_compare)
    sub.add_parser("simulate", help="low-fidelity simulation").set_defaults(func=_cmd_simulate)

    pc = sub.add_parser("check", help="forbidden-claim check on a file")
    pc.add_argument("file")
    pc.set_defaults(func=_cmd_check)

    pr = sub.add_parser("rfi", help="generate a sample RFI")
    pr.add_argument("--branch", default="all")
    pr.set_defaults(func=_cmd_rfi)

    pd = sub.add_parser("dossier", help="build entry validation dossier")
    pd.add_argument("--branch", default="GT-1")
    pd.add_argument("--out", default=None)
    pd.set_defaults(func=_cmd_dossier)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
