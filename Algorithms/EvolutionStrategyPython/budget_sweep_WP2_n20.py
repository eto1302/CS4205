"""
WP2 budget sweep at n=20: does comma's higher ceiling overtake plus given more
evaluations, or is plus genuinely more reliable on this hard problem?

At 100k evals, (mu+lambda) "plus" beat (mu,lambda) "comma" at n=20 decisively
(Mann-Whitney p~0, A12=0.08) even though comma's single best seed was higher.
Two explanations: (A) comma needs more budget to cash in its higher ceiling, or
(B) plus is simply more reliable here. This sweep distinguishes them.

Because max_evaluations is ONLY a stop criterion in evopy.run() (local_search is
off, so _lbfgsb_polish never runs), a single 500k run has an identical trajectory
to shorter runs with the same seed. So we run once to 500k per seed and slice the
trace at each budget -- exact and 3x cheaper than rerunning per budget.

"As-reported" fitness at budget B = what the algorithm would return if stopped at
B (the current population best, non-monotone for comma). "Best-so-far" = the
running max up to B (comma's ceiling). We report both.

Run from this directory:  python budget_sweep_n20.py
Output: results/WP2/plots/budget_sweep_n20_comma_vs_plus.png
        results/WP2/budget_sweep_n20_summary.csv
"""

import csv
import os
import sys
from statistics import mean, pstdev

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from scipy.stats import mannwhitneyu

from benchmark_Cala import Benchmark, KNOWN_OPTIMA
from ES.evopy.strategy import Strategy

# ── Config ───────────────────────────────────────────────────────────────────
N = 20
N_RUNS = 15
MAX_EVALS = 500_000
BUDGETS = [100_000, 200_000, 300_000, 500_000]
OPT = KNOWN_OPTIMA[N - 2]

SCHEME_STYLE = {
    "comma": dict(color="#1f77b4", label="(μ,λ) comma"),
    "plus":  dict(color="#d62728", label="(μ+λ) plus"),
}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLOTS_DIR = os.path.join(REPO_ROOT, "results", "WP2", "plots")
PLOT_PATH = os.path.join(PLOTS_DIR, "budget_sweep_n20_comma_vs_plus.png")
CSV_PATH = os.path.join(REPO_ROOT, "results", "WP2", "budget_sweep_n20_summary.csv")


def as_reported_at(trace, budget):
    """Fitness the algorithm would return if stopped at `budget` evals."""
    vals = [f for ev, f in trace if ev <= budget]
    return vals[-1] if vals else None


def best_so_far_at(trace, budget):
    """Running max fitness up to `budget` evals (comma's ceiling)."""
    vals = [f for ev, f in trace if ev <= budget]
    return max(vals) if vals else None


def a12(x, y):
    """Vargha-Delaney A12 = P(x>y)+0.5P(=); >0.5 favors x (maximizing)."""
    gt = eq = 0
    for xi in x:
        for yi in y:
            if xi > yi:
                gt += 1
            elif xi == yi:
                eq += 1
    return (gt + 0.5 * eq) / (len(x) * len(y))


def mean_curve(runs, grid):
    """Mean as-reported fitness across seeds on a common eval grid."""
    out = []
    for ev in grid:
        vals = [as_reported_at(r.trace, ev) for r in runs]
        vals = [v for v in vals if v is not None]
        out.append(mean(vals) if vals else None)
    return out


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    bench = Benchmark(
        n_circles_list=[N],
        strategies=[Strategy.SINGLE_VARIANCE],
        selection_schemes=list(SCHEME_STYLE.keys()),
        archive_modes=["off"],
        population_sizes=[30],
        num_children_list=[7],
        n_runs=N_RUNS,
        max_evaluations=MAX_EVALS,
        verbose=True,
    )
    bench.run_all()

    runs = {s: [r for r in bench.results if r.selection_scheme == s] for s in SCHEME_STYLE}

    # ── Per-budget stats + significance ──────────────────────────────────────
    print(f"\n── Budget sweep, n={N}, {N_RUNS} seeds (as-reported / stop-here) ──")
    header = (f"{'budget':>8} {'comma gap%':>11} {'plus gap%':>10} "
              f"{'p(MWU)':>9} {'A12':>6} {'comma ceil gap%':>16}")
    print(header)
    rows = []
    for B in BUDGETS:
        c_rep = [as_reported_at(r.trace, B) for r in runs["comma"]]
        p_rep = [as_reported_at(r.trace, B) for r in runs["plus"]]
        c_rep = [v for v in c_rep if v is not None]
        p_rep = [v for v in p_rep if v is not None]
        c_ceil = [best_so_far_at(r.trace, B) for r in runs["comma"]]
        c_ceil = [v for v in c_ceil if v is not None]

        c_gap = mean((OPT - v) / OPT * 100 for v in c_rep)
        p_gap = mean((OPT - v) / OPT * 100 for v in p_rep)
        c_ceil_gap = mean((OPT - v) / OPT * 100 for v in c_ceil)
        u, pv = mannwhitneyu(c_rep, p_rep, alternative="two-sided")
        a = a12(c_rep, p_rep)
        winner = "comma" if a > 0.5 else "plus"
        print(f"{B:>8,} {c_gap:>11.2f} {p_gap:>10.2f} {pv:>9.4f} {a:>6.2f} "
              f"{c_ceil_gap:>16.2f}   -> {winner}{' *' if pv < 0.05 else ''}")
        rows.append(dict(budget=B, comma_gap_pct=round(c_gap, 3),
                         plus_gap_pct=round(p_gap, 3), mwu_p=round(pv, 5),
                         a12=round(a, 3), comma_ceiling_gap_pct=round(c_ceil_gap, 3),
                         winner=winner, significant=pv < 0.05))

    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nSummary saved -> {CSV_PATH}")

    # ── Plot: convergence to 500k, comma vs plus, budget markers ─────────────
    grid = sorted({ev for s in SCHEME_STYLE for r in runs[s] for ev, _ in r.trace})
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle(f"Budget sweep at n={N} — does comma overtake plus with more evaluations?",
                 fontsize=13)
    for s, style in SCHEME_STYLE.items():
        for r in runs[s]:
            if r.trace:
                ev, ft = zip(*r.trace)
                ax.plot(ev, ft, color=style["color"], alpha=0.10, linewidth=0.6)
        mc = mean_curve(runs[s], grid)
        gx = [g for g, m in zip(grid, mc) if m is not None]
        gy = [m for m in mc if m is not None]
        ax.plot(gx, gy, color=style["color"], linewidth=2.4, label=style["label"] + " (mean)")
    ax.axhline(OPT, color="black", linewidth=1, linestyle="--", label=f"optimum ({OPT:.4f})")
    for B in BUDGETS:
        ax.axvline(B, color="grey", linewidth=0.8, linestyle=":", alpha=0.7)
    ax.set_xlabel("Evaluations")
    ax.set_ylabel("Best fitness (as-reported / stop-here)")
    ax.legend(fontsize=9, loc="lower right")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    fig.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    fig.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    print(f"Plot saved -> {PLOT_PATH}")


if __name__ == "__main__":
    main()
