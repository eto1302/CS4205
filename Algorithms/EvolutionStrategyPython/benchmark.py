import math
import os
import multiprocessing
from itertools import product

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import euclidean_distances

from ES.evopy import EvoPy, Strategy

# ── Configuration ──────────────────────────────────────────────────────────────
CIRCLE_SIZES = [2, 3, 5, 7, 10, 15, 20]
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
    n = len(individual)
    distances = []
    for i in range(0, n - 1, 2):
        for j in range(i + 2, n, 2):
            distances.append(math.sqrt(
                (individual[i] - individual[j]) ** 2 +
                (individual[i + 1] - individual[j + 1]) ** 2
            ))
    return min(distances)


def circles_in_a_square_scipy(individual):
    points = np.reshape(individual, (-1, 2))
    dist = euclidean_distances(points)
    np.fill_diagonal(dist, 1e10)
    return np.min(dist)


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

    fitness_fn = circles_in_a_square if n_circles < 12 else circles_in_a_square_scipy

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
    df['run_id']    = seed
    df['n_circles'] = n_circles
    df['strategy']  = strategy.name
    df['seed']      = seed
    return df


def compute_summary(run_dfs, target, n_circles, strategy_name):
    """Compute ERT, success rate, and fitness statistics across multiple runs."""
    final_rows    = [df.iloc[-1] for df in run_dfs]
    final_fitness = np.array([r['best_fitness'] for r in final_rows])
    final_evals   = np.array([r['evaluations']  for r in final_rows])

    successes    = np.abs(final_fitness - target) < TARGET_TOL
    n_success    = int(successes.sum())
    success_rate = n_success / len(run_dfs)

    # ERT = total evaluations across all runs / successful runs (BBOB definition)
    ert = float(final_evals.sum()) / n_success if n_success > 0 else float('inf')

    return {
        'n_circles':            n_circles,
        'strategy':             strategy_name,
        'success_rate':         round(success_rate, 4),
        'ert':                  ert,
        'median_final_fitness': float(np.median(final_fitness)),
        'mean_final_fitness':   float(np.mean(final_fitness)),
        'std_final_fitness':    float(np.std(final_fitness)),
        'median_evals':         float(np.median(final_evals)),
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
