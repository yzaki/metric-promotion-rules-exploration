"""Step 1: download papers from OpenAlex.

For each country (Italy, France, Germany) and each year, downloads every journal
article in the chosen field with at least one author from that country, and
saves one row per (paper, author). Files are saved per country-year, so you can
stop and restart: finished files are skipped.

Before running:
    1. Get a free API key at https://openalex.org/settings/api
    2. export OPENALEX_API_KEY="your-key"

Usage:
    python fetch_openalex.py                          # all countries and years in config.py
    python fetch_openalex.py --countries IT --years 2004 2005

Budget: the free key allows $1 of use per day. Each page holds up to 100 papers.
If you run out, the script stops cleanly; run it again the next day and it resumes.
"""
import argparse
import csv
import gzip
import os
import sys
import time

import requests

import config

BASE = "https://api.openalex.org"
SELECT = "id,publication_year,cited_by_count,primary_topic,authorships"
COLUMNS = ["work_id", "year", "cited_by_count", "topic_id", "subfield_id",
           "author_id", "countries"]

session = requests.Session()


class BudgetExhausted(Exception):
    pass


def short(openalex_id):
    """'https://openalex.org/T10001' -> 'T10001'."""
    return (openalex_id or "").replace("https://openalex.org/", "")


def get(url, params, tries=8):
    """GET with retries on rate limits and server errors."""
    params = {k: v for k, v in params.items() if not (k == "api_key" and not v)}   # keyless if no key
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, timeout=90)
        except requests.RequestException as err:
            wait = min(60, 2 ** attempt)
            print(f"    network error ({err}); retrying in {wait}s")
            time.sleep(wait)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429 and "budget" in r.text.lower():
            raise BudgetExhausted(r.text[:300])
        if r.status_code in (429, 500, 502, 503, 504):
            wait = min(60, 2 ** attempt)
            print(f"    HTTP {r.status_code}; retrying in {wait}s")
            time.sleep(wait)
            continue
        raise RuntimeError(f"HTTP {r.status_code} for {r.url}\n{r.text[:500]}")
    raise RuntimeError(f"Gave up after {tries} tries: {url}")


def check_field(field_id):
    """Print the field's name, and find which id format the works filter accepts."""
    data = get(f"{BASE}/fields/{field_id}", {"api_key": config.OPENALEX_API_KEY})
    print(f"Field {field_id} = {data.get('display_name')}")
    for candidate in (field_id, f"fields/{field_id}", f"https://openalex.org/fields/{field_id}"):
        try:
            test = get(f"{BASE}/works", {"filter": f"primary_topic.field.id:{candidate}",
                                         "per_page": 1, "api_key": config.OPENALEX_API_KEY}, tries=3)
        except RuntimeError:
            continue
        if test["meta"]["count"] > 0:
            print(f"Using field filter primary_topic.field.id:{candidate}")
            return candidate
    raise SystemExit("Could not filter works by this field id. Check FIELD_ID in config.py.")


def rows_from_work(work):
    topic = work.get("primary_topic") or {}
    if not topic.get("id"):
        return
    topic_id = short(topic["id"])
    subfield_id = short((topic.get("subfield") or {}).get("id"))
    for au in work.get("authorships") or []:
        author_id = short((au.get("author") or {}).get("id"))
        if not author_id:
            continue
        countries = au.get("countries") or sorted({i.get("country_code") for i in au.get("institutions") or []
                                                   if i.get("country_code")})
        yield [short(work["id"]), work.get("publication_year"), work.get("cited_by_count", 0),
               topic_id, subfield_id, author_id, "|".join(countries)]


def fetch_country_year(cc, year, field_id):
    out = os.path.join(config.RAW_DIR, f"works_{cc}_{year}.csv.gz")
    if os.path.exists(out):
        print(f"  {cc} {year}: already downloaded, skipping")
        return
    params = {
        "filter": (f"authorships.institutions.country_code:{cc},publication_year:{year},"
                   f"primary_topic.field.id:{field_id},type:article"),
        "select": SELECT,
        "per_page": 200,
        "cursor": "*",
        "api_key": config.OPENALEX_API_KEY,
    }
    tmp = out + ".part"
    n_works = n_rows = 0
    with gzip.open(tmp, "wt", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        while params["cursor"]:
            data = get(f"{BASE}/works", params)
            if n_works == 0:
                print(f"  {cc} {year}: {data['meta']['count']:,} papers to download")
            for work in data.get("results", []):
                for row in rows_from_work(work):
                    writer.writerow(row)
                    n_rows += 1
                n_works += 1
            params["cursor"] = data["meta"].get("next_cursor")
            if not data.get("results"):
                break
    os.replace(tmp, out)   # only a complete file gets the final name
    print(f"  {cc} {year}: saved {n_works:,} papers, {n_rows:,} author rows")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--countries", nargs="+", default=config.COUNTRIES)
    ap.add_argument("--years", nargs="+", type=int, default=config.FETCH_YEARS)
    ap.add_argument("--field", default=config.FIELD_ID)
    args = ap.parse_args()

    if not config.OPENALEX_API_KEY:
        print("No API key found: running keyless, which allows only about 1,000 requests a day.\n"
              "Get a free key at https://openalex.org/settings/api and run:\n"
              '    export OPENALEX_API_KEY="your-key"\n')
    os.makedirs(config.RAW_DIR, exist_ok=True)
    field_filter = check_field(args.field)
    try:
        for cc in args.countries:
            for year in args.years:
                fetch_country_year(cc, year, field_filter)
    except BudgetExhausted as err:
        print(f"\nDaily free budget used up ({err}).\nRun the same command tomorrow; it resumes where it stopped.")
        sys.exit(0)
    print("\nDone. Next step: python build_trajectories.py")


if __name__ == "__main__":
    main()
