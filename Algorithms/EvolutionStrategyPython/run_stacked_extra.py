"""Extra stacked variants beyond stacked_benchmark.CHAIN: the final-polish (f-polish)
arms, plus a raw-trace capture of all six variants (per-generation best, NOT
best-so-far) so a 'current-gen median' convergence can be plotted.

  STK_EVALS=100000 python run_stacked_extra.py   # writes results/STACKED/{traces_fpolish,traces_raw}.csv
  STK_EVALS=200000 python run_stacked_extra.py   # writes results/STACKED_200k/...
"""
import os, csv, numpy as np
import stacked_benchmark as sb

sb.MAX_EVALS = int(os.environ.get("STK_EVALS", "100000"))
TAG = "" if sb.MAX_EVALS == 100000 else f"_{sb.MAX_EVALS // 1000}k"
OUTDIR = os.path.join(sb.REPO_ROOT, "results", "STACKED" + TAG); os.makedirs(OUTDIR, exist_ok=True)

FPOLISH = [("+clip+f-polish",             {"repair": "clip", "local_search": "final"}),
           ("+clip+f-polish+bookkeeping", {"repair": "clip", "local_search": "final",
                                           "archive_mode": "bookkeeping"})]
ALL6 = [("baseline", {}), ("+clip", {"repair": "clip"})] + FPOLISH + [
    ("+clip+polish",         {"repair": "clip", "local_search": "interleaved"}),
    ("+clip+polish+archive", {"repair": "clip", "local_search": "interleaved", "archive_mode": "bookkeeping"})]
NS = [7, 10, 15, 20]; SEEDS = 25

def sweep(variants, out, accumulate):
    with open(out, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["variant", "n_circles", "seed", "evaluations", "best_fitness"])
        for label, ov in variants:
            for n in NS:
                for s in range(SEEDS):
                    _, trace = sb.run_one(ov, n, s)
                    bf = np.array([b for _, b in trace], float)
                    bf = np.maximum.accumulate(bf) if (accumulate and len(bf)) else bf
                    for (e, _), b in zip(trace, bf): w.writerow([label, n, s, int(e), f"{b:.8f}"])
                print(f"done {label:28s} n={n}", flush=True)
    print("saved", out)

sweep(FPOLISH, os.path.join(OUTDIR, "traces_fpolish.csv"), accumulate=True)   # best-so-far
sweep(ALL6,    os.path.join(OUTDIR, "traces_raw.csv"),      accumulate=False)  # raw per-gen
