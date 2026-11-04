"""Heterogeneity by gender and Italian region, and an ORCID-only robustness check.

Uses data_meta/authors.csv.gz and data_meta/institutions_it.csv.gz (fetch_authors.py).
  gender  inferred from the first name with gender-guesser, using the scientist's country;
          initials-only and ambiguous names are left unclassified.
  region  macro-region (North / Centre / South and islands) of an Italian scientist's last known
          Italian institution (OpenAlex geo.region). This is the latest institution, not
          necessarily the one at the time of the reform.
  ORCID   scientists with an ORCID in OpenAlex (more reliable author identity).

Subgroup effects use the full model (inverse-RL difference-in-differences of the nearby-move
weight; choices restricted to the subgroup, transitions from the full group) and the model-free
linear probability DiD (scientist and year fixed effects). For gender, the subgroup is defined on
both sides (e.g. Italian women vs control women); for region, Italian scientists in the region
vs all control scientists. ORCID-only re-estimates on the restricted sample.

Usage:
    python heterogeneity.py --input data/trajectories_world.csv --out results_world
"""
import argparse
import os

import gender_guesser.detector as gd
import numpy as np
import pandas as pd

import config
from estimate import Panel, run_did, summarise
from reduced_form import demean, ols_cluster

META = os.path.join(config.HERE, "data_meta")
COUNTRY_NAME = {"IT": "italy", "FR": "france", "DE": "germany", "ES": "spain"}
NORTH = {"piemonte", "piedmont", "valle d'aosta", "aosta valley", "lombardia", "lombardy", "trentino-alto adige",
         "trentino-south tyrol", "trentino-alto adige/südtirol", "veneto", "friuli-venezia giulia", "friuli venezia giulia",
         "liguria", "emilia-romagna", "emilia romagna"}
CENTRE = {"toscana", "tuscany", "umbria", "marche", "lazio", "latium"}
SOUTH = {"abruzzo", "molise", "campania", "puglia", "apulia", "basilicata", "calabria", "sicilia", "sicily",
         "sardegna", "sardinia"}


def first_name(name):
    for tok in str(name).replace("-", " ").split():
        t = tok.strip(".,")
        if len(t) > 2 and not t.isupper():
            return t
    return ""


def macro(region):
    r = str(region).strip().lower()
    return "North" if r in NORTH else "Centre" if r in CENTRE else "South" if r in SOUTH else ""


# Fallback when OpenAlex has no geo.region: university/research-centre city in the institution name.
CITY = {"North": ["milan", "milano", "turin", "torino", "politecnico di torino", "genoa", "genova", "bologna",
                  "padua", "padova", "venice", "venezia", "ca' foscari", "verona", "trieste", "sissa", "udine",
                  "trento", "bolzano", "pavia", "parma", "modena", "ferrara", "brescia", "bergamo", "insubria",
                  "bicocca", "piemonte orientale", "legnaro", "ispra", "aosta"],
        "Centre": ["rome", "roma", "sapienza", "tor vergata", "frascati", "florence", "firenze", "pisa",
                   "scuola normale", "sant'anna", "siena", "perugia", "ancona", "marche", "camerino", "urbino",
                   "macerata", "viterbo", "tuscia", "cassino", "lucca"],
        "South": ["naples", "napoli", "federico ii", "salerno", "caserta", "campania", "benevento", "sannio",
                  "bari", "lecce", "salento", "foggia", "potenza", "basilicata", "cosenza", "calabria", "catanzaro",
                  "reggio calabria", "palermo", "catania", "messina", "cagliari", "sassari", "l'aquila", "aquila",
                  "chieti", "pescara", "teramo", "gran sasso", "molise", "campobasso"]}


def macro_from_name(name):
    n = str(name).lower()
    for area, keys in CITY.items():
        if any(k in n for k in keys):
            return area
    return ""


