# WP4 Summary (medium results)

Generated from:
- benchmark_wp4_results/benchmark_sigma_medium_2026-05-30_14-10-41 (sigma ablation)
- benchmark_wp4_results/benchmark_recomb_single_medium_2026-05-30_14-17-34 (recombination on SINGLE_VARIANCE)

---

## 1. Sigma-strategy ablation

| n_circles | SINGLE_VARIANCE median final_gap | MULTIPLE_VARIANCE median final_gap | FULL_VARIANCE median final_gap | Best strategy |
|----------:|----------------------------------:|-----------------------------------:|-------------------------------:|:-------------:|
| 7         | 0.045851                         | 0.127711                          | 0.265906                       | SINGLE_VARIANCE |
| 10        | 0.079377                         | 0.221321                          | 0.475185                       | SINGLE_VARIANCE |

(Values from `comparisons_sigma.csv` in the sigma medium folder.)

---

## 2. Recombination on best σ-strategy: SINGLE_VARIANCE

Effect is defined as: baseline median final_gap minus arm median final_gap. Negative effects mean the arm performed worse than the baseline.

| treatment                      | n_circles | base_median | arm_median | effect     | A12  | p_value  | marker |
|:------------------------------|----------:|------------:|-----------:|-----------:|:----:|:--------:|:------:|
| sigma_single_recomb_coord     | 7         | 0.045851    | 0.462203  | -0.416351  | 0.00 | 1.83e-04 | ***    |
| sigma_single_recomb_coord     | 10        | 0.079377    | 0.506463  | -0.427086  | 0.00 | 1.83e-04 | ***    |
| sigma_single_recomb_pair      | 7         | 0.045851    | 0.457281  | -0.411429  | 0.00 | 1.83e-04 | ***    |
| sigma_single_recomb_pair      | 10        | 0.079377    | 0.522755  | -0.443378  | 0.00 | 1.83e-04 | ***    |

(Values from `comparisons_recomb_single.csv` in the recomb-single medium folder.)

---

## 3. Interpretation


SINGLE_VARIANCE was the best-performing σ-strategy among the tested medium settings (n=7 and n=10), so recombination experiments were re-run using `SINGLE_VARIANCE` as the baseline. Both coordinate-wise and circle-pair recombination markedly and significantly worsened `final_gap` relative to the SINGLE baseline (highly significant at p≈1.8e-4). Circle-pair recombination did not rescue performance. Negative effect values indicate the arm's median final_gap is larger (worse) than the baseline. The current recombination operators are not recommended as final improvements, but they provide useful evidence that naive recombination is disruptive for CiaS. A likely reason is that CiaS has permutation symmetry: circle index `i` is not semantically aligned across parents, so mixing coordinates without an explicit matching/alignment step scrambles solutions. Recombination should therefore align or match components (or operate on permutation-invariant representations) before mixing.

---

Files saved in this workspace:
- `benchmark_wp4_results/benchmark_sigma_medium_2026-05-30_14-10-41`
- `benchmark_wp4_results/benchmark_recomb_single_medium_2026-05-30_14-17-34`

