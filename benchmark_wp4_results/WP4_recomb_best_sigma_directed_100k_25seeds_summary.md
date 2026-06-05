# WP4 — Directed recombination benchmark (best-sigma strategies, final)

This report summarises the final directed recombination benchmark rerun. The canonical results used are from:

benchmark_wp4_results/benchmark_recomb_best_sigma_directed_100k_25seeds_2026-06-05_12-04-37/

Why we reran
- The previous directed run produced a partial output (250/450 rows) with intermittent worker failures. We reran the full grid from scratch to obtain a complete, clean artifact set and to ensure reliable comparisons.

Experimental grid
- n and strategies:
  - n = 7: `SINGLE_VARIANCE` and `MULTIPLE_VARIANCE`
  - n = 10: `SINGLE_VARIANCE` and `MULTIPLE_VARIANCE`
  - n = 15: `MULTIPLE_VARIANCE` only
  - n = 20: `MULTIPLE_VARIANCE` only
- seeds: 25 (0..24)
- evaluations per run: 100000
- treatments:
  - `baseline` (no recombination)
  - `coordinate` (coordinate-wise discrete recombination)
  - `circle_pair` (inherit each `(x_i,y_i)` pair from one parent)
- Notes on strategy parameters: `SINGLE_VARIANCE` and `MULTIPLE_VARIANCE` do not include alpha/rotation parameters, so no alpha-aware recombination was used.

Method (brief)
- Coordinate-wise recombination: each scalar coordinate is chosen independently from one of the two parents.
- Circle-pair recombination: each full circle centre `(x_i,y_i)` is inherited as a pair from one parent.
- Sigma (step-size) parameters are averaged arithmetically between parents.
- No parent alignment (Hungarian matching) or label-correction was performed.

Median final_gap (from final per-run results)

| n | strategy | treatment | median_final_gap |
|---:|:---------|:----------|------------------:|
| 7 | MULTIPLE_VARIANCE | baseline | 0.0491411 |
| 7 | MULTIPLE_VARIANCE | circle_pair | 0.479215 |
| 7 | MULTIPLE_VARIANCE | coordinate | 0.46054 |
| 7 | SINGLE_VARIANCE | baseline | 0.0522277 |
| 7 | SINGLE_VARIANCE | circle_pair | 0.461352 |
| 7 | SINGLE_VARIANCE | coordinate | 0.437715 |
| 10 | MULTIPLE_VARIANCE | baseline | 0.136092 |
| 10 | MULTIPLE_VARIANCE | circle_pair | 0.536086 |
| 10 | MULTIPLE_VARIANCE | coordinate | 0.522065 |
| 10 | SINGLE_VARIANCE | baseline | 0.133756 |
| 10 | SINGLE_VARIANCE | circle_pair | 0.530005 |
| 10 | SINGLE_VARIANCE | coordinate | 0.546204 |
| 15 | MULTIPLE_VARIANCE | baseline | 0.290562 |
| 15 | MULTIPLE_VARIANCE | circle_pair | 0.620374 |
| 15 | MULTIPLE_VARIANCE | coordinate | 0.607986 |
| 20 | MULTIPLE_VARIANCE | baseline | 0.387672 |
| 20 | MULTIPLE_VARIANCE | circle_pair | 0.65923 |
| 20 | MULTIPLE_VARIANCE | coordinate | 0.668251 |

Effects vs baseline (median difference: baseline_median - treatment_median)

(Values taken from `comparisons.csv` produced in the final folder)

| treatment | n | metric | base_median | arm_median | effect | p_value | A12 | significance |
|:----------|---:|:-------|-----------:|----------:|-------:|--------:|----:|:-------------|
| circle_pair | 7  | final_gap | 0.051832 | 0.471097 | -0.419265 | 7.07e-18 | 0.0   | *** |
| circle_pair | 10 | final_gap | 0.135841 | 0.531469 | -0.395629 | 2.42e-15 | 0.04  | *** |
| circle_pair | 15 | final_gap | 0.290562 | 0.620374 | -0.329812 | 1.42e-09 | 0.0   | *** |
| circle_pair | 20 | final_gap | 0.387672 | 0.659230 | -0.271558 | 2.29e-09 | 0.006 | *** |
| coordinate   | 7  | final_gap | 0.051832 | 0.451508 | -0.399675 | 7.07e-18 | 0.0   | *** |
| coordinate   | 10 | final_gap | 0.135841 | 0.531503 | -0.395662 | 1.24e-15 | 0.036 | *** |
| coordinate   | 15 | final_gap | 0.290562 | 0.607986 | -0.317424 | 1.42e-09 | 0.0   | *** |
| coordinate   | 20 | final_gap | 0.387672 | 0.668251 | -0.280579 | 1.60e-09 | 0.002 | *** |

Notes on comparisons
- For `n` values where both `SINGLE_VARIANCE` and `MULTIPLE_VARIANCE` were present (n=7,10), `comparisons.csv` reports `n_base=50` and the `base_median` is the combined median across both baseline strategies (50 runs). For n=15 and n=20 the baseline is the single strategy present (25 runs).
- Therefore comparisons in `comparisons.csv` are against the combined baseline per `n` when both strategies exist, not separately per-strategy.

Conclusions
- Both `coordinate` and `circle_pair` recombination treatments significantly worsened `final_gap` compared with the baseline (no recombination) across the directed grid (p << 0.001 for all reported comparisons).
- Recombination is not recommended for the selected SINGLE/MULTIPLE sigma strategies in this directed setting.
- Likely reason: CiaS has permutation symmetry (circle labels arbitrary); naive indexed recombination mixes non-corresponding circles between parents and disrupts structure.

Limitations
- This is a directed grid using previously-selected sigma winners and competitive strategies; results do not imply global generality.
- FULL_VARIANCE and alpha-aware recombination were not part of this run (see separate `full_alpha` diagnostic).
- No parent alignment (Hungarian matching) or label-correction was attempted; such methods might reduce recombination disruption.

Artifacts
- Canonical folder: benchmark_wp4_results/benchmark_recomb_best_sigma_directed_100k_25seeds_2026-06-05_12-04-37/
- per_run.csv and comparisons.csv included in the folder; summary and plots also present.

