"""Spain as a treated country: national accreditation for professorships (Royal Decree 1312/2007,
first evaluations 2008) and tighter quantitative criteria (Royal Decree 415/2015).

Uses the six-country trajectory file; Spain is compared with France + Germany (Italy and the other
countries left out). Reports
    - the event study of the nearby-move weight, Spain minus control, relative to 2004-05 (before the
      2008 accreditation), with a scientist bootstrap;
    - DiD 2004-07 vs 2010-13 (2008 accreditation) and 2010-13 vs 2016-18 (2015 criteria);
    - the model-free DiD for the same comparisons.

Usage:
    set CT_FIELD_ID=31 & python spain_check.py --input data/trajectories_world_ctrl_FR_DE_ES_NL_PT.csv --out results_world_spain
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel, fit_groups, did
from reduced_form import demean, ols_cluster

NEAR = irl.PARAMS.index("theta_near")
WINDOWS = [(2004, 2005), (2006, 2007), (2008, 2009), (2010, 2011), (2012, 2013), (2014, 2015), (2016, 2017)]
COMPARISONS = {"accreditation 2008 (2004-07 vs 2010-13)": (list(range(2004, 2008)), list(range(2010, 2014))),
               "criteria 2015 (2010-13 vs 2016-18)": (list(range(2010, 2014)), list(range(2016, 2019)))}


def window_diffs(panel, weights=None):
    out = {}
    for w in WINDOWS:
        m = np.isin(panel.year, list(range(w[0], w[1] + 1)))
        th = {}
        for flag in (True, False):
            choices, trans = panel.counts(m & (panel.is_it == flag), weights)
            th[flag] = irl.fit_counts(choices, trans, config.GAMMA)["theta"][NEAR]
        out[w] = th[True] - th[False]
    return {w: v - out[WINDOWS[0]] for w, v in out.items()}


def lpm(df, pre, post):
    s = df[df.year.isin(pre + post)].reset_index(drop=True)
    d = ((s.group == "IT") & s.year.isin(post)).astype(float).to_numpy()
    author = pd.factorize(s.author_id)[0]
    groups = [author, s.year.to_numpy()]
    y = (s.action == "near").astype(float).to_numpy()
    b, se = ols_cluster(demean(y[:, None], groups)[:, 0], demean(d[:, None], groups), author)
    return 100 * b[0], 100 * se[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    df = pd.read_csv(args.input)
    df = df[df.country.isin(["ES", "FR", "DE"])].reset_index(drop=True)
    df["group"] = np.where(df.country == "ES", "IT", "CTRL")   # 'IT' = treated label used by Panel
    panel = Panel(df)
    rng = np.random.default_rng(config.SEED)

    point = window_diffs(panel)
    boots = [window_diffs(panel, panel.bootstrap_weights(rng)) for _ in range(args.n_boot)]
    rows = [{"analysis": "event study vs 2004-05", "window": f"{w[0]}-{w[1]}", "estimate": point[w],
             "ci_low": np.percentile([b[w] for b in boots], 2.5),
             "ci_high": np.percentile([b[w] for b in boots], 97.5)} for w in WINDOWS]
    for label, (pre, post) in COMPARISONS.items():
        est = did(fit_groups(panel, pre, post, config.GAMMA))[NEAR]
        draws = [did(fit_groups(panel, pre, post, config.GAMMA, weights=panel.bootstrap_weights(rng)))[NEAR]
                 for _ in range(args.n_boot)]
        rows.append({"analysis": "DiD weight", "window": label, "estimate": est,
                     "ci_low": np.percentile(draws, 2.5), "ci_high": np.percentile(draws, 97.5)})
        b, se = lpm(df, pre, post)
        rows.append({"analysis": "DiD model-free pp", "window": label, "estimate": b,
                     "ci_low": b - 1.96 * se, "ci_high": b + 1.96 * se})
    t = pd.DataFrame(rows)
    t["n_spain_scientists"] = df.author_id[df.group == "IT"].nunique()
    os.makedirs(args.out, exist_ok=True)
    t.to_csv(os.path.join(args.out, "spain_check.csv"), index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
