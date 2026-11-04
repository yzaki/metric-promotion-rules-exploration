"""Stage A consequences: did staying put pay off in output and citations?

Uses the raw papers already downloaded (no API calls). For scientists in the trajectory
sample, builds author-year outcomes:
    papers        number of articles that year
    log_cites     mean log(1 + normalised citations) of those articles; citations are
                  divided by the mean for their publication year (all downloaded papers)
    top10         share of those articles in the top 10% most cited of their year

1. Reform DiD on author-year outcomes: (Italy after - before) - (control after - before).
2. Move premium: outcome in the NEXT active year after a nearby move (or distant jump),
   minus after staying; and the DiD of that premium (did the reform change it for Italy?).

95% intervals: bootstrap resampling whole scientists within Italy and control.

Usage:
    python outcomes_citations.py                                   # Physics
    python outcomes_citations.py --input data/trajectories_es.csv --tag es
    set CT_FIELD_ID=22 && python outcomes_citations.py             # Engineering
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from build_trajectories import load_raw

OUTCOMES = ("papers", "log_cites", "top10")


def author_year_outcomes(df, authors):
    works = df.drop_duplicates("work_id")[["work_id", "year", "cited_by_count"]].copy()
    works["c_norm"] = works.cited_by_count / works.groupby("year").cited_by_count.transform("mean")
    works["log_c"] = np.log1p(works.c_norm)
    works["top10"] = (works.groupby("year").cited_by_count.rank(pct=True) > 0.9).astype(float)
    d = df[df.author_id.isin(authors)][["author_id", "work_id", "year"]].drop_duplicates()
    d = d.merge(works[["work_id", "log_c", "top10"]], on="work_id")
    return (d.groupby(["author_id", "year"])
            .agg(papers=("work_id", "size"), log_cites=("log_c", "mean"), top10=("top10", "mean"))
            .reset_index())


def cell_sums(frame, keys, value):
    """Per author: sum and count of `value` in each cell defined by `keys`."""
    g = frame.groupby(["author_id"] + keys)[value].agg(["sum", "count"])
    return g.unstack(keys, fill_value=0)


def boot_ci(stat_fn, sums, is_it, rng, n_boot):
    point = stat_fn(np.ones(len(sums)))
    draws = []
    for _ in range(n_boot):
        w = np.zeros(len(sums))
        for flag in (True, False):
            idx = np.flatnonzero(is_it == flag)
            w[idx] = rng.multinomial(len(idx), np.full(len(idx), 1 / len(idx)))
        draws.append(stat_fn(w))
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return point, lo, hi


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--controls", nargs="+", default=None, help="must match the trajectory file")
    ap.add_argument("--tag", default="")
    ap.add_argument("--n-boot", type=int, default=config.N_BOOT)
    ap.add_argument("--lead", type=int, default=2,
                    help="measure move outcomes this many active years after the decision year")
    args = ap.parse_args()
    if args.controls:
        config.CONTROLS = args.controls
        config.COUNTRIES = [config.TREATED] + args.controls
    suffix = (f"_{args.tag}" if args.tag else "") + ("" if args.lead == 2 else f"_lead{args.lead}")
    rng = np.random.default_rng(config.SEED)

    traj = pd.read_csv(args.input)
    group = traj.drop_duplicates("author_id").set_index("author_id").group
    ay = author_year_outcomes(load_raw(), set(group.index))
    ay["period"] = np.select([ay.year.isin(config.PRE_YEARS), ay.year.isin(config.POST_YEARS)],
                             ["pre", "post"], "")
    rows = []

    # 1. Reform DiD on author-year outcomes
    a1 = ay[ay.period != ""]
    for out in OUTCOMES:
        sums = cell_sums(a1, ["period"], out)
        is_it = (group.reindex(sums.index) == "IT").to_numpy()
        S, N = sums["sum"], sums["count"]

        def stat(w, S=S, N=N, is_it=is_it):
            m = {}
            for g, flag in (("IT", True), ("CTRL", False)):
                ww = w * (is_it == flag)
                for p in ("pre", "post"):
                    m[g, p] = (ww * S[p]).sum() / (ww * N[p]).sum()
            return (m["IT", "post"] - m["IT", "pre"]) - (m["CTRL", "post"] - m["CTRL", "pre"])

        point, lo, hi = boot_ci(stat, sums, is_it, rng, args.n_boot)
        means = {f"{g}_{p}": (S[p][is_it == (g == "IT")].sum() / N[p][is_it == (g == "IT")].sum())
                 for g in ("IT", "CTRL") for p in ("pre", "post")}
        rows.append({"analysis": "reform_did", "outcome": out, "estimate": point,
                     "ci_low": lo, "ci_high": hi, **means})

    # 2. Move premium: outcome `lead` active years later, by action taken this year.
    # lead=1 is the year the move is observed in, so its own paper count partly defines the
    # move (one-paper years have noisy topics); lead=2 avoids that mechanical link.
    nxt = ay[["author_id", "year"] + list(OUTCOMES)].sort_values(["author_id", "year"])
    nxt = nxt.assign(prev_year=nxt.groupby("author_id").year.shift(args.lead))
    ch = traj.merge(nxt.drop(columns="year").rename(columns={"prev_year": "year"}),
                    on=["author_id", "year"], how="inner")
    ch["period"] = np.select([ch.year.isin(config.PRE_YEARS), ch.year.isin(config.POST_YEARS)],
                             ["pre", "post"], "")
    ch = ch[ch.period != ""]
    for move in ("near", "far"):
        sub = ch[ch.action.isin(["stay", move])]
        for out in OUTCOMES:
            sums = cell_sums(sub, ["period", "action"], out)
            is_it = (group.reindex(sums.index) == "IT").to_numpy()
            S, N = sums["sum"], sums["count"]

            def gap(w, flag, p, S=S, N=N, is_it=is_it, move=move):
                ww = w * (is_it == flag)
                return ((ww * S[p, move]).sum() / (ww * N[p, move]).sum()
                        - (ww * S[p, "stay"]).sum() / (ww * N[p, "stay"]).sum())

            for label, fn in (
                ("premium_IT_pre", lambda w: gap(w, True, "pre")),
                ("premium_IT_post", lambda w: gap(w, True, "post")),
                ("premium_CTRL_pre", lambda w: gap(w, False, "pre")),
                ("premium_CTRL_post", lambda w: gap(w, False, "post")),
                ("premium_did", lambda w: (gap(w, True, "post") - gap(w, True, "pre"))
                                          - (gap(w, False, "post") - gap(w, False, "pre"))),
            ):
                point, lo, hi = boot_ci(fn, sums, is_it, rng, args.n_boot)
                rows.append({"analysis": f"{move}_vs_stay_{label}", "outcome": out,
                             "estimate": point, "ci_low": lo, "ci_high": hi})

    table = pd.DataFrame(rows)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    out = os.path.join(config.RESULTS_DIR, f"outcomes_citations{suffix}.csv")
    table.to_csv(out, index=False)
    pd.set_option("display.width", 200)
    print(table.round(4).to_string(index=False))
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
