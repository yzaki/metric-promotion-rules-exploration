"""Supplementary tables for the paper, generated from saved result files (no manual numbers).

Writes LaTeX tables to ../paper_overleaf/tables/ (included by supplementary.tex).
Tables whose inputs do not exist yet are skipped with a message.
"""
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "paper_overleaf", "tables")
PNAME = {"theta_cite": "Citation potential", "theta_near": "Nearby move", "theta_far": "Distant jump"}

# (label, main results folder, +Spain folder)
SPECS = [
    ("Physics (world citation measure)", "results_world", "results_world_es"),
    ("Physics (four-country citation measure)", "results", "results_es"),
    ("Engineering (world citation measure)", "results_field22_world", "results_field22_world_es"),
    ("Engineering (four-country citation measure)", "results_field22", "results_field22_es"),
    ("Biochemistry (world citation measure)", "results_field13_world", "results_field13_world_es"),
    ("Biochemistry (four-country citation measure)", "results_field13", "results_field13_es"),
    ("Chemistry (world citation measure)", "results_field16_world", "results_field16_world_es"),
    ("Economics (four-country citation measure)", "results_field20", "results_field20_es"),
]


def path(*p):
    return os.path.join(HERE, *p)


def ci(r, d=2):
    return f"${r.did:+.{d}f}$ [${r.ci_low:+.{d}f}$, ${r.ci_high:+.{d}f}$]"


def write(name, body):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(body)
    print("wrote", name)


def table_did():
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Field and specification & Weight & Control FR+DE & Control FR+DE+ES \\", r"\midrule"]
    for label, main, es in SPECS:
        if not os.path.exists(path(main, "did_main.csv")):
            print("skip", label)
            continue
        a = pd.read_csv(path(main, "did_main.csv")).set_index("parameter")
        b = pd.read_csv(path(es, "did_main.csv")).set_index("parameter") if os.path.exists(path(es, "did_main.csv")) else None
        for i, p in enumerate(("theta_near", "theta_far", "theta_cite")):
            lines.append(f"{label if i == 0 else ''} & {PNAME[p]} & {ci(a.loc[p])} & "
                         f"{ci(b.loc[p]) if b is not None else '--'} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_did_all.tex", "\n".join(lines))


def table_placebo():
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Field and specification & Weight & Control FR+DE & Control FR+DE+ES \\", r"\midrule"]
    for label, main, es in SPECS:
        f1, f2 = path(main, "did_placebo_2007.csv"), path(es, "did_placebo_2007.csv")
        if not os.path.exists(f1):
            continue
        a = pd.read_csv(f1).set_index("parameter")
        b = pd.read_csv(f2).set_index("parameter") if os.path.exists(f2) else None
        for i, p in enumerate(("theta_near", "theta_far", "theta_cite")):
            lines.append(f"{label if i == 0 else ''} & {PNAME[p]} & {ci(a.loc[p])} & "
                         f"{ci(b.loc[p]) if b is not None else '--'} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_placebo.tex", "\n".join(lines))


def table_robustness():
    rows = [("Main (four-country citation measure, $\\gamma=0.9$)", "results"),
            ("World-wide citation measure", "results_world"),
            ("Discount factor $\\gamma=0.8$", "results_g08"),
            ("Discount factor $\\gamma=0.95$", "results_g095"),
            ("Scientists active before and after (balanced)", "results_balanced"),
            ("Articles with at most 20 authors", "results_team20"),
            ("Control group FR+DE+ES", "results_es")]
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Specification (physics) & Nearby move & Distant jump & Citation potential \\", r"\midrule"]
    for label, folder in rows:
        if not os.path.exists(path(folder, "did_main.csv")):
            continue
        a = pd.read_csv(path(folder, "did_main.csv")).set_index("parameter")
        lines.append(f"{label} & {ci(a.loc['theta_near'])} & {ci(a.loc['theta_far'])} & {ci(a.loc['theta_cite'])} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_robustness.tex", "\n".join(lines))


