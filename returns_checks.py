"""Robustness of the decline in returns (model-free DiD, Italy vs France + Germany, 2004-09 vs 2013-18).

  gap >= 1/2/3: return to a topic with no article in it in the decision year (gap >= 1), nor in the
                year before (gap >= 2), nor two years before (gap >= 3); at least one article earlier
                in the 6-year window before the next active year
  output FE:    gap return (>= 1) with fixed effects for articles in t x articles in t+1 (bins 1, 2, 3,
                4-5, 6-9, 10+), so that more articles cannot mechanically stabilise the yearly topic
  random paper: each scientist-year's topic is one randomly drawn article instead of the most frequent
                topic (5 draws), and returns are reclassified (presence still uses all articles)
Usage: CT_FIELD_ID=22 python returns_checks.py
"""
import os

import numpy as np
import pandas as pd

import build_trajectories as bt
import config
from reduced_form import demean, ols_cluster

BINS = [0, 1, 2, 3, 5, 9, np.inf]


def did(ch, y, extra=()):
    d = ((ch.group == "IT") & ch.year.isin(config.POST_YEARS)).astype(float).to_numpy()
    a = pd.factorize(ch.author_id)[0]
    g = [a, ch.year.to_numpy()] + [pd.factorize(ch[c])[0] for c in extra]
    Xd = demean(d[:, None], g)
    yd = demean(y.astype(float).to_numpy()[:, None], g)[:, 0]
    b, se = ols_cluster(yd, Xd, a)
    return 100 * b[0], 100 * (b[0] - 1.96 * se[0]), 100 * (b[0] + 1.96 * se[0])


def choices(ay):
    nxt = ay.groupby("author_id").shift(-1)
    ok = nxt.year.notna() & ((nxt.year - ay.year) <= config.MAX_GAP)
    ch = ay[ok].copy()
    ch["ny"], ch["nt"], ch["ns"] = nxt.year[ok].astype(int), nxt.topic_id[ok], nxt.subfield_id[ok]
    ch["group"] = np.where(ch.country == config.TREATED, "IT", "CTRL")
    ch["near"] = (ch.nt != ch.topic_id) & (ch.ns == ch.subfield_id)
    return ch[ch.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)


def gap_flags(ch, pres):
    has = lambda yy: np.array([(a, t, y) in pres for a, t, y in zip(ch.author_id, ch.nt, yy)])
    in_t, in_t1, in_t2 = has(ch.year), has(ch.year - 1), has(ch.year - 2)
    window = np.zeros(len(ch), bool)
    for lag in range(1, 7):
        yy = ch.ny - lag
        window |= has(yy) & (yy != ch.year)
    any_window = window | in_t
    return {"gap>=1": ch.near & ~in_t & window,
            "gap>=2": ch.near & ~in_t & ~in_t1 & window & has_before(ch, pres, 2),
            "gap>=3": ch.near & ~in_t & ~in_t1 & ~in_t2 & window & has_before(ch, pres, 3),
            "all returns": ch.near & any_window}


def has_before(ch, pres, k):
    """An article in the destination topic at least k years before the decision year, within the window."""
    out = np.zeros(len(ch), bool)
    for lag in range(1, 7):
        yy = ch.ny - lag
        ok = (ch.year - yy) >= k
        out |= np.array([(a, t, y) in pres for a, t, y in zip(ch.author_id, ch.nt, yy)]) & ok.to_numpy()
    return out


def main():
    df = bt.load_raw()
    country = bt.assign_countries(df)
    ay = bt.author_years(df, country)
    ay = ay[ay.groupby("author_id").year.transform("size") >= config.MIN_ACTIVE_YEARS].reset_index(drop=True)
    keep = set(ay.author_id)
    d = df[df.author_id.isin(keep)]
    pres = set(zip(d.author_id, d.topic_id, d.year))
    rows = []
    ch = choices(ay)
    for k, y in gap_flags(ch, pres).items():
        rows.append(("most frequent topic", k, *did(ch, y)))
    n = d.groupby(["author_id", "year"]).work_id.nunique()
    ch["n_t"] = [n.get((a, y), 1) for a, y in zip(ch.author_id, ch.year)]
    ch["n_t1"] = [n.get((a, y), 1) for a, y in zip(ch.author_id, ch.ny)]
    ch["bins"] = pd.cut(ch.n_t, BINS, labels=False) * 10 + pd.cut(ch.n_t1, BINS, labels=False)
    g1 = gap_flags(ch, pres)["gap>=1"]
    rows.append(("most frequent topic, FE articles t x t+1", "gap>=1", *did(ch, g1, ("bins",))))
    rows.append(("most frequent topic, FE articles t x t+1", "all returns", *did(ch, gap_flags(ch, pres)["all returns"], ("bins",))))
    for s in range(1, 6):
        r = (d.sample(frac=1.0, random_state=s).drop_duplicates(["author_id", "year"])
             [["author_id", "year", "topic_id", "subfield_id"]].merge(ay[["author_id", "year", "country"]], on=["author_id", "year"]))
        r = r.sort_values(["author_id", "year"]).reset_index(drop=True)
        chr_ = choices(r)
        f = gap_flags(chr_, pres)
        rows.append((f"one random article per year, draw {s}", "gap>=1", *did(chr_, f["gap>=1"])))
        rows.append((f"one random article per year, draw {s}", "all returns", *did(chr_, f["all returns"])))
    t = pd.DataFrame(rows, columns=["definition", "outcome", "beta_pp", "ci_low_pp", "ci_high_pp"])
    out = config.RESULTS_DIR + "_world"
    t.to_csv(os.path.join(out, "returns_checks.csv"), index=False)
    print(t.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
