"""
WP2 population-size sweep at n=20: is comma (mu,lambda) under-performing because
the population is too small?

Background: at n=20, comma's best-so-far ("ceiling") reaches ~48% gap but it
REPORTS ~61% because (mu,lambda) discards its best every generation, so plus
(mu+lambda) wins. Two reasons a larger mu might rescue comma:
  (1) comma's edge is sigma self-adaptation, which needs enough samples — mu=30
      is small for a 40-D problem (n=20 -> 40 coords);
  (2) a broader population carries more near-best solutions, dampening comma's
      per-generation loss of its best (shrinking the ceiling-vs-reported gap).
Since comma's ceiling already BEATS plus's reported value, a good mu could flip
the n=20 verdict. Trade-off: at a fixed eval budget, bigger mu => bigger lambda
=> fewer generations, so expect a sweet spot (U-shaped curve).

We hold num_children=7 fixed so lambda/mu stays at the BSw95 comma-optimal ratio
(and lambda > mu, required for comma); only the absolute mu varies.

Run from this directory so you can watch progress live:
    python pop_size_sweep_n20.py

Outputs:
    results/WP2/plots/pop_size_sweep_n20.png
    results/WP2/pop_size_sweep_n20_per_run.csv
"""

import csv
import os
import sys
import time
from statistics import mean, pstdev

import matplotlib

matplotlib.use("Agg")  # save figures headless; never blocks the terminal
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu

from benchmark_Cala import Benchmark, KNOWN_OPTIMA
from ES.evopy.strategy import Strategy

# ── Config (edit here) ───────────────────────────────────────────────────────
N = 20
POPS = [15, 30, 60, 120]      # mu values to sweep (num_children fixed -> lambda = 7*mu)
NUM_CHILDREN = 7
SEEDS = 8
MAX_EVALS = 300_000
SCHEMES = ["comma", "plus"]
# ─────────────────────────────────────────────────────────────────────────────

OPT = KNOWN_OPTIMA[N - 2]
COLOR = {"comma": "#1f77b4", "plus": "#d62728"}

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLOTS_DIR = os.path.join(REPO_ROOT, "results", "WP2", "plots")
PLOT_PATH = os.path.join(PLOTS_DIR, "pop_size_sweep_n20.png")
CSV_PATH = os.path.join(REPO_ROOT, "results", "WP2", "pop_size_sweep_n20_per_run.csv")


def gap_pct(fit):
    return (OPT - fit) / OPT * 100.0


