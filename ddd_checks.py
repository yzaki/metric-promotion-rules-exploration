"""Checks on the career-stage triple difference (mid-career 6-15 y minus senior 16+ y), Italy vs control.

    python ddd_checks.py --input data/trajectories_world.csv --out results_world_placebo_space --placebo-year 2007
    python ddd_checks.py --input data_field20/trajectories.csv --out results_field20_ddd      # economics

With --placebo-year the comparison is 2004..(year-1) vs year..2009, inside the pre-reform period.
Scientist bootstrap, the same resample for both career stages.
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel, fit_groups, did

NEAR = irl.PARAMS.index("theta_near")


def ddd(panel, pre, post, weights=None):
    r = {k: did(fit_groups(panel, pre, post, config.GAMMA, weights=weights,
                           choice_mask=(panel.career == k)))[NEAR] for k in (1, 2)}
    return {"mid": r[1], "senior": r[2], "ddd": r[1] - r[2]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--placebo-year", type=int, default=None)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    if args.placebo_year:
        pre = [y for y in config.PRE_YEARS if y < args.placebo_year]
        post = [y for y in config.PRE_YEARS if y >= args.placebo_year]
        tag = f"placebo_{args.placebo_year}"
    else:
        pre, post, tag = config.PRE_YEARS, config.POST_YEARS, "main"

    df = pd.read_csv(args.input)
    df = df[df.year.isin(pre + post)].reset_index(drop=True)
    panel = Panel(df)
    point = ddd(panel, pre, post)
    rng = np.random.default_rng(config.SEED)
    draws = pd.DataFrame([ddd(panel, pre, post, panel.bootstrap_weights(rng)) for _ in range(args.n_boot)])
    t = pd.DataFrame([{"estimate": k, "point": point[k], "ci_low": np.percentile(draws[k], 2.5),
                       "ci_high": np.percentile(draws[k], 97.5)} for k in ("mid", "senior", "ddd")])
    os.makedirs(args.out, exist_ok=True)
    t.to_csv(os.path.join(args.out, f"italy_ddd_{tag}.csv"), index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
