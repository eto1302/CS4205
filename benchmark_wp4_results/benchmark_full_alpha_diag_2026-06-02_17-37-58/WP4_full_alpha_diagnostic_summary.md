# WP4 full variance alpha diagnostic

Ran treatments: full_baseline, full_recomb_coordinate, full_recomb_circle_pair, full_recomb_coordinate_alpha, full_recomb_circle_pair_alpha

## Pilot / grid settings

n values: [7, 10], seeds: 10, evals per run: 20000

## Median final_gap by treatment and n

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

## Effects vs full_baseline

| treatment | n | median_effect (baseline - treatment) |
|---|---:|---:|
| full_baseline | 7 | 0.0 |
| full_baseline | 10 | 0.0 |
| full_recomb_coordinate | 7 | -0.18017545499999998 |
| full_recomb_coordinate | 10 | -0.06529070999999997 |
| full_recomb_circle_pair | 7 | -0.18538859999999996 |
| full_recomb_circle_pair | 10 | -0.0793587349999999 |
| full_recomb_coordinate_alpha | 7 | -0.20339924999999998 |
| full_recomb_coordinate_alpha | 10 | -0.06816000999999994 |
| full_recomb_circle_pair_alpha | 7 | -0.20105480999999997 |
| full_recomb_circle_pair_alpha | 10 | -0.063779315 |

## Comparisons (see comparisons.csv)

Comparisons were computed using Mann-Whitney U where SciPy is available, and Vargha-Delaney A12. Significance: *** p<0.001, ** p<0.01, * p<0.05, ns otherwise.

## Interpretation

- This is exploratory: alpha recombination is not the canonical ES rule.
- Pilot suggests recombination treatments are worse than the FULL_VARIANCE baseline for these settings, but the pilot uses few seeds and is inconclusive.
- CiaS permutation symmetry may make naive indexed recombination disruptive.

## Limitations

- Small diagnostic only; n values = [7, 10]; seeds configurable via WP4_SEEDS; evals = 20000.
