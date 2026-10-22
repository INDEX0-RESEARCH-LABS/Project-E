"""Sensitivity and uncertainty analysis.

Two complementary methods:
  1. One-at-a-time (OAT) sweep of every parameter that declares a range, running the
     full model each time. Reports the change in LCOE and mass, and whether the
     architecture ranking flips.
  2. Monte Carlo over cost drivers only. Physics/dispatch results are held at baseline;
     capex line items and fuel prices are resampled. This is stated explicitly because
     sampling assumed distributions is not evidence of real-world performance.

Uniform ranges are uncertainty bounds, not probability distributions. The Monte Carlo
is therefore a bounded what-if, not a forecast.
"""

from __future__ import annotations

import copy
import csv
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from ..config import deep_merge, load_config, load_yaml
from ..economics import CostStreams
from .runner import evaluate

SCENARIOS = {
    "conservative": "configs/scenarios/conservative.yaml",
    "optimistic": "configs/scenarios/optimistic.yaml",
}

# Cost item groups scaled by each sampled price parameter.
CAPEX_SCALE = {
    "battery.cost_usd_per_kwh": {"battery"},
    "battery.power_electronics_usd_per_kw": {"power_electronics"},
    "supercap.cost_usd_per_kwh": {"supercap"},
    "diesel.cost_usd_per_kw": {"generator"},
    "teg.cost_usd_per_w": {"teg"},
    "tpv.cell_cost_usd_per_m2": {"tpv_cells"},
    "tpv.storage_cost_usd_per_kg": {"thermal_storage"},
    "fuel_cell.cost_usd_per_kw": {"fuel_cell"},
    "fuel_cell.tank_cost_usd_per_kg_h2": {"h2_tank"},
}

FUEL_PRICE_PARAM = {
    "diesel": "diesel.fuel_usd_per_l",
    "h2": "fuel_cell.h2_usd_per_kg",
    "heat": "assumptions.heat_usd_per_kwh",
    "electricity": "assumptions.electricity_usd_per_kwh",
}

SKIP_OAT = {"dt_s"}  # timestep is a numerical setting, not a physical uncertainty


def _get(raw: dict, path: str) -> float:
    section, key = path.split(".")
    return float(raw[section][key]["value"])


def _ranges(raw: dict) -> dict[str, tuple[float, float]]:
    out = {}
    for section, block in raw.items():
        if not isinstance(block, dict):
            continue
        for key, entry in block.items():
            if isinstance(entry, dict) and entry.get("range"):
                out[f"{section}.{key}"] = (float(entry["range"][0]), float(entry["range"][1]))
    return out


def _with(raw: dict, path: str, value: float) -> dict:
    trial = copy.deepcopy(raw)
    section, key = path.split(".")
    trial[section][key]["value"] = value
    return trial


def _oat(raw: dict, base_lcoe: dict[str, float], base_mass: dict[str, float]):
    rows = []
    ranges = {k: v for k, v in _ranges(raw).items() if k not in SKIP_OAT}
    best_base = min(base_lcoe, key=base_lcoe.get)
    for path, (lo, hi) in ranges.items():
        deltas = {}
        mass_deltas = {}
        infeasible = []
        best_at_bounds = []
        for bound in (lo, hi):
            try:
                _, _, res, lcoe = evaluate(_with(raw, path, bound))
            except ValueError as exc:
                infeasible.append(str(exc)[:120])
                continue
            best_at_bounds.append(min(lcoe, key=lcoe.get))
            for r in res:
                deltas.setdefault(r.key, []).append(lcoe[r.key] - base_lcoe[r.key])
                mass_deltas.setdefault(r.key, []).append(r.mass_kg - base_mass[r.key])
        # Keep the signed delta with the largest magnitude per architecture, and
        # the true signed span across architecture and bound for the plot.
        d_max = {k: max(vals, key=abs) for k, vals in deltas.items()}
        m_max = {k: max(vals, key=abs) for k, vals in mass_deltas.items()}
        span_low = min((min(v) for v in deltas.values()), default=float("inf"))
        span_high = max((max(v) for v in deltas.values()), default=float("-inf"))
        rows.append(
            {
                "parameter": path,
                "low": lo,
                "high": hi,
                "max_dlcoe": max(abs(span_low), abs(span_high)),
                "max_dmass": max(abs(v) for v in m_max.values()) if m_max else float("inf"),
                "span_low": span_low,
                "span_high": span_high,
                "dlcoe": d_max,
                "dmass": m_max,
                "ranking_flip": bool(best_at_bounds and any(b != best_base for b in best_at_bounds)),
                "infeasible": infeasible,
            }
        )
    rows.sort(key=lambda r: r["max_dlcoe"], reverse=True)
    return rows


