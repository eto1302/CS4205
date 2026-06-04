---
title: "Cross-WP Audit — Inconsistencies, Gaps & Pre-Deadline Actions"
subtitle: "A branch-by-branch sweep of every work package against the shared baseline"
status: "Leo's local working notes (groupwork-notes/, NOT the team repo). 2026-06-03. Deadline 2026-06-07."
---

# Audit — what's inconsistent across the branches

I swept every pushed branch (`git show origin/<branch>:…`, read-only) and cross-checked
each work package against the **shared OFAT baseline** on `main`. Headline:

> **The code is clean; most experiments are now aligned.** No logic bugs were found in anyone's new
> code. **WP1, WP3 and WP5 are merged to `main` and measured at 25 seeds / 100k / n=7-20.** The
> remaining drift is **WP2 (Ivan)** and **WP4 (Agata)** — still on fewer seeds / non-shared budgets and
> needing one pass through the shared pipeline. Not fatal; a short re-run before the 06-07 hand-in.

The shared baseline (on `main`, commit `3fa67f7`):

> **B = single-variance · LHS init · (μ,λ) "comma" · random-resample repair · pop 30 · 7 children · 100 000 evals · 25 seeds.**

---

## 1. Config matrix — every divergence at a glance

| WP | Owner | Branch | σ-strategy of baseline | repair | seeds | eval budget | n values | p-values on shared pipeline? | pushed? |
|----|-------|--------|------------------------|--------|------:|------------:|----------|:---:|:---:|
| **WP1** | Leo | `bugfix/ta-handoff` → **merged to main** | **single** ✓ | random ✓ | **25** | **100k** | 7/10/15/20 | ✅ yes | ✅ |
| **WP2** | Ivan | `selection-elitism` | OFAT pins **FULL** 🔴; factorial ran single | n/a | **4** | 50k & **300k** | **n=5 only** | ❌ no (factorial, no MW) | ✅ |
| **WP3** | Cala | **merged to main** ✅ | single ✓ (fixed) | random→clip/reflect | **25** ✓ | 100k ✓ | 7/10/15/20 ✓ | ✅ yes | ✅ merged |
| **WP4** | Agata | `recombination-agata` | OFAT pins **single** ✓; σ-ablation refs **FULL** | random | **10** | **~20k (early stop)** | 7/10/15/20 (σ), **7/10 only** (recomb) | ✅ yes (medium) | ✅ |
| **WP5** | Martin | **merged to main** ✅ | single + random ✓ | random | **25** ✓ | **100k** ✓ | 7/10/15/20 ✓ | ✅ yes | ✅ merged |

"OFAT pins FULL" = the `BASELINE` dict in that branch's `ofat_benchmark.py` still says
`strategy=Strategy.FULL_VARIANCE` (the value before the 2026-06-01 switch). It does **not**
mean their *results* are full-variance — Ivan and Cala both ran single-variance arms
separately — but it means a naive `uv run ofat_benchmark.py` on their branch reproduces the
**wrong** reference.

---

## 2. Ranked inconsistency list

### ✅ Resolved (were critical)

1. **WP5 — merged + measured on the correct baseline.** Martin's branch (which had a stale
   FULL_VARIANCE baseline + reflect repair, forked at `85115f0`) is now **merged to `main`** with the
   single+random baseline. Re-run at 25 seeds / 100k / n=7-20: **interleaved polish significantly
   improves n≥15** (62%→29% at n=15, `**`); final polish doesn't. The old "n=10 = 44%" baseline
   anomaly was purely the stale full-variance baseline — **gone**. (See
   [WP5-martin.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP5-martin.md).)

### 🔴 Still open

3. **Stale `FULL_VARIANCE` baseline still in `selection-elitism` (Ivan)** — the last branch not yet
   updated. (Cala + Martin are merged on single+random.) **→ Ivan: one-line fix**
   `Strategy.FULL_VARIANCE → Strategy.SINGLE_VARIANCE`, then rerun.

### 🟡 Medium (must standardise before final numbers)

4. **Seed counts: standardising on 25. Done: Leo, Martin, ~~Cala~~ (now 25 ✓, merged). Still at
   10: Agata. At 4: Ivan.** p-values/CIs are only comparable at a fixed seed count → **Agata and
   Ivan still need to rerun at 25.** (This was the "10 vs 25" split Leo flagged; Cala is now fixed.)

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

8. **Cala's "25 seeds break single-variance" — RESOLVED.** ✅ Her final 25-seed single-variance
   run completed cleanly and is merged to `main`; the earlier worry **did not reproduce**. (As
   suspected, there was no code-level seed bug.)

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
- **WP5's smooth surrogate (optional future work, not a blocker).** Martin polishes the **raw**
  min-distance (non-smooth → flat at converged points), which is why **`final` polish doesn't help**.
  `interleaved` polish already gives a significant large-n win without it; a soft-min surrogate is the
  clean "future work" line that would likely rescue `final` polish too.
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
| **WP3** | Cala | ✅ **Done + merged.** 25-seed single-variance run on `main`; baseline fixed; clip significant at every n. Nothing outstanding. | ~0 |
| **WP4** | Agata | **100k confirmation** of σ-ablation + recomb at **25 seeds, n=7/10/15/20**; relabel the σ-ablation reference; (optional/Arthur) prototype **recombine-best-σ**. | ~1–2 runs |
| **WP5** | Martin | ✅ **Done + merged.** 25-seed run on `main`; interleaved polish significant at n≥15. Optional future work: smooth soft-min surrogate (could rescue `final` polish too). | ~0 |

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
