"""Hard versus soft metric-based promotion rules: a stacked model-free difference-in-differences.

Each case is a treated country with its own before and after years, compared with France + Germany:
    hard (fixed numerical thresholds): Italy 2012 (2004-09 vs 2013-18), Romania 2012 (2004-09 vs 2013-18),
                                       Spain 2015/16 (2010-13 vs 2016-18)
    soft (indicators judged by committees, no fixed bars): Poland 2011 (2004-09 vs 2013-18),
                                       Spain 2008 (2004-07 vs 2010-13)
Cases are stacked with case-specific scientist and year fixed effects and a separate treatment indicator
per case; standard errors are clustered by scientist across stacks (control scientists appear in several
cases). Reported: each case, hard cases outside Italy (mean of Spain 2015 and Romania), all hard, soft, and
hard outside Italy minus soft. Optionally pooled over fields (field-specific fixed effects).

Usage:
    python stacked_rules.py --out results_stacked_rules
"""
import argparse
import os

import numpy as np
import pandas as pd

from reduced_form import demean

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = {"Physics": "data", "Engineering": "data_field22", "Biochemistry": "data_field13"}
Y = lambda a, b: list(range(a, b + 1))
CASES = [  # name, kind, file suffix, treated country, pre, post
    ("Italy 2012", "hard", "world", "IT", Y(2004, 2009), Y(2013, 2018)),
    ("Romania 2012", "hard", "world_RO", "RO", Y(2004, 2009), Y(2013, 2018)),
    ("Spain 2015", "hard", "world_ctrl_FR_DE_ES_NL_PT", "ES", Y(2010, 2013), Y(2016, 2018)),
    ("Poland 2011", "soft", "world_PL", "PL", Y(2004, 2009), Y(2013, 2018)),
    ("Spain 2008", "soft", "world_ctrl_FR_DE_ES_NL_PT", "ES", Y(2004, 2007), Y(2010, 2013)),
]
NAMES = [c[0] for c in CASES]
COMBOS = {"Hard outside Italy (mean of Spain 2015, Romania)": {"Romania 2012": .5, "Spain 2015": .5},
          "All hard (mean of three)": {"Italy 2012": 1 / 3, "Romania 2012": 1 / 3, "Spain 2015": 1 / 3},
          "Soft (mean of Poland, Spain 2008)": {"Poland 2011": .5, "Spain 2008": .5},
          "Hard outside Italy minus soft": {"Romania 2012": .5, "Spain 2015": .5, "Poland 2011": -.5, "Spain 2008": -.5}}


def stack(fields):
    parts = []
    for field in fields:
        for name, kind, suf, cc, pre, post in CASES:
            d = pd.read_csv(os.path.join(HERE, FIELDS[field], f"trajectories_{suf}.csv"),
                            usecols=["author_id", "country", "year", "action"])
            d = d[d.country.isin([cc, "FR", "DE"]) & d.year.isin(pre + post)].copy()
            d["case"], d["field"] = name, field
            d["treat"] = ((d.country == cc) & d.year.isin(post)).astype(float)
            parts.append(d)
    return pd.concat(parts, ignore_index=True)


def estimate(s):
    sid = pd.factorize(s.author_id + "|" + s.case + "|" + s.field)[0]
    yid = pd.factorize(s.year.astype(str) + "|" + s.case + "|" + s.field)[0]
    X = np.column_stack([(s.treat * (s.case == n)).to_numpy() for n in NAMES])
    y = (s.action == "near").astype(float).to_numpy()
    Xd, yd = demean(X, [sid, yid]), demean(y[:, None], [sid, yid])[:, 0]
    XtX_inv = np.linalg.inv(Xd.T @ Xd)
    b = XtX_inv @ Xd.T @ yd
    u = yd - Xd @ b
    cl = pd.factorize(s.author_id)[0]   # cluster on the scientist across stacks
    scores = pd.DataFrame(Xd * u[:, None]).groupby(cl).sum().to_numpy()
    G = scores.shape[0]
    V = XtX_inv @ (scores.T @ scores * G / (G - 1)) @ XtX_inv
    rows = []
    for k, n in enumerate(NAMES):
        rows.append({"estimate": n, "beta_pp": 100 * b[k], "se_pp": 100 * np.sqrt(V[k, k]),
                     "n_treated": int(s.author_id[(s.case == n) & ~s.country.isin(["FR", "DE"])].nunique())})
    for label, w in COMBOS.items():
        c = np.array([w.get(n, 0) for n in NAMES])
        rows.append({"estimate": label, "beta_pp": 100 * c @ b, "se_pp": 100 * np.sqrt(c @ V @ c), "n_treated": np.nan})
    t = pd.DataFrame(rows)
    t["ci_low_pp"], t["ci_high_pp"] = t.beta_pp - 1.96 * t.se_pp, t.beta_pp + 1.96 * t.se_pp
    return t


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(HERE, "results_stacked_rules"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    out = []
    for scope in list(FIELDS) + ["All three fields"]:
        fields = list(FIELDS) if scope == "All three fields" else [scope]
        t = estimate(stack(fields))
        t.insert(0, "scope", scope)
        out.append(t)
        print(t.round(2).to_string(index=False), flush=True)
    pd.concat(out).to_csv(os.path.join(args.out, "stacked_rules.csv"), index=False)


if __name__ == "__main__":
    main()
