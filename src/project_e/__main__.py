"""Project E command line entry point."""

from __future__ import annotations

import argparse
import sys

from .simulation.runner import run


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="project-e", description="Project E reduced-order energy system models")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("simulate", help="run the architecture comparison for a configuration")
    s.add_argument("--config", default="configs/baseline.yaml")
    s.add_argument("--scenario", default=None, help="optional scenario override YAML")
    s.add_argument("--out", default="results/runs")
    s.add_argument("--no-plots", action="store_true")

    sen = sub.add_parser("sensitivity", help="one-at-a-time sensitivity and cost Monte Carlo")
    sen.add_argument("--config", default="configs/baseline.yaml")
    sen.add_argument("--out", default="reports/SENSITIVITY_ANALYSIS.md")
    sen.add_argument("--samples", type=int, default=2000)
    sen.add_argument("--seed", type=int, default=20261022)

    st = sub.add_parser("study", help="deterministic sizing and mission-scaling studies")
    st.add_argument("--config", default="configs/baseline.yaml")
    st.add_argument("--kind", choices=["sizing", "mission", "all"], default="all")

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "simulate":
        summary = run(args.config, args.scenario, args.out, make_plots=not args.no_plots)
        print(f"run_id: {summary['run_id']}")
        print(f"runtime: {summary['runtime_s']} s")
        for key, m in summary["architecture_metrics"].items():
            print(
                f"{key:>3}  {m['name'][:46]:<46} "
                f"mass {m['mass_kg']:7.1f} kg  capex ${m['capex_usd']:8,.0f}  "
                f"LCOE ${m['lcoe_usd_per_kwh']:.3f}/kWh  targets {m['targets_met']}/5"
            )
        return 0
    if args.command == "sensitivity":
        from .simulation.sensitivity import run_sensitivity

        path = run_sensitivity(args.config, args.out, samples=args.samples, seed=args.seed)
        print(f"wrote {path}")
        return 0
    if args.command == "study":
        from .simulation.studies import run_mission_study, run_sizing_study

        if args.kind in ("sizing", "all"):
            print(f"wrote {run_sizing_study(args.config)}")
        if args.kind in ("mission", "all"):
            print(f"wrote {run_mission_study(args.config)}")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
