"""WP1 — statistics layer for the Architecture-B OFAT comparison.

Reads `results/per_run.csv`, and for every (treatment != baseline, n, metric)
compares the treatment against the SAME baseline with a two-sided Mann-Whitney U
test + the Vargha-Delaney A12 effect size. Writes `results/comparisons.csv`.

Design choices (see groupwork-notes/statistics-guide + comparison-architectures):
  * Mann-Whitney (rank-based) not t-test — final_gap over seeds is skewed,
    bounded at 0, and has outliers, so a t-test's normality assumption is unsafe.
  * A12 reported alongside every p (significance != magnitude).
  * Metrics: `final_gap` (fixed-budget) AND `evals_to_1e-2` (fixed-target/speed),
    so saturated cells (everyone converged) fall back to the metric that still
    has signal. A `note` column flags saturation / insufficient data.
  * Holm-Bonferroni multiple-comparison correction: NOT applied for now (parked).
  * success-rate via Fisher's exact: PARKED (stub below) — only needed when an
    improvement shows up as "converges more often" in the partial-convergence
    regime. The per_run.csv already stores what it needs (non-empty evals_to_*).

Run:  uv run --with scipy --with numpy stats.py
"""
import csv
import os

import numpy as np
from scipy.stats import mannwhitneyu

RESULTS_DIR     = "results"
PER_RUN_CSV     = os.path.join(RESULTS_DIR, "per_run.csv")
COMPARISONS_CSV = os.path.join(RESULTS_DIR, "comparisons.csv")
BASELINE_LABEL  = "baseline"
METRICS         = ["final_gap", "evals_to_1e-02"]  # quality, then speed (col names match ofat_benchmark's :.0e format)
MIN_VALID       = 5                                 # need >= this many runs per side
SATUR_FLOOR     = 1e-3                               # final_gap IQR below this == saturated


def a12(arm, base):
    """P(arm beats baseline) + 0.5 P(tie). Lower metric = better for both
    final_gap and evals_to_target, so 'arm beats base' == arm < base.
    0.5 = no effect, > 0.5 = arm better."""
    arm, base = np.asarray(arm, float), np.asarray(base, float)
    lt = sum((arm < b).sum() for b in base)
    eq = sum((arm == b).sum() for b in base)
    return (lt + 0.5 * eq) / (len(arm) * len(base))


def marker(p):
    return "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 5e-2 else "ns"


def boot_ci(base, arm, n_boot=2000, rng=None):
    """Bootstrap 95% CI of the effect (median(base) - median(arm)) — the forest
    plot's whisker. Resample each side with replacement, recompute the median
    difference, take the 2.5/97.5 percentiles."""
    rng = rng or np.random.default_rng(0)
    base, arm = np.asarray(base), np.asarray(arm)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        diffs[i] = (np.median(rng.choice(base, len(base))) -
                    np.median(rng.choice(arm, len(arm))))
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


# ── PARKED: success-rate comparison via Fisher's exact test ──────────────────
# Use ONLY when the improvement is "converges more often" (partial-convergence
# regime), not "ends closer"/"faster". 2x2 table = (reached vs not) x (base vs arm),
# reached = non-empty evals_to_<tol>. Uncomment + `from scipy.stats import
# fisher_exact` when a success-rate claim becomes part of the story.
#
# def success_rate_fisher(arm_reached, base_reached, n_arm, n_base):
#     table = [[arm_reached, n_arm - arm_reached],
#              [base_reached, n_base - base_reached]]
#     return fisher_exact(table, alternative="two-sided")  # (odds_ratio, p)


def load(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def column(rows, treatment, n, metric):
    """Numeric values of `metric` for one (treatment, n); drops blanks."""
    out = []
    for r in rows:
        if r["treatment"] == treatment and int(r["n_circles"]) == n and r[metric] != "":
            out.append(float(r[metric]))
    return np.array(out)


def main():
    rows = load(PER_RUN_CSV)
    treatments = [t for t in dict.fromkeys(r["treatment"] for r in rows) if t != BASELINE_LABEL]
    ns = sorted({int(r["n_circles"]) for r in rows})

    out_fields = ["treatment", "wp", "n_circles", "metric", "n_base", "n_arm",
                  "base_median", "arm_median", "effect", "ci_lo", "ci_hi",
                  "a12", "p_value", "marker", "note"]
    out_rows = []

    for treatment in treatments:
        wp = next(r["wp"] for r in rows if r["treatment"] == treatment)
        for n in ns:
            for metric in METRICS:
                base = column(rows, BASELINE_LABEL, n, metric)
                arm = column(rows, treatment, n, metric)

                note = ""
                if len(base) < MIN_VALID or len(arm) < MIN_VALID:
                    note = "insufficient data (few runs reached target)"
                    out_rows.append(dict(treatment=treatment, wp=wp, n_circles=n,
                                         metric=metric, n_base=len(base), n_arm=len(arm),
                                         base_median="", arm_median="", effect="",
                                         ci_lo="", ci_hi="",
                                         a12="", p_value="", marker="", note=note))
                    continue

                if metric == "final_gap":
                    iqr = np.percentile(np.concatenate([base, arm]), 75) - \
                          np.percentile(np.concatenate([base, arm]), 25)
                    if iqr < SATUR_FLOOR:
                        note = "saturated (use speed metric)"

                p = mannwhitneyu(arm, base, alternative="two-sided").pvalue
                effect = float(np.median(base) - np.median(arm))   # >0 = arm better
                lo, hi = boot_ci(base, arm)
                out_rows.append(dict(
                    treatment=treatment, wp=wp, n_circles=n, metric=metric,
                    n_base=len(base), n_arm=len(arm),
                    base_median=round(float(np.median(base)), 6),
                    arm_median=round(float(np.median(arm)), 6),
                    effect=round(effect, 6), ci_lo=round(lo, 6), ci_hi=round(hi, 6),
                    a12=round(a12(arm, base), 3),
                    p_value=f"{p:.2e}", marker=marker(p), note=note))

    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(COMPARISONS_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=out_fields)
        w.writeheader()
        w.writerows(out_rows)

    # readable console table
    print(f"{'treatment':12s} {'n':>3s} {'metric':14s} {'base':>9s} {'arm':>9s} "
          f"{'effect':>9s} {'A12':>5s} {'p':>9s} {'sig':>4s}  note")
    for r in out_rows:
        print(f"{r['treatment']:12s} {r['n_circles']:>3d} {r['metric']:14s} "
              f"{str(r['base_median']):>9s} {str(r['arm_median']):>9s} "
              f"{str(r['effect']):>9s} {str(r['a12']):>5s} {str(r['p_value']):>9s} "
              f"{r['marker']:>4s}  {r['note']}")
    print(f"\nWrote {COMPARISONS_CSV}")


if __name__ == "__main__":
    main()
