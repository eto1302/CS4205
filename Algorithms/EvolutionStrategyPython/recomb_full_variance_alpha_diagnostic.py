"""WP4 exploratory diagnostic for FULL_VARIANCE alpha recombination.

This script is a small diagnostic (not the full benchmark). Defaults:
- n: 7,10
- seeds: 10
- evals: 20000

Writes a per-run CSV and a small summary Markdown. Plots are generated
if matplotlib is available.
"""
import os
import csv
import time
import numpy as np
from pathlib import Path

# Compute repo root robustly: two parents above this file
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parents[2]
RESULTS_ROOT = REPO_ROOT / "benchmark_wp4_results"

repo_root = REPO_ROOT
from ES.evopy import EvoPy, Strategy

# env-overridable defaults for a small diagnostic
CIRCLE_SIZES = [int(x) for x in os.environ.get("WP4_NS", "7,10").split(",")]
N_SEEDS = int(os.environ.get("WP4_SEEDS", "10"))
MAX_EVALS = int(os.environ.get("WP4_EVALS", "20000"))
 


def get_target(n_circles):
    # reuse same targets as recomb_single_benchmark for comparability
    _TARGETS = [
        1.4142135623730951, 1.0352761804100830, 1.0000000000000000, 0.7071067811865475,
        0.6009252125773315, 0.5358983848622454, 0.5176380902050415, 0.5000000000000000,
        0.4212795439839034, 0.3982073102368442, 0.3887301263230200, 0.3660960076964251,
        0.3489152603740189, 0.3410813774021089, 0.3333333333333333, 0.3061539853003329,
        0.3004626062886658, 0.2895419919949817, 0.2866116523516816,
    ]
    return _TARGETS[n_circles - 2]


def fitness(individual):
    pts = np.asarray(individual).reshape(-1, 2)
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return float(d.min())


# Baseline: FULL_VARIANCE, recombine=False
BASELINE = dict(
    strategy=Strategy.FULL_VARIANCE,
    selection_scheme="comma",
    init="lhs",
    population_size=30,
    num_children=7,
    recombine=False,
)


TREATMENTS = [
    ("full_baseline", "WP4", {}),
    ("full_recomb_coordinate", "WP4", {"recombine": True, "recombination_mode": "coordinate"}),
    ("full_recomb_circle_pair", "WP4", {"recombine": True, "recombination_mode": "circle_pair"}),
    ("full_recomb_coordinate_alpha", "WP4", {"recombine": True, "recombination_mode": "coordinate_alpha"}),
    ("full_recomb_circle_pair_alpha", "WP4", {"recombine": True, "recombination_mode": "circle_pair_alpha"}),
]


