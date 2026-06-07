---
title: "How to read our statistics — Mann–Whitney, A12, bootstrap CI"
subtitle: "Plain-English explainer for the team, tied to our actual results"
status: "Leo's local working notes. 2026-06-03. For the team (we all have to present this to Arthur)."
---

# Reading our p-values (without a stats degree)

Arthur asked for **"p-values almost everywhere."** Every forest dot in the WP guides comes from
one little pipeline (`stats.py`). This page explains, in plain language, **exactly what those
three numbers mean** so we can present them confidently. It's the short, results-focused version
of the fuller [`../statistics-guide/`](../../groupwork-notes/statistics-guide/statistics-guide.md) (which builds
p-values from scratch with figures).

There are only **three numbers** per comparison. That's it:

| number | one-line meaning | "good" looks like |
|--------|------------------|-------------------|
| **p-value** (Mann–Whitney U) | "could this difference be pure luck?" | **small** (< 0.05) = probably real |
| **A12** (Vargha–Delaney) | "how *often* does the improvement win?" | **far from 0.5** (→1.0 better, →0.0 worse) |
| **95% CI** (bootstrap) | "how big is the gap, with error bars?" | **doesn't cross 0** |

---

## 0. The setup: what we're even comparing

For each treatment (say "clip repair") at each problem size n, we have **two lists of numbers**:

- **baseline**: the final gap-to-optimum from 25 (or 10) independent runs of plain B.
- **arm**: the final gap from 25 runs of B with *one thing changed* (clip).

Lower gap = better. The question is always: **is the arm's list meaningfully lower than the
baseline's list?** All three statistics are different lenses on that one question.

---

## 1. Why NOT a normal t-test (the thing everyone half-remembers)

A t-test compares **means** and assumes each list is a tidy bell curve. Our gaps are **not** a
bell curve — they're skewed and often **bimodal**: most seeds converge, a few get stuck near a
bad local optimum. Here's our *actual* baseline at n=10 (25 seeds):

![why not a t-test](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/mw_hist.png)

22 seeds land around 7–20%; **3 unlucky seeds get stuck at ~54%**. Those 3 outliers drag the
**mean up to 17.9%** while the **median is 13.4%**. A t-test would compare the lying means; it
could also be fooled by the fat tail into "significance" that's really just one stuck seed.

**The fix:** use a test based on **ranks**, not means. Ranks don't care that the stuck seed is at
54% vs 80% — only that it's *worse*. That test is the Mann–Whitney U.

---

## 2. Mann–Whitney U — "does the arm tend to beat the baseline?"

Pool both lists, **sort everyone by rank** (best to worst), and ask: do the arm's runs sit
**systematically higher up** (better) than the baseline's? Concretely, U counts — over all
arm-vs-baseline pairs — **how often the arm's run beats the baseline's run**.

- If arm and baseline are interchangeable, the arm wins about **half** the pairings → big p-value.
- If the arm almost always wins (or always loses), that's very unlikely by chance → tiny p-value.

The **p-value** is "if there were truly *no* difference, what's the probability of seeing a split
this lopsided (in *either* direction)?" We use **two-sided** (`alternative="two-sided"`) because an
"improvement" could secretly make things *worse* — we want to catch both. In `stats.py`:

```python
p = mannwhitneyu(arm, base, alternative="two-sided").pvalue
```

Significance markers in our tables: `*** = p<0.001`, `** = p<0.01`, `* = p<0.05`, `ns = not
significant (p≥0.05)`.

> ⚠️ p only tells you **"is it real?"**, not **"is it big?"** With enough seeds a *tiny*
> improvement can be `***`. That's why we also report A12 and the CI.

---

## 3. A12 (Vargha–Delaney) — "how often does it win?" (effect size)

A12 = **the probability that a random arm-run beats a random baseline-run** (with ties counting
half). It's literally U rescaled to 0–1:

- **A12 = 0.5** → coin flip, no difference.
- **A12 → 1.0** → the arm beats the baseline almost every time (big win).
- **A12 → 0.0** → the arm *loses* almost every time (big regression).

In our `stats.py`, lower gap = better, so it's computed as `P(arm < base) + 0.5·P(tie)`. Rough
rule of thumb: 0.56 small, 0.64 medium, 0.71+ large.

This is the number that makes a result **intuitive**: "A12 = 0.96" means *clip beat random repair
in 96% of head-to-head seed pairings.* No statistics background needed to feel that.

---

## 4. Bootstrap 95% CI — "how big is the gap, with error bars?"

p and A12 say *whether* and *how often*; the CI says *how much*. We resample the runs **2000×**
with replacement and look at the spread of `median(baseline) − median(arm)`. The 2.5%–97.5% range
is the **95% confidence interval** on the improvement.

- **CI entirely above 0** → confidently an improvement.
- **CI straddling 0** → could go either way (consistent with `ns`).

On the forest plots: the **dot** is the median improvement, the **whisker** is this CI, the
**vertical line at 0** is "no effect." Filled dot = significant, hollow = ns.

---

## 5. Reading two REAL rows from our results

These are copy-pasted from our `comparisons.csv` files — practice reading them:

**A clear WIN — WP3 clip repair at n=15** (`data/wp3_comparisons_single.csv`):

```
treatment      n  base_median  arm_median  effect   ci_lo  ci_hi  a12   p        marker
B-repair_clip  15 0.572142     0.150019    0.422123 0.0951 0.4749 0.96  5.83e-04 ***
```

Read it as: "Random repair leaves a **57.2%** gap at n=15; clip cuts it to **15.0%**. That's a
**42-point** improvement (CI 9.5–47.5%, doesn't touch 0), clip **wins 96% of pairings** (A12=0.96),
and there's a **0.06% chance** this is luck (`***`)." → a big, real, justified win.

**A clean NULL — WP1 removing LHS at n=10** (`data/wp1_comparisons.csv`):

```
treatment  n   base_median  arm_median  effect    ci_lo    ci_hi   a12    p       marker
B-no_lhs   10  0.133756     0.164283    -0.030528 -0.0606  0.0062  0.379  1.46e-01 ns
```

Read it as: "Swapping LHS for plain uniform init barely moves the median (13.4% → 16.4%), the CI
**crosses 0**, A12 is **near 0.5**, p = **0.15** → **not significant.**" → LHS makes no measurable
difference. An honest negative, reported as-is (per Arthur's rules).

---

## 6. The one caveat that bites us: seed count

p-values and CIs are only **comparable at the same sample size**. With **10 seeds** the CIs are
wide and the speed metric (`evals_to_1e-02`) often reads "insufficient data" — which is exactly
what bit Martin. The fix isn't statistical, it's just **run more seeds**: we should lock **25 seeds**
for every final comparison. (See [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) item 4.)

> **One-sentence summary for the slide:** *We use the rank-based Mann–Whitney U test (not a
> t-test, because our gap distributions are skewed/bimodal), report the Vargha–Delaney A12 effect
> size (how often the change wins) and a bootstrap 95% CI (how big the change is) — so every
> claimed improvement is shown to be real, large, and not a fluke.*
