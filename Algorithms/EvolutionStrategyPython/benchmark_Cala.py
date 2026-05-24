"""
Benchmark for the EvoPy Evolution Strategy - focused on MULTIPLE_VARIANCE.

Measures convergence speed, final solution, and succes rate across
multiple runs and problem sizes. Results are printed as a summary table
and optionally saved as CSV for further analysis.

Usage: 
    python benchmark_Cala.py



"""

import argparse
import csv
import math
import sys
import time
from dataclasses import dataclass, field, asdict
from statistics import mean, stdev
from typing import Optional
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from sklearn.metrics.pairwise import euclidean_distances

# - Import package layout --
from ES.evopy import EvoPy, ProgressReport, Strategy
from ES.evopy.strategy import Strategy

#Fitness functions two: choose depending on the size of the problem

def circles_in_a_square(individual):
    """Pure-Python CiaS - faster for small n (<12)"""
    n = len(individual)
    distances = []
    for i in range(0, n-1, 2):
        for j in range(i+2, n, 2):
            distances.append(
                math.sqrt(
                    (individual[i] - individual[j]) ** 2
                    + (individual[i + 1] - individual[j + 1]) ** 2
                )
            )
    return min(distances)

def circles_in_a_square_scipy(individual):
    """NumPy/SciPy CiaS - faster for large n (>=12)"""
    points = np.reshape(individual, (-1, 2))
    dist = euclidean_distances(points)
    np.fill_diagonal(dist, 1e10)
    return np.min(dist)

# Known optima: From main.py - get_target - values_to_reach, for 2...20 circles (index 0 = 2 circles).
# Maximum achievable minimum distance between the centres of the circles inside a unit square
KNOWN_OPTIMA = [
            1.414213562373095048801688724220,  # 2
            1.035276180410083049395595350499,  # 3
            1.000000000000000000000000000000,  # 4
            0.707106781186547524400844362106,  # 5
            0.600925212577331548853203544579,  # 6
            0.535898384862245412945107316990,  # 7
            0.517638090205041524697797675248,  # 8
            0.500000000000000000000000000000,  # 9
            0.421279543983903432768821760651,  # 10
            0.398207310236844165221512929748,  # 11
            0.388730126323020031391610191835,  # 12
            0.366096007696425085295389370603,  # 13
            0.348915260374018877918854409001,  # 14
            0.341081377402108877637121191351,  # 15
            0.333333333333333333333333333333,  # 16
            0.306153985300332915214516914060,  # 17
            0.300462606288665774426601772290,  # 18
            0.289541991994981660261698764510,  # 19
            0.286611652351681559449894454738   # 20
        ]

def get_fitness_fn(n_circles: int):
    return circles_in_a_square if n_circles < 12 else circles_in_a_square_scipy


# ---- Data classes ------------------------

#Holds the outcome of one single run: fitness achieved, evaluations used, wall time, and convergence over time (snapshots from the reporter callback)
@dataclass
class RunResult:
    """Outcome of a single ES run"""
    n_circles: int
    run_id: int
    strategy: str
    population_size: int
    num_children: int
    best_fitness: float
    optimum: float
    gap: float          # optimum - best_fitness 
    gap_pct: float      # gap as % of optimum
    success: bool       # gap <= tolerance
    evaluations_used: int
    wall_time_s: float
    #Convergence trace: list of (evaluation, best_fitness) tuples
    trace: list = field(default_factory=list, repr = False)


#Holds aggregated stats across all runs of one configuration
@dataclass
class SummaryStats:
    """Aggregated stats over multiple runs of one configuration"""

    n_circles: int
    strategy: str
    population_size: int
    num_children: int
    n_runs: int
    success_rate: float
    mean_gap_pct: float
    std_gap_pct: float
    mean_evals: float
    std_evals: float
    mean_time_s: float
    median_best_fitness: float
    optimum: float


# ------ Benchmark Runner ------------------

