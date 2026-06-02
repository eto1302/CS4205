# WP4 — Full-variance alpha recombination diagnostic (final 10-seed results)

This file summarises the small diagnostic comparing FULL_VARIANCE with several recombination treatments (including alpha-aware variants). Only the final 10-seed results in `benchmark_wp4_results/benchmark_full_alpha_diag_2026-06-02_17-37-58/` are used.

## 1. Experimental setup

- `n` values: 7, 10
- seeds: 10
- evaluations per run: 20,000
- strategy: `FULL_VARIANCE`
- treatments:
  - `full_baseline`
  - `full_recomb_coordinate`
  - `full_recomb_circle_pair`
  - `full_recomb_coordinate_alpha`
  - `full_recomb_circle_pair_alpha`

The diagnostic runs the same EvoPy settings used in earlier WP4 diagnostics (population/children/init/selection kept consistent with the baseline). Comparisons use per-run median final_gap and Mann–Whitney U tests where SciPy is available; A12 (Vargha–Delaney) is reported when computed from the U statistic.

## 2. Method tried

This diagnostic tested whether recombination can improve the `FULL_VARIANCE` strategy, especially when the full-variance strategy parameters include both step-size parameters and rotation/inclination parameters.

In the project implementation, an individual has:

- object variables / genotype:

$x = (x_0, y_0, x_1, y_1, \ldots, x_{n-1}, y_{n-1})$

- strategy parameters for `FULL_VARIANCE`:

$(\sigma_1, \ldots, \sigma_d, \alpha_1, \ldots, \alpha_{d(d-1)/2})$

where \(d = 2n\) is the number of object variables. The \(\sigma\) values control mutation step sizes, while the \(\alpha\) values represent rotation/inclination parameters for correlated mutation.

The baseline treatment, `full_baseline`, used `FULL_VARIANCE` without recombination. The recombination treatments first selected two parents and then constructed a recombined temporary parent before mutation.

Two object-variable recombination schemes were tested:

1. **Coordinate-wise recombination**  
   Each scalar coordinate is inherited discretely from one of the two parents. For example, each entry of

$(x_0, y_0, x_1, y_1, \ldots)$

is independently chosen from either parent.

2. **Circle-pair recombination**  
   Instead of mixing scalar coordinates independently, each full circle centre \((x_i, y_i)\) is inherited as a pair from one parent. This was intended to be more CiaS-aware because it preserves each circle centre as a geometric unit.

For strategy parameters, two variants were tested:

1. **Standard ES-style strategy recombination**  
   The \(\sigma\) parameters are recombined by intermediary/arithmetic recombination:

$\sigma_{\text{child}} = \frac{\sigma^{(1)} + \sigma^{(2)}}{2}$


The \(\alpha\) rotation parameters are inherited unchanged from one parent. This corresponds to the base rule used earlier in WP4: recombine object variables and step sizes, but do not introduce a special covariance/orientation recombination operator.

2. **Exploratory alpha-aware recombination**  
   In the exploratory `*_alpha` modes, the \(\sigma\) parameters are still averaged, but the \(\alpha\) rotation parameters are recombined using a circular mean:

$\alpha_{\text{child}} = \operatorname{atan2} \left( \sin(\alpha^{(1)}) + \sin(\alpha^{(2)}), \cos(\alpha^{(1)}) + \cos(\alpha^{(2)}) \right)$

This avoids naive arithmetic averaging of angles near the wrap-around boundary, for example near \(-\pi\) and \(+\pi\).

The resulting five treatments were:

| treatment | object-variable recombination | sigma handling | alpha handling |
|---|---|---|---|
| `full_baseline` | none | normal `FULL_VARIANCE` mutation/adaptation | normal `FULL_VARIANCE` mutation/adaptation |
| `full_recomb_coordinate` | coordinate-wise discrete recombination | arithmetic average | inherit from one parent |
| `full_recomb_circle_pair` | whole \((x_i,y_i)\) pair recombination | arithmetic average | inherit from one parent |
| `full_recomb_coordinate_alpha` | coordinate-wise discrete recombination | arithmetic average | circular mean |
| `full_recomb_circle_pair_alpha` | whole \((x_i,y_i)\) pair recombination | arithmetic average | circular mean |

The alpha-aware variants are treated as an exploratory extension, not as the canonical textbook ES recombination rule. The purpose was to test the teammate suggestion that `FULL_VARIANCE` might benefit from recombining its richer strategy-parameter structure, especially the rotation parameters.

## 3. Median final_gap (final 10-seed results)