def table_career():
    """Nearby-move effect by true career age (first publication in the full MAG record)."""
    folders = [f + "_career" for _, f in W3]
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Nearby-move weight, Italy vs FR+DE & Physics & Engineering & Biochemistry \\", r"\midrule"]

    def cell(fn):
        out = []
        for f in folders:
            try:
                out.append(fn(f))
            except (FileNotFoundError, KeyError, IndexError):
                out.append("--")
        return " & ".join(out)

    lines.append(f"All matched scientists & {cell(lambda f: ci(pd.read_csv(path(f, 'did_main.csv')).set_index('parameter').loc['theta_near']))} \\\\")
    lines.append(r"\multicolumn{4}{l}{\emph{Career stage (years since first publication)}} \\")
    for stage in ("0-5 years", "6-15 years", "16+ years"):
        lines.append(f"\\quad {stage.replace('-', '--')} & " + cell(lambda f, stage=stage: ci(
            (lambda t: t[t.career_stage == stage])(pd.read_csv(path(f, "did_by_career_main.csv")))
            .set_index("parameter").loc["theta_near"])) + r" \\")
    lines.append(r"\multicolumn{4}{l}{\emph{Finer bands of career age}} \\")
    for band in ("0-10", "11-20", "21-30", "31+"):
        lines.append(f"\\quad {band.replace('-', '--')} years & " + cell(lambda f: (lambda r: _pp(r.irl_near, r.irl_low, r.irl_high, 2))(
            pd.read_csv(path(f, "career_bands.csv")).set_index("band").loc[band])) + r" \\")
    lines.append(r"\addlinespace")
    for tag, label in (("main", "Mid-career (6--15) minus senior (16+)"), ("placebo_2007", "\\quad placebo reform 2007")):
        lines.append(f"{label} & " + cell(lambda f: (lambda r: _pp(r.point, r.ci_low, r.ci_high, 2))(
            pd.read_csv(path(f, f"italy_ddd_{tag}.csv")).set_index("estimate").loc["ddd"])) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_career.tex", "\n".join(lines))


def table_return_value():
    lines = [r"\begin{tabular}{lllll}", r"\toprule",
             r"Outcome two active years later, relative to staying & Choice & Physics & Engineering & Biochemistry \\", r"\midrule"]
    tabs = [pd.read_csv(path(f, "return_value_lead2.csv")) for _, f in W3]
    labels = {"near_return": "Nearby, return", "near_new": "Nearby, first entry",
              "far_return": "Distant, return", "far_new": "Distant, first entry"}
    for sample in tabs[0]["sample"].unique():
        for o, olabel in (("log_cites", "Mean log normalised citations"), ("top10", "Share in top 10\\%"), ("papers", "Articles")):
            for i, c in enumerate(labels):
                cells = [(lambda r: _pp(r.vs_stay, r.ci_low, r.ci_high, 3))(
                    t[(t["sample"] == sample) & (t.outcome == o) & (t.choice == c)].iloc[0]) for t in tabs]
                first = f"{olabel} ({sample})" if i == 0 else ""
                lines.append(f"{first} & {labels[c]} & {' & '.join(cells)} \\\\")
            lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_return_value.tex", "\n".join(lines))


def table_new_countries():
    lines = [r"\begin{tabular}{lllll}", r"\toprule",
             r"Treated country vs FR+DE & Estimate & Physics & Engineering & Biochemistry \\", r"\midrule"]
    for c, name in (("IT", "Italy (main)"), ("PL", "Poland"), ("RO", "Romania")):
        folders = [f if c == "IT" else f"{f}_{c}" for _, f in W3]
        rows = (("Nearby-move weight", lambda f: ci(pd.read_csv(path(f, "did_main.csv")).set_index("parameter").loc["theta_near"])),
                ("Placebo 2007", lambda f: ci(pd.read_csv(path(f, "did_placebo_2007.csv")).set_index("parameter").loc["theta_near"])),
                ("Model-free, pp", lambda f: (lambda r: _pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp))(
                    pd.read_csv(path(f, "reduced_form.csv")).query("choice == 'near'").iloc[0])),
                ("Treated-country choices", lambda f: f"{int(pd.read_csv(path(f, 'weights_by_group_main.csv'), index_col=0).loc['n_choices', ['IT_pre', 'IT_post']].sum()):,} choices"))
        for i, (label, fn) in enumerate(rows):
            cells = []
            for f in folders:
                try:
                    cells.append(fn(f))
                except (FileNotFoundError, KeyError, IndexError):
                    cells.append("--")
            lines.append(f"{name if i == 0 else ''} & {label} & {' & '.join(cells)} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_new_countries.tex", "\n".join(lines))


def table_effects():
    sets = [("Physics", "results_world"), ("Physics, +ES", "results_world_es"),
            ("Engineering", "results_field22_world"), ("Biochemistry", "results_field13_world"),
            ("Chemistry", "results_field16_world")]
    lines = [r"\begin{tabular}{lllll}", r"\toprule",
             r"Field & Choice & Predicted (actual) & Predicted (no reform) & Change, pp [95\% CI] \\", r"\midrule"]
    for name, folder in sets:
        f = path(folder, "effect_sizes.csv")
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f)
        for i, r in t.iterrows():
            lines.append(f"{name if i == 0 else ''} & {r.choice} & {100 * r.predicted_actual:.1f}\\% & "
                         f"{100 * r.predicted_no_reform:.1f}\\% & ${r.diff_pp:+.2f}$ [${r.diff_pp_low:+.2f}$, ${r.diff_pp_high:+.2f}$] \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_effects.tex", "\n".join(lines))


