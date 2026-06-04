"""WP1 — Architecture-B OFAT benchmark runner.

Sweeps (treatment x n x seed) and writes ONE row per run to
`results/per_run.csv` — the direct input to `stats.py` (Mann-Whitney + A12).

"OFAT" = one-factor-at-a-time: every treatment is the frozen BASELINE with
exactly ONE thing changed, and is compared against that same baseline. Each work
package adds **one line** to TREATMENTS (no merge conflicts). See
`groupwork-notes/comparison-architectures/`.

The per-run row stores both the fixed-budget metric (`final_gap`) and the
fixed-target metric (`evals_to_<tol>`), so the comparison survives saturation:
when everyone converges, `final_gap` is useless but `evals_to_*` still
discriminates (and vice-versa on hard n). success-rate (Fisher's exact) is
PARKED — the columns to compute it later are already here (count of non-empty
`evals_to_<tol>`).

Run (full):   uv run --with numpy ofat_benchmark.py
Run (smoke):  WP1_SEEDS=6 WP1_NS=7 WP1_EVALS=4000 uv run --with numpy ofat_benchmark.py
"""
import os
import csv
import numpy as np

from ES.evopy import EvoPy, Strategy

# ── config (env-overridable so the smoke test is cheap) ──────────────────────
CIRCLE_SIZES = [int(x) for x in os.environ.get("WP1_NS", "15").split(",")]
N_SEEDS      = int(os.environ.get("WP1_SEEDS", "25"))
MAX_EVALS    = int(os.environ.get("WP1_EVALS", "100000"))
POPULATION   = 30
NUM_CHILDREN = 7                      # lambda = 210, lambda/mu = 7 (BSw95)
TOLS         = [1e-2, 1e-3, 1e-5]
RESULTS_DIR  = "results"
PER_RUN_CSV  = os.path.join(RESULTS_DIR, "per_run.csv")

# Packomania optimal min pairwise distance, n = 2..20
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
    """CiaS: maximise the minimum pairwise distance between n points."""
    pts = np.asarray(individual).reshape(-1, 2)
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return float(d.min())


# ── Architecture B: frozen baseline + one-line-per-WP treatment registry ─────
BASELINE = dict(
    strategy=Strategy.SINGLE_VARIANCE,
    selection_scheme="comma",          # B pins (mu,lambda); scheme choice is WP2's axis
    init="lhs",
    population_size=POPULATION,
    num_children=NUM_CHILDREN,
)

# (label, owning-WP, overrides-on-top-of-BASELINE). Each WP appends ONE line.
TREATMENTS = [
    ("baseline",  "WP1", {}),
    ("B-no_lhs",  "WP1", {"init": "uniform"}),   # LHS ablation: quantifies LHS's contribution
    # ("B+archive",      "WP2", {"archive_size": 5}),       # Ivan
    # ("B+plus",         "WP2", {"selection_scheme": "plus"}),
    # ("B-clip",         "WP3", {"repair": "clip"}),         # Cala
    # ("B+recomb",       "WP4", {"recombine": True}),        # Agata
    ("B+final_polish",       "WP5", {"local_search": "final"}),        # Martin
    ("B+interleaved_polish", "WP5", {"local_search": "interleaved"}),  # Martin
]


def run_one(overrides, n_circles, seed):
    """One run → one per_run row dict. No early-stop: full budget, so SR/ERT are
    computed offline at every tolerance (benchmark-review I1)."""
    target = get_target(n_circles)
    trace = []                                   # (evaluations, best_fitness) per generation

    def reporter(r):
        trace.append((r.evaluations, r.best_fitness))

    kwargs = dict(BASELINE)
    kwargs.update(overrides)
    result_genotype = EvoPy(
        fitness, n_circles * 2,
        reporter=reporter, maximize=True, bounds=(0, 1),
        generations=100000,                      # never the binding cap
        max_evaluations=MAX_EVALS,               # the only stop criterion
        random_seed=seed,
        **kwargs,
    ).run()

    evals = np.array([e for e, _ in trace])
    best = np.array([b for _, b in trace])
    # Evaluate the returned genotype: for "final" polish this captures the
    # post-polish fitness that was never recorded by the reporter.
    final_best = float(fitness(result_genotype)) if result_genotype is not None else float(best[-1])

    row = {
        "treatment": None, "wp": None, "n_circles": n_circles, "seed": seed,
        "strategy": kwargs["strategy"].name, "init": kwargs["init"],
        "selection_scheme": kwargs["selection_scheme"],
        "final_best": round(final_best, 8),
        "final_gap": round((target - final_best) / target, 8),
        "total_evals": int(evals[-1]),
        "total_generations": len(trace),
    }
    # fixed-target columns: first eval where |best - target| < tol; "" if never
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
    print(f"OFAT sweep: {len(TREATMENTS)} treatments x {len(CIRCLE_SIZES)} n x "
          f"{N_SEEDS} seeds = {n_total} runs, budget {MAX_EVALS:,} evals\n")

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
