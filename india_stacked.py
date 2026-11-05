"""India (UGC Regulations 2010) vs France + Germany: model-free tests stacked over four fields.

Plan: ../PREREGISTRATION_india_2026-11-05.md.
    I1  nearby move, after (2013-18) vs before (2004-09)
    I2  placebo: 2007-09 vs 2004-06
    I3  nearby returns and first entries (choice files from first_entry.py --save-choices)
    I4  (with --groups) UGC-covered minus not covered, nearby move
Field-specific scientist and year fixed effects; standard errors clustered by scientist across fields.
Also reported per field. The treated country is labelled IT in the trajectory files.

Usage:
    python india_stacked.py --out results_india
    python india_stacked.py --out results_india --groups results_india/india_groups.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

from reduced_form import demean

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = {"Physics": "data", "Engineering": "data_field22", "Biochemistry": "data_field13", "Chemistry": "data_field16"}
PRE, POST = list(range(2004, 2010)), list(range(2013, 2019))


def fit(s, ycol, dcols):
    sid = pd.factorize(s.author_id + "|" + s.field)[0]
    yid = pd.factorize(s.year.astype(str) + "|" + s.field)[0]
    X = s[dcols].to_numpy(dtype=float)
    y = s[ycol].to_numpy(dtype=float)
    Xd, yd = demean(X, [sid, yid]), demean(y[:, None], [sid, yid])[:, 0]
    XtX_inv = np.linalg.inv(Xd.T @ Xd)
    b = XtX_inv @ Xd.T @ yd
    u = yd - Xd @ b
    sc = pd.DataFrame(Xd * u[:, None]).groupby(pd.factorize(s.author_id)[0]).sum().to_numpy()
    G = sc.shape[0]
    return b, XtX_inv @ (sc.T @ sc * G / (G - 1)) @ XtX_inv


def row(label, scope, b, se, n):
    return {"test": label, "scope": scope, "beta_pp": 100 * b, "ci_low_pp": 100 * (b - 1.96 * se),
            "ci_high_pp": 100 * (b + 1.96 * se), "n_treated": n}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(HERE, "results_india"))
    ap.add_argument("--groups", default=None, help="csv author_id,group for I4")
    ap.add_argument("--suffix", default="IN", help="treated country of the trajectory files (IN, RU)")
    ap.add_argument("--covered-label", default="UGC-covered", help="group label of scientists covered by the policy")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    traj, choices = [], []
    for f, d in FIELDS.items():
        t = pd.read_csv(os.path.join(HERE, d, f"trajectories_world_{args.suffix}.csv"), usecols=["author_id", "group", "year", "action"])
        traj.append(t.assign(field=f))
        cf = os.path.join(args.out, f"choices_{d}.csv.gz")
        if os.path.exists(cf):
            choices.append(pd.read_csv(cf).assign(field=f))
    T = pd.concat(traj, ignore_index=True)
    T["near"] = (T.action == "near").astype(float)
    rows = []
    for label, pre, post in (("I1 nearby move", PRE, POST), ("I2 placebo 2007", list(range(2004, 2007)), list(range(2007, 2010)))):
        for scope in ["All four fields"] + list(FIELDS):
            s = T[T.year.isin(pre + post)] if scope == "All four fields" else T[(T.field == scope) & T.year.isin(pre + post)]
            s = s.assign(d=((s.group == "IT") & s.year.isin(post)).astype(float)).reset_index(drop=True)
            b, V = fit(s, "near", ["d"])
            rows.append(row(label, scope, b[0], np.sqrt(V[0, 0]), s.author_id[s.group == "IT"].nunique()))
    if choices:
        C = pd.concat(choices, ignore_index=True)
        C = C[C.year.isin(PRE + POST)].reset_index(drop=True)
        C["d"] = ((C.group == "IT") & C.year.isin(POST)).astype(float)
        C["near_return"] = ((C.action == "near") & C.seen_window).astype(float)
        C["near_new"] = ((C.action == "near") & ~C.seen_window).astype(float)
        for oc in ("near_return", "near_new"):
            for scope in ["All four fields"] + list(FIELDS):
                s = C if scope == "All four fields" else C[C.field == scope]
                s = s.reset_index(drop=True)
                if s.empty:
                    continue
                b, V = fit(s, oc, ["d"])
                rows.append(row(f"I3 {oc.replace('_', ' ')}", scope, b[0], np.sqrt(V[0, 0]), s.author_id[s.group == "IT"].nunique()))
    if args.groups:
        g = pd.read_csv(args.groups).set_index("author_id").group
        s = T[T.year.isin(PRE + POST)].copy()
        s["g"] = s.author_id.map(g)
        s = s[(s.group == "CTRL") | s.g.notna()].reset_index(drop=True)
        post = s.year.isin(POST)
        cov = args.covered_label
        s["d_ugc"] = ((s.g == cov) & post).astype(float)
        s["d_not"] = ((s.g == "not covered") & post).astype(float)
        b, V = fit(s, "near", ["d_ugc", "d_not"])
        c = np.array([1.0, -1.0])
        for k, lab in enumerate((cov, "not covered")):
            rows.append(row(f"I4 nearby move, {lab}", "All four fields", b[k], np.sqrt(V[k, k]), int((s.g == lab).groupby(s.author_id).any().sum())))
        rows.append(row(f"I4 {cov} minus not covered", "All four fields", c @ b, np.sqrt(c @ V @ c), np.nan))
    t = pd.DataFrame(rows)
    name = "india" if args.suffix == "IN" else {"RU": "russia"}.get(args.suffix, args.suffix.lower())
    t.to_csv(os.path.join(args.out, f"{name}_stacked.csv"), index=False)
    print(t.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