def table_secondary():
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Outcome (Italy vs control DiD) & Physics & Engineering & Biochemistry \\", r"\midrule"]
    specs = [("Articles per scientist-year", "outcomes_citations.csv", "reform_did", "papers", 2, 1),
             ("Mean log normalised citations", "outcomes_citations.csv", "reform_did", "log_cites", 3, 1),
             ("Share of articles in top 10\\% (pp)", "outcomes_citations.csv", "reform_did", "top10", 1, 100),
             ("Share of references new to the scientist (pp)", "novelty.csv", None, "new_share", 1, 100),
             ("Specialisation, main subfield (pp)", "reconcile_abramo.csv", None, "spec_subfield", 1, 100),
             ("Specialisation, main topic (pp)", "reconcile_abramo.csv", None, "spec_topic", 1, 100),
             ("Disruption (CD index)", "disruption.csv", None, "disruption", 4, 1),
             ("Share of disruptive articles (pp)", "disruption.csv", None, "disruptive", 1, 100),
             ("Atypicality, 10th-pct $z$", "disruption.csv", None, "atyp_10pct", 2, 1)]
    for label, fname, analysis, outcome, d, scale in specs:
        cells = []
        for folder in ("results", "results_field22", "results_field13"):
            f = path(folder, fname)
            if not os.path.exists(f):
                cells.append("--")
                continue
            t = pd.read_csv(f)
            key = "outcome" if "outcome" in t.columns else "measure"
            if analysis:
                t = t[t.analysis == analysis]
            r = t[t[key] == outcome].iloc[0]
            est = r.estimate if "estimate" in t.columns else r.did
            cells.append(f"${scale * est:+.{d}f}$ [${scale * r.ci_low:+.{d}f}$, ${scale * r.ci_high:+.{d}f}$]")
        lines.append(f"{label} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_secondary.tex", "\n".join(lines))


def table_samples():
    sets = [("Physics", "results"), ("Engineering", "results_field22"),
            ("Biochemistry", "results_field13"), ("Chemistry", "results_field16"), ("Economics", "results_field20")]
    lines = [r"\begin{tabular}{llrrrrr}", r"\toprule",
             r"Field & Country & Scientists before & Scientists after & Choices before & Choices after & Nearby share (before$\to$after) \\",
             r"\midrule"]
    for name, folder in sets:
        f = path(folder, "descriptives_es.csv")
        if not os.path.exists(f):
            f = path(folder, "descriptives_world_es.csv")   # chemistry: world citation measure only
        if not os.path.exists(f):
            f = path(folder, "descriptives.csv")
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f).set_index(["country", "period"])
        for i, c in enumerate(["IT", "FR", "DE", "ES"]):
            if (c, "before") not in t.index:
                continue
            b, a = t.loc[(c, "before")], t.loc[(c, "after")]
            lines.append(f"{name if i == 0 else ''} & {c} & {int(b.scientists):,} & {int(a.scientists):,} & "
                         f"{int(b.choices):,} & {int(a.choices):,} & {100 * b.share_near:.1f}\\% $\\to$ {100 * a.share_near:.1f}\\% \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_samples.tex", "\n".join(lines))


def table_dose():
    sets = [("Physics", "results_world"), ("Engineering", "results_field22_world"), ("Biochemistry", "results_field13_world")]
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Field & Indicators above reference median, 2002--11 & Nearby move & Citation potential \\", r"\midrule"]
    for name, folder in sets:
        f = path(folder, "dose_response.csv")
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f)
        for i, g in enumerate(t.group.unique()):
            s = t[t.group == g].set_index("parameter")
            lines.append(f"{name if i == 0 else ''} & {g} & {ci(s.loc['theta_near'])} & {ci(s.loc['theta_cite'])} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_dose.tex", "\n".join(lines))


def table_long_run():
    sets = [("Physics", "results"), ("Engineering", "results_field22"), ("Biochemistry", "results_field13"),
            ("Economics", "results_field20")]
    labels = [("distinct_topics", "Distinct topics per scientist and period", 2, 1),
              ("distinct_subfields", "Distinct subfields per scientist and period", 2, 1),
              ("top1_share", "Share of articles in top 1\\% of year (pp)", 1, 100),
              ("left_research", "No article 7 years later (pp)", 1, 100)]
    lines = [r"\begin{tabular}{lllll}", r"\toprule",
             r"Outcome & Physics & Engineering & Biochemistry & Economics \\", r"\midrule"]
    tabs = {n: pd.read_csv(path(f, "long_run.csv")).set_index("outcome") for n, f in sets
            if os.path.exists(path(f, "long_run.csv"))}
    for key, label, d, sc in labels:
        cells = []
        for n, _ in sets:
            if n not in tabs:
                cells.append("--")
                continue
            r = tabs[n].loc[key]
            cells.append(f"${sc * r.did:+.{d}f}$ [${sc * r.ci_low:+.{d}f}$, ${sc * r.ci_high:+.{d}f}$]")
        lines.append(f"{label} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_long_run.tex", "\n".join(lines))


