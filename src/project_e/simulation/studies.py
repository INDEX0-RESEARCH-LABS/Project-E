"""Deterministic design studies.

Two questions the architecture comparison cannot answer on its own:

  1. Sizing: is the fixed 1.3x source / 0.5 kWh buffer actually the best point for
     the hybrid, or does a different split of source and buffer meet the targets?
  2. Requirement feasibility: how do mass and cost move with mission duration and
     peak load, and what mission is actually achievable at 35 kg?

Both are grid/bisection studies on the same model. They are deterministic: no
sampling, no optimisation heuristics. A point is "feasible" only if dispatch
serves the whole load (unmet <= 1e-6 kWh).
"""

from __future__ import annotations

import copy
import csv
import pathlib

from ..config import load_config, resolve
from .architectures import (
    battery_only,
    diesel_direct,
    diesel_hybrid,
    fuel_cell_hybrid,
    screen_architecture,
)
from .dispatch import Mission
from .runner import lcoe_for

ARCH = {
    "A1": battery_only,
    "B1": diesel_direct,
    "C1": fuel_cell_hybrid,
    "C2": diesel_hybrid,
}

SOURCE_SECTION = {"C1": "fuel_cell", "C2": "diesel"}


def _make(key: str, mission: Mission, cfg: dict):
    r = ARCH[key](mission, cfg)
    return screen_architecture(r, mission, cfg)


def _row(key: str, mission: Mission, cfg: dict) -> dict:
    r = _make(key, mission, cfg)
    lcoe, _ = lcoe_for(r, cfg)
    t = cfg["targets"]
    return {
        "key": key,
        "energy_kwh": round(mission.energy_kwh, 4),
        "mass_kg": r.mass_kg,
        "volume_l": r.volume_l,
        "capex_usd": r.capex_usd,
        "lcoe": lcoe,
        "efficiency": r.efficiency,
        "met": sum(
            [
                r.mass_kg <= t["mass_kg"],
                r.volume_l <= t["volume_l"],
                r.capex_usd <= t["capex_usd"],
                lcoe <= t["lcoe_usd_per_kwh"],
                r.unmet_kwh <= 1e-6,
            ]
        ),
    }


