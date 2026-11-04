"""Second test: did behaviour partly recover when the thresholds were relaxed in 2016?

Compares 2013-15 (first habilitation rules) with 2016-18 (second round, relaxed thresholds),
Italy vs control. If the rules drove the change, the nearby-move weight (and the probability
of a nearby move) should rise again for Italy relative to control: a positive difference.
Reports the inverse-RL difference-in-differences (bootstrap) and the model-free linear
probability version (scientist and year fixed effects, clustered by scientist).

Usage:
    python relax_2016.py --input data/trajectories_world.csv --out results_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from estimate import Panel, run_did, summarise
from reduced_form import demean, ols_cluster

EARLY, LATE = [2013, 2014, 2015], [2016, 2017, 2018]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--out", default=config.RESULTS_DIR)
    ap.add_argument("--n-boot", type=int, default=200)
    args = ap.parse_args()
    rng = np.random.default_rng(config.SEED)
    df = pd.read_csv(args.input)

    _, est, draws = run_did(Panel(df), EARLY, LATE, config.GAMMA, args.n_boot, rng, label="2016")
    irl_t = summarise(est, draws).assign(method="inverse RL (weight)")

    d = df[df.year.isin(EARLY + LATE)].reset_index(drop=True)
    treat = ((d.group == "IT") & d.year.isin(LATE)).astype(float).to_numpy()[:, None]
    author, year = pd.factorize(d.author_id)[0], d.year.to_numpy()
    Xd = demean(treat, [author, year])
    rows = []
    for choice in ("near", "stay", "far"):
        y = (d.action == choice).astype(float).to_numpy()[:, None]
        b, se = ols_cluster(demean(y, [author, year])[:, 0], Xd, author)
        rows.append({"parameter": f"P({choice}) pp", "did": 100 * b[0],
                     "ci_low": 100 * (b[0] - 1.96 * se[0]), "ci_high": 100 * (b[0] + 1.96 * se[0])})
    lpm_t = pd.DataFrame(rows).assign(method="linear probability (pp)")
    t = pd.concat([irl_t, lpm_t], ignore_index=True)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "relax_2016.csv")
    t.to_csv(path, index=False)
    print(t[["method", "parameter", "did", "ci_low", "ci_high"]].round(3).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
