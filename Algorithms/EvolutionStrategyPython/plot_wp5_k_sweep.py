"""Q2 — Plot k sensitivity sweep results.

Reads results/per_run_k_sweep.csv (written by wp5_k_sweep.py) and plots
median final_gap vs k for each n_circles, with IQR bands.

Run:  python3 plot_wp5_k_sweep.py
"""
import matplotlib
matplotlib.use("Agg")

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

IN_CSV   = "results/per_run_k_sweep.csv"
OUT_PATH = "plots_wp1/wp5_k_sweep.png"

N_COLORS = {7: "steelblue", 10: "darkorange", 15: "forestgreen", 20: "crimson"}
K_VALUES = [5, 10, 20, 50]


def main():
    if not os.path.exists(IN_CSV):
        print(f"ERROR: {IN_CSV} not found — run wp5_k_sweep.py first.")
        return

    os.makedirs("plots_wp1", exist_ok=True)

    df = pd.read_csv(IN_CSV)
    ns = sorted(df["n_circles"].unique())

    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    # Left: median final_gap vs k
    ax = axes[0]
    for n in ns:
        color = N_COLORS.get(n, "black")
        sub = df[df["n_circles"] == n]
        medians = [sub[sub["k"] == k]["final_gap"].median() for k in K_VALUES]
        q25     = [sub[sub["k"] == k]["final_gap"].quantile(0.25) for k in K_VALUES]
        q75     = [sub[sub["k"] == k]["final_gap"].quantile(0.75) for k in K_VALUES]
        ax.plot(K_VALUES, medians, marker="o", color=color, label=f"n={n}", linewidth=1.5)
        ax.fill_between(K_VALUES, q25, q75, color=color, alpha=0.15)

    ax.set_xscale("log")
    ax.set_xticks(K_VALUES)
    ax.set_xticklabels([str(k) for k in K_VALUES])
    ax.set_xlabel("k (polish interval, generations)", fontsize=10)
    ax.set_ylabel("Median final gap", fontsize=10)
    ax.set_title("Final gap vs polish interval k", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # Right: mean L-BFGS-B evals per call vs k (shows eval cost trade-off)
    ax = axes[1]
    for n in ns:
        color = N_COLORS.get(n, "black")
        sub = df[df["n_circles"] == n]
        mean_calls = [sub[sub["k"] == k]["lbfgsb_calls"].median() for k in K_VALUES]
        ax.plot(K_VALUES, mean_calls, marker="s", color=color, label=f"n={n}", linewidth=1.5)

    ax.set_xscale("log")
    ax.set_xticks(K_VALUES)
    ax.set_xticklabels([str(k) for k in K_VALUES])
    ax.set_xlabel("k (polish interval, generations)", fontsize=10)
    ax.set_ylabel("Median number of L-BFGS-B calls", fontsize=10)
    ax.set_title("Polish call count vs k", fontsize=11)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.suptitle(f"k sensitivity sweep — interleaved L-BFGS-B polish ({df['seed'].nunique()} seeds per k×n)",
                 fontsize=12)
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved {OUT_PATH}")

    # Summary table
    print("\nMedian final_gap by k and n:")
    pivot = df.groupby(["n_circles", "k"])["final_gap"].median().unstack("k")
    print(pivot.to_string())


if __name__ == "__main__":
    main()
