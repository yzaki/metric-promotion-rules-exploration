"""Russia, hypothesis R4: was the decline larger among scientists at the 21 Project 5-100 universities?

Main Russian affiliation in 2009-12 (OpenAlex dated affiliations, data_meta/affiliations_ru.csv.gz; most frequent
institution): '5-100' if its name matches one of the plan's patterns, otherwise 'not covered'. Per field:
nearby-move weight for each group vs France + Germany with paired scientist resamples, and the difference.
Writes russia_groups.csv (author_id, group) for the stacked model-free test (india_stacked.py --suffix RU).
Plan: ../PREREGISTRATION_russia_2026-11-05.md.

Usage:
    python russia_mechanism.py --out results_russia
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
PROJECT_5_100 = re.compile("|".join([
    r"Higher School of Economics", r"Moscow Institute of Physics and Technology", r"MISiS|MISIS",
    r"MEPhI|National Research Nuclear University", r"Lobachevsky", r"Novosibirsk State University(?! of)",
    r"Sechenov|First Moscow State Medical University", r"Peoples'? Friendship University|RUDN",
    r"Samara National Research University|Samara University", r"Electrotechnical University|LETI",
    r"Peter the Great|Saint Petersburg Polytechnic|St\.? Petersburg Polytechnic", r"Siberian Federal University",
    r"Tomsk State University(?! of)", r"Tomsk Polytechnic", r"University of Tyumen|Tyumen State University",
    r"ITMO", r"Ural Federal University", r"South Ural State University(?! of)", r"Immanuel Kant|Baltic Federal University",
    r"Far Eastern Federal University", r"Kazan Federal University"]), re.I)


def classify():
    aff = pd.read_csv(os.path.join(META, "affiliations_ru.csv.gz"), dtype={"institution_id": str})
    types = pd.read_csv(os.path.join(META, "institution_types.csv.gz")).drop_duplicates("id").set_index("id")
    aff = aff[aff.year.between(2009, 2012) & (aff.country == "RU")].copy()
    aff["name"] = aff.institution_id.map(types["name"]).fillna("")
    aff = aff[aff.name != ""]
    aff["cls"] = np.where(aff.name.str.contains(PROJECT_5_100), "5-100", "not covered")
    return aff.groupby("author_id").cls.agg(lambda s: s.value_counts().index[0]), aff


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(config.HERE, "results_russia"))
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    g, aff = classify()
    g.rename("group").to_csv(os.path.join(args.out, "russia_groups.csv"))
    matched = aff[aff.cls == "5-100"].drop_duplicates("institution_id")[["institution_id", "name"]]
    matched.to_csv(os.path.join(args.out, "russia_5_100_institutions_matched.csv"), index=False)
    print(g.value_counts().to_string(), "\nmatched 5-100 institution names:\n", matched.name.sort_values().to_string(index=False), flush=True)
    pre, post = config.PRE_YEARS, config.POST_YEARS
    rows = []
    rng = np.random.default_rng(config.SEED)
    for field, d in FIELDS.items():
        df = pd.read_csv(os.path.join(config.HERE, d, "trajectories_world_RU.csv"))
        df = df[df.year.isin(pre + post)].reset_index(drop=True)
        df["g"] = df.author_id.map(g).where(df.group == "IT")
        groups = ["5-100", "not covered"]
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
        draws["diff"] = draws["5-100"] - draws["not covered"]
        point["diff"] = point["5-100"] - point["not covered"]
        for x in groups + ["diff"]:
            rows.append({"field": field, "group": "5-100 minus not covered" if x == "diff" else x,
                         "irl_near": point[x], "irl_low": np.percentile(draws[x], 2.5), "irl_high": np.percentile(draws[x], 97.5),
                         "n_russian": int(df.author_id[df.g == x].nunique()) if x != "diff" else np.nan})
        print(pd.DataFrame(rows[-3:]).round(3).to_string(index=False), flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(args.out, "russia_mechanism.csv"), index=False)


if __name__ == "__main__":
    main()
