"""Model-free check: linear-probability difference-in-differences on yearly choices.

    1[choice = c]_it = beta * Italy_i * After_t + scientist FE + year FE (+ state FE) + e_it

for c in {near, stay, far}, decision years 2004-09 (before) and 2013-18 (after). Fixed effects
are removed by alternating demeaning; standard errors are clustered by scientist. beta is in
probability units (x100 = percentage points). No inverse RL is involved.

Usage:
    python reduced_form.py --input data/trajectories_world.csv --out results_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config


def demean(M, groups, iters=50, tol=1e-10):
    M = M.copy()
    for _ in range(iters):
        before = M.copy()
        for g in groups:
            M -= pd.DataFrame(M).groupby(g).transform("mean").to_numpy()
        if np.max(np.abs(M - before)) < tol:
            break
    return M


def ols_cluster(y, X, cluster):
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    u = y - X @ b
    scores = pd.DataFrame(X * u[:, None]).groupby(cluster).sum().to_numpy()
    G = scores.shape[0]
    meat = scores.T @ scores * G / (G - 1)
    V = XtX_inv @ meat @ XtX_inv
    return b, np.sqrt(np.diag(V))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--out", default=config.RESULTS_DIR)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df = df[df.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)
    d = ((df.group == "IT") & df.year.isin(config.POST_YEARS)).astype(float).to_numpy()
    author = pd.factorize(df.author_id)[0]
    year = df.year.to_numpy()
    state = (df.s_tier * 9 + df.s_tenure * 3 + df.s_career).to_numpy()
    S = pd.get_dummies(state, drop_first=True).to_numpy(dtype=float)

    rows = []
    for spec, X0 in (("scientist + year FE", d[:, None]),
                     ("scientist + year + state FE", np.column_stack([d, S]))):
        Xd = demean(X0, [author, year])
        for choice in ("near", "stay", "far"):
            y = (df.action == choice).astype(float).to_numpy()
            yd = demean(y[:, None], [author, year])[:, 0]
            b, se = ols_cluster(yd, Xd, author)
            rows.append({"spec": spec, "choice": choice, "beta_pp": 100 * b[0],
                         "ci_low_pp": 100 * (b[0] - 1.96 * se[0]), "ci_high_pp": 100 * (b[0] + 1.96 * se[0]),
                         "n_choices": len(y), "n_scientists": author.max() + 1,
                         "baseline_IT_pre_pp": 100 * y[(df.group == "IT") & df.year.isin(config.PRE_YEARS)].mean()})
    t = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, f"reduced_form{('_' + args.tag) if args.tag else ''}.csv")
    t.to_csv(path, index=False)
    print(t.round(3).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
