---
title: "Cross-WP Audit — Inconsistencies, Gaps & Pre-Deadline Actions"
subtitle: "A branch-by-branch sweep of every work package against the shared baseline"
status: "Leo's local working notes (groupwork-notes/, NOT the team repo). 2026-06-03. Deadline 2026-06-07."
---

# Audit — what's inconsistent across the branches

I swept every pushed branch (`git show origin/<branch>:…`, read-only) and cross-checked
each work package against the **shared OFAT baseline** on `main`. Headline:

> **The code is clean. The *experiments* are not yet apples-to-apples.**
> No logic bugs were found in anyone's new code. The problems are all
> **experiment-configuration drift** — different seed counts, eval budgets, σ-strategies
> and baselines — plus **WP5 sitting on a stale full-variance baseline** and missing the smooth
> surrogate its design needs. None of this is fatal; it's a half-day of re-running on one agreed
> configuration before the 06-07 hand-in.

The shared baseline (on `main`, commit `3fa67f7`):

> **B = single-variance · LHS init · (μ,λ) "comma" · random-resample repair · pop 30 · 7 children · 100 000 evals · 25 seeds.**

---

## 1. Config matrix — every divergence at a glance

| WP | Owner | Branch | σ-strategy of baseline | repair | seeds | eval budget | n values | p-values on shared pipeline? | pushed? |
|----|-------|--------|------------------------|--------|------:|------------:|----------|:---:|:---:|
| **WP1** | Leo | `bugfix/ta-handoff` → **merged to main** | **single** ✓ | random ✓ | **25** | **100k** | 7/10/15/20 | ✅ yes | ✅ |
| **WP2** | Ivan | `selection-elitism` | OFAT pins **FULL** 🔴; factorial ran single | n/a | **4** | 50k & **300k** | **n=5 only** | ❌ no (factorial, no MW) | ✅ |
| **WP3** | Cala | `constraint_handling-improvements` | OFAT pins **FULL** 🔴; committed runs per-strategy | random→clip/reflect | **10** | 100k ✓ | 7/10/15/20 | ✅ yes (per strategy) | ✅ |
| **WP4** | Agata | `recombination-agata` | OFAT pins **single** ✓; σ-ablation refs **FULL** | random | **10** | **~20k (early stop)** | 7/10/15/20 (σ), **7/10 only** (recomb) | ✅ yes (medium) | ✅ |
| **WP5** | Martin | `martin` | OFAT pins **FULL** 🔴 + **2 commits behind main** | random (full path) | **25** | **100k** | **7/10 only** | partial (his own) | ✅ (2026-06-03) |

"OFAT pins FULL" = the `BASELINE` dict in that branch's `ofat_benchmark.py` still says
`strategy=Strategy.FULL_VARIANCE` (the value before the 2026-06-01 switch). It does **not**
mean their *results* are full-variance — Ivan and Cala both ran single-variance arms
separately — but it means a naive `uv run ofat_benchmark.py` on their branch reproduces the
**wrong** reference.

---

## 2. Ranked inconsistency list

### 🔴 Critical (block a clean final story)

1. **WP5 ran on a stale FULL_VARIANCE baseline + 2 commits behind main** (branch `martin`,
   pushed 2026-06-03). His `ofat_benchmark.py:61` still pins `FULL_VARIANCE`, and the branch forks
   at `85115f0` — *before* the single-variance switch (`723639d`) and random-repair switch
   (`3fa67f7`). So his entire WP5 comparison sits on the wrong baseline. **→ rebase onto `main`,
   set `BASELINE=SINGLE_VARIANCE`, rerun.** (His polish code itself is sound — see point below.)

2. **The n=10 baseline anomaly — RESOLVED.** Martin's baseline n=10 = **0.4376** vs the
   single-variance **0.1338**: the cause is item 1 (his baseline is **full-variance**). At 100k,
   full-variance has ≈ n+n(n−1)/2 params to adapt — OK at n=7 (28 → 6%), far from converged at
   n=10 (55 → 44%). Not a polish artefact; the wrong baseline. ✅ explained. (See
   [WP5-martin.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP5-martin.md).)

