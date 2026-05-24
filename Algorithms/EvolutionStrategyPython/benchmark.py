import math
import os
import multiprocessing
from itertools import product

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist

from ES.evopy import EvoPy, Strategy

np.seterr(all='raise')  # Turn warnings into exceptions with a traceback

# ── Configuration ──────────────────────────────────────────────────────────────
CIRCLE_SIZES = [7, 10, 15, 20]
STRATEGIES   = [Strategy.SINGLE_VARIANCE, Strategy.MULTIPLE_VARIANCE, Strategy.FULL_VARIANCE]
N_RUNS       = 25
MAX_EVALS    = 100_000
POPULATION   = 30
GENERATIONS  = 1_000
TARGET_TOLS  = [1e-2, 1e-3, 1e-5]   # finest last; compute_summary loops over these
CONFIG_LABEL = "baseline"
INIT_MODES   = ["random", "cluster_corner"]   # cluster_corner = deceptive degenerate start
RESULTS_DIR  = "results"

# Cluster-trap warm-start parameters: all points in a tight corner cluster.
# Chosen so warm_start ± 3σ stays inside bounds (avoids bounds-resampling
# at init, which would otherwise destroy the cluster — see evopy.py:126).
_CLUSTER_MEAN = 0.1
_CLUSTER_STD  = 0.02

# Known optimal min pairwise distances for n = 2..20 circles (from Packomania)
_TARGETS = [
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
    0.286611652351681559449894454738,  # 20
]


def get_target(n_circles):
    return _TARGETS[n_circles - 2]



def circles_in_a_square(individual):
    points = np.reshape(individual, (-1, 2))
    return pdist(points).min()


def _init_kwargs(init_mode, n_circles):
    """Resolve init_mode to EvoPy warm_start/mean/std kwargs."""
    if init_mode == "random":
        # Defaults: warm_start=None → zeros; std=1 → most coords resampled
        # uniformly across bounds (see evopy.py:126-127). Effectively uniform init.
        return {}
    if init_mode == "cluster_corner":
        return {
            'warm_start': np.full(n_circles * 2, _CLUSTER_MEAN),
            'mean':       0.0,
            'std':        _CLUSTER_STD,
        }
    raise ValueError(f"unknown init_mode: {init_mode!r}")


def run_single(args):
    """Run one ES trial. Returns a DataFrame of per-generation statistics."""
    n_circles, strategy, seed, init_mode = args
    target = get_target(n_circles)
    records = []

    def reporter(report):
        records.append({
            'generation':   report.generation,
            'evaluations':  report.evaluations,
            'best_fitness': report.best_fitness,
            'avg_fitness':  report.avg_fitness,
            'std_fitness':  report.std_fitness,
            'gap':          (target - report.best_fitness) / target,
        })

    EvoPy(
        fitness_function=circles_in_a_square,
        individual_length=n_circles * 2,
        reporter=reporter,
        maximize=True,
        generations=GENERATIONS,
        population_size=POPULATION,
        bounds=(0, 1),
        target_fitness_value=target,
        target_tolerance=min(TARGET_TOLS),
        max_evaluations=MAX_EVALS,
        random_seed=seed,
        strategy=strategy,
        num_children=7,
        **_init_kwargs(init_mode, n_circles),
    ).run()

    df = pd.DataFrame(records)
    df['seed']      = seed
    df['n_circles'] = n_circles
    df['strategy']  = strategy.name
    df['config']    = CONFIG_LABEL
    df['init_mode'] = init_mode
    return df


