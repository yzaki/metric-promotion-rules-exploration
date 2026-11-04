"""Distance to each scientist's own habilitation bar, by competition sector (settore concorsuale).

The 2012 rule: a candidate for associate (full) professor had to exceed, on at least two of three
indicators, the median of current associate (full) professors in the same sector. We rebuild that rule in
our data, with the same measurement for candidates and reference groups: for Italian university staff matched
to the 2011 register (rank_2011_match.csv, with sector), indicators from articles published 2002-2011 in the
field (articles, citations, h-index of those articles; articles and citations scaled by 10/academic age when
the academic age in 2012 is below 10, as ANVUR did). Associates are compared with full professors of their
sector, researchers with associates (sector, or its macro-sector if fewer than 5 reference scientists).
Candidates are grouped by how many bars they exceed: 2-3 (met), 1 (one short), 0 (far below).

Reform effect on the nearby-move weight (and model-free) for each group vs France + Germany, paired scientist
bootstrap. Validation: correlation across sectors between our full-professor medians and ANVUR's published
2012 medians for full-professor candidates (Table 2, bibliometric sectors).

Usage:
    set CT_FIELD_ID=22 & python sector_thresholds.py --input data_field22/trajectories_world_career.csv --out results_field22_world_career
"""
import argparse
import os

import numpy as np
import pandas as pd

import build_trajectories as bt
import config
import irl
from estimate import Panel, fit_groups, did
from read_xlsx_raw import read as read_xlsx
from reduced_form import demean, ols_cluster

NEAR = irl.PARAMS.index("theta_near")
IND = ["articles", "citations", "h"]


def indicators(raw, authors, first_year):
    d = raw[raw.author_id.isin(authors) & raw.year.between(2002, 2011)].drop_duplicates(["author_id", "work_id"])
    g = d.groupby("author_id")
    t = pd.DataFrame({"articles": g.size(), "citations": g.cited_by_count.sum()})
    t["h"] = g.cited_by_count.apply(lambda c: int((np.sort(c.to_numpy())[::-1] >= np.arange(1, len(c) + 1)).sum()))
    age = (2012 - t.index.map(first_year)).to_numpy(dtype=float)
    scale = np.where(np.isfinite(age) & (age < 10) & (age > 0), 10 / np.maximum(age, 1), 1.0)
    t["articles"] *= scale
    t["citations"] *= scale
    return t


