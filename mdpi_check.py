"""Do broad-scope MDPI journals drive the result? (journal name is an input to OpenAlex's topic classifier)

Reports the MDPI share of articles by country and period, then re-estimates the model-free DiD for nearby
moves and gap returns after removing every article in an MDPI journal (MDPI sources from OpenAlex,
data_meta/mdpi_sources.txt; journal of each article from data*/venues, decision years 2004-09 and 2013-18 plus 2019;
articles in other years are kept, where MDPI's share was small).
Usage: CT_FIELD_ID=22 python mdpi_check.py
"""
import glob
import os

import pandas as pd

import build_trajectories as bt
import config
from returns_checks import did, choices, gap_flags


def main():
    mdpi = set(open(os.path.join(config.HERE, "data_meta", "mdpi_sources.txt")).read().split())
    ven = pd.concat(pd.read_csv(f, usecols=["work_id", "source_id"]) for f in glob.glob(os.path.join(config.DATA_DIR, "venues", "venues_*.csv.gz"))
                    if os.path.basename(f).split("_")[1] in config.COUNTRIES).drop_duplicates("work_id")
    is_mdpi = set(ven.work_id[ven.source_id.isin(mdpi)])
    df = bt.load_raw()
    country = bt.assign_countries(df)
    rows = []
    w = df.drop_duplicates(["work_id", "author_id"]).assign(c=lambda x: x.author_id.map(country)).dropna(subset=["c"])
    w = w[w.year.isin(config.PRE_YEARS + config.POST_YEARS)].drop_duplicates(["work_id", "c"])
    w["period"] = w.year.isin(config.POST_YEARS).map({True: "after", False: "before"})
    share = w.assign(m=w.work_id.isin(is_mdpi)).groupby(["c", "period"]).m.mean().unstack()
    for spec, data in (("all articles", df), ("without MDPI articles", df[~df.work_id.isin(is_mdpi)])):
        ay = bt.author_years(data, country)
        ay = ay[ay.groupby("author_id").year.transform("size") >= config.MIN_ACTIVE_YEARS].reset_index(drop=True)
        d = data[data.author_id.isin(set(ay.author_id))]
        pres = set(zip(d.author_id, d.topic_id, d.year))
        ch = choices(ay)
        f = gap_flags(ch, pres)
        rows.append((spec, "near", *did(ch, ch.near)))
        rows.append((spec, "gap return", *did(ch, f["gap>=1"])))
    t = pd.DataFrame(rows, columns=["spec", "outcome", "beta_pp", "ci_low_pp", "ci_high_pp"])
    for c in share.index:
        for p in ("before", "after"):
            t.loc[len(t)] = ["MDPI share of articles", f"{c} {p}", 100 * share.loc[c, p], None, None]
    t.to_csv(os.path.join(config.RESULTS_DIR + "_world", "mdpi_check.csv"), index=False)
    print(t.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
