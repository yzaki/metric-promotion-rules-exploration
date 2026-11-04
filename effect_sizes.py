"""Translate the reform effect into plain numbers (choice shares).

For Italian scientists after the reform, compares
    actual         : choices predicted by Italy's fitted post-reform weights
    counterfactual : the same scientists, same situations, with the reform effect removed
                     (Italy's post weights minus the difference-in-differences)
Both use Italy's post-reform transitions and Italy's observed post-reform states, so
only the reform effect differs. 95% intervals use the saved bootstrap draws of the effect
(holding Italy's post weights at their point estimate).

Usage:
    python effect_sizes.py --input data/trajectories.csv --results results
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel


def shares(theta, P, state_counts, gamma):
    """Average predicted probability of stay / near / far over the observed states."""
    pi = irl.policy(theta, P, gamma)
    return (state_counts[:, None] * pi).sum(axis=0) / state_counts.sum()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--results", default=config.RESULTS_DIR)
    ap.add_argument("--gamma", type=float, default=config.GAMMA)
    args = ap.parse_args()

    panel = Panel(pd.read_csv(args.input))
    mask = panel.is_it & np.isin(panel.year, config.POST_YEARS)
    choices, trans = panel.counts(mask)
    P = irl.transition_probs(trans)
    state_counts = choices.sum(axis=1)

    w = pd.read_csv(os.path.join(args.results, "weights_by_group_main.csv"), index_col=0)
    theta_post = w.loc[list(irl.PARAMS), "IT_post"].astype(float).to_numpy()
    did = pd.read_csv(os.path.join(args.results, "did_main.csv")).set_index("parameter").did
    did = did.loc[list(irl.PARAMS)].to_numpy()
    draws = pd.read_csv(os.path.join(args.results, "did_bootstrap_main.csv"))[list(irl.PARAMS)].to_numpy()

    actual = shares(theta_post, P, state_counts, args.gamma)
    cf = shares(theta_post - did, P, state_counts, args.gamma)
    boot = np.array([actual - shares(theta_post - d, P, state_counts, args.gamma) for d in draws])
    lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)

    observed = choices.sum(axis=0) / choices.sum()
    n_scientists = panel.df[mask].author_id.nunique()
    per_year = choices.sum() / len(config.POST_YEARS)
    rows = []
    for k, a in enumerate(irl.ACTIONS):
        diff = actual[k] - cf[k]
        rows.append({"choice": a, "observed": observed[k], "predicted_actual": actual[k],
                     "predicted_no_reform": cf[k], "diff_pp": 100 * diff,
                     "diff_pp_low": 100 * lo[k], "diff_pp_high": 100 * hi[k],
                     "relative_change_pct": 100 * diff / cf[k],
                     "choices_per_year_change": diff * per_year})
    table = pd.DataFrame(rows)
    out = os.path.join(args.results, "effect_sizes.csv")
    table.to_csv(out, index=False)
    print(f"Italian post-reform sample: {n_scientists:,} scientists, {int(choices.sum()):,} choices "
          f"({per_year:,.0f} per year)")
    print(table.round(3).to_string(index=False))
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
