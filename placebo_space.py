"""Inference with one treated country: placebo-in-space and a within-country triple difference.

For each country c in {IT, FR, DE, ES, NL, PT}, c is treated as if it had the reform and compared with
the other non-Italian countries (Italy itself is compared with all five). For each assignment:
    - IRL nearby-move DiD (point estimate),
    - model-free LPM nearby-move DiD (scientist + year FE, pp),
    - IRL nearby-move DiD by career stage, and the triple difference mid-career (6-15 y) minus
      senior (16+ y). The triple difference removes any country-wide shock that moved all career
      stages alike (for example a national funding or assessment change).
Italy's estimates are then ranked among the six. For Italy, the triple difference also gets a
scientist bootstrap (the same resample for both stages).

Usage:
    python placebo_space.py --input data/trajectories_world_ctrl_FR_DE_ES_NL_PT.csv --out results_world_placebo_space
"""
import argparse
import os
import time

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel, fit_groups, did
from reduced_form import demean, ols_cluster

NEAR = irl.PARAMS.index("theta_near")
COUNTRIES = ["IT", "FR", "DE", "ES", "NL", "PT"]


def lpm_near(df):
    d = ((df.group == "IT") & df.year.isin(config.POST_YEARS)).astype(float).to_numpy()
    author = pd.factorize(df.author_id)[0]
    groups = [author, df.year.to_numpy()]
    Xd = demean(d[:, None], groups)
    y = (df.action == "near").astype(float).to_numpy()
    yd = demean(y[:, None], groups)[:, 0]
    b, se = ols_cluster(yd, Xd, author)
    return 100 * b[0], 100 * se[0]


def irl_set(panel, weights=None):
    pre, post, g = config.PRE_YEARS, config.POST_YEARS, config.GAMMA
    out = {"all": did(fit_groups(panel, pre, post, g, weights=weights))[NEAR]}
    for k in (1, 2):
        out[k] = did(fit_groups(panel, pre, post, g, weights=weights, choice_mask=(panel.career == k)))[NEAR]
    out["ddd"] = out[1] - out[2]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()

    full = pd.read_csv(args.input)
    full = full[full.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)
    rows = []
    for c in COUNTRIES:
        t0 = time.time()
        df = full if c == "IT" else full[full.country != "IT"]
        df = df.assign(group=np.where(df.country == c, "IT", "CTRL")).reset_index(drop=True)
        panel = Panel(df)
        r = irl_set(panel)
        b, se = lpm_near(df)
        rows.append({"treated": c, "n_treated_scientists": df.author_id[df.group == "IT"].nunique(),
                     "irl_near": r["all"], "irl_near_mid": r[1], "irl_near_senior": r[2],
                     "irl_ddd_mid_minus_senior": r["ddd"], "lpm_near_pp": b, "lpm_se_pp": se})
        print(f"{c}: IRL {r['all']:+.3f}  mid {r[1]:+.3f}  senior {r[2]:+.3f}  DDD {r['ddd']:+.3f}  "
              f"LPM {b:+.2f} pp ({time.time() - t0:.0f}s)", flush=True)
    t = pd.DataFrame(rows)
    for col in ("irl_near", "irl_ddd_mid_minus_senior", "lpm_near_pp"):
        t[f"rank_{col}"] = t[col].rank(method="min").astype(int)   # 1 = most negative
    os.makedirs(args.out, exist_ok=True)
    t.to_csv(os.path.join(args.out, "placebo_space.csv"), index=False)
    print("\n", t.round(3).to_string(index=False))

    # Bootstrap for Italy's triple difference (same resample for both career stages)
    df = full.assign(group=np.where(full.country == "IT", "IT", "CTRL"))
    panel = Panel(df)
    rng = np.random.default_rng(config.SEED)
    draws = []
    for b in range(args.n_boot):
        draws.append(irl_set(panel, panel.bootstrap_weights(rng)))
        if (b + 1) % 25 == 0:
            print(f"  bootstrap {b + 1}/{args.n_boot}", flush=True)
    draws = pd.DataFrame(draws)
    draws.to_csv(os.path.join(args.out, "italy_ddd_bootstrap.csv"), index=False)
    summ = pd.DataFrame([{"estimate": k, "point": t.loc[0, col], "ci_low": np.percentile(draws[k], 2.5),
                          "ci_high": np.percentile(draws[k], 97.5)}
                         for k, col in (("all", "irl_near"), (1, "irl_near_mid"), (2, "irl_near_senior"),
                                        ("ddd", "irl_ddd_mid_minus_senior"))])
    summ.to_csv(os.path.join(args.out, "italy_ddd.csv"), index=False)
    print("\nItaly, bootstrap 95% intervals:\n", summ.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
