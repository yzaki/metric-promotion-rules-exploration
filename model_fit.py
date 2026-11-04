"""Model fit: in-sample and out-of-sample checks of the inverse-RL model.

In-sample: for each group (Italy, control) and period (before, after), the model's predicted
choice shares in each of the 27 states versus observed shares; reports the count-weighted mean
absolute error and correlation, and aggregate shares.

Out-of-sample: fit on the first three years of each period (2004-06, 2013-15), predict the last
three (2007-09, 2016-18). Mean log-likelihood per choice is compared with (i) constant overall
shares and (ii) a saturated lookup table of observed shares per state (54 free parameters,
estimated on the same training years; unseen states fall back to overall shares).

Usage:
    python model_fit.py --input data/trajectories_world.csv --out results_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel


def fit_cell(panel, mask):
    choices, trans = panel.counts(mask)
    P = irl.transition_probs(trans)
    res = irl.fit(choices, P, config.GAMMA)
    return res["theta"], P, choices


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--out", default=config.RESULTS_DIR)
    args = ap.parse_args()
    panel = Panel(pd.read_csv(args.input))

    rows = []
    periods = {"before": (config.PRE_YEARS[:3], config.PRE_YEARS[3:]),
               "after": (config.POST_YEARS[:3], config.POST_YEARS[3:])}
    for gname, gmask in (("Italy", panel.is_it), ("Control", ~panel.is_it)):
        for pname, (train, test) in periods.items():
            full = gmask & np.isin(panel.year, train + test)
            theta, P, choices = fit_cell(panel, full)
            pi = irl.policy(theta, P, config.GAMMA)
            n_s = choices.sum(axis=1)
            obs = np.divide(choices, n_s[:, None], out=np.zeros_like(choices), where=n_s[:, None] > 0)
            w = n_s / n_s.sum()
            mae = float((w[:, None] * np.abs(pi - obs)).sum() / 3)
            keep = n_s >= 30
            corr = float(np.corrcoef(pi[keep].ravel(), obs[keep].ravel())[0, 1])
            agg_obs = choices.sum(axis=0) / choices.sum()
            agg_pred = (n_s[:, None] * pi).sum(axis=0) / n_s.sum()

            tr = gmask & np.isin(panel.year, train)
            te = gmask & np.isin(panel.year, test)
            theta_tr, P_tr, ch_tr = fit_cell(panel, tr)
            pi_tr = irl.policy(theta_tr, P_tr, config.GAMMA)
            ch_te, _ = panel.counts(te)
            n_te = ch_te.sum()
            ll_irl = float((ch_te * np.log(pi_tr)).sum() / n_te)
            const = ch_tr.sum(axis=0) / ch_tr.sum()
            ll_const = float((ch_te * np.log(const)[None, :]).sum() / n_te)
            n_tr_s = ch_tr.sum(axis=1, keepdims=True)
            sat = np.where(n_tr_s > 0, (ch_tr + 0.5) / (n_tr_s + 1.5), const[None, :])
            ll_sat = float((ch_te * np.log(sat)).sum() / n_te)
            rows.append({"group": gname, "period": pname, "choices": int(choices.sum()),
                         "mae_state_shares_pp": 100 * mae, "corr_state_shares": corr,
                         **{f"obs_{a}": agg_obs[k] for k, a in enumerate(irl.ACTIONS)},
                         **{f"pred_{a}": agg_pred[k] for k, a in enumerate(irl.ACTIONS)},
                         "oos_ll_irl": ll_irl, "oos_ll_constant": ll_const, "oos_ll_saturated": ll_sat})
    t = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    path = os.path.join(args.out, "model_fit.csv")
    t.to_csv(path, index=False)
    print(t.round(4).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
