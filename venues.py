"""Where scientists published, and with how many institutions (plan ../PREREGISTRATION_venues_coauthors_2026-11-05.md).

Scientist-year outcomes over the scientist's articles in the field (venue files from fetch_venues.py, journal
metadata from fetch_sources.py):
    V1 top_quartile, bottom_quartile   share of articles in the top / bottom quartile of the field's journals,
                                       journals ranked by OpenAlex two-year mean citedness (current values),
                                       quartiles weighted by the field's articles in our data (all five
                                       countries' venue files, decision years, one ranking per field)
       journal_pct                     mean article-weighted percentile of the journal (0-100)
    V2 fee_oa                          share of articles in journals listed in DOAJ with an APC > 0
    C4 n_institutions, single_inst     distinct institutions per article; share of single-institution articles
    *_yr (exploratory, not in the plan) the same journal tier measured in the year of publication: journals
                                       ranked within each year by the field-year-normalised citations of that
                                       year's articles by French or German authors without a treated-country
                                       author (journal_year_ranks), because current citedness misstates the
                                       standing of a journal in 2004-09
    *_yr_intl (exploratory check)      the same, excluding domestic journals: journals where the treated
                                       country holds at least DOMESTIC_SHARE of the field's articles in the
                                       five countries' venue files (tests whether newly indexed national
                                       journals drive the shift)
The scientist-year panel is saved as <out>/panel_<treated>.csv.gz for venue_checks.py (placebo, event study).
V1 and V2 use articles whose primary location is a journal with a citedness value; C4 uses all articles.
Difference-in-differences as in coauthors.py (treated vs France + Germany, 2004-09 vs 2013-18, scientist and
year fixed effects, clustered by scientist), per field and stacked.

Usage:
    python venues.py --treated IT --out results_venues
    python venues.py --treated IN --groups results_india/india_groups.csv --covered-label UGC-covered --out results_venues
    python venues.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100 --out results_venues
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

import build_trajectories as bt
import config
from coauthors import FIELDS, SUFFIX, did_rows

HERE = os.path.dirname(os.path.abspath(__file__))
OUTCOMES = ["top_quartile", "bottom_quartile", "journal_pct", "fee_oa", "n_institutions", "single_inst",
            "top_quartile_yr", "bottom_quartile_yr", "journal_pct_yr",
            "top_quartile_yr_intl", "bottom_quartile_yr_intl", "journal_pct_yr_intl"]
DOMESTIC_SHARE = 0.25


def journal_ranks(venues, sources):
    """Article-weighted quartile and percentile of each journal in the field."""
    j = venues.merge(sources, on="source_id", how="inner")
    j = j[(j.source_type == "journal") & j.citedness_2yr.notna()]
    w = j.groupby("source_id").agg(n=("work_id", "size"), c=("citedness_2yr", "first")).sort_values("c")
    cum = w.n.cumsum() / w.n.sum()
    w["pct"] = 100 * (cum - w.n / (2 * w.n.sum()))          # mid-point of the journal's article mass
    w["quartile"] = np.minimum(4, 1 + np.floor(4 * (cum - w.n / (2 * w.n.sum()))).astype(int))   # 1 bottom, 4 top
    return w[["pct", "quartile"]]


def journal_year_ranks(ven, raw, treated, min_control=5):
    """Contemporaneous journal tier (exploratory, not in the plan): for each journal and publication year, the
    mean field-year-normalised citation count of its articles by French or German authors without a
    treated-country author (so the treated country's own papers do not set their journals' rank); journals
    with at least `min_control` such articles are ranked within each year, quartiles weighted by all of the
    journal-year's articles in the venue files."""
    w = raw.groupby("work_id").agg(year=("year", "first"), cites=("cited_by_count", "first"),
                                   cc=("countries", lambda s: set("|".join(s).split("|"))))
    w["control"] = [("FR" in c or "DE" in c) and treated not in c for c in w.cc]
    j = ven[ven.source_type == "journal"][["work_id", "source_id"]].join(w[["year", "cites", "control"]], on="work_id", how="inner")
    c = j[j.control].copy()
    c["norm"] = c.cites / c.groupby("year").cites.transform("mean")
    score = c.groupby(["year", "source_id"]).norm.agg(["mean", "size"])
    score = score[score["size"] >= min_control]["mean"].rename("score")
    n = j.groupby(["year", "source_id"]).size().rename("n")
    t = pd.concat([score, n], axis=1, join="inner").reset_index().sort_values(["year", "score"])
    tot = t.groupby("year").n.transform("sum")
    mid = (t.groupby("year").n.cumsum() - t.n / 2) / tot
    t["pct_yr"] = 100 * mid
    t["quartile_yr"] = np.minimum(4, 1 + np.floor(4 * mid).astype(int))
    return t.set_index(["year", "source_id"])[["pct_yr", "quartile_yr"]]