3. **Stale `FULL_VARIANCE` baseline in THREE branches** (`selection-elitism`,
   `constraint_handling-improvements`, **`martin`**). Harmless to per-strategy committed results,
   but their OFAT entry point disagrees with `main`. **→ one-line fix** on each:
   `Strategy.FULL_VARIANCE → Strategy.SINGLE_VARIANCE`, then rerun.

### 🟡 Medium (must standardise before final numbers)

4. **Seed counts are all over the place: 25 (Leo, Martin) vs 10 (Cala, Agata) vs 4 (Ivan).**
   p-values and CIs are only comparable at a fixed seed count. **Decision needed: pick ONE.**
   Recommendation: **25** — single-variance is cheap now, and 10 seeds gave wide CIs / the
   "insufficient data" speed-metric problem Martin hit. (This is exactly the "10 vs 25" split
   Leo flagged.)

5. **Eval budgets differ: 100k (standard) vs ~20k (Agata's "medium" runs, *early-stopped*) vs
   50k/300k (Ivan).** Agata's "recombination is ~10× worse" and her σ-ablation are at **~20k**,
   not 100k. The *direction* is rock-solid (A12=0/1.0), but the *magnitudes* (and "full is
   worst") are partly a **budget artefact** — at 20k, full-variance (≈n+rotations strategy
   params) simply hasn't had time to adapt. **→ a 100k confirmation run would settle it.**

6. **Missing p-values on the shared pipeline for WP2 and WP4-OFAT.** Ivan's headline comes from
   a *factorial* (`benchmark_Cala.py`), not OFAT → no Mann–Whitney. Agata's OFAT scripts exist
   but no `per_run.csv` is committed. Arthur mandated "p-values almost everywhere" → **both need
   one pass through `ofat_benchmark.py → stats.py` on B.**

7. **n-range gaps.** Ivan's factorial is **n=5 only** (n=5 is solved by everything → near-zero
   signal); Martin and Agata-medium are **n=7/10 only**. The interesting regime is **n≥15**
   (where gaps and effects are large). Final runs should all cover **7/10/15/20**.

8. **Cala's "25 seeds break single-variance" — OPEN, not yet root-caused.** She reported the
   single-variance result changes/degrades when she bumps 10→25 seeds. The sweep found **no
   code-level seed bug** (no hardcoded seed list, no seed-count-dependent buffer). This is an
   *unexplained* report, not a confirmed bug — **needs a reproduce** (run her branch at 10 and
   25 seeds, diff the per_run.csv) before we either fix it or dismiss it. Do **not** state it as
   fact in the report.

### 🟢 Minor / by-design (note, don't necessarily fix)

9. **Agata's σ-ablation uses FULL as its reference row** (effect = full − arm). That's why
   "single is best" reads as a positive effect. Fine, but **relabel** it as a neutral
   "single/multiple/full comparison," not "improvement over full," to avoid implying full was
   ever the baseline.

10. **Heavy committed artefact trees.** `benchmark_wp4_results/` (many run folders + PNGs) and
    assorted `scripts/` are committed on Agata's branch. Low conflict risk, but bulky —
    candidate for `.gitignore` before the final merge.

---

## 3. Missing / not-yet-done (gaps vs the assignment)

- **Agata's "recombine only the best-performing σ-parameter"** — Arthur asked for this
  explicitly; it was **never implemented**. Her negative result is a verdict on *coordinate*
  recombination (positions), **not** on *strategy-parameter* recombination. Worth saying out
  loud so it doesn't look like we ignored his suggestion.
- **WP5's smooth surrogate** — the spec required L-BFGS-B to polish a *soft-min* surrogate (the
  min-distance objective is non-smooth); Martin polishes the **raw** objective, which is flat in
  almost every direction → the polish is a near-no-op. **Not implemented yet** → the current "no
  gain" is "no gain from a no-op," a weaker claim than we can make once the surrogate is added.
