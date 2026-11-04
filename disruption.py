"""Stage C consequences: were Italian papers less disruptive or less atypical after the reform?

Uses SciSciNet paper-level metrics (Lin et al. 2023), filtered on Jubail to our papers
(data_sciscinet/sciscinet_our_papers.tsv.gz; OpenAlex W-ids of MAG-era works equal MAG
PaperIDs). Papers with zero references are dropped (their CD index is degenerate).
Author-year outcomes (mean over the scientist's papers that year):
    disruption      CD index (SciSciNet "Disruption")
    disruptive      share of papers with disruption > 0
    atyp_10pct      SciSciNet "Atyp_10pct_Z" (10th-percentile z-score; lower = more atypical)
    atyp_median     SciSciNet "Atyp_Median_Z" (median z-score; higher = more conventional)
Reform DiD (Italy vs control), bootstrap over scientists.

Usage:
    python disruption.py                                   # Physics, FR+DE
    set CT_FIELD_ID=22 && python disruption.py
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from build_trajectories import load_raw
from outcomes_citations import boot_ci, cell_sums

SCI = os.path.join(config.HERE, "data_sciscinet", "sciscinet_our_papers.tsv.gz")


def load_sciscinet():
    head = pd.read_csv(SCI, sep="\t", nrows=0).columns
    pick = {c.lower(): c for c in head}
    need = {"paperid": "work", "disruption": "disruption", "atyp_10pct_z": "atyp_10pct",
            "atyp_median_z": "atyp_median", "reference_count": "n_refs"}
    missing = [k for k in need if k not in pick]
    if missing:
        raise SystemExit(f"Columns not found: {missing}. Header: {list(head)}")
    s = pd.read_csv(SCI, sep="\t", usecols=[pick[k] for k in need]).rename(
        columns={pick[k]: v for k, v in need.items()})
    s = s[s.n_refs > 0]
    s["disruptive"] = (s.disruption > 0).astype(float).where(s.disruption.notna())
    print(f"SciSciNet rows with references: {len(s):,}; with disruption: {s.disruption.notna().sum():,}")
    return s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--controls", nargs="+", default=None, help="must match the trajectory file")
    ap.add_argument("--tag", default="")
    ap.add_argument("--n-boot", type=int, default=config.N_BOOT)
    args = ap.parse_args()
    if args.controls:
        config.CONTROLS = args.controls
        config.COUNTRIES = [config.TREATED] + args.controls
    suffix = f"_{args.tag}" if args.tag else ""
    rng = np.random.default_rng(config.SEED)

    group = pd.read_csv(args.input, usecols=["author_id", "group"]).drop_duplicates("author_id")
    group = group.set_index("author_id").group
    raw = load_raw()
    raw = raw[raw.author_id.isin(group.index)][["author_id", "work_id", "year"]].drop_duplicates()
    raw["work"] = raw.work_id.str[1:].astype(np.int64)
    papers = raw.merge(load_sciscinet(), on="work", how="inner")
    print(f"Matched {papers.work.nunique():,} of {raw.work.nunique():,} sample papers "
          f"({papers.work.nunique() / raw.work.nunique():.1%})")
    papers["period"] = np.select([papers.year.isin(config.PRE_YEARS), papers.year.isin(config.POST_YEARS)],
                                 ["pre", "post"], "")
    papers = papers[papers.period != ""]
    outs = ("disruption", "disruptive", "atyp_10pct", "atyp_median")
    ay = papers.groupby(["author_id", "year", "period"])[list(outs)].mean().reset_index()

    rows = []
    for out in outs:
        a = ay.dropna(subset=[out])
        sums = cell_sums(a, ["period"], out)
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
        means = {f"{g}_{p}": S[p][is_it == (g == "IT")].sum() / N[p][is_it == (g == "IT")].sum()
                 for g in ("IT", "CTRL") for p in ("pre", "post")}
        rows.append({"outcome": out, "did": point, "ci_low": lo, "ci_high": hi, **means})

    table = pd.DataFrame(rows)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    path = os.path.join(config.RESULTS_DIR, f"disruption{suffix}.csv")
    table.to_csv(path, index=False)
    print(table.round(5).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
