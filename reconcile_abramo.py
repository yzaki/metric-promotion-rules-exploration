"""Reconcile with Abramo, D'Angelo & Di Costa (2024): specialisation at two levels.

Abramo et al. define a scientist's core field as the (coarse) WoS subject category holding
most of their papers, and specialisation as the share of papers in it; they found Italian
specialisation fell after the 2012 habilitation. Here the same index is computed on our
data at two levels, per scientist and period (before 2004-09, after 2013-18; at least
MIN_PAPERS papers in the period):
    spec_subfield  share of papers in the scientist's main OpenAlex subfield (~ WoS SC)
    spec_topic     share of papers in the scientist's main OpenAlex topic (finer)
Reform DiD (Italy vs control), bootstrap over scientists.
Caveat: only papers in the downloaded field are seen, so moves to other fields are missed.

Usage:
    python reconcile_abramo.py                    # Physics
    set CT_FIELD_ID=22 && python reconcile_abramo.py
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from build_trajectories import load_raw
from outcomes_citations import boot_ci

MIN_PAPERS = 3


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--n-boot", type=int, default=config.N_BOOT)
    args = ap.parse_args()
    rng = np.random.default_rng(config.SEED)

    group = pd.read_csv(args.input, usecols=["author_id", "group"]).drop_duplicates("author_id")
    group = group.set_index("author_id").group
    df = load_raw()
    df = df[df.author_id.isin(group.index)].drop_duplicates(["author_id", "work_id"])
    df["period"] = np.select([df.year.isin(config.PRE_YEARS), df.year.isin(config.POST_YEARS)],
                             ["pre", "post"], "")
    df = df[df.period != ""]

    def spec(level):
        n = df.groupby(["author_id", "period", level]).size()
        tot = n.groupby(["author_id", "period"]).sum()
        top = n.groupby(["author_id", "period"]).max()
        out = (top / tot).rename("spec").to_frame().assign(n=tot)
        return out[out.n >= MIN_PAPERS].spec.unstack("period")

    rows = []
    for level, name in (("subfield_id", "spec_subfield"), ("topic_id", "spec_topic")):
        s = spec(level)
        is_it = (group.reindex(s.index) == "IT").to_numpy()
        S = {p: s[p].fillna(0).to_numpy() for p in ("pre", "post")}
        N = {p: s[p].notna().to_numpy().astype(float) for p in ("pre", "post")}

        def stat(w, S=S, N=N, is_it=is_it):
            m = {}
            for g, flag in (("IT", True), ("CTRL", False)):
                ww = w * (is_it == flag)
                for p in ("pre", "post"):
                    m[g, p] = (ww * S[p]).sum() / (ww * N[p]).sum()
            return (m["IT", "post"] - m["IT", "pre"]) - (m["CTRL", "post"] - m["CTRL", "pre"])

        point, lo, hi = boot_ci(stat, s, is_it, rng, args.n_boot)
        means = {f"{g}_{p}": S[p][is_it == (g == "IT")].sum() / N[p][is_it == (g == "IT")].sum()
                 for g in ("IT", "CTRL") for p in ("pre", "post")}
        rows.append({"measure": name, "did": point, "ci_low": lo, "ci_high": hi, **means,
                     "n_scientists": len(s)})

    table = pd.DataFrame(rows)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    path = os.path.join(config.RESULTS_DIR, "reconcile_abramo.csv")
    table.to_csv(path, index=False)
    print(table.round(4).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
