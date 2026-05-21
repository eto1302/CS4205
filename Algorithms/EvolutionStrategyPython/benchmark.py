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
TARGET_TOL   = 1e-2
RESULTS_DIR  = "results"

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


def run_single(args):
    """Run one ES trial. Returns a DataFrame of per-generation statistics."""
    n_circles, strategy, seed = args
    records = []

    def reporter(report):
        records.append({
            'generation':   report.generation,
            'evaluations':  report.evaluations,
            'best_fitness': report.best_fitness,
            'avg_fitness':  report.avg_fitness,
            'std_fitness':  report.std_fitness,
        })

    fitness_fn = circles_in_a_square

    EvoPy(
        fitness_function=fitness_fn,
        individual_length=n_circles * 2,
        reporter=reporter,
        maximize=True,
        generations=GENERATIONS,
        population_size=POPULATION,
        bounds=(0, 1),
        target_fitness_value=get_target(n_circles),
        target_tolerance=TARGET_TOL,
        max_evaluations=MAX_EVALS,
        random_seed=seed,
        strategy=strategy,
        num_children=7
    ).run()

    df = pd.DataFrame(records)
    df['seed']    = seed
    df['n_circles'] = n_circles
    df['strategy']  = strategy.name
    return df


def compute_summary(run_dfs, target, n_circles, strategy_name):
    final_rows    = [df.iloc[-1] for df in run_dfs]
    final_fitness = np.array([r['best_fitness'] for r in final_rows])
    final_evals   = np.array([r['evaluations']  for r in final_rows])

    successes    = np.abs(final_fitness - target) < TARGET_TOL
    n_success    = int(successes.sum())
    success_rate = n_success / len(run_dfs)

    ert = float(final_evals.sum()) / n_success if n_success > 0 else float('inf')

    fitness_gap = np.abs(final_fitness - target)

    hitting_evals = []
    for df, success in zip(run_dfs, successes):
        if success:
            hit = df[np.abs(df['best_fitness'] - target) < TARGET_TOL]
            if not hit.empty:
                hitting_evals.append(hit.iloc[0]['evaluations'])
    hitting_evals = np.array(hitting_evals) if hitting_evals else np.array([np.inf])

    convergence_evals_90 = []
    threshold_90 = 0.9 * target
    for df in run_dfs:
        reached = df[df['best_fitness'] >= threshold_90]
        convergence_evals_90.append(reached.iloc[0]['evaluations'] if not reached.empty else np.inf)

    return {
        'n_circles':              n_circles,
        'strategy':               strategy_name,
        # Success
        'success_rate':           round(success_rate, 4),
        'n_success':              n_success,
        # ERT (BBOB standard)
        'ert':                    ert,
        'ert_normalised':         ert / MAX_EVALS,
        # First-hitting time (successful runs only)
        'fht_median':             float(np.median(hitting_evals))   if n_success > 0 else float('nan'),
        'fht_mean':               float(np.mean(hitting_evals))     if n_success > 0 else float('nan'),
        'fht_std':                float(np.std(hitting_evals))      if n_success > 1 else float('nan'),
        'fht_min':                float(np.min(hitting_evals))      if n_success > 0 else float('nan'),
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
    }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    summary_rows = []
    configs = list(product(CIRCLE_SIZES, STRATEGIES))

    print(f"Benchmarking {len(configs)} configurations × {N_RUNS} runs each "
          f"(max {MAX_EVALS:,} evals/run)\n")

    for n_circles, strategy in configs:
        label = f"n={n_circles:2d}  strategy={strategy.name}"
        print(f"Running {label} ...", flush=True)

        args_list = [(n_circles, strategy, seed) for seed in range(N_RUNS)]

        with multiprocessing.Pool() as pool:
            run_dfs = pool.map(run_single, args_list)

        combined = pd.concat(run_dfs, ignore_index=True)
        fname = os.path.join(RESULTS_DIR, f"raw_{n_circles}circles_{strategy.name}.csv")
        combined.to_csv(fname, index=False)

        target  = get_target(n_circles)
        summary = compute_summary(run_dfs, target, n_circles, strategy.name)
        summary_rows.append(summary)

        ert_str = f"{summary['ert']:.0f}" if not np.isinf(summary['ert']) else ">max"
        print(f"  success={summary['success_rate']:.2f}  ERT={ert_str}"
              f"  median_fitness={summary['median_final_fitness']:.6f}")

    summary_df = pd.DataFrame(summary_rows)
    summary_df.to_csv(os.path.join(RESULTS_DIR, "summary.csv"), index=False)

    print("\n── Summary ────────────────────────────────────────────────────────────")
    print(summary_df.to_string(index=False))
    print(f"\nResults saved to '{RESULTS_DIR}/'")
    print("Run  python plot_results.py  to generate figures.")


if __name__ == "__main__":
    main()
