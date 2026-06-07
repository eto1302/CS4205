"""Q4 — L-BFGS-B evaluation budget consumption per call.

Shows how many evaluations each L-BFGS-B call consumes, and what fraction
of the total 100k budget goes to gradient search vs EA search.

Run from the EvolutionStrategyPython directory:
    python3 plot_wp5_lbfgsb.py
"""
import matplotlib
matplotlib.use("Agg")

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

RESULTS_CSV = "results/per_run.csv"
OUT_PATH    = "plots_wp1/wp5_lbfgsb.png"
MAX_EVALS   = 100_000
N_ORDER     = [7, 10, 15, 20]
N_COLORS    = {7: "steelblue", 10: "darkorange", 15: "forestgreen", 20: "crimson"}


def main():
    os.makedirs("plots_wp1", exist_ok=True)

    df = pd.read_csv(RESULTS_CSV)
    wp5 = df[df["wp"] == "WP5"].copy()

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    # --- Panel 1: evals per call vs n (both treatments) ---
    ax = axes[0]
    for treat, marker, label in [
        ("B+interleaved_polish", "o", "Interleaved"),
        ("B+final_polish",       "s", "Final"),
    ]:
        sub = wp5[wp5["treatment"] == treat]
        medians = [sub[sub["n_circles"] == n]["lbfgsb_evals_mean"].median() for n in N_ORDER]
        ax.plot(N_ORDER, medians, marker=marker, linewidth=1.5, label=label)

    ax.set_xlabel("n circles  (dimensionality = 2n)", fontsize=9)
    ax.set_ylabel("Median evals per L-BFGS-B call", fontsize=9)
    ax.set_title("Evals per call — scales with dim", fontsize=10)
    ax.set_xticks(N_ORDER)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    # --- Panel 2: number of polish calls vs n (interleaved only) ---
    ax = axes[1]
    sub = wp5[wp5["treatment"] == "B+interleaved_polish"]
    medians_calls = [sub[sub["n_circles"] == n]["lbfgsb_calls"].median() for n in N_ORDER]
    ax.bar(N_ORDER, medians_calls,
           color=[N_COLORS[n] for n in N_ORDER], width=1.2, alpha=0.75)
    for i, (n, v) in enumerate(zip(N_ORDER, medians_calls)):
        ax.text(n, v + 0.3, f"{v:.0f}", ha="center", fontsize=9)
    ax.set_xlabel("n circles", fontsize=9)
    ax.set_ylabel("Median L-BFGS-B calls per run", fontsize=9)
    ax.set_title("Fewer calls at larger n\n(each call consumes more budget)", fontsize=10)
    ax.set_xticks(N_ORDER)
    ax.grid(True, alpha=0.3, axis="y")

    # --- Panel 3: budget split — EA vs polish (interleaved) ---
    ax = axes[2]
    sub = wp5[wp5["treatment"] == "B+interleaved_polish"]
    for n in N_ORDER:
        vals = sub[sub["n_circles"] == n]["lbfgsb_evals_total"].values
        polish_pct = vals / MAX_EVALS * 100
        ax.scatter([n] * len(polish_pct),
                   polish_pct,
                   alpha=0.4, color=N_COLORS[n], s=18, zorder=3)
        ax.hlines(np.median(polish_pct), n - 0.4, n + 0.4,
                  color=N_COLORS[n], linewidth=2.0)

    ax.set_xlabel("n circles", fontsize=9)
    ax.set_ylabel("% of 100k budget consumed by L-BFGS-B", fontsize=9)
    ax.set_title("Budget eaten by polish (interleaved)", fontsize=10)
    ax.set_xticks(N_ORDER)
    ax.set_ylim(0, 105)
    ax.axhline(50, color="grey", linewidth=0.8, linestyle="--", label="50% threshold")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    fig.suptitle("L-BFGS-B budget consumption (interleaved polish, 25 seeds per n)", fontsize=12)
    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved {OUT_PATH}")

    # Print summary table
    print("\nSummary — Median evals per L-BFGS-B call:")
    print(f"{'n':>4}  {'Interleaved':>14}  {'Final':>10}  {'% budget to polish':>20}")
    sub_i = wp5[wp5["treatment"] == "B+interleaved_polish"]
    sub_f = wp5[wp5["treatment"] == "B+final_polish"]
    for n in N_ORDER:
        ie = sub_i[sub_i["n_circles"] == n]["lbfgsb_evals_mean"].median()
        fe = sub_f[sub_f["n_circles"] == n]["lbfgsb_evals_mean"].median()
        pct = sub_i[sub_i["n_circles"] == n]["lbfgsb_evals_total"].median() / MAX_EVALS * 100
        print(f"{n:>4}  {ie:>14.0f}  {fe:>10.0f}  {pct:>20.1f}%")


if __name__ == "__main__":
    main()