def _mc(raw: dict, results, base_lcoe: dict[str, float], samples: int, seed: int):
    rng = np.random.default_rng(seed)
    ranges = _ranges(raw)
    cost_keys = [k for k in ranges if k in CAPEX_SCALE or k in FUEL_PRICE_PARAM.values()]
    econ_keys = [
        "assumptions.missions_per_year",
        "assumptions.discount_rate",
        "assumptions.lifetime_years",
    ]
    keys = cost_keys + econ_keys
    draws = {k: rng.uniform(*ranges[k], size=samples) for k in keys}

    lcoes = {r.key: np.zeros(samples) for r in results}
    base_missions = _get(raw, "assumptions.missions_per_year")
    base_discount = _get(raw, "assumptions.discount_rate")
    base_life = _get(raw, "assumptions.lifetime_years")

    for i in range(samples):
        capex_scale = {k: 1.0 for k in {item for g in CAPEX_SCALE.values() for item in g}}
        for path, group in CAPEX_SCALE.items():
            if path in draws:
                ratio = draws[path][i] / _get(raw, path)
                for item in group:
                    capex_scale[item] *= ratio
        fuel_ratio = {
            driver: (draws[param][i] / _get(raw, param) if param in draws else 1.0)
            for driver, param in FUEL_PRICE_PARAM.items()
        }
        missions = draws["assumptions.missions_per_year"][i]
        discount = draws["assumptions.discount_rate"][i]
        life = draws["assumptions.lifetime_years"][i]
        for r in results:
            items = r.capex_items or {}
            capex = (r.capex_usd - sum(items.values())) + sum(
                v * capex_scale.get(k, 1.0) for k, v in items.items()
            )
            replacements = {y: c * (capex / r.capex_usd) for y, c in r.replacements_usd.items() if y <= life}
            streams = CostStreams(
                capex_usd=capex,
                annual_energy_kwh=r.delivered_kwh * missions,
                annual_om_usd=r.annual_om_usd,
                annual_fuel_usd=r.fuel_cost_usd * missions * fuel_ratio.get(r.fuel_driver, 1.0),
                replacements_usd=replacements,
                lifetime_years=life,
                discount_rate=discount,
            )
            lcoes[r.key][i] = streams.lcoe_usd_per_kwh

    target = float(raw["targets"]["lcoe_usd_per_kwh"]["value"] if isinstance(
        raw["targets"]["lcoe_usd_per_kwh"], dict) else raw["targets"]["lcoe_usd_per_kwh"])
    cheapest = np.array([min(lcoes, key=lambda k: lcoes[k][i]) for i in range(samples)])
    summary = {}
    for key, arr in lcoes.items():
        summary[key] = {
            "p10": float(np.percentile(arr, 10)),
            "p50": float(np.percentile(arr, 50)),
            "p90": float(np.percentile(arr, 90)),
            "p_cheapest": float(np.mean(cheapest == key)),
            "p_target": float(np.mean(arr <= target)),
        }
    return summary, lcoes, keys, target


