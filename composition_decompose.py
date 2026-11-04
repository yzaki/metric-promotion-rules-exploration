"""Decompose the raw nearby-move DiD by who is observed: stayers (choices in both periods),
leavers (before only) and entrants (after only).

Prints, for Italy and control, the nearby-move share and the number of choices of each group in
each period, and the 'entrant vs leaver' contrast (entrants after minus leavers before), Italy minus
control, with a scientist bootstrap. This is the part of the raw DiD that a scientist-FE model ignores.

Usage:
    python composition_decompose.py --input data_field13/trajectories_world.csv --out results_field13_world
"""
import argparse
import os

import numpy as np
import pandas as pd

import config


def contrasts(df):
    near = (df.action == "near").to_numpy()
    out = {}
    for g in ("IT", "CTRL"):
        m = (df.group == g).to_numpy()
        for typ in ("stayer", "leaver", "entrant"):
            for per in ("before", "after"):
                k = m & (df.type == typ).to_numpy() & (df.period == per).to_numpy()
                out[(g, typ, per)] = (near[k].mean() if k.any() else np.nan, k.sum())
    stay = lambda g: out[(g, "stayer", "after")][0] - out[(g, "stayer", "before")][0]
    turn = lambda g: out[(g, "entrant", "after")][0] - out[(g, "leaver", "before")][0]
    return out, 100 * (stay("IT") - stay("CTRL")), 100 * (turn("IT") - turn("CTRL"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=200)
    args = ap.parse_args()

    df = pd.read_csv(args.input)
    df = df[df.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)
    df["period"] = np.where(df.year.isin(config.PRE_YEARS), "before", "after")
    has = df.groupby("author_id").period.agg(lambda p: set(p))
    typ = has.map(lambda s: "stayer" if len(s) == 2 else ("leaver" if "before" in s else "entrant"))
    df["type"] = df.author_id.map(typ)

    out, d_stay, d_turn = contrasts(df)
    rng = np.random.default_rng(config.SEED)
    authors = df.author_id.unique()
    grp = df.drop_duplicates("author_id").set_index("author_id").group
    rows_by_author = df.groupby("author_id").indices
    boots = []
    for _ in range(args.n_boot):
        idx = []
        for g in ("IT", "CTRL"):
            a = grp.index[grp == g].to_numpy()
            pick = rng.choice(a, size=len(a), replace=True)
            idx.append(np.concatenate([rows_by_author[x] for x in pick]))
        _, s, t = contrasts(df.iloc[np.concatenate(idx)])
        boots.append((s, t))
    boots = np.array(boots)

    rows = [{"group": g, "type": t, "period": p, "share_near_pct": 100 * v[0], "n_choices": v[1]}
            for (g, t, p), v in out.items()]
    shares = pd.DataFrame(rows)
    print(shares.round(2).to_string(index=False))
    summ = pd.DataFrame([
        {"contrast": "stayers: after minus before", "did_pp": d_stay,
         "ci_low": np.percentile(boots[:, 0], 2.5), "ci_high": np.percentile(boots[:, 0], 97.5)},
        {"contrast": "entrants after minus leavers before", "did_pp": d_turn,
         "ci_low": np.percentile(boots[:, 1], 2.5), "ci_high": np.percentile(boots[:, 1], 97.5)}])
    print("\nItaly minus control:\n", summ.round(2).to_string(index=False))
    os.makedirs(args.out, exist_ok=True)
    shares.to_csv(os.path.join(args.out, "composition_shares.csv"), index=False)
    summ.to_csv(os.path.join(args.out, "composition_decompose.csv"), index=False)


if __name__ == "__main__":
    main()
