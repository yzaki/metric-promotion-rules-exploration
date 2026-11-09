"""Every pre-specified test and headline estimate on both OpenAlex downloads.

Original download: 3-5 November 2026 (the data the analysis plans were written against), results in
ORIG (the package as first shipped). Latest download: 7-8 November 2026, results in this folder.
Writes results_downloads/download_comparison.csv.

Usage: python download_comparison.py   (earlier-download results are shipped in results_original/)
"""
import argparse
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))


def irl(base, folder, name="did_main.csv", p="theta_near"):
    f = os.path.join(base, folder, name)
    if not os.path.exists(f):
        return None
    r = pd.read_csv(f).set_index("parameter").loc[p]
    return r.did, r.ci_low, r.ci_high


def stacked(base, fn, test, scope="All four fields"):
    f = os.path.join(base, fn)
    t = pd.read_csv(f)
    r = t[(t.test == test) & (t.scope == scope)]
    return None if r.empty else tuple(r.iloc[0][["beta_pp", "ci_low_pp", "ci_high_pp"]])


def fe(base, folder, outcome):
    f = os.path.join(base, folder, "first_entry.csv")
    if not os.path.exists(f):
        return None
    t = pd.read_csv(f)
    r = t[(t.definition == t.definition.iloc[0]) & (t.outcome == outcome)]
    return None if r.empty else tuple(r.iloc[0][["beta_pp", "ci_low_pp", "ci_high_pp"]])


def other(base, fn, outcome, scale=100):
    f = os.path.join(base, fn)
    t = pd.read_csv(f)
    r = t[(t.outcome == outcome) & (t.scope == "All four fields")]
    return None if r.empty else tuple(scale * r.iloc[0][["did", "ci_low", "ci_high"]])


def career_order(base):
    f = os.path.join(base, "results_field13_world_career", "did_by_career_main.csv")
    t = pd.read_csv(f).query("parameter == 'theta_near'").set_index("career_stage")
    return t.loc["0-5 years"].did, t.loc["6-15 years"].did, t.loc["16+ years"].did


def russia_rule(base):
    """Plan rule (our reading of "the fields that drive it"): R1 supported, R2 holds, and the decline is not
    explained by pre-trends in the fields that drive it (fields with a significant model-free decline; pre-trend = 2004-05 or 2006-07 excludes 0
    with both FR+DE and FR+DE+ES)."""
    st = pd.read_csv(os.path.join(base, "results_russia", "russia_stacked.csv"))
    g = lambda t, sc="All four fields": st[(st.test == t) & (st.scope == sc)].iloc[0]
    r1, r2 = g("I1 nearby move"), g("I2 placebo 2007")
    drive = [f for f in ("Physics", "Engineering", "Biochemistry", "Chemistry") if g("I1 nearby move", f).ci_high_pp < 0]
    folder = {"Physics": "results", "Engineering": "results_field22", "Biochemistry": "results_field13", "Chemistry": "results_field16"}
    def pretrend(f):
        out = []
        for suf in ("_world_RU", "_world_RU_es"):
            e = pd.read_csv(os.path.join(base, folder[f] + suf, "event_study.csv")).query("parameter == 'theta_near'").set_index("window")
            out.append(any(e.loc[w].ci_low > 0 or e.loc[w].ci_high < 0 for w in ("2004-2005", "2006-2007")))
        return all(out)
    bad = [f for f in drive if pretrend(f)]
    ok = r1.ci_high_pp < 0 and r2.ci_low_pp <= 0 <= r2.ci_high_pp and drive and not bad
    return ok, drive, bad


