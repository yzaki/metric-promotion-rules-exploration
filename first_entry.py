"""Are the forgone nearby moves first-time entries or returns to familiar topics?

Rebuilds the yearly choices exactly as build_trajectories.py (world citation measure) but keeps the
topic of the next active year, and flags whether the scientist had published any article in that topic
before. 'New' uses a fixed look-back (default 6 years before the next active year, so the window is
fully observed for every decision year from 2004), and 'new since 1998' uses all earlier years.
Each move is split into near-new, near-return, far-new and far-return, and each is analysed with the
model-free DiD (scientist + year FE, standard errors clustered by scientist).

Returns are further split by whether the destination topic was already in the scientist's work in the
decision year itself (the look-back window includes that year):
  concurrent return: an article in the destination topic in the decision year (a secondary topic became
                     the most frequent one; no work was taken up again)
  gap return:        no article in the destination topic in the decision year, at least one in the
                     earlier years of the window (an earlier line of work taken up again)
With --timing, the script also writes first_entry_timing.csv: a placebo reform in 2007 (2004-06 vs
2007-09) and an annual event study (reference 2009) with a joint test of the pre-2009 coefficients.

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
    ap.add_argument("--timing", action="store_true", help="placebo 2007 and annual event study (first_entry_timing.csv)")
    ap.add_argument("--controls", nargs="+", default=None, help="control countries instead of FR DE, e.g. ES NL PT")
    ap.add_argument("--stable-only", action="store_true",
                    help="keep only articles also in the field on 5 Nov 2026 (<raw dir>_ITFRDE_5nov), i.e. whose "
                         "field assignment did not change in the OpenAlex reclassification")
    args = ap.parse_args()
    if args.controls:
        config.CONTROLS = args.controls
    if args.treated or args.controls:
        config.TREATED = args.treated or config.TREATED
        config.COUNTRIES = [config.TREATED] + config.CONTROLS
    out_dir = args.out or config.RESULTS_DIR + "_world"

    df = bt.load_raw()
    if args.stable_only:
        import glob as _g
        old = set()
        for f in _g.glob(config.RAW_DIR.rstrip("/") + "_ITFRDE_5nov/works_*.csv.gz"):
            old |= set(pd.read_csv(f, usecols=["work_id"]).work_id)
        n0 = df.work_id.nunique()
        df = df[df.work_id.isin(old)].reset_index(drop=True)
        print(f"Stable articles only: {df.work_id.nunique():,} of {n0:,}")
    # citation tiers do not enter the model-free move types; use world-wide rates when available
    import glob
    world = glob.glob(os.path.join(config.DATA_DIR, "world", "cites_*.csv.gz"))
    pot = bt.citation_potential_world(df) if world else bt.citation_potential(df)
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
    ch = ch[ch.year.between(min(config.PRE_YEARS), max(config.POST_YEARS))].reset_index(drop=True)

    keys = pd.DataFrame({"author_id": ch.author_id, "topic_id": ch.next_topic, "year": ch.next_year})
    ch["seen_window"] = seen_before(df, keys, args.lookback)
    ch["seen_ever"] = seen_before(df, keys, None)
    pres = df[["author_id", "topic_id", "year"]].drop_duplicates().assign(cur=True)
    ch["in_decision_year"] = ch[["author_id", "next_topic", "year"]].rename(columns={"next_topic": "topic_id"}).merge(
        pres, on=["author_id", "topic_id", "year"], how="left").cur.fillna(False).to_numpy(dtype=bool)
    timing_ch = ch.copy()
    ch = ch[ch.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)
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
            "move": ch.action != "stay", "far": ch.action == "far",
            "any_return": (ch.action != "stay") & ch[flag],
            "near_new": (ch.action == "near") & ~ch[flag], "near_return": (ch.action == "near") & ch[flag],
            "far_new": (ch.action == "far") & ~ch[flag], "far_return": (ch.action == "far") & ch[flag],
        }
        if flag == "seen_window":
            outcomes["near_concurrent_return"] = (ch.action == "near") & ch.in_decision_year
            outcomes["near_gap_return"] = (ch.action == "near") & ch[flag] & ~ch.in_decision_year
        for name, y in outcomes.items():
            if name in ("near", "move", "far") and label == "since 1998":
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
    if args.timing:
        timing(timing_ch, out_dir)


def timing(ch, out_dir):
    """Placebo 2007 and annual event study for nearby moves, returns and gap returns."""
    from scipy import stats
    it = (ch.group == "IT").to_numpy()
    yr = ch.year.to_numpy()
    outs = {"near": ch.action == "near", "move": ch.action != "stay", "far": ch.action == "far",
            "any_return": (ch.action != "stay") & ch.seen_window,
            "near_return": (ch.action == "near") & ch.seen_window,
            "near_gap_return": (ch.action == "near") & ch.seen_window & ~ch.in_decision_year,
            "near_new": (ch.action == "near") & ~ch.seen_window}
    rows = []
    for name, y in outs.items():
        m = np.isin(yr, [2004, 2005, 2006, 2007, 2008, 2009])
        a = pd.factorize(ch.author_id[m])[0]
        g = [a, yr[m]]
        d = (it[m] & (yr[m] >= 2007)).astype(float)
        Xd = demean(d[:, None], g)
        yd = demean(y[m].astype(float).to_numpy()[:, None], g)[:, 0]
        b, se = ols_cluster(yd, Xd, a)
        years = [v for v in range(2004, 2019) if v != 2009]
        a2 = pd.factorize(ch.author_id)[0]
        g2 = [a2, yr]
        X = np.column_stack([(it & (yr == v)).astype(float) for v in years])
        Xd2 = demean(X, g2)
        yd2 = demean(y.astype(float).to_numpy()[:, None], g2)[:, 0]
        XtX = np.linalg.inv(Xd2.T @ Xd2)
        bb = XtX @ Xd2.T @ yd2
        u = yd2 - Xd2 @ bb
        sc = pd.DataFrame(Xd2 * u[:, None]).groupby(a2).sum().to_numpy()
        G = sc.shape[0]
        V = XtX @ (sc.T @ sc * G / (G - 1)) @ XtX
        pre = [k for k, v in enumerate(years) if v < 2009]
        p = 1 - stats.chi2.cdf(bb[pre] @ np.linalg.inv(V[np.ix_(pre, pre)]) @ bb[pre], len(pre))
        row = {"outcome": name, "placebo2007_pp": 100 * b[0], "placebo_ci_low_pp": 100 * (b[0] - 1.96 * se[0]),
               "placebo_ci_high_pp": 100 * (b[0] + 1.96 * se[0]), "pretrend_wald_p": p}
        row.update({f"es_{v}": 100 * bb[k] for k, v in enumerate(years)})
        row.update({f"se_{v}": 100 * np.sqrt(V[k, k]) for k, v in enumerate(years)})
        rows.append(row)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(out_dir, "first_entry_timing.csv"), index=False)
    print(t[["outcome", "placebo2007_pp", "placebo_ci_low_pp", "placebo_ci_high_pp", "pretrend_wald_p"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
