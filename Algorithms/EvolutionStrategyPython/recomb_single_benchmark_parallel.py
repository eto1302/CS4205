"""Parallel recombination-on-SINGLE runner.

Parallelises independent runs (treatment x n_circles x seed) using
`concurrent.futures.ProcessPoolExecutor` and writes `results/per_run.csv`
after all workers complete.

This script is non-destructive and leaves the sequential
`recomb_single_benchmark.py` unchanged.
"""
import os
import csv
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import the run logic from the sequential script
from recomb_single_benchmark import run_one, TREATMENTS, CIRCLE_SIZES, N_SEEDS, TOLS, MAX_EVALS

RESULTS_DIR = "results"
PER_RUN_CSV = os.path.join(RESULTS_DIR, "per_run.csv")


def _get_workers():
    env = os.environ.get("WP1_WORKERS")
    if env:
        try:
            v = int(env)
            return max(1, v)
        except Exception:
            pass
    try:
        import os as _os
        cpu = _os.cpu_count() or 1
    except Exception:
        cpu = 1
    return max(1, min(cpu - 1 if cpu > 1 else 1, 8))


def _task(args):
    # args: (label, wp, overrides, n, seed)
    label, wp, overrides, n, seed = args
    row = run_one(overrides, n, seed)
    row["treatment"] = label
    row["wp"] = wp
    return row


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    fields = ["treatment", "wp", "n_circles", "seed", "strategy", "init",
              "selection_scheme", "final_best", "final_gap", "total_evals",
              "total_generations"] + [f"evals_to_{t:.0e}" for t in TOLS]

    tasks = []
    for label, wp, overrides in TREATMENTS:
        for n in CIRCLE_SIZES:
            for seed in range(N_SEEDS):
                tasks.append((label, wp, overrides, n, seed))

    n_total = len(tasks)
    workers = _get_workers()

    # Header
    print("=== Parallel recomb-single sweep ===", flush=True)
    print(f"treatments: {len(TREATMENTS)}", flush=True)
    print(f"n values: {CIRCLE_SIZES}", flush=True)
    print(f"seeds: {N_SEEDS}", flush=True)
    print(f"total runs: {n_total}", flush=True)
    print(f"eval budget per run: {MAX_EVALS}", flush=True)
    print(f"workers: {workers}", flush=True)

    t0 = time.time()
    rows = []
    completed = 0
    group_counts = {}
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_task, task): task for task in tasks}
        for fut in as_completed(futures):
            try:
                row = fut.result()
            except Exception as e:
                print(f"Task failed: {e}", flush=True)
                continue
            completed += 1
            rows.append(row)
            elapsed = time.time() - t0
            avg = elapsed / completed
            remaining = n_total - completed
            eta = avg * remaining
            # format
            def fmt_s(s):
                m, s = divmod(int(s), 60)
                h, m = divmod(m, 60)
                return f"{h:02d}:{m:02d}:{s:02d}"

            avg_str = f"{int(avg//60):02d}:{int(avg%60):02d}"
            eta_str = fmt_s(eta)
            elapsed_str = fmt_s(elapsed)

            tname = row.get("treatment")
            tn = row.get("n_circles")
            tseed = row.get("seed")
            print(f"[{completed}/{n_total}] treatment={tname} n={tn} seed={tseed} elapsed={elapsed_str} avg/run={avg_str} ETA={eta_str}", flush=True)

            key = (tname, tn)
            group_counts[key] = group_counts.get(key, 0) + 1
            if group_counts[key] == N_SEEDS:
                print(f"completed {tname} n={tn}: {N_SEEDS}/{N_SEEDS} seeds", flush=True)

    # sort rows for deterministic output ordering
    rows.sort(key=lambda r: (r["treatment"], int(r["n_circles"]), int(r["seed"])))

    with open(PER_RUN_CSV, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    dt = time.time() - t0
    print(f"Wrote {PER_RUN_CSV}.  Collected {len(rows)} rows in {dt:.1f}s")


if __name__ == '__main__':
    main()
