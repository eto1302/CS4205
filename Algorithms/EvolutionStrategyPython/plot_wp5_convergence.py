"""Q3 — Convergence curves for interleaved polish on n=10 vs n=15.

Shows where L-BFGS-B fires (tick marks), whether each call improved the
best fitness (green = improved, grey = no improvement), and why the polish
helps at n=15 but not n=10.

Run from the EvolutionStrategyPython directory:
    python3 plot_wp5_convergence.py
"""
import matplotlib
matplotlib.use("Agg")

import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

from ES.evopy import EvoPy, Strategy

OUT_PATH = "plots_wp1/wp5_convergence.png"

# Packomania optimal min pairwise distance (index = n - 2)
_TARGETS = [
    1.4142135623730951, 1.0352761804100830, 1.0000000000000000, 0.7071067811865475,
    0.6009252125773315, 0.5358983848622454, 0.5176380902050415, 0.5000000000000000,
    0.4212795439839034, 0.3982073102368442, 0.3887301263230200, 0.3660960076964251,
    0.3489152603740189, 0.3410813774021089, 0.3333333333333333, 0.3061539853003329,
    0.3004626062886658, 0.2895419919949817, 0.2866116523516816,
]


def get_target(n):
    return _TARGETS[n - 2]


def fitness(individual):
    pts = np.asarray(individual).reshape(-1, 2)
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return float(d.min())


BASELINE = dict(
    strategy=Strategy.SINGLE_VARIANCE,
    selection_scheme="comma",
    init="lhs",
    population_size=30,
    num_children=7,
)

MAX_EVALS = 100_000


def run_seed(n_circles, seed):
    """Run one seed with interleaved polish; return trace and polish_log."""
    target = get_target(n_circles)
    trace = []

    def reporter(r):
        trace.append((r.evaluations, r.best_fitness))

    es = EvoPy(
        fitness, n_circles * 2,
        reporter=reporter, maximize=True, bounds=(0, 1),
        generations=100_000,
        max_evaluations=MAX_EVALS,
        random_seed=seed,
        local_search="interleaved",
        **BASELINE,
    )
    es.run()

    evals = np.array([e for e, _ in trace])
    best  = np.array([b for _, b in trace])
    gap   = (target - best) / target
    gap   = np.clip(gap, 1e-6, None)   # avoid log(0)
    return evals, gap, es.polish_log, target


def add_polish_ticks(ax, polish_log, gap_at_tick=None):
    """Draw vertical lines at each L-BFGS-B call; green=improved, grey=no gain."""
    for evals_at, _, fit_before, fit_after, improved in polish_log:
        color = "#2ca02c" if improved else "#9e9e9e"
        ax.axvline(evals_at, color=color, linewidth=0.8, alpha=0.7, zorder=2)


def main():
    os.makedirs("plots_wp1", exist_ok=True)

    # Choose seeds that tell a clear story
    cases = [
        (10, 0,  "n=10, seed 0 (representative)"),
        (15, 20, "n=15, seed 20 (best outcome)"),
        (15, 2,  "n=15, seed 2  (worst outcome)"),
    ]

    print("Running convergence experiments...")
    results = []
    for n, seed, label in cases:
        print(f"  {label}...")
        evals, gap, plog, target = run_seed(n, seed)
        results.append((evals, gap, plog, label))
        print(f"    final gap={gap[-1]:.4f}, {len(plog)} polish calls")

    fig, axes = plt.subplots(1, 3, figsize=(14, 4), sharey=False)

    for ax, (evals, gap, plog, label) in zip(axes, results):
        ax.semilogy(evals, gap, color="steelblue", linewidth=1.2, zorder=3)
        add_polish_ticks(ax, plog)
        ax.set_title(label, fontsize=9)
        ax.set_xlabel("Evaluations", fontsize=9)
        ax.set_ylabel("Gap to optimum (log)" if ax is axes[0] else "")
        ax.set_xlim(0, MAX_EVALS)
        ax.yaxis.set_major_formatter(ticker.LogFormatterSciNotation())
        ax.grid(True, which="both", alpha=0.25)

    # Legend
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="steelblue", linewidth=1.5, label="Best fitness (gap)"),
        Line2D([0], [0], color="#2ca02c",  linewidth=1.0, label="L-BFGS-B call (improved)"),
        Line2D([0], [0], color="#9e9e9e",  linewidth=1.0, label="L-BFGS-B call (no gain)"),
    ]
    fig.legend(handles=legend_elements, loc="upper right", fontsize=8, framealpha=0.9)
    fig.suptitle("ES + interleaved L-BFGS-B polish: convergence curves", fontsize=12)

    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"Saved {OUT_PATH}")


if __name__ == "__main__":
    main()
