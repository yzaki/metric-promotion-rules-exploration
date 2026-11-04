"""Robustness: a richer reward in which the value of moves depends on the state.

Reward features (11): citation tier; near; far; near and far interacted with time in topic
(2-3, 4+ years) and with career stage (6-15, 16+ years). Staying remains the baseline.

1. Fit: out-of-sample mean log-likelihood (train first 3 years of each period, test last 3),
   compared with the 3-weight model and a saturated lookup table.
2. Reform effect: the 11 weights are fitted for the four groups; the effect is expressed as the
   change in Italy's predicted yearly nearby-move share after the reform when the full
   difference-in-differences of all weights is removed (as in effect_sizes.py). 95% intervals
   from bootstrap resamples of scientists.

Usage:
    python rich_model.py --input data/trajectories_world.csv --out results_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel

NAMES = ["cite", "near", "far", "near_x_ten2", "near_x_ten3", "far_x_ten2", "far_x_ten3",
         "near_x_car2", "near_x_car3", "far_x_car2", "far_x_car3"]


def rich_phi():
    tier, ten, car = irl.state_parts()
    phi = np.zeros((irl.N_STATES, irl.N_ACTIONS, len(NAMES)))
    phi[:, :, 0] = (tier / 2)[:, None]
    phi[:, 1, 1] = 1
    phi[:, 2, 2] = 1
    for a, base in ((1, 3), (2, 5)):
        phi[:, a, base] = ten == 1
        phi[:, a, base + 1] = ten == 2
    for a, base in ((1, 7), (2, 9)):
        phi[:, a, base] = car == 1
        phi[:, a, base + 1] = car == 2
    return phi


PHI = rich_phi()


def fit(panel, mask, weights=None, theta0=None):
    choices, trans = panel.counts(mask, weights)
    P = irl.transition_probs(trans)
    return irl.fit(choices, P, config.GAMMA, phi=PHI, theta0=theta0)["theta"], P, choices


def near_share(theta, P, start):
    pi = irl.policy(theta, P, config.GAMMA, phi=PHI)
    return float((start[:, None] * pi).sum(axis=0)[1])


def effect(panel, weights=None, warm=None):
    pre, post = np.isin(panel.year, config.PRE_YEARS), np.isin(panel.year, config.POST_YEARS)
    th = {}
    for name, m in (("IT_pre", panel.is_it & pre), ("IT_post", panel.is_it & post),
                    ("CTRL_pre", ~panel.is_it & pre), ("CTRL_post", ~panel.is_it & post)):
        th[name], P, ch = fit(panel, m, weights, None if warm is None else warm[name])
        if name == "IT_post":
            P_post, start = P, ch.sum(axis=1) / ch.sum()
    did = (th["IT_post"] - th["IT_pre"]) - (th["CTRL_post"] - th["CTRL_pre"])
    return 100 * (near_share(th["IT_post"], P_post, start) - near_share(th["IT_post"] - did, P_post, start)), th


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--out", default=config.RESULTS_DIR)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    rng = np.random.default_rng(config.SEED)
    panel = Panel(pd.read_csv(args.input))

    fit_rows = []
    for gname, gm in (("Italy", panel.is_it), ("Control", ~panel.is_it)):
        for pname, yrs in (("before", config.PRE_YEARS), ("after", config.POST_YEARS)):
            tr, te = gm & np.isin(panel.year, yrs[:3]), gm & np.isin(panel.year, yrs[3:])
            th, P, ch_tr = fit(panel, tr)
            ch_te, _ = panel.counts(te)
            ll_rich = float((ch_te * np.log(irl.policy(th, P, config.GAMMA, phi=PHI))).sum() / ch_te.sum())
            ch3, tr3 = panel.counts(tr)
            P3 = irl.transition_probs(tr3)
            th3 = irl.fit(ch3, P3, config.GAMMA)["theta"]
            ll_3 = float((ch_te * np.log(irl.policy(th3, P3, config.GAMMA))).sum() / ch_te.sum())
            const = ch_tr.sum(axis=0) / ch_tr.sum()
            ll_c = float((ch_te * np.log(const)[None, :]).sum() / ch_te.sum())
            n_s = ch_tr.sum(axis=1, keepdims=True)
            sat = np.where(n_s > 0, (ch_tr + 0.5) / (n_s + 1.5), const[None, :])
            ll_sat = float((ch_te * np.log(sat)).sum() / ch_te.sum())
            fit_rows.append({"group": gname, "period": pname, "oos_ll_rich11": ll_rich, "oos_ll_3weights": ll_3,
                             "oos_ll_constant": ll_c, "oos_ll_saturated": ll_sat})
    fit_t = pd.DataFrame(fit_rows)
    print(fit_t.round(4).to_string(index=False))

    point, th = effect(panel)
    draws = []
    for b in range(args.n_boot):
        draws.append(effect(panel, panel.bootstrap_weights(rng), warm=th)[0])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    did_w = (th["IT_post"] - th["IT_pre"]) - (th["CTRL_post"] - th["CTRL_pre"])
    print(f"\nReform effect on Italy's yearly nearby-move share (rich model): {point:+.2f} pp [{lo:+.2f}, {hi:+.2f}]")
    print("DiD of the 11 weights:", dict(zip(NAMES, np.round(did_w, 3))))
    os.makedirs(args.out, exist_ok=True)
    fit_t.to_csv(os.path.join(args.out, "rich_model_fit.csv"), index=False)
    pd.DataFrame([{"effect_near_pp": point, "ci_low": lo, "ci_high": hi, **dict(zip(NAMES, did_w))}]).to_csv(
        os.path.join(args.out, "rich_model_effect.csv"), index=False)


if __name__ == "__main__":
    main()
