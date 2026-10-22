"""Fetch abstracts for registered sources (OpenAlex, public API) and store raw JSON.

Rebuilds abstract text from OpenAlex's inverted index. Missing abstract is recorded
as "not available" -- never filled in from memory.

Usage: .venv/bin/python research/fetch_abstracts.py
"""
from __future__ import annotations

import csv
import json
import pathlib
import time
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
RAW = HERE / "raw"
UA = "ProjectE-research/0.1 (mailto:research@example.invalid)"


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.load(r)


def abstract_text(inv: dict | None) -> str:
    if not inv:
        return ""
    slots: list[tuple[int, str]] = []
    for word, positions in inv.items():
        for p in positions:
            slots.append((p, word))
    return " ".join(w for _, w in sorted(slots))


def main() -> None:
    rows = list(csv.DictReader((HERE / "source_registry.csv").open()))
    out = []
    for row in rows:
        doi = row["doi"]
        try:
            data = get(
                "https://api.openalex.org/works/doi:"
                + urllib.parse.quote(doi, safe="/")
            )
        except Exception as exc:
            print(f"{row['id']} abstract FETCH FAILED: {exc}")
            out.append({**row, "abstract": "", "openalex_id": "", "oa_status": ""})
            continue
        (RAW / f"openalex_{row['id']}.json").write_text(json.dumps(data, indent=1))
        txt = abstract_text(data.get("abstract_inverted_index"))
        out.append(
            {
                **row,
                "abstract": txt,
                "openalex_id": data.get("id", ""),
                "oa_status": (data.get("open_access") or {}).get("oa_status", ""),
            }
        )
        print(f"{row['id']} abstract {'OK' if txt else 'MISSING'} ({len(txt)} chars)")
        time.sleep(0.25)

    with (HERE / "source_registry_with_abstracts.json").open("w") as fh:
        json.dump(out, fh, indent=1)

    with (HERE / "source_registry.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main()