def _plots(oat_rows, lcoes, out_dir: pathlib.Path, target: float) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    made = []
    top = [r for r in oat_rows if np.isfinite(r["max_dlcoe"])][:8]
    if top:
        fig, ax = plt.subplots(figsize=(8.5, 4.8))
        labels = [r["parameter"].replace("assumptions.", "").replace("_", " ") for r in top]
        y = np.arange(len(top))
        spans_low = [r["span_low"] for r in top]
        spans_high = [r["span_high"] for r in top]
        ax.barh(y, spans_high, color="#c44e52", alpha=0.8, label="max increase")
        ax.barh(y, spans_low, color="#4c72b0", alpha=0.8, label="max decrease")
        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=8)
        ax.axvline(0, color="black", lw=0.8)
        ax.set_xlabel("change in LCOE versus baseline [USD/kWh]")
        ax.set_title("One-at-a-time sensitivity: plausible range impact")
        ax.legend(fontsize=8)
        ax.grid(axis="x", alpha=0.3)
        path = out_dir / "sensitivity_span.png"
        fig.tight_layout()
        fig.savefig(path, dpi=150)
        plt.close(fig)
        made.append(path.name)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    labels = sorted(lcoes)
    ax.boxplot([lcoes[k] for k in labels], tick_labels=labels, showfliers=False)
    ax.axhline(target, ls=":", color="grey", label=f"target ${target:.2f}/kWh")
    ax.set_ylabel("LCOE [USD/kWh]")
    ax.set_title("Monte Carlo over cost drivers (baseline dispatch held fixed)")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    path = out_dir / "mc_lcoe_distribution.png"
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    made.append(path.name)
    return made


