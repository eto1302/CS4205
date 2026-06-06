"""WP1 init-scheme figures: 'does where you start matter?'

Two team-style figures answering Leo's question — is LHS an improvement over a
random start, and how do the clustered / warm-start inits compare to random:

  figs/wp1_init_forest.png  — the 'tree thing': init effect vs a random start,
                              for LHS and for the clustered warm-start, all n.
  figs/wp1_init_box.png     — intuitive final-gap boxplots, all 4 init schemes.

Data sources (both read from findings/data/, all single-variance, 25 seeds, 100k):
  - LHS vs uniform  -> wp1_comparisons.csv      (the canonical OFAT arm B-no_lhs)
  - lhs/uniform per-run final gaps -> wp1_per_run.csv (treatment baseline / B-no_lhs)
  - random vs cluster_corner -> wp1_init_per_run.csv  (extracted from the older
    benchmark.py raw curves; stats recomputed here with the SAME Mann-Whitney +
    A12 + bootstrap-CI recipe the shared pipeline uses).

Caveat (annotated on the forest): the LHS row comes from the OFAT pipeline
(bug-fixed code, LHS baseline vs uniform) while the clustered row comes from the
older benchmark harness (random vs cluster_corner). 'uniform' and 'random' are
both un-stratified box fills but not byte-identical harnesses — so read this as
'no init scheme separates from a random start', not a single controlled sweep.

Run:  uv run --with matplotlib --with numpy --with scipy wp1_init_figs.py
"""
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

DATA = "data"
FIGS = "figs"
os.makedirs(FIGS, exist_ok=True)
NS = [7, 10, 15, 20]

C = {"baseline": "#7f7f7f", "good": "#2ca02c", "bad": "#d62728",
     "blue": "#4C72B0", "orange": "#DD8452", "green": "#55A868",
     "purple": "#8172B3", "grey": "#999999"}
plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
                     "figure.dpi": 150, "font.size": 10})


