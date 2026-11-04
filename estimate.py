"""Step 3: fit the inverse-RL model and measure the reform effect.

Fits reward weights for four groups (Italy / control x before / after), computes
the difference-in-differences on each weight, and adds bootstrap 95% intervals
by resampling whole scientists.

Usage:
    python estimate.py                                   # real data from build_trajectories.py
    python estimate.py --event-study --by-career         # extra analyses
    python estimate.py --placebo-year 2007               # fake reform inside the pre-period
    python estimate.py --input data/simulated_trajectories.csv --truth data/simulated_truth.json
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

import config
import irl

ACTION_CODE = {name: i for i, name in enumerate(irl.ACTIONS)}
PRETTY = {"theta_cite": "Citation weight", "theta_near": "Nearby-move weight",
          "theta_far": "Distant-jump weight"}


# ---------------------------------------------------------------- data ------
class Panel:
    """Choices as integer arrays, ready for fast weighted counting."""

    def __init__(self, df):
        self.df = df.reset_index(drop=True)
        self.s = irl.state_index(df.s_tier.to_numpy(), df.s_tenure.to_numpy(), df.s_career.to_numpy())
        self.sn = irl.state_index(df.ns_tier.to_numpy(), df.ns_tenure.to_numpy(), df.ns_career.to_numpy())
        self.a = df.action.map(ACTION_CODE).to_numpy()
        self.year = df.year.to_numpy()
        self.career = df.s_career.to_numpy()
        self.is_it = (df.group == "IT").to_numpy()
        codes, uniques = pd.factorize(df.author_id)
        self.author = codes
        self.author_is_it = pd.Series(self.is_it).groupby(codes).first().to_numpy()
        self.n_authors = len(uniques)

    def counts(self, mask, weights=None, choice_mask=None):
        """Choice counts (from choice_mask, default mask) and transition counts (from mask)."""
        w = None if weights is None else weights[mask]
        _, trans = irl.count_arrays(self.s[mask], self.a[mask], self.sn[mask], w)
        if choice_mask is None:
            return trans.sum(axis=2), trans
        cm = mask & choice_mask
        wc = None if weights is None else weights[cm]
        choices, _ = irl.count_arrays(self.s[cm], self.a[cm], self.sn[cm], wc)
        return choices, trans

    def bootstrap_weights(self, rng):
        """Resample scientists with replacement, separately for Italy and control."""
        w_author = np.zeros(self.n_authors)
        for flag in (True, False):
            idx = np.flatnonzero(self.author_is_it == flag)
            w_author[idx] = rng.multinomial(len(idx), np.full(len(idx), 1 / len(idx)))
        return w_author[self.author]


# ------------------------------------------------------------- fitting ------
def fit_groups(panel, pre_years, post_years, gamma, weights=None, choice_mask=None, warm=None):
    """Fit theta for the four groups; return dict group -> theta."""
    in_pre = np.isin(panel.year, pre_years)
    in_post = np.isin(panel.year, post_years)
    cells = {"IT_pre": panel.is_it & in_pre, "IT_post": panel.is_it & in_post,
             "CTRL_pre": ~panel.is_it & in_pre, "CTRL_post": ~panel.is_it & in_post}
    out = {}
    for name, mask in cells.items():
        choices, trans = panel.counts(mask, weights, choice_mask)
        theta0 = None if warm is None else warm[name]
        res = irl.fit_counts(choices, trans, gamma, theta0=theta0)
        out[name] = res["theta"]
        out[name + "_n"] = res["n"]
        out[name + "_ok"] = res["converged"]
    return out


def did(th):
    return (th["IT_post"] - th["IT_pre"]) - (th["CTRL_post"] - th["CTRL_pre"])


def run_did(panel, pre_years, post_years, gamma, n_boot, rng, choice_mask=None, label="main"):
    point = fit_groups(panel, pre_years, post_years, gamma, choice_mask=choice_mask)
    est = did(point)
    draws = []
    for b in range(n_boot):
        w = panel.bootstrap_weights(rng)
        th = fit_groups(panel, pre_years, post_years, gamma, weights=w,
                        choice_mask=choice_mask, warm=point)
        draws.append(did(th))
        if (b + 1) % 50 == 0:
            print(f"    [{label}] bootstrap {b + 1}/{n_boot}")
    draws = np.array(draws) if draws else np.full((0, len(irl.PARAMS)), np.nan)
    return point, est, draws


def summarise(est, draws):
    rows = []
    for k, p in enumerate(irl.PARAMS):
        lo, hi = (np.percentile(draws[:, k], [2.5, 97.5]) if len(draws) else (np.nan, np.nan))
        rows.append({"parameter": p, "did": est[k], "ci_low": lo, "ci_high": hi,
                     "boot_se": draws[:, k].std(ddof=1) if len(draws) > 1 else np.nan})
    return pd.DataFrame(rows)


def event_study(panel, gamma, n_boot, rng):
    """Italy-minus-control difference in each window, relative to the reference window."""
    def diffs(weights=None):
        out = {}
        for win in config.EVENT_WINDOWS:
            yrs = list(range(win[0], win[1] + 1))
            mask = np.isin(panel.year, yrs)
            th = {}
            for flag, name in ((True, "IT"), (False, "CTRL")):
                choices, trans = panel.counts(mask & (panel.is_it == flag), weights)
                th[name] = irl.fit_counts(choices, trans, gamma)["theta"]
            out[win] = th["IT"] - th["CTRL"]
        ref = out[config.EVENT_REFERENCE]
        return {win: v - ref for win, v in out.items()}

    point = diffs()
    boots = []
    for b in range(n_boot):
        boots.append(diffs(panel.bootstrap_weights(rng)))
        if (b + 1) % 25 == 0:
            print(f"    [event study] bootstrap {b + 1}/{n_boot}")
    rows = []
    for win in config.EVENT_WINDOWS:
        for k, p in enumerate(irl.PARAMS):
            bk = np.array([d[win][k] for d in boots]) if boots else np.array([])
            lo, hi = np.percentile(bk, [2.5, 97.5]) if len(bk) else (np.nan, np.nan)
            rows.append({"window": f"{win[0]}-{win[1]}", "start": win[0], "parameter": p,
                         "it_minus_ctrl_vs_ref": point[win][k], "ci_low": lo, "ci_high": hi})
    return pd.DataFrame(rows)


# ------------------------------------------------------------- figures ------
def plot_did(table, truth, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(7, 3.6))
    ys = np.arange(len(table))[::-1]
    ax.axvline(0, color="#888888", lw=1)
    ax.errorbar(table.did, ys, xerr=[table.did - table.ci_low, table.ci_high - table.did],
                fmt="o", color="#2a6fdb", ecolor="#2a6fdb", capsize=4, label="Estimate, 95% CI")
    if truth is not None:
        ax.scatter([truth[p] for p in table.parameter], ys, marker="x", s=70,
                   color="#d1495b", zorder=3, label="Planted true effect")
    ax.set_yticks(ys, [PRETTY[p] for p in table.parameter])
    ax.set_xlabel("Change in reward weight, Italy vs control (after minus before)")
    ax.set_title(title, loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=9, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_event(es, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 3, figsize=(13, 3.4), sharex=True)
    for ax, p in zip(axes, irl.PARAMS):
        d = es[es.parameter == p].sort_values("start")
        x = d.start + 0.5
        ax.axhline(0, color="#888888", lw=1)
        ax.axvspan(2010, 2013, color="#eeeeee", label="Reform transition")
        ax.fill_between(x, d.ci_low, d.ci_high, color="#2a6fdb", alpha=0.18)
        ax.plot(x, d.it_minus_ctrl_vs_ref, "o-", color="#2a6fdb")
        ax.set_title(PRETTY[p], loc="left", fontsize=11)
        ax.set_xlabel("Two-year window")
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    axes[0].set_ylabel("Italy minus control,\nrelative to 2008-09")
    axes[0].legend(frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ---------------------------------------------------------------- main ------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", default=os.path.join(config.DATA_DIR, "trajectories.csv"))
    ap.add_argument("--out", default=config.RESULTS_DIR)
    ap.add_argument("--n-boot", type=int, default=config.N_BOOT)
    ap.add_argument("--gamma", type=float, default=config.GAMMA)
    ap.add_argument("--truth", default=None, help="JSON with planted effects (simulation only)")
    ap.add_argument("--event-study", action="store_true")
    ap.add_argument("--by-career", action="store_true")
    ap.add_argument("--placebo-year", type=int, default=None,
                    help="fake reform year inside the pre-period, e.g. 2007")
    ap.add_argument("--balanced", action="store_true",
                    help="keep only scientists with choices both before and after (robustness)")
    ap.add_argument("--seed", type=int, default=config.SEED)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rng = np.random.default_rng(args.seed)
    df = pd.read_csv(args.input)
    if args.balanced:
        pre_ids = set(df.author_id[df.year.isin(config.PRE_YEARS)])
        post_ids = set(df.author_id[df.year.isin(config.POST_YEARS)])
        df = df[df.author_id.isin(pre_ids & post_ids)]
        print(f"Balanced panel: {df.author_id.nunique():,} scientists active before and after")
    panel = Panel(df)
    truth = None
    if args.truth:
        with open(args.truth) as f:
            truth = json.load(f)["did"]

    if args.placebo_year:
        pre = [y for y in config.PRE_YEARS if y < args.placebo_year]
        post = [y for y in config.PRE_YEARS if y >= args.placebo_year]
        tag = f"placebo_{args.placebo_year}"
    else:
        pre, post, tag = config.PRE_YEARS, config.POST_YEARS, "main"

    print(f"Loaded {len(panel.df):,} choices by {panel.n_authors:,} scientists from {args.input}")
    print(f"Before = {pre[0]}-{pre[-1]}, after = {post[0]}-{post[-1]}, gamma = {args.gamma}")

    # Choice shares, for a first look at the data
    sub = panel.df[panel.df.year.isin(pre + post)].copy()
    sub["period"] = np.where(sub.year.isin(pre), "before", "after")
    shares = (sub.groupby(["group", "period"]).action.value_counts(normalize=True)
              .unstack().reindex(columns=list(irl.ACTIONS)))
    shares.to_csv(os.path.join(args.out, f"choice_shares_{tag}.csv"))
    print("\nShare of each choice:\n", shares.round(3).to_string())

    print(f"\nFitting the model ({args.n_boot} bootstrap draws)...")
    point, est, draws = run_did(panel, pre, post, args.gamma, args.n_boot, rng, label=tag)

    weights = pd.DataFrame({g: point[g] for g in ("IT_pre", "IT_post", "CTRL_pre", "CTRL_post")},
                           index=list(irl.PARAMS))
    weights.loc["n_choices"] = [point[g + "_n"] for g in weights.columns]
    weights.loc["converged"] = [point[g + "_ok"] for g in weights.columns]
    weights.to_csv(os.path.join(args.out, f"weights_by_group_{tag}.csv"))

    table = summarise(est, draws)
    if truth is not None:
        table["true"] = [truth[p] for p in table.parameter]
        table["covered"] = (table.ci_low <= table.true) & (table.true <= table.ci_high)
    table.to_csv(os.path.join(args.out, f"did_{tag}.csv"), index=False)
    pd.DataFrame(draws, columns=list(irl.PARAMS)).to_csv(
        os.path.join(args.out, f"did_bootstrap_{tag}.csv"), index=False)

    print("\nReward weights by group:\n", weights.to_string())
    print("\nReform effect (difference-in-differences):\n", table.round(3).to_string(index=False))
    title = "Simulated data: estimated vs planted effect" if truth else "Effect of the reform on reward weights"
    plot_did(table, truth, os.path.join(args.out, f"did_{tag}.png"), title)

    if args.by_career:
        rows = []
        for k, label in enumerate(("0-5 years", "6-15 years", "16+ years")):
            print(f"\nCareer stage {label}...")
            _, est_k, draws_k = run_did(panel, pre, post, args.gamma, max(args.n_boot // 2, 0), rng,
                                        choice_mask=(panel.career == k), label=label)
            t = summarise(est_k, draws_k)
            t.insert(0, "career_stage", label)
            rows.append(t)
        by_career = pd.concat(rows)
        by_career.to_csv(os.path.join(args.out, f"did_by_career_{tag}.csv"), index=False)
        print("\nReform effect by career stage:\n", by_career.round(3).to_string(index=False))

    if args.event_study:
        print("\nEvent study...")
        es = event_study(panel, args.gamma, max(args.n_boot // 2, 0), rng)
        es.to_csv(os.path.join(args.out, "event_study.csv"), index=False)
        plot_event(es, os.path.join(args.out, "event_study.png"))
        print(es[es.parameter != "theta_near"].round(3).to_string(index=False))

    print(f"\nResults saved in {args.out}")


if __name__ == "__main__":
    main()