W3 = [("Physics", "results_world"), ("Engineering", "results_field22_world"), ("Biochemistry", "results_field13_world")]


def _pp(v, lo, hi, d=1):
    return f"${v:+.{d}f}$ [${lo:+.{d}f}$, ${hi:+.{d}f}$]"


def table_validation():
    """Model-free DiD, richer reward model and alternative definition of nearby moves."""
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Check (effect on nearby moves) & Physics & Engineering & Biochemistry \\", r"\midrule"]
    specs = [("Main model: nearby-move weight", lambda f: ci(pd.read_csv(path(f, "did_main.csv")).set_index("parameter").loc["theta_near"])),
             ("Main model: yearly share, pp", lambda f: (lambda r: _pp(r.diff_pp, r.diff_pp_low, r.diff_pp_high))(
                 pd.read_csv(path(f, "effect_sizes.csv")).set_index("choice").loc["near"])),
             ("Model-free: scientist + year FE, pp", lambda f: (lambda r: _pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp))(
                 pd.read_csv(path(f, "reduced_form.csv")).query("choice == 'near'").iloc[0])),
             ("Model-free: + state FE, pp", lambda f: (lambda r: _pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp))(
                 pd.read_csv(path(f, "reduced_form.csv")).query("choice == 'near'").iloc[1])),
             ("Richer reward (11 weights): yearly share, pp", lambda f: (lambda r: _pp(r.effect_near_pp, r.ci_low, r.ci_high))(
                 pd.read_csv(path(f, "rich_model_effect.csv")).iloc[0])),
             ("Nearby = 10 most similar topics: weight", lambda f: ci(pd.read_csv(path(f + "_near10", "did_main.csv")).set_index("parameter").loc["theta_near"])),
             ("Nearby = 10 most similar topics: placebo 2007", lambda f: ci(pd.read_csv(path(f + "_near10", "did_placebo_2007.csv")).set_index("parameter").loc["theta_near"])),
             ("Nearby = 10 most similar topics: model-free, pp", lambda f: (lambda r: _pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp))(
                 pd.read_csv(path(f + "_near10", "reduced_form.csv")).query("choice == 'near'").iloc[0]))]
    for label, fn in specs:
        cells = []
        for _, f in W3:
            try:
                cells.append(fn(f))
            except (FileNotFoundError, KeyError, IndexError):
                cells.append("--")
        lines.append(f"{label} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_validation.tex", "\n".join(lines))


def table_fit():
    lines = [r"\begin{tabular}{lllrrrr}", r"\toprule",
             r"Field & Group & Period & 3 weights & 11 weights & Constant shares & Saturated (54) \\", r"\midrule"]
    for name, f in W3:
        p = path(f, "rich_model_fit.csv")
        if not os.path.exists(p):
            continue
        t = pd.read_csv(p)
        for i, r in t.iterrows():
            lines.append(f"{name if i == 0 else ''} & {r.group} & {r.period} & {r.oos_ll_3weights:.3f} & "
                         f"{r.oos_ll_rich11:.3f} & {r.oos_ll_constant:.3f} & {r.oos_ll_saturated:.3f} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_fit.tex", "\n".join(lines))


def table_relax():
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"2016--18 vs 2013--15, Italy vs control & Physics & Engineering & Biochemistry \\", r"\midrule"]
    rows = [("Nearby-move weight (model)", "inverse RL (weight)", "theta_near", 2),
            ("P(nearby move), pp (model-free)", "linear probability (pp)", "P(near) pp", 1),
            ("P(stay), pp (model-free)", "linear probability (pp)", "P(stay) pp", 1),
            ("P(distant jump), pp (model-free)", "linear probability (pp)", "P(far) pp", 1)]
    for label, method, par, d in rows:
        cells = []
        for _, f in W3:
            p = path(f, "relax_2016.csv")
            if not os.path.exists(p):
                cells.append("--")
                continue
            r = pd.read_csv(p).query("method == @method and parameter == @par").iloc[0]
            cells.append(_pp(r.did, r.ci_low, r.ci_high, d))
        lines.append(f"{label} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_relax.tex", "\n".join(lines))


