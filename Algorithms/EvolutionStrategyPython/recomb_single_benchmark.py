"""WP4 recombination benchmark using SINGLE_VARIANCE as baseline.

Treatments:
 - baseline (SINGLE_VARIANCE, recombine=False)
 - sigma_single_recomb_coord (SINGLE_VARIANCE, recombine coordinate)
 - sigma_single_recomb_pair  (SINGLE_VARIANCE, recombine circle_pair)

Writes results/per_run.csv compatible with stats.py.
"""
import os
import csv
import numpy as np

from ES.evopy import EvoPy, Strategy

# env-overridable
CIRCLE_SIZES = [int(x) for x in os.environ.get("WP1_NS", "7,10,15,20").split(",")]
N_SEEDS      = int(os.environ.get("WP1_SEEDS", "25"))
MAX_EVALS    = int(os.environ.get("WP1_EVALS", "100000"))
POPULATION   = 30
NUM_CHILDREN = 7
TOLS         = [1e-2, 1e-3, 1e-5]
RESULTS_DIR  = "results"
PER_RUN_CSV  = os.path.join(RESULTS_DIR, "per_run.csv")

_TARGETS = [
    1.4142135623730951, 1.0352761804100830, 1.0000000000000000, 0.7071067811865475,
    0.6009252125773315, 0.5358983848622454, 0.5176380902050415, 0.5000000000000000,
    0.4212795439839034, 0.3982073102368442, 0.3887301263230200, 0.3660960076964251,
    0.3489152603740189, 0.3410813774021089, 0.3333333333333333, 0.3061539853003329,
    0.3004626062886658, 0.2895419919949817, 0.2866116523516816,
]


def get_target(n_circles):
    return _TARGETS[n_circles - 2]


def fitness(individual):
    pts = np.asarray(individual).reshape(-1, 2)
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return float(d.min())


# Baseline: SINGLE_VARIANCE, recombine=False
BASELINE = dict(
    strategy=Strategy.SINGLE_VARIANCE,
    selection_scheme="comma",
    init="lhs",
    population_size=POPULATION,
    num_children=NUM_CHILDREN,
    recombine=False,
)

TREATMENTS = [
    ("baseline", "WP4", {}),
    ("sigma_single_recomb_coord", "WP4", {"recombine": True, "recombination_mode": "coordinate"}),
    ("sigma_single_recomb_pair",  "WP4", {"recombine": True, "recombination_mode": "circle_pair"}),
]


def run_one(overrides, n_circles, seed):
    target = get_target(n_circles)
    trace = []

    def reporter(r):
        trace.append((r.evaluations, r.best_fitness))

    kwargs = dict(BASELINE)
    kwargs.update(overrides)
    EvoPy(
        fitness, n_circles * 2,
        reporter=reporter, maximize=True, bounds=(0, 1),
        generations=100000, max_evaluations=MAX_EVALS, random_seed=seed,
        **kwargs,
    ).run()

    evals = np.array([e for e, _ in trace])
    best = np.array([b for _, b in trace])
    final_best = float(best[-1])

    row = {
        "treatment": None, "wp": None, "n_circles": n_circles, "seed": seed,
        "strategy": kwargs["strategy"].name, "init": kwargs["init"],
        "selection_scheme": kwargs["selection_scheme"],
        "final_best": round(final_best, 8),
        "final_gap": round((target - final_best) / target, 8),
        "total_evals": int(evals[-1]),
        "total_generations": len(trace),
    }
    for tol in TOLS:
        hit = np.where(np.abs(best - target) < tol)[0]
        row[f"evals_to_{tol:.0e}"] = int(evals[hit[0]]) if len(hit) else ""
    return row


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fields = ["treatment", "wp", "n_circles", "seed", "strategy", "init",
              "selection_scheme", "final_best", "final_gap", "total_evals",
              "total_generations"] + [f"evals_to_{t:.0e}" for t in TOLS]

    n_total = len(TREATMENTS) * len(CIRCLE_SIZES) * N_SEEDS
    print(f"Recomb (single-sigma) sweep: {len(TREATMENTS)} treatments x {len(CIRCLE_SIZES)} n x {N_SEEDS} seeds = {n_total} runs, budget {MAX_EVALS:,} evals\n")

    with open(PER_RUN_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for label, wp, overrides in TREATMENTS:
            for n in CIRCLE_SIZES:
                for seed in range(N_SEEDS):
                    row = run_one(overrides, n, seed)
                    row["treatment"], row["wp"] = label, wp
                    writer.writerow(row)
                print(f"  done {label:12s} n={n:<3d} ({N_SEEDS} seeds)", flush=True)

    print(f"\nWrote {PER_RUN_CSV}.  Next:  uv run --with scipy --with numpy stats.py")


if __name__ == "__main__":
    main()
