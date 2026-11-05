"""Export (author, paper) pairs and surnames of every sampled scientist, for matching to MAG authors
in SciSciNet (true career start). OpenAlex W-ids of MAG-era works equal MAG PaperIDs.

Writes data_meta/author_papers.tsv.gz (author_id, paper_id) and data_meta/author_names.tsv.gz
(author_id, surname, first_initial, first_year_in_data).

Usage:
    python export_author_papers.py
"""
import glob
import os
import unicodedata

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = {"31": "data", "22": "data_field22", "13": "data_field13", "20": "data_field20", "16": "data_field16"}


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(ch if ch.isalpha() or ch == " " else " " for ch in s).split()


def main():
    import sys
    out = os.path.join(HERE, "data_meta")
    sample, pairs = set(), []
    for f, d in FIELDS.items():
        for t in glob.glob(os.path.join(HERE, d, "trajectories*.csv")):
            sample |= set(pd.read_csv(t, usecols=["author_id"]).author_id)
    print(f"Sampled scientists (any field, any specification): {len(sample):,}")
    if "--names-only" in sys.argv:   # reuse the exported pairs
        p = pd.read_csv(os.path.join(out, "author_papers.tsv.gz"), sep="\t")
        first = None
    else:
        for f, d in FIELDS.items():
            for g in glob.glob(os.path.join(HERE, d, "raw", "works_*.csv.gz")):
                w = pd.read_csv(g, usecols=["work_id", "year", "author_id"])
                pairs.append(w[w.author_id.isin(sample)].drop_duplicates(["work_id", "author_id"]))
        p = pd.concat(pairs).drop_duplicates(["work_id", "author_id"])
        first = p.groupby("author_id").year.min().rename("first_year_in_data")
        p["paper_id"] = p.work_id.str.lstrip("W").astype("int64")
        p[["author_id", "paper_id"]].to_csv(os.path.join(out, "author_papers.tsv.gz"), sep="\t", index=False)
        first.to_csv(os.path.join(out, "first_year_in_data.csv"))
    if first is None:
        fy = os.path.join(out, "first_year_in_data.csv")
        first = (pd.read_csv(fy, index_col=0).iloc[:, 0] if os.path.exists(fy) else
                 pd.read_csv(os.path.join(out, "author_names.tsv.gz"), sep="\t").set_index("author_id").first_year_in_data)

    a = pd.read_csv(os.path.join(out, "authors.csv.gz"), usecols=["id", "name"]).set_index("id").name
    rows = []
    for aid in sample:
        toks = norm(a.get(aid, ""))
        rows.append({"author_id": aid, "full_name": " ".join(toks), "surname": toks[-1] if toks else "",
                     "first_initial": toks[0][0] if toks else "", "first_year_in_data": first.get(aid)})
    n = pd.DataFrame(rows)
    n.to_csv(os.path.join(out, "author_names.tsv.gz"), sep="\t", index=False)
    print(f"{len(p):,} author-paper pairs; {(n.surname != '').mean():.1%} with a name")


if __name__ == "__main__":
    main()
