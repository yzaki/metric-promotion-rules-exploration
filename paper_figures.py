"""Figures for the paper, built from saved result tables (no refitting).

Writes PDF (vector, embedded TrueType fonts) to ../paper_overleaf/figures/:
    Fig1_design_main            design schematic; nearby-move effect by field; effect in choice shares (main Fig. 1)
    Fig5_who_changed            first entries vs returns; who changed in engineering and physics (main Fig. 2)
    Fig2_timing_career          event studies; career stage (main Fig. 3)
    Fig3_not_citation_chasing   citation-potential weight; distant jumps (main Fig. 4)
    Fig4_consequences           output, new references, specialization, disruption (SI Fig. S1)

Style: all text black; categorical colours in fixed order (blue, orange, aqua; validated for
colour-vision deficiency) with a distinct marker shape per series as secondary encoding.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "v3_out", "figures")

INK = "#000000"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
REF = "#9a9a9a"        # zero / reference lines only (never text)
GREY = "#5a5a5a"       # second measure within one panel (orange is reserved for the alternative control group)
BAND = "#eeeeee"       # reform-transition shading

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 16.2,
    "axes.titlesize": 17.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 16.2,
    "xtick.labelsize": 15,
    "ytick.labelsize": 15.6,
    "legend.fontsize": 15,
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.edgecolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.linewidth": 1.0,
    "lines.linewidth": 2.0,
    "lines.markersize": 8,
    "errorbar.capsize": 4,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

FIELDS = [("Physics", "results_world", "results_world_es"),
          ("Engineering", "results_field22_world", "results_field22_world_es"),
          ("Biochemistry", "results_field13_world", "results_field13_world_es"),
          ("Economics\n(placebo field)", "results_field20", "results_field20_es")]
WORLD3 = [("Physics", "results_world"), ("Engineering", "results_field22_world"),
          ("Biochemistry", "results_field13_world")]
PARAMS = [("theta_near", "Nearby move"), ("theta_far", "Distant jump"), ("theta_cite", "Citation potential")]


def did(folder):
    return pd.read_csv(os.path.join(HERE, folder, "did_main.csv")).set_index("parameter")


def _pointrange(ax, y, r, color, mk="o"):
    est = float(r["did"]) if "did" in r else float(r["estimate"])
    ax.errorbar(est, y, xerr=[[est - float(r["ci_low"])], [float(r["ci_high"]) - est]],
                fmt=mk, color=color, mec="white", mew=0.8, elinewidth=2.0)


def _clean(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def _zero(ax, vertical=True):
    (ax.axvline if vertical else ax.axhline)(0, color=REF, lw=1.2, zorder=0)
    if vertical:   # point-range panels: a few clean x ticks, never crowded
        from matplotlib.ticker import MaxNLocator
        ax.xaxis.set_major_locator(MaxNLocator(nbins=5, steps=[1, 2, 2.5, 5, 10]))


def _save(fig, name):
    fig.savefig(os.path.join(OUT, f"{name}.pdf"))
    plt.close(fig)


def _control_legend(fig, y=-0.02):
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="Control: France + Germany"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="Control: France + Germany + Spain")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, y))


# ===================================================================== composite figures
# Multi-panel figures: Fig1, Fig5 (main Fig. 2), Fig2 (main Fig. 3), Fig3 (main Fig. 4) in the main
# text; Fig4 is SI Fig. S1. Economics and the full three-weight table are in the SI Appendix.

def _panel(ax, letter, title):
    ax.set_title(f"{letter}  {title}", loc="left")


def _schematic(ax):
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    ax.set_xlim(0, 13)
    ax.set_ylim(0.3, 3.75)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#eaf2fc", ec=BLUE, fs=11.5):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.08",
                                    fc=fc, ec=ec, lw=1.6))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK)

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=16, lw=1.6, color=INK))

    ax.text(0.1, 3.45, "1. Each scientist, each year", fontsize=15.6, fontweight="bold")
    box(0.1, 1.1, 2.7, 1.9, "State in year $t$\n\ncitation potential\nof the topic\ntime in topic\ncareer stage")
    box(3.8, 2.5, 2.3, 0.7, "stay in topic", fc="white", ec=INK)
    box(3.8, 1.65, 2.3, 0.7, "nearby topic\n(same subfield)", fc="white", ec=INK)
    box(3.8, 0.8, 2.3, 0.7, "distant topic\n(other subfield)", fc="white", ec=INK)
    for yy in (2.85, 2.0, 1.15):
        arrow(2.8, 2.05, 3.8, yy)
    ax.text(4.95, 0.42, "choice → state in year $t+1$", ha="center", fontsize=14.4, color=INK)
    ax.text(6.8, 3.45, "2. Inverse RL", fontsize=15.6, fontweight="bold")
    box(6.8, 1.1, 2.8, 1.9, "Recover the rewards that\nbest explain all observed\nchoice sequences\n\n"
                            "$\\theta_{cite}$, $\\theta_{near}$, $\\theta_{far}$   (stay = 0)")
    arrow(6.1, 2.05, 6.8, 2.05)
    ax.text(10.1, 3.45, "3. Reform effect", fontsize=15.6, fontweight="bold")
    box(10.1, 1.1, 2.85, 1.9, "Fit Italy and controls\n(FR + DE; + ES as check),\nbefore and after\n\n"
                              "$\\Delta\\theta=(\\theta^{IT}_{after}-\\theta^{IT}_{before})$\n"
                              "$-(\\theta^{C}_{after}-\\theta^{C}_{before})$")
    arrow(9.6, 2.05, 10.1, 2.05)


def _hollow(ax, x, y, color, mk):
    ax.plot(x, y, mk, mfc="white", mec=color, mew=1.8, ms=8, zorder=6)


def _did_rows(ax, param, rows, xlabel, hollow=()):
    """Point ranges for one weight: rows = [(label, main_folder, es_folder_or_None)]; fields in `hollow` drawn open."""
    _zero(ax)
    for i, (name, main, es) in enumerate(rows):
        y = len(rows) - 1 - i
        r = did(main).loc[param]
        _pointrange(ax, y + (0.14 if es else 0), r, BLUE, "o")
        if name in hollow:
            _hollow(ax, float(r["did"]) if "did" in r else float(r["estimate"]), y + (0.14 if es else 0), BLUE, "o")
        if es:
            r = did(es).loc[param]
            _pointrange(ax, y - 0.14, r, ORANGE, "s")
            if name in hollow:
                _hollow(ax, float(r["did"]) if "did" in r else float(r["estimate"]), y - 0.14, ORANGE, "s")
    ax.set_yticks(range(len(rows)), [r[0] for r in rows][::-1])
    ax.set_xlabel(xlabel)
    _clean(ax)


def _event(ax, folder, param, ylabel=None):
    e = pd.read_csv(os.path.join(HERE, folder, "event_study.csv"))
    d = e[e.parameter == param].sort_values("start")
    x = d.start + 0.5
    _zero(ax, vertical=False)
    ax.axvspan(2010, 2013, color=BAND, zorder=0)
    ax.axvline(2012, color="#c0392b", lw=1.6, ls="--")
    ax.fill_between(x, d.ci_low, d.ci_high, color=BLUE, alpha=0.2, lw=0)
    ax.plot(x, d.it_minus_ctrl_vs_ref, "o-", color=BLUE, mec="white", mew=0.8)
    ax.set_xticks([2004, 2010, 2016])
    ax.set_xlabel("Two-year window")
    if ylabel:
        ax.set_ylabel(ylabel)
    _clean(ax)


def _outcome_rows(ax, fields, fname, outcome, scale, xlabel, analysis="reform_did"):
    _zero(ax)
    for i, (name, folder) in enumerate(fields):
        y = len(fields) - 1 - i
        f = os.path.join(HERE, folder, fname)
        if not os.path.exists(f):
            ax.text(0.03, y, "pending", ha="left", va="center", fontsize=15, color=INK, style="italic",
                    transform=ax.get_yaxis_transform())
            continue
        t = pd.read_csv(f)
        if "analysis" in t.columns:
            t = t[t.analysis == analysis]
        key = "outcome" if "outcome" in t.columns else "measure"
        r = t[t[key] == outcome].iloc[0]
        est = "estimate" if "estimate" in t.columns else "did"
        _pointrange(ax, y, {"did": scale * float(r[est]), "ci_low": scale * float(r.ci_low),
                            "ci_high": scale * float(r.ci_high)}, BLUE)
    ax.set_yticks(range(len(fields)), [f[0] for f in fields][::-1])
    ax.set_ylim(-0.5, len(fields) - 0.5)
    ax.set_xlabel(xlabel)
    _clean(ax)


THREE = [("Physics", "results_world", "results_world_es"),
         ("Engineering", "results_field22_world", "results_field22_world_es"),
         ("Biochemistry", "results_field13_world", "results_field13_world_es")]
LOCAL3 = [("Physics", "results"), ("Engineering", "results_field22"), ("Biochemistry", "results_field13")]
# chemistry (field 16) was analysed later
FOUR = THREE + [("Chemistry", "results_field16_world", "results_field16_world_es")]
LOCAL4 = LOCAL3 + [("Chemistry", "results_field16")]
# event studies with the main control group (France + Germany), from the main runs
ES_FRDE = {"results_world_es": "results_world", "results_field22_world_es": "results_field22_world",
           "results_field13_world_es": "results_field13_world", "results_field16_world_es": "results_field16_world"}


def main_fig1():
    """Design and main result."""
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.85, 1.15], hspace=0.25, wspace=0.42)
    a = fig.add_subplot(gs[0, :])
    _schematic(a)
    a.set_title("A  Design", loc="left", pad=2)
    b = fig.add_subplot(gs[1, 0])
    # chemistry fails the pre-trend rule of the India and Russia plans (Table S33): drawn open
    _did_rows(b, "theta_near", FOUR, "Change in nearby-move weight\n(Italy vs control, after − before)", hollow={"Chemistry"})
    _panel(b, "B", "Nearby-move weight")
    c = fig.add_subplot(gs[1, 1])
    choices = [("near", "Nearby move", BLUE, "o"), ("stay", "Stay", ORANGE, "s"), ("far", "Distant jump", AQUA, "D")]
    _zero(c)
    for i, (name, folder, _) in enumerate(FOUR):
        t = pd.read_csv(os.path.join(HERE, folder, "effect_sizes.csv")).set_index("choice")
        for j, (ch, _, col, mk) in enumerate(choices):
            r = t.loc[ch]
            _pointrange(c, len(FOUR) - 1 - i + (0.22 - 0.22 * j),
                        {"did": r.diff_pp, "ci_low": r.diff_pp_low, "ci_high": r.diff_pp_high}, col, mk)
            if name == "Chemistry":
                _hollow(c, r.diff_pp, len(FOUR) - 1 - i + (0.22 - 0.22 * j), col, mk)
    c.set_yticks(range(len(FOUR)), [t[0] for t in FOUR][::-1])
    c.set_xlabel("Change in yearly choice share,\npercentage points (vs no reform)")
    _panel(c, "C", "Yearly choice shares")
    _clean(c)
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="B: control FR + DE;  C: nearby move"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="B: control FR + DE + ES;  C: stay"),
         plt.Line2D([], [], color=AQUA, marker="D", ls="none", ms=9, label="C: distant jump"),
         plt.Line2D([], [], color=INK, marker="o", mfc="white", ls="none", ms=9, label="open: fails the plans\u2019 pre-trend rule")]
    fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=14.4)
    fig.subplots_adjust(bottom=0.15)
    _save(fig, "Fig1_design_main")


def main_fig2():
    """Timing and who."""
    fig = plt.figure(figsize=(13, 8.8))
    gs = fig.add_gridspec(2, 4, height_ratios=[1, 1.05], hspace=0.45, wspace=0.3)
    first = None
    for k, (name, _, es) in enumerate(FOUR):
        ax = fig.add_subplot(gs[0, k], sharey=first)
        first = first or ax
        _event(ax, ES_FRDE.get(es, es), "theta_near", "Nearby-move weight,\nItaly − control (vs 2008–09)" if k == 0 else None)
        _panel(ax, "ABCD"[k], name)
    d = fig.add_subplot(gs[1, :])
    stages = [("0-5 years", BLUE, "o"), ("6-15 years", ORANGE, "s"), ("16+ years", AQUA, "D")]
    _zero(d)
    for i, (name, folder, _) in enumerate(FOUR):   # true career age (SciSciNet/MAG first publication)
        t = pd.read_csv(os.path.join(HERE, folder + "_career", "did_by_career_main.csv"))
        t = t[t.parameter == "theta_near"].set_index("career_stage")
        for j, (st, col, mk) in enumerate(stages):
            _pointrange(d, len(FOUR) - 1 - i + (0.22 - 0.22 * j), t.loc[st], col, mk)
    d.set_yticks(range(len(FOUR)), [t[0] for t in FOUR][::-1])
    d.set_xlabel("Change in nearby-move weight, Italy vs control (after − before)")
    _panel(d, "E", "By career stage (years since first publication)")
    _clean(d)
    h = [plt.Rectangle((0, 0), 1, 1, color=BAND, label="Reform transition"),
         plt.Line2D([], [], color="#c0392b", ls="--", lw=1.6, label="First habilitation round (2012)")] + \
        [plt.Line2D([], [], color=c, marker=m, ls="none", ms=9, label="E: " + s.replace("-", "–")) for s, c, m in stages]
    fig.legend(handles=h, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=13.8)
    fig.subplots_adjust(bottom=0.13)
    _save(fig, "Fig2_timing_career")


def main_fig3():
    """Not citation-chasing."""
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(2, 2, hspace=0.5, wspace=0.42)
    a = fig.add_subplot(gs[0, 0])
    _zero(a)
    for i, ((name, world, _), local) in enumerate(zip(FOUR, [l for _, l in LOCAL4])):
        y = len(FOUR) - 1 - i
        _pointrange(a, y + (0.14 if local else 0), did(world).loc["theta_cite"], BLUE, "o")
        if local:
            _pointrange(a, y - 0.14, did(local).loc["theta_cite"], ORANGE, "s")
    a.set_yticks(range(len(FOUR)), [t[0] for t in FOUR][::-1])
    a.set_xlabel("Change in citation-potential weight")
    _panel(a, "A", "Citation-potential weight")
    _clean(a)
    b = fig.add_subplot(gs[0, 1])
    _event(b, "results_field22_world_es", "theta_cite", "Italy − control (vs 2008–09)")
    _panel(b, "B", "Engineering, over time")
    c = fig.add_subplot(gs[1, 0])
    _did_rows(c, "theta_far", FOUR, "Change in distant-jump weight")
    _panel(c, "C", "Distant-jump weight")
    d = fig.add_subplot(gs[1, 1])
    _did_rows(d, "theta_cite", FOUR, "Change in citation-potential weight")
    _panel(d, "D", "Citation weight, two control sets")
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="A: world-wide citation rates;  C–D: control FR + DE"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="A: study-country citation rates;  C–D: control FR + DE + ES")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=14.4)
    fig.subplots_adjust(bottom=0.12)
    _save(fig, "Fig3_not_citation_chasing")


def main_fig4():
    """Consequences and reconciliation."""
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.3)
    a = fig.add_subplot(gs[0, 0])
    _outcome_rows(a, LOCAL4, "outcomes_citations.csv", "papers", 1, "Articles per scientist-year")
    _panel(a, "A", "Output")
    b = fig.add_subplot(gs[0, 1])
    _outcome_rows(b, LOCAL4, "novelty.csv", "new_share", 100, "Percentage points")
    _panel(b, "B", "References new to the scientist")
    c = fig.add_subplot(gs[1, 0])
    _zero(c)
    for i, (name, folder) in enumerate(LOCAL4):
        t = pd.read_csv(os.path.join(HERE, folder, "reconcile_abramo.csv"))
        for mk, meas, col, dy in (("o", "spec_subfield", BLUE, 0.14), ("s", "spec_topic", GREY, -0.14)):
            r = t[t.measure == meas].iloc[0]
            _pointrange(c, len(LOCAL4) - 1 - i + dy, {k: 100 * float(r[k]) for k in ("did", "ci_low", "ci_high")}, col, mk)
    c.set_yticks(range(len(LOCAL4)), [t[0] for t in LOCAL4][::-1])
    c.set_xlabel("Percentage points")
    _panel(c, "C", "Specialization: subfield vs topic")
    _clean(c)
    d = fig.add_subplot(gs[1, 1])
    _outcome_rows(d, LOCAL4, "disruption.csv", "disruptive", 100, "Percentage points")
    _panel(d, "D", "Share of disruptive articles")
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="A, B, D; C: main subfield (as Abramo et al.)"),
         plt.Line2D([], [], color=GREY, marker="s", ls="none", ms=9, label="C: main topic")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=14.4)
    fig.subplots_adjust(bottom=0.12)
    _save(fig, "Fig4_consequences")


def _who_rows(folder):
    """Rank, own-bar and institution groups (nearby-move weight) for one field, top to bottom."""
    f = os.path.join(HERE, folder + "_career")
    rk = pd.read_csv(os.path.join(f, "rank_exposure.csv"))
    rk = rk[rk["sample"] == "all career ages"].set_index("group")
    sb = pd.read_csv(os.path.join(f, "sector_thresholds.csv")).set_index("group")
    ins = pd.read_csv(os.path.join(f, "institution_split.csv")).set_index("group")
    rows = [("Rank 2011: full professor", rk.loc["full professor"]),
            ("associate professor", rk.loc["associate professor"]),
            ("researcher", rk.loc["researcher"]),
            ("Own sector bar: met", sb.loc["met"]),
            ("one indicator short", sb.loc["one short"]),
            ("far below", sb.loc["far below"]),
            ("Institution: university staff", ins.loc["university staff"]),
            ("university, early career", ins.loc["university, early career"]),
            ("research institute", ins.loc["research institute"])]
    return [(lab, {"did": r.irl_near, "ci_low": r.irl_low, "ci_high": r.irl_high}) for lab, r in rows]


def main_fig5():
    """What declined, and who changed."""
    fig = plt.figure(figsize=(13, 9.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.7, 1.45], hspace=0.42, wspace=0.95)
    a = fig.add_subplot(gs[0, :])
    _zero(a)
    four = THREE + [("Chemistry", "results_field16_world", None)]
    for i, (name, folder, _) in enumerate(four):
        t = pd.read_csv(os.path.join(HERE, folder, "first_entry.csv"))
        t = t[t.definition == t.definition.iloc[0]].set_index("outcome")
        for dy, oc, col, mk in ((0.2, "near_new", BLUE, "o"), (0.0, "near_return", ORANGE, "s"),
                                (-0.2, "near_gap_return", AQUA, "D")):
            if oc not in t.index:
                continue
            r = t.loc[oc]
            _pointrange(a, len(four) - 1 - i + dy, {"did": r.beta_pp, "ci_low": r.ci_low_pp, "ci_high": r.ci_high_pp}, col, mk)
            # same rule as Fig. 5: hollow if Italy's model-free timing check fails for this outcome
            tm = pd.read_csv(os.path.join(HERE, folder, "first_entry_timing.csv")).set_index("outcome")
            if oc in tm.index:
                q = tm.loc[oc]
                if q.pretrend_wald_p < 0.05 or q.placebo_ci_low_pp > 0 or q.placebo_ci_high_pp < 0:
                    a.plot(r.beta_pp, len(four) - 1 - i + dy, mk, mfc="white", mec=col, mew=1.8, ms=8, zorder=6)
    a.set_yticks(range(len(four)), [t[0] for t in four][::-1])
    a.set_xlabel("Change in yearly probability, percentage points (model-free)")
    _panel(a, "A", "Nearby moves: first entries and returns")
    _clean(a)
    for k, (field, folder) in enumerate((("Engineering", "results_field22_world"), ("Physics", "results_world"))):
        ax = fig.add_subplot(gs[1, k])
        _zero(ax)
        rows = _who_rows(folder)
        n = len(rows)
        for i, (lab, r) in enumerate(rows):
            _pointrange(ax, n - 1 - i, r, [BLUE, ORANGE, AQUA][i // 3], "osD"[i // 3])
        ax.set_yticks(range(n), [lab for lab, _ in rows][::-1])
        for yline in (2.5, 5.5):
            ax.axhline(yline, color=REF, lw=0.8, ls=":")
        ax.set_xlabel("Change in nearby-move weight\n(Italian group vs control)")
        _panel(ax, "BC"[k], f"{field}: who changed")
        _clean(ax)
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="A: first entry;  B–C: rank"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="A: return (all);  B–C: own sector bar"),
         plt.Line2D([], [], color=AQUA, marker="D", ls="none", ms=9, label="A: gap return;  B–C: institution 2009–12")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=14.4)
    fig.subplots_adjust(bottom=0.14)
    _save(fig, "Fig5_who_changed")


def supp_fig_returns_timing():
    """Fig. S2: annual model-free event studies (Italy vs France + Germany, ref. 2009)."""
    four = [("Physics", "results_world"), ("Engineering", "results_field22_world"),
            ("Biochemistry", "results_field13_world"), ("Chemistry", "results_field16_world")]
    fig, axes = plt.subplots(2, 4, figsize=(15, 7), sharex=True)
    for j, (name, folder) in enumerate(four):
        f = os.path.join(HERE, folder, "first_entry_timing.csv")
        if not os.path.exists(f):
            continue
        t = pd.read_csv(f).set_index("outcome")
        for i, (oc, lab, col) in enumerate((("near", "Nearby move", BLUE), ("near_gap_return", "Gap return", AQUA))):
            ax = axes[i, j]
            yrs = list(range(2004, 2019))
            b = [0.0 if y == 2009 else t.loc[oc, f"es_{y}"] for y in yrs]
            se = [0.0 if y == 2009 else t.loc[oc, f"se_{y}"] for y in yrs]
            lo = [x - 1.96 * e for x, e in zip(b, se)]
            hi = [x + 1.96 * e for x, e in zip(b, se)]
            ax.axvspan(2009.5, 2012.5, color=BAND, lw=0)
            ax.axhline(0, color=REF, lw=1)
            ax.fill_between(yrs, lo, hi, color=col, alpha=0.18, lw=0)
            ax.plot(yrs, b, "-o", color=col, ms=5)
            ax.set_xticks(range(2004, 2019, 4))
            ax.text(0.03, 0.04, f"pre-2009 test p = {t.loc[oc, 'pretrend_wald_p']:.3f}", transform=ax.transAxes, fontsize=13.1)
            _panel(ax, "ABCDEFGH"[i * 4 + j], f"{name}: {lab.lower()}")
            _clean(ax)
            if j == 0:
                ax.set_ylabel("Italy − control, pp vs 2009")
    fig.tight_layout()
    _save(fig, "FigS2_returns_timing")


def main_fig_countries():
    """Italy, Russia and India side by side: nearby moves and gap returns, model-free, by field and pooled."""
    import numpy as np
    fields = [("Physics", "results"), ("Engineering", "results_field22"), ("Biochemistry", "results_field13"),
              ("Chemistry", "results_field16")]
    ctry = [("Italy", "_world", BLUE, "o"), ("Russia", "_world_RU", ORANGE, "s"), ("India", "_world_IN", AQUA, "D")]
    stacked = {"Russia": "results_russia/russia_stacked.csv", "India": "results_india/india_stacked.csv"}

    def near(c, base, suf, field):
        if c == "Italy":
            r = pd.read_csv(os.path.join(HERE, base + suf, "reduced_form.csv")).query("choice == 'near'").iloc[0]
            return r.beta_pp, r.ci_low_pp, r.ci_high_pp
        t = pd.read_csv(os.path.join(HERE, stacked[c]))
        r = t[(t.test == "I1 nearby move") & (t.scope == field)].iloc[0]
        return r.beta_pp, r.ci_low_pp, r.ci_high_pp

    def gap(base, suf):
        t = pd.read_csv(os.path.join(HERE, base + suf, "first_entry.csv"))
        r = t[(t.definition == t.definition.iloc[0]) & (t.outcome == "near_gap_return")].iloc[0]
        return r.beta_pp, r.ci_low_pp, r.ci_high_pp

    def pool(vals):
        b = np.array([v[0] for v in vals]); se = np.array([(v[2] - v[1]) / 3.92 for v in vals])
        w = 1 / se ** 2
        m, e = (w * b).sum() / w.sum(), np.sqrt(1 / w.sum())
        return m, m - 1.96 * e, m + 1.96 * e

    # one rule for all countries and both outcomes: Italy's model-free timing check, failed if the joint test of the
    # pre-2009 years has p < 0.05 or the 2007 placebo excludes zero (first_entry.py --timing; Tables S33, S38).
    # Pooled markers are hollow if any field is.
    def fails(base, suf, outcome):
        t = pd.read_csv(os.path.join(HERE, base + suf, "first_entry_timing.csv"))
        r = t[t.outcome == outcome].iloc[0]   # Italy's timing check: joint test or 2007 placebo
        return r.pretrend_wald_p < 0.05 or r.placebo_ci_low_pp > 0 or r.placebo_ci_high_pp < 0
    HOLLOW = {(c, what): {field for field, base in fields
                          if fails(base, "_world" if c == "Italy" else suf, "near" if what == "near" else "near_gap_return")}
              for c, suf, _, _ in ctry for what in ("near", "gap")}
    print("Fig. 5 hollow:", HOLLOW)
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.6), sharey=True)
    labels = [f for f, _ in fields] + ["Pooled"]
    for k, (ax, what) in enumerate(zip(axes, ("near", "gap"))):
        _zero(ax)
        for j, (c, suf, col, mk) in enumerate(ctry):
            vals = []
            for i, (field, base) in enumerate(fields):
                v = near(c, base, suf if c != "Italy" else "_world", field) if what == "near" else gap(base, suf)
                vals.append(v)
                yy = len(labels) - 1 - i + 0.22 - 0.22 * j
                _pointrange(ax, yy, {"did": v[0], "ci_low": v[1], "ci_high": v[2]}, col, mk)
                if field in HOLLOW[(c, what)]:   # field fails a pre-trend check for this outcome
                    ax.plot(v[0], yy, mk, mfc="white", mec=col, mew=1.8, ms=8, zorder=6)
            pv = pool(vals)
            _pointrange(ax, 0.22 - 0.22 * j, {"did": pv[0], "ci_low": pv[1], "ci_high": pv[2]}, col, mk)
            if HOLLOW[(c, what)]:   # pooled over fields that include one failing the pre-test
                ax.plot(pv[0], 0.22 - 0.22 * j, mk, mfc="white", mec=col, mew=1.8, ms=8, zorder=6)
        ax.axhline(0.5, color=REF, lw=0.8, ls=":")
        ax.set_yticks(range(len(labels)), labels[::-1])
        ax.set_xlabel("Change in yearly probability, pp")
        _panel(ax, "AB"[k], "Nearby moves" if what == "near" else "Gap returns (exploratory)")
        _clean(ax)
    h = [plt.Line2D([], [], color=col, marker=mk, ls="none", ms=9, label=c) for c, _, col, mk in ctry]
    h.append(plt.Line2D([], [], color=INK, marker="o", mfc="white", ls="none", ms=9, label="hollow: fails the model-free timing check"))
    fig.legend(handles=h, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.02))
    fig.subplots_adjust(bottom=0.2, wspace=0.12)
    _save(fig, "Fig6_countries")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (main_fig1, main_fig2, main_fig3, main_fig4, main_fig5, supp_fig_returns_timing, main_fig_countries):
        f()
    print("figures written to", os.path.abspath(OUT))
