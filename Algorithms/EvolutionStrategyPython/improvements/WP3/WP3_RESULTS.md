# WP3 — Results: Constraint Handling Repair Modes

**Run config:** 10 seeds × n ∈ {7, 10, 15, 20} × 100,000 evals × FULL_VARIANCE,
(μ,λ), LHS init. Two arms tested: `B+repair_clip` and `B+repair_reflect`, each
compared against the same frozen baseline using Mann–Whitney U + A12.

> **Note on seed count:** the full sweep specifies 25 seeds. These results use 10.
> The directional findings are clear but confidence intervals are wider than they
> would be with 25 seeds. The conclusions below should be treated as strong
> indicators, not final verdicts.

---

## Summary

| Arm | n | A12 | p | Significant? | Verdict |
|---|---|---|---|---|---|
| `B+repair_clip` | 7 | 0.87 | 0.006 | ✓ ** | Real improvement |
| `B+repair_clip` | 10 | 0.98 | 0.0003 | ✓ *** | Real improvement |
| `B+repair_clip` | 15 | 1.00 | 0.0002 | ✓ *** | Real improvement |
| `B+repair_clip` | 20 | 1.00 | 0.0002 | ✓ *** | Real improvement |
| `B+repair_reflect` | 7 | 0.78 | 0.038 | ✓ * | Real improvement |
| `B+repair_reflect` | 10 | 0.92 | 0.002 | ✓ ** | Real improvement |
| `B+repair_reflect` | 15 | 0.74 | 0.076 | ✗ ns | No significant improvement |
| `B+repair_reflect` | 20 | 0.43 | 0.623 | ✗ ns | No improvement (slightly worse) |

**Clip passes the WP1 significance rule (p < 0.05 and A12 clearly above 0.5) at
every problem size.** Reflect passes on small n but fails on large n.

---

## Detailed results

### Median `final_gap` (lower is better)

`final_gap` = (optimum − best\_fitness) / optimum. A value of 0 means the run
reached the known optimum exactly.

| n | baseline | clip | reflect |
|---|---|---|---|
| 7 | 0.2096 | **0.0277** | 0.0432 |
| 10 | 0.1934 | **0.0593** | 0.0691 |
| 15 | 0.6226 | **0.1804** | 0.5729 |
| 20 | 0.6644 | **0.2178** | 0.6750 |

Clip reduces the median gap by **78–71%** on small n and by **71–67%** on large n
compared to the baseline. The improvement grows with problem size: at n=15 and
n=20, clip's A12 is 1.0, meaning clip won in 100% of pairwise comparisons against
the baseline — not a single baseline run outperformed a clip run.

Reflect matches clip at small n (within a few percentage points) but collapses at
large n, where it performs no better than the baseline. At n=20 its A12 is 0.43 —
below the coin-flip threshold — meaning the baseline was slightly more likely to
win.

### Success rate (runs that reached within 1% of the optimum)

| n | baseline | clip | reflect |
|---|---|---|---|
| 7 | 0% | **40%** | 10% |
| 10 | 0% | 0% | 10% |
| 15 | 0% | 0% | 0% |
| 20 | 0% | 0% | 0% |

CiaS is hard: with 100k evals no method reliably solves n ≥ 10. At n=7, clip
reaches within 1% of the optimum in 4 out of 10 runs; the baseline reaches it in
none. The `evals_to_*` columns are mostly empty for all treatments (insufficient
runs hit the tolerance thresholds) — consistent with the WP1 note that on hard n,
`final_gap` is the discriminating metric and `evals_to_*` saturates.

---

## Why clip beats reflect here

This is the result that diverges most from the theoretical prediction. Clip was
expected to be a moderate improvement; reflect was expected to be the best because
it preserves full step magnitude. The data shows the opposite pattern at large n.
Two likely explanations:

**Boundary attraction helps CiaS.** Clip accumulates probability density at the
boundary by design — alleles that overshoot get pushed to exactly `0` or `1`.
For CiaS this is not a bug but a feature: optimal packings place circle centres
*on* the boundary. The bias accelerates convergence to the right region of the
search space.

**Reflect destabilises σ on large problems.** At n=15 and n=20, σ is large during
exploration. A coordinate that overshoots the wall by a large δ gets reflected
back into the interior — far from the boundary — instead of landing on it. The
resulting child is worse than a clipped child, and the σ self-adaptation feedback
penalises the step. Over many generations this produces the high variance visible
in the std column (reflect std at n=15 = 0.215 vs clip std = 0.029). Reflect is
theoretically better when σ is small and steps are close to the boundary; at large
n with a high-dimensional rotation matrix generating large steps, this assumption
breaks down.

---

## Conclusion

**Clip is the recommended repair mode for CiaS.** It is significant at every
tested problem size, effect sizes are large to perfect (A12 0.87–1.0), and it is
the simpler of the two changes (one line: `np.clip`). The improvement is not
marginal — at n=15 and n=20 where the baseline is essentially failing (median gap
~0.66), clip reduces the gap to ~0.18–0.22, a qualitative difference in solution
quality.

**Reflect is a partial improvement** — valid on small n but unreliable on large n.
It could be revisited with an adaptive σ cap or a step-size limit near the
boundary, but as implemented it should not be used as the default repair for large
CiaS instances.

**Neither mode reaches the optimum reliably on n ≥ 10** within the 100k eval
budget. The constraint repair improvement is real and large, but CiaS at large n
requires additional improvements (step-size tuning, local search, better
initialisation) to close the remaining gap.

---

## Forest plot

![forest plot](forest_final_gap_WP3.png)

Filled dots = significant (p < 0.05). Hollow dots = not significant.
Horizontal position = improvement in median `final_gap` vs baseline (right = better).
Whiskers = bootstrap 95% CI.

The plot confirms the table: all four clip rows are filled and shifted well to the
right; reflect rows are filled at n=7 and n=10 but hollow at n=15 and n=20, with
the n=20 dot sitting on the wrong side of zero.


## Proposed runs

1.  Increase the eval budget for large n

Right now the ES is not converging for 100k evals. We want to figure out if its not gonna converge or just slower. A larger budget can tell if reflect strategy eventually catches up to clip.

2. Run n=7 and n=10 only, with 25 seeds

These are the two sizes where reflect looked promising. Getting to 25 seeds here firms up those confidence intervals and gives a statistically complete result for the small-n cases, which is useful if we want to claim reflect is valid in a limited regime.