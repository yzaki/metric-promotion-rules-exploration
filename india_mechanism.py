"""India, hypothesis I4: was the decline larger among scientists covered by the UGC Regulations 2010?

Main Indian affiliation in 2009-12 (OpenAlex dated affiliations, data_meta/affiliations_in.csv.gz; most
frequent institution type, then institution): 'UGC-covered' = education institutions (universities and
colleges) except autonomous institutes matched by the name patterns fixed in the plan; 'not covered' =
facility or government institutions and the autonomous institutes. Per field: nearby-move weight for each
group vs France + Germany with paired scientist resamples, and the difference. Writes india_groups.csv
(author_id, group) for the stacked model-free test in india_stacked.py.

Usage:
    python india_mechanism.py --out results_india
"""
import argparse
import os
import re

import numpy as np
import pandas as pd

import config
import irl
from estimate import Panel, fit_groups, did

NEAR = irl.PARAMS.index("theta_near")
META = os.path.join(config.HERE, "data_meta")
FIELDS = {"Physics": "data", "Engineering": "data_field22", "Biochemistry": "data_field13", "Chemistry": "data_field16"}
AUTONOMOUS = re.compile("|".join(["Indian Institute of Technology", "Indian Institute of Science",
                                  "Indian Institute of Science Education and Research", "National Institute of Technology",
                                  "Indian Statistical Institute", "Tata Institute", "All India Institute of Medical Sciences",
                                  "Indian Institute of Management", "Indian Institute of Information Technology",
                                  "Homi Bhabha"]), re.I)


def classify():
    aff = pd.read_csv(os.path.join(META, "affiliations_in.csv.gz"), dtype={"institution_id": str})
    types = pd.read_csv(os.path.join(META, "institution_types.csv.gz")).drop_duplicates("id").set_index("id")
    aff = aff[aff.year.between(2009, 2012) & (aff.country == "IN")].copy()
    aff["type"] = aff.institution_id.map(types["type"])
    aff["name"] = aff.institution_id.map(types["name"]).fillna("")
    aff["cls"] = np.select([aff.type.isin(["facility", "government"]),
                            (aff.type == "education") & aff.name.str.contains(AUTONOMOUS),
                            aff.type == "education"], ["not covered", "not covered", "UGC-covered"], "other")
    aff = aff[aff.cls != "other"]
    # main institution: most affiliation records in 2009-12; ties to the most recent, then the smallest ID
    n = aff.groupby(["author_id", "institution_id"]).agg(n=("year", "size"), last=("year", "max")).reset_index()
    n = n.sort_values(["author_id", "n", "last", "institution_id"], ascending=[True, False, False, True])
    main_inst = n.drop_duplicates("author_id").set_index("author_id").institution_id
    return main_inst.map(aff.drop_duplicates("institution_id").set_index("institution_id").cls)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(config.HERE, "results_india"))
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    g = classify()
    g.rename("group").to_csv(os.path.join(args.out, "india_groups.csv"))
    print(g.value_counts().to_string(), flush=True)
    pre, post = config.PRE_YEARS, config.POST_YEARS
    rows = []
    rng = np.random.default_rng(config.SEED)
    for field, d in FIELDS.items():
        df = pd.read_csv(os.path.join(config.HERE, d, "trajectories_world_IN.csv"))
        df = df[df.year.isin(pre + post)].reset_index(drop=True)
        df["g"] = df.author_id.map(g).where(df.group == "IT")
        groups = ["UGC-covered", "not covered"]
        panels = {x: Panel(df[(df.group == "CTRL") | (df.g == x)].reset_index(drop=True)) for x in groups}
        point = {x: did(fit_groups(panels[x], pre, post, config.GAMMA))[NEAR] for x in groups}
        it_auth = df.author_id[df.g.isin(groups)].unique()
        ct_auth = df.author_id[df.group == "CTRL"].unique()
        draws = []
        for _ in range(args.n_boot):
            w = pd.concat([pd.Series(rng.multinomial(len(it_auth), np.full(len(it_auth), 1 / len(it_auth))), index=it_auth),
                           pd.Series(rng.multinomial(len(ct_auth), np.full(len(ct_auth), 1 / len(ct_auth))), index=ct_auth)])
            draws.append({x: did(fit_groups(panels[x], pre, post, config.GAMMA,
                                            weights=panels[x].df.author_id.map(w).to_numpy(dtype=float)))[NEAR] for x in groups})
        draws = pd.DataFrame(draws)
        draws["diff"] = draws["UGC-covered"] - draws["not covered"]
        point["diff"] = point["UGC-covered"] - point["not covered"]
        for x in groups + ["diff"]:
            rows.append({"field": field, "group": "UGC-covered minus not covered" if x == "diff" else x,
                         "irl_near": point[x], "irl_low": np.percentile(draws[x], 2.5), "irl_high": np.percentile(draws[x], 97.5),
                         "n_indian": int(df.author_id[df.g == x].nunique()) if x != "diff" else np.nan})
        print(pd.DataFrame(rows[-3:]).round(3).to_string(index=False), flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(args.out, "india_mechanism.csv"), index=False)


if __name__ == "__main__":
    main()
