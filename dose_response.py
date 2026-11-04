"""Dose-response: does the reform effect depend on distance to the habilitation thresholds?

The 2012 habilitation in bibliometric sectors required candidates to exceed the median of
their sector on at least two of three indicators computed over the previous ten years
(article count, citations, h-index). Sector membership is not observed in OpenAlex, so each
scientist is placed relative to the medians of comparable scientists in their own country
(same field and career stage as of 2011), using articles published 2002-2011:
    n_above = number of the three indicators above the reference-group median (0-3)
    0 = well below, 1 = one indicator short (just below), 2 = just cleared, 3 = well above
Citations are counted as of the download date (not 2012), so the citation and h-index
indicators rank scientists only approximately.

The reform effect on each weight is then estimated separately for each group (choices
restricted to the group; transitions from the full group), as for career stages.
Prediction if the thresholds drove the behaviour: largest effect near the bar (1 and 2).

Usage:
    python dose_response.py --input data/trajectories_world.csv --out results_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from build_trajectories import load_raw
from estimate import Panel, run_did, summarise

LABELS = {0: "0 of 3 (well below)", 1: "1 of 3 (just below)", 2: "2 of 3 (just cleared)", 3: "3 of 3 (well above)"}


def h_index(c):
    c = np.sort(np.asarray(c))[::-1]
    return int((c >= np.arange(1, len(c) + 1)).sum())


def threshold_groups(authors, country):
    df = load_raw()
    df = df[df.author_id.isin(authors) & df.year.between(2002, 2011)]
    first = load_raw_first_year(authors)
    per = (df.drop_duplicates(["author_id", "work_id"]).groupby("author_id")
           .agg(articles=("work_id", "size"), citations=("cited_by_count", "sum"),
                h=("cited_by_count", h_index)))
    per["country"] = per.index.map(country)
    age = 2011 - per.index.map(first)
    per["stage"] = np.select([age <= 5, age <= 15], [0, 1], 2)
    med = per.groupby(["country", "stage"])[["articles", "citations", "h"]].transform("median")
    per["n_above"] = (per[["articles", "citations", "h"]] > med).sum(axis=1)
    return per


def load_raw_first_year(authors):
    df = load_raw()
    return df[df.author_id.isin(authors)].groupby("author_id").year.min()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--out", default=config.RESULTS_DIR)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    rng = np.random.default_rng(config.SEED)

    traj = pd.read_csv(args.input)
    country = traj.drop_duplicates("author_id").set_index("author_id").country
    pre_authors = set(traj.author_id[traj.year.isin(config.PRE_YEARS)])
    per = threshold_groups(pre_authors, country)
    print("Scientists per group (pre-reform active):\n",
          per.groupby(["country", "n_above"]).size().unstack().to_string())

    panel = Panel(traj)
    grp = panel.df.author_id.map(per.n_above).to_numpy()
    rows = []
    for k in range(4):
        mask = grp == k
        print(f"\n{LABELS[k]}: {mask.sum():,} choices")
        _, est, draws = run_did(panel, config.PRE_YEARS, config.POST_YEARS, config.GAMMA, args.n_boot, rng,
                                choice_mask=mask, label=LABELS[k])
        t = summarise(est, draws)
        t.insert(0, "group", LABELS[k])
        t.insert(1, "n_above", k)
        rows.append(t)
    out = pd.concat(rows)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "dose_response.csv")
    out.to_csv(path, index=False)
    print("\n", out[out.parameter == "theta_near"].round(3).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
