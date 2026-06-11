"""Command-line entry point for common HAEN design-support tasks.

All data-consuming commands accept ``--project <haen-project.yaml>`` to run on
real, human-authored data; without it they fall back to the bundled sample so the
commands work out of the box. Nothing here performs any external action and every
generated artifact is internal-only and human-review-required.

Usage:
    haen compare [--project P]      # branch comparison table
    haen simulate [--project P]     # low-fidelity simulation results
    haen screen [--project P]       # braking + load-transfer dynamics screening
    haen check <file>               # run forbidden-claim check on a text file
    haen rfi [--project P]          # generate an RFI (incl. completeness prompts)
    haen dossier [--project P]      # build the entry validation dossier
    haen export --out DIR           # internal review package
    haen validate <dir|zip>         # validate an internal package
    haen readiness [--project P]    # internal release-readiness checklist
    haen release-candidate --out D  # full internal release candidate package
"""

from __future__ import annotations

import argparse
import sys

from . import DISCLAIMER, __version__


# --------------------------------------------------------------------------- #
# Project loading (sample fallback) + shared helpers
# --------------------------------------------------------------------------- #
def _project(args):
    """Load the project from ``--project`` or fall back to the bundled sample."""
    path = getattr(args, "project", None)
    if path:
        from . import io

        return io.load_project(path)
    from .sample_data import build_sample_project

    return build_sample_project()


def _rfi_for(proj, branch: str):
    from .rfi_builder import build_rfi

    expected = [c.name for c in proj.components] or None
    return build_rfi(
        title=f"{proj.programme} RFI",
        branch=branch,
        ledger=proj.ledger,
        evidence=proj.evidence,
        expected_components=expected,
        partners=proj.partners,
        vehicles=proj.vehicles,
    )


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def _cmd_compare(args) -> int:
    from . import design_space_explorer as dse

    result = dse.score_branches(_project(args).vehicles)
    print(result.table.to_string())
    print("\nTrade-off ranking (advisory):")
    print(result.ranking.to_string())
    return 0


def _cmd_simulate(args) -> int:
    from . import low_fidelity_simulation as sim

    results = sim.simulate_all(_project(args).vehicles)
    for r in results:
        flag = "  [!] top-speed = MODEL ARTIFACT" if r.top_speed_is_artifact else ""
        print(
            f"{r.vehicle_id:16s} top={r.top_speed_kph:6.1f} kph  "
            f"0-100={r.zero_to_100_s:5.2f} s  range={r.estimated_range_km:6.1f} km  "
            f"({r.avg_consumption_kwh_per_100km} kWh/100km){flag}"
        )
    for r in results:
        for w in r.warnings:
            print(f"\n[!] {r.vehicle_id}: {w}")
    print("\n[low-fidelity screening estimates; not real-world predictions]")
    return 0


def _cmd_screen(args) -> int:
    from . import low_fidelity_simulation as sim

    print("Dynamics screening (low_fidelity_screening — not vehicle-dynamics validation):")
    for v in _project(args).vehicles:
        b = sim.screen_braking(vehicle_id=v.id)
        lt = sim.screen_load_transfer_for(v)
        print(
            f"  {v.id:16s} brake_decel={b.deceleration_mps2:5.2f} m/s^2  "
            f"stop@100kph={b.stopping_distance_m:6.1f} m  "
            f"long_LT={lt.longitudinal_load_transfer_n:8.1f} N  "
            f"lat_LT={lt.lateral_load_transfer_n:8.1f} N"
        )
    print("\n[braking mu=1.0@100kph; load transfer ~1g; idealized rigid-body screening only]")
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
    print(_rfi_for(_project(args), args.branch).to_markdown())
    return 0


def _cmd_dossier(args) -> int:
    from .report_builder import build_dossier, save_dossier

    proj = _project(args)
    rfi = _rfi_for(proj, args.branch)
    text = build_dossier(
        programme=proj.programme,
        branch=args.branch,
        vehicles=proj.vehicles,
        evidence=proj.evidence,
        ledger=proj.ledger,
        rfi=rfi,
        components=proj.components,
    )
    if args.out:
        path = save_dossier(text, args.out)
        print(f"Dossier written to {path}")
    else:
        print(text)
    return 0


def _cmd_export(args) -> int:
    from .export import export_release_package, validate_release
    from .report_builder import build_dossier

    proj = _project(args)
    rfi = _rfi_for(proj, args.branch)
    text = build_dossier(
        programme=proj.programme, branch=args.branch, vehicles=proj.vehicles,
        components=proj.components, evidence=proj.evidence, ledger=proj.ledger, rfi=rfi,
    )
    pkg = export_release_package(
        text, args.out, programme=proj.programme, branch=args.branch,
        components=proj.components, vehicle=proj.vehicles[0], rfi_markdown=rfi.to_markdown(),
    )
    print(f"Internal release package written to {pkg.out_dir}")
    for name in sorted(pkg.files):
        print(f"  {name}  {pkg.files[name][:12]}…")
    problems = validate_release(pkg.out_dir)
    print("Validation:", "OK" if not problems else f"{len(problems)} problem(s): {problems}")
    print("  [INTERNAL ONLY — human review required; external release not allowed]")
    return 0 if not problems else 1


def _cmd_readiness(args) -> int:
    from .report_builder import build_dossier, build_release_readiness, release_readiness_md

    proj = _project(args)
    text = build_dossier(programme=proj.programme, branch=args.branch, vehicles=proj.vehicles)
    checklist = build_release_readiness(dossier_text=text)
    print(release_readiness_md(checklist))
    return 0


