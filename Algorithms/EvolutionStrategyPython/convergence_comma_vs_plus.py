"""
WP2 convergence-speed comparison: baseline (mu,lambda)="comma" vs (mu+lambda)="plus".

Reuses the Benchmark runner from benchmark_Cala.py, holding everything at the
shared baseline (SINGLE_VARIANCE, pop=30, children=7, archive off, LHS-free
defaults) and varying ONLY the selection scheme. Produces a single convergence
figure (best fitness vs evaluations, one panel per n_circles) so we can read off
how fast comma vs plus closes the gap to the known optimum over 100k evaluations.

Run from this directory:
    python convergence_comma_vs_plus.py

Output: results/WP2/plots/convergence_comma_vs_plus_100k.png
        results/WP2/convergence_comma_vs_plus_per_run.csv   (raw data, for reproducibility)
"""

import math
import os
import sys
from statistics import mean

import matplotlib

matplotlib.use("Agg")  # headless: just save the figure, never pop a window
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from benchmark_Cala import Benchmark, KNOWN_OPTIMA
from ES.evopy.strategy import Strategy

# ── Config ───────────────────────────────────────────────────────────────────
N_CIRCLES_LIST = [5, 7, 10, 15, 20]   # standard study set
N_RUNS = 25                            # seeds per (n, scheme) — matches baseline
MAX_EVALS = 100_000

# Selection schemes to compare: comma is the baseline, plus is the WP2 contrast.
SCHEME_STYLE = {
    "comma": dict(color="#1f77b4", label="(μ,λ) comma  [baseline]"),
    "plus":  dict(color="#d62728", label="(μ+λ) plus"),
}

# repo_root/Algorithms/EvolutionStrategyPython/this_file.py  →  repo_root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLOTS_DIR = os.path.join(REPO_ROOT, "results", "WP2", "plots")
CSV_PATH = os.path.join(REPO_ROOT, "results", "WP2", "convergence_comma_vs_plus_per_run.csv")
PLOT_PATH = os.path.join(PLOTS_DIR, "convergence_comma_vs_plus_100k.png")


def mean_trace(runs):
    """Step-interpolate every run's (eval, fitness) trace onto a common eval grid
    and return (evals, mean_fitness) — the average best-so-far across seeds."""
    all_evals = sorted({ev for r in runs for ev, _ in r.trace})
    evals, fits = [], []
    for ev in all_evals:
        vals = []
        for r in runs:
            past = [f for e, f in r.trace if e <= ev]
            if past:
                vals.append(past[-1])
        if vals:
            evals.append(ev)
            fits.append(mean(vals))
    return evals, fits


def plot_convergence(bench):
    n_list = sorted({r.n_circles for r in bench.results})
    n_cols = min(2, len(n_list))
    n_rows = math.ceil(len(n_list) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(7 * n_cols, 4 * n_rows), squeeze=False)
    fig.suptitle(
        "Convergence speed — (μ,λ) comma baseline vs (μ+λ) plus "
        f"(SINGLE_VARIANCE, {N_RUNS} seeds, {MAX_EVALS:,} evals)",
        fontsize=13,
    )

    for idx, n in enumerate(n_list):
        ax = axes[idx // n_cols][idx % n_cols]
        optimum = KNOWN_OPTIMA[n - 2]

        for scheme, style in SCHEME_STYLE.items():
            runs = [r for r in bench.results
                    if r.n_circles == n and r.selection_scheme == scheme]
            if not runs:
                continue
            # faint individual seeds
            for r in runs:
                if r.trace:
                    evals, fits = zip(*r.trace)
                    ax.plot(evals, fits, color=style["color"], alpha=0.12, linewidth=0.7)
            # bold mean-of-seeds trace
            mevals, mfits = mean_trace(runs)
            if mevals:
                ax.plot(mevals, mfits, color=style["color"], linewidth=2.2,
                        label=style["label"])

        ax.axhline(optimum, color="black", linewidth=1, linestyle="--",
                   label=f"optimum ({optimum:.4f})")
        ax.set_title(f"{n} circles")
        ax.set_xlabel("Evaluations")
        ax.set_ylabel("Best fitness (min pairwise distance)")
        ax.legend(fontsize=8, loc="lower right")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    for idx in range(len(n_list), n_rows * n_cols):
        axes[idx // n_cols][idx % n_cols].set_visible(False)

    fig.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    fig.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    print(f"\nConvergence plot saved -> {PLOT_PATH}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    bench = Benchmark(
        n_circles_list=N_CIRCLES_LIST,
        strategies=[Strategy.SINGLE_VARIANCE],
        selection_schemes=list(SCHEME_STYLE.keys()),  # comma vs plus only
        archive_modes=["off"],                          # baseline: no archive
        population_sizes=[30],
        num_children_list=[7],
        n_runs=N_RUNS,
        max_evaluations=MAX_EVALS,
        verbose=True,
    )

    bench.run_all()
    bench.print_table()

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    bench.save_csv(CSV_PATH)
    plot_convergence(bench)


if __name__ == "__main__":
    main()
