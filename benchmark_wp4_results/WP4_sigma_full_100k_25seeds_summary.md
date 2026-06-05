**Sigma Ablation — Full Budget (100k evals, 25 seeds)**

- **Runs:** 3 treatments (`baseline`=FULL_VARIANCE, `SINGLE_VARIANCE`, `MULTIPLE_VARIANCE`) × 4 n values (7,10,15,20) × 25 seeds = 300 runs; per-run budget = 100000 evals.
- **Note:** `baseline` is the FULL_VARIANCE treatment (so comparisons report improvements relative to FULL_VARIANCE, not an external control).
- **Artifacts:** [per_run.csv](benchmark_wp4_results/benchmark_sigma_alln_medium_2026-06-04_20-13-50/per_run.csv#L1) — detailed run rows; [comparisons.csv](benchmark_wp4_results/benchmark_sigma_alln_medium_2026-06-04_20-13-50/comparisons.csv#L1) — statistical comparisons vs `baseline`.

**Key comparison highlights (relative to `baseline` = FULL_VARIANCE):**

- **MULTIPLE_VARIANCE**
  - n=15: base_median=0.623621 → arm_median=0.290562, effect=0.333059, A12=1.00, p=1.42e-09 (***). Strong improvement.
  - n=20: base_median=0.660551 → arm_median=0.387672, effect=0.272879, A12=1.00, p=1.42e-09 (***). Strong improvement.
  - n=10: base_median=0.437623 → arm_median=0.136092, effect=0.30153, A12=0.712, p=1.04e-02 (*).
  - n=7:  base_median=0.060516 → arm_median=0.049141, effect=0.011375, A12=0.694, p=1.89e-02 (*).

- **SINGLE_VARIANCE**
  - n=10: base_median=0.437623 → arm_median=0.133756, effect=0.303867, A12=0.694, p=1.89e-02 (*).
  - n=7:  base_median=0.060516 → arm_median=0.052228, effect=0.008288, A12=0.704, p=1.37e-02 (*).
  - n=15 and n=20: not significant (ns) under these settings.

**Interpretation:**
- Both `SINGLE_VARIANCE` and `MULTIPLE_VARIANCE` show significant wins at small n (7,10). For larger problems (n=15,20) `MULTIPLE_VARIANCE` provides a large, highly significant improvement over `FULL_VARIANCE`, while `SINGLE_VARIANCE` does not.

**Next actions (options):**
- Produce publication-ready figures (boxplots / median gap lines) from the per-run data. The run folder already contains PNGs; I can regenerate higher-resolution plots if you prefer.
- Run additional checks (effect size bootstrap, or per-seed traces for outliers).
- Archive and tag results or prepare a short report section for the WP4 summary.

If you want figures or a deeper numeric table (CI, A12 per comparison) included in the markdown, tell me which format you prefer and I will add them.