def table_counterfactual():
    lines = [r"\begin{tabular}{lrrrrrr}", r"\toprule",
             r" & \multicolumn{2}{c}{Physics} & \multicolumn{2}{c}{Engineering} & \multicolumn{2}{c}{Biochemistry} \\",
             r"Scenario & Nearby moves, 10 y & Any in 6 y & Nearby moves, 10 y & Any in 6 y & Nearby moves, 10 y & Any in 6 y \\",
             r"\midrule"]
    tabs = [pd.read_csv(path(f, "counterfactual.csv")).set_index("scenario") for _, f in W3
            if os.path.exists(path(f, "counterfactual.csv"))]
    if len(tabs) == 3:
        for sc in tabs[0].index:
            cells = []
            for t in tabs:
                r = t.loc[sc]
                cells.append(f"{r.nearby_moves_10y:.2f} & {100 * r.share_any_nearby_6y:.0f}\\%")
            lines.append(f"{sc} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_counterfactual.tex", "\n".join(lines))


def table_heterogeneity():
    lines = [r"\begin{tabular}{lllllll}", r"\toprule",
             r" & \multicolumn{2}{c}{Physics} & \multicolumn{2}{c}{Engineering} & \multicolumn{2}{c}{Biochemistry} \\",
             r"Subgroup & Weight & pp & Weight & pp & Weight & pp \\", r"\midrule"]
    tabs = [pd.read_csv(path(f, "heterogeneity.csv")).set_index("subgroup") if os.path.exists(path(f, "heterogeneity.csv"))
            else None for _, f in W3]
    if all(t is not None for t in tabs):
        for sg in tabs[0].index:
            cells = []
            for t in tabs:
                r = t.loc[sg]
                cells.append(f"{_pp(r.irl_near, r.irl_low, r.irl_high, 2)} & {_pp(r.lpm_near_pp, r.lpm_low, r.lpm_high)}")
            lines.append(f"{sg} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_heterogeneity.tex", "\n".join(lines))


def table_controls():
    sets = [("France", "FR"), ("Germany", "DE"), ("Spain", "ES"), ("Netherlands", "NL"), ("Portugal", "PT"),
            ("All five", "FR_DE_ES_NL_PT")]
    folders = [("Physics", "results"), ("Engineering", "results_field22"), ("Biochemistry", "results_field13")]
    lines = [r"\begin{tabular}{lllllll}", r"\toprule",
             r" & \multicolumn{2}{c}{Physics} & \multicolumn{2}{c}{Engineering} & \multicolumn{2}{c}{Biochemistry} \\",
             r"Control group & Weight & Model-free, pp & Weight & Model-free, pp & Weight & Model-free, pp \\", r"\midrule"]
    for label, tag in sets:
        cells = []
        for _, base in folders:
            f = f"{base}_world_ctrl_{tag}"
            try:
                w = ci(pd.read_csv(path(f, "did_main.csv")).set_index("parameter").loc["theta_near"])
                r = pd.read_csv(path(f, "reduced_form.csv")).query("choice == 'near'").iloc[0]
                cells.append(f"{w} & {_pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp)}")
            except (FileNotFoundError, KeyError, IndexError):
                cells.append("-- & --")
        lines.append(f"{label} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_controls.tex", "\n".join(lines))


def table_simulation():
    f1, f2 = path("results_sim", "did_main.csv"), path("results_sim", "did_placebo_2007.csv")
    if not (os.path.exists(f1) and os.path.exists(f2)):
        return
    a, b = pd.read_csv(f1).set_index("parameter"), pd.read_csv(f2).set_index("parameter")
    lines = [r"\begin{tabular}{lrlcl}", r"\toprule",
             r"Weight & Planted effect & Estimated effect [95\% CI] & Covers planted & Placebo 2007 [95\% CI] \\", r"\midrule"]
    for p in ("theta_cite", "theta_near", "theta_far"):
        r, q = a.loc[p], b.loc[p]
        lines.append(f"{PNAME[p]} & ${r.true:+.2f}$ & {ci(r)} & {'yes' if r.covered else 'no'} & {ci(q)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_simulation.tex", "\n".join(lines))


