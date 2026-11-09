"""Who needed the habilitation? Reform effect by academic rank in 2011 (MUR staff register).

The national habilitation was required for promotion to associate and to full professor. Full professors
(ordinari) in December 2011 no longer needed it for promotion (only to sit on its committees); associate
professors and researchers did. Italian scientists in the sample are matched by name to the MUR register
of university staff at 31/12/2011 (cercauniversita.mur.gov.it exports, areas 02, 05, 08, 09; files in
data_meta/staff_register/, not distributed). A match requires the same first given name and surname and
must be unique on both sides.

For each Italian rank group, the nearby-move DiD against all French and German scientists (IRL weight and
model-free LPM), and the difference between groups, with paired scientist resamples. Also restricted to
scientists at least 16 years into their careers (true career start), so rank is not just age.

Usage:
    set CT_FIELD_ID=31 & python rank_exposure.py --input data/trajectories_world_career.csv --out results_world_career
"""
import argparse
import glob
import os
import unicodedata

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel, fit_groups, did
from reduced_form import demean, ols_cluster

NEAR = irl.PARAMS.index("theta_near")
META = os.path.join(config.HERE, "data_meta")


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(ch if ch.isalpha() or ch == " " else " " for ch in s).split()


def register(snapshot="31122011"):
    rows = []
    for f in sorted(glob.glob(os.path.join(META, "staff_register", f"docenti_area*_{snapshot}.xlsx"))):
        d = pd.read_excel(f)
        for rank, name, ateneo, sc in zip(d["Fascia"], d["Cognome e Nome"], d["Ateneo"], d["SC2015"]):
            parts = str(name).split()
            sur = [p for p in parts if p.isupper() and len(p) > 1]
            given = [p for p in parts if not (p.isupper() and len(p) > 1)]
            if not sur or not given or not norm(given[0]):
                continue
            rows.append({"key": norm(given[0])[0] + "|" + " ".join(norm(" ".join(sur))),
                         "rank": str(rank).strip(), "ateneo": ateneo, "sc": str(sc).strip()})
    r = pd.DataFrame(rows).drop_duplicates(["key", "rank", "ateneo"])
    return r[~r.key.duplicated(keep=False)].set_index("key")   # unique names only


def our_keys(ids):
    n = pd.read_csv(os.path.join(META, "author_names.tsv.gz"), sep="\t").set_index("author_id")
    out = {}
    for a in ids:
        toks = norm(n.full_name.get(a, "")) if a in n.index else []
        if len(toks) < 2:
            continue
        cands = {toks[0] + "|" + " ".join(toks[k:]) for k in range(1, len(toks))}
        out[a] = cands
    return out


def group_of(rank):
    if rank.startswith("Ordinario"):
        return "full professor"
    if rank.startswith("Associato"):
        return "associate professor"
    return "researcher"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    pre, post = config.PRE_YEARS, config.POST_YEARS

    df = pd.read_csv(args.input)
    df = df[df.year.isin(pre + post)].reset_index(drop=True)
    reg = register()
    it_ids = df.author_id[df.group == "IT"].unique()
    keys = our_keys(it_ids)
    hits = {}
    for a, cands in keys.items():
        m = [k for k in cands if k in reg.index]
        if len(m) == 1:
            hits[a] = m[0]
    hit_keys = pd.Series(hits)
    hit_keys = hit_keys[~hit_keys.duplicated(keep=False)]   # one scientist per register entry
    rank = hit_keys.map(lambda k: group_of(reg.loc[k, "rank"]))
    print(f"Italian scientists {len(it_ids):,}; matched to the 2011 register {len(rank):,} "
          f"({len(rank) / len(it_ids):.1%}); by rank:\n{rank.value_counts().to_string()}", flush=True)
    pd.DataFrame({"rank_2011": rank, "sc_2011": hit_keys.map(lambda k: reg.loc[k, "sc"])}).to_csv(
        os.path.join(args.out, "rank_2011_match.csv"))   # ids, rank and sector only; not distributed

    cs = pd.read_csv(os.path.join(config.HERE, "career_start", "career_start.tsv.gz"), sep="\t").set_index("author_id").mag_first_year
    career_2011 = 2011 - cs   # years since first publication (full MAG record), by author_id

    df["rank"] = df.author_id.map(rank).where(df.group == "IT")
    groups = ["full professor", "associate professor", "researcher"]
    samples = {"all career ages": df,
               "16+ years in 2011": df[(df.group == "CTRL") | df.author_id.map(career_2011).ge(16)]}
    rng = np.random.default_rng(config.SEED)
    rows = []
    for sname, s in samples.items():
        s = s.reset_index(drop=True)
        panels = {g: Panel(s[(s.group == "CTRL") | (s["rank"] == g)].reset_index(drop=True)) for g in groups}
        point = {g: did(fit_groups(panels[g], pre, post, config.GAMMA))[NEAR] for g in groups}
        it_auth = s.author_id[s["rank"].isin(groups)].unique()
        ct_auth = s.author_id[s.group == "CTRL"].unique()
        draws = []
        for _ in range(args.n_boot):
            w = pd.concat([pd.Series(rng.multinomial(len(it_auth), np.full(len(it_auth), 1 / len(it_auth))), index=it_auth),
                           pd.Series(rng.multinomial(len(ct_auth), np.full(len(ct_auth), 1 / len(ct_auth))), index=ct_auth)])
            draws.append({g: did(fit_groups(panels[g], pre, post, config.GAMMA,
                                            weights=panels[g].df.author_id.map(w).to_numpy(dtype=float)))[NEAR]
                          for g in groups})
        draws = pd.DataFrame(draws)
        draws["needed minus full"] = (draws["associate professor"] + draws["researcher"]) / 2 - draws["full professor"]
        point["needed minus full"] = (point["associate professor"] + point["researcher"]) / 2 - point["full professor"]
        for g in groups + ["needed minus full"]:
            row = {"sample": sname, "group": g, "irl_near": point[g],
                   "irl_low": np.percentile(draws[g], 2.5), "irl_high": np.percentile(draws[g], 97.5)}
            if g in groups:
                sub = s[(s.group == "CTRL") | (s["rank"] == g)].reset_index(drop=True)
                d = ((sub.group == "IT") & sub.year.isin(post)).astype(float).to_numpy()
                author = pd.factorize(sub.author_id)[0]
                fe = [author, sub.year.to_numpy()]
                y = (sub.action == "near").astype(float).to_numpy()
                b, se = ols_cluster(demean(y[:, None], fe)[:, 0], demean(d[:, None], fe), author)
                row.update(lpm_near_pp=100 * b[0], lpm_low=100 * (b[0] - 1.96 * se[0]),
                           lpm_high=100 * (b[0] + 1.96 * se[0]),
                           n_italian=int(sub.author_id[sub.group == "IT"].nunique()))
            rows.append(row)
            print(rows[-1], flush=True)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(args.out, "rank_exposure.csv"), index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
