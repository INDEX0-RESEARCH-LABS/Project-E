"""Fetch real bibliographic records for Project E. Raw JSON is preserved; nothing is invented.

Usage: .venv/bin/python research/fetch_literature.py
"""
from __future__ import annotations

import json
import pathlib
import time
import urllib.parse
import urllib.request

RAW = pathlib.Path(__file__).parent / "raw"
RAW.mkdir(exist_ok=True)
UA = "ProjectE-research/0.1 (mailto:research@example.invalid)"

QUERIES = {
    "tpv_efficiency": "thermophotovoltaic efficiency emitter",
    "teg_zt": "thermoelectric generator efficiency figure of merit ZT",
    "liion_degradation": "lithium-ion battery cycle life degradation model",
    "sofc_efficiency": "solid oxide fuel cell system electrical efficiency",
    "pumped_thermal": "pumped thermal energy storage round-trip efficiency",
    "pcm_storage": "phase change material latent heat thermal energy storage",
    "supercapacitor": "electrochemical capacitor energy density power density",
    "lcoe_storage": "levelized cost of electricity battery energy storage",
    "csp_tpv": "concentrated solar thermophotovoltaic system",
    "si_anode": "silicon anode lithium-ion battery energy density",
    "thermoelectric_harvesting": "thermoelectric waste heat recovery internal combustion engine",
    "heat_engine_small": "small scale organic Rankine cycle efficiency",
}


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def main() -> None:
    summary = {}
    for key, q in QUERIES.items():
        url = (
            "https://api.crossref.org/works?"
            + urllib.parse.urlencode(
                {
                    "query.bibliographic": q,
                    "rows": 6,
                    "select": "DOI,title,author,issued,container-title,type,is-referenced-by-count,abstract",
                    "mailto": "research@example.invalid",
                }
            )
        )
        try:
            data = get(url)
        except Exception as exc:  # network failure must be visible, not hidden
            summary[key] = f"FAILED: {exc}"
            print(f"{key}: FAILED {exc}")
            continue
        (RAW / f"crossref_{key}.json").write_text(json.dumps(data, indent=1))
        items = data["message"]["items"]
        summary[key] = len(items)
        print(f"{key}: {len(items)} records")
        time.sleep(0.4)

    # Pull abstracts for the top hit of each query from OpenAlex (Crossref abstracts are sparse).
    for key in QUERIES:
        path = RAW / f"crossref_{key}.json"
        if not path.exists():
            continue
        item = json.loads(path.read_text())["message"]["items"][0]
        doi = item["DOI"]
        try:
            data = get(f"https://api.openalex.org/works/https://doi.org/{doi}")
        except Exception as exc:
            print(f"{key}: openalex FAILED {exc}")
            continue
        (RAW / f"openalex_{key}.json").write_text(json.dumps(data, indent=1))
        time.sleep(0.3)

    (RAW / "fetch_summary.json").write_text(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
