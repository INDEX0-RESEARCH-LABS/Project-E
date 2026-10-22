"""Configuration loading, merging, validation, and provenance extraction."""

from __future__ import annotations

import copy
import hashlib
import json
import pathlib
from typing import Any

import yaml

REQUIRED_TOP = {"meta", "mission", "targets", "assumptions", "battery", "diesel", "teg", "tpv", "fuel_cell"}


def load_yaml(path: str | pathlib.Path) -> dict[str, Any]:
    with open(path) as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return data


def deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def load_config(path: str | pathlib.Path, scenario: str | pathlib.Path | None = None) -> dict:
    cfg = load_yaml(path)
    if scenario:
        cfg = deep_merge(cfg, load_yaml(scenario))
    missing = REQUIRED_TOP - set(cfg)
    if missing:
        raise ValueError(f"config missing sections: {sorted(missing)}")
    for section in ("battery", "diesel", "teg", "tpv", "fuel_cell", "assumptions"):
        if not isinstance(cfg[section], dict):
            raise ValueError(f"section {section} must be a mapping")
    return cfg


def values(section: dict) -> dict:
    """Flatten {'key': {'value': x, ...}} -> {'key': x}."""
    return {k: (v["value"] if isinstance(v, dict) and "value" in v else v) for k, v in section.items()}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _in_unit_interval(name: str, value: float) -> None:
    _require(isinstance(value, (int, float)) and 0.0 < value <= 1.0,
             f"{name} must be in (0, 1], got {value!r}")


def _positive(name: str, value: float) -> None:
    _require(isinstance(value, (int, float)) and value > 0.0,
             f"{name} must be > 0, got {value!r}")


def _nonnegative(name: str, value: float) -> None:
    _require(isinstance(value, (int, float)) and value >= 0.0,
             f"{name} must be >= 0, got {value!r}")


def _validate(out: dict) -> None:
    """Reject nonsensical parameters at the boundary.

    This is deliberately explicit rather than schema-driven: these are the values
    that turn into divisions or physical claims downstream.
    """
    m, a, b = out["mission"], out["assumptions"], out["battery"]
    _positive("mission.duration_h", m["duration_h"])
    _positive("mission.base_load_kw", m["base_load_kw"])
    _positive("mission.peak_load_kw", m["peak_load_kw"])
    _require(m["peak_load_kw"] >= m["base_load_kw"], "peak_load_kw must be >= base_load_kw")
    _positive("mission.pulse_duration_s", m["pulse_duration_s"])
    _positive("mission.pulse_period_s", m["pulse_period_s"])

    _in_unit_interval("assumptions.converter_efficiency", a["converter_efficiency"])
    _in_unit_interval("assumptions.charger_efficiency", a["charger_efficiency"])
    _positive("assumptions.packaging_factor", a["packaging_factor"])
    _positive("assumptions.missions_per_year", a["missions_per_year"])
    _positive("assumptions.lifetime_years", a["lifetime_years"])
    _positive("assumptions.h_convection_w_m2k", a["h_convection_w_m2k"])
    _nonnegative("assumptions.degradation_margin", a["degradation_margin"])

    _positive("battery.specific_energy_wh_kg", b["specific_energy_wh_kg"])
    _positive("battery.specific_power_w_kg", b["specific_power_w_kg"])
    _positive("battery.energy_density_wh_l", b["energy_density_wh_l"])
    _in_unit_interval("battery.round_trip_efficiency", b["round_trip_efficiency"])
    _require(0.0 <= b["soc_min"] < b["soc_max"] <= 1.0, "battery SOC window must satisfy 0 <= min < max <= 1")
    _positive("battery.cycle_life", b["cycle_life"])
    _nonnegative("battery.cost_usd_per_kwh", b["cost_usd_per_kwh"])
    _nonnegative("battery.power_electronics_usd_per_kw", b["power_electronics_usd_per_kw"])

    d = out["diesel"]
    _in_unit_interval("diesel.efficiency_lhv", d["efficiency_lhv"])
    _in_unit_interval("diesel.part_load_floor", d["part_load_floor"])
    _nonnegative("diesel.cost_usd_per_kw", d["cost_usd_per_kw"])
    _positive("diesel.mass_kg_per_kw", d["mass_kg_per_kw"])
    _nonnegative("diesel.fuel_usd_per_l", d["fuel_usd_per_l"])
    _positive("diesel.fuel_density_kg_per_l", d["fuel_density_kg_per_l"])
    _positive("diesel.source_sizing_factor", d["source_sizing_factor"])
    _positive("diesel.buffer_kwh", d["buffer_kwh"])

    t = out["teg"]
    _nonnegative("teg.zt", t["zt"])
    _require(t["hot_c"] > t["cold_c"], "teg.hot_c must exceed teg.cold_c")
    _in_unit_interval("teg.burner_efficiency", t["burner_efficiency"])
    _nonnegative("teg.cost_usd_per_w", t["cost_usd_per_w"])
    _positive("teg.mass_kg_per_kw", t["mass_kg_per_kw"])

    v = out["tpv"]
    _in_unit_interval("tpv.efficiency", v["efficiency"])
    _in_unit_interval("tpv.spectral_quality", v["spectral_quality"])
    _positive("tpv.storage_specific_kwh_per_kg", v["storage_specific_kwh_per_kg"])
    _nonnegative("tpv.vessel_mass_fraction", v["vessel_mass_fraction"])
    _positive("tpv.storage_density_kg_per_l", v["storage_density_kg_per_l"])
    _positive("tpv.power_density_w_cm2", v["power_density_w_cm2"])
    _require(v["emitter_c"] > v["cold_c"], "tpv.emitter_c must exceed tpv.cold_c")

    f = out["fuel_cell"]
    _in_unit_interval("fuel_cell.efficiency_lhv", f["efficiency_lhv"])
    _nonnegative("fuel_cell.cost_usd_per_kw", f["cost_usd_per_kw"])
    _positive("fuel_cell.mass_kg_per_kw", f["mass_kg_per_kw"])
    _in_unit_interval("fuel_cell.tank_gravimetric_fraction", f["tank_gravimetric_fraction"])
    _nonnegative("fuel_cell.h2_usd_per_kg", f["h2_usd_per_kg"])
    _positive("fuel_cell.source_sizing_factor", f["source_sizing_factor"])
    _positive("fuel_cell.buffer_kwh", f["buffer_kwh"])


def resolve(cfg: dict) -> dict:
    """Resolve every parameter block to plain values, keeping non-parameter sections."""
    out = copy.deepcopy(cfg)
    for section in ("mission", "targets", "assumptions", "battery", "supercap", "diesel", "teg", "tpv", "fuel_cell"):
        if section in out:
            out[section] = values(out[section])
    _validate(out)
    return out


def config_checksum(cfg: dict) -> str:
    blob = json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


def provenance_rows(cfg: dict) -> list[dict]:
    rows = []
    for section, block in cfg.items():
        if not isinstance(block, dict):
            continue
        for key, entry in block.items():
            if isinstance(entry, dict) and "value" in entry:
                rows.append(
                    {
                        "section": section,
                        "parameter": key,
                        "value": entry["value"],
                        "source": entry.get("source", ""),
                        "evidence": entry.get("evidence", ""),
                        "range_low": (entry.get("range") or [None])[0],
                        "range_high": (entry.get("range") or [None, None])[1],
                        "units": entry.get("units", ""),
                    }
                )
    return rows


def write_provenance_csv(cfg: dict, path: str | pathlib.Path) -> None:
    import csv

    rows = provenance_rows(cfg)
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
