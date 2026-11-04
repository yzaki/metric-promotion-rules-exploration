"""Fetch dated affiliations of Italian scientists (OpenAlex author 'affiliations': institution + years)
and the type of each institution (education, facility, government, healthcare, company, ...).

Writes data_meta/affiliations_it.csv.gz (author_id, institution_id, country, year) and
data_meta/institution_types.csv.gz (id, name, type, country). Resumable.

Usage:
    python fetch_affiliations.py
"""
import csv
import glob
import gzip
import os
import sys

import pandas as pd

import config
from fetch_openalex import BASE, BudgetExhausted, get, short

META = os.path.join(config.HERE, "data_meta")


def batches(ids, n=100):
    ids = list(ids)
    for i in range(0, len(ids), n):
        yield ids[i:i + n]


def main():
    if not config.OPENALEX_API_KEY:
        sys.exit("No API key")
    it = set()
    for f in ("data/trajectories_world_career.csv", "data_field22/trajectories_world_career.csv",
              "data_field13/trajectories_world_career.csv"):
        d = pd.read_csv(os.path.join(config.HERE, f), usecols=["author_id", "group"])
        it |= set(d.author_id[d.group == "IT"])
    out = os.path.join(META, "affiliations_it.csv.gz")
    done = set(pd.read_csv(out, usecols=["author_id"]).author_id) if os.path.exists(out) else set()
    todo = sorted(it - done)
    print(f"Italian scientists {len(it):,}; to fetch {len(todo):,}")
    try:
        with gzip.open(out, "at" if done else "wt", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not done:
                w.writerow(["author_id", "institution_id", "country", "year"])
            for k, b in enumerate(batches(todo)):
                data = get(f"{BASE}/authors", {"filter": "openalex_id:" + "|".join(b), "per_page": 100,
                                               "select": "id,affiliations", "api_key": config.OPENALEX_API_KEY})
                for r in data.get("results", []):
                    aid = short(r["id"])
                    wrote = False
                    for a in r.get("affiliations") or []:
                        inst = a.get("institution") or {}
                        for y in a.get("years") or []:
                            w.writerow([aid, short(inst.get("id")), inst.get("country_code") or "", y])
                            wrote = True
                    if not wrote:
                        w.writerow([aid, "", "", ""])
                if (k + 1) % 50 == 0:
                    print(f"  {(k + 1) * 100:,} / {len(todo):,}", flush=True)
        aff = pd.read_csv(out, dtype={"institution_id": str})
        ids = sorted(set(aff.institution_id.dropna()) - {""})
        tout = os.path.join(META, "institution_types.csv.gz")
        tdone = set(pd.read_csv(tout, usecols=["id"]).id) if os.path.exists(tout) else set()
        ttodo = [i for i in ids if i not in tdone]
        print(f"Institutions {len(ids):,}; to fetch {len(ttodo):,}")
        with gzip.open(tout, "at" if tdone else "wt", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if not tdone:
                w.writerow(["id", "name", "type", "country"])
            for b in batches(ttodo):
                data = get(f"{BASE}/institutions", {"filter": "openalex_id:" + "|".join(b), "per_page": 100,
                                                    "select": "id,display_name,type,country_code",
                                                    "api_key": config.OPENALEX_API_KEY})
                for r in data.get("results", []):
                    w.writerow([short(r["id"]), r.get("display_name") or "", r.get("type") or "",
                                r.get("country_code") or ""])
    except BudgetExhausted as err:
        sys.exit(f"Budget exhausted: {err}; rerun to resume.")
    print("Done.")


if __name__ == "__main__":
    main()
