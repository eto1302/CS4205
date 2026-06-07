"""Q1 — Per-seed scatter showing variance of interleaved vs final polish vs baseline.

Run from the EvolutionStrategyPython directory:
    uv run --with matplotlib --with pandas --with numpy plot_wp5_variance.py
"""
import matplotlib
matplotlib.use("Agg")

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

RESULTS_CSV = "results/per_run.csv"
OUT_PATH    = "plots_wp1/wp5_variance.png"

TREATMENTS = {
    "baseline":              ("Baseline",           "steelblue"),
    "B+final_polish":        ("Final polish",        "darkorange"),
    "B+interleaved_polish":  ("Interleaved polish",  "crimson"),
}

N_ORDER = [7, 10, 15, 20]


def strip_and_box(ax, groups, colors, labels):
    """Box plot + individual seed dots for a list of arrays."""
    rng = np.random.default_rng(0)
    positions = range(len(groups))

    bp = ax.boxplot(
        groups,
        positions=positions,
        widths=0.35,
        patch_artist=True,
        medianprops=dict(color="black", linewidth=1.5),
        whiskerprops=dict(linewidth=1.0),
        capprops=dict(linewidth=1.0),
        flierprops=dict(marker=""),
        showfliers=False,
    )
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.35)

    for i, (vals, color) in enumerate(zip(groups, colors)):
        jitter = rng.uniform(-0.14, 0.14, size=len(vals))
        ax.scatter(i + jitter, vals, color=color, s=18, alpha=0.7, zorder=3)

    ax.set_xticks(list(positions))
    ax.set_xticklabels(labels, fontsize=8)


def main():
    os.makedirs("plots_wp1", exist_ok=True)

    df = pd.read_csv(RESULTS_CSV)
    df = df[df["treatment"].isin(TREATMENTS)]

    fig, axes = plt.subplots(1, 4, figsize=(14, 4), sharey=False)

    for ax, n in zip(axes, N_ORDER):
        sub = df[df["n_circles"] == n]
        groups = [sub[sub["treatment"] == t]["final_gap"].values for t in TREATMENTS]
        colors = [TREATMENTS[t][1] for t in TREATMENTS]
        labels = [TREATMENTS[t][0] for t in TREATMENTS]

        strip_and_box(ax, groups, colors, labels)
        ax.set_title(f"n = {n}", fontsize=11)
        ax.set_ylabel("Final gap (lower = better)" if n == 7 else "")
        ax.set_ylim(bottom=0)
        ax.axhline(0, color="grey", linewidth=0.5, linestyle="--")

    legend_handles = [
        mpatches.Patch(color=TREATMENTS[t][1], label=TREATMENTS[t][0], alpha=0.7)
        for t in TREATMENTS
    ]
    fig.legend(handles=legend_handles, loc="upper right", fontsize=9, framealpha=0.9)
    fig.suptitle("Per-seed final gap distribution by treatment (25 seeds each)", fontsize=12)

    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved {OUT_PATH}")

    # Quick sanity print
    for t in TREATMENTS:
        for n in N_ORDER:
            vals = df[(df["treatment"] == t) & (df["n_circles"] == n)]["final_gap"].values
            print(f"  {t:28s}  n={n}  median={np.median(vals):.4f}  IQR={np.percentile(vals,75)-np.percentile(vals,25):.4f}")


if __name__ == "__main__":
    main()
