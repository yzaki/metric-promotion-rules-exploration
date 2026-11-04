"""Step 1b: download WORLD-WIDE citation distributions per topic and year.

The citation potential in build_trajectories.py is, by default, computed from the
downloaded countries' papers only. This script gets the citation counts of every
article in the field, world-wide, without downloading the papers themselves: for each
topic and year, OpenAlex returns how many articles have 0, 1, 2, ... citations
(group_by=cited_by_count). Roughly 2 requests per topic-year.

Writes data/world/cites_<YEAR>.csv.gz with columns topic_id, year, cited_by_count, n.
Finished years are skipped, so it resumes after the daily budget runs out.

Usage:
    python fetch_world_citations.py                     # all years in config.py
    python fetch_world_citations.py --years 2005        # test one year
    python build_trajectories.py --world                # use it
"""
import argparse
import csv
import gzip
import os
import sys

import config
from fetch_openalex import BASE, BudgetExhausted, check_field, get, short

WORLD_DIR = os.path.join(config.DATA_DIR, "world")


def grouped(filter_str, group_by):
    """All groups for a filter, following the cursor; yields (key, count)."""
    params = {"filter": filter_str, "group_by": group_by, "per_page": 200, "cursor": "*",
              "api_key": config.OPENALEX_API_KEY}
    while params["cursor"]:
        data = get(f"{BASE}/works", params)
        groups = data.get("group_by", [])
        for g in groups:
            yield g["key"], g["count"]
        if len(groups) < 200:   # last page: skip the extra empty request
            break
        params["cursor"] = data["meta"].get("next_cursor")


def fetch_year(year, field_filter):
    out = os.path.join(WORLD_DIR, f"cites_{year}.csv.gz")
    if os.path.exists(out):
        print(f"  {year}: already downloaded, skipping")
        return
    base = f"publication_year:{year},primary_topic.field.id:{field_filter},type:article"
    topics = [(short(k), c) for k, c in grouped(base, "primary_topic.id") if k]
    tmp = out + ".part"
    n_papers = 0
    with gzip.open(tmp, "wt", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["topic_id", "year", "cited_by_count", "n"])
        for topic_id, count in topics:
            got = 0
            for key, n in grouped(f"{base},primary_topic.id:{topic_id}", "cited_by_count"):
                writer.writerow([topic_id, year, int(key), n])
                got += n
            if got != count:
                print(f"    note: {topic_id} {year}: {got} of {count} papers in citation groups")
            n_papers += got
    os.replace(tmp, out)
    print(f"  {year}: {len(topics)} topics, {n_papers:,} papers")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--years", nargs="+", type=int, default=config.FETCH_YEARS)
    args = ap.parse_args()
    if not config.OPENALEX_API_KEY:
        sys.exit("No API key found; cursor paging needs one. See fetch_openalex.py.")
    os.makedirs(WORLD_DIR, exist_ok=True)
    field_filter = check_field(config.FIELD_ID)
    try:
        for year in args.years:
            fetch_year(year, field_filter)
    except BudgetExhausted as err:
        print(f"\nDaily free budget used up ({err}).\nRun the same command tomorrow; it resumes.")
        sys.exit(0)
    print("\nDone. Next step: python build_trajectories.py --world")


if __name__ == "__main__":
    main()
