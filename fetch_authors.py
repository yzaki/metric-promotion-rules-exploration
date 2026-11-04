"""Fetch author metadata (name, ORCID, last known institutions) and Italian institution regions.

For every scientist in the trajectory files of the given fields, retrieves from OpenAlex
(100 ids per request): display_name, orcid, last_known_institutions. For institutions of
Italian scientists, retrieves geo.region. Writes data_meta/authors.csv.gz and
data_meta/institutions_it.csv.gz (resumable: already-fetched ids are skipped).

Usage:
    python fetch_authors.py
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
TRAJ = ["data/trajectories_es.csv", "data_field22/trajectories_es.csv", "data_field13/trajectories_es.csv",
        "data/trajectories.csv", "data_field22/trajectories.csv", "data_field13/trajectories.csv"]


def batches(ids, n=100):
    ids = list(ids)
    for i in range(0, len(ids), n):
        yield ids[i:i + n]


def fetch(entity, ids, select, out, row_fn, header):
    done = set()
    if os.path.exists(out):
        done = set(pd.read_csv(out, usecols=["id"], encoding="utf-8").id)
    todo = [i for i in ids if i not in done]
    print(f"{entity}: {len(done):,} done, {len(todo):,} to fetch")
    mode = "at" if done else "wt"
    with gzip.open(out, mode, newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if not done:
            w.writerow(header)
        for k, b in enumerate(batches(todo)):
            data = get(f"{BASE}/{entity}", {"filter": "openalex_id:" + "|".join(b), "per_page": 100,
                                            "select": select, "api_key": config.OPENALEX_API_KEY})
            for r in data.get("results", []):
                w.writerow(row_fn(r))
            if (k + 1) % 100 == 0:
                print(f"  {entity}: {(k + 1) * 100:,} / {len(todo):,}")
                f.flush()


def author_row(r):
    insts = r.get("last_known_institutions") or []
    return [short(r["id"]), r.get("display_name") or "", short(r.get("orcid") or "").replace("https://orcid.org/", ""),
            "|".join(short(i.get("id")) for i in insts), "|".join(i.get("country_code") or "" for i in insts)]


def inst_row(r):
    geo = r.get("geo") or {}
    return [short(r["id"]), r.get("display_name") or "", geo.get("region") or "", geo.get("city") or ""]


def main():
    if not config.OPENALEX_API_KEY:
        sys.exit("No API key")
    os.makedirs(META, exist_ok=True)
    authors = set()
    for p in TRAJ:
        f = os.path.join(config.HERE, p)
        if os.path.exists(f):
            authors |= set(pd.read_csv(f, usecols=["author_id"]).author_id)
    print(f"{len(authors):,} scientists across fields")
    a_out = os.path.join(META, "authors.csv.gz")
    try:
        fetch("authors", sorted(authors), "id,display_name,orcid,last_known_institutions", a_out, author_row,
              ["id", "name", "orcid", "inst_ids", "inst_countries"])
        a = pd.read_csv(a_out, dtype=str, encoding="utf-8").fillna("")
        it_insts = {i for ids, cc in zip(a.inst_ids, a.inst_countries)
                    for i, c in zip(ids.split("|"), cc.split("|")) if i and c == "IT"}
        fetch("institutions", sorted(it_insts), "id,display_name,geo",
              os.path.join(META, "institutions_it.csv.gz"), inst_row, ["id", "name", "region", "city"])
    except BudgetExhausted as err:
        print(f"Budget exhausted: {err}; rerun later to resume.")
        sys.exit(0)
    print("Done.")


if __name__ == "__main__":
    main()
