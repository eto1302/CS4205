# WP3 Results Analysis: Constraint Handling Strategies
**Single Variance ES — Circles-in-a-Square**

Details: Single Variance Strategy, 25 seeds, 100k evals, n = 7,10,15,20, mu = 30, lambda = 7
Constraint handling strategies: Random, Clipping, Reflection

---

## Overall Picture

Both clipping and reflection are decisively better than the random repair baseline — but **only at higher problem dimensions (n=15, n=20)**. At n=7, neither repair method consistently beats the baseline in a statistically significant way.

---

## Result-by-Result Breakdown

### n=7 (small problem)

| Treatment | Median final\_gap | A12 | Significance |
|---|---|---|---|
| Baseline | 0.0522 | — | — |
| Clip | 0.0286 | 0.758 | ** |
| Reflect | 0.0418 | 0.627 | ns |

Clip is the only method that reaches significance here (p=0.00178, A12=0.758), but the absolute gap improvement is small (~0.024). Reflection falls short of significance (p=0.125). At n=7, the search space is small enough that random repair "gets away with it" — out-of-bounds events are less destructive.

### n=10

| Treatment | Median final\_gap | A12 | Significance |
|---|---|---|---|
| Baseline | 0.1338 | — | — |
| Clip | 0.0628 | 0.867 | *** |
| Reflect | 0.0850 | 0.851 | *** |

Both methods are highly significant (p<0.0001). Clip edges out reflect on median (0.063 vs 0.085), and has a slightly larger A12, suggesting it produces better solutions more consistently at this dimension.

### n=15 (biggest win)

| Treatment | Median final\_gap | A12 | Significance |
|---|---|---|---|
| Baseline | 0.6186 | — | — |
| Clip | 0.1476 | 0.976 | *** |
| Reflect | 0.1715 | 0.962 | *** |

This is the standout result. The baseline essentially stagnates (median gap ~0.62, very close to "no progress"), while both repair strategies reduce the gap by ~75%. The A12 values near 1.0 mean that across almost all 25 seed pairs, the repair method produced a better result — essentially stochastic dominance. The ladder plot shows this clearly: going from baseline → clip → reflect brings the median final\_gap from +0.62 all the way to −0.28 (i.e., surpassing the target).

### n=20

| Treatment | Median final\_gap | A12 | Significance |
|---|---|---|---|
| Baseline | 0.6416 | — | — |
| Clip | 0.1754 | 1.000 | *** |
| Reflect | 0.2265 | 0.946 | *** |

Clip achieves A12=1.0 — it beat the baseline in **every single one of the 25 seed comparisons**, a perfect effect. Reflect is close behind (A12=0.946). Absolute improvements are ~0.47 and ~0.42 respectively. However, note that neither method actually closes the gap to zero at n=20 — the problem remains hard.

---

## Clip vs. Reflect: Head-to-Head

Clipping consistently outperforms reflection across all problem sizes:

| n | Clip median | Reflect median | Clip advantage |
|---|---|---|---|
| 7 | 0.0286 | 0.0418 | ~0.013 |
| 10 | 0.0628 | 0.0850 | ~0.022 |
| 15 | 0.1476 | 0.1715 | ~0.024 |
| 20 | 0.1754 | 0.2265 | ~0.051 |

The gap between them widens with dimensionality. A likely reason: **reflection introduces a deterministic bias** in the direction of mutation — when a candidate is out of bounds, reflecting it back creates a child that is "bounced" toward the interior, which can interfere with the search direction the step size has adapted to. Clipping simply truncates and keeps the step size adaptation unaffected, which may be more compatible with Single Variance's global σ update.

---

## Key Takeaways

1. **Random repair is harmful at scale.** At n=15 and n=20, it causes near-complete failure (median gaps of 0.62–0.64 against a target around 0.35–0.42), likely because with 30–40 dimensions, random repair constantly disrupts the search by teleporting individuals within the bounds rather than respecting the gradient of the fitness landscape.

2. **Clip is the better repair strategy** for Single Variance ES across all tested n values, particularly at higher dimensions.

3. **The no-LHS initialization (WP1 treatment) had no significant effect** at any n — the initialization method doesn't matter much compared to the repair strategy.

4. **The ladder plot confirms additivity** (at least for n=15): applying clip on top of baseline, then reflect on top of clip, shows clean cumulative improvement. This is a good sign for the robustness of the findings.

5. **The `evals_to_1e-02` metric was largely unusable** — very few runs hit that threshold from the baseline, which is itself evidence that random repair severely impedes convergence speed.

---

## Caveat

The comparison between clip and reflect is not directly tested statistically here — each is only tested against the baseline. To formally claim clip is significantly better than reflect, a direct paired statistical test between those two arms would be needed.
