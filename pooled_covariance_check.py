"""How much do pooled return estimates change when scientists who appear in several fields are accounted for?

For Italy, Russia and India (each vs France + Germany) and for nearby moves, all returns and gap returns: the
inverse-variance pool over the four fields, with its standard error (a) assuming the fields are independent (as in
Fig. 4) and (b) from each scientist's influence summed across fields (first_entry.py --save-influence).
Writes results_downloads/pooled_covariance_check.csv.
Usage: python pooled_covariance_check.py
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FIELDS = ["results_world", "results_field22_world", "results_field13_world", "results_field16_world"]


def main():
    rows = []
    for country, suf in (("Italy", ""), ("Russia", "_RU"), ("India", "_IN")):
        for outcome in ("near", "near_return", "near_gap_return"):
            b, se, psis = [], [], []
            for f in FIELDS:
                t = pd.read_csv(os.path.join(HERE, f + suf, "first_entry.csv"))
                r = t[(t.definition == t.definition.iloc[0]) & (t.outcome == outcome)].iloc[0]
                b.append(r.beta_pp); se.append((r.ci_high_pp - r.ci_low_pp) / 3.92)
                i = pd.read_csv(os.path.join(HERE, f + suf, "first_entry_influence.csv.gz"))
                psis.append(i[i.outcome == outcome].set_index("author_id").psi_pp)
            b, se = np.array(b), np.array(se)
            w = (1 / se ** 2) / (1 / se ** 2).sum()
            psi = pd.concat([p * wk for p, wk in zip(psis, w)]).groupby(level=0).sum()
            g = len(psi)
            se_infl = np.sqrt((psi ** 2).sum() * g / (g - 1))
            se_ind = np.sqrt(1 / (1 / se ** 2).sum())
            rows.append({"country": country, "outcome": outcome, "pooled_pp": (w * b).sum(), "se_independent": se_ind,
                         "se_with_overlap": se_infl, "ratio": se_infl / se_ind,
                         "scientists_in_2plus_fields": int((pd.concat(psis).index.value_counts() > 1).sum())})
    t = pd.DataFrame(rows)
    os.makedirs(os.path.join(HERE, "results_downloads"), exist_ok=True)
    t.to_csv(os.path.join(HERE, "results_downloads", "pooled_covariance_check.csv"), index=False)
    print(t.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