def field_outcomes(field_id, treated, sources):
    name, d = FIELDS[field_id]
    config.FIELD_ID = field_id
    config.DATA_DIR = os.path.join(HERE, d)
    config.RAW_DIR = os.path.join(config.DATA_DIR, "raw")
    config.TREATED = treated
    config.COUNTRIES = [treated, "FR", "DE"]
    traj = pd.read_csv(os.path.join(HERE, d, f"trajectories_{SUFFIX[treated]}.csv"), usecols=["author_id", "country", "group"])
    home = traj.drop_duplicates("author_id").set_index("author_id")
    files = glob.glob(os.path.join(HERE, d, "venues", "venues_*.csv.gz"))
    ven = pd.concat((pd.read_csv(f).assign(cc=os.path.basename(f).split("_")[1]) for f in files), ignore_index=True)
    in_treated = set(ven.work_id[ven.cc == treated])
    ven = ven.drop_duplicates("work_id").drop(columns="cc")
    # domestic journals (exploratory check): the treated country holds >= DOMESTIC_SHARE of the journal's articles
    # in the five countries' venue files of this field
    share = ven[ven.source_type == "journal"].assign(t=ven.work_id.isin(in_treated)).groupby("source_id").t.mean()
    domestic = set(share[share >= DOMESTIC_SHARE].index)
    ranks = journal_ranks(ven, sources)
    doaj_fee = set(sources.source_id[(sources.is_in_doaj == True) & (sources.apc_usd.fillna(0) > 0)])  # noqa: E712
    ven = ven.join(ranks, on="source_id")
    ven["top_quartile"] = (ven.quartile == 4).astype(float).where(ven.quartile.notna())
    ven["bottom_quartile"] = (ven.quartile == 1).astype(float).where(ven.quartile.notna())
    ven["journal_pct"] = ven.pct
    ven["fee_oa"] = ven.source_id.isin(doaj_fee).astype(float).where(ven.quartile.notna())
    ven["single_inst"] = (ven.n_institutions <= 1).astype(float).where(ven.n_institutions > 0)
    ven["n_institutions"] = ven.n_institutions.where(ven.n_institutions > 0)
    full = bt.load_raw()
    yr = journal_year_ranks(ven, full, treated)
    raw = full[["work_id", "year", "author_id"]]
    del full
    wy = raw.drop_duplicates("work_id").set_index("work_id").year
    ven["year"] = ven.work_id.map(wy)
    ven = ven.join(yr, on=["year", "source_id"])
    ven["top_quartile_yr"] = (ven.quartile_yr == 4).astype(float).where(ven.quartile_yr.notna())
    ven["bottom_quartile_yr"] = (ven.quartile_yr == 1).astype(float).where(ven.quartile_yr.notna())
    ven["journal_pct_yr"] = ven.pct_yr
    intl = ~ven.source_id.isin(domestic)
    for c in ("top_quartile_yr", "bottom_quartile_yr", "journal_pct_yr"):
        ven[c + "_intl"] = ven[c].where(intl)
    mine = raw[raw.author_id.isin(home.index)].drop_duplicates()
    mine = mine.merge(ven[["work_id"] + OUTCOMES], on="work_id", how="inner")
    ay = mine.groupby(["author_id", "year"])[OUTCOMES].mean().reset_index()
    ay["group"] = ay.author_id.map(home.group)
    ay["field"] = name
    dec = raw[raw.author_id.isin(home.index) & raw.year.isin(config.PRE_YEARS + config.POST_YEARS)].drop_duplicates()
    cov = mine.year.isin(config.PRE_YEARS + config.POST_YEARS).sum() / max(1, len(dec))
    dom_art = mine.work_id.map(ven.set_index("work_id").source_id).isin(domestic)
    print(f"  {name}: {len(ranks):,} ranked journals; {cov:.1%} of sampled author-articles in decision years "
          f"matched to a venue row; {len(domestic):,} domestic journals ({dom_art[mine.author_id.map(home.group) == 'IT'].mean():.1%} "
          f"of treated scientists' articles)", flush=True)
    return ay


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--treated", required=True, choices=list(SUFFIX))
    ap.add_argument("--out", default=os.path.join(HERE, "results_venues"))
    ap.add_argument("--groups", default=None, help="csv author_id,group: also estimate by group and the difference")
    ap.add_argument("--covered-label", default="UGC-covered")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    sources = pd.read_csv(os.path.join(HERE, "data_meta", "sources.csv.gz"))
    parts = []
    for fid in FIELDS:
        a = field_outcomes(fid, args.treated, sources)
        a = a[a.year.isin(config.PRE_YEARS + config.POST_YEARS)]
        parts.append(a)
        print(f"{args.treated} {FIELDS[fid][0]}: {a.author_id.nunique():,} scientists, {len(a):,} scientist-years", flush=True)
    A = pd.concat(parts, ignore_index=True)
    A.to_csv(os.path.join(args.out, f"panel_{args.treated}.csv.gz"), index=False)
    rows = did_rows(A, OUTCOMES, args.treated, args.groups, args.covered_label)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(args.out, f"venues_{args.treated}.csv"), index=False)
    print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