def read(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def a12(x, y):
    """P(X<Y) + 0.5 P(=) with 'smaller gap = better' -> chance that x beats y."""
    gt = sum(1 for a in x for b in y if a < b)
    eq = sum(1 for a in x for b in y if a == b)
    return (gt + 0.5 * eq) / (len(x) * len(y))


def boot_ci(ref, arm, B=5000):
    """Bootstrap 95% CI of the improvement median(ref) - median(arm)."""
    rng = np.random.default_rng(0)
    # improvement = median(ref) - median(arm)  -> >0 means arm has the smaller gap
    # (arm better), plotted to the RIGHT, matching the team pipeline (stats.py:123).
    d = [np.median(rng.choice(ref, len(ref))) - np.median(rng.choice(arm, len(arm)))
         for _ in range(B)]
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def marker(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"


# ── gather effects: each row = (label, n, effect, lo, hi, a12, marker) ─────────
def lhs_rows():
    """LHS effect vs random (uniform), straight from the OFAT comparisons."""
    comp = [r for r in read(f"{DATA}/wp1_comparisons.csv")
            if r["treatment"] == "B-no_lhs" and r["metric"] == "final_gap" and r["effect"] != ""]
    rows = []
    for r in comp:
        # OFAT 'effect' = median(base=lhs) - median(arm=uniform).  We want the
        # IMPROVEMENT of LHS over the random (uniform) start = median(uniform) -
        # median(lhs) = -effect, so >0 = LHS better, plotted RIGHT (team convention).
        eff = -float(r["effect"]); lo = -float(r["ci_hi"]); hi = -float(r["ci_lo"])
        a = 1.0 - float(r["a12"])  # A12 was P(uniform beats lhs); flip to P(lhs beats uniform)
        rows.append(("LHS", int(r["n_circles"]), eff, lo, hi, round(a, 3), r["marker"]))
    return rows


def cluster_rows():
    """Clustered warm-start effect vs random, recomputed from per-run final gaps."""
    runs = read(f"{DATA}/wp1_init_per_run.csv")
    def gaps(n, init):
        return np.array([float(r["final_gap"]) for r in runs
                         if int(r["n_circles"]) == n and r["init_mode"] == init])
    rows = []
    for n in NS:
        rnd = gaps(n, "random"); clu = gaps(n, "cluster_corner")
        eff = float(np.median(rnd) - np.median(clu))   # improvement of clustered over random (>0 = better, RIGHT)
        lo, hi = boot_ci(rnd, clu)
        a = a12(clu, rnd)                               # P(clustered beats random)
        _, p = mannwhitneyu(rnd, clu, alternative="two-sided")
        rows.append(("clustered\nwarm-start", n, eff, lo, hi, round(a, 3), marker(p)))
    return rows


def forest():
    groups = [("LHS", C["blue"], lhs_rows()),
              ("clustered\nwarm-start", C["orange"], cluster_rows())]
    fig, ax = plt.subplots(figsize=(9, 6))
    yticks, ylabels = [], []
    y = 0
    for gname, gcol, rows in groups:
        rows = sorted(rows, key=lambda r: r[1])
        for (_, n, eff, lo, hi, a, mk) in rows:
            sig = mk != "ns"
            ax.plot([lo, hi], [y, y], color=gcol, lw=2.4, alpha=.85)
            ax.scatter([eff], [y], s=110, zorder=3, edgecolor="black",
                       facecolor=gcol if sig else "white")
            ax.annotate(f"{mk}  A12={a:.2f}", (max(hi, 0), y), textcoords="offset points",
                        xytext=(8, 0), va="center", fontsize=8, color=C["grey"])
            yticks.append(y); ylabels.append(f"{gname.splitlines()[0]}  (n={n})")
            y += 1
        y += 0.8  # gap between groups
    ax.axvline(0, color="black", lw=1.3)
    ax.text(0, y - 0.3, "  random start (reference)", fontsize=8, color="black", va="center")
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels)
    ax.set_xlabel("improvement in gap vs a random start   (right = better than random)  + bootstrap 95% CI")
    ax.set_title("WP1 · Does where you start matter?  No scheme separates from random\n"
                 "single-variance, 25 seeds, 100k evals — every CI crosses 0 (all ns)")
    # honest harness note
    ax.annotate("LHS row: OFAT pipeline (lhs vs uniform)\nclustered row: older benchmark (random vs cluster_corner)",
                xy=(0.5, -0.16), xycoords="axes fraction", ha="center", fontsize=7.5,
                color=C["grey"], style="italic")
    fig.tight_layout()
    fig.savefig(f"{FIGS}/wp1_init_forest.png", bbox_inches="tight")
    plt.close(fig)
    print("wp1_init_forest.png")


def boxplot():
    ofat = read(f"{DATA}/wp1_per_run.csv")
    init = read(f"{DATA}/wp1_init_per_run.csv")
    def og(n, tr):
        return [float(r["final_gap"]) for r in ofat
                if int(r["n_circles"]) == n and r["treatment"] == tr]
    def ig(n, mode):
        return [float(r["final_gap"]) for r in init
                if int(r["n_circles"]) == n and r["init_mode"] == mode]
    schemes = [("LHS", "baseline", C["blue"], og),
               ("uniform", "B-no_lhs", C["green"], og),
               ("random", "random", C["grey"], ig),
               ("clustered", "cluster_corner", C["orange"], ig)]
    fig, axes = plt.subplots(1, len(NS), figsize=(13, 4), sharey=False)
    for ax, n in zip(axes, NS):
        data, colors, labels = [], [], []
        for name, key, col, getter in schemes:
            data.append(getter(n, key)); colors.append(col); labels.append(name)
        bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=False)
        for patch, col in zip(bp["boxes"], colors):
            patch.set_facecolor(col); patch.set_alpha(0.55)
        for med in bp["medians"]:
            med.set_color("black"); med.set_linewidth(1.6)
        # divider: schemes 1-2 = bug-fixed OFAT harness, 3-4 = older benchmark harness.
        # Only compare WITHIN a half — across the line mixes harness + init definition.
        ax.axvline(2.5, color="black", ls=":", lw=1.1, alpha=0.6)
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.set_title(f"n = {n}")
        if ax is axes[0]:
            ax.set_ylabel("final gap to optimum (lower = better)")
    fig.suptitle("WP1 · Final-gap by init scheme — within each harness (dotted split) the boxes overlap: "
                 "init is a wash at 100k\n"
                 "left of split = bug-fixed OFAT (LHS vs uniform);  right = older benchmark (random vs clustered) "
                 "— don't compare across the split (harness + init-defn differ)",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(f"{FIGS}/wp1_init_box.png", bbox_inches="tight")
    plt.close(fig)
    print("wp1_init_box.png")


# ── CLEAN single-harness sweep (wp1_init_sweep.py output) ─────────────────────
# All four schemes share baseline-B; only the init differs; reference = random
# (uniform). No harness/code-version confound — this is the bulletproof version.
SWEEP = f"{DATA}/wp1_init_sweep_per_run.csv"
_LABEL = {"lhs": "LHS", "warm": "warm-start\n(Gaussian)", "clustered": "clustered\n(corner)"}
_COL = {"lhs": C["blue"], "warm": C["purple"], "clustered": C["orange"]}


def _sweep_gaps(rows, n, scheme):
    return np.array([float(r["final_gap"]) for r in rows
                     if int(r["n_circles"]) == n and r["init_scheme"] == scheme])


def clean_forest():
    if not os.path.exists(SWEEP):
        print("clean_forest: sweep CSV not ready — run wp1_init_sweep.py first"); return
    rows = read(SWEEP)
    fig, ax = plt.subplots(figsize=(9, 6.2))
    yticks, ylabels = [], []
    y = 0
    for scheme in ["clustered", "warm", "lhs"]:   # bottom-up so LHS sits lowest
        for n in sorted(NS, reverse=True):
            ref = _sweep_gaps(rows, n, "random"); arm = _sweep_gaps(rows, n, scheme)
            if len(ref) == 0 or len(arm) == 0:
                continue
            eff = float(np.median(ref) - np.median(arm))   # improvement of arm over random (>0 = better, RIGHT)
            lo, hi = boot_ci(ref, arm)
            a = a12(arm, ref); _, p = mannwhitneyu(ref, arm, alternative="two-sided")
            mk = marker(p); sig = mk != "ns"
            col = _COL[scheme]
            ax.plot([lo, hi], [y, y], color=col, lw=2.4, alpha=.85)
            ax.scatter([eff], [y], s=110, zorder=3, edgecolor="black",
                       facecolor=col if sig else "white")
            ax.annotate(f"{mk}  A12={a:.2f}", (max(hi, 0), y), textcoords="offset points",
                        xytext=(8, 0), va="center", fontsize=8, color=C["grey"])
            yticks.append(y); ylabels.append(f"{_LABEL[scheme].splitlines()[0]}  (n={n})")
            y += 1
        y += 0.8
    ax.axvline(0, color="black", lw=1.3)
    ax.set_ylim(-0.8, y - 0.2)
    ax.annotate("random (uniform) start = reference (x=0)", xy=(0, -0.6),
                xytext=(6, 0), textcoords="offset points", fontsize=8, va="center", color="black")
    ax.set_yticks(yticks); ax.set_yticklabels(ylabels)
    ax.set_xlabel("improvement in gap vs the random start   (right = better than random)  + bootstrap 95% CI")
    ax.set_title("WP1 · Clean init sweep — ONE harness, baseline-B, only init varies\n"
                 "single-variance, 25 seeds, 100k evals — no scheme separates from random")
    fig.tight_layout()
    fig.savefig(f"{FIGS}/wp1_init_sweep_forest.png", bbox_inches="tight")
    plt.close(fig)
    print("wp1_init_sweep_forest.png")


def clean_box():
    if not os.path.exists(SWEEP):
        print("clean_box: sweep CSV not ready — run wp1_init_sweep.py first"); return
    rows = read(SWEEP)
    order = ["random", "lhs", "warm", "clustered"]
    labels = ["random\n(uniform)", "LHS", "warm-start", "clustered"]
    cols = [C["grey"], C["blue"], C["purple"], C["orange"]]
    fig, axes = plt.subplots(1, len(NS), figsize=(13, 4))
    for ax, n in zip(axes, NS):
        data = [_sweep_gaps(rows, n, s) for s in order]
        if any(len(d) == 0 for d in data):
            continue
        bp = ax.boxplot(data, patch_artist=True, widths=0.6, showfliers=False)
        for patch, col in zip(bp["boxes"], cols):
            patch.set_facecolor(col); patch.set_alpha(0.55)
        for med in bp["medians"]:
            med.set_color("black"); med.set_linewidth(1.6)
        ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
        ax.set_title(f"n = {n}")
        if ax is axes[0]:
            ax.set_ylabel("final gap to optimum (lower = better)")
    fig.suptitle("WP1 · Clean init sweep — same harness, 25 seeds: boxes overlap at every n "
                 "(initialization is a wash at 100k)", fontsize=11)
    fig.tight_layout()
    fig.savefig(f"{FIGS}/wp1_init_sweep_box.png", bbox_inches="tight")
    plt.close(fig)
    print("wp1_init_sweep_box.png")


if __name__ == "__main__":
    forest()
    boxplot()
    clean_forest()
    clean_box()
