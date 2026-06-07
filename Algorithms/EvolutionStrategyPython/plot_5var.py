"""Replot the 5-variant stacked convergence figure with a clean title + legend.

Reads results/STACKED_5var/traces.csv (4 stacked variants + the final-polish+archive
variant) and renders the convergence figure with:
  - title:  "stacked improvements"
  - the new variant's legend label: "+clip+f-polish+bookkeeping"

Run: uv run --with numpy --with matplotlib plot_5var.py
"""
import os
import csv
import math
import shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

import stacked_benchmark as sb
import ofat_benchmark as ofat

OUT = os.path.join(sb.REPO_ROOT, "results", "STACKED_5var")
OVERLEAF = ("/mnt/c/Users/user/uni-notes/courses/CS4205-evolutionary-algorithms/assignments/"
            "groupwork-notes/wp1-presentation-figs/overleaf-STACKED")
MAX_EVALS = 100000

# (data key in traces.csv, legend label, colour)
VARIANTS = [
    ("baseline",               "baseline",                 "#7f7f7f"),
    ("+clip",                  "+clip",                    "#1f77b4"),
    ("+clip+polish",           "+clip+polish",             "#2ca02c"),
    ("+clip+polish+archive",   "+clip+polish+archive",     "#9467bd"),
    ("+clip+f-polish+archive", "+clip+f-polish+bookkeeping", "#ff7f0e"),
]


def load_traces():
    tmp = {}
    with open(os.path.join(OUT, "traces.csv")) as f:
        for row in csv.DictReader(f):
            key = (row["variant"], int(row["n_circles"]), int(row["seed"]))
            tmp.setdefault(key, []).append((float(row["evaluations"]), float(row["best_fitness"])))
    traces = {}
    for (v, n, _s), pts in tmp.items():
        pts.sort()
        ev = np.array([p[0] for p in pts]); bsf = np.array([p[1] for p in pts])
        traces.setdefault((v, n), []).append((ev, bsf))
    return traces


def main():
    traces = load_traces()
    n_list = sorted({n for _, n in traces})
    n_cols = min(2, len(n_list)); n_rows = math.ceil(len(n_list) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(7 * n_cols, 4 * n_rows), squeeze=False)
    fig.suptitle("stacked improvements", fontsize=15)
    yticks = [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
    for idx, n in enumerate(n_list):
        ax = axes[idx // n_cols][idx % n_cols]
        target = ofat.get_target(n)
        grid = np.linspace(1, MAX_EVALS, 200)
        for key, leg, col in VARIANTS:
            st = traces.get((key, n))
            if not st:
                continue
            med = sb._median_gap_grid(st, target, grid)
            ax.plot(grid, med, color=col, lw=2.2, label=leg)
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(mticker.FixedLocator(yticks))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:g}"))
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
        ax.set_title(f"{n} circles")
        ax.set_xlabel("Evaluations")
        ax.set_ylabel("Median relative gap to optimum  (lower = better)")
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(fontsize=8, loc="upper right")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    for idx in range(len(n_list), n_rows * n_cols):
        axes[idx // n_cols][idx % n_cols].set_visible(False)
    fig.tight_layout()
    os.makedirs(os.path.join(OUT, "plots"), exist_ok=True)
    p = os.path.join(OUT, "plots", "convergence_stacked_5var.png")
    fig.savefig(p, dpi=150, bbox_inches="tight")
    plt.close(fig)
    shutil.copy(p, os.path.join(OVERLEAF, "convergence_stacked_5var_finalpolish_100k.png"))
    print("saved + copied -> overleaf-STACKED/convergence_stacked_5var_finalpolish_100k.png")


if __name__ == "__main__":
    main()
