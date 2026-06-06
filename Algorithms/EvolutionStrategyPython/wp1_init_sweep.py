"""WP1 — clean single-harness initialization sweep.

Answers Leo's question with NO confound: vary ONLY the init scheme on the
bug-fixed baseline-B harness (single-variance, (mu,lambda), num_children=7,
pop 30, random repair, 100k evals), and measure every scheme against the honest
random (uniform) start. One harness, one reference, 25 seeds.

Four schemes (all share baseline-B otherwise):
  random     init="uniform"  -> i.i.d. uniform in the box  (the REFERENCE start)
  lhs        init="lhs"       -> Latin-hypercube stratified fill
  warm       warm_start=0,std=1 (else-branch Gaussian, center-biased, clamped/
             repaired) -> the old benchmark.py "random" mode = a warm start
  clustered  warm_start=0.1,std=0.02 -> tight corner blob (deceptive degenerate start)

Writes ONE row per run to ../../findings/data/wp1_init_sweep_per_run.csv.
Then: uv run --with matplotlib --with numpy --with scipy ../../findings/wp1_init_figs.py
(point its loader at the sweep file) to get the clean forest + boxplot.

Run (full):  uv run --with numpy wp1_init_sweep.py
Run (smoke): INIT_SEEDS=3 INIT_NS=7 INIT_EVALS=3000 uv run --with numpy wp1_init_sweep.py
"""
import os
import csv
import numpy as np

from ES.evopy import EvoPy, Strategy

CIRCLE_SIZES = [int(x) for x in os.environ.get("INIT_NS", "7,10,15,20").split(",")]
N_SEEDS   = int(os.environ.get("INIT_SEEDS", "25"))
MAX_EVALS = int(os.environ.get("INIT_EVALS", "100000"))
POPULATION   = 30
NUM_CHILDREN = 7
OUT = os.path.join("..", "..", "findings", "data", "wp1_init_sweep_per_run.csv")

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


# Baseline-B, everything frozen EXCEPT init (the swept factor).
BASE = dict(
    strategy=Strategy.SINGLE_VARIANCE,
    selection_scheme="comma",
    population_size=POPULATION,
    num_children=NUM_CHILDREN,
    repair="random",
)


def init_kwargs(scheme, n):
    """Resolve a scheme name to the EvoPy init-related kwargs (on top of BASE)."""
    d = n * 2
    if scheme == "random":      # honest random start = the REFERENCE
        return {"init": "uniform"}
    if scheme == "lhs":
        return {"init": "lhs"}
    if scheme == "warm":        # else-branch Gaussian: warm_start=0, std=1 (old "random")
        return {"init": "warm", "warm_start": np.zeros(d), "mean": 0.0, "std": 1.0}
    if scheme == "clustered":   # tight corner blob: deceptive degenerate start
        return {"init": "warm", "warm_start": np.full(d, 0.1), "mean": 0.0, "std": 0.02}
    raise ValueError(scheme)


SCHEMES = ["random", "lhs", "warm", "clustered"]


def run_one(scheme, n, seed):
    target = get_target(n)
    final = {"v": None}

    def reporter(r):
        final["v"] = r.best_fitness

    genotype = EvoPy(
        fitness, n * 2,
        reporter=reporter, maximize=True, bounds=(0, 1),
        generations=100000, max_evaluations=MAX_EVALS, random_seed=seed,
        **BASE, **init_kwargs(scheme, n),
    ).run()

    best = float(fitness(genotype)) if genotype is not None else float(final["v"])
    return {
        "init_scheme": scheme, "n_circles": n, "seed": seed,
        "final_best": round(best, 8),
        "final_gap": round((target - best) / target, 8),
    }


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fields = ["init_scheme", "n_circles", "seed", "final_best", "final_gap"]
    total = len(SCHEMES) * len(CIRCLE_SIZES) * N_SEEDS
    print(f"init sweep: {len(SCHEMES)} schemes x {len(CIRCLE_SIZES)} n x {N_SEEDS} seeds "
          f"= {total} runs, budget {MAX_EVALS:,} evals\n")
    with open(OUT, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for scheme in SCHEMES:
            for n in CIRCLE_SIZES:
                for seed in range(N_SEEDS):
                    w.writerow(run_one(scheme, n, seed))
                print(f"  done {scheme:10s} n={n:<3d} ({N_SEEDS} seeds)", flush=True)
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
