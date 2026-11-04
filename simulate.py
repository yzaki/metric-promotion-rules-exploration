"""Create simulated scientists with a KNOWN reform effect, to test the method.

The output file has exactly the same columns as data/trajectories.csv, so
estimate.py runs on it unchanged. If estimate.py recovers the planted effect,
the pipeline works; only then is it worth trusting on real data.

Usage:
    python simulate.py                      # writes data/simulated_trajectories.csv
    python estimate.py --input data/simulated_trajectories.csv --truth data/simulated_truth.json
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import config
import irl

# True reward weights (theta_cite, theta_near, theta_far) for each group and period.
# Control countries drift a little over time (a common trend). Italy gets the same
# drift PLUS a reform effect: citations matter more, distant jumps feel costlier.
COMMON_TREND = np.array([0.20, 0.00, 0.10])
REFORM_EFFECT = np.array([0.80, 0.00, -0.60])
THETA = {
    ("CTRL", "pre"): np.array([1.50, -1.00, -2.50]),
    ("IT", "pre"): np.array([1.40, -1.10, -2.50]),
}
THETA[("CTRL", "post")] = THETA[("CTRL", "pre")] + COMMON_TREND
THETA[("IT", "post")] = THETA[("IT", "pre")] + COMMON_TREND + REFORM_EFFECT


def true_transitions():
    """How the world moves: P(s' | s, a) used to generate the data."""
    tier_s, ten_s, car_s = irl.state_parts()
    P = np.zeros((irl.N_STATES, irl.N_ACTIONS, irl.N_STATES))

    def tier_dist(tier, action):
        d = np.zeros(3)
        if action == 0:                     # stay: topic's citation potential drifts slowly
            d[tier] = 0.85
            for t in (tier - 1, tier + 1):
                if 0 <= t <= 2:
                    d[t] += 0.075
        elif action == 1:                   # nearby: lands close to where you were
            d[tier] = 0.5
            for t in (tier - 1, tier + 1):
                if 0 <= t <= 2:
                    d[t] += 0.25
        else:                               # distant jump: could land anywhere
            d[:] = 1.0
        return d / d.sum()

    def tenure_dist(ten, action):
        d = np.zeros(3)
        if action != 0:
            d[0] = 1.0                      # new topic: time in topic resets
        elif ten == 0:
            d[1] = 1.0
        elif ten == 1:
            d[1], d[2] = 0.5, 0.5           # bin 1 covers 2-3 years
        else:
            d[2] = 1.0
        return d

    def career_dist(car):
        d = np.zeros(3)
        if car == 0:
            d[0], d[1] = 5 / 6, 1 / 6       # bin 0 covers 6 years
        elif car == 1:
            d[1], d[2] = 0.9, 0.1           # bin 1 covers 10 years
        else:
            d[2] = 1.0
        return d

    for s in range(irl.N_STATES):
        for a in range(irl.N_ACTIONS):
            joint = np.einsum("i,j,k->ijk", tier_dist(tier_s[s], a),
                              tenure_dist(ten_s[s], a), career_dist(car_s[s]))
            P[s, a] = joint.reshape(-1)
    return P


def theta_for(group, year):
    """Pre weights up to 2009, post weights from 2013, a straight line in between."""
    pre, post = THETA[(group, "pre")], THETA[(group, "post")]
    if year <= 2009:
        return pre
    if year >= 2013:
        return post
    w = (year - 2009) / 4
    return (1 - w) * pre + w * post


def simulate(n_it, n_ctrl, gamma, seed):
    rng = np.random.default_rng(seed)
    P = true_transitions()
    years = list(range(2004, 2019))
    policies = {(g, y): irl.policy(theta_for(g, y), P, gamma)
                for g in ("IT", "CTRL") for y in years}
    tier_s, ten_s, car_s = irl.state_parts()

    rows = []
    authors = [("IT", "IT")] * n_it + [("CTRL", c) for c in config.CONTROLS
                                       for _ in range(n_ctrl // len(config.CONTROLS))]
    for i, (group, country) in enumerate(authors):
        s = int(irl.state_index(rng.integers(0, 3), 0, rng.choice(3, p=[0.4, 0.4, 0.2])))
        for y in years:
            a = int(rng.choice(3, p=policies[(group, y)][s]))
            s_next = int(rng.choice(irl.N_STATES, p=P[s, a]))
            rows.append((f"A{i:06d}", country, group, y,
                         tier_s[s], ten_s[s], car_s[s], irl.ACTIONS[a],
                         tier_s[s_next], ten_s[s_next], car_s[s_next]))
            s = s_next

    cols = ["author_id", "country", "group", "year", "s_tier", "s_tenure", "s_career",
            "action", "ns_tier", "ns_tenure", "ns_career"]
    return pd.DataFrame(rows, columns=cols)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n-it", type=int, default=3000, help="number of simulated Italian scientists")
    ap.add_argument("--n-ctrl", type=int, default=6000, help="number of simulated control scientists")
    ap.add_argument("--seed", type=int, default=config.SEED)
    args = ap.parse_args()

    os.makedirs(config.DATA_DIR, exist_ok=True)
    df = simulate(args.n_it, args.n_ctrl, config.GAMMA, args.seed)
    out = os.path.join(config.DATA_DIR, "simulated_trajectories.csv")
    df.to_csv(out, index=False)

    truth = {
        "did": dict(zip(irl.PARAMS, REFORM_EFFECT.tolist())),
        "groups": {f"{g}_{p}": dict(zip(irl.PARAMS, v.tolist())) for (g, p), v in THETA.items()},
    }
    with open(os.path.join(config.DATA_DIR, "simulated_truth.json"), "w") as f:
        json.dump(truth, f, indent=2)

    print(f"Wrote {len(df):,} simulated choices by {df.author_id.nunique():,} scientists to {out}")
    print("Planted reform effect (difference-in-differences):", truth["did"])


if __name__ == "__main__":
    main()
