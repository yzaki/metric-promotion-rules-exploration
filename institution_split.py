"""Reform effect by where Italian scientists worked in 2009-2012 (OpenAlex dated affiliations).

Groups of Italian scientists (each vs all French and German scientists):
    university staff         matched to the 2011 university staff register (rank_2011_match.csv)
    university, early career not in the register, mainly at a university (education), <= 10 years since first
                             publication in 2011: mostly postdoctoral and fixed-term researchers
    university, other        not in the register, at a university, > 10 years (mostly names not matched uniquely)
    research institute       mainly at a facility or government institution (INFN, CNR, INAF, ...)
    hospital or company      mainly at a healthcare institution or company
The main institution type is the most frequent type of Italian institution-years in 2009-2012.
Nearby-move weight with paired scientist resamples, and the model-free estimate.

Usage:
    set CT_FIELD_ID=31 & python institution_split.py --input data/trajectories_world_career.csv --out results_world_career
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
META = os.path.join(config.HERE, "data_meta")
GROUPS = ["university staff", "university, early career", "university, other", "research institute",
          "hospital or company"]


def classify(authors, matched, career_2011):
    aff = pd.read_csv(os.path.join(META, "affiliations_it.csv.gz"), dtype={"institution_id": str})
    types = pd.read_csv(os.path.join(META, "institution_types.csv.gz")).set_index("id")
    aff = aff[aff.year.between(2009, 2012) & (aff.country == "IT") & aff.author_id.isin(authors)]
    aff["type"] = aff.institution_id.map(types["type"])
    main = aff.dropna(subset=["type"]).groupby("author_id")["type"].agg(lambda s: s.value_counts().index[0])
    out = {}
    for a in authors:
        if a in matched:
            out[a] = "university staff"
            continue
        t = main.get(a)
        if t == "education":
            out[a] = "university, early career" if career_2011.get(a, np.nan) <= 10 else "university, other"
        elif t in ("facility", "government"):
            out[a] = "research institute"
        elif t in ("healthcare", "company"):
            out[a] = "hospital or company"
    return pd.Series(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    pre, post = config.PRE_YEARS, config.POST_YEARS
    df = pd.read_csv(args.input)
    df = df[df.year.isin(pre + post)].reset_index(drop=True)
    matched = set(pd.read_csv(os.path.join(args.out, "rank_2011_match.csv"), index_col=0).index)
    cs = pd.read_csv(os.path.join(META, "career_start.tsv.gz"), sep="\t").set_index("author_id").mag_first_year
    it = df.author_id[df.group == "IT"].unique()
    g = classify(it, matched, (2011 - cs).to_dict())
    print(f"Italian scientists {len(it):,}; classified {len(g):,}\n{g.value_counts().to_string()}", flush=True)
    df["g"] = df.author_id.map(g).where(df.group == "IT")
    groups = [x for x in GROUPS if (g == x).sum() >= 100]
    panels = {x: Panel(df[(df.group == "CTRL") | (df.g == x)].reset_index(drop=True)) for x in groups}
    point = {x: did(fit_groups(panels[x], pre, post, config.GAMMA))[NEAR] for x in groups}
    it_auth = df.author_id[df.g.isin(groups)].unique()
    ct_auth = df.author_id[df.group == "CTRL"].unique()
    rng = np.random.default_rng(config.SEED)
    draws = []
    for _ in range(args.n_boot):
        w = pd.concat([pd.Series(rng.multinomial(len(it_auth), np.full(len(it_auth), 1 / len(it_auth))), index=it_auth),
                       pd.Series(rng.multinomial(len(ct_auth), np.full(len(ct_auth), 1 / len(ct_auth))), index=ct_auth)])
        draws.append({x: did(fit_groups(panels[x], pre, post, config.GAMMA,
                                        weights=panels[x].df.author_id.map(w).to_numpy(dtype=float)))[NEAR] for x in groups})
    draws = pd.DataFrame(draws)
    extra = []
    if "research institute" in groups:
        for x in ("university staff", "university, early career"):
            if x in groups:
                k = f"{x} minus research institute"
                draws[k], point[k] = draws[x] - draws["research institute"], point[x] - point["research institute"]
                extra.append(k)
    rows = []
    for x in groups + extra:
        row = {"group": x, "irl_near": point[x], "irl_low": np.percentile(draws[x], 2.5),
               "irl_high": np.percentile(draws[x], 97.5)}
        if x in groups:
            sub = panels[x].df
            d = ((sub.group == "IT") & sub.year.isin(post)).astype(float).to_numpy()
            author = pd.factorize(sub.author_id)[0]
            fe = [author, sub.year.to_numpy()]
            y = (sub.action == "near").astype(float).to_numpy()
            b, se = ols_cluster(demean(y[:, None], fe)[:, 0], demean(d[:, None], fe), author)
            row.update(lpm_near_pp=100 * b[0], lpm_low=100 * (b[0] - 1.96 * se[0]), lpm_high=100 * (b[0] + 1.96 * se[0]),
                       n_italian=int(sub.author_id[sub.group == "IT"].nunique()))
        rows.append(row)
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(args.out, "institution_split.csv"), index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
