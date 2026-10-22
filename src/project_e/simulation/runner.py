"""Reproducible simulation runner: load config, evaluate architectures, persist artifacts."""

from __future__ import annotations

import csv
import json
import pathlib
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ..config import config_checksum, load_config, resolve, write_provenance_csv
from ..economics import CostStreams
from .architectures import ArchResult, all_architectures
from .dispatch import Mission

ROOT = pathlib.Path(__file__).resolve().parents[3]


def git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return "uncommitted"


def lcoe_for(
    r: ArchResult,
    cfg: dict,
    capex_scale: float = 1.0,
    fuel_scale: float = 1.0,
) -> tuple[float, CostStreams]:
    a = cfg["assumptions"]
    annual_energy = r.delivered_kwh * a["missions_per_year"]
    streams = CostStreams(
        capex_usd=r.capex_usd * capex_scale,
        annual_energy_kwh=annual_energy,
        annual_om_usd=r.annual_om_usd,
        annual_fuel_usd=r.fuel_cost_usd * a["missions_per_year"] * fuel_scale,
        replacements_usd={y: c * capex_scale for y, c in r.replacements_usd.items()},
        lifetime_years=a["lifetime_years"],
        discount_rate=a["discount_rate"],
    )
    return streams.lcoe_usd_per_kwh, streams


def target_checks(r: ArchResult, cfg: dict, lcoe: float) -> dict[str, bool]:
    t = cfg["targets"]
    return {
        "mass": bool(r.mass_kg <= t["mass_kg"]),
        "volume": bool(r.volume_l <= t["volume_l"]),
        "capex": bool(r.capex_usd <= t["capex_usd"]),
        "lcoe": bool(lcoe <= t["lcoe_usd_per_kwh"]),
        "unmet": bool(r.unmet_kwh <= 1e-6),
    }


def _validate_thermal_feasibility(cfg: dict) -> None:
    """A coolant at or below ambient cannot reject heat by convection.

    This is a hard physical constraint, not a numerical tolerance: reject the
    configuration with an actionable message instead of returning an infinite radiator.
    """
    a = cfg["assumptions"]
    coolants = {
        "battery_coolant_c": a["battery_coolant_c"],
        "coolant_c": a["coolant_c"],
        "teg cold side": cfg["teg"]["cold_c"],
        "tpv cell": cfg["tpv"]["cold_c"],
    }
    for name, temp in coolants.items():
        if temp <= a["ambient_c"]:
            raise ValueError(
                f"{name} ({temp} C) must exceed ambient ({a['ambient_c']} C) to reject heat; "
                "active cooling or a lower ambient assumption is required"
            )


def check_invariants(results: list[ArchResult], mission: Mission) -> list[str]:
    problems = []
    for r in results:
        # Only the hybrids are dispatched. Direct architectures set delivered and
        # unmet analytically from their rating, so checking those two values there
        # would be tautological; their mass/cost/heat invariants are still checked.
        if r.key in {"C1", "C2"}:
            if abs(r.delivered_kwh - mission.energy_kwh) > 1e-3:
                problems.append(f"{r.key}: delivered {r.delivered_kwh:.4f} != mission {mission.energy_kwh:.4f}")
            if r.unmet_kwh > 1e-6:
                problems.append(f"{r.key}: unmet load {r.unmet_kwh:.6g} kWh")
        if not (0 < r.efficiency <= 1):
            problems.append(f"{r.key}: efficiency outside (0,1]: {r.efficiency}")
        if r.mass_kg <= 0 or r.capex_usd <= 0:
            problems.append(f"{r.key}: non-positive mass or capex")
        if r.waste_heat_kw < 0:
            problems.append(f"{r.key}: negative waste heat")
    return problems