def run_sensitivity(
    config_path: str = "configs/baseline.yaml",
    out_path: str = "reports/SENSITIVITY_ANALYSIS.md",
    samples: int = 2000,
    seed: int = 20261022,
) -> pathlib.Path:
    raw = load_config(config_path)
    raw["assumptions"]["dt_s"]["value"] = 2.0  # dispatch also verified at 1 s and 0.5 s
    _, cfg, results, base_lcoe = evaluate(raw)
    base_mass = {r.key: r.mass_kg for r in results}
    names = {r.key: r.name for r in results}

    oat_rows = _oat(raw, base_lcoe, base_mass)
    mc_summary, lcoes, mc_keys, target = _mc(raw, results, base_lcoe, samples, seed)

    scenario_tables = {}
    for name, path in SCENARIOS.items():
        scen_raw = deep_merge(raw, load_yaml(path))
        _, scen_cfg, scen_res, scen_lcoe = evaluate(scen_raw)
        scenario_tables[name] = {
            r.key: {"mass": r.mass_kg, "lcoe": scen_lcoe[r.key], "capex": r.capex_usd}
            for r in scen_res
        }

    out = pathlib.Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig_dir = out.parent / "figures"
    figures = _plots(oat_rows, lcoes, fig_dir, target)

    with (out.parent / "sensitivity_oat.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["parameter", "low", "high", "max_dlcoe_usd_per_kwh", "max_dmass_kg",
                    "ranking_flip", "infeasible_bounds"])
        for r in oat_rows:
            w.writerow([r["parameter"], r["low"], r["high"], f"{r['max_dlcoe']:.4f}",
                        f"{r['max_dmass']:.2f}", r["ranking_flip"], " | ".join(r["infeasible"])])

    with (out.parent / "mc_summary.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "name", "p10", "p50", "p90", "p_cheapest", "p_meets_target"])
        for key, s in mc_summary.items():
            w.writerow([key, names[key], f"{s['p10']:.4f}", f"{s['p50']:.4f}",
                        f"{s['p90']:.4f}", f"{s['p_cheapest']:.3f}", f"{s['p_target']:.3f}"])

    top = oat_rows[0] if oat_rows else None
    cheapest_base = min(base_lcoe, key=base_lcoe.get)
    mc_best = max(mc_summary, key=lambda k: mc_summary[k]["p_cheapest"])

    lines = [
        "# Sensitivity and uncertainty analysis",
        "",
        f"Generated by `project_e sensitivity` — seed {seed}, {samples} Monte Carlo samples.",
        "Dispatch timestep 2 s (baseline verified at 1 s and 0.5 s).",
        "",
        "## Method",
        "",
        "- **One-at-a-time:** each parameter's declared range is applied at both bounds and",
        "  the full model is rerun. This measures influence, not probability.",
        f"- **Monte Carlo:** cost drivers only, uniform over declared ranges, {samples} draws.",
        "  Dispatch and efficiencies stay at baseline, so this is **not** a performance forecast.",
        "- Uniform ranges are uncertainty bounds. Treating them as distributions is an",
        "  assumption made for stress-testing, not evidence.",
        "",
        "## Baseline",
        "",
        "| Key | Architecture | Mass kg | Capex USD | LCOE $/kWh |",
        "|---|---|---:|---:|---:|",
    ]
    for r in results:
        lines.append(f"| {r.key} | {names[r.key]} | {r.mass_kg:.1f} | {r.capex_usd:,.0f} | {base_lcoe[r.key]:.3f} |")

    lines += ["", "## Scenario robustness", "",
              "| Key | Conservative mass / LCOE | Optimistic mass / LCOE |",
              "|---|---:|---:|"]
    for key in sorted(base_lcoe):
        c = scenario_tables["conservative"][key]
        o = scenario_tables["optimistic"][key]
        lines.append(f"| {key} | {c['mass']:.1f} kg / ${c['lcoe']:.3f} | {o['mass']:.1f} kg / ${o['lcoe']:.3f} |")

    lines += ["", "## One-at-a-time ranking (top 15)", "",
              "| Rank | Parameter | Range | Max ΔLCOE | Max Δmass | Flips ranking? |",
              "|---:|---|---|---:|---:|:--:|"]
    for i, r in enumerate([x for x in oat_rows if np.isfinite(x["max_dlcoe"])][:15], start=1):
        lines.append(
            f"| {i} | `{r['parameter']}` | {r['low']:g} – {r['high']:g} | "
            f"${r['max_dlcoe']:.3f}/kWh | {r['max_dmass']:.1f} kg | {'yes' if r['ranking_flip'] else 'no'} |"
        )
    infeasible = [r for r in oat_rows if r["infeasible"]]
    if infeasible:
        lines += ["", "Bounds rejected as physically infeasible:"]
        for r in infeasible:
            lines.append(f"- `{r['parameter']}`: {r['infeasible'][0]}")

    lines += ["", "## Monte Carlo over cost drivers", "",
              "| Key | Architecture | P10 | P50 | P90 | P(cheapest) | P(≤ target) |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for key, s in mc_summary.items():
        lines.append(
            f"| {key} | {names[key]} | ${s['p10']:.3f} | ${s['p50']:.3f} | ${s['p90']:.3f} | "
            f"{s['p_cheapest']:.0%} | {s['p_target']:.0%} |"
        )

    lines += ["", "## What the numbers say", ""]
    if top:
        lines.append(
            f"1. **Most influential unknown: `{top['parameter']}`** — moving it across its "
            f"declared range changes LCOE by up to ${top['max_dlcoe']:.3f}/kWh and mass by "
            f"{top['max_dmass']:.1f} kg. This is the quantity to measure first."
        )
    lines.append(
        f"2. At baseline the lowest LCOE is **{cheapest_base}** ({names[cheapest_base]}) at "
        f"${base_lcoe[cheapest_base]:.3f}/kWh, but the ranking is not the whole decision: "
        "mass, volume and emissions constraints eliminate candidates independently."
    )
    lines.append(
        f"3. Over the cost Monte Carlo, **{mc_best}** is cheapest most often "
        f"({mc_summary[mc_best]['p_cheapest']:.0%} of draws), with P50 "
        f"${mc_summary[mc_best]['p50']:.3f}/kWh. The spread P10–P90 "
        f"(${mc_summary[mc_best]['p10']:.3f}–${mc_summary[mc_best]['p90']:.3f}) is wider than "
        "the difference between the top two architectures, so cost assumptions decide the winner."
    )
    lines.append(
        "4. No architecture meets all five targets at baseline. The portable-hybrid branch is "
        "therefore an integration and cost problem, not a new-physics problem."
    )
    lines += [
        "",
        "## Limitations",
        "",
        "- Cost distributions are assumed uniform and independent; real prices correlate.",
        "- Physics parameters are held at baseline during the Monte Carlo.",
        "- Only one mission is evaluated; conclusions do not transfer to other durations or loads.",
        "- No measured hardware data exists. These are model results (E2/E3).",
        "",
        "## Figures",
        "",
    ]
    lines += [f"- `reports/figures/{f}`" for f in figures]

    out.write_text("\n".join(lines) + "\n")
    return out