def ceiling_fit(trace):
    """Best-so-far fitness over the whole run (comma's ceiling)."""
    return max(f for _, f in trace) if trace else 0.0


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


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    total_runs = len(POPS) * len(SCHEMES) * SEEDS
    print(f"\nPopulation-size sweep @ n={N}: mu in {POPS}, num_children={NUM_CHILDREN} "
          f"(lambda=7*mu), {SEEDS} seeds, {MAX_EVALS:,} evals")
    print(f"{len(SCHEMES)} schemes x {len(POPS)} pops x {SEEDS} seeds = {total_runs} runs. "
          f"Watch the [done/total] counter below.\n")

    per_run = []          # one dict per run, written to CSV
    # summary[(pop, scheme)] = dict(reported=[...fit], ceiling=[...fit])
    summary = {}
    t_start = time.time()

    for pop in POPS:
        lam = pop * NUM_CHILDREN
        print(f"=== population_size mu={pop}  (lambda={lam}, lambda/mu={NUM_CHILDREN}) "
              f"— {len(SCHEMES)*SEEDS} runs ===", flush=True)

        # One Benchmark per pop so a result row prints right after each pop finishes.
        bench = Benchmark(
            n_circles_list=[N],
            strategies=[Strategy.SINGLE_VARIANCE],
            selection_schemes=SCHEMES,
            archive_modes=["off"],
            population_sizes=[pop],
            num_children_list=[NUM_CHILDREN],
            n_runs=SEEDS,
            max_evaluations=MAX_EVALS,
            verbose=True,          # live [done/total] progress to the terminal
        )
        bench.run_all()

        for sch in SCHEMES:
            runs = [r for r in bench.results if r.selection_scheme == sch]
            rep = [r.best_fitness for r in runs]                  # as-reported (stop-here)
            ceil = [ceiling_fit(r.trace) for r in runs]           # best-so-far
            summary[(pop, sch)] = dict(reported=rep, ceiling=ceil)
            for r, cf in zip(runs, ceil):
                per_run.append(dict(
                    n=N, population_size=pop, num_children=NUM_CHILDREN, lam=lam,
                    selection_scheme=sch, seed=r.run_id,
                    reported_fit=r.best_fitness, ceiling_fit=cf,
                    reported_gap_pct=round(gap_pct(r.best_fitness), 3),
                    ceiling_gap_pct=round(gap_pct(cf), 3),
                ))

        # immediate per-pop readout
        cr = summary[(pop, "comma")]["reported"]
        cc = summary[(pop, "comma")]["ceiling"]
        pr = summary[(pop, "plus")]["reported"]
        print(f"    comma: reported gap {mean(gap_pct(f) for f in cr):5.2f}% | "
              f"ceiling gap {mean(gap_pct(f) for f in cc):5.2f}%   "
              f"plus: reported gap {mean(gap_pct(f) for f in pr):5.2f}%", flush=True)

    # ── Final table: comma vs plus (as-reported) at each pop + significance ───
    print("\n" + "─" * 78)
    print(f"{'mu':>5} {'comma rep gap%':>15} {'comma ceil gap%':>16} "
          f"{'plus rep gap%':>14} {'p(MWU)':>9} {'A12':>6}  winner")
    print("─" * 78)
    for pop in POPS:
        cr = summary[(pop, "comma")]["reported"]
        cc = summary[(pop, "comma")]["ceiling"]
        pr = summary[(pop, "plus")]["reported"]
        u, pv = mannwhitneyu(cr, pr, alternative="two-sided")
        a = a12(cr, pr)
        win = "comma" if a > 0.5 else "plus"
        star = " *" if pv < 0.05 else ""
        print(f"{pop:>5} {mean(gap_pct(f) for f in cr):>15.2f} "
              f"{mean(gap_pct(f) for f in cc):>16.2f} "
              f"{mean(gap_pct(f) for f in pr):>14.2f} {pv:>9.4f} {a:>6.2f}  {win}{star}")
    print("─" * 78)
    print("(rep = as-reported/stop-here; ceil = best-so-far; * = significant at 0.05)")

    # ── Save per-run CSV ─────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    with open(CSV_PATH, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(per_run[0].keys()))
        w.writeheader()
        w.writerows(per_run)
    print(f"\nPer-run data saved -> {CSV_PATH}")

    # ── Plot ─────────────────────────────────────────────────────────────────
    xs = list(range(len(POPS)))

    def series(scheme, kind):
        ys = [mean(gap_pct(f) for f in summary[(p, scheme)][kind]) for p in POPS]
        es = [pstdev([gap_pct(f) for f in summary[(p, scheme)][kind]]) for p in POPS]
        return ys, es

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(14, 5.5))
    fig.suptitle(f"Population-size sweep at n={N} — is comma pop-size-limited? "
                 f"({SEEDS} seeds, {MAX_EVALS:,} evals)", fontsize=13)

    # Panel A: gap% vs mu — comma reported, comma ceiling, plus reported
    ya, ea = series("comma", "reported")
    axA.errorbar(xs, ya, yerr=ea, marker="o", color=COLOR["comma"], capsize=4,
                 label="comma  as-reported")
    yc, ec = series("comma", "ceiling")
    axA.errorbar(xs, yc, yerr=ec, marker="s", linestyle="--", color=COLOR["comma"],
                 alpha=0.7, capsize=4, label="comma  ceiling (best-so-far)")
    yp, ep = series("plus", "reported")
    axA.errorbar(xs, yp, yerr=ep, marker="o", color=COLOR["plus"], capsize=4,
                 label="plus  as-reported")
    axA.set_xticks(xs)
    axA.set_xticklabels([f"mu={p}\nlam={p*NUM_CHILDREN}" for p in POPS])
    axA.set_ylabel("Gap from optimum (%)  — lower is better")
    axA.set_xlabel("Population size")
    axA.set_title("Does a larger population rescue comma (and overtake plus)?")
    axA.legend(fontsize=9)
    axA.grid(alpha=0.3)

    # Panel B: comma retention gap (reported gap − ceiling gap) vs mu
    retention = [mean(gap_pct(f) for f in summary[(p, "comma")]["reported"])
                 - mean(gap_pct(f) for f in summary[(p, "comma")]["ceiling"]) for p in POPS]
    axB.bar(xs, retention, color=COLOR["comma"], alpha=0.8)
    for x, v in zip(xs, retention):
        axB.text(x, v, f"{v:.1f}", ha="center", va="bottom", fontsize=9)
    axB.set_xticks(xs)
    axB.set_xticklabels([f"mu={p}" for p in POPS])
    axB.set_ylabel("Comma retention gap (reported − ceiling), pct points")
    axB.set_xlabel("Population size")
    axB.set_title("How much of its own ceiling does comma throw away?")
    axB.grid(alpha=0.3, axis="y")

    fig.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    fig.savefig(PLOT_PATH, dpi=150, bbox_inches="tight")
    print(f"Plot saved -> {PLOT_PATH}")
    print(f"\nTotal wall time: {(time.time() - t_start)/60:.1f} min")


if __name__ == "__main__":
    main()
