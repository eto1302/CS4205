# WP4 Artifact Inventory and Results Summary

## 1. Scope of WP4

- Implemented a recombination hook for the project ES implementation:
  - textbook-style recombination on the genotype `x` (discrete mixing),
    intermediary recombination on the strategy `sigma` (no `alpha` recombination).
- Implemented a CiaS-aware circle-pair recombination operator (circle-pair
  crossover that is aware of circle-in-space structure).
- Implemented a sigma-strategy ablation: `SINGLE_VARIANCE` vs `MULTIPLE_VARIANCE`
  vs `FULL_VARIANCE` and benchmark drivers to compare them.
- Final experiment plan: benchmark recombination arms using the best-performing
  sigma strategy from the ablation (do not run recombination until confirmed).

## 2. Code files created or changed

| File | Type | Purpose |
|---|---|---|
| `ES/evopy/recombination.py` | Modified / New | Recombination helper functions. Implements coordinate-wise and circle-pair recombination and accepts an RNG for reproducibility. (New/modified to add CiaS-aware modes.) |
| `ES/evopy/evopy.py` | Modified | Adds `recombine` and `recombination_mode` options, calls the recombination helper before mutation, and passes the seeded RNG through for reproducibility. |
| `ofat_benchmark.py` | Modified | OFAT wrapper used to run individual treatments; integrated WP4 treatment definitions so existing pipelines can run the new arms. |
| `sigma_ablation.py` | New | Sequential sigma-strategy ablation runner. Generates `results/per_run.csv` for treatments across `n_circles` and seeds. |
| `sigma_ablation_parallel.py` | New | Parallelized version of `sigma_ablation.py` using `ProcessPoolExecutor`, with progress/ETA printing. |
| `recomb_single_benchmark.py` | New | Sequential recombination-on-SINGLE runner (baseline SINGLE + recombination arms). |
| `recomb_single_benchmark_parallel.py` | New | Parallel version of the recombination runner with progress/ETA printing. |
| `scripts/make_wp4_artifacts.py` | New | Helper to assemble final WP4 artifacts (archive, filtered CSVs, summary helpers). |
| `scripts/make_sigma_artifacts.py` | New | Filters `results/per_run.csv` and `results/comparisons.csv` to `per_run_sigma.csv` and `comparisons_sigma.csv`. |
| `scripts/make_recomb_single_artifacts.py` | New | Filters and assembles artifacts for recombination-on-SINGLE experiments. |
| `scripts/save_sigma_artifacts.py` | New | Copies `results` and plots into a timestamped `benchmark_wp4_results` folder and appends the medium all-n table to `WP4_summary_full.md`. |
| `tests/test_recombination_repro.py` | New | Unit test to assert recombination + EvoPy RNG usage is deterministic across repeated runs (reproducibility test). |

Notes: for each file above the repo contains either the original sequential runner (used as the canonical run logic) and a parallel wrapper that imports the sequential `run_one` logic. Parallel wrappers were written non-destructively so existing sequential outputs are preserved.

## 3. Benchmark result folders

| Folder | Purpose | Main files |
|---|---|---|
| `benchmark_wp4_results/benchmark_sigma_medium_2026-05-30_14-10-41` | Medium-budget sigma ablation (example run) | `per_run.csv`, `comparisons.csv`, plots `plots_wp1/*.png` |
| `benchmark_wp4_results/benchmark_recomb_single_medium_2026-05-30_14-17-34` | Medium recombination-on-SINGLE run | `per_run.csv`, `comparisons.csv`, recombination plots |
| `benchmark_wp4_results/benchmark_sigma_alln_medium_2026-06-01_11-57-29` | All-n medium sigma ablation (runs for n=7,10,15,20; seeds=10; evals=20k) | `per_run.csv`, `comparisons.csv`, `per_run_sigma.csv`, `comparisons_sigma.csv`, `plots_wp1/*.png` |
| `benchmark_wp4_results/WP4_summary.md` | Short human-facing summary | Markdown summary (short) |
| `benchmark_wp4_results/WP4_summary_full.md` | Full summary and appended tables | Markdown with full tables and interpretations |

Diagnostic / older folders (non-final):

- Diagnostic / older folders, if present, are timestamped folders under `benchmark_wp4_results/` from exploratory runs. They are considered non-final unless explicitly referenced above.

## 4. Sigma-strategy ablation results

All-n medium results (20k evals per run, 10 seeds):

