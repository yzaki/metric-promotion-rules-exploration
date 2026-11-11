"""Russia, hypothesis R4: was the decline larger among scientists at the 21 Project 5-100 universities?

Main Russian affiliation in 2009-12 (OpenAlex dated affiliations, data_meta/affiliations_ru.csv.gz; the institution
with the most records, ties to the most recent): '5-100' if it is one of the 21 universities (PROJECT_5_100, by
OpenAlex ID), otherwise 'not covered'. Per field:
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
# The 21 Project 5-100 universities (plan, as of 2015), as OpenAlex institution IDs (reviewed by name; an earlier
# name-pattern match also caught four unrelated institutions named after Peter the Great or N.V. Rudnitsky and
# missed MISiS, which OpenAlex calls "National University of Science and Technology").
PROJECT_5_100 = {
    "I118501908": "National Research University Higher School of Economics",
    "I153845743": "Moscow Institute of Physics and Technology",
    "I12003341": "National University of Science and Technology (MISiS)",
    "I887846188": "National Research Nuclear University MEPhI",
    "I79563041": "N. I. Lobachevsky State University of Nizhny Novgorod",
    "I188973947": "Novosibirsk State University",
    "I17877952": "Sechenov University",
    "I126527374": "Peoples' Friendship University of Russia",
    "I3124489027": "Samara National Research University",
    "I41518628": "Saint Petersburg State Electrotechnical University (LETI)",
    "I212220629": "Peter the Great St. Petersburg Polytechnic University",
    "I4853710": "Siberian Federal University",
    "I196355604": "National Research Tomsk State University",
    "I30849647": "Tomsk Polytechnic University",
    "I3020440027": "University of Tyumen",
    "I173089394": "ITMO University",
    "I130823665": "Ural Federal University",
    "I107640659": "South Ural State University",
    "I149643846": "Immanuel Kant Baltic Federal University",
    "I204947315": "Far Eastern Federal University",
    "I21203515": "Kazan Federal University",
}


def main_institution(aff):
    """Each scientist's main institution: the one with the most affiliation records in the window; ties go to the
    institution seen most recently, then to the smallest institution ID."""
    n = aff.groupby(["author_id", "institution_id"]).agg(n=("year", "size"), last=("year", "max")).reset_index()
    n = n.sort_values(["author_id", "n", "last", "institution_id"], ascending=[True, False, False, True])
    return n.drop_duplicates("author_id").set_index("author_id").institution_id


def classify():
    aff = pd.read_csv(os.path.join(META, "affiliations_ru.csv.gz"), dtype={"institution_id": str})
    types = pd.read_csv(os.path.join(META, "institution_types.csv.gz")).drop_duplicates("id").set_index("id")
    aff = aff[aff.year.between(2009, 2012) & (aff.country == "RU")].copy()
    aff["name"] = aff.institution_id.map(types["name"]).fillna("")
    aff = aff[aff.name != ""]
    main_inst = main_institution(aff)
    cls = pd.Series(np.where(main_inst.isin(list(PROJECT_5_100)), "5-100", "not covered"), index=main_inst.index)
    return cls, aff


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(config.HERE, "results_russia"))
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    g, aff = classify()
    g.rename("group").to_csv(os.path.join(args.out, "russia_groups.csv"))
    matched = pd.DataFrame({"institution_id": list(PROJECT_5_100), "name_in_plan": list(PROJECT_5_100.values())})
    matched["name"] = matched.institution_id.map(aff.drop_duplicates("institution_id").set_index("institution_id")["name"])
    matched["main_institution_of"] = matched.institution_id.map(main_institution(aff).value_counts()).fillna(0).astype(int)
    matched.to_csv(os.path.join(args.out, "russia_5_100_institutions_matched.csv"), index=False)
    print(g.value_counts().to_string(), "\n5-100 universities (main institution of N scientists):\n", matched.to_string(index=False), flush=True)
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
