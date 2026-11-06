"""Journal metadata for every source in the venue files (plan V1, V2): two-year mean citedness, DOAJ, APC.

Reads the source ids in data*/venues/venues_*.csv.gz (written by fetch_venues.py) and fetches, 100 ids per
request, id, display_name, type, summary_stats.2yr_mean_citedness, is_in_doaj, is_oa, apc_usd and the ISSNs (issn_l, issn; for the Scimago match). Values are
current OpenAlex values, not contemporaneous ones (a caveat fixed in the plan).

Usage:
    python fetch_sources.py            # writes data_meta/sources.csv.gz
"""
import csv
import glob
import gzip
import os
import sys

import pandas as pd

import config
from fetch_openalex import BASE, BudgetExhausted, get, short

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data_meta", "sources.csv.gz")


def main():
    if not config.OPENALEX_API_KEY:
        sys.exit("No API key found.")
    ids = set()
    for f in glob.glob(os.path.join(HERE, "data*", "venues", "venues_*.csv.gz")):
        ids |= set(pd.read_csv(f, usecols=["source_id"]).source_id.dropna())
    ids = sorted(ids)
    print(f"{len(ids):,} distinct sources", flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".part"
    try:
        with gzip.open(tmp, "wt", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["source_id", "name", "type", "citedness_2yr", "is_in_doaj", "is_oa", "apc_usd", "issn_l", "issn"])
            for k in range(0, len(ids), 100):
                chunk = ids[k:k + 100]
                data = get(f"{BASE}/sources", {"filter": "openalex_id:" + "|".join(chunk), "per_page": 100,
                                               "select": "id,display_name,type,summary_stats,is_in_doaj,is_oa,apc_usd,issn_l,issn",
                                               "api_key": config.OPENALEX_API_KEY})
                for s in data.get("results", []):
                    st = s.get("summary_stats") or {}
                    w.writerow([short(s["id"]), s.get("display_name"), s.get("type"), st.get("2yr_mean_citedness"),
                                s.get("is_in_doaj"), s.get("is_oa"), s.get("apc_usd"),
                                s.get("issn_l") or "", "|".join(s.get("issn") or [])])
                if k // 100 % 50 == 0:
                    print(f"  {k + len(chunk):,} / {len(ids):,}", flush=True)
    except BudgetExhausted as err:
        sys.exit(f"Daily budget used up ({err}); rerun tomorrow.")
    os.replace(tmp, OUT)
    print("Saved", OUT, flush=True)


if __name__ == "__main__":
    main()
