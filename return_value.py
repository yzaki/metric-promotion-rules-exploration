"""Does a return to a familiar neighbouring topic pay off? (Why fewer returns might matter.)

Outcome `lead` active years after each choice (papers, mean log normalised citations, share of top-10%
articles; as in outcomes_citations.py), regressed on the type of choice with staying as the baseline:
near-return, near-new, far-return, far-new ('new' = no article in the topic in the 6 previous years).
Scientist and year fixed effects, standard errors clustered by scientist. Estimated on scientists in
the control countries (all decision years) and, separately, on Italy before the reform, so the reform
itself does not enter. Descriptive: choices are not randomly assigned.

Usage:
    set CT_FIELD_ID=22 & python return_value.py
"""
import argparse
import os

import numpy as np
import pandas as pd

import build_trajectories as bt
import config
from first_entry import seen_before
from outcomes_citations import OUTCOMES, author_year_outcomes
from reduced_form import demean, ols_cluster

TYPES = ["near_return", "near_new", "far_return", "far_new"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lead", type=int, default=2)
    ap.add_argument("--lookback", type=int, default=6)
    args = ap.parse_args()
    out_dir = config.RESULTS_DIR + "_world"

    df = bt.load_raw()
    pot = bt.citation_potential_world(df)
    country = bt.assign_countries(df)
    ay = bt.author_years(df, country)
    ay = ay[ay.groupby("author_id").year.transform("size") >= config.MIN_ACTIVE_YEARS].reset_index(drop=True)
    ay = bt.add_state(ay, pot)
    ch = bt.make_choices(ay)
    nxt = ay.groupby("author_id").shift(-1)
    ok = nxt.year.notna() & ((nxt.year - ay.year) <= config.MAX_GAP)
    ch["next_topic"] = nxt.topic_id[ok].to_numpy()
    ch["next_year"] = nxt.year[ok].astype(int).to_numpy()
    ch = ch[ch.year.between(min(config.PRE_YEARS), max(config.POST_YEARS))].reset_index(drop=True)
    keys = pd.DataFrame({"author_id": ch.author_id, "topic_id": ch.next_topic, "year": ch.next_year})
    seen = seen_before(df, keys, args.lookback)
    ch["type"] = np.where(ch.action == "stay", "stay",
                          ch.action + np.where(seen, "_return", "_new"))

    out_ay = author_year_outcomes(df, set(ch.author_id)).sort_values(["author_id", "year"])
    del df
    out_ay["year0"] = out_ay.groupby("author_id").year.shift(args.lead)
    ch = ch.merge(out_ay.drop(columns="year").rename(columns={"year0": "year"}), on=["author_id", "year"], how="inner")

    rows = []
    for sample, mask in (("control countries, 2004-2018", ch.group == "CTRL"),
                         ("Italy before the reform", (ch.group == "IT") & ch.year.isin(config.PRE_YEARS))):
        s = ch[mask].dropna(subset=list(OUTCOMES)).reset_index(drop=True)
        author = pd.factorize(s.author_id)[0]
        groups = [author, s.year.to_numpy()]
        X = np.column_stack([(s.type == t).astype(float).to_numpy() for t in TYPES])
        Xd = demean(X, groups)
        for o in OUTCOMES:
            y = s[o].astype(float).to_numpy()
            b, se = ols_cluster(demean(y[:, None], groups)[:, 0], Xd, author)
            base = y[(s.type == "stay").to_numpy()].mean()
            for k, t in enumerate(TYPES):
                rows.append({"sample": sample, "outcome": o, "choice": t, "vs_stay": b[k],
                             "ci_low": b[k] - 1.96 * se[k], "ci_high": b[k] + 1.96 * se[k],
                             "stay_mean": base, "n_choices": len(s), "share_of_choices": (s.type == t).mean()})
    t = pd.DataFrame(rows)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"return_value_lead{args.lead}.csv")
    t.to_csv(path, index=False)
    print(t.round(4).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