def compute_summary(run_dfs, target, n_circles, strategy_name, init_mode):
    final_rows    = [df.iloc[-1] for df in run_dfs]
    final_fitness = np.array([r['best_fitness'] for r in final_rows])
    final_evals   = np.array([r['evaluations']  for r in final_rows])
    fitness_gap   = np.abs(final_fitness - target)

    row = {'n_circles': n_circles, 'strategy': strategy_name, 'init_mode': init_mode}

    # Per-tolerance metrics: SR, ERT, FHT — all computed offline from the same runs
    for tol in TARGET_TOLS:
        tag = f"{tol:.0e}"   # "1e-02", "1e-03", "1e-05"
        successes = np.abs(final_fitness - target) < tol
        n_success = int(successes.sum())
        success_rate = n_success / len(run_dfs)
        ert = float(final_evals.sum()) / n_success if n_success > 0 else float('inf')

        hitting_evals = []
        for df, success in zip(run_dfs, successes):
            if success:
                hit = df[np.abs(df['best_fitness'] - target) < tol]
                if not hit.empty:
                    hitting_evals.append(hit.iloc[0]['evaluations'])
        hitting_evals = np.array(hitting_evals) if hitting_evals else np.array([np.inf])

        row.update({
            f'success_rate_{tag}':    round(success_rate, 4),
            f'n_success_{tag}':       n_success,
            f'ert_{tag}':             ert,
            f'ert_normalised_{tag}':  ert / MAX_EVALS,
            f'fht_median_{tag}':      float(np.median(hitting_evals)) if n_success > 0 else float('nan'),
            f'fht_mean_{tag}':        float(np.mean(hitting_evals))   if n_success > 0 else float('nan'),
            f'fht_std_{tag}':         float(np.std(hitting_evals))    if n_success > 1 else float('nan'),
            f'fht_min_{tag}':         float(np.min(hitting_evals))    if n_success > 0 else float('nan'),
        })

    # Tolerance-independent metrics
    convergence_evals_90 = []
    threshold_90 = 0.9 * target
    for df in run_dfs:
        reached = df[df['best_fitness'] >= threshold_90]
        convergence_evals_90.append(reached.iloc[0]['evaluations'] if not reached.empty else np.inf)

    row.update({
        # Final fitness
        'median_final_fitness':   float(np.median(final_fitness)),
        'mean_final_fitness':     float(np.mean(final_fitness)),
        'std_final_fitness':      float(np.std(final_fitness)),
        'best_final_fitness':     float(np.max(final_fitness)),
        'worst_final_fitness':    float(np.min(final_fitness)),
        # Fitness gap to optimum
        'median_gap':             float(np.median(fitness_gap)),
        'mean_gap':               float(np.mean(fitness_gap)),
        'best_gap':               float(np.min(fitness_gap)),
        # Evaluations used
        'median_evals':           float(np.median(final_evals)),
        'mean_evals':             float(np.mean(final_evals)),
        # Convergence speed
        'median_evals_to_90pct':  float(np.median(convergence_evals_90)),
        # Budget exhaustion: how many runs hit the eval cap
        'budget_exhausted_count': int(np.sum(final_evals >= MAX_EVALS)),
    })
    return row


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    summary_rows = []
    configs = list(product(CIRCLE_SIZES, STRATEGIES, INIT_MODES))

    print(f"Benchmarking {len(configs)} configurations × {N_RUNS} runs each "
          f"(max {MAX_EVALS:,} evals/run)\n")

    for n_circles, strategy, init_mode in configs:
        label = f"n={n_circles:2d}  strategy={strategy.name:<17s}  init={init_mode}"
        print(f"Running {label} ...", flush=True)

        args_list = [(n_circles, strategy, seed, init_mode) for seed in range(N_RUNS)]

        with multiprocessing.Pool() as pool:
            run_dfs = pool.map(run_single, args_list)

        combined = pd.concat(run_dfs, ignore_index=True)
        fname = os.path.join(RESULTS_DIR, f"raw_{n_circles}circles_{strategy.name}_{init_mode}.csv")
        combined.to_csv(fname, index=False)

        target  = get_target(n_circles)
        summary = compute_summary(run_dfs, target, n_circles, strategy.name, init_mode)
        summary_rows.append(summary)

        loose_tag = f"{max(TARGET_TOLS):.0e}"
        sr_key  = f"success_rate_{loose_tag}"
        ert_key = f"ert_{loose_tag}"
        ert_str = f"{summary[ert_key]:.0f}" if not np.isinf(summary[ert_key]) else ">max"
        print(f"  success@{loose_tag}={summary[sr_key]:.2f}  ERT@{loose_tag}={ert_str}"
              f"  median_fitness={summary['median_final_fitness']:.6f}")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(os.path.join(RESULTS_DIR, "summary.csv"), index=False)

    print("\n── Summary ────────────────────────────────────────────────────────────")
    print(summary_df.to_string(index=False))
    print(f"\nResults saved to '{RESULTS_DIR}/'")
    print("Run  python plot_results.py  to generate figures.")


if __name__ == "__main__":
    main()
