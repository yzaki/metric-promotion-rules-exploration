"""Journal and institutions of each article (plan ../PREREGISTRATION_venues_coauthors_2026-11-05.md, V1, V2, C4).

For each country-year of the decision years (2004-09, 2013-18), fetches the field's articles again with only
id, primary_location and authorships, and saves one row per article: work_id, source_id (the journal of the
primary location, empty if none), source_type, n_institutions (distinct institutions over all authorships)
and n_authorships. Files go to <data dir>/venues/venues_<CC>_<YEAR>.csv.gz; finished files are skipped, so
it resumes after the daily budget runs out. 200 papers per request.

Then `python fetch_sources.py` downloads the journal metadata (two-year mean citedness, DOAJ, APC).

Usage (field via CT_FIELD_ID, as for fetch_openalex.py):
    python fetch_venues.py --countries IT --years 2005      # test
    python fetch_venues.py --countries IT FR DE IN RU       # all decision years
"""
import argparse
import csv
import gzip
import os
import sys

import config
from fetch_openalex import BASE, BudgetExhausted, check_field, get, short

VENUE_DIR = os.path.join(config.DATA_DIR, "venues")
YEARS = list(range(2004, 2010)) + list(range(2013, 2019))


def fetch_country_year(cc, year, field_filter):
    out = os.path.join(VENUE_DIR, f"venues_{cc}_{year}.csv.gz")
    if os.path.exists(out):
        print(f"  {cc} {year}: already downloaded, skipping", flush=True)
        return
    params = {
        "filter": (f"authorships.institutions.country_code:{cc},publication_year:{year},"
                   f"primary_topic.field.id:{field_filter},type:article"),
        "select": "id,primary_location,authorships",
        "per_page": 200,
        "cursor": "*",
        "api_key": config.OPENALEX_API_KEY,
    }
    tmp = out + ".part"
    n = 0
    with gzip.open(tmp, "wt", newline="") as f:
        w = csv.writer(f)
        w.writerow(["work_id", "source_id", "source_type", "n_institutions", "n_authorships"])
        while params["cursor"]:
            data = get(f"{BASE}/works", params)
            for work in data.get("results", []):
                src = ((work.get("primary_location") or {}).get("source") or {})
                aus = work.get("authorships") or []
                inst = {i.get("id") for a in aus for i in (a.get("institutions") or []) if i.get("id")}
                w.writerow([short(work["id"]), short(src.get("id")), src.get("type") or "", len(inst), len(aus)])
                n += 1
            params["cursor"] = data["meta"].get("next_cursor")
            if not data.get("results"):
                break
    os.replace(tmp, out)
    print(f"  {cc} {year}: {n:,} papers", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--countries", nargs="+", default=["IT", "FR", "DE", "IN", "RU"])
    ap.add_argument("--years", nargs="+", type=int, default=YEARS)
    args = ap.parse_args()
    if not config.OPENALEX_API_KEY:
        sys.exit("No API key found; cursor paging needs one.")
    os.makedirs(VENUE_DIR, exist_ok=True)
    field_filter = check_field(config.FIELD_ID)
    try:
        for cc in args.countries:
            for year in args.years:
                fetch_country_year(cc, year, field_filter)
    except BudgetExhausted as err:
        print(f"\nDaily budget used up ({err}).\nRun the same command tomorrow; it resumes.", flush=True)
        sys.exit(3)
    print("\nDone.", flush=True)


if __name__ == "__main__":
    main()
