"""Build a verified source registry.

Each entry names an EXPECTED title. The script queries Crossref by title, requires a
close match, and records the DOI actually returned. Unmatched entries fail loudly;
nothing is invented or hand-typed into the registry.

Usage: .venv/bin/python research/build_registry.py
"""
from __future__ import annotations

import csv
import difflib
import json
import pathlib
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
RAW = HERE / "raw"
RAW.mkdir(exist_ok=True)
UA = "ProjectE-research/0.1 (mailto:research@example.invalid)"

# (registry_id, expected_title, evidence_class, relevance_to_project_e)
TARGETS = [
    ("S01", "Thermophotovoltaic efficiency of 40%", "experimental",
     "Upper-bound anchor for TPV conversion; defines the emitter-temperature regime."),
    ("S02", "Complex thermoelectric materials", "review",
     "ZT physics and practical TEG efficiency ceiling."),
    ("S03", "Materials for electrochemical capacitors", "review",
     "Supercapacitor energy/power density split versus batteries."),
    ("S04", "Li-ion battery materials: present and future", "review",
     "Incumbent storage energy density and materials limits."),
    ("S05", "Detailed Balance Limit of Efficiency of p-n Junction Solar Cells", "analytical",
     "Thermodynamic ceiling for any single-junction photovoltaic conversion."),
    ("S06", "Electrical Energy Storage for the Grid: A Battery of Choices", "review",
     "Technology comparison and round-trip efficiency context."),
    ("S07", "Thermoelectric generators: A review of applications", "review",
     "Real TEG system efficiencies in waste-heat service."),
    ("S08", "Pumped thermal electricity storage: A technology overview", "review",
     "Thermal-mechanical storage round-trip efficiency and cost drivers."),
    ("S09", "Review on thermal energy storage with phase change materials and applications", "review",
     "Latent-heat storage density and heat-transfer limits."),
    ("S10", "Overview of current development in electrical energy storage technologies and the application potential in power system operation", "review",
     "Cross-technology efficiency/lifetime/cost comparison."),
    ("S11", "Hydrogen and fuel cells: Towards a sustainable energy future", "review",
     "Fuel-cell efficiency chain and hydrogen round-trip penalties."),
    ("S12", "A review of organic Rankine cycles (ORCs) for the recovery of low-grade waste heat", "review",
     "Small/medium heat-engine efficiency in the 100-400 C range."),
]


# Prefer the primary journal record where a title search returns a reprint/book chapter.
# Each override is still verified against the expected title by DOI lookup.
DOI_OVERRIDES = {
    "S02": "10.1038/nmat2090",
    "S03": "10.1038/nmat2297",
    "S05": "10.1063/1.1736034",
}


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def norm(s: str) -> str:
    return " ".join("".join(c.lower() if c.isalnum() else " " for c in s).split())


def main() -> None:
    rows = []
    failures = []
    for rid, expected, evidence, relevance in TARGETS:
        url = (
            "https://api.crossref.org/works?"
            + urllib.parse.urlencode(
                {
                    "query.title": expected,
                    "rows": 5,
                    "select": "DOI,title,author,issued,container-title,type,is-referenced-by-count,publisher",
                    "mailto": "research@example.invalid",
                }
            )
        )
        try:
            if rid in DOI_OVERRIDES:
                best = get(
                    "https://api.crossref.org/works/"
                    + urllib.parse.quote(DOI_OVERRIDES[rid], safe="")
                )["message"]
                title = (best.get("title") or [""])[0]
                best_score = difflib.SequenceMatcher(
                    None, norm(title), norm(expected)
                ).ratio()
                if best_score < 0.86:
                    failures.append((rid, f"override DOI title mismatch {best_score:.2f}"))
                    continue
                items = [best]
            else:
                data = get(url)
                items = data["message"]["items"]
        except Exception as exc:
            failures.append((rid, f"network: {exc}"))
            continue
        best, best_score = None, 0.0
        for it in items:
            title = (it.get("title") or [""])[0]
            score = difflib.SequenceMatcher(None, norm(title), norm(expected)).ratio()
            if score > best_score:
                best, best_score = it, score
        if best is None or best_score < 0.86:
            failures.append((rid, f"no match >=0.86 (best {best_score:.2f})"))
            print(f"{rid} FAIL {best_score:.2f} {expected}")
            continue
        (RAW / f"crossref_{rid}.json").write_text(json.dumps(best, indent=1))
        authors = "; ".join(
            f"{a.get('family','')}, {a.get('given','')}".strip(", ")
            for a in best.get("author", [])[:6]
        )
        year = ((best.get("issued", {}).get("date-parts") or [[None]])[0] or [None])[0]
        rows.append(
            {
                "id": rid,
                "title": (best.get("title") or [""])[0],
                "authors": authors,
                "year": year,
                "doi": best["DOI"],
                "venue": (best.get("container-title") or [""])[0],
                "publisher": best.get("publisher", ""),
                "crossref_type": best.get("type", ""),
                "crossref_citations": best.get("is-referenced-by-count", ""),
                "match_score": f"{best_score:.3f}",
                "evidence_class": evidence,
                "relevance": relevance,
            }
        )
        print(f"{rid} OK {best_score:.2f} {best['DOI']} | {(best.get('title') or [''])[0][:70]}")
        time.sleep(0.4)

    if failures:
        print("\nFAILURES (must be resolved, not papered over):")
        for f in failures:
            print("  ", f)

    out = HERE / "source_registry.csv"
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (RAW / "registry_failures.json").write_text(json.dumps(failures, indent=1))
    print(f"\nwrote {out} with {len(rows)} verified rows, {len(failures)} failures")


if __name__ == "__main__":
    main()
