"""Stage B consequences: did scientists draw on less new knowledge after the reform?

Needs reference lists (fetch_references.py). For each scientist in the trajectory sample
and each year, counts the distinct works they cite that year and how many of those they
had never cited before (counting back to the first reference year downloaded, 2001; 2001-03
only seed the history). Outcomes per author-year:
    refs        distinct works cited that year
    new_refs    of those, works the author had never cited before
    new_share   new_refs / refs

Reform DiD: (Italy after - before) - (control after - before), bootstrap over scientists.

Usage:
    python novelty.py                                      # Physics, FR+DE
    python novelty.py --input data/trajectories_es.csv --controls FR DE ES --tag es
    set CT_FIELD_ID=22 && python novelty.py                # Engineering
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

import config
from build_trajectories import load_raw
from outcomes_citations import boot_ci, cell_sums

N_CHUNKS = 16


def load_refs():
    files = sorted(f for f in glob.glob(os.path.join(config.DATA_DIR, "refs", "refs_*.csv.gz"))
                   if os.path.basename(f).split("_")[1] in config.COUNTRIES)
    if not files:
        raise SystemExit("No reference files. Run fetch_references.py first.")
    parts = []
    for f in files:
        r = pd.read_csv(f)
        parts.append(pd.DataFrame({"work": r.work_id.str[1:].astype(np.int64),
                                   "ref": r.ref_id.str[1:].astype(np.int64)}))
    refs = pd.concat(parts, ignore_index=True).drop_duplicates()
    print(f"Loaded {refs.work.nunique():,} papers with {len(refs):,} references from {len(files)} files")
    return refs


def author_year_novelty(papers, refs):
    """papers: author (int), work (int), year. Returns author-year refs / new_refs."""
    out = []
    for k in range(N_CHUNKS):   # chunk by author to keep memory small
        p = papers[papers.author % N_CHUNKS == k]
        ar = p.merge(refs, on="work")[["author", "year", "ref"]].drop_duplicates(["author", "ref", "year"])
        first = ar.groupby(["author", "ref"]).year.transform("min")
        ar["new"] = ar.year == first
        out.append(ar.groupby(["author", "year"]).agg(refs=("ref", "size"), new_refs=("new", "sum"))
                   .reset_index())
    ay = pd.concat(out, ignore_index=True)
    ay["new_share"] = ay.new_refs / ay.refs
    return ay


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

    traj = pd.read_csv(args.input)
    group = traj.drop_duplicates("author_id").set_index("author_id").group
    raw = load_raw()
    raw = raw[raw.author_id.isin(group.index) & (raw.year >= 2001)]
    papers = pd.DataFrame({"author_id": raw.author_id, "work": raw.work_id.str[1:].astype(np.int64),
                           "year": raw.year}).drop_duplicates()
    codes, uniques = pd.factorize(papers.author_id)
    papers["author"] = codes
    ay = author_year_novelty(papers[["author", "work", "year"]], load_refs())
    ay["author_id"] = uniques[ay.author]
    ay["period"] = np.select([ay.year.isin(config.PRE_YEARS), ay.year.isin(config.POST_YEARS)],
                             ["pre", "post"], "")
    a1 = ay[ay.period != ""]

    rows = []
    for out in ("refs", "new_refs", "new_share"):
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
        rows.append({"outcome": out, "did": point, "ci_low": lo, "ci_high": hi, **means})

    table = pd.DataFrame(rows)
    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    path = os.path.join(config.RESULTS_DIR, f"novelty{suffix}.csv")
    table.to_csv(path, index=False)
    ay.to_csv(os.path.join(config.RESULTS_DIR, f"novelty_author_year{suffix}.csv.gz"), index=False)
    print(table.round(4).to_string(index=False))
    print(f"\nSaved {path}")


if __name__ == "__main__":
    main()
