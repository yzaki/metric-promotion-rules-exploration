"""Supplementary tables for the paper, generated from saved result files (no manual numbers).

Writes LaTeX tables to ../paper_overleaf/tables/ (included by supplementary.tex).
Tables whose inputs do not exist yet are skipped with a message.
"""
import os

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
    sets = [("Physics", "results_world"), ("Engineering", "results_field22_world"), ("Biochemistry", "results_field13_world")]
    lines = [r"\begin{tabular}{llll}", r"\toprule",
             r"Field & Career stage & Nearby move & Citation potential \\", r"\midrule"]
    for name, folder in sets:
        f = path(folder, "did_by_career_main.csv")
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f)
        for i, stage in enumerate(t.career_stage.unique()):
            s = t[t.career_stage == stage].set_index("parameter")
            lines.append(f"{name if i == 0 else ''} & {stage} & {ci(s.loc['theta_near'])} & {ci(s.loc['theta_cite'])} \\\\")
        lines.append(r"\addlinespace")
    lines += [r"\bottomrule", r"\end{tabular}"]
    write("tab_career.tex", "\n".join(lines))


def table_effects():
    sets = [("Physics", "results_world"), ("Physics, +ES", "results_world_es"),
            ("Engineering", "results_field22_world"), ("Biochemistry", "results_field13_world")]
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
            ("Biochemistry", "results_field13"), ("Economics", "results_field20")]
    lines = [r"\begin{tabular}{llrrrrr}", r"\toprule",
             r"Field & Country & Scientists before & Scientists after & Choices before & Choices after & Nearby share (before$\to$after) \\",
             r"\midrule"]
    for name, folder in sets:
        f = path(folder, "descriptives_es.csv")
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


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
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
