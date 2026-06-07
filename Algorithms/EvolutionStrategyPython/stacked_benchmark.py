"""Stacked-improvements benchmark — the cumulative "best settings" chain.

Unlike `ofat_benchmark.py` (one factor at a time vs a FROZEN baseline), this runs
the CUMULATIVE chain: each variant turns on every improvement of the previous one
PLUS one more, so we measure the *real* stacked algorithm instead of assuming the
OFAT effects add up.

Chain (each variant = FULL kwargs on top of the shared BASELINE, not a delta):

  baseline               WP1 bug-fixed B: single-var, LHS, (mu,lambda), random repair
  +clip                  + WP3 clip constraint repair
  +clip+polish           + WP5 interleaved L-BFGS-B gradient polish
  +clip+polish+archive   + WP2 elitist bookkeeping archive

The first variant keeps the literal label "baseline" so `stats.py` compares each
later stage against it (the cumulative effect of the climb). Excluded on purpose:
WP2 plus-selection (hurts n=10) and WP4 recombination (honest negative).

Outputs go under  results/STACKED/  (repo root) and NEVER touch the OFAT results/:
  per_run.csv      one row per run  (schema == ofat_benchmark -> stats.py-ready)
  traces.csv       one row per generation per run: variant,n_circles,seed,evaluations,best_fitness
  comparisons.csv  stats.py output (each variant vs baseline)
  plots/convergence_stacked_improvements.png   median best-so-far GAP vs evals (2x2 by n)
  plots/final_gap_vs_n_stacked.png             median final gap vs problem size n
  plots/forest_final_gap.png                   reused OFAT forest (stats verdict)

Run (full):   uv run --with numpy --with scipy --with matplotlib stacked_benchmark.py
Run (smoke):  STK_SEEDS=3 STK_NS=10 STK_EVALS=4000 uv run --with numpy --with scipy --with matplotlib stacked_benchmark.py
"""
import os
import csv
import math

import numpy as np

from ES.evopy import EvoPy
import ofat_benchmark as ofat            # BASELINE, get_target, fitness, TOLS (reused verbatim)
import stats as ofat_stats               # Mann-Whitney + A12 layer (paths monkeypatched below)
import plot_ofat                         # forest plot (paths monkeypatched below)

# ── config (env-overridable so the smoke test is cheap) ──────────────────────
CIRCLE_SIZES = [int(x) for x in os.environ.get("STK_NS", "7,10,15,20").split(",")]
N_SEEDS      = int(os.environ.get("STK_SEEDS", "25"))
MAX_EVALS    = int(os.environ.get("STK_EVALS", "100000"))
TOLS         = ofat.TOLS

# results/STACKED at the REPO ROOT (…/Algorithms/EvolutionStrategyPython/this.py -> repo).
# Non-default budgets get their own folder (e.g. results/STACKED_200k) so the 100k
# figures are never overwritten — STK_TAG overrides the auto suffix if needed.
REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TAG         = os.environ.get("STK_TAG", "" if MAX_EVALS == 100000 else f"_{MAX_EVALS // 1000}k")
OUT_DIR     = os.path.join(REPO_ROOT, "results", "STACKED" + TAG)
PER_RUN_CSV = os.path.join(OUT_DIR, "per_run.csv")
TRACES_CSV  = os.path.join(OUT_DIR, "traces.csv")
COMPARE_CSV = os.path.join(OUT_DIR, "comparisons.csv")
PLOTS_DIR   = os.path.join(OUT_DIR, "plots")

# ── the cumulative chain (label, overrides-on-top-of-BASELINE) ───────────────
# Order matters: it is the order improvements are switched ON.
CHAIN = [
    ("baseline",             {}),                                                              # WP1
    ("+clip",                {"repair": "clip"}),                                              # WP3
    ("+clip+polish",         {"repair": "clip", "local_search": "interleaved"}),              # WP5
    ("+clip+polish+archive", {"repair": "clip", "local_search": "interleaved",
                              "archive_mode": "bookkeeping"}),                                 # WP2
]

# stable colours for the climb (baseline -> full stack)
COLORS = {
    "baseline":             "#7f7f7f",
    "+clip":                "#1f77b4",
    "+clip+polish":         "#2ca02c",
    "+clip+polish+archive": "#9467bd",
}


def run_one(overrides, n_circles, seed):
    """One run -> (per_run row dict, trace list of (evals, best_fitness)).

    Mirrors ofat_benchmark.run_one but ALSO returns the per-generation trace and
    appends a terminal (total_evals, final_best) point so the convergence-curve
    endpoint reflects the returned (post-polish) genotype, which the reporter —
    firing before the polish step — would otherwise miss.
    """
    target = ofat.get_target(n_circles)
    trace = []

    def reporter(r):
        trace.append((r.evaluations, r.best_fitness))

    kwargs = dict(ofat.BASELINE)
    kwargs.update(overrides)
    result_genotype = EvoPy(
        ofat.fitness, n_circles * 2,
        reporter=reporter, maximize=True, bounds=(0, 1),
        generations=100000,                 # never the binding cap
        max_evaluations=MAX_EVALS,          # the only stop criterion
        random_seed=seed,
        **kwargs,
    ).run()

    evals = np.array([e for e, _ in trace])
    best = np.array([b for _, b in trace])
    final_best = float(ofat.fitness(result_genotype)) if result_genotype is not None else float(best[-1])

    # terminal point: capture polish gains the reporter never logged
    if len(evals) and final_best > best[-1] + 1e-12:
        trace.append((int(evals[-1]), final_best))

    row = {
        "treatment": None, "wp": "STACK", "n_circles": n_circles, "seed": seed,
        "strategy": kwargs["strategy"].name, "init": kwargs["init"],
        "selection_scheme": kwargs["selection_scheme"],
        "archive_mode": kwargs.get("archive_mode", "off"),
        "repair": kwargs.get("repair", "random"),
        "final_best": round(final_best, 8),
        "final_gap": round((target - final_best) / target, 8),
        "total_evals": int(evals[-1]) if len(evals) else 0,
        "total_generations": len(evals),
    }
    for tol in TOLS:
        hit = np.where(np.abs(best - target) < tol)[0]
        row[f"evals_to_{tol:.0e}"] = int(evals[hit[0]]) if len(hit) else ""
    return row, trace


def run_chain():
    """Sweep (variant x n x seed); write per_run.csv + traces.csv; keep traces in memory."""
    os.makedirs(OUT_DIR, exist_ok=True)
    fields = ["treatment", "wp", "n_circles", "seed", "strategy", "init",
              "selection_scheme", "archive_mode", "repair", "final_best", "final_gap",
              "total_evals", "total_generations"] + [f"evals_to_{t:.0e}" for t in TOLS]

    n_total = len(CHAIN) * len(CIRCLE_SIZES) * N_SEEDS
    print(f"STACKED sweep: {len(CHAIN)} variants x {len(CIRCLE_SIZES)} n x {N_SEEDS} seeds "
          f"= {n_total} runs, budget {MAX_EVALS:,} evals\n")

    per_run_rows = []
    traces = {}   # (variant, n) -> list of per-seed trace arrays (evals, bestsofar)

    with open(PER_RUN_CSV, "w", newline="") as fr, open(TRACES_CSV, "w", newline="") as ft:
        rw = csv.DictWriter(fr, fieldnames=fields)
        rw.writeheader()
        tw = csv.writer(ft)
        tw.writerow(["variant", "n_circles", "seed", "evaluations", "best_fitness"])

        for label, overrides in CHAIN:
            for n in CIRCLE_SIZES:
                for seed in range(N_SEEDS):
                    row, trace = run_one(overrides, n, seed)
                    row["treatment"] = label
                    rw.writerow(row)
                    per_run_rows.append(row)

                    ev = np.array([e for e, _ in trace], dtype=float)
                    bf = np.array([b for _, b in trace], dtype=float)
                    bsf = np.maximum.accumulate(bf) if len(bf) else bf   # best-so-far
                    for e, b in zip(ev, bsf):
                        tw.writerow([label, n, seed, int(e), f"{b:.8f}"])
                    traces.setdefault((label, n), []).append((ev, bsf))
                print(f"  done {label:22s} n={n:<3d} ({N_SEEDS} seeds)", flush=True)

    print(f"\nWrote {PER_RUN_CSV}\nWrote {TRACES_CSV}")
    return per_run_rows, traces