def verdict(rule, x):
    if x is None:
        return "--"
    b, lo, hi = x
    if rule == "chem":   # chemistry plan C3-C5
        return "supported" if hi < 0 else ("consistent" if b < 0 else "not supported")
    return {"neg": "met" if hi < 0 else "not met", "null": "met" if lo <= 0 <= hi else "not met",
            "sig": "significant" if (hi < 0 or lo > 0) else "n.s.", "none": ""}[rule]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--orig", default=os.path.join(HERE, "results_original"),
                    help="result files of the earlier download (shipped in results_original/)")
    args = ap.parse_args()
    O, N = args.orig, HERE
    rows = []

    def add(plan, test, rule, getter):
        a, b = getter(O), getter(N)
        rows.append({"plan": plan, "test": test, "orig": a, "latest": b,
                     "verdict_orig": verdict(rule, a), "verdict_latest": verdict(rule, b)})

    # Biochemistry plan (4 Nov): study-country citation measure, FR+DE
    add("Biochemistry (4 Nov)", "H-R1 nearby-move weight", "neg", lambda B: irl(B, "results_field13"))
    add("Biochemistry (4 Nov)", "H-R2 placebo 2007", "null", lambda B: irl(B, "results_field13", "did_placebo_2007.csv"))
    add("Economics (4 Nov)", "nearby-move weight", "none", lambda B: irl(B, "results_field20"))
    add("Economics (4 Nov)", "placebo 2007", "null", lambda B: irl(B, "results_field20", "did_placebo_2007.csv"))
    # Biochemistry H-R3: decline larger at 0-5 and 6-15 than at 16+ (true career start)
    for B, key in ((O, "orig"), (N, "latest")):
        pass
    co, cn = career_order(O), career_order(N)
    hr3 = lambda c: "met" if (c[0] < c[2] and c[1] < c[2]) else "not met"
    rows.append({"plan": "Biochemistry (4 Nov)", "test": "H-R3 decline larger at 0-5 and 6-15 than at 16+ (weights 0-5 / 6-15 / 16+)",
                 "orig": None, "latest": None, "verdict_orig": hr3(co), "verdict_latest": hr3(cn),
                 "note_orig": " / ".join(f"{x:+.2f}" for x in co), "note_latest": " / ".join(f"{x:+.2f}" for x in cn)})
    hp = lambda x: "includes 0 (citation thresholds)" if x[1] <= 0 <= x[2] else ("negative (publication counts suffice)" if x[2] < 0 else "positive")
    a, b = irl(O, "results_field20"), irl(N, "results_field20")
    rows.append({"plan": "Economics (4 Nov)", "test": "H-P1 interpretation of the nearby-move weight", "orig": a, "latest": b,
                 "verdict_orig": hp(a), "verdict_latest": hp(b)})

    # Chemistry plan (5 Nov)
    add("Chemistry (5 Nov)", "C1 nearby-move weight, FR+DE", "neg", lambda B: irl(B, "results_field16_world"))
    add("Chemistry (5 Nov)", "C1 nearby-move weight, FR+DE+ES", "neg", lambda B: irl(B, "results_field16_world_es"))
    add("Chemistry (5 Nov)", "C2 placebo 2007", "null", lambda B: irl(B, "results_field16_world", "did_placebo_2007.csv"))
    def mech(B, fn, row, col="group"):
        f = os.path.join(B, "results_field16_world_career", fn)
        if not os.path.exists(f):
            return None
        t = pd.read_csv(f)
        if "sample" in t.columns:
            t = t[t["sample"] == t["sample"].iloc[0]]
        r = t[t[col] == row]
        return None if r.empty else tuple(r.iloc[0][["irl_near", "irl_low", "irl_high"]])
    c3 = lambda B: mech(B, "institution_split.csv", "university staff minus research institute")
    c4 = lambda B: mech(B, "rank_exposure.csv", "needed minus full")
    c5 = lambda B: mech(B, "sector_thresholds.csv", "below (0-1) minus met")
    add("Chemistry (5 Nov)", "C3 university staff minus research institute (weight)", "chem", c3)
    add("Chemistry (5 Nov)", "C4 needed the habilitation minus full professors (weight)", "chem", c4)
    add("Chemistry (5 Nov)", "C5 below own bar minus met (weight)", "chem", c5)
    def mrule(B):
        vs = [verdict("chem", g(B)) for g in (c3, c4, c5)]
        xs = [g(B) for g in (c3, c4, c5)]
        ok = sum(v in ("supported", "consistent") for v in vs) >= 2 and not any(x and x[1] > 0 for x in xs)
        return "met" if ok else "not met"
    rows.append({"plan": "Chemistry (5 Nov)", "test": "Mechanism rule (at least two of C3-C5 supported or consistent, none opposite)",
                 "orig": None, "latest": None, "verdict_orig": mrule(O), "verdict_latest": mrule(N)})
    # India and Russia plans (5 Nov)
    for c, fn, cov in (("India", "results_india/india_stacked.csv", "UGC-covered"), ("Russia", "results_russia/russia_stacked.csv", "5-100")):
        k = "I" if c == "India" else "R"
        add(f"{c} (5 Nov)", f"{k}1 nearby move, pp", "neg", lambda B, fn=fn: stacked(B, fn, "I1 nearby move"))
        add(f"{c} (5 Nov)", f"{k}2 placebo 2007, pp", "null", lambda B, fn=fn: stacked(B, fn, "I2 placebo 2007"))
        add(f"{c} (5 Nov)", f"{k}3 returns, pp", "neg", lambda B, fn=fn: stacked(B, fn, "I3 near return"))
        add(f"{c} (5 Nov)", f"{k}4 covered minus not covered, pp", "neg",
            lambda B, fn=fn, cov=cov: stacked(B, fn, f"I4 {cov} minus not covered"))
    ro, rn = russia_rule(O), russia_rule(N)
    fmt = lambda r: f"driving fields: {', '.join(r[1]) or 'none'}; with pre-trend: {', '.join(r[2]) or 'none'}"
    rows.append({"plan": "Russia (5 Nov)", "test": "Replication rule (R1, R2, no pre-trend in the driving fields)", "orig": None, "latest": None,
                 "verdict_orig": "met" if ro[0] else "not met", "verdict_latest": "met" if rn[0] else "not met",
                 "note_orig": fmt(ro), "note_latest": fmt(rn)})
    # Co-authorship and journals plan (5 Nov)
    for c in ("IT", "IN", "RU"):
        for o, lab in (("team_size", "listed authors"), ("international", "international co-authorship, pp"),
                       ("new_coauthors", "new co-authors, pp")):
            sc = 1 if o == "team_size" else 100
            add(f"Co-authorship/journals (5 Nov), {c}", lab, "none", lambda B, c=c, o=o, sc=sc: other(B, f"results_coauthors/coauthors_{c}.csv", o, sc))
        for o, lab in (("bottom_quartile", "bottom-quartile journals, pp"), ("fee_oa", "fee-charging open access, pp")):
            add(f"Co-authorship/journals (5 Nov), {c}", lab, "none", lambda B, c=c, o=o: other(B, f"results_venues/venues_{c}.csv", o))
    # Headline estimates (not pre-specified for Italy)
    for nm, s in (("Physics", ""), ("Engineering", "_field22"), ("Biochemistry", "_field13"), ("Chemistry", "_field16")):
        add("Headline, Italy", f"{nm}: nearby-move weight", "sig", lambda B, s=s: irl(B, f"results{s}_world"))
        add("Headline, Italy", f"{nm}: nearby moves (model-free, pp)", "sig", lambda B, s=s: fe(B, f"results{s}_world", "near"))
        add("Headline, Italy", f"{nm}: distant-jump weight", "sig", lambda B, s=s: irl(B, f"results{s}_world", p="theta_far"))
        add("Headline, Italy", f"{nm}: returns (model-free, pp)", "sig", lambda B, s=s: fe(B, f"results{s}_world", "near_return"))
    out = os.path.join(HERE, "results_downloads")
    os.makedirs(out, exist_ok=True)
    t = pd.DataFrame(rows)
    for col in ("orig", "latest"):
        t[[f"{col}_b", f"{col}_lo", f"{col}_hi"]] = pd.DataFrame(
            [x if x is not None else (None, None, None) for x in t[col]], index=t.index)
    t.drop(columns=["orig", "latest"]).to_csv(os.path.join(out, "download_comparison.csv"), index=False)
    print(t[["plan", "test", "verdict_orig", "verdict_latest"]].to_string(index=False))


if __name__ == "__main__":
    main()
