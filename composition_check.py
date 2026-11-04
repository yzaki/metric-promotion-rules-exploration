"""Why the model-free and model-based estimates can differ: within-scientist change vs sample composition.

Linear-probability DiD on P(near) under increasingly strict comparisons:
    raw shares; year FE; year + state FE; scientist + year FE;
and the same on the balanced panel (scientists with choices both before and after).
The scientist-FE estimate uses only within-scientist change, so it ignores differences between
scientists who enter or leave the sample across periods. Standard errors clustered by scientist.

Usage:
    python composition_check.py --input data_field13/trajectories_world.csv --out results_field13_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from reduced_form import demean, ols_cluster


def lpm(df, fes, with_state):
    d = ((df.group == "IT") & df.year.isin(config.POST_YEARS)).astype(float).to_numpy()
    author = pd.factorize(df.author_id)[0]
    groups = [df.year.to_numpy()]
    if "scientist" in fes:
        groups = [author] + groups
    else:   # without scientist FE, keep the Italy and after main effects (after is absorbed by year FE)
        d = np.column_stack([d, (df.group == "IT").astype(float).to_numpy()])
    X0 = d if d.ndim == 2 else d[:, None]
    if with_state:
        state = (df.s_tier * 9 + df.s_tenure * 3 + df.s_career).to_numpy()
        X0 = np.column_stack([X0, pd.get_dummies(state, drop_first=True).to_numpy(dtype=float)])
    Xd = demean(X0, groups)
    y = (df.action == "near").astype(float).to_numpy()
    yd = demean(y[:, None], groups)[:, 0]
    b, se = ols_cluster(yd, Xd, author)
    return 100 * b[0], 100 * se[0]


def raw_did(df):
    is_it = df.group == "IT"
    post = df.year.isin(config.POST_YEARS)
    near = df.action == "near"
    m = lambda mask: near[mask].mean()
    return 100 * ((m(is_it & post) - m(is_it & ~post)) - (m(~is_it & post) - m(~is_it & ~post)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df = df[df.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)
    pre_ids = set(df.author_id[df.year.isin(config.PRE_YEARS)])
    post_ids = set(df.author_id[df.year.isin(config.POST_YEARS)])
    samples = {"all": df, "balanced": df[df.author_id.isin(pre_ids & post_ids)].reset_index(drop=True)}

    rows = []
    for sname, s in samples.items():
        rows.append({"sample": sname, "spec": "raw shares", "beta_pp": raw_did(s), "se_pp": np.nan})
        for spec, fes, st in (("year FE", ("year",), False), ("year + state FE", ("year",), True),
                              ("scientist + year FE", ("scientist", "year"), False),
                              ("scientist + year + state FE", ("scientist", "year"), True)):
            b, se = lpm(s, fes, st)
            rows.append({"sample": sname, "spec": spec, "beta_pp": b, "se_pp": se})
        for r in rows[-5:]:
            r.update(n_choices=len(s), n_scientists=s.author_id.nunique(),
                     n_it=s.author_id[s.group == "IT"].nunique())
    t = pd.DataFrame(rows)
    t["ci_low_pp"] = t.beta_pp - 1.96 * t.se_pp
    t["ci_high_pp"] = t.beta_pp + 1.96 * t.se_pp
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "composition_check.csv")
    t.to_csv(path, index=False)
    print(t.round(2).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