def run_stats():
    """Reuse stats.py on the STACKED per_run.csv (monkeypatch its paths)."""
    ofat_stats.PER_RUN_CSV = PER_RUN_CSV
    ofat_stats.COMPARISONS_CSV = COMPARE_CSV
    ofat_stats.RESULTS_DIR = OUT_DIR
    print("\n── stats (each variant vs baseline) ──")
    ofat_stats.main()


# ── plots ────────────────────────────────────────────────────────────────────
def _median_gap_grid(seed_traces, target, grid):
    """For one (variant, n): median best-so-far GAP across seeds at each grid eval."""
    rows = []
    for ev, bsf in seed_traces:
        if not len(ev):
            continue
        idx = np.clip(np.searchsorted(ev, grid, side="right") - 1, 0, len(bsf) - 1)
        rows.append((target - bsf[idx]) / target)
    return np.median(np.vstack(rows), axis=0)


def plot_convergence(traces):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker

    n_list = sorted({n for _, n in traces})
    n_cols = min(2, len(n_list))
    n_rows = math.ceil(len(n_list) / n_cols)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(7 * n_cols, 4 * n_rows), squeeze=False)
    fig.suptitle("Stacked improvements — convergence  (median best-so-far RELATIVE gap to optimum vs evaluations,\n"
                 f"{N_SEEDS} seeds, {MAX_EVALS:,} evals;  gap = (optimum − achieved)/optimum,  0 = optimal)",
                 fontsize=12)

    yticks = [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 1.0]
    for idx, n in enumerate(n_list):
        ax = axes[idx // n_cols][idx % n_cols]
        target = ofat.get_target(n)
        grid = np.linspace(1, MAX_EVALS, 200)
        for label, _ in CHAIN:
            seed_traces = traces.get((label, n))
            if not seed_traces:
                continue
            med = _median_gap_grid(seed_traces, target, grid)
            ax.plot(grid, med, color=COLORS[label], lw=2.2, label=label)
        ax.set_yscale("log")
        # plain-decimal y ticks (no scientific notation)
        ax.yaxis.set_major_locator(mticker.FixedLocator(yticks))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:g}"))
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
        ax.set_title(f"{n} circles")
        ax.set_xlabel("Evaluations")
        ax.set_ylabel("Median relative gap to optimum  (lower = better)")
        ax.grid(True, which="both", alpha=0.25)
        ax.legend(fontsize=8, loc="upper right", title="improvements stacked")
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

    for idx in range(len(n_list), n_rows * n_cols):
        axes[idx // n_cols][idx % n_cols].set_visible(False)

    fig.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    out = os.path.join(PLOTS_DIR, "convergence_stacked_improvements.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def plot_final_gap_vs_n(per_run_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ns = sorted({r["n_circles"] for r in per_run_rows})
    fig, ax = plt.subplots(figsize=(8, 5.5))
    for label, _ in CHAIN:
        meds = []
        for n in ns:
            vals = [r["final_gap"] for r in per_run_rows
                    if r["treatment"] == label and r["n_circles"] == n]
            meds.append(np.median(vals) if vals else np.nan)
        ax.plot(ns, meds, "o-", color=COLORS[label], lw=2, ms=7, label=label)

    ax.set_xticks(ns)
    ax.set_xlabel("Problem size  n  (number of circles)")
    ax.set_ylabel("Median relative final gap to optimum  (0 = optimal; lower = better)")
    ax.set_title("Stacked improvements — relative final gap vs problem size\n"
                 f"({N_SEEDS} seeds, {MAX_EVALS:,} evals;  gap = (optimum − achieved)/optimum)", fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(title="improvements stacked", fontsize=9)
    fig.tight_layout()
    os.makedirs(PLOTS_DIR, exist_ok=True)
    out = os.path.join(PLOTS_DIR, "final_gap_vs_n_stacked.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def plot_forest():
    """Reuse the OFAT forest on the STACKED comparisons (cumulative effect vs baseline)."""
    plot_ofat.COMPARISONS_CSV = COMPARE_CSV
    plot_ofat.PLOTS_DIR = PLOTS_DIR
    plot_ofat.main()


def main():
    per_run_rows, traces = run_chain()
    run_stats()
    print("\n── plots ──")
    plot_convergence(traces)
    plot_final_gap_vs_n(per_run_rows)
    plot_forest()
    print(f"\nDone. Outputs under {OUT_DIR}")


if __name__ == "__main__":
    main()
