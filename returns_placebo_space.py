"""Are the declines in gap returns specific to Italy? (model-free DiD, 2004-09 vs 2013-18)

Builds yearly choices for scientists in Italy, France, Germany, Spain, the Netherlands and Portugal (80%
country rule across the six), flags nearby moves, gap returns and first entries as in first_entry.py, and
estimates the DiD (scientist + year FE, clustered by scientist) for:
  - each country treated as if reformed against the other non-Italian countries (Italy against all five);
  - Italy against Spain + Netherlands + Portugal only (France and Germany left out), and against the
    Netherlands + Portugal only (Spain also left out, because of its own 2015 accreditation reform).
Usage: CT_FIELD_ID=22 python returns_placebo_space.py
"""
import os

import numpy as np
import pandas as pd

import build_trajectories as bt
import config
from returns_checks import did, choices, gap_flags

C6 = ["IT", "FR", "DE", "ES", "NL", "PT"]


def main():
    config.CONTROLS = C6[1:]
    config.COUNTRIES = C6
    df = bt.load_raw()
    country = bt.assign_countries(df)
    ay = bt.author_years(df, country)
    ay = ay[ay.groupby("author_id").year.transform("size") >= config.MIN_ACTIVE_YEARS].reset_index(drop=True)
    d = df[df.author_id.isin(set(ay.author_id))]
    pres = set(zip(d.author_id, d.topic_id, d.year))
    ch = choices(ay)
    f = gap_flags(ch, pres)
    ch["gap"] = f["gap>=1"]
    ch["ret"] = f["all returns"]
    ch["new"] = ch.near & ~f["all returns"]
    rows = []
    for c in C6:
        sub = ch if c == "IT" else ch[ch.country != "IT"]
        sub = sub.assign(group=np.where(sub.country == c, "IT", "CTRL")).reset_index(drop=True)
        for o in ("near", "gap", "ret", "new"):
            rows.append(("each country as reformed", c, o, *did(sub, sub[o])))
    for design, ctrl in (("Italy vs ES+NL+PT", ["ES", "NL", "PT"]), ("Italy vs NL+PT", ["NL", "PT"])):
        sub = ch[ch.country.isin(["IT"] + ctrl)].reset_index(drop=True)
        sub = sub.assign(group=np.where(sub.country == "IT", "IT", "CTRL"))
        for o in ("near", "gap", "ret", "new"):
            rows.append((design, "IT", o, *did(sub, sub[o])))
    t = pd.DataFrame(rows, columns=["design", "treated", "outcome", "beta_pp", "ci_low_pp", "ci_high_pp"])
    t["rank"] = t[t.design == "each country as reformed"].groupby("outcome").beta_pp.rank()
    t.to_csv(os.path.join(config.RESULTS_DIR + "_world", "returns_placebo_space.csv"), index=False)
    print(t.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