| n_circles | SINGLE_VARIANCE median final_gap | MULTIPLE_VARIANCE median final_gap | FULL_VARIANCE median final_gap | Best strategy |
|---:|---:|---:|---:|:---:|
| 7 | 0.045851 | 0.127711 | 0.265906 | SINGLE_VARIANCE |
| 10 | 0.079377 | 0.221321 | 0.475185 | SINGLE_VARIANCE |
| 15 | 0.180430 | 0.499452 | 0.618002 | SINGLE_VARIANCE |
| 20 | 0.249201 | 0.631384 | 0.668338 | SINGLE_VARIANCE |

Notes:
- `final_gap` is a lower-is-better metric (closer to zero = better objective attainment).
- `SINGLE_VARIANCE` is the best-performing sigma strategy for all tested `n` values in this medium-budget experiment.
- No crossover point (where another sigma strategy overtakes SINGLE) was observed within these budgets.
- `MULTIPLE_VARIANCE` is intermediate; it significantly improves over `FULL_VARIANCE` at `n=15` in this medium run, but remains worse than `SINGLE_VARIANCE`.

## 5. Recombination results on best sigma strategy

Medium recombination-on-`SINGLE_VARIANCE` results (selected rows):

| treatment | n_circles | base_median | arm_median | effect | A12 | p_value | marker |
|---|---:|---:|---:|---:|---:|---:|:---:|
| sigma_single_recomb_coord | 7 | 0.045851 | 0.462203 | -0.416351 | 0.00 | 1.83e-04 | *** |
| sigma_single_recomb_coord | 10 | 0.079377 | 0.506463 | -0.427086 | 0.00 | 1.83e-04 | *** |
| sigma_single_recomb_pair | 7 | 0.045851 | 0.457281 | -0.411429 | 0.00 | 1.83e-04 | *** |
| sigma_single_recomb_pair | 10 | 0.079377 | 0.522755 | -0.443378 | 0.00 | 1.83e-04 | *** |

Notes:
- `effect` is computed as `baseline_median - arm_median`; negative values indicate that the arm performed worse than the baseline.
- Both coordinate-wise and circle-pair recombination strongly and significantly worsened performance for `n=7` and `n=10` under the medium-budget runs (A12 ≈ 0, p ≪ 0.001, marked `***`).
- Full all-n recombination (n=15 and n=20) has not been run yet; those experiments are listed as optional future work.

## 6. Runtime and feasibility

- A sequential timing run for the `n=20` sample (12 runs: 3 seeds × 4 strategies) with 20k evals took about `2100.32` seconds (~35.0 minutes).
- A naive sequential full 100k × 25 seeds × all `n` grid was estimated to require multiple days, so it was avoided.
-- The parallel all-n medium sigma ablation (160 runs, seeds=10, n in {7,10,15,20}, evals=20k) completed in roughly `3885.9` seconds (~64.8 minutes) using 4 workers.

- The 160 rows include the baseline/FULL reference plus the three sigma-strategy arms.

## 7. Current conclusions

- `SINGLE_VARIANCE` is the best sigma strategy across `n={7,10,15,20}` under these medium-budget experiments.
- Recombination (both coordinate-wise and circle-pair) was tested on the `SINGLE_VARIANCE` baseline and significantly hurt performance for the tested small/medium cases (`n=7,10`).
- Circle-pair recombination did not rescue performance; the likely cause is that the CiaS representation exhibits permutation symmetry (circle indices are not aligned between parents), so naive recombination mixes mismatched circles.
- A robust recombination operator for CiaS would require alignment / matching or a permutation-invariant representation before mixing.

## 8. Remaining possible work (do not run without explicit approval)

- Optional: run recombination-on-`SINGLE_VARIANCE` for `n=15,20` (medium budget) to complete medium-size coverage.
- Optional: create boxplots and per-run diagnostics (plots over seeds) for deeper analysis.
- Optional: run full 25-seed 100k sweep only if adequate compute resources and time are available.
- Optional: implement improved CiaS-aware recombination (matching/alignment) and re-run recombination experiments.



## Generated WP4 plots

The following plots were generated from existing CSV artifacts and saved under `benchmark_wp4_results/wp4_plots/`:

- `sigma_final_gap_boxplot.png`: Boxplots of `final_gap` by `n_circles` for the three sigma strategies (SINGLE, MULTIPLE, FULL).
- `sigma_median_final_gap_lines.png`: Median `final_gap` vs `n_circles` lines for each sigma strategy (lower is better).
- `recomb_effect_barplot.png`: Bar plot showing `effect` (baseline median - arm median) per `n_circles` for the two recombination arms; negative values indicate the arm performed worse than the SINGLE baseline.
- `recomb_final_gap_boxplot.png`: Boxplots of `final_gap` by `n_circles` comparing `SINGLE_VARIANCE`, `sigma_single_recomb_coord`, and `sigma_single_recomb_pair`.


---

Path to this file:

`benchmark_wp4_results/WP4_artifact_inventory.md`
