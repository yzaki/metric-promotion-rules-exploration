"""Long-run consequences of the reform (difference-in-differences, Italy vs control).

1. Topic breadth per scientist and period (before 2004-09, after 2013-18; at least 3 articles):
   distinct topics, distinct subfields.
2. Breakthrough articles: share of a scientist's articles in the top 1% most cited of their
   publication year (all downloaded articles in the field), averaged over scientist-years.
3. Leaving research: among scientists with at least 3 articles in a base window, the share
   with no article in a later window 7 years on. Pre-reform cohort: base 2000-02, check
   2007-09. Post-reform cohort: base 2008-10, check 2015-17. Uses all scientists with a home
   country (not only the 5-active-year trajectory sample, which would condition on staying).

Bootstrap: 200 resamples of scientists within Italy and within control.

Usage:
    python long_run.py --input data/trajectories.csv              # Physics
    set CT_FIELD_ID=22 && python long_run.py --input data_field22/trajectories.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from build_trajectories import assign_countries, load_raw
from outcomes_citations import boot_ci, cell_sums


def did_stat(sums, is_it, rng, n_boot, periods=("pre", "post")):
    S, N = sums["sum"], sums["count"]
    a, b = periods

    def stat(w):
        m = {}
        for g, flag in (("IT", True), ("CTRL", False)):
            ww = w * (is_it == flag)
            for p in periods:
                m[g, p] = (ww * S[p]).sum() / (ww * N[p]).sum()
        return (m["IT", b] - m["IT", a]) - (m["CTRL", b] - m["CTRL", a])

    point, lo, hi = boot_ci(stat, sums, is_it, rng, n_boot)
    means = {f"{g}_{p}": S[p][is_it == (g == "IT")].sum() / N[p][is_it == (g == "IT")].sum()
             for g in ("IT", "CTRL") for p in periods}
    return point, lo, hi, means


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--n-boot", type=int, default=config.N_BOOT)
    args = ap.parse_args()
    rng = np.random.default_rng(config.SEED)
    rows = []

    raw = load_raw()
    group = pd.read_csv(args.input, usecols=["author_id", "group"]).drop_duplicates("author_id")
    group = group.set_index("author_id").group
    pap = raw[raw.author_id.isin(group.index)].drop_duplicates(["author_id", "work_id"]).copy()

    # 1. topic breadth
    pap["period"] = np.select([pap.year.isin(config.PRE_YEARS), pap.year.isin(config.POST_YEARS)], ["pre", "post"], "")
    p1 = pap[pap.period != ""]
    for level, name in (("topic_id", "distinct_topics"), ("subfield_id", "distinct_subfields")):
        g = p1.groupby(["author_id", "period"]).agg(n=("work_id", "size"), k=(level, "nunique")).reset_index()
        g = g[g.n >= 3].rename(columns={"k": name})
        sums = cell_sums(g, ["period"], name)
        is_it = (group.reindex(sums.index) == "IT").to_numpy()
        point, lo, hi, means = did_stat(sums, is_it, rng, args.n_boot)
        rows.append({"outcome": name, "did": point, "ci_low": lo, "ci_high": hi, **means})

    # 2. breakthrough share (top 1% of year, among all downloaded articles)
    works = raw.drop_duplicates("work_id")[["work_id", "year", "cited_by_count"]]
    works = works.assign(top1=(works.groupby("year").cited_by_count.rank(pct=True) > 0.99).astype(float))
    ay = (p1.merge(works[["work_id", "top1"]], on="work_id")
          .groupby(["author_id", "year", "period"]).top1.mean().reset_index())
    sums = cell_sums(ay, ["period"], "top1")
    is_it = (group.reindex(sums.index) == "IT").to_numpy()
    point, lo, hi, means = did_stat(sums, is_it, rng, args.n_boot)
    rows.append({"outcome": "top1_share", "did": point, "ci_low": lo, "ci_high": hi, **means})

    # 3. leaving research (all scientists with a home country)
    home = assign_countries(raw)
    allp = raw[raw.author_id.isin(home.index)].drop_duplicates(["author_id", "work_id"])
    cohorts = []
    for label, base, check in (("pre", (2000, 2002), (2007, 2009)), ("post", (2008, 2010), (2015, 2017))):
        nb = allp[allp.year.between(*base)].groupby("author_id").size()
        active = nb[nb >= 3].index
        later = set(allp[allp.year.between(*check)].author_id)
        cohorts.append(pd.DataFrame({"author_id": active, "period": label,
                                     "left": [0.0 if a in later else 1.0 for a in active]}))
    c = pd.concat(cohorts, ignore_index=True)
    grp_all = home.map(lambda x: "IT" if x == config.TREATED else "CTRL")
    sums = cell_sums(c, ["period"], "left")
    is_it = (grp_all.reindex(sums.index) == "IT").to_numpy()
    point, lo, hi, means = did_stat(sums, is_it, rng, args.n_boot)
    rows.append({"outcome": "left_research", "did": point, "ci_low": lo, "ci_high": hi, **means,
                 "n_scientists": len(sums)})

    table = pd.DataFrame(rows)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    path = os.path.join(config.RESULTS_DIR, "long_run.csv")
    table.to_csv(path, index=False)
    print(table.round(4).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