def _plots(results: list[ArchResult], lcoes: dict[str, float], cfg: dict, fig_dir: pathlib.Path) -> list[str]:
    fig_dir.mkdir(parents=True, exist_ok=True)
    made = []
    t = cfg["targets"]

    fig, ax = plt.subplots(figsize=(8, 5.5))
    for r in results:
        ax.scatter(r.mass_kg, lcoes[r.key], s=70)
        ax.annotate(r.key, (r.mass_kg, lcoes[r.key]), textcoords="offset points", xytext=(6, 4))
    ax.axvline(t["mass_kg"], ls="--", color="grey", label=f"mass target {t['mass_kg']} kg")
    ax.axhline(t["lcoe_usd_per_kwh"], ls=":", color="grey", label=f"LCOE target {t['lcoe_usd_per_kwh']} $/kWh")
    ax.set_xscale("log")
    ax.set_xlabel("system mass [kg] (log scale)")
    ax.set_ylabel("levelized cost of delivered energy [USD/kWh]")
    ax.set_title("Project E architecture trade-off (baseline)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    path = fig_dir / "mass_vs_lcoe.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    made.append(f"figures/{path.name}")

    fig, ax = plt.subplots(figsize=(9, 4.8))
    keys = [r.key for r in results]
    vals = [lcoes[k] for k in keys]
    colors = ["#2a6fdb" if v <= t["lcoe_usd_per_kwh"] else "#c44e52" for v in vals]
    ax.bar(keys, vals, color=colors)
    ax.axhline(t["lcoe_usd_per_kwh"], ls=":", color="grey")
    ax.set_ylabel("LCOE [USD/kWh]")
    ax.set_title("Levelized cost by architecture (10 a, 8% discount)")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    path = fig_dir / "lcoe_by_architecture.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    made.append(f"figures/{path.name}")

    fig, ax = plt.subplots(figsize=(8, 5))
    for r in results:
        ax.scatter(r.mass_kg, r.efficiency * 100, s=70)
        ax.annotate(r.key, (r.mass_kg, r.efficiency * 100), textcoords="offset points", xytext=(6, 4))
    ax.set_xscale("log")
    ax.set_xlabel("system mass [kg] (log scale)")
    ax.set_ylabel("source-to-load efficiency [%]")
    ax.set_title("Efficiency versus mass")
    ax.grid(alpha=0.3)
    path = fig_dir / "efficiency_vs_mass.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    made.append(f"figures/{path.name}")
    return made


def evaluate(cfg_raw: dict) -> tuple[object, object, list[ArchResult], dict[str, float]]:
    """Evaluate all architectures for an already-loaded config (no artifacts written)."""
    cfg = resolve(cfg_raw)
    _validate_thermal_feasibility(cfg)
    mission = Mission(**cfg["mission"])
    results = all_architectures(mission, cfg)
    problems = check_invariants(results, mission)
    if problems:
        raise RuntimeError("invariant failures: " + "; ".join(problems))
    lcoes = {r.key: lcoe_for(r, cfg)[0] for r in results}
    return mission, cfg, results, lcoes


def run(
    config_path: str | pathlib.Path,
    scenario: str | pathlib.Path | None = None,
    out_root: str | pathlib.Path = "results/runs",
    make_plots: bool = True,
) -> dict:
    started = time.perf_counter()
    raw_cfg = load_config(config_path, scenario)
    cfg = resolve(raw_cfg)
    _validate_thermal_feasibility(cfg)
    mission = Mission(**cfg["mission"])
    results = all_architectures(mission, cfg)
    problems = check_invariants(results, mission)
    if problems:
        raise RuntimeError("invariant failures: " + "; ".join(problems))

    metrics = {}
    for r in results:
        lcoe, streams = lcoe_for(r, cfg)
        checks = target_checks(r, cfg, lcoe)
        metrics[r.key] = {
            "name": r.name,
            "class": r.architecture_class,
            "source": r.energy_source,
            "delivered_kwh": round(r.delivered_kwh, 4),
            "input_kwh": round(r.input_kwh, 4),
            "efficiency": round(r.efficiency, 4),
            "mass_kg": round(r.mass_kg, 2),
            "volume_l": round(r.volume_l, 1),
            "capex_usd": round(r.capex_usd, 0),
            "lcoe_usd_per_kwh": round(lcoe, 4),
            "waste_heat_kw": round(r.waste_heat_kw, 3),
            "radiator_area_m2": round(r.radiator_area_m2, 2),
            "unmet_kwh": r.unmet_kwh,
            "targets": checks,
            "targets_met": sum(checks.values()),
            "notes": list(r.notes),
            "evidence": r.evidence,
        }

    stamp = datetime.now(timezone.utc)
    checksum = config_checksum(raw_cfg)
    run_id = f"{stamp:%Y%m%dT%H%M%SZ}_{checksum[:8]}"
    run_dir = pathlib.Path(out_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    (run_dir / "config.resolved.json").write_text(
        json.dumps(cfg, indent=2, default=str)
    )
    (run_dir / "mission.json").write_text(json.dumps(cfg["mission"], indent=2))
    write_provenance_csv(raw_cfg, run_dir / "provenance.csv")

    summary = {
        "run_id": run_id,
        "timestamp_utc": stamp.isoformat(),
        "git_commit": git_commit(),
        "config_checksum_sha256": checksum,
        "software": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "numpy": __import__("numpy").__version__,
            "scipy": __import__("scipy").__version__,
        },
        "mission": cfg["mission"],
        "targets": cfg["targets"],
        "architecture_metrics": metrics,
        "invariants": "passed",
        "warnings": [
            "Component parameters are estimates; no hardware was measured.",
            "Mass and cost are parametric estimates, not bills of materials.",
            "Diesel emissions and noise are not modeled.",
        ],
        "runtime_s": None,
    }

    if make_plots:
        summary["figures"] = _plots(results, {k: v["lcoe_usd_per_kwh"] for k, v in metrics.items()},
                                     cfg, run_dir / "figures")

    with (run_dir / "architectures.csv").open("w", newline="") as fh:
        fields = ["key", "name", "class", "source", "delivered_kwh", "input_kwh", "efficiency",
                  "mass_kg", "volume_l", "capex_usd", "lcoe_usd_per_kwh", "waste_heat_kw",
                  "radiator_area_m2", "unmet_kwh", "targets_met"]
        w = csv.writer(fh)
        w.writerow(fields)
        for key, m in metrics.items():
            w.writerow([key, m["name"], m["class"], m["source"], m["delivered_kwh"], m["input_kwh"],
                        m["efficiency"], m["mass_kg"], m["volume_l"], m["capex_usd"],
                        m["lcoe_usd_per_kwh"], m["waste_heat_kw"], m["radiator_area_m2"],
                        m["unmet_kwh"], m["targets_met"]])

    summary["runtime_s"] = round(time.perf_counter() - started, 2)
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    (run_dir / "report.md").write_text(render_report(summary))
    return summary


def render_report(s: dict) -> str:
    m = s["architecture_metrics"]
    lines = [
        f"# Simulation report — {s['run_id']}",
        "",
        f"- git commit: `{s['git_commit']}`",
        f"- config checksum: `{s['config_checksum_sha256'][:16]}…`",
        f"- runtime: {s['runtime_s']} s",
        f"- mission: {s['mission']['base_load_kw']} kW base, {s['mission']['peak_load_kw']} kW peak, "
        f"{s['mission']['duration_h']} h",
        "",
        "## Architecture results",
        "",
        "| Key | Architecture | Delivered kWh | Efficiency | Mass kg | Capex USD | LCOE $/kWh | Targets met (of 5) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for key, r in m.items():
        lines.append(
            f"| {key} | {r['name']} | {r['delivered_kwh']:.2f} | {r['efficiency']:.1%} | "
            f"{r['mass_kg']:.1f} | {r['capex_usd']:,.0f} | {r['lcoe_usd_per_kwh']:.3f} | "
            f"{r['targets_met']} |"
        )
    lines += [
        "",
        "## Targets",
        "",
        "| Metric | Target |",
        "|---|---:|",
        f"| Mass | ≤ {s['targets']['mass_kg']} kg |",
        f"| Volume | ≤ {s['targets']['volume_l']} L |",
        f"| Capex | ≤ ${s['targets']['capex_usd']:,.0f} |",
        f"| LCOE | ≤ ${s['targets']['lcoe_usd_per_kwh']:.2f}/kWh |",
        "",
        "All delivered-energy values are model outputs for the defined mission, not measured data.",
        "Component parameters are parameterised estimates (see `provenance.csv`).",
        "",
        "## Warnings",
        "",
    ]
    lines += [f"- {w}" for w in s["warnings"]]
    return "\n".join(lines) + "\n"