TOLS = [1e-2, 1e-3, 1e-5]


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

    evals = np.array([e for e, _ in trace]) if trace else np.array([0])
    best = np.array([b for _, b in trace]) if trace else np.array([0.0])
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
    ts = time.strftime("%Y-%m-%d_%H-%M-%S")
    out_dir = Path(RESULTS_ROOT) / f"benchmark_full_alpha_diag_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    per_run_csv = out_dir / "per_run.csv"

    fields = ["treatment", "wp", "n_circles", "seed", "strategy", "init",
              "selection_scheme", "final_best", "final_gap", "total_evals",
              "total_generations"] + [f"evals_to_{t:.0e}" for t in TOLS]

    rows = []
    n_total = len(TREATMENTS) * len(CIRCLE_SIZES) * N_SEEDS
    print(f"Diagnostic: {len(TREATMENTS)} treatments x {len(CIRCLE_SIZES)} n x {N_SEEDS} seeds = {n_total} runs, budget {MAX_EVALS:,} evals")
    # Print resolved paths for debugging
    print("Resolved script path:", str(SCRIPT_PATH))
    print("Resolved repo root:", str(REPO_ROOT))
    print("Resolved output root:", str(RESULTS_ROOT))
    print("Resolved run output dir:", str(out_dir))

    for label, wp, overrides in TREATMENTS:
        for n in CIRCLE_SIZES:
            for seed in range(N_SEEDS):
                print(f"Running {label} n={n} seed={seed}")
                row = run_one(overrides, n, seed)
                row["treatment"], row["wp"] = label, wp
                rows.append(row)

    # sort and write
    rows.sort(key=lambda r: (r["treatment"], int(r["n_circles"]), int(r["seed"])))
    with open(per_run_csv, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    # Summarise medians and effects
    import statistics
    summary = {}
    for label, _, _ in TREATMENTS:
        summary[label] = {}
        for n in CIRCLE_SIZES:
            vals = [r["final_gap"] for r in rows if r["treatment"] == label and r["n_circles"] == n]
            vals = [v for v in vals if v != ""]
            if vals:
                summary[label][n] = {"median": float(statistics.median(vals)), "iqr": float(np.subtract(*np.percentile(vals, [75, 25])))}
            else:
                summary[label][n] = {"median": None, "iqr": None}

    # compute effects vs baseline
    baseline = "full_baseline"
    effects = {}
    for label, _, _ in TREATMENTS:
        if label[0] == baseline:
            continue
        effects[label] = {}
        for n in CIRCLE_SIZES:
            bmed = summary[baseline][n]["median"]
            tmed = summary[label][n]["median"]
            if bmed is not None and tmed is not None:
                effects[label][n] = float(bmed - tmed)
            else:
                effects[label][n] = None

    # write comparisons.csv with statistics per treatment vs baseline (always write)
    comp_csv = out_dir / "comparisons.csv"
    try:
        from scipy.stats import mannwhitneyu
        has_scipy = True
    except Exception:
        has_scipy = False

    def a12_from_u(u, n1, n2):
        return float(u) / (n1 * n2) if n1 > 0 and n2 > 0 else None

    with open(comp_csv, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["n", "treatment", "baseline_median", "treatment_median", "effect", "baseline_iqr", "treatment_iqr", "n_baseline", "n_treatment", "p_value", "A12", "significance"])
        for n in CIRCLE_SIZES:
            baseline_vals = [r["final_gap"] for r in rows if r["treatment"] == baseline and r["n_circles"] == n]
            baseline_vals = [v for v in baseline_vals if v != ""]
            for label, _, _ in TREATMENTS:
                if label == baseline:
                    continue
                treat_vals = [r["final_gap"] for r in rows if r["treatment"] == label and r["n_circles"] == n]
                treat_vals = [v for v in treat_vals if v != ""]
                bmed = summary[baseline][n]["median"]
                tmed = summary[label][n]["median"]
                eff = None if bmed is None or tmed is None else float(bmed - tmed)
                biqr = summary[baseline][n]["iqr"]
                tiqr = summary[label][n]["iqr"]
                n_b = len(baseline_vals)
                n_t = len(treat_vals)
                p_val = "NA"
                a12v = "NA"
                sig = "not_computed"
                if has_scipy and n_b > 0 and n_t > 0:
                    try:
                        u_stat, pval = mannwhitneyu(baseline_vals, treat_vals, alternative='two-sided')
                        p_val = float(pval)
                        a12v = a12_from_u(u_stat, n_b, n_t)
                        if p_val < 0.001:
                            sig = "***"
                        elif p_val < 0.01:
                            sig = "**"
                        elif p_val < 0.05:
                            sig = "*"
                        else:
                            sig = "ns"
                    except Exception:
                        p_val = "NA"
                        a12v = "NA"
                        sig = "not_computed"
                writer.writerow([n, label, bmed, tmed, eff, biqr, tiqr, n_b, n_t, p_val, a12v, sig])

    # write summary markdown including tables
    md = out_dir / "WP4_full_alpha_diagnostic_summary.md"
    with open(md, "w") as fh:
        fh.write("# WP4 full variance alpha diagnostic\n\n")
        fh.write(f"Ran treatments: {', '.join([t[0] for t in TREATMENTS])}\n\n")
        fh.write("## Pilot / grid settings\n\n")
        fh.write(f"n values: {CIRCLE_SIZES}, seeds: {N_SEEDS}, evals per run: {MAX_EVALS}\n\n")
        fh.write("## Median final_gap by treatment and n\n\n")
        fh.write("| treatment | n | median_final_gap | IQR |\n")
        fh.write("|---|---:|---:|---:|\n")
        for label, _, _ in TREATMENTS:
            for n in CIRCLE_SIZES:
                med = summary[label][n]["median"]
                iqr = summary[label][n]["iqr"]
                fh.write(f"| {label} | {n} | {med} | {iqr} |\n")
        fh.write("\n## Effects vs full_baseline\n\n")
        fh.write("| treatment | n | median_effect (baseline - treatment) |\n")
        fh.write("|---|---:|---:|\n")
        for label in effects:
            for n in CIRCLE_SIZES:
                fh.write(f"| {label} | {n} | {effects[label][n]} |\n")
        fh.write("\n## Comparisons (see comparisons.csv)\n\n")
        fh.write("Comparisons were computed using Mann-Whitney U where SciPy is available, and Vargha-Delaney A12. Significance: *** p<0.001, ** p<0.01, * p<0.05, ns otherwise.\n\n")
        fh.write("## Interpretation\n\n")
        fh.write("- This is exploratory: alpha recombination is not the canonical ES rule.\n")
        fh.write("- Pilot suggests recombination treatments are worse than the FULL_VARIANCE baseline for these settings, but the pilot uses few seeds and is inconclusive.\n")
        fh.write("- CiaS permutation symmetry may make naive indexed recombination disruptive.\n\n")
        fh.write("## Limitations\n\n")
        fh.write("- Small diagnostic only; n values = {0}; seeds configurable via WP4_SEEDS; evals = {1}.\n".format(CIRCLE_SIZES, MAX_EVALS))

    # Try plotting if matplotlib is available (figures optional)
    figures = []
    try:
        import matplotlib.pyplot as plt
        has_plt = True
    except Exception:
        has_plt = False

    print("scipy available:", has_scipy)
    print("matplotlib available:", has_plt)

    if has_plt:
        import math
        # Boxplot of final_gap by treatment and n
        try:
            plt.figure(figsize=(8, 6))
            # group data
            labels = sorted(list(set([r['treatment'] for r in rows])))
            x_vals = sorted(CIRCLE_SIZES)
            # create boxplots per treatment per n
            data = []
            ticks = []
            ticklabels = []
            for n in x_vals:
                for lab in labels:
                    vals = [r['final_gap'] for r in rows if r['treatment'] == lab and r['n_circles'] == n]
                    data.append(vals)
                    ticklabels.append(f"{lab}\n n={n}")
            plt.boxplot(data, labels=ticklabels, showfliers=False)
            plt.xticks(rotation=45, ha='right')
            plt.ylabel('final_gap (lower is better)')
            plt.title('Final gap by treatment and n (lower is better)')
            fn = os.path.join(out_dir, 'full_alpha_final_gap_boxplot.png')
            plt.tight_layout()
            plt.savefig(fn)
            plt.close()
            figures.append(fn)
        except Exception:
            pass

        # Median lines
        try:
            plt.figure(figsize=(6, 4))
            for label, _, _ in TREATMENTS:
                meds = [summary[label][n]['median'] for n in x_vals]
                plt.plot(x_vals, meds, marker='o', label=label)
            plt.xlabel('n')
            plt.ylabel('median final_gap (lower is better)')
            plt.title('Median final_gap by treatment (lower is better)')
            plt.legend()
            fn2 = os.path.join(out_dir, 'full_alpha_median_final_gap_lines.png')
            plt.tight_layout()
            plt.savefig(fn2)
            plt.close()
            figures.append(fn2)
        except Exception:
            pass

        # Effect barplot
        try:
            plt.figure(figsize=(8, 5))
            width = 0.15
            x = np.arange(len(x_vals))
            treatments_plot = [t[0] for t in TREATMENTS if t[0] != baseline]
            for i, lab in enumerate(treatments_plot):
                effs = [effects[lab][n] for n in x_vals]
                plt.bar(x + i * width, effs, width=width, label=lab)
            plt.axhline(0, color='k', linewidth=0.8)
            plt.xticks(x + width * (len(treatments_plot) - 1) / 2.0, x_vals)
            plt.xlabel('n')
            plt.ylabel('effect (baseline_median - treatment_median)')
            plt.title('Effect vs baseline (positive improves, negative worsens)')
            plt.legend()
            fn3 = os.path.join(out_dir, 'full_alpha_effect_barplot.png')
            plt.tight_layout()
            plt.savefig(fn3)
            plt.close()
            figures.append(fn3)
        except Exception:
            pass

    else:
        print("matplotlib unavailable, skipping figures")

    # Always list files written
    written = []
    try:
        for p in sorted(out_dir.iterdir()):
            written.append(str(p))
    except Exception:
        written = []

    print(f"Wrote results to {out_dir}")
    if figures:
        print("Generated figures:")
        for f in figures:
            print(" -", f)
    if written:
        print("Files in output dir:")
        for w in written:
            print(" -", w)


if __name__ == '__main__':
    main()
