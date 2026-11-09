"""Was the November 2026 OpenAlex topic reclassification balanced between Italy and France + Germany?

For physics, engineering and biochemistry, compares the Italian, French and German works fetched on 5 November
(<raw>_ITFRDE_5nov) with those fetched on 8 November (<raw>): an article "left" the field if it is in the
5 November files but not the 8 November ones, and "entered" if the reverse. Article-level linear probability
model of leaving (and entering) on Italy x after (2013-18 vs 2004-09) with country and year fixed effects,
standard errors clustered by topic (whole topics were moved between fields); percentage points.
Usage: python reclass_check.py
"""
import glob
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = [("Physics", "data"), ("Engineering", "data_field22"), ("Biochemistry", "data_field13"), ("Chemistry", "data_field16")]
# Old files: the 5 Nov re-download for three fields; for chemistry, the authors' original download of 5 Nov 2026
# (03:55-05:17, log fetch_field16.txt), supplied with the original working repository.
ORIG = os.path.join(HERE, "..", "..", "original_repo", "Citation Targets", "citation-targets-irl")
PRE, POST = range(2004, 2010), range(2013, 2019)


def ids(d, sub, cc):
    out = []
    base = os.path.join(ORIG, d, "raw") if (d == "data_field16" and sub == "raw_ITFRDE_5nov") else os.path.join(HERE, d, sub)
    for f in glob.glob(os.path.join(base, f"works_{cc}_*.csv.gz")):
        w = pd.read_csv(f, usecols=["work_id", "year", "topic_id", "subfield_id"]).drop_duplicates("work_id")
        out.append(w)
    return pd.concat(out).assign(country=cc)


def did(df, y):
    df = df[df.year.isin(list(PRE) + list(POST))].copy()
    df["it_post"] = ((df.country == "IT") & df.year.isin(POST)).astype(float)
    X = pd.get_dummies(df[["country", "year"]].astype(str), drop_first=True).astype(float)
    X.insert(0, "it_post", df.it_post.to_numpy()); X.insert(0, "const", 1.0)
    Xv, yv = X.to_numpy(), df[y].to_numpy(float)
    XtX = np.linalg.inv(Xv.T @ Xv); b = XtX @ Xv.T @ yv; u = yv - Xv @ b
    # standard errors clustered by topic: OpenAlex moved whole topics between fields, so reassignment is
    # correlated within topic
    g = pd.factorize(df.topic_id)[0]
    sc = pd.DataFrame(Xv * u[:, None]).groupby(g).sum().to_numpy()
    G = sc.shape[0]
    V = XtX @ (sc.T @ sc) @ XtX * G / (G - 1)
    Vr = XtX @ (Xv.T * u ** 2) @ Xv @ XtX   # heteroskedasticity-robust, for comparison
    return 100 * b[1], 100 * np.sqrt(V[1, 1]), 100 * np.sqrt(Vr[1, 1])


def main():
    rows = []
    for name, d in FIELDS:
        old = pd.concat(ids(d, "raw_ITFRDE_5nov", c) for c in ("IT", "FR", "DE"))
        new = pd.concat(ids(d, "raw", c) for c in ("IT", "FR", "DE"))
        old["left"] = ~old.set_index(["country", "work_id"]).index.isin(new.set_index(["country", "work_id"]).index)
        new["entered"] = ~new.set_index(["country", "work_id"]).index.isin(old.set_index(["country", "work_id"]).index)
        for lab, df, y in (("left the field", old, "left"), ("entered the field", new, "entered")):
            b, se, se_r = did(df, y)
            m = lambda c, yrs: 100 * df[c & df.year.isin(yrs)][y].mean()
            it = df.country == "IT"
            rows.append({"field": name, "outcome": lab, "beta_pp": b, "ci_low_pp": b - 1.96 * se, "ci_high_pp": b + 1.96 * se,
                         "ci_low_robust_pp": b - 1.96 * se_r, "ci_high_robust_pp": b + 1.96 * se_r,
                         "IT_before_pct": m(it, PRE), "IT_after_pct": m(it, POST),
                         "FRDE_before_pct": 100 * df[(df.country != "IT") & df.year.isin(PRE)][y].mean(),
                         "FRDE_after_pct": 100 * df[(df.country != "IT") & df.year.isin(POST)][y].mean()})
            print(rows[-1], flush=True)
        tl = old.groupby("topic_id")["left"].mean()
        rows.append({"field": name, "outcome": "topics with all or none of their articles leaving (%)",
                     "beta_pp": 100 * ((tl == 0) | (tl == 1)).mean()})
        rows.append({"field": name, "outcome": "articles in topics that left entirely (% of those that left)",
                     "beta_pp": 100 * old[old.topic_id.map(tl) == 1]["left"].sum() / max(old["left"].sum(), 1)})
        # articles in the field on both dates: same topic? same subfield? (subfield changes move a choice between
        # nearby move and distant jump)
        both = old.drop_duplicates("work_id").merge(new.drop_duplicates("work_id"), on="work_id", suffixes=("_old", "_new"))
        rows.append({"field": name, "outcome": "stable articles: topic changed (%)",
                     "beta_pp": 100 * (both.topic_id_old != both.topic_id_new).mean()})
        rows.append({"field": name, "outcome": "stable articles: subfield changed (%)",
                     "beta_pp": 100 * (both.subfield_id_old != both.subfield_id_new).mean()})
        print(rows[-2], rows[-1], flush=True)
    os.makedirs(os.path.join(HERE, "results_downloads"), exist_ok=True)
    pd.DataFrame(rows).to_csv(os.path.join(HERE, "results_downloads", "reclass_check.csv"), index=False)


if __name__ == "__main__":
    main()
