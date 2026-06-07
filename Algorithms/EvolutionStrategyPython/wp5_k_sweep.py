"""Q2 — k sensitivity sweep for interleaved L-BFGS-B polish.

Sweeps local_search_k in {5, 10, 20, 50} across all n_circles and seeds,
writing results/per_run_k_sweep.csv.  Then run plot_wp5_k_sweep.py to plot.

Run (full, ~33 min):  python3 wp5_k_sweep.py
Run (smoke, ~2 min):  WP1_SEEDS=5 WP1_NS=10 python3 wp5_k_sweep.py
"""
import os
import csv
import numpy as np

from ES.evopy import EvoPy, Strategy

CIRCLE_SIZES = [int(x) for x in os.environ.get("WP1_NS",    "7, 10, 15, 20").split(",")]
N_SEEDS      = int(os.environ.get("WP1_SEEDS", "25"))
MAX_EVALS    = int(os.environ.get("WP1_EVALS", "100000"))
POPULATION   = 30
NUM_CHILDREN = 7
RESULTS_DIR  = "results"
OUT_CSV      = os.path.join(RESULTS_DIR, "per_run_k_sweep.csv")

_TARGETS = [
    1.4142135623730951, 1.0352761804100830, 1.0000000000000000, 0.7071067811865475,
    0.6009252125773315, 0.5358983848622454, 0.5176380902050415, 0.5000000000000000,
    0.4212795439839034, 0.3982073102368442, 0.3887301263230200, 0.3660960076964251,
    0.3489152603740189, 0.3410813774021089, 0.3333333333333333, 0.3061539853003329,
    0.3004626062886658, 0.2895419919949817, 0.2866116523516816,
]

K_VALUES = [5, 10, 20, 50]

BASELINE = dict(
    strategy=Strategy.SINGLE_VARIANCE,
    selection_scheme="comma",
    init="lhs",
    population_size=POPULATION,
    num_children=NUM_CHILDREN,
)


def get_target(n):
    return _TARGETS[n - 2]


def fitness(individual):
    pts = np.asarray(individual).reshape(-1, 2)
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return float(d.min())


def run_one(k, n_circles, seed):
    target = get_target(n_circles)

    es = EvoPy(
        fitness, n_circles * 2,
        maximize=True, bounds=(0, 1),
        generations=100_000,
        max_evaluations=MAX_EVALS,
        random_seed=seed,
        local_search="interleaved",
        local_search_k=k,
        **BASELINE,
    )
    result_genotype = es.run()
    final_best = float(fitness(result_genotype)) if result_genotype is not None else 0.0

    plog = es.polish_log
    return {
        "k":                  k,
        "n_circles":          n_circles,
        "seed":               seed,
        "final_gap":          round((target - final_best) / target, 8),
        "lbfgsb_calls":       len(plog),
        "lbfgsb_evals_total": sum(e for _, e, _, _, _ in plog),
        "lbfgsb_evals_mean":  round(sum(e for _, e, _, _, _ in plog) / len(plog), 1) if plog else 0,
    }


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fields = ["k", "n_circles", "seed", "final_gap", "lbfgsb_calls",
              "lbfgsb_evals_total", "lbfgsb_evals_mean"]

    n_total = len(K_VALUES) * len(CIRCLE_SIZES) * N_SEEDS
    print(f"k-sweep: {len(K_VALUES)} k-values x {len(CIRCLE_SIZES)} n x "
          f"{N_SEEDS} seeds = {n_total} runs, budget {MAX_EVALS:,} evals\n")

    with open(OUT_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for k in K_VALUES:
            for n in CIRCLE_SIZES:
                for seed in range(N_SEEDS):
                    row = run_one(k, n, seed)
                    writer.writerow(row)
                print(f"  done k={k:<3d}  n={n:<3d}  ({N_SEEDS} seeds)", flush=True)

    print(f"\nWrote {OUT_CSV}.  Next:  python3 plot_wp5_k_sweep.py")


if __name__ == "__main__":
    main()
