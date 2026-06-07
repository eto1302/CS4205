"""Regenerate the stacked-improvement figures from saved CSVs (no EA re-run).

Reads per_run.csv + traces.csv from results/STACKED and results/STACKED_200k and
re-renders the convergence + final-gap-vs-n plots with the corrected labels
(relative gap) and plain-decimal y ticks.

Run: uv run --with numpy --with scipy --with matplotlib replot_stacked.py
"""
import os
import csv

import numpy as np

import stacked_benchmark as sb


def load_traces(d):
    tmp = {}
    with open(os.path.join(d, "traces.csv")) as fh:
        for row in csv.DictReader(fh):
            key = (row["variant"], int(row["n_circles"]), int(row["seed"]))
            tmp.setdefault(key, []).append((float(row["evaluations"]), float(row["best_fitness"])))
    out = {}
    for (variant, n, _seed), pts in tmp.items():
        pts.sort()
        ev = np.array([p[0] for p in pts]); bsf = np.array([p[1] for p in pts])
        out.setdefault((variant, n), []).append((ev, bsf))
    return out


def load_per_run(d):
    rows = list(csv.DictReader(open(os.path.join(d, "per_run.csv"))))
    for r in rows:
        r["final_gap"] = float(r["final_gap"]); r["n_circles"] = int(r["n_circles"])
    return rows


for tag, evals in [("", 100000), ("_200k", 200000)]:
    d = os.path.join(sb.REPO_ROOT, "results", "STACKED" + tag)
    if not os.path.exists(d):
        continue
    sb.MAX_EVALS = evals
    sb.N_SEEDS = 25
    sb.OUT_DIR = d
    sb.PLOTS_DIR = os.path.join(d, "plots")
    sb.plot_convergence(load_traces(d))
    sb.plot_final_gap_vs_n(load_per_run(d))
    print(f"replotted {d}")
