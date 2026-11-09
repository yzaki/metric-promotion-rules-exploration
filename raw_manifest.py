"""Manifest of the raw OpenAlex works files: download time, SHA-256, articles, and the live OpenAlex count of the
same query on the day the manifest was made (shows which files predate a reclassification).
Usage: python raw_manifest.py   (needs OPENALEX_API_KEY for the live counts)
"""
import datetime, glob, hashlib, os, re
from concurrent.futures import ThreadPoolExecutor
import pandas as pd, requests

HERE = os.path.dirname(os.path.abspath(__file__))
FIELD = {"data": 31, "data_field22": 22, "data_field13": 13, "data_field16": 16, "data_field20": 20}
KEY = os.environ.get("OPENALEX_API_KEY", "")


def live(field, cc, year):
    f = f"primary_topic.field.id:{field},authorships.institutions.country_code:{cc.lower()},publication_year:{year},type:article"
    try:
        return requests.get("https://api.openalex.org/works", params={"filter": f, "per-page": 1, "api_key": KEY},
                            timeout=60).json()["meta"]["count"]
    except Exception:
        return None


def row(f):
    d = os.path.basename(os.path.dirname(os.path.dirname(f)))
    cc, year = re.match(r"works_([A-Z]{2})_(\d{4})", os.path.basename(f)).groups()
    h = hashlib.sha256(open(f, "rb").read()).hexdigest()
    n = pd.read_csv(f, usecols=["work_id"]).work_id.nunique()
    t = datetime.datetime.fromtimestamp(os.path.getmtime(f)).strftime("%Y-%m-%d %H:%M")
    l = live(FIELD[d], cc, int(year)) if KEY else None
    return {"folder": d, "file": os.path.basename(f), "field": FIELD[d], "country": cc, "year": int(year),
            "downloaded": t, "sha256": h, "articles": n, "live_count": l,
            "live_minus_file_pct": None if not l else round(100 * (l - n) / l, 2)}


def main():
    files = sorted(glob.glob(os.path.join(HERE, "data*", "raw", "works_*.csv.gz")))
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(row, files))
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(HERE, "data_meta", "raw_manifest.csv"), index=False)
    s = t.groupby(["field", "country"]).agg(downloaded=("downloaded", "min"), files=("file", "size"),
                                            max_abs_gap_pct=("live_minus_file_pct", lambda x: x.abs().max()))
    print(s.to_string())


if __name__ == "__main__":
    main()
