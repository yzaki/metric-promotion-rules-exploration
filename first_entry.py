"""Are the forgone nearby moves first-time entries or returns to familiar topics?

Rebuilds the yearly choices exactly as build_trajectories.py (world citation measure) but keeps the
topic of the next active year, and flags whether the scientist had published any article in that topic
before. 'New' uses a fixed look-back (default 6 years before the next active year, so the window is
fully observed for every decision year from 2004), and 'new since 1998' uses all earlier years.
Each move is split into near-new, near-return, far-new and far-return, and each is analysed with the
model-free DiD (scientist + year FE, standard errors clustered by scientist).

Usage:
    set CT_FIELD_ID=13 & python first_entry.py
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import build_trajectories as bt
from composition_check import raw_did
from reduced_form import demean, ols_cluster


def seen_before(df, keys, lookback):
    """For each (author_id, topic_id, year) in keys: any article by the author in that topic in the
    `lookback` years before `year` (all earlier years if lookback is None)."""
    pres = df[["author_id", "topic_id", "year"]].drop_duplicates()
    if lookback is None:
        first = pres.groupby(["author_id", "topic_id"]).year.min().rename("first").reset_index()
        k = keys.merge(first, on=["author_id", "topic_id"], how="left")
        return (k["first"] < k["year"]).to_numpy()
    hit = np.zeros(len(keys), dtype=bool)
    for lag in range(1, lookback + 1):
        p = pres.assign(year=pres.year + lag, hit=True)
        k = keys.merge(p, on=["author_id", "topic_id", "year"], how="left")
        hit |= k.hit.fillna(False).to_numpy(dtype=bool)
    return hit


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lookback", type=int, default=6)
    ap.add_argument("--out", default=None)
    ap.add_argument("--treated", default=None, help="treated country instead of Italy (labelled IT), e.g. IN")
    ap.add_argument("--save-choices", default=None, help="write choice-level move types to this .csv.gz")
    args = ap.parse_args()
    if args.treated:
        config.TREATED = args.treated
        config.COUNTRIES = [config.TREATED] + config.CONTROLS
    out_dir = args.out or config.RESULTS_DIR + "_world"

    df = bt.load_raw()
    pot = bt.citation_potential_world(df)
    country = bt.assign_countries(df)
    ay = bt.author_years(df, country)
    ay = ay[ay.groupby("author_id").year.transform("size") >= config.MIN_ACTIVE_YEARS].reset_index(drop=True)
    ay = bt.add_state(ay, pot)
    ch = bt.make_choices(ay)
    # same rows as make_choices, keeping the next topic
    nxt = ay.groupby("author_id").shift(-1)
    ok = nxt.year.notna() & ((nxt.year - ay.year) <= config.MAX_GAP)
    ch["next_topic"] = nxt.topic_id[ok].to_numpy()
    ch["next_year"] = nxt.year[ok].astype(int).to_numpy()
    ch = ch[ch.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)

    keys = pd.DataFrame({"author_id": ch.author_id, "topic_id": ch.next_topic, "year": ch.next_year})
    ch["seen_window"] = seen_before(df, keys, args.lookback)
    ch["seen_ever"] = seen_before(df, keys, None)
    del df
    if args.save_choices:
        ch[["author_id", "group", "year", "action", "seen_window", "seen_ever"]].to_csv(args.save_choices, index=False)

    d = ((ch.group == "IT") & ch.year.isin(config.POST_YEARS)).astype(float).to_numpy()
    author = pd.factorize(ch.author_id)[0]
    groups = [author, ch.year.to_numpy()]
    Xd = demean(d[:, None], groups)
    is_it, post = (ch.group == "IT"), ch.year.isin(config.POST_YEARS)
    rows = []
    for flag, label in (("seen_window", f"{args.lookback}-year look-back"), ("seen_ever", "since 1998")):
        outcomes = {
            "near": ch.action == "near",
            "near_new": (ch.action == "near") & ~ch[flag], "near_return": (ch.action == "near") & ch[flag],
            "far_new": (ch.action == "far") & ~ch[flag], "far_return": (ch.action == "far") & ch[flag],
        }
        for name, y in outcomes.items():
            if name == "near" and label == "since 1998":
                continue
            yv = y.astype(float).to_numpy()
            yd = demean(yv[:, None], groups)[:, 0]
            b, se = ols_cluster(yd, Xd, author)
            rows.append({"definition": label, "outcome": name, "beta_pp": 100 * b[0],
                         "ci_low_pp": 100 * (b[0] - 1.96 * se[0]), "ci_high_pp": 100 * (b[0] + 1.96 * se[0]),
                         "raw_did_pp": raw_did(ch.assign(action=np.where(y, "near", "x"))),
                         "IT_before_pct": 100 * yv[is_it & ~post].mean(), "IT_after_pct": 100 * yv[is_it & post].mean(),
                         "CTRL_before_pct": 100 * yv[~is_it & ~post].mean(), "CTRL_after_pct": 100 * yv[~is_it & post].mean()})
    t = pd.DataFrame(rows)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "first_entry.csv")
    t.to_csv(path, index=False)
    print(t.round(2).to_string(index=False))
    print(f"\nChoices {len(ch):,}; saved {path}")


if __name__ == "__main__":
    main()
