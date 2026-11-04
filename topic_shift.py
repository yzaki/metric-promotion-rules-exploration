"""Where did Italian scientists' work shift after the reform? (descriptive)

Using the same author-year sample as build_trajectories.py and the WORLD-WIDE citation
potential (fetch_world_citations.py), reports:
  1. share of author-years in low / middle / high citation-potential topics, Italy vs
     control, before vs after, and the difference-in-differences (percentage points);
  2. the topics whose share of Italian author-years rose or fell most relative to control.

Usage:
    set CT_FIELD_ID=22 && python topic_shift.py
"""
import argparse
import os

import numpy as np
import pandas as pd

import config
from build_trajectories import (add_state, assign_countries, author_years,
                                citation_potential_world, load_raw)
from fetch_openalex import BASE, get


def topic_names(ids):
    names = {}
    for t in ids:
        try:
            names[t] = get(f"{BASE}/topics/{t}", {"api_key": config.OPENALEX_API_KEY},
                           tries=3).get("display_name")
        except Exception:
            names[t] = ""
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--top", type=int, default=12)
    args = ap.parse_args()

    df = load_raw()
    pot = citation_potential_world(df)
    country = assign_countries(df)
    ay = author_years(df, country)
    ay = ay[ay.groupby("author_id").year.transform("size") >= config.MIN_ACTIVE_YEARS]
    ay = add_state(ay.reset_index(drop=True), pot)
    ay["group"] = np.where(ay.country == config.TREATED, "IT", "CTRL")
    ay["period"] = np.select([ay.year.isin(config.PRE_YEARS), ay.year.isin(config.POST_YEARS)],
                             ["before", "after"], "")
    ay = ay[ay.period != ""]

    tiers = (ay.groupby(["group", "period"]).tier.value_counts(normalize=True)
             .unstack().rename(columns={0: "low", 1: "middle", 2: "high"}) * 100)
    did = ((tiers.loc[("IT", "after")] - tiers.loc[("IT", "before")])
           - (tiers.loc[("CTRL", "after")] - tiers.loc[("CTRL", "before")]))
    print("Share of author-years by world citation tier (%):\n", tiers.round(1).to_string())
    print("\nDiD (Italy vs control, after minus before, pp):\n", did.round(2).to_string())

    share = ay.groupby(["group", "period"]).topic_id.value_counts(normalize=True).unstack(["group", "period"])
    share = share.fillna(0) * 100
    change = ((share["IT", "after"] - share["IT", "before"])
              - (share["CTRL", "after"] - share["CTRL", "before"])).rename("did_pp")
    pot_t = pot["topic_id"]
    mean_pot = (pot_t[pot_t.year.isin(config.PRE_YEARS + config.POST_YEARS)]
                .groupby("topic_id").potential_topic_id.mean().rename("world_citation_potential"))
    table = pd.concat([change, share["IT", "before"].rename("IT_before"), share["IT", "after"].rename("IT_after"),
                       mean_pot], axis=1).dropna(subset=["did_pp"])
    picks = pd.concat([table.nlargest(args.top, "did_pp"), table.nsmallest(args.top, "did_pp")])
    picks["name"] = picks.index.map(topic_names(picks.index))
    print("\nTopics gaining / losing most Italian share relative to control:\n",
          picks.round(3).to_string())
    print("\nCorrelation across topics: Italian share change vs world citation potential:",
          round(table.did_pp.corr(table.world_citation_potential), 3))

    os.makedirs(config.RESULTS_DIR, exist_ok=True)
    tiers.to_csv(os.path.join(config.RESULTS_DIR, "topic_shift_tiers.csv"))
    table.sort_values("did_pp").to_csv(os.path.join(config.RESULTS_DIR, "topic_shift_topics.csv"))
    picks.to_csv(os.path.join(config.RESULTS_DIR, "topic_shift_top.csv"))


if __name__ == "__main__":
    main()
