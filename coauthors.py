"""Co-authorship before and after the reforms (plan ../PREREGISTRATION_venues_coauthors_2026-11-05.md).

Scientist-year outcomes over the scientist's articles in the field (stored author lists and affiliation
countries; no new download):
    C1 team_size, log_team     listed authors per article (OpenAlex lists at most 100)
    C2 international           share of articles with an author outside the scientist's country
    C3 new_coauthors           share of the year's distinct co-authors with no joint article in the six previous
                               years; computed on articles with at most 20 authors (deviation from the plan:
                               co-author pairs of very large collaborations do not fit in memory)
Difference-in-differences (treated vs France + Germany, 2004-09 vs 2013-18) with scientist and year fixed
effects, clustered by scientist; per field and stacked over the four fields.

Usage:
    python coauthors.py --treated IT --out results_coauthors
    python coauthors.py --treated IN --out results_coauthors
"""
import argparse
import os

import numpy as np
import pandas as pd

import build_trajectories as bt
import config
from india_stacked import fit

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = {"31": ("Physics", "data"), "22": ("Engineering", "data_field22"),
          "13": ("Biochemistry", "data_field13"), "16": ("Chemistry", "data_field16")}
SUFFIX = {"IT": "world", "IN": "world_IN", "RU": "world_RU"}
OUTCOMES = ["team_size", "log_team", "international", "new_coauthors"]


def field_outcomes(field_id, treated):
    name, d = FIELDS[field_id]
    config.FIELD_ID = field_id
    config.DATA_DIR = os.path.join(HERE, d)
    config.RAW_DIR = os.path.join(config.DATA_DIR, "raw")
    config.TREATED = treated
    config.COUNTRIES = [treated, "FR", "DE"]
    traj = pd.read_csv(os.path.join(HERE, d, f"trajectories_{SUFFIX[treated]}.csv"), usecols=["author_id", "country", "group"])
    home = traj.drop_duplicates("author_id").set_index("author_id")
    raw = bt.load_raw()[["work_id", "year", "author_id", "countries"]]
    team = raw.groupby("work_id").author_id.nunique().rename("team")
    wc = raw.assign(c=raw.countries.str.split("|")).explode("c")
    wc = wc[wc.c.fillna("") != ""].groupby("work_id").c.agg(set)
    mine = raw[raw.author_id.isin(home.index)][["work_id", "year", "author_id"]].drop_duplicates()
    mine = mine.join(team, on="work_id").join(wc.rename("wcs"), on="work_id")
    mine["home"] = mine.author_id.map(home.country)
    mine["international"] = [float(bool(s) and len(s - {h}) > 0) if isinstance(s, set) else np.nan
                             for s, h in zip(mine.wcs, mine.home)]
    ay = mine.groupby(["author_id", "year"]).agg(team_size=("team", "mean"), international=("international", "mean"))
    ay["log_team"] = mine.assign(lt=np.log(mine.team)).groupby(["author_id", "year"]).lt.mean()
    # new co-authors, articles with at most 20 authors
    small = raw[raw.work_id.map(team) <= 20][["work_id", "year", "author_id"]].drop_duplicates()
    pairs = small[small.author_id.isin(home.index)].merge(small, on=["work_id", "year"], suffixes=("", "_co"))
    pairs = pairs[pairs.author_id != pairs.author_id_co][["author_id", "author_id_co", "year"]].drop_duplicates()
    first = pairs.groupby(["author_id", "author_id_co"]).year.min().rename("first")
    pairs = pairs.join(first, on=["author_id", "author_id_co"])
    # 'new' = no joint article in the six previous years (first joint year is this year, or last joint year > 6 y ago)
    pairs = pairs.sort_values(["author_id", "author_id_co", "year"])
    prev = pairs.groupby(["author_id", "author_id_co"]).year.shift()
    pairs["new"] = (prev.isna() | (pairs.year - prev > 6)).astype(float)
    ay["new_coauthors"] = pairs.groupby(["author_id", "year"]).new.mean()
    ay = ay.reset_index()
    ay["group"] = ay.author_id.map(home.group)
    ay["field"] = name
    del raw, wc, mine, pairs
    return ay


def did_rows(A, outcomes, treated, groups=None, covered_label="UGC-covered"):
    """Difference-in-differences (scientist + year FE, clustered by scientist) of each outcome, stacked over
    fields and per field; with `groups` (csv author_id,group) also by covered / not covered and the difference."""
    A["d"] = ((A.group == "IT") & A.year.isin(config.POST_YEARS)).astype(float)
    rows = []
    for oc in outcomes:
        for scope in ["All four fields"] + [v[0] for v in FIELDS.values()]:
            s = (A if scope == "All four fields" else A[A.field == scope]).dropna(subset=[oc]).reset_index(drop=True)
            b, V = fit(s, oc, ["d"])
            se = np.sqrt(V[0, 0])
            pre = s[(s.group == "IT") & s.year.isin(config.PRE_YEARS)][oc].mean()
            rows.append({"treated": treated, "outcome": oc, "scope": scope, "did": b[0],
                         "ci_low": b[0] - 1.96 * se, "ci_high": b[0] + 1.96 * se, "treated_pre_mean": pre,
                         "n_treated": int(s.author_id[s.group == "IT"].nunique())})
    if groups:
        g = pd.read_csv(groups).set_index("author_id").group
        A["g"] = A.author_id.map(g)
        B = A[(A.group == "CTRL") | A.g.notna()].reset_index(drop=True)
        post = B.year.isin(config.POST_YEARS)
        B["d_cov"] = ((B.g == covered_label) & post).astype(float)
        B["d_not"] = ((B.g == "not covered") & post).astype(float)
        c = np.array([1.0, -1.0])
        for oc in outcomes:
            s = B.dropna(subset=[oc]).reset_index(drop=True)
            b, V = fit(s, oc, ["d_cov", "d_not"])
            for k, lab in enumerate((covered_label, "not covered")):
                rows.append({"treated": treated, "outcome": oc, "scope": f"All four fields, {lab}", "did": b[k],
                             "ci_low": b[k] - 1.96 * np.sqrt(V[k, k]), "ci_high": b[k] + 1.96 * np.sqrt(V[k, k]),
                             "treated_pre_mean": np.nan, "n_treated": int(s.author_id[s.g == lab].nunique())})
            dv, ds = c @ b, np.sqrt(c @ V @ c)
            rows.append({"treated": treated, "outcome": oc, "scope": f"All four fields, {covered_label} minus not covered",
                         "did": dv, "ci_low": dv - 1.96 * ds, "ci_high": dv + 1.96 * ds, "treated_pre_mean": np.nan, "n_treated": np.nan})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--treated", required=True, choices=list(SUFFIX))
    ap.add_argument("--out", default=os.path.join(HERE, "results_coauthors"))
    ap.add_argument("--groups", default=None,
                    help="csv author_id,group (e.g. results_india/india_groups.csv): also estimate by group and the difference")
    ap.add_argument("--covered-label", default="UGC-covered")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    parts = []
    for fid in FIELDS:
        a = field_outcomes(fid, args.treated)
        a = a[a.year.isin(config.PRE_YEARS + config.POST_YEARS)]
        parts.append(a)
        print(f"{args.treated} {FIELDS[fid][0]}: {a.author_id.nunique():,} scientists, {len(a):,} scientist-years", flush=True)
    A = pd.concat(parts, ignore_index=True)
    rows = did_rows(A, OUTCOMES, args.treated, args.groups, args.covered_label)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(args.out, f"coauthors_{args.treated}.csv"), index=False)
    print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
