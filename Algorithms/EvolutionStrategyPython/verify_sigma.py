"""Verify single vs multiple variance at large n, on BOTH repair regimes.

Agata's OFAT shows MULTIPLE_VARIANCE beats SINGLE at n=15/20 — but on the
random-repair baseline. Question for the stacked chain (which uses clip): does
multiple still beat single once clip repair is in? Random repair is destructive
at large n; clip is not — multiple/clip may be redundant (same failure mode).

Runs 4 configs x {n} x 25 seeds x 100k, prints Mann-Whitney multiple-vs-single
for each repair regime. No L-BFGS, so it's cheap.

Run: uv run --with numpy --with scipy verify_sigma.py
"""
import os
import numpy as np
from scipy.stats import mannwhitneyu

from ES.evopy import EvoPy, Strategy
import ofat_benchmark as ofat
import stats as S

NS       = [int(x) for x in os.environ.get("VS_NS", "10,15,20").split(",")]
N_SEEDS  = int(os.environ.get("VS_SEEDS", "25"))
MAX_EVAL = int(os.environ.get("VS_EVALS", "100000"))

CONFIGS = [
    ("single_random",   Strategy.SINGLE_VARIANCE,   "random"),
    ("multiple_random", Strategy.MULTIPLE_VARIANCE, "random"),
    ("single_clip",     Strategy.SINGLE_VARIANCE,   "clip"),
    ("multiple_clip",   Strategy.MULTIPLE_VARIANCE, "clip"),
]


def run(strategy, repair, n, seed):
    target = ofat.get_target(n)
    kw = dict(ofat.BASELINE); kw.pop("strategy", None)
    g = EvoPy(ofat.fitness, n * 2, maximize=True, bounds=(0, 1),
              generations=100000, max_evaluations=MAX_EVAL, random_seed=seed,
              strategy=strategy, repair=repair,
              **{k: v for k, v in kw.items() if k != "strategy"}).run()
    return (target - float(ofat.fitness(g))) / target


def main():
    data = {}   # (label, n) -> list of gaps
    for label, strat, rep in CONFIGS:
        for n in NS:
            gaps = [run(strat, rep, n, s) for s in range(N_SEEDS)]
            data[(label, n)] = np.array(gaps)
            print(f"  done {label:16s} n={n:<3d} median_gap={np.median(gaps):.4f}", flush=True)

    print("\n=== multiple vs single, per repair regime (effect>0 => multiple better) ===")
    print(f"{'repair':8s} {'n':>3} {'single':>8} {'multiple':>9} {'effect':>8} {'A12':>5} {'p':>9}  verdict")
    verdicts = {}
    for rep in ("random", "clip"):
        for n in NS:
            s = data[(f"single_{rep}", n)]
            m = data[(f"multiple_{rep}", n)]
            eff = float(np.median(s) - np.median(m))
            p = mannwhitneyu(m, s, alternative="two-sided").pvalue
            a12 = S.a12(m, s)
            v = "MULTIPLE" if eff > 0 and p < .05 else ("single" if eff < 0 and p < .05 else "tie(ns)")
            verdicts[(rep, n)] = (p, v)
            print(f"{rep:8s} {n:>3} {np.median(s):8.4f} {np.median(m):9.4f} {eff:8.4f} {a12:5.2f} {p:9.2e}  {v}")
        print()

    _save_csv(data)
    _plot(data, verdicts)


def _save_csv(data):
    out = os.path.join(REPO_ROOT, "results", "sigma_verify")
    os.makedirs(out, exist_ok=True)
    import csv
    with open(os.path.join(out, "per_run.csv"), "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["config", "n_circles", "seed", "final_gap"])
        for (label, n), gaps in data.items():
            for seed, g in enumerate(gaps):
                w.writerow([label, n, seed, round(float(g), 8)])
    print(f"saved {out}/per_run.csv")


def _star(p):
    return "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 5e-2 else "ns"


def _plot(data, verdicts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    out = os.path.join(REPO_ROOT, "results", "sigma_verify")
    os.makedirs(out, exist_ok=True)
    COL = {"single": "#2ca02c", "multiple": "#1f77b4"}
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), sharey=True)
    for ax, rep, title in [(axes[0], "random", "RANDOM repair (Agata's OFAT baseline B)"),
                           (axes[1], "clip", "CLIP repair (the stacked algorithm)")]:
        for strat in ("single", "multiple"):
            meds = [np.median(data[(f"{strat}_{rep}", n)]) for n in NS]
            q1 = [np.percentile(data[(f"{strat}_{rep}", n)], 25) for n in NS]
            q3 = [np.percentile(data[(f"{strat}_{rep}", n)], 75) for n in NS]
            ax.plot(NS, meds, "o-", color=COL[strat], lw=2, ms=7, label=f"{strat}-σ")
            ax.fill_between(NS, q1, q3, color=COL[strat], alpha=0.15)
        for n in NS:
            p, _ = verdicts[(rep, n)]
            top = max(np.percentile(data[(f"single_{rep}", n)], 75),
                      np.percentile(data[(f"multiple_{rep}", n)], 75))
            ax.annotate(_star(p), (n, top), textcoords="offset points", xytext=(0, 6),
                        ha="center", fontsize=11, fontweight="bold")
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("Problem size  n"); ax.set_xticks(NS)
        ax.grid(True, alpha=0.3); ax.legend(fontsize=10)
    axes[0].set_ylabel("Median final gap to optimum  (lower = better)\nband = IQR over seeds")
    fig.suptitle("σ-strategy winner FLIPS with the repair method  "
                 f"({N_SEEDS} seeds, {MAX_EVAL:,} evals)\n"
                 "multiple-σ only helps because it dodges destructive random repair; clip removes that need",
                 fontsize=12)
    fig.tight_layout()
    p = os.path.join(out, "sigma_single_vs_multiple_by_repair.png")
    fig.savefig(p, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"saved {p}")


if __name__ == "__main__":
    main()
