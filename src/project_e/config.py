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


def resolve(cfg: dict) -> dict:
    """Resolve every parameter block to plain values, keeping non-parameter sections."""
    out = copy.deepcopy(cfg)
    for section in ("mission", "targets", "assumptions", "battery", "supercap", "diesel", "teg", "tpv", "fuel_cell"):
        if section in out:
            out[section] = values(out[section])
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