- **Elitist-archive reintroduction** (WP2) was only exercised on multiple-variance, 4 seeds,
  300k — too thin to claim anything beyond "no help here."
- **WP2 & WP4 OFAT+stats reruns** on B (item 6) — the single biggest "make it defense-ready" task.
- **One agreed (seeds, budget, n) triple** for the final sweep (items 4, 5, 7).

---

## 4. Pre-deadline action table (what each WP must do)

| WP | Owner | To be defense-ready by 06-07 | Effort |
|----|-------|------------------------------|--------|
| **WP1** | Leo | Done (merged). Maybe re-emit forest at the agreed seed/budget if those change. | ~0 |
| **WP2** | Ivan | Fix `BASELINE → SINGLE_VARIANCE`; run the **two headline arms** (B+plus, B+archive) through `ofat_benchmark.py → stats.py` at **25 seeds, 100k, n=7/10/15/20** to get real p-values + A12. | ~1 run |
| **WP3** | Cala | Drop the stale `FULL_VARIANCE` BASELINE line; **rerun single-variance at 25 seeds** (currently 10); **reproduce the "25-seed breaks single" report** and report what it actually is. | ~1 run + debug |
| **WP4** | Agata | **100k confirmation** of σ-ablation + recomb at **25 seeds, n=7/10/15/20**; relabel the σ-ablation reference; (optional/Arthur) prototype **recombine-best-σ**. | ~1–2 runs |
| **WP5** | Martin | **Rebase onto `main`** + set `BASELINE=SINGLE_VARIANCE` (fixes the n=10 anomaly); **add the soft-min surrogate** for the gradient step (without it the polish is a no-op); extend to **n=15/20**; rerun. | rebase + 1 feature + run |

**Cross-cutting (team decision at the Friday TA meeting):** lock the **(seeds=25, budget=100k,
n∈{7,10,15,20})** triple for *all* final runs so every forest plot is comparable.

---

## 5. Code-cleanliness note (we did check)

These were read line-by-line and are **correct** — call this out so the team isn't worried:

- **Elitist archive** (`origin/selection-elitism:…/ES/evopy/evopy.py`): deep `clone()`s, RNG not
  disturbed, stagnation counter has no off-by-one, bookkeeping is byte-identical to "off" (as it
  should be).
- **Recombination** (`origin/recombination-agata:…/ES/evopy/recombination.py`): reproducible RNG,
  safe odd-length fallback, full-variance angle handling intentional. Permutation-symmetry is a
  *documented limitation*, not a hidden bug.
- **Repair** (`origin/constraint_handling-improvements:…/ES/evopy/individual.py`): the `reflect`
  tent-map `(x−lo) % (2·span)` correctly handles arbitrarily large overshoot; `clip` is a plain
  `np.clip`; repair is threaded to children across all three σ-strategies.
- **Gradient polish** (`origin/martin:…/ES/evopy/evopy.py:181–200`): `_lbfgsb_polish` charges every
  objective call to `self.evaluations` (fair budget), caps `maxfun` at the remaining budget, and
  handles the maximize/minimize sign correctly. The *only* issue is design, not a bug: it optimises
  the **raw** non-smooth objective instead of a smooth surrogate → near-no-op (see §3 + WP5 guide).

The four **WP1 bug fixes** (selection pressure, τ precedence, rotation index, RNG propagation) are
the only genuine code defects found in the whole project, and they're already fixed + merged.

---

## Related
- Per-WP detail: [WP1-leo.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP1-leo.md) · [WP2-ivan.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP2-ivan.md) · [WP3-cala.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP3-cala.md) · [WP4-agata.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP4-agata.md) · [WP5-martin.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP5-martin.md)
- How the p-values are computed: [mann-whitney-explained.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/mann-whitney-explained.md)
- Prior deep reviews: `../wp3-review.md`, `../wp4-review.md`
