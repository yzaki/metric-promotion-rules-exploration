"""Reform effect on nearby moves by finer bands of true career age (years since the first publication
in the full MAG record, data_meta/career_start.tsv.gz).

The habilitation mattered for promotion to associate and to full professor (and for serving on its
committees), so exposure should fall only for the most senior scientists, most of whom were already full
professors or close to retirement. For each band: IRL nearby-move DiD (choices restricted to the band,
transitions of the full group; scientist bootstrap) and the model-free DiD (scientist + year FE, within band).

Usage:
    python career_bands.py --input data/trajectories_world_career.csv --out results_world_career
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel, fit_groups, did
from reduced_form import demean, ols_cluster

BANDS = [(0, 10), (11, 20), (21, 30), (31, 80)]
NEAR = irl.PARAMS.index("theta_near")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--career-start", default=os.path.join(config.HERE, "data_meta", "career_start.tsv.gz"))
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    pre, post = config.PRE_YEARS, config.POST_YEARS

    df = pd.read_csv(args.input)
    df = df[df.year.isin(pre + post)].reset_index(drop=True)
    cs = pd.read_csv(args.career_start, sep="\t").set_index("author_id")
    first = np.minimum(df.author_id.map(cs.mag_first_year), df.groupby("author_id").year.transform("min"))
    df["career_years"] = df.year - first
    panel = Panel(df)
    rng = np.random.default_rng(config.SEED)
    rows = []
    for lo, hi in BANDS:
        m = df.career_years.between(lo, hi).to_numpy()
        est = did(fit_groups(panel, pre, post, config.GAMMA, choice_mask=m))[NEAR]
        draws = [did(fit_groups(panel, pre, post, config.GAMMA, weights=panel.bootstrap_weights(rng),
                                choice_mask=m))[NEAR] for _ in range(args.n_boot)]
        s = df[m].reset_index(drop=True)
        d = ((s.group == "IT") & s.year.isin(post)).astype(float).to_numpy()
        author = pd.factorize(s.author_id)[0]
        groups = [author, s.year.to_numpy()]
        y = (s.action == "near").astype(float).to_numpy()
        b, se = ols_cluster(demean(y[:, None], groups)[:, 0], demean(d[:, None], groups), author)
        n = {f"n_{g}_{p}": int(((s.group == g) & s.year.isin(yrs)).sum())
             for g in ("IT", "CTRL") for p, yrs in (("pre", pre), ("post", post))}
        rows.append({"band": f"{lo}-{hi}" if hi < 80 else f"{lo}+", "irl_near": est,
                     "irl_low": np.percentile(draws, 2.5), "irl_high": np.percentile(draws, 97.5),
                     "lpm_near_pp": 100 * b[0], "lpm_low": 100 * (b[0] - 1.96 * se[0]),
                     "lpm_high": 100 * (b[0] + 1.96 * se[0]), **n})
        print(rows[-1], flush=True)
    t = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    t.to_csv(os.path.join(args.out, "career_bands.csv"), index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
