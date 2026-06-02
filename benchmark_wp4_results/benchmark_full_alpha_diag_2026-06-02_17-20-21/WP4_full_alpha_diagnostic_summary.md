# WP4 full variance alpha diagnostic

Ran treatments: full_baseline, full_recomb_coordinate, full_recomb_circle_pair, full_recomb_coordinate_alpha, full_recomb_circle_pair_alpha

## Pilot / grid settings

n values: [7, 10], seeds: 1, evals per run: 20000

## Median final_gap by treatment and n

| treatment | n | median_final_gap | IQR |
|---|---:|---:|---:|
| full_baseline | 7 | 0.30734225 | 0.0 |
| full_baseline | 10 | 0.17025774 | 0.0 |
| full_recomb_coordinate | 7 | 0.39861492 | 0.0 |
| full_recomb_coordinate | 10 | 0.52701193 | 0.0 |
| full_recomb_circle_pair | 7 | 0.51702807 | 0.0 |
| full_recomb_circle_pair | 10 | 0.55745904 | 0.0 |
| full_recomb_coordinate_alpha | 7 | 0.51702807 | 0.0 |
| full_recomb_coordinate_alpha | 10 | 0.53349743 | 0.0 |
| full_recomb_circle_pair_alpha | 7 | 0.51702807 | 0.0 |
| full_recomb_circle_pair_alpha | 10 | 0.56280686 | 0.0 |

## Effects vs full_baseline

| treatment | n | median_effect (baseline - treatment) |
|---|---:|---:|
| full_baseline | 7 | 0.0 |
| full_baseline | 10 | 0.0 |
| full_recomb_coordinate | 7 | -0.09127267 |
| full_recomb_coordinate | 10 | -0.35675419 |
| full_recomb_circle_pair | 7 | -0.20968581999999997 |
| full_recomb_circle_pair | 10 | -0.3872013 |
| full_recomb_coordinate_alpha | 7 | -0.20968581999999997 |
| full_recomb_coordinate_alpha | 10 | -0.36323969000000006 |
| full_recomb_circle_pair_alpha | 7 | -0.20968581999999997 |
| full_recomb_circle_pair_alpha | 10 | -0.39254912000000003 |

## Comparisons (see comparisons.csv)

Comparisons were computed using Mann-Whitney U where SciPy is available, and Vargha-Delaney A12. Significance: *** p<0.001, ** p<0.01, * p<0.05, ns otherwise.

## Interpretation

- This is exploratory: alpha recombination is not the canonical ES rule.
- Pilot suggests recombination treatments are worse than the FULL_VARIANCE baseline for these settings, but the pilot uses few seeds and is inconclusive.
- CiaS permutation symmetry may make naive indexed recombination disruptive.

## Limitations

- Small diagnostic only; n values = [7, 10]; seeds configurable via WP4_SEEDS; evals = 20000.