def table_composition():
    """Model-free nearby-move DiD on all scientists and on those observed in both periods."""
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Nearby-move DiD, pp & Physics & Engineering & Biochemistry \\", r"\midrule"]
    tabs = [pd.read_csv(path(f, "composition_check.csv")) for _, f in W3]
    decs = [pd.read_csv(path(f, "composition_decompose.csv")).set_index("contrast") for _, f in W3]
    for sample, slabel in (("all", "All scientists"), ("balanced", "Observed before and after")):
        lines.append(rf"\multicolumn{{4}}{{l}}{{\emph{{{slabel}}}}} \\")
        for spec in ("raw shares", "year FE", "year + state FE", "scientist + year FE", "scientist + year + state FE"):
            cells = []
            for t in tabs:
                r = t[(t["sample"] == sample) & (t.spec == spec)].iloc[0]
                cells.append(f"${r.beta_pp:+.1f}$" if spec == "raw shares" else _pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp))
            lines.append(f"\\quad {spec[0].upper() + spec[1:]} & {' & '.join(cells)} \\\\")
        lines.append(r"\addlinespace")
    lines.append(r"\multicolumn{4}{l}{\emph{Decomposition of the raw difference}} \\")
    for key, label in (("stayers: after minus before", "Same scientists, after vs before"),
                       ("entrants after minus leavers before", "Entrants after vs leavers before")):
        cells = [_pp(d.loc[key].did_pp, d.loc[key].ci_low, d.loc[key].ci_high) for d in decs]
        lines.append(f"\\quad {label} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_composition.tex", "\n".join(lines))


def table_placebo_space():
    """Each country as the treated unit; Italy's rank (1 = most negative of six)."""
    names = {"IT": "Italy", "FR": "France", "DE": "Germany", "ES": "Spain", "NL": "Netherlands", "PT": "Portugal"}
    folders = [f + "_career_placebo_space" for _, f in W3]
    tabs = [pd.read_csv(path(f, "placebo_space.csv")).set_index("treated") for f in folders]
    lines = [r"\begin{tabular}{lrrrrrrrrr}", r"\toprule",
             r" & \multicolumn{3}{c}{Physics} & \multicolumn{3}{c}{Engineering} & \multicolumn{3}{c}{Biochemistry} \\",
             r"Treated country & Weight & Model-free, pp & Mid $-$ senior & Weight & Model-free, pp & Mid $-$ senior & Weight & Model-free, pp & Mid $-$ senior \\",
             r"\midrule"]
    for c in tabs[0].index:
        cells = []
        for t in tabs:
            r = t.loc[c]
            cells.append(f"${r.irl_near:+.2f}$ & ${r.lpm_near_pp:+.1f}$ & ${r.irl_ddd_mid_minus_senior:+.2f}$")
        lines.append(f"{names[c]} & {' & '.join(cells)} \\\\")
    lines.append(r"\addlinespace")
    cells = []
    for t in tabs:
        r = t.loc["IT"]
        cells.append(f"{int(r.rank_irl_near)} of 6 & {int(r.rank_lpm_near_pp)} of 6 & {int(r.rank_irl_ddd_mid_minus_senior)} of 6")
    lines.append(f"Italy's rank (1 = most negative) & {' & '.join(cells)} \\\\")
    cells = []
    for f in folders:
        d = pd.read_csv(path(f, "italy_ddd.csv")).set_index("estimate").loc["ddd"]
        cells.append(f"\\multicolumn{{3}}{{r}}{{{_pp(d.point, d.ci_low, d.ci_high, 2)}}}")
    lines.append(f"Italy, mid $-$ senior, 95\\% CI & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_placebo_space.tex", "\n".join(lines))


def table_first_entry():
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Yearly choice, model-free DiD, pp & Physics & Engineering & Biochemistry \\", r"\midrule"]
    tabs = [pd.read_csv(path(f, "first_entry.csv")) for _, f in W3]
    labels = {"near": "Nearby move (all)", "near_new": "Nearby move, new topic", "near_return": "Nearby move, return",
              "far_new": "Distant jump, new topic", "far_return": "Distant jump, return"}
    for definition in tabs[0].definition.unique():
        lines.append(rf"\multicolumn{{4}}{{l}}{{\emph{{New = no article in the topic, {definition}}}}} \\")
        for o in tabs[0][tabs[0].definition == definition].outcome:
            cells = []
            for t in tabs:
                r = t[(t.definition == definition) & (t.outcome == o)].iloc[0]
                cells.append(f"{_pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp)} ({r.IT_before_pct:.1f}\\%)")
            lines.append(f"\\quad {labels[o]} & {' & '.join(cells)} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_first_entry.tex", "\n".join(lines))


def table_stacked_rules():
    t = pd.read_csv(path("results_stacked_rules", "stacked_rules.csv"))
    scopes = ["Physics", "Engineering", "Biochemistry", "All three fields"]
    lines = [r"\begin{tabular}{lllll}", r"\toprule",
             r"Nearby moves, model-free DiD, pp & " + " & ".join(scopes) + r" \\", r"\midrule"]
    for e in t.estimate.unique():
        cells = [(lambda r: _pp(r.beta_pp, r.ci_low_pp, r.ci_high_pp))(t[(t.scope == s) & (t.estimate == e)].iloc[0]) for s in scopes]
        lines.append(f"{e} & {' & '.join(cells)} \\\\")
        if e == "Spain 2008":
            lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_stacked_rules.tex", "\n".join(lines))


