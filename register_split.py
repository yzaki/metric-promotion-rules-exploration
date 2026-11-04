"""Model-free nearby-move DiD for Italian scientists matched to the 2011 university staff register
(rank_2011_match.csv from rank_exposure.py) versus those not matched, each against France + Germany.
Unmatched scientists include research-institute staff (INFN, CNR, INAF), postdocs, students and
university staff whose names could not be matched uniquely.

Usage:
    python register_split.py --input data/trajectories_world_career.csv --out results_world_career
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from reduced_form import demean, ols_cluster


def lpm(sub):
    d = ((sub.group == "IT") & sub.year.isin(config.POST_YEARS)).astype(float).to_numpy()
    author = pd.factorize(sub.author_id)[0]
    fe = [author, sub.year.to_numpy()]
    y = (sub.action == "near").astype(float).to_numpy()
    b, se = ols_cluster(demean(y[:, None], fe)[:, 0], demean(d[:, None], fe), author)
    return 100 * b[0], 100 * se[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    df = pd.read_csv(args.input)
    df = df[df.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)
    matched = set(pd.read_csv(os.path.join(args.out, "rank_2011_match.csv")).iloc[:, 0])
    rows = []
    for label, keep in (("matched to register", df.author_id.isin(matched)),
                        ("not matched", ~df.author_id.isin(matched)), ("all Italian", True)):
        sub = df[(df.group == "CTRL") | ((df.group == "IT") & keep)].reset_index(drop=True)
        b, se = lpm(sub)
        rows.append({"italian_group": label, "lpm_near_pp": b, "ci_low": b - 1.96 * se, "ci_high": b + 1.96 * se,
                     "n_italian": int(sub.author_id[sub.group == "IT"].nunique())})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(args.out, "register_split.csv"), index=False)
    print(t.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