def sizing_grid(raw: dict, key: str = "C2", limit: int = 60) -> list[dict]:
    """Grid over source sizing factor and buffer energy. Infeasible points kept."""
    section = SOURCE_SECTION[key]
    factors = [0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]
    buffers = [0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
    rows = []
    for factor in factors:
        for buffer in buffers:
            trial = copy.deepcopy(raw)
            trial[section]["source_sizing_factor"]["value"] = factor
            trial[section]["buffer_kwh"]["value"] = buffer
            cfg = resolve(trial)
            mission = Mission(**cfg["mission"])
            try:
                r = _make(key, mission, cfg)
                if r.unmet_kwh > 1e-6:
                    raise ValueError(f"unmet {r.unmet_kwh:.4f} kWh")
            except ValueError as exc:
                rows.append({
                    "key": key, "factor": factor, "buffer_kwh": buffer,
                    "feasible": False, "reason": str(exc)[:80],
                    "mass_kg": None, "lcoe": None, "capex_usd": None,
                    "volume_l": None, "met": 0,
                })
                continue
            lcoe, _ = lcoe_for(r, cfg)
            t = cfg["targets"]
            rows.append({
                "key": key, "factor": factor, "buffer_kwh": buffer,
                "feasible": True, "reason": "",
                "mass_kg": r.mass_kg, "lcoe": lcoe, "capex_usd": r.capex_usd,
                "volume_l": r.volume_l,
                "met": sum([
                    r.mass_kg <= t["mass_kg"], r.volume_l <= t["volume_l"],
                    r.capex_usd <= t["capex_usd"], lcoe <= t["lcoe_usd_per_kwh"],
                    r.unmet_kwh <= 1e-6,
                ]),
            })
    return rows


def pareto(rows: list[dict]) -> list[dict]:
    """Non-dominated points on (mass, LCOE); lower is better on both."""
    pts = sorted((r for r in rows if r["feasible"]), key=lambda r: (r["mass_kg"], r["lcoe"]))
    front = []
    best = float("inf")
    for r in pts:
        if r["lcoe"] < best - 1e-12:
            front.append(r)
            best = r["lcoe"]
    return front


def max_value_at(key: str, raw: dict, metric: str, limit: float) -> float | None:
    """Bisection on mission duration until ``mass_kg`` reaches ``limit``.

    Only mass is monotone in duration. LCOE is not: capex is spread over more
    delivered energy, so A1's LCOE *falls* from 0.5 h to 8 h. Restrict the helper
    to mass rather than silently returning a wrong inverse for cost.

    Returns None if even the shortest mission exceeds the limit; returns the
    upper bound (24 h) when the limit is still met there.
    """
    if metric != "mass_kg":
        raise ValueError("max_value_at is only valid for monotone mass_kg, not " + metric)

    def value(duration: float) -> float:
        cfg = resolve(raw)
        cfg["mission"]["duration_h"] = duration
        mission = Mission(**cfg["mission"])
        row = _row(key, mission, cfg)
        return row[metric]

    lo, hi = 0.5, 24.0
    if value(lo) > limit:
        return None
    if value(hi) <= limit:
        return hi
    for _ in range(30):
        mid = (lo + hi) / 2.0
        if value(mid) <= limit:
            lo = mid
        else:
            hi = mid
    return int(lo * 100) / 100.0  # floor: never report a duration that fails


def mission_table(raw: dict, durations: list[float], keys: list[str]) -> list[dict]:
    rows = []
    for duration in durations:
        cfg = resolve(raw)
        cfg["mission"]["duration_h"] = duration
        mission = Mission(**cfg["mission"])
        for key in keys:
            row = _row(key, mission, cfg)
            row["duration_h"] = duration
            rows.append(row)
    return rows


def peak_table(raw: dict, peaks: list[float], keys: list[str]) -> list[dict]:
    rows = []
    for peak in peaks:
        cfg = resolve(raw)
        cfg["mission"]["peak_load_kw"] = peak
        mission = Mission(**cfg["mission"])
        for key in keys:
            row = _row(key, mission, cfg)
            row["peak_kw"] = peak
            rows.append(row)
    return rows


def _write_csv(path: pathlib.Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.4f}" if isinstance(v, float) else v) for k, v in r.items()})


def run_sizing_study(config_path: str = "configs/baseline.yaml",
                     out_md: str = "reports/SIZING_STUDY.md") -> pathlib.Path:
    raw = load_config(config_path)
    all_rows = []
    for key in ("C2", "C1"):
        all_rows.extend(sizing_grid(raw, key))
    _write_csv(pathlib.Path("reports/sizing_grid.csv"), all_rows,
               ["key", "factor", "buffer_kwh", "feasible", "reason", "mass_kg",
                "lcoe", "capex_usd", "volume_l", "met"])

    lines = [
        "# Sizing study — hybrid source and buffer",
        "",
        "Grid: source sizing factor 0.9–1.5 × average load, buffer 0.3–1.0 kWh.",
        "A point is feasible only if dispatch serves the whole mission (unmet ≤ 1e-6 kWh)",
        "and the source can sustain the DC load plus the buffer's round-trip loss over",
        "repeated missions. A source at exactly average load fails the second test.",
        "C1 is the fuel-cell hybrid; C2 the diesel hybrid. All other parameters at baseline.",
        "",
    ]
    for key in ("C2", "C1"):
        rows = [r for r in all_rows if r["key"] == key]
        feasible = [r for r in rows if r["feasible"]]
        front = pareto(rows)
        lines += [
            f"## {key}",
            "",
            f"- feasible points: {len(feasible)} / {len(rows)}",
            f"- infeasible: {len(rows) - len(feasible)} (source below sustainable load, "
            "unmet pulse, or rejected configuration; per-point reason in the CSV)",
        ]
        if feasible:
            best_mass = min(feasible, key=lambda r: r["mass_kg"])
            best_lcoe = min(feasible, key=lambda r: r["lcoe"])
            lines += [
                f"- lightest feasible: {best_mass['mass_kg']:.1f} kg at "
                f"{best_mass['factor']:.1f}× source, {best_mass['buffer_kwh']:.1f} kWh buffer, "
                f"${best_mass['lcoe']:.3f}/kWh, {best_mass['met']}/5 targets",
                f"- cheapest feasible: ${best_lcoe['lcoe']:.3f}/kWh at "
                f"{best_lcoe['factor']:.1f}× source, {best_lcoe['buffer_kwh']:.1f} kWh buffer, "
                f"{best_lcoe['mass_kg']:.1f} kg, {best_lcoe['met']}/5 targets",
                "",
                "### Pareto front (mass vs LCOE)",
                "",
                "| Source × | Buffer kWh | Mass kg | LCOE $/kWh | Capex USD | Targets |",
                "|---:|---:|---:|---:|---:|---:|",
            ]
            for r in front:
                lines.append(
                    f"| {r['factor']:.1f} | {r['buffer_kwh']:.1f} | {r['mass_kg']:.1f} | "
                    f"{r['lcoe']:.3f} | {r['capex_usd']:,.0f} | {r['met']}/5 |"
                )
            met_best = max(feasible, key=lambda r: r["met"])
            lines += [
                "",
                f"Best target score over the grid: **{met_best['met']}/5** at "
                f"{met_best['factor']:.1f}× source and {met_best['buffer_kwh']:.1f} kWh buffer.",
                "",
            ]
            if best_mass["mass_kg"] > 35.0:
                lines.append(
                    f"Even the lightest feasible point is {best_mass['mass_kg'] - 35.0:.1f} kg "
                    "above the mass target. Re-sizing the hybrid cannot close that gap."
                )
            else:
                lines.append("A feasible point meets the mass target; check the other targets.")
            lines.append("")

    out = pathlib.Path(out_md)
    out.write_text("\n".join(lines) + "\n")
    return out


def run_mission_study(config_path: str = "configs/baseline.yaml",
                      out_md: str = "reports/MISSION_SCALING.md") -> pathlib.Path:
    raw = load_config(config_path)
    durations = [2.0, 4.0, 6.0, 8.0, 10.0, 12.0]
    keys = ["A1", "B1", "C2"]
    rows = mission_table(raw, durations, keys)
    _write_csv(pathlib.Path("reports/mission_scaling.csv"), rows,
               ["duration_h", "key", "energy_kwh", "mass_kg", "volume_l", "capex_usd",
                "lcoe", "efficiency", "met"])

    peaks = [2.0, 3.0, 4.0, 6.0, 8.0]
    prows = peak_table(raw, peaks, ["A1", "C2"])
    _write_csv(pathlib.Path("reports/peak_load.csv"), prows,
               ["peak_kw", "key", "energy_kwh", "mass_kg", "volume_l", "capex_usd",
                "lcoe", "efficiency", "met"])

    lines = [
        "# Mission scaling — what the 35 kg target actually allows",
        "",
        "All points use the baseline parameters; only duration or peak load changes.",
        "Missions per year is held at 250, so a shorter mission delivers less annual",
        "energy and its LCOE rises. That is deliberate: it compares cost per delivered",
        "kWh at fixed utilisation, not at fixed operating hours.",
        "",
        "## Mass and cost versus duration (1 kW base, 6 kW peak)",
        "",
        "| Duration h | Energy kWh | A1 mass kg | A1 $/kWh | C2 mass kg | C2 $/kWh | B1 mass kg | B1 $/kWh |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for duration in durations:
        d = {r["key"]: r for r in rows if r["duration_h"] == duration}
        lines.append(
            f"| {duration:.0f} | {d['A1']['energy_kwh']:.1f} | {d['A1']['mass_kg']:.1f} | "
            f"{d['A1']['lcoe']:.3f} | {d['C2']['mass_kg']:.1f} | {d['C2']['lcoe']:.3f} | "
            f"{d['B1']['mass_kg']:.1f} | {d['B1']['lcoe']:.3f} |"
        )

    lines += ["", "## Maximum mission length at the mass target (35 kg)", ""]
    a = resolve(raw)["assumptions"]
    peak = resolve(raw)["mission"]["peak_load_kw"]
    cell_power_kg = peak / a["converter_efficiency"] * 1000.0 / resolve(raw)["battery"]["specific_power_w_kg"]
    converter_kg = peak * a["power_electronics_kg_per_kw"] * a["packaging_factor"]
    causes = {
        "A1": "the 6 kW pulse (power-rated cells plus converter)",
        "B1": "the 6 kW genset",
        "C2": "the 6 kW converter plus the minimum genset, buffer and radiator",
    }
    for key in keys:
        dur = max_value_at(key, raw, "mass_kg", 35.0)
        if dur is None:
            short = _row(key, Mission(0.5, 1.0, peak, 30.0, 600.0), resolve(raw))
            lines.append(
                f"- **{key}**: {short['mass_kg']:.1f} kg at 0.5 h — {short['mass_kg'] - 35.0:.1f} kg "
                f"above target before useful mission energy is added. The floor is set by "
                f"{causes[key]}, not the 8 h duration."
            )
        else:
            cfg = resolve(raw)
            cfg["mission"]["duration_h"] = dur
            energy = Mission(**cfg["mission"]).energy_kwh
            lines.append(
                f"- **{key}**: {dur:.2f} h ({energy:.1f} kWh delivered) at 35 kg. "
                f"The 8 h mission is {8.0 / dur:.1f}× too long for this mass."
            )
    lines += [
        "",
        "For A1 the battery at 0.5 h is power-limited, not energy-limited: 6 kW ÷ "
        f"{resolve(raw)['battery']['specific_power_w_kg']:.0f} W/kg = "
        f"{cell_power_kg:.1f} kg of cells before packaging, plus {converter_kg:.1f} kg "
        "of converter. That is the floor the requirement set has to live with.",
    ]

    lines += ["", "## Peak load sweep (8 h, 1 kW base)", "",
              "| Peak kW | Energy kWh | A1 mass kg | A1 $/kWh | C2 mass kg | C2 $/kWh |",
              "|---:|---:|---:|---:|---:|---:|"]
    for peak in peaks:
        d = {r["key"]: r for r in prows if r["peak_kw"] == peak}
        lines.append(
            f"| {peak:.0f} | {d['A1']['energy_kwh']:.1f} | {d['A1']['mass_kg']:.1f} | "
            f"{d['A1']['lcoe']:.3f} | {d['C2']['mass_kg']:.1f} | {d['C2']['lcoe']:.3f} |"
        )

    lines += [
        "",
        "## Interpretation",
        "",
        "- The 35 kg, 6 kW, 8 h mission is not a design point any candidate reaches;",
        "  it is a requirement set that is internally inconsistent for a battery and",
        "  for a hydrocarbon hybrid.",
        "- The peak-load sweep isolates the cost of the 6 kW pulse: converter and",
        "  radiator scale with peak, while energy scales with duration.",
        "- Reducing peak (staggered motor starts) or splitting the pack into modules",
        "  are requirement-level changes, not hardware improvements.",
        "",
        "These are model results. They do not replace the bench test.",
    ]

    out = pathlib.Path(out_md)
    out.write_text("\n".join(lines) + "\n")
    return out