def lpm(df, mask):
    d = df[mask & df.year.isin(config.PRE_YEARS + config.POST_YEARS)].reset_index(drop=True)
    x = ((d.group == "IT") & d.year.isin(config.POST_YEARS)).astype(float).to_numpy()[:, None]
    author, year = pd.factorize(d.author_id)[0], d.year.to_numpy()
    y = (d.action == "near").astype(float).to_numpy()[:, None]
    b, se = ols_cluster(demean(y, [author, year])[:, 0], demean(x, [author, year]), author)
    return 100 * b[0], 100 * (b[0] - 1.96 * se[0]), 100 * (b[0] + 1.96 * se[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--out", default=config.RESULTS_DIR)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    rng = np.random.default_rng(config.SEED)

    df = pd.read_csv(args.input)
    a = pd.read_csv(os.path.join(META, "authors.csv.gz"), dtype=str, encoding="utf-8").fillna("").set_index("id")
    inst = pd.read_csv(os.path.join(META, "institutions_it.csv.gz"), dtype=str, encoding="utf-8").fillna("")
    inst_region = {i: (macro(r) or macro_from_name(n)) for i, r, n in zip(inst.id, inst.region, inst.name)}
    det = gd.Detector(case_sensitive=False)
    home = df.drop_duplicates("author_id").set_index("author_id").country

    def gender(aid):
        if aid not in a.index:
            return ""
        g = det.get_gender(first_name(a.at[aid, "name"]), COUNTRY_NAME.get(home.get(aid), None))
        return "Women" if g in ("female", "mostly_female") else "Men" if g in ("male", "mostly_male") else ""

    def region(aid):
        if aid not in a.index or home.get(aid) != "IT":
            return ""
        for i, c in zip(a.at[aid, "inst_ids"].split("|"), a.at[aid, "inst_countries"].split("|")):
            if c == "IT" and inst_region.get(i):
                return inst_region[i]
        return ""

    ids = home.index
    meta = pd.DataFrame({"gender": [gender(i) for i in ids], "region": [region(i) for i in ids],
                         "orcid": [i in a.index and a.at[i, "orcid"] != "" for i in ids]}, index=ids)
    df = df.join(meta, on="author_id")
    print("Coverage:", meta.gender.ne("").mean().round(3), "gender;",
          meta[home == "IT"].region.ne("").mean().round(3), "region (Italy);", meta.orcid.mean().round(3), "ORCID")
    print(meta.assign(country=home).groupby("country").gender.value_counts().unstack().to_string())

    panel = Panel(df)
    pdf = panel.df
    rows = []
    subsets = [("Women", (pdf.gender == "Women").to_numpy()), ("Men", (pdf.gender == "Men").to_numpy())]
    for r in ("North", "Centre", "South"):
        subsets.append((f"Italy {r} vs all control", ((pdf.region == r) | (pdf.group == "CTRL")).to_numpy()))
    for name, mask in subsets:
        _, est, draws = run_did(panel, config.PRE_YEARS, config.POST_YEARS, config.GAMMA, args.n_boot, rng,
                                choice_mask=mask, label=name)
        s = summarise(est, draws).set_index("parameter").loc["theta_near"]
        b, lo, hi = lpm(pdf, pd.Series(mask))
        rows.append({"subgroup": name, "n_choices": int(mask.sum()), "irl_near": s.did, "irl_low": s.ci_low,
                     "irl_high": s.ci_high, "lpm_near_pp": b, "lpm_low": lo, "lpm_high": hi})

    orc = Panel(df[df.orcid].reset_index(drop=True))
    _, est, draws = run_did(orc, config.PRE_YEARS, config.POST_YEARS, config.GAMMA, args.n_boot, rng, label="ORCID")
    s = summarise(est, draws).set_index("parameter").loc["theta_near"]
    b, lo, hi = lpm(df, df.orcid)
    rows.append({"subgroup": "ORCID-only sample", "n_choices": int(df.orcid.sum()), "irl_near": s.did,
                 "irl_low": s.ci_low, "irl_high": s.ci_high, "lpm_near_pp": b, "lpm_low": lo, "lpm_high": hi})
    t = pd.DataFrame(rows)
    os.makedirs(args.out, exist_ok=True)
    t.to_csv(os.path.join(args.out, "heterogeneity.csv"), index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