def anvur_table2():
    p = os.path.join(config.HERE, "data_meta", "anvur_medians", "tabella_2_mediane_candidati_abilitazione_po_bib_0.xlsx")
    d = read_xlsx(p)
    d = d[d[0].astype(str).str.match(r"^\d\d/[A-Z]\d$")].iloc[:, [0, 2, 3, 4]]
    d.columns = ["sc", "articles", "citations", "h"]
    for c in IND:
        d[c] = pd.to_numeric(d[c].astype(str).str.replace(",", "."), errors="coerce")
    return d.set_index("sc")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-boot", type=int, default=100)
    args = ap.parse_args()
    pre, post = config.PRE_YEARS, config.POST_YEARS

    match = pd.read_csv(os.path.join(args.out, "rank_2011_match.csv"), index_col=0)
    cs = pd.read_csv(os.path.join(config.HERE, "data_meta", "career_start.tsv.gz"), sep="\t").set_index("author_id").mag_first_year
    raw = bt.load_raw()
    ind = indicators(raw, set(match.index), cs).reindex(match.index).fillna(0)
    del raw
    m = match.join(ind)
    m["macro"] = m.sc_2011.astype(str).str[:4]

    def medians(rank):
        ref = m[m.rank_2011 == rank]
        by_sc = ref.groupby("sc_2011")[IND].median().assign(n=ref.groupby("sc_2011").size())
        by_mac = ref.groupby("macro")[IND].median().assign(n=ref.groupby("macro").size())
        return by_sc, by_mac

    rows = []
    for cand, ref_rank in (("associate professor", "full professor"), ("researcher", "associate professor")):
        by_sc, by_mac = medians(ref_rank)
        for a, r in m[m.rank_2011 == cand].iterrows():
            if r.sc_2011 in by_sc.index and by_sc.loc[r.sc_2011, "n"] >= 5:
                med = by_sc.loc[r.sc_2011]
            elif r.macro in by_mac.index and by_mac.loc[r.macro, "n"] >= 5:
                med = by_mac.loc[r.macro]
            else:
                continue
            rows.append({"author_id": a, "rank": cand, "n_above": int(sum(r[c] > med[c] for c in IND))})
    cands = pd.DataFrame(rows).set_index("author_id")
    cands["bar"] = np.select([cands.n_above >= 2, cands.n_above == 1], ["met", "one short"], "far below")
    print(pd.crosstab(cands["rank"], cands.bar), flush=True)

    # validation against ANVUR's published medians for full-professor candidates
    fp_sc, _ = medians("full professor")
    v = fp_sc[fp_sc.n >= 5].join(anvur_table2(), rsuffix="_anvur", how="inner")
    val = {c: v[c].corr(v[c + "_anvur"], method="spearman") for c in IND}
    print(f"Sectors compared with ANVUR Table 2: {len(v)}; Spearman correlations {val}", flush=True)

    df = pd.read_csv(args.input)
    df = df[df.year.isin(pre + post)].reset_index(drop=True)
    grp = cands.bar.rename("g")
    grp = pd.concat([grp, pd.Series("full professor", index=match.index[match.rank_2011 == "full professor"], name="g")])
    df["g"] = df.author_id.map(grp).where(df.group == "IT")
    groups = ["met", "one short", "far below", "full professor"]
    panels = {g: Panel(df[(df.group == "CTRL") | (df.g == g)].reset_index(drop=True)) for g in groups}
    point = {g: did(fit_groups(panels[g], pre, post, config.GAMMA))[NEAR] for g in groups}
    it_auth = df.author_id[df.g.isin(groups)].unique()
    ct_auth = df.author_id[df.group == "CTRL"].unique()
    rng = np.random.default_rng(config.SEED)
    draws = []
    for _ in range(args.n_boot):
        w = pd.concat([pd.Series(rng.multinomial(len(it_auth), np.full(len(it_auth), 1 / len(it_auth))), index=it_auth),
                       pd.Series(rng.multinomial(len(ct_auth), np.full(len(ct_auth), 1 / len(ct_auth))), index=ct_auth)])
        draws.append({g: did(fit_groups(panels[g], pre, post, config.GAMMA,
                                        weights=panels[g].df.author_id.map(w).to_numpy(dtype=float)))[NEAR] for g in groups})
    draws = pd.DataFrame(draws)
    for k, (a, b) in {"one short minus met": ("one short", "met"), "below (0-1) minus met": (None, "met")}.items():
        if a:
            draws[k], point[k] = draws[a] - draws[b], point[a] - point[b]
        else:
            draws[k] = (draws["one short"] + draws["far below"]) / 2 - draws[b]
            point[k] = (point["one short"] + point["far below"]) / 2 - point[b]
    out = []
    for g in groups + ["one short minus met", "below (0-1) minus met"]:
        row = {"group": g, "irl_near": point[g], "irl_low": np.percentile(draws[g], 2.5),
               "irl_high": np.percentile(draws[g], 97.5)}
        if g in groups:
            sub = panels[g].df
            d = ((sub.group == "IT") & sub.year.isin(post)).astype(float).to_numpy()
            author = pd.factorize(sub.author_id)[0]
            fe = [author, sub.year.to_numpy()]
            y = (sub.action == "near").astype(float).to_numpy()
            b, se = ols_cluster(demean(y[:, None], fe)[:, 0], demean(d[:, None], fe), author)
            row.update(lpm_near_pp=100 * b[0], lpm_low=100 * (b[0] - 1.96 * se[0]), lpm_high=100 * (b[0] + 1.96 * se[0]),
                       n_italian=int(sub.author_id[sub.group == "IT"].nunique()))
        out.append(row)
    t = pd.DataFrame(out)
    t["validation_spearman_articles"], t["validation_spearman_citations"], t["validation_spearman_h"] = (
        val["articles"], val["citations"], val["h"])
    t["validation_n_sectors"] = len(v)
    t.to_csv(os.path.join(args.out, "sector_thresholds.csv"), index=False)
    print(t.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