def _cmd_release_candidate(args) -> int:
    """Build the full internal release candidate package (internal-only).

    Reuses the canonical reproducibility mechanism in haen.export: passing
    --generated-at enables reproducible mode (fixed timestamp, PNGs suppressed,
    byte-stable package + archive). No external action of any kind.
    """
    from . import mass_energy
    from .export import archive_release, export_release_package, validate_release
    from .governance import semantic_risk_scan
    from .report_builder import build_dossier, build_release_readiness, release_readiness_md

    proj = _project(args)
    generated = args.generated_at
    reproducible = generated is not None

    rfi = _rfi_for(proj, args.branch)
    text = build_dossier(
        programme=proj.programme, branch=args.branch, vehicles=proj.vehicles,
        components=proj.components, evidence=proj.evidence, ledger=proj.ledger,
        rfi=rfi, generated_at=generated,
    )
    pkg = export_release_package(
        text, args.out, programme=proj.programme, branch=args.branch,
        generated_at=generated, components=proj.components, vehicle=proj.vehicles[0],
        rfi_markdown=rfi.to_markdown(), reproducible=reproducible,
    )

    problems = validate_release(pkg.out_dir)
    dossier_text = pkg.out_dir.joinpath("dossier.md").read_text(encoding="utf-8")
    checklist = build_release_readiness(
        dossier_text=dossier_text,
        validation_problems=problems,
        semantic_findings=len(semantic_risk_scan(dossier_text)),
        completeness=mass_energy.metadata_completeness(proj.vehicles[0]),
    )
    (pkg.out_dir / "readiness.md").write_text(
        release_readiness_md(checklist), encoding="utf-8"
    )
    archive = archive_release(pkg.out_dir, generated_at=generated)

    print(f"Internal release candidate written to {pkg.out_dir}")
    print(f"  reproducible: {reproducible}")
    print(f"  archive: {archive.name} (+ {archive.name}.sha256 sidecar)")
    print("  validation:", "OK" if not problems else f"{len(problems)} problem(s): {problems}")
    print("  [INTERNAL ONLY — human review required; external release not allowed]")
    return 0 if not problems else 1


def _cmd_validate(args) -> int:
    from .export import validate_release, validate_release_archive

    target = args.path or args.dir
    if not target:
        print("error: provide a package directory or .zip archive (positional or --dir)")
        return 2
    if str(target).endswith(".zip"):
        problems = validate_release_archive(target)
    else:
        problems = validate_release(target)
    if not problems:
        print(f"OK — release package at {target} is valid and internal-only")
        return 0
    print(f"INVALID — {len(problems)} problem(s):")
    for p in problems:
        print(f"  - {p}")
    return 1


def _add_project(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--project", default=None,
        help="path to a haen-project.yaml manifest (default: bundled sample data)",
    )


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="haen", description=DISCLAIMER)
    p.add_argument("--version", action="version", version=f"haen {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pcmp = sub.add_parser("compare", help="branch comparison table")
    pcmp.set_defaults(func=_cmd_compare)
    psim = sub.add_parser("simulate", help="low-fidelity simulation")
    psim.set_defaults(func=_cmd_simulate)
    psc = sub.add_parser("screen", help="braking + load-transfer dynamics screening")
    psc.set_defaults(func=_cmd_screen)
    for sp in (pcmp, psim, psc):
        _add_project(sp)

    pc = sub.add_parser("check", help="forbidden-claim check on a file")
    pc.add_argument("file")
    pc.set_defaults(func=_cmd_check)

    pr = sub.add_parser("rfi", help="generate an RFI (incl. completeness prompts)")
    pr.add_argument("--branch", default="all")
    _add_project(pr)
    pr.set_defaults(func=_cmd_rfi)

    pd = sub.add_parser("dossier", help="build entry validation dossier")
    pd.add_argument("--branch", default="GT-1")
    pd.add_argument("--out", default=None)
    _add_project(pd)
    pd.set_defaults(func=_cmd_dossier)

    pe = sub.add_parser("export", help="export an internal review package (dossier + images + manifest)")
    pe.add_argument("--branch", default="GT-1")
    pe.add_argument("--out", required=True, help="output directory for the internal package")
    _add_project(pe)
    pe.set_defaults(func=_cmd_export)

    pv = sub.add_parser(
        "validate", help="validate an exported internal review package (dir or .zip)"
    )
    pv.add_argument("path", nargs="?", default=None,
                    help="package directory or .zip archive")
    pv.add_argument("--dir", default=None, help="package directory (legacy flag)")
    pv.set_defaults(func=_cmd_validate)

    prr = sub.add_parser("readiness", help="print the internal release-readiness checklist")
    prr.add_argument("--branch", default="GT-1")
    _add_project(prr)
    prr.set_defaults(func=_cmd_readiness)

    prc = sub.add_parser(
        "release-candidate",
        help="build the full internal release-candidate package (internal-only)",
    )
    prc.add_argument("--out", required=True, help="output directory for the internal package")
    prc.add_argument("--branch", default="GT-1")
    prc.add_argument(
        "--generated-at", default=None,
        help="fixed ISO timestamp; enables reproducible mode (shared export mechanism)",
    )
    _add_project(prc)
    prc.set_defaults(func=_cmd_release_candidate)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
