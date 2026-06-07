"""Add a 5th stacked variant: +clip + FINAL polish + archive.

Hypothesis: interleaved polish + archive hurt because the archive hijacks the
polish target away from the live population. FINAL polish runs once after the
loop on the archived best-ever, so there is no feedback loop to break — it should
NOT suffer that interaction. This runs only the new variant, merges it with the
existing 4-variant STACKED data, and rebuilds the convergence figure with 5 lines.

Run: uv run --with numpy --with scipy --with matplotlib run_final_archive.py
Smoke: FA_SEEDS=2 FA_NS=10 FA_EVALS=3000 uv run ... run_final_archive.py
"""
import os
import csv
import shutil
import numpy as np
from scipy.stats import mannwhitneyu

import stacked_benchmark as sb
import stats as S

NEW_LABEL = "+clip+f-polish+archive"
NEW_OV = {"repair": "clip", "local_search": "final", "archive_mode": "bookkeeping"}
NEW_COLOR = "#ff7f0e"

NS = [int(x) for x in os.environ.get("FA_NS", "7,10,15,20").split(",")]
SEEDS = int(os.environ.get("FA_SEEDS", "25"))
sb.MAX_EVALS = int(os.environ.get("FA_EVALS", "100000"))

STACKED = os.path.join(sb.REPO_ROOT, "results", "STACKED")
OUT = os.path.join(sb.REPO_ROOT, "results", "STACKED_5var")
OVERLEAF = ("/mnt/c/Users/user/uni-notes/courses/CS4205-evolutionary-algorithms/assignments/"
            "groupwork-notes/wp1-presentation-figs/overleaf-STACKED")
os.makedirs(os.path.join(OUT, "plots"), exist_ok=True)

# ── 1. run only the new variant ──────────────────────────────────────────────
new_per_run, new_trace_rows = [], []
for n in NS:
    for seed in range(SEEDS):
        row, trace = sb.run_one(NEW_OV, n, seed)
        row["treatment"] = NEW_LABEL
        new_per_run.append(row)
        ev = np.array([e for e, _ in trace]); bf = np.array([b for _, b in trace])
        bsf = np.maximum.accumulate(bf) if len(bf) else bf
        for e, b in zip(ev, bsf):
            new_trace_rows.append([NEW_LABEL, n, seed, int(e), f"{b:.8f}"])
    print(f"  done {NEW_LABEL} n={n} ({SEEDS} seeds)", flush=True)

# ── 2. merge with the existing 4-variant STACKED data ────────────────────────
with open(os.path.join(STACKED, "per_run.csv")) as f:
    r = csv.DictReader(f); existing = list(r); pr_fields = r.fieldnames
with open(os.path.join(OUT, "per_run.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=pr_fields); w.writeheader()
    for row in existing:
        w.writerow(row)
    for row in new_per_run:
        w.writerow({k: row.get(k, "") for k in pr_fields})
shutil.copy(os.path.join(STACKED, "traces.csv"), os.path.join(OUT, "traces.csv"))
with open(os.path.join(OUT, "traces.csv"), "a", newline="") as f:
    w = csv.writer(f)
    for tr in new_trace_rows:
        w.writerow(tr)

# ── 3. rebuild convergence figure with the 5th line ──────────────────────────
sb.CHAIN = list(sb.CHAIN) + [(NEW_LABEL, NEW_OV)]
sb.COLORS = dict(sb.COLORS); sb.COLORS[NEW_LABEL] = NEW_COLOR
sb.N_SEEDS = 25
sb.OUT_DIR = OUT; sb.PLOTS_DIR = os.path.join(OUT, "plots")

traces, tmp = {}, {}
with open(os.path.join(OUT, "traces.csv")) as f:
    for row in csv.DictReader(f):
        key = (row["variant"], int(row["n_circles"]), int(row["seed"]))
        tmp.setdefault(key, []).append((float(row["evaluations"]), float(row["best_fitness"])))
for (v, n, _s), pts in tmp.items():
    pts.sort()
    ev = np.array([p[0] for p in pts]); bsf = np.array([p[1] for p in pts])
    traces.setdefault((v, n), []).append((ev, bsf))
sb.plot_convergence(traces)

if SEEDS >= 10:                                  # don't ship a smoke figure
    shutil.copy(os.path.join(OUT, "plots", "convergence_stacked_improvements.png"),
                os.path.join(OVERLEAF, "convergence_stacked_5var_finalpolish_100k.png"))
    print("copied figure -> overleaf-STACKED/convergence_stacked_5var_finalpolish_100k.png")

# ── 4. does final-polish+archive help? (step-wise Mann-Whitney) ──────────────
allrows = list(csv.DictReader(open(os.path.join(OUT, "per_run.csv"))))
def col(t, n):
    return np.array([float(r["final_gap"]) for r in allrows
                     if r["treatment"] == t and int(r["n_circles"]) == n])
print(f"\n=== {NEW_LABEL}  vs  references (effect>0 => new variant better) ===")
for ref in ["+clip", "+clip+polish", "+clip+polish+archive"]:
    for n in NS:
        a, b = col(ref, n), col(NEW_LABEL, n)
        if len(a) == 0 or len(b) == 0:
            continue
        d = float(np.median(a) - np.median(b))
        p = mannwhitneyu(b, a, alternative="two-sided").pvalue
        a12 = S.a12(b, a)
        v = "NEW better" if d > 0 and p < .05 else ("NEW worse" if d < 0 and p < .05 else "ns")
        print(f"  vs {ref:22s} n={n:<3} {np.median(a):.4f} -> {np.median(b):.4f}  d={d:+.4f}  A12={a12:.2f}  p={p:.2e}  {v}")
    print()
print("DONE")
