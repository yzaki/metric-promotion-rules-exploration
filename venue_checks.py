"""Timing checks for the journal outcomes (exploratory): 2007 placebo and event study, from the saved panel.

Reads results_venues/panel_<treated>.csv.gz (venues.py). For each outcome: the 2007 placebo (2004-06 vs 2007-09)
of treated vs France + Germany, and an event study in two-year windows relative to 2008-09; with --groups, the
same for covered minus not-covered scientists of the treated country. Model-free, scientist and year fixed
effects, standard errors clustered by scientist (india_stacked.fit).

Usage:
    python venue_checks.py --treated RU --groups results_russia/russia_groups.csv --covered-label 5-100
"""
import argparse
import os

import numpy as np
import pandas as pd

from india_stacked import fit

HERE = os.path.dirname(os.path.abspath(__file__))
WINDOWS = {"2004-05": (2004, 2005), "2006-07": (2006, 2007), "2013-14": (2013, 2014),
           "2015-16": (2015, 2016), "2017-18": (2017, 2018)}           # reference 2008-09
OUTCOMES = ["bottom_quartile_yr", "top_quartile_yr", "journal_pct_yr", "bottom_quartile_yr_intl",
            "bottom_quartile", "fee_oa"]


def who(df, k, covered):
    """t: treated-country scientists; c: covered; n: not covered."""
    if k == "t":
        return df.group == "IT"
    return df.g == (covered if k == "c" else "not covered")


def estimates(s, oc, treat_masks):
    """treat_masks: {name: boolean Series}; returns {name: (b, lo, hi)} and, for two masks, their difference."""
    cols = []
    for k, m in treat_masks.items():
        s[k] = m.astype(float)
        cols.append(k)
    b, V = fit(s, oc, cols)
    out = {k: (b[i], b[i] - 1.96 * np.sqrt(V[i, i]), b[i] + 1.96 * np.sqrt(V[i, i])) for i, k in enumerate(cols)}
    return out, b, V


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--treated", required=True)
    ap.add_argument("--groups", default=None)
    ap.add_argument("--covered-label", default="5-100")
    ap.add_argument("--out", default=os.path.join(HERE, "results_venues"))
    args = ap.parse_args()
    A = pd.read_csv(os.path.join(args.out, f"panel_{args.treated}.csv.gz"))
    if args.groups:
        A["g"] = A.author_id.map(pd.read_csv(args.groups).set_index("author_id").group)
    rows = []
    for oc in OUTCOMES:
        base = A.dropna(subset=[oc]).reset_index(drop=True)
        # (1) treated vs control; (2) covered vs not covered (control scientists kept as the comparison)
        specs = [("treated vs FR+DE", base, {"t": base.group == "IT"})]
        if args.groups:
            B = base[(base.group == "CTRL") | base.g.notna()].reset_index(drop=True)
            specs.append((f"{args.covered_label} minus not covered", B,
                          {"c": B.g == args.covered_label, "n": B.g == "not covered"}))
        for label, s, groups in specs:
            # placebo: 2004-06 vs 2007-09
            p = s[s.year <= 2009].reset_index(drop=True)
            masks = {f"{k}_pl": who(p, k, args.covered_label) & (p.year >= 2007) for k in groups}
            est, b, V = estimates(p.copy(), oc, masks)
            if len(masks) == 2:
                c = np.array([1.0, -1.0]); dv, ds = c @ b, np.sqrt(c @ V @ c); r = (dv, dv - 1.96 * ds, dv + 1.96 * ds)
            else:
                r = next(iter(est.values()))
            rows.append({"outcome": oc, "comparison": label, "test": "placebo 2007", "window": "", "est": r[0], "lo": r[1], "hi": r[2]})
            # event study relative to 2008-09
            masks = {}
            for w, (y0, y1) in WINDOWS.items():
                inw = s.year.between(y0, y1)
                for k in groups:
                    masks[f"{k}_{w}"] = who(s, k, args.covered_label) & inw
            est, b, V = estimates(s.copy(), oc, masks)
            names = list(masks)
            for w in WINDOWS:
                if len(groups) == 2:
                    i, j = names.index(f"c_{w}"), names.index(f"n_{w}")
                    c = np.zeros(len(names)); c[i], c[j] = 1, -1
                    dv, ds = c @ b, np.sqrt(c @ V @ c); r = (dv, dv - 1.96 * ds, dv + 1.96 * ds)
                else:
                    r = est[f"t_{w}"]
                rows.append({"outcome": oc, "comparison": label, "test": "event study", "window": w, "est": r[0], "lo": r[1], "hi": r[2]})
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(args.out, f"venue_checks_{args.treated}.csv"), index=False)
    pd.set_option("display.width", 200)
    print(t.assign(est=t.est.round(4), lo=t.lo.round(4), hi=t.hi.round(4)).to_string(index=False))


if __name__ == "__main__":
    main()
