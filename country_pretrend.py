"""Model-free annual pre-trend test for Russia and India (the test Table S33 applies to Italy).

For each field: linear probability of a nearby move on treated x year (reference 2009) with scientist and
year fixed effects, clustered by scientist; joint Wald test that all pre-2009 coefficients are zero.
country_model_free_pretrend.csv uses the choice files saved by first_entry.py --treated, which hold the
before and after years only (the version first reported); country_model_free_pretrend_all_years.csv
collects the test exactly as applied to Italy (all years 2004-18, every move type) from
first_entry.py --treated <C> --timing.
Also writes the Russia leave-out estimate: model-free nearby moves and returns pooled (inverse-variance)
over the fields that pass the plan's pre-trend rule (physics, biochemistry), from the stacked results of
a given package (--orig for the earlier download).
Usage: python country_pretrend.py --orig <earlier package>
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy import stats

from reduced_form import demean

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = [("Physics", "data"), ("Engineering", "data_field22"), ("Biochemistry", "data_field13"), ("Chemistry", "data_field16")]


def pretest(ch):
    ch = ch[ch.year.between(2004, 2018)].reset_index(drop=True)
    it = (ch.group == "IT").to_numpy()
    yr = ch.year.to_numpy()
    years = [v for v in sorted(set(yr)) if v != 2009]   # saved choice files hold the before and after years only
    a = pd.factorize(ch.author_id)[0]
    g = [a, yr]
    X = np.column_stack([(it & (yr == v)).astype(float) for v in years])
    Xd = demean(X, g)
    yd = demean((ch.action == "near").astype(float).to_numpy()[:, None], g)[:, 0]
    XtX = np.linalg.inv(Xd.T @ Xd)
    b = XtX @ Xd.T @ yd
    u = yd - Xd @ b
    sc = pd.DataFrame(Xd * u[:, None]).groupby(a).sum().to_numpy()
    G = sc.shape[0]
    V = XtX @ (sc.T @ sc * G / (G - 1)) @ XtX
    pre = [k for k, v in enumerate(years) if v < 2009]
    return 1 - stats.chi2.cdf(b[pre] @ np.linalg.inv(V[np.ix_(pre, pre)]) @ b[pre], len(pre))


def leaveout(base):
    t = pd.read_csv(os.path.join(base, "results_russia", "russia_stacked.csv"))
    out = {}
    for test in ("I1 nearby move", "I3 near return"):
        r = t[(t.test == test) & t.scope.isin(["Physics", "Biochemistry"])]
        se = (r.ci_high_pp - r.ci_low_pp) / 3.92
        w = 1 / se ** 2
        b = (w * r.beta_pp).sum() / w.sum()
        e = np.sqrt(1 / w.sum())
        out[test] = (b, b - 1.96 * e, b + 1.96 * e)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--orig", default=os.path.join(HERE, "results_original"))
    args = ap.parse_args()
    rows = []
    for country, folder in (("Russia", "results_russia"), ("India", "results_india")):
        for name, d in FIELDS:
            ch = pd.read_csv(os.path.join(HERE, folder, f"choices_{d}.csv.gz"), usecols=["author_id", "group", "year", "action"])
            rows.append({"country": country, "field": name, "pretrend_wald_p": pretest(ch)})
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(os.path.join(HERE, "results_downloads", "country_model_free_pretrend.csv"), index=False)
    # the same test as Table S33 for Italy (all years 2004-18, including the 2010-12 transition), for every move
    # type, from first_entry.py --treated <C> --timing (run_round9_pretest.sh)
    full = []
    for country, c in (("Russia", "RU"), ("India", "IN")):
        for name, d in FIELDS:
            base = "results" if d == "data" else "results_field" + d.split("field")[1]
            t = pd.read_csv(os.path.join(HERE, f"{base}_world_{c}", "first_entry_timing.csv"))
            for _, r in t.iterrows():
                full.append({"country": country, "field": name, "outcome": r.outcome, "pretrend_wald_p": r.pretrend_wald_p,
                             "placebo2007_pp": r.placebo2007_pp, "placebo_ci_low_pp": r.placebo_ci_low_pp,
                             "placebo_ci_high_pp": r.placebo_ci_high_pp})
    pd.DataFrame(full).to_csv(os.path.join(HERE, "results_downloads", "country_model_free_pretrend_all_years.csv"), index=False)
    lo = []
    for lab, base in (("earlier download", args.orig), ("latest download", HERE)):
        for test, v in leaveout(base).items():
            lo.append({"download": lab, "test": test, "estimate_pp": v[0], "ci_low_pp": v[1], "ci_high_pp": v[2]})
    pd.DataFrame(lo).to_csv(os.path.join(HERE, "results_downloads", "russia_leaveout.csv"), index=False)
    print(pd.DataFrame(lo).round(2).to_string(index=False))


if __name__ == "__main__":
    main()
