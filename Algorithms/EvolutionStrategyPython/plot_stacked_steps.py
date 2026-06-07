"""Marginal-contribution plot for the stacked chain.

Reads results/STACKED/per_run.csv and shows, for each problem size n, how much
gap each improvement removes *relative to the step before it* (not vs baseline).
This is the plot that demonstrates "clip is the entire improvement": the clip
bars are large and significant, polish/archive bars sit at ~0 (or below).

Run: uv run --with numpy --with scipy --with matplotlib plot_stacked_steps.py
"""
import os
import csv

import numpy as np
from scipy.stats import mannwhitneyu

import stats as S   # boot_ci, a12, marker

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Match stacked_benchmark.py's budget-aware folder (STK_EVALS / STK_TAG).
_MAX_EVALS = int(os.environ.get("STK_EVALS", "100000"))
TAG       = os.environ.get("STK_TAG", "" if _MAX_EVALS == 100000 else f"_{_MAX_EVALS // 1000}k")
OUT_DIR   = os.path.join(REPO_ROOT, "results", "STACKED" + TAG)
PER_RUN   = os.path.join(OUT_DIR, "per_run.csv")
PLOTS_DIR = os.path.join(OUT_DIR, "plots")

# (prev label, next label, display name, colour) — the order improvements switch on
STEPS = [
    ("baseline",     "+clip",                "+ clip repair (WP3)",       "#1f77b4"),
    ("+clip",        "+clip+polish",         "+ gradient polish (WP5)",   "#2ca02c"),
    ("+clip+polish", "+clip+polish+archive", "+ elitist archive (WP2)",   "#9467bd"),
]


def col(rows, t, n):
    return np.array([float(r["final_gap"]) for r in rows
                     if r["treatment"] == t and int(r["n_circles"]) == n])


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    rows = list(csv.DictReader(open(PER_RUN)))
    ns = sorted({int(r["n_circles"]) for r in rows})

    fig, ax = plt.subplots(figsize=(10, 6))
    n_steps = len(STEPS)
    width = 0.8 / n_steps
    x = np.arange(len(ns))

    for i, (prev, nxt, name, color) in enumerate(STEPS):
        effects, los, his, markers = [], [], [], []
        for n in ns:
            a, b = col(rows, prev, n), col(rows, nxt, n)
            eff = float(np.median(a) - np.median(b))     # >0 = this step lowered the gap
            lo, hi = S.boot_ci(a, b)
            p = mannwhitneyu(b, a, alternative="two-sided").pvalue
            effects.append(eff); los.append(eff - lo); his.append(hi - eff)
            markers.append(S.marker(p))
        xpos = x + (i - (n_steps - 1) / 2) * width
        yerr = np.vstack([np.clip(los, 0, None), np.clip(his, 0, None)])
        bars = ax.bar(xpos, effects, width, yerr=yerr, capsize=3, color=color,
                      label=name, edgecolor="black", linewidth=0.5)
        for xb, eff, mk in zip(xpos, effects, markers):
            ax.annotate(mk, (xb, eff), textcoords="offset points",
                        xytext=(0, 4 if eff >= 0 else -12), ha="center",
                        fontsize=9, fontweight="bold",
                        color="#222" if mk != "ns" else "#999")

    ax.axhline(0, color="black", lw=1)
    ax.set_xticks(x); ax.set_xticklabels([f"n={n}" for n in ns])
    ax.set_ylabel("Reduction in median relative gap vs the PREVIOUS step\n"
                  "(relative gap = (optimum − achieved)/optimum;  higher = this step helped;  < 0 = it hurt)")
    ax.set_xlabel("Problem size")
    ax.set_title("Stacked improvements — marginal contribution of each step\n"
                 "clip removes essentially all the gap; polish & archive add nothing "
                 "(*** p<1e-3, ** p<1e-2, * p<0.05, ns)", fontsize=11)
    ax.legend(title="step added", fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    out = os.path.join(PLOTS_DIR, "marginal_contribution_stacked.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {out}")


if __name__ == "__main__":
    main()