class Benchmark:
    """Runs multiple ES experiments and collects results."""

    def __init__(
        self,
        n_circles_list: list[int],
        strategies: list[Strategy],
        population_sizes: list[int],
        num_children_list: list[int],
        n_runs: int = 10,
        max_evaluations: int = 100_000,
        tolerance: float = 1e-4,
        random_seed_base: int = 42,
        verbose: bool = True,
        ):

        self.n_circles_list = n_circles_list
        self.strategies = strategies
        self.population_sizes = population_sizes
        self.num_children_list = num_children_list
        self.n_runs = n_runs
        self.max_evaluations = max_evaluations
        self.tolerance = tolerance
        self.random_seed_base = random_seed_base
        self.verbose = verbose
        self.results: list[RunResult] = []

    def _run_single(
            self,
            n_circles: int,
            strategy: Strategy,
            population_size: int,
            num_children: int,
            run_id: int,
    ) -> RunResult:
        
        """Execute one ES run and return its result."""

        optimum = KNOWN_OPTIMA[n_circles - 2] #because 2 circles in index 0
        fitness_fn = get_fitness_fn(n_circles)
        trace: list[tuple[int, float]] = []

        def reporter(report: ProgressReport):
            trace.append((report.evaluations, report.best_fitness))

        #Each run gets a specific seed, so runs are reproducible and independent from each other
        seed = self.random_seed_base + run_id * 1000 + n_circles * 100

        t0 = time.perf_counter()
        evopy = EvoPy(
            fitness_fn,
            n_circles * 2,
            maximize=True,
            generations = 10_000,
            population_size = population_size,
            num_children=num_children,
            strategy=strategy,
            bounds = (0,1),
            target_fitness_value = optimum,
            target_tolerance = self.tolerance,
            max_evaluations = self.max_evaluations,
            random_seed=seed,
            reporter=reporter,
        )

        best_genotype = evopy.run()
        wall_time = time.perf_counter() - t0

        best_fitness = trace[-1][1] if trace else 0.0  # last reported fitness
        gap = optimum - best_fitness
        gap_pct = (gap / optimum) * 100

        return RunResult(
            n_circles=n_circles,
            run_id=run_id,
            strategy=strategy.name,
            population_size=population_size,
            num_children=num_children,
            best_fitness=best_fitness,
            optimum=optimum,
            gap=gap,
            gap_pct=max(gap_pct, 0.0),
            success=gap <= self.tolerance,
            evaluations_used=evopy.evaluations,
            wall_time_s=wall_time,
            trace=trace,
            )

    def run_all(self):
        """Run the full benchmark grid: every 
        combination of:
        n_circles x strategy x population_size x num_children x run_id
        calls _run_single for each of them
        Every combination gets the same number of runs
        """
        configs = [
            (n, s, p, c)
            for n in self.n_circles_list
            for s in self.strategies
            for p in self.population_sizes
            for c in self.num_children_list
        ]

        total = len(configs) * self.n_runs 
        done = 0 # runs completed so far

        for n_circles, strategy, population_size, num_children in configs:
            for run_id in range(self.n_runs):
                if self.verbose: # to indicate in the terminal which run is running
                    done += 1
                    tag = (
                        f"[{done}/{total}] "
                        f"n={n_circles} strat={strategy.name} "
                        f"pop={population_size} children={num_children} "
                        f"run={run_id}"
                    )
                    print(tag, end="\r", flush=True)
 
                result = self._run_single(
                    n_circles, strategy, population_size, num_children, run_id
                )
                self.results.append(result) 

        if self.verbose:
            print() #newline after \r progress


    def summarize(self) -> list[SummaryStats]:
        """Aggregate results into per-configuration summary stats."""
        from itertools import groupby
 
        key = lambda r: (r.n_circles, r.strategy, r.population_size, r.num_children)
        sorted_results = sorted(self.results, key=key)
 
        summaries = []
        for (n_circles, strategy, pop, children), group in groupby(sorted_results, key=key):
            runs = list(group)
            gaps = [r.gap_pct for r in runs]
            evals = [r.evaluations_used for r in runs]
            times = [r.wall_time_s for r in runs]
            fitnesses = sorted([r.best_fitness for r in runs])
 
            summaries.append(SummaryStats(
                n_circles=n_circles,
                strategy=strategy,
                population_size=pop,
                num_children=children,
                n_runs=len(runs),
                success_rate=sum(r.success for r in runs) / len(runs),
                mean_gap_pct=mean(gaps),
                std_gap_pct=stdev(gaps) if len(gaps) > 1 else 0.0,
                mean_evals=mean(evals),
                std_evals=stdev(evals) if len(evals) > 1 else 0.0,
                mean_time_s=mean(times),
                median_best_fitness=fitnesses[len(fitnesses) // 2],
                optimum=KNOWN_OPTIMA[n_circles - 2],
            ))
 
        return summaries

    def print_table(self):
        """Print a human-readable summary table to stdout."""
        summaries = self.summarize()
 
        # Header
        print("\n" + "═" * 110)
        print(
            f"{'n':>3} {'strategy':<18} {'pop':>4} {'chd':>4} "
            f"{'success%':>9} {'mean gap%':>10} {'±gap%':>7} "
            f"{'mean evals':>11} {'±evals':>9} {'mean t(s)':>9} "
            f"{'median fit':>11} {'optimum':>11}"
        )
        print("─" * 110)
 
        for s in summaries:
            print(
                f"{s.n_circles:>3} {s.strategy:<18} {s.population_size:>4} {s.num_children:>4} "
                f"{s.success_rate * 100:>8.1f}% {s.mean_gap_pct:>10.4f} {s.std_gap_pct:>7.4f} "
                f"{s.mean_evals:>11.0f} {s.std_evals:>9.0f} {s.mean_time_s:>9.3f} "
                f"{s.median_best_fitness:>11.6f} {s.optimum:>11.6f}"
            )
 
        print("═" * 110)
 
    def convergence_table(self):
        """
        Show evaluation budget at which each run first hit 1%, 0.1%, 0.01%
        of the known optimum (for MULTIPLE_VARIANCE runs only).
        """
        mv_runs = [r for r in self.results if r.strategy == "MULTIPLE_VARIANCE"]
        if not mv_runs:
            return
 
        thresholds = [0.01, 0.001, 0.0001]  # relative gap thresholds
 
        print("\n── Convergence budget (MULTIPLE_VARIANCE) ──────────────────────────────────")
        print(f"{'n':>3}  {'run':>3}  {'evals@1%':>10}  {'evals@0.1%':>11}  {'evals@0.01%':>12}")
        print("─" * 55)
 
        for r in mv_runs:
            row = [r.n_circles, r.run_id]
            for thr in thresholds:
                # Find first evaluation where gap <= thr * optimum
                hit = next(
                    (ev for ev, fit in r.trace if (r.optimum - fit) / r.optimum <= thr),
                    None,
                )
                row.append(hit if hit is not None else "—")
            print(f"{row[0]:>3}  {row[1]:>3}  {str(row[2]):>10}  {str(row[3]):>11}  {str(row[4]):>12}")
 
    def save_csv(self, path: str):
        """Save individual run results to CSV."""
        if not self.results:
            return
        rows = [asdict(r) for r in self.results]
        # Remove trace (too large for CSV) — save it as length only
        for row in rows:
            row["trace_len"] = len(row.pop("trace"))
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResults saved → {path}")

    def plot(self, save_path: str = None):
        """
        Produce three figures: 
            1. Convergence curves: best fitness vs evaluations, one subplot per n_circles
            2. Success rate bars: per strategy per n_circles
            3. Box plots of gap%: distribution of final gap% per strategy per n_circles
        
        """
        if not self.results:
            print("No results to plot.")
            return
        
        n_circles_list = sorted(set(r.n_circles for r in self.results))
        strategies = sorted(set(r.strategy  for r in self.results))
        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        strat_color    = {s: colors[i % len(colors)] for i, s in enumerate(strategies)}

        # ── 1. Convergence curves ─────────────────────────────────────────────
        n_cols  = min(2, len(n_circles_list))
        n_rows  = math.ceil(len(n_circles_list) / n_cols)
        fig1, axes1 = plt.subplots(n_rows, n_cols,
                                   figsize=(7 * n_cols, 4 * n_rows),
                                   squeeze=False)
        fig1.suptitle("Convergence curves — best fitness vs evaluations", fontsize=13)
 
        for idx, n in enumerate(n_circles_list):
            ax = axes1[idx // n_cols][idx % n_cols]
            optimum = KNOWN_OPTIMA[n - 2]
 
            for strat in strategies:
                runs = [r for r in self.results if r.n_circles == n and r.strategy == strat]
                color = strat_color[strat]
 
                # Plot every individual run as a faint line
                for r in runs:
                    if not r.trace:
                        continue
                    evals, fits = zip(*r.trace)
                    ax.plot(evals, fits, color=color, alpha=0.15, linewidth=0.8)
 
                # Plot the mean trace as a solid line
                # Interpolate all traces onto a common eval grid first
                all_evals = sorted(set(ev for r in runs for ev, _ in r.trace))
                if all_evals:
                    mean_fits = []
                    for ev in all_evals:
                        vals = []
                        for r in runs:
                            # Last fitness at or before this eval count
                            past = [f for e, f in r.trace if e <= ev]
                            if past:
                                vals.append(past[-1])
                        if vals:
                            mean_fits.append(mean(vals))
                        else:
                            mean_fits.append(None)
 
                    clean_evals = [e for e, f in zip(all_evals, mean_fits) if f is not None]
                    clean_fits  = [f for f in mean_fits if f is not None]
                    ax.plot(clean_evals, clean_fits, color=color,
                            linewidth=2, label=strat)
 
            # Known optimum reference line
            ax.axhline(optimum, color="black", linewidth=1,
                       linestyle="--", label=f"optimum ({optimum:.4f})")
            ax.set_title(f"{n} circles")
            ax.set_xlabel("Evaluations")
            ax.set_ylabel("Best fitness")
            ax.legend(fontsize=7)
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(
                lambda x, _: f"{int(x):,}"))
 
        # Hide unused subplots
        for idx in range(len(n_circles_list), n_rows * n_cols):
            axes1[idx // n_cols][idx % n_cols].set_visible(False)
 
        fig1.tight_layout()
 
        # ── 2. Success rate bar chart ─────────────────────────────────────────
        fig2, ax2 = plt.subplots(figsize=(max(7, len(n_circles_list) * 2), 5))
        fig2.suptitle("Success rate per strategy and problem size", fontsize=13)
 
        summaries   = self.summarize()
        x           = np.arange(len(n_circles_list))
        bar_width   = 0.8 / len(strategies)
 
        for i, strat in enumerate(strategies):
            rates = []
            for n in n_circles_list:
                matching = [s for s in summaries
                            if s.n_circles == n and s.strategy == strat]
                if matching:
                    # Average success rate across all pop/children configs
                    rates.append(mean(s.success_rate for s in matching) * 100)
                else:
                    rates.append(0.0)
            offset = (i - len(strategies) / 2 + 0.5) * bar_width
            bars = ax2.bar(x + offset, rates, bar_width,
                           label=strat, color=strat_color[strat], alpha=0.85)
            # Value labels on bars
            for bar, rate in zip(bars, rates):
                if rate > 0:
                    ax2.text(bar.get_x() + bar.get_width() / 2,
                             bar.get_height() + 1,
                             f"{rate:.0f}%", ha="center", va="bottom", fontsize=8)
 
        ax2.set_xticks(x)
        ax2.set_xticklabels([f"{n} circles" for n in n_circles_list])
        ax2.set_ylabel("Success rate (%)")
        ax2.set_ylim(0, 115)
        ax2.legend()
        ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0f}%"))
        fig2.tight_layout()
 
        # ── 3. Box plots of final gap% ────────────────────────────────────────
        fig3, axes3 = plt.subplots(1, len(n_circles_list),
                                   figsize=(max(7, len(n_circles_list) * 3), 5),
                                   squeeze=False)
        fig3.suptitle("Distribution of final gap % from optimum", fontsize=13)
 
        for idx, n in enumerate(n_circles_list):
            ax = axes3[0][idx]
            data   = []
            labels = []
            for strat in strategies:
                gaps = [r.gap_pct for r in self.results
                        if r.n_circles == n and r.strategy == strat]
                data.append(gaps)
                labels.append(strat.replace("_", "\n"))
 
            bp = ax.boxplot(data, patch_artist=True, widths=0.5)
            for patch, strat in zip(bp["boxes"], strategies):
                patch.set_facecolor(strat_color[strat])
                patch.set_alpha(0.75)
 
            ax.set_title(f"{n} circles")
            ax.set_xticklabels(labels, fontsize=8)
            ax.set_ylabel("Gap from optimum (%)" if idx == 0 else "")
            ax.axhline(0, color="black", linewidth=0.8, linestyle="--")
 
        fig3.tight_layout()
 
        if save_path:
            base, ext = save_path.rsplit(".", 1) if "." in save_path else (save_path, "png")
            fig1.savefig(f"{base}_convergence.{ext}", dpi=150, bbox_inches="tight")
            fig2.savefig(f"{base}_success_rate.{ext}", dpi=150, bbox_inches="tight")
            fig3.savefig(f"{base}_gap_boxplot.{ext}", dpi=150, bbox_inches="tight")
            print(f"Plots saved → {base}_convergence.{ext}, "
                  f"{base}_success_rate.{ext}, {base}_gap_boxplot.{ext}")
        else:
            plt.show()


 
 
# ─── Entry point ─────────────────────────────────────────────────────────────
  
def main():
    # ── Configure your run here ──────────────────────
    QUICK        = True
    SAVE_CSV     = True
    CSV_PATH     = "benchmark_results_cala.csv"
    N_RUNS       = 10
    MAX_EVALS    = 100_000
    # ─────────────────────────────────────────────────

    if QUICK:
        bench = Benchmark(
            n_circles_list=[5, 8],
            strategies=[Strategy.SINGLE_VARIANCE, Strategy.MULTIPLE_VARIANCE, Strategy.FULL_VARIANCE],
            population_sizes=[30],
            num_children_list=[7],
            n_runs=3,
            max_evaluations=50_000,
            verbose=True,
        )
    else:
        bench = Benchmark(
            n_circles_list=[5, 7, 10, 15],
            strategies=[Strategy.SINGLE_VARIANCE, Strategy.MULTIPLE_VARIANCE],
            population_sizes=[15, 30, 50],
            num_children_list=[5, 10],
            n_runs=N_RUNS,
            max_evaluations=MAX_EVALS,
            verbose=True,
        )

    bench.run_all()
    bench.print_table()
    bench.convergence_table()

    if SAVE_CSV:
        bench.save_csv(CSV_PATH)
    
    # ── Plots ─────────────────────────────────────────────────────────────────
    SAVE_PLOTS = True        # set False to show interactively instead of saving
    PLOT_PATH  = "benchmark" # produces benchmark_convergence.png etc.
 
    if SAVE_PLOTS:
        bench.plot(save_path=f"{PLOT_PATH}.png")
    else:
        bench.plot()


 
if __name__ == "__main__":
    main()  