def table_rank():
    folders = [f + "_career" for _, f in W3]
    tabs = [pd.read_csv(path(f, "rank_exposure.csv")) for f in folders]
    splits = [pd.read_csv(path(f, "register_split.csv")).set_index("italian_group") for f in folders]
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Italian group (rank at 31 Dec 2011) vs FR+DE & Physics & Engineering & Biochemistry \\", r"\midrule"]
    for sample in tabs[0]["sample"].unique():
        lines.append(rf"\multicolumn{{4}}{{l}}{{\emph{{Nearby-move weight, {sample}}}}} \\")
        for g in ("full professor", "associate professor", "researcher", "needed minus full"):
            cells = []
            for t in tabs:
                r = t[(t["sample"] == sample) & (t.group == g)].iloc[0]
                n = "" if g == "needed minus full" else f" ({int(r.n_italian):,})"
                cells.append(_pp(r.irl_near, r.irl_low, r.irl_high, 2) + n)
            label = "Needed it minus full professors" if g == "needed minus full" else g[0].upper() + g[1:]
            lines.append(f"\\quad {label} & {' & '.join(cells)} \\\\")
        lines.append(r"\addlinespace")
    lines.append(r"\multicolumn{4}{l}{\emph{Model-free, pp}} \\")
    for g in ("matched to register", "not matched"):
        cells = [(lambda r: _pp(r.lpm_near_pp, r.ci_low, r.ci_high) + f" ({int(r.n_italian):,})")(s.loc[g]) for s in splits]
        lines.append(f"\\quad Italian scientists {g} & {' & '.join(cells)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_rank.tex", "\n".join(lines))