| treatment | n | median_final_gap | IQR |
|---|---:|---:|---:|
| full_baseline | 7 | 0.265905555 | 0.3539882775 |
| full_baseline | 10 | 0.47518530000000003 | 0.37083013749999993 |
| full_recomb_coordinate | 7 | 0.44608101 | 0.07390606500000002 |
| full_recomb_coordinate | 10 | 0.54047601 | 0.04731937249999996 |
| full_recomb_circle_pair | 7 | 0.451294155 | 0.04484170000000004 |
| full_recomb_circle_pair | 10 | 0.5545440349999999 | 0.017153337500000032 |
| full_recomb_coordinate_alpha | 7 | 0.469304805 | 0.06568556000000003 |
| full_recomb_coordinate_alpha | 10 | 0.54334531 | 0.040700664999999914 |
| full_recomb_circle_pair_alpha | 7 | 0.466960365 | 0.05591025500000002 |
| full_recomb_circle_pair_alpha | 10 | 0.538964615 | 0.03815743249999992 |

## 4. Effects vs baseline (baseline_median - treatment_median)

Positive effect = improvement (treatment better than baseline). Negative = worse.

| n | treatment | baseline_median | treatment_median | effect | p_value | A12 | significance |
|---:|---|---:|---:|---:|---:|---:|---:|
| 7 | full_recomb_coordinate | 0.265905555 | 0.44608101 | -0.180175455 | 0.0312090128 | 0.21 | * |
| 7 | full_recomb_circle_pair | 0.265905555 | 0.451294155 | -0.1853886 | 0.0072845570 | 0.14 | ** |
| 7 | full_recomb_coordinate_alpha | 0.265905555 | 0.469304805 | -0.20339925 | 0.0091084964 | 0.15 | ** |
| 7 | full_recomb_circle_pair_alpha | 0.265905555 | 0.466960365 | -0.20105481 | 0.0057953585 | 0.13 | ** |
| 10 | full_recomb_coordinate | 0.4751853 | 0.54047601 | -0.06529071 | 0.0756615721 | 0.26 | ns |
| 10 | full_recomb_circle_pair | 0.4751853 | 0.554544035 | -0.079358735 | 0.0889730117 | 0.27 | ns |
| 10 | full_recomb_coordinate_alpha | 0.4751853 | 0.54334531 | -0.06816001 | 0.0756615721 | 0.26 | ns |
| 10 | full_recomb_circle_pair_alpha | 0.4751853 | 0.538964615 | -0.063779315 | 0.0889730117 | 0.27 | ns |

## 5. Main conclusion

- All recombination treatments had worse median `final_gap` than the `FULL_VARIANCE` baseline in this diagnostic (10-seed results).
- Alpha-aware recombination (`*_alpha`) did not improve `FULL_VARIANCE`.
- At `n=7`, the worsening for all recombination treatments is statistically significant (Mann–Whitney U, p < 0.05 / p < 0.01 as reported).
- At `n=10`, effects are negative (worse) but not statistically significant in this diagnostic.

## 6. Interpretation

- This supports treating alpha recombination as an exploratory negative result rather than a recommended modification to the `FULL_VARIANCE` method.
- The result is consistent with earlier observations that recombination can be disruptive for the CiaS problem class.
- CiaS has permutation symmetry: circle labels are arbitrary, so naive indexed recombination can mix non-corresponding circles between parents and disrupt structure.
- Circle-pair recombination preserves `(x_i,y_i)` units, but does not guarantee correct parent alignment across individuals and so may still be disruptive.

## 7. Limitations

- Small diagnostic only (not the full benchmark): `n` in {7,10}
- seeds = 10
- evaluations per run = 20,000 (not 100k)
- Results are specific to the diagnostic settings and the implementation used here.

## 8. Figures (from final 10-seed run)

- `benchmark_full_alpha_diag_2026-06-02_17-37-58/full_alpha_final_gap_boxplot.png`
- `benchmark_full_alpha_diag_2026-06-02_17-37-58/full_alpha_median_final_gap_lines.png`
- `benchmark_full_alpha_diag_2026-06-02_17-37-58/full_alpha_effect_barplot.png`

## 9. Reproducibility and notes

- Script: `Algorithms/EvolutionStrategyPython/recomb_full_variance_alpha_diagnostic.py`
- The script now writes `per_run.csv`, `comparisons.csv`, a summary markdown, and generates figures when `matplotlib` is available. Statistical tests use `scipy.stats.mannwhitneyu` when SciPy is present; `comparisons.csv` is always written (p/A12 fields set to NA when not computed).

---
Generated from final results in `benchmark_wp4_results/benchmark_full_alpha_diag_2026-06-02_17-37-58/`.
