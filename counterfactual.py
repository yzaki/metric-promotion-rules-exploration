"""Counterfactual policy simulation with the recovered rewards.

For Italian scientists after the reform, simulate 10-year careers from their observed
post-reform state distribution, using Italy's post-reform transitions, under alternative
reward weights (each scenario re-solves the scientists' forward-looking choice rule):
    actual             Italy's fitted post-reform weights
    no reform          post weights minus the difference-in-differences (all three weights)
    credit +x          actual, plus an "exploration credit" x on nearby moves
    stronger citations actual, with the citation-potential weight raised by 0.5
Outputs: expected nearby moves per scientist over 10 years, share of scientists with at least
one nearby move in 6 years, and the yearly nearby-move share.

Usage:
    python counterfactual.py --input data/trajectories_world.csv --results results_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel

HORIZON, WINDOW, N_SIM = 10, 6, 20000


def simulate(theta, P, start, rng):
    pi = irl.policy(theta, P, config.GAMMA)
    s = rng.choice(irl.N_STATES, size=N_SIM, p=start)
    near = np.zeros((N_SIM, HORIZON), dtype=bool)
    for t in range(HORIZON):
        u = rng.random(N_SIM)
        cum = np.cumsum(pi[s], axis=1)
        a = (u[:, None] > cum).sum(axis=1)
        near[:, t] = a == 1
        nxt = np.cumsum(P[s, a], axis=1)
        s = np.minimum((rng.random(N_SIM)[:, None] > nxt).sum(axis=1), irl.N_STATES - 1)
    return {"nearby_moves_10y": near.sum(axis=1).mean(),
            "share_any_nearby_6y": near[:, :WINDOW].any(axis=1).mean(),
            "yearly_nearby_share": near.mean()}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--results", default=config.RESULTS_DIR)
    args = ap.parse_args()
    rng = np.random.default_rng(config.SEED)

    panel = Panel(pd.read_csv(args.input))
    mask = panel.is_it & np.isin(panel.year, config.POST_YEARS)
    choices, trans = panel.counts(mask)
    P = irl.transition_probs(trans)
    start = choices.sum(axis=1) / choices.sum()
    w = pd.read_csv(os.path.join(args.results, "weights_by_group_main.csv"), index_col=0)
    theta = w.loc[list(irl.PARAMS), "IT_post"].astype(float).to_numpy()
    did = pd.read_csv(os.path.join(args.results, "did_main.csv")).set_index("parameter").did
    did = did.loc[list(irl.PARAMS)].to_numpy()

    scenarios = [("actual", theta), ("no reform", theta - did)]
    for x in (0.05, 0.10, 0.15, 0.20, 0.30):
        scenarios.append((f"credit +{x:.2f} on nearby moves", theta + np.array([0, x, 0])))
    scenarios.append(("citation weight +0.5", theta + np.array([0.5, 0, 0])))
    rows = [{"scenario": n, **simulate(th, P, start, rng)} for n, th in scenarios]
    t = pd.DataFrame(rows)
    base = t.loc[t.scenario == "actual", "nearby_moves_10y"].iloc[0]
    t["change_vs_actual_pct"] = 100 * (t.nearby_moves_10y / base - 1)
    path = os.path.join(args.results, "counterfactual.csv")
    t.to_csv(path, index=False)
    print(t.round(3).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