def _group_table(fname, order, labels, header, outname, extra_rows=None):
    folders = [f + "_career" for _, f in W3]
    tabs = [pd.read_csv(path(f, fname)).set_index("group") for f in folders]
    lines = [r"\begin{tabular}{llll}", r"\toprule", header + r" & Physics & Engineering & Biochemistry \\", r"\midrule"]
    for g in order:
        cells = []
        for t in tabs:
            if g not in t.index:
                cells.append("--")
                continue
            r = t.loc[g]
            s = _pp(r.irl_near, r.irl_low, r.irl_high, 2)
            if pd.notna(r.get("lpm_near_pp", np.nan)):
                s += f"; ${r.lpm_near_pp:+.1f}$ ({int(r.n_italian):,})"
            cells.append(s)
        lines.append(f"{labels.get(g, g)} & {' & '.join(cells)} \\\\")
    for label, fn in (extra_rows or []):
        lines.append(f"{label} & {' & '.join(fn(t) for t in tabs)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write(outname, "\n".join(lines))


def table_sector_bars():
    _group_table("sector_thresholds.csv", ["met", "one short", "far below", "full professor", "one short minus met",
                                          "below (0-1) minus met"],
                 {"met": "Associates and researchers: bar met (2--3 of 3)", "one short": "\\quad one indicator short",
                  "far below": "\\quad far below (0 of 3)", "full professor": "Full professors (no bar)",
                  "one short minus met": "One short minus met", "below (0-1) minus met": "Below (0--1) minus met"},
                 "Group (weight; model-free pp, $n$)", "tab_sector_bars.tex",
                 [("Validation: Spearman vs ANVUR 2012 medians (articles / citations / h; sectors)",
                   lambda t: f"{t.validation_spearman_articles.iloc[0]:.2f} / {t.validation_spearman_citations.iloc[0]:.2f} / "
                             f"{t.validation_spearman_h.iloc[0]:.2f} ({int(t.validation_n_sectors.iloc[0])})")])


def table_institutions():
    _group_table("institution_split.csv",
                 ["university staff", "university, early career", "university, other", "research institute",
                  "hospital or company", "university staff minus research institute",
                  "university, early career minus research institute"],
                 {"university staff": "University staff (in the 2011 register)",
                  "university, early career": "University, not in register, $\\le$10 years",
                  "university, other": "University, not in register, $>$10 years",
                  "research institute": "Research institute (e.g.\\ INFN, CNR, INAF)",
                  "hospital or company": "Hospital or company",
                  "university staff minus research institute": "University staff minus research institute",
                  "university, early career minus research institute": "Early career minus research institute"},
                 "Italian group, 2009--12 (weight; model-free pp, $n$)", "tab_institutions.tex")


def table_chemistry():
    """Chemistry (field 16): tests specified in advance (PREREGISTRATION_chemistry_2026-11-05.md)."""
    w, es, c = "results_field16_world", "results_field16_world_es", "results_field16_world_career"
    near = lambda f, n="did_main.csv": ci(pd.read_csv(path(f, n)).set_index("parameter").loc["theta_near"])
    ev = pd.read_csv(path(es, "event_study.csv")).query("parameter == 'theta_near'").set_index("window")
    rf = pd.read_csv(path(w, "reduced_form.csv")).query("choice == 'near'").iloc[0]
    dec = pd.read_csv(path(w, "composition_decompose.csv")).set_index("contrast")
    fe = pd.read_csv(path(w, "first_entry.csv"))
    fe = fe[fe.definition == fe.definition.iloc[0]].set_index("outcome")
    car = pd.read_csv(path(c, "did_by_career_main.csv")).query("parameter == 'theta_near'").set_index("career_stage")
    ins = pd.read_csv(path(c, "institution_split.csv")).set_index("group")
    rk = pd.read_csv(path(c, "rank_exposure.csv")).query("sample == 'all career ages'").set_index("group")
    sb = pd.read_csv(path(c, "sector_thresholds.csv")).set_index("group")
    irl = lambda r: _pp(r.irl_near, r.irl_low, r.irl_high, 2)
    pp = lambda b, lo, hi: _pp(b, lo, hi)
    rows = [
        ("C1 Nearby-move weight, FR+DE", near(w), "met"),
        ("C1 Nearby-move weight, FR+DE+ES (primary under the pre-trend rule)", near(es), "met"),
        ("C2 Placebo 2007, FR+DE / FR+DE+ES", near(w, "did_placebo_2007.csv") + " / " + near(es, "did_placebo_2007.csv"), "met"),
        ("Event study vs 2008--09: 2004--05 / 2006--07", " / ".join(_pp(ev.loc[x].it_minus_ctrl_vs_ref, ev.loc[x].ci_low, ev.loc[x].ci_high, 2)
                                                         for x in ("2004-2005", "2006-2007")), "pre-trend"),
        ("Event study: 2012--13 / 2014--15 / 2016--17", " / ".join(f"${ev.loc[x].it_minus_ctrl_vs_ref:+.2f}$" for x in ("2012-2013", "2014-2015", "2016-2017")), "no break"),
        ("Model-free, scientist + year FE, pp", pp(rf.beta_pp, rf.ci_low_pp, rf.ci_high_pp), ""),
        ("Same scientists / entrants vs leavers, pp", " / ".join(pp(dec.loc[k].did_pp, dec.loc[k].ci_low, dec.loc[k].ci_high)
                                                          for k in ("stayers: after minus before", "entrants after minus leavers before")), ""),
        ("Nearby first entries / returns, pp", " / ".join(pp(fe.loc[k].beta_pp, fe.loc[k].ci_low_pp, fe.loc[k].ci_high_pp)
                                                     for k in ("near_new", "near_return")), ""),
        ("Career stage 0--5 / 6--15 / 16+", " / ".join(f"${car.loc[s].did:+.2f}$" for s in ("0-5 years", "6-15 years", "16+ years")), ""),
        ("C3 University staff minus research institute", irl(ins.loc["university staff minus research institute"]), "consistent"),
        ("C4 Needed it minus full professors", irl(rk.loc["needed minus full"]), "not supported"),
        ("\\quad full / associate / researcher", " / ".join(f"${rk.loc[g].irl_near:+.2f}$" for g in ("full professor", "associate professor", "researcher")), ""),
        ("C5 Below own bar (0--1) minus met", irl(sb.loc["below (0-1) minus met"]), "consistent"),
    ]
    lines = [r"\begin{tabular}{lll}", r"\toprule", r"Test (chemistry, Italy vs control) & Estimate [95\% CI] & Verdict \\", r"\midrule"]
    lines += [f"{a} & {b} & {v} \\\\" for a, b, v in rows]
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_chemistry.tex", "\n".join(lines))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for fn in (table_composition, table_placebo_space, table_first_entry, table_return_value, table_new_countries,
               table_stacked_rules, table_rank, table_sector_bars, table_institutions, table_chemistry):
        try:
            fn()
        except (FileNotFoundError, KeyError, IndexError) as e:
            print("skip", fn.__name__, e)
    table_simulation()
    table_heterogeneity()
    table_controls()
    table_validation()
    table_fit()
    table_relax()
    table_counterfactual()
    table_dose()
    table_long_run()
    table_samples()
    table_did()
    table_placebo()
    table_robustness()
    table_career()
    table_effects()
    table_secondary()
