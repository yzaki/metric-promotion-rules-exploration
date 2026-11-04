"""Stage B, step 1: download each paper's reference list (for novelty measures).

For each country-year already downloaded, fetches the same articles again with only
id + referenced_works, and saves one row per (paper, referenced work). Files go to
data/refs/refs_<CC>_<YEAR>.csv.gz; finished files are skipped, so it resumes after the
daily budget runs out. About one request per 100 papers (same as fetch_openalex.py).

Usage:
    python fetch_references.py --countries IT --years 2005    # test
    python fetch_references.py                                # all countries and years
"""
import argparse
import csv
import gzip
import os
import sys

import config
from fetch_openalex import BASE, BudgetExhausted, check_field, get, short

REFS_DIR = os.path.join(config.DATA_DIR, "refs")


def fetch_country_year(cc, year, field_filter):
    out = os.path.join(REFS_DIR, f"refs_{cc}_{year}.csv.gz")
    if os.path.exists(out):
        print(f"  {cc} {year}: already downloaded, skipping")
        return
    params = {
        "filter": (f"authorships.institutions.country_code:{cc},publication_year:{year},"
                   f"primary_topic.field.id:{field_filter},type:article"),
        "select": "id,referenced_works",
        "per_page": 100,
        "cursor": "*",
        "api_key": config.OPENALEX_API_KEY,
    }
    tmp = out + ".part"
    n_works = n_refs = 0
    with gzip.open(tmp, "wt", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["work_id", "ref_id"])
        while params["cursor"]:
            data = get(f"{BASE}/works", params)
            for work in data.get("results", []):
                wid = short(work["id"])
                for ref in work.get("referenced_works") or []:
                    writer.writerow([wid, short(ref)])
                    n_refs += 1
                n_works += 1
            params["cursor"] = data["meta"].get("next_cursor")
            if not data.get("results"):
                break
    os.replace(tmp, out)
    print(f"  {cc} {year}: {n_works:,} papers, {n_refs:,} references")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--countries", nargs="+", default=config.COUNTRIES)
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2001, 2020)))
    args = ap.parse_args()
    if not config.OPENALEX_API_KEY:
        sys.exit("No API key found; cursor paging needs one.")
    os.makedirs(REFS_DIR, exist_ok=True)
    field_filter = check_field(config.FIELD_ID)
    try:
        for cc in args.countries:
            for year in args.years:
                fetch_country_year(cc, year, field_filter)
    except BudgetExhausted as err:
        print(f"\nDaily free budget used up ({err}).\nRun the same command tomorrow; it resumes.")
        sys.exit(0)
    print("\nDone.")


if __name__ == "__main__":
    main()
