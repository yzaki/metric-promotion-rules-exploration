"""Main-text figures for the paper, built from saved result tables (no refitting).

Writes PDF (vector, embedded TrueType fonts) and 300-dpi PNG to ../paper_overleaf/figures/:
    fig0_design          design schematic
    fig1_did_by_field    nearby / distant / citation DiD with 95% CI, by field and control set
    fig2_event_study     nearby-move event studies (FR+DE+ES), three citation-threshold fields
    fig3_career          nearby-move DiD by career stage
    fig4_citations       citation-potential weight: world vs four-country measure; engineering event study
    fig5_consequences    output, new-reference share, specialisation

Style: all text black; categorical colours in fixed order (blue, orange, aqua; validated for
colour-vision deficiency) with a distinct marker shape per series as secondary encoding.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "paper_overleaf", "figures")

INK = "#000000"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
REF = "#9a9a9a"        # zero / reference lines only (never text)
BAND = "#eeeeee"       # reform-transition shading

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 13,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 13,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12.5,
    "legend.fontsize": 12,
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
    fig.savefig(os.path.join(OUT, f"{name}.png"))
    plt.close(fig)


def _control_legend(fig, y=-0.02):
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="Control: France + Germany"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="Control: France + Germany + Spain")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, y))


def fig0():
    """Schematic of the design: yearly choices, recovered rewards, difference-in-differences."""
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
    fig, ax = plt.subplots(figsize=(13, 3.6))
    ax.set_xlim(0, 13)
    ax.set_ylim(0.3, 3.7)
    ax.axis("off")

    def box(x, y, w, h, text, fc="#eaf2fc", ec=BLUE, fs=11.5):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.08",
                                    fc=fc, ec=ec, lw=1.6))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK)

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=16,
                                     lw=1.6, color=INK))

    ax.text(0.1, 3.5, "A  One scientist, one year", fontsize=14, fontweight="bold")
    box(0.1, 1.1, 2.7, 1.9, "State in year $t$\n\ncitation potential\nof the topic\ntime in topic\ncareer stage")
    box(3.8, 2.5, 2.3, 0.7, "stay in topic", fc="white", ec=INK)
    box(3.8, 1.65, 2.3, 0.7, "nearby topic\n(same subfield)", fc="white", ec=INK)
    box(3.8, 0.8, 2.3, 0.7, "distant topic\n(other subfield)", fc="white", ec=INK)
    for yy in (2.85, 2.0, 1.15):
        arrow(2.8, 2.05, 3.8, yy)
    ax.text(4.95, 0.45, "choice → state in year $t+1$", ha="center", fontsize=12, color=INK)

    ax.text(6.8, 3.5, "B  Inverse RL", fontsize=14, fontweight="bold")
    box(6.8, 1.1, 2.8, 1.9, "Recover the rewards that\nbest explain all observed\nchoice sequences\n\n"
                            "$\\theta_{cite}$, $\\theta_{near}$, $\\theta_{far}$   (stay = 0)")
    arrow(6.1, 2.05, 6.8, 2.05)

    ax.text(10.1, 3.5, "C  Reform effect", fontsize=14, fontweight="bold")
    box(10.1, 1.1, 2.85, 1.9, "Fit Italy and controls\n(FR, DE, ES),\nbefore and after\n\n"
                              "$\\Delta\\theta=(\\theta^{IT}_{after}-\\theta^{IT}_{before})$\n"
                              "$-(\\theta^{C}_{after}-\\theta^{C}_{before})$")
    arrow(9.6, 2.05, 10.1, 2.05)
    _save(fig, "fig0_design")


def fig1():
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.8), sharey=True)
    for ax, (p, label) in zip(axes, PARAMS):
        _zero(ax)
        for i, (name, main, es) in enumerate(FIELDS):
            y = len(FIELDS) - 1 - i
            _pointrange(ax, y + 0.14, did(main).loc[p], BLUE, "o")
            _pointrange(ax, y - 0.14, did(es).loc[p], ORANGE, "s")
        ax.set_title(label, loc="left")
        ax.set_yticks(range(len(FIELDS)), [f[0] for f in FIELDS][::-1])
        _clean(ax)
    axes[1].set_xlabel("Change in reward weight, Italy vs control (after − before)")
    _control_legend(fig, y=-0.06)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig1_did_by_field")


def fig2():
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.4), sharey=True)
    for ax, (name, _, es) in zip(axes, FIELDS[:3]):
        e = pd.read_csv(os.path.join(HERE, es, "event_study.csv"))
        d = e[e.parameter == "theta_near"].sort_values("start")
        x = d.start + 0.5
        _zero(ax, vertical=False)
        ax.axvspan(2010, 2013, color=BAND, zorder=0)
        ax.axvline(2012, color="#c0392b", lw=1.6, ls="--")
        ax.fill_between(x, d.ci_low, d.ci_high, color=BLUE, alpha=0.2, lw=0)
        ax.plot(x, d.it_minus_ctrl_vs_ref, "o-", color=BLUE, mec="white", mew=0.8)
        ax.set_title(name, loc="left")
        ax.set_xlabel("Two-year window")
        ax.set_xticks([2004, 2008, 2012, 2016])
        _clean(ax)
    axes[0].set_ylabel("Nearby-move weight,\nItaly − control (vs 2008–09)")
    h = [plt.Rectangle((0, 0), 1, 1, color=BAND, label="Reform transition (2010–12)"),
         plt.Line2D([], [], color="#c0392b", ls="--", lw=1.6, label="First habilitation round (2012)"),
         plt.Line2D([], [], color=BLUE, marker="o", label="Estimate with 95% band")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    _save(fig, "fig2_event_study")


def fig3():
    """Career-stage heterogeneity of the nearby-move effect (world citation measure)."""
    stages = [("0-5 years", BLUE, "o"), ("6-15 years", ORANGE, "s"), ("16+ years", AQUA, "D")]
    fig, ax = plt.subplots(figsize=(9, 5))
    _zero(ax)
    for i, (name, folder) in enumerate(WORLD3):
        t = pd.read_csv(os.path.join(HERE, folder, "did_by_career_main.csv"))
        t = t[t.parameter == "theta_near"].set_index("career_stage")
        for j, (st, col, mk) in enumerate(stages):
            _pointrange(ax, len(WORLD3) - 1 - i + (0.24 - 0.24 * j), t.loc[st], col, mk)
    ax.set_yticks(range(len(WORLD3)), [w[0] for w in WORLD3][::-1])
    ax.set_xlabel("Change in nearby-move weight, Italy vs control (after − before)")
    h = [plt.Line2D([], [], color=c, marker=m, ls="none", ms=9, label=s.replace("-", "–") + " since first paper")
         for s, c, m in stages]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.07), fontsize=11.5)
    _clean(ax)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig3_career")


def fig4():
    """Citation weight: world-wide vs four-country measure; engineering event study."""
    local = {"Physics": "results", "Engineering": "results_field22", "Biochemistry": "results_field13"}
    fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1, 1.15]})
    _zero(a)
    for i, (name, folder) in enumerate(WORLD3):
        y = len(WORLD3) - 1 - i
        _pointrange(a, y + 0.14, did(folder).loc["theta_cite"], BLUE, "o")
        _pointrange(a, y - 0.14, did(local[name]).loc["theta_cite"], ORANGE, "s")
    a.set_yticks(range(len(WORLD3)), [w[0] for w in WORLD3][::-1])
    a.set_xlabel("Change in citation-potential weight")
    a.set_title("A  Citation-potential weight", loc="left")
    _clean(a)
    e = pd.read_csv(os.path.join(HERE, "results_field22_world_es", "event_study.csv"))
    d = e[e.parameter == "theta_cite"].sort_values("start")
    x = d.start + 0.5
    _zero(b, vertical=False)
    b.axvspan(2010, 2013, color=BAND, zorder=0)
    b.axvline(2012, color="#c0392b", lw=1.6, ls="--")
    b.fill_between(x, d.ci_low, d.ci_high, color=BLUE, alpha=0.2, lw=0)
    b.plot(x, d.it_minus_ctrl_vs_ref, "o-", color=BLUE, mec="white", mew=0.8)
    b.set_title("B  Engineering: citation-potential weight over time", loc="left")
    b.set_xlabel("Two-year window")
    b.set_ylabel("Italy − control (vs 2008–09)")
    b.set_xticks([2004, 2008, 2012, 2016])
    _clean(b)
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="World-wide citation rates"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="Four-country citation rates (panel A)")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig4_citations")


def fig5():
    """Consequences: output, knowledge breadth, specialisation (subfield vs topic)."""
    fields = [("Physics", "results"), ("Engineering", "results_field22"), ("Biochemistry", "results_field13")]
    panels = [("A  Articles per scientist-year", "outcomes_citations.csv", "papers", 1, "Articles"),
              ("B  New references (pp)", "novelty.csv", "new_share", 100, "Percentage points"),
              ("C  Specialisation (pp)", "reconcile_abramo.csv", None, 100, "Percentage points")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), sharey=True)
    for ax, (title, fname, outcome, scale, xlab) in zip(axes, panels):
        _zero(ax)
        for i, (name, folder) in enumerate(fields):
            f = os.path.join(HERE, folder, fname)
            y = len(fields) - 1 - i
            if not os.path.exists(f):
                ax.text(0.02, y, "  pending", ha="left", va="center", fontsize=12, color=INK,
                        style="italic", transform=ax.get_yaxis_transform())
                continue
            t = pd.read_csv(f)
            if outcome is None:
                for mk, meas, col, dy in (("o", "spec_subfield", BLUE, 0.14), ("s", "spec_topic", ORANGE, -0.14)):
                    r = t[t.measure == meas].iloc[0]
                    _pointrange(ax, y + dy, {k: scale * float(r[k]) for k in ("did", "ci_low", "ci_high")}, col, mk)
                continue
            if "analysis" in t.columns:
                t = t[t.analysis == "reform_did"]
            r = t[t.outcome == outcome].iloc[0]
            est = "estimate" if "estimate" in t.columns else "did"
            _pointrange(ax, y, {"did": scale * float(r[est]), "ci_low": scale * float(r.ci_low),
                                "ci_high": scale * float(r.ci_high)}, BLUE)
        ax.set_title(title, loc="left")
        ax.set_xlabel(xlab)
        ax.set_yticks(range(len(fields)), [f[0] for f in fields][::-1])
        _clean(ax)
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="Panels A–B; panel C: main subfield (as Abramo et al.)"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="Panel C: main topic")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.06))
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, "fig5_consequences")


# ===================================================================== composite figures
# Four multi-panel main-text figures (Science Advances style). Economics and the full
# three-weight table are in the Supplementary Materials.

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

    ax.text(0.1, 3.45, "1. Each scientist, each year", fontsize=12.5, fontweight="bold")
    box(0.1, 1.1, 2.7, 1.9, "State in year $t$\n\ncitation potential\nof the topic\ntime in topic\ncareer stage")
    box(3.8, 2.5, 2.3, 0.7, "stay in topic", fc="white", ec=INK)
    box(3.8, 1.65, 2.3, 0.7, "nearby topic\n(same subfield)", fc="white", ec=INK)
    box(3.8, 0.8, 2.3, 0.7, "distant topic\n(other subfield)", fc="white", ec=INK)
    for yy in (2.85, 2.0, 1.15):
        arrow(2.8, 2.05, 3.8, yy)
    ax.text(4.95, 0.42, "choice → state in year $t+1$", ha="center", fontsize=11.5, color=INK)
    ax.text(6.8, 3.45, "2. Inverse RL", fontsize=12.5, fontweight="bold")
    box(6.8, 1.1, 2.8, 1.9, "Recover the rewards that\nbest explain all observed\nchoice sequences\n\n"
                            "$\\theta_{cite}$, $\\theta_{near}$, $\\theta_{far}$   (stay = 0)")
    arrow(6.1, 2.05, 6.8, 2.05)
    ax.text(10.1, 3.45, "3. Reform effect", fontsize=12.5, fontweight="bold")
    box(10.1, 1.1, 2.85, 1.9, "Fit Italy and controls\n(FR, DE, ES),\nbefore and after\n\n"
                              "$\\Delta\\theta=(\\theta^{IT}_{after}-\\theta^{IT}_{before})$\n"
                              "$-(\\theta^{C}_{after}-\\theta^{C}_{before})$")
    arrow(9.6, 2.05, 10.1, 2.05)


def _did_rows(ax, param, rows, xlabel):
    """Point ranges for one weight: rows = [(label, main_folder, es_folder_or_None)]."""
    _zero(ax)
    for i, (name, main, es) in enumerate(rows):
        y = len(rows) - 1 - i
        _pointrange(ax, y + (0.14 if es else 0), did(main).loc[param], BLUE, "o")
        if es:
            _pointrange(ax, y - 0.14, did(es).loc[param], ORANGE, "s")
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
    ax.set_xticks([2004, 2008, 2012, 2016])
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
            ax.text(0.03, y, "pending", ha="left", va="center", fontsize=12, color=INK, style="italic",
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


def main_fig1():
    """Design and main result."""
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[0.85, 1.15], hspace=0.2, wspace=0.3)
    a = fig.add_subplot(gs[0, :])
    _schematic(a)
    a.set_title("A  Design", loc="left", pad=2)
    b = fig.add_subplot(gs[1, 0])
    _did_rows(b, "theta_near", THREE, "Change in nearby-move weight\n(Italy vs control, after − before)")
    _panel(b, "B", "Value of moving to a nearby topic")
    c = fig.add_subplot(gs[1, 1])
    choices = [("near", "Nearby move", BLUE, "o"), ("stay", "Stay", ORANGE, "s"), ("far", "Distant jump", AQUA, "D")]
    _zero(c)
    for i, (name, folder, _) in enumerate(THREE):
        t = pd.read_csv(os.path.join(HERE, folder, "effect_sizes.csv")).set_index("choice")
        for j, (ch, _, col, mk) in enumerate(choices):
            r = t.loc[ch]
            _pointrange(c, len(THREE) - 1 - i + (0.22 - 0.22 * j),
                        {"did": r.diff_pp, "ci_low": r.diff_pp_low, "ci_high": r.diff_pp_high}, col, mk)
    c.set_yticks(range(len(THREE)), [t[0] for t in THREE][::-1])
    c.set_xlabel("Change in yearly choice share,\npercentage points (vs no reform)")
    _panel(c, "C", "What Italians chose instead")
    _clean(c)
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="B: control FR + DE;  C: nearby move"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="B: control FR + DE + ES;  C: stay"),
         plt.Line2D([], [], color=AQUA, marker="D", ls="none", ms=9, label="C: distant jump")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.02), fontsize=11.5)
    fig.subplots_adjust(bottom=0.15)
    _save(fig, "Fig1_design_main")


def main_fig2():
    """Timing and who."""
    fig = plt.figure(figsize=(13, 8.8))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.05], hspace=0.45, wspace=0.25)
    first = None
    for k, (name, _, es) in enumerate(THREE):
        ax = fig.add_subplot(gs[0, k], sharey=first)
        first = first or ax
        _event(ax, es, "theta_near", "Nearby-move weight,\nItaly − control (vs 2008–09)" if k == 0 else None)
        _panel(ax, "ABC"[k], name)
    d = fig.add_subplot(gs[1, :])
    stages = [("0-5 years", BLUE, "o"), ("6-15 years", ORANGE, "s"), ("16+ years", AQUA, "D")]
    _zero(d)
    for i, (name, folder, _) in enumerate(THREE):
        t = pd.read_csv(os.path.join(HERE, folder, "did_by_career_main.csv"))
        t = t[t.parameter == "theta_near"].set_index("career_stage")
        for j, (st, col, mk) in enumerate(stages):
            _pointrange(d, len(THREE) - 1 - i + (0.22 - 0.22 * j), t.loc[st], col, mk)
    d.set_yticks(range(len(THREE)), [t[0] for t in THREE][::-1])
    d.set_xlabel("Change in nearby-move weight, Italy vs control (after − before)")
    _panel(d, "D", "By career stage (years since first paper)")
    _clean(d)
    h = [plt.Rectangle((0, 0), 1, 1, color=BAND, label="Reform transition"),
         plt.Line2D([], [], color="#c0392b", ls="--", lw=1.6, label="First habilitation round (2012)")] + \
        [plt.Line2D([], [], color=c, marker=m, ls="none", ms=9, label="D: " + s.replace("-", "–")) for s, c, m in stages]
    fig.legend(handles=h, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=11)
    fig.subplots_adjust(bottom=0.13)
    _save(fig, "Fig2_timing_career")


def main_fig3():
    """Not citation-chasing."""
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.3)
    a = fig.add_subplot(gs[0, 0])
    _zero(a)
    for i, ((name, world, _), (_, local)) in enumerate(zip(THREE, LOCAL3)):
        y = len(THREE) - 1 - i
        _pointrange(a, y + 0.14, did(world).loc["theta_cite"], BLUE, "o")
        _pointrange(a, y - 0.14, did(local).loc["theta_cite"], ORANGE, "s")
    a.set_yticks(range(len(THREE)), [t[0] for t in THREE][::-1])
    a.set_xlabel("Change in citation-potential weight")
    _panel(a, "A", "Value of a topic's citation potential")
    _clean(a)
    b = fig.add_subplot(gs[0, 1])
    _event(b, "results_field22_world_es", "theta_cite", "Italy − control (vs 2008–09)")
    _panel(b, "B", "Engineering: citation weight over time")
    c = fig.add_subplot(gs[1, 0])
    _did_rows(c, "theta_far", THREE, "Change in distant-jump weight")
    _panel(c, "C", "Value of a distant jump")
    d = fig.add_subplot(gs[1, 1])
    _did_rows(d, "theta_cite", THREE, "Change in citation-potential weight")
    _panel(d, "D", "Citation weight, both control groups")
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="A: world-wide citation rates;  C–D: control FR + DE"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="A: four-country citation rates;  C–D: control FR + DE + ES")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=11.5)
    fig.subplots_adjust(bottom=0.12)
    _save(fig, "Fig3_not_citation_chasing")


def main_fig4():
    """Consequences and reconciliation."""
    fig = plt.figure(figsize=(13, 8.6))
    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.3)
    a = fig.add_subplot(gs[0, 0])
    _outcome_rows(a, LOCAL3, "outcomes_citations.csv", "papers", 1, "Articles per scientist-year")
    _panel(a, "A", "Output")
    b = fig.add_subplot(gs[0, 1])
    _outcome_rows(b, LOCAL3, "novelty.csv", "new_share", 100, "Percentage points")
    _panel(b, "B", "References new to the scientist")
    c = fig.add_subplot(gs[1, 0])
    _zero(c)
    for i, (name, folder) in enumerate(LOCAL3):
        t = pd.read_csv(os.path.join(HERE, folder, "reconcile_abramo.csv"))
        for mk, meas, col, dy in (("o", "spec_subfield", BLUE, 0.14), ("s", "spec_topic", ORANGE, -0.14)):
            r = t[t.measure == meas].iloc[0]
            _pointrange(c, len(LOCAL3) - 1 - i + dy, {k: 100 * float(r[k]) for k in ("did", "ci_low", "ci_high")}, col, mk)
    c.set_yticks(range(len(LOCAL3)), [t[0] for t in LOCAL3][::-1])
    c.set_xlabel("Percentage points")
    _panel(c, "C", "Specialisation: subfield vs topic")
    _clean(c)
    d = fig.add_subplot(gs[1, 1])
    _outcome_rows(d, LOCAL3, "disruption.csv", "disruptive", 100, "Percentage points")
    _panel(d, "D", "Share of disruptive articles")
    h = [plt.Line2D([], [], color=BLUE, marker="o", ls="none", ms=9, label="A, B, D; C: main subfield (as Abramo et al.)"),
         plt.Line2D([], [], color=ORANGE, marker="s", ls="none", ms=9, label="C: main topic")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=11.5)
    fig.subplots_adjust(bottom=0.12)
    _save(fig, "Fig4_consequences")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for f in (main_fig1, main_fig2, main_fig3, main_fig4):
        f()
    print("figures written to", os.path.abspath(OUT))
