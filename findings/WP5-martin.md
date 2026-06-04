---
title: "WP5 — Gradient + EA hybrid (Martin)"
subtitle: "Findings guide · the 'big' change: EA for global search + L-BFGS-B local polish"
owner: "Martin · branch `martin` (pushed 2026-06-03)"
status: "findings summary (Leo, 2026-06-03) from Martin's pushed code + his WhatsApp OFAT table. Local working notes."
---

# WP5 — Gradient + EA hybrid

## What Arthur asked for (TA meeting, 2026-05-27)

> The **"big" change:** a **gradient + EA hybrid loop** — the EA does the broad/global search,
> a gradient-based local optimiser does the fine/local polish.

This is the ambitious "memetic" idea: keep the EA's global exploration, but bolt on a classical
local optimiser to squeeze out the last bit of precision the EA is slow at.

## What Martin built (code audit — it works, with one important omission)

On branch `martin`, in `ES/evopy/evopy.py`:

- A `local_search` kwarg: `"none"` (default), `"final"` (one L-BFGS-B polish after the EA loop), or
  `"interleaved"` (polish the current best every `local_search_k` generations). Wired as two OFAT
  treatments — `B+final_polish`, `B+interleaved_polish` (`ofat_benchmark.py:76–77`).
- `_lbfgsb_polish()` (`evopy.py:181–200`): runs `scipy.optimize.minimize(method="L-BFGS-B")` from
  the EA's best, with the box bounds `[(0,1)]·2n`.
- ✅ **Budget accounting is fair:** every objective call inside the polish does `self.evaluations += 1`
  and `maxfun` is capped at the *remaining* budget — so gradient evals are charged to the same
  100k as the EA (exactly what the spec demanded). The maximize/minimize sign handling is correct.

**The one omission (and it's the whole story):** the polish optimises the **raw** fitness function
— the true `min` pairwise distance — **not a smooth surrogate.** The spec
(`../wp5-gradient-hybrid.md`) explicitly called for a **soft-min surrogate** for the gradient step,
*because* the min-distance objective is non-smooth. Skipping it is why the hybrid does nothing —
see Finding 2.

---

## Finding 1 — No significant gain (but on the WRONG baseline)

![wp5 results](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_results.png)

Martin's OFAT sweep (4 treatments × n∈{7,10} × **25 seeds**, 100k evals; his WhatsApp paste,
`data/wp5_martin_chat.csv`):

| treatment | n | baseline gap | arm gap | A12 | p | verdict |
|---|---|---|---|---|---|---|
| final polish | 7 | 6.05% | 6.05% | 0.527 | 0.75 | ns |
| final polish | 10 | 43.8% | 39.2% | 0.566 | 0.43 | ns |
| interleaved | 7 | 6.05% | 5.34% | 0.635 | 0.10 | ns |
| interleaved | 10 | 43.8% | 26.9% | 0.523 | 0.79 | ns |

- **Nothing is significant** at 25 seeds — the polish doesn't reliably beat pure EA.
- **Read the interleaved n=10 row carefully:** the *median* drops a lot (43.8% → 26.9%) but
  **A12 = 0.52, p = 0.79** → it is **not** a consistent win (a couple of lucky polishes moved the
  median; most runs didn't budge). This is the textbook reason we report A12 + p, not just medians
  — see [mann-whitney-explained.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/mann-whitney-explained.md).

### 🔴 The n=10 baseline anomaly — RESOLVED

Martin's baseline gap at n=10 is **43.8%**, but the team's single-variance baseline is **13.4%**
(`data/wp1_per_run.csv`). Cause found in his code:

- **His `ofat_benchmark.py` (line 61) pins `BASELINE = Strategy.FULL_VARIANCE`** — the *stale*
  baseline, never switched to single (same drift as WP2/WP3).
- **His branch is 2 commits behind `main`:** it forks at `85115f0`, *before* the single-variance
  switch (`723639d`) and the random-repair switch (`3fa67f7`).

So Martin benchmarked his polish on a **full-variance** baseline. At 100k evals, full-variance has
≈ n + n(n−1)/2 strategy parameters to self-adapt — fine at n=7 (28 params → 6% gap) but **far from
converged at n=10** (55 params → 44% gap). That *entirely* explains the 0.44-vs-0.13 gap; it's not
a polish artefact, it's the wrong baseline. **Fix: rebase onto `main` and rerun on single-variance.**

---

## Finding 2 — *Why* the polish stalls: a non-smooth objective (the real insight)

![why flat](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_why_flat.png)

CiaS fitness is the **minimum** over all pairwise distances. The minimum is set by **one binding
pair** of circles. That has a brutal consequence for a gradient method:

- Nudge **any circle that isn't in the binding pair** → the binding distance is unchanged → the
  objective is **exactly flat** → its gradient is **zero**.
- So out of all 2n coordinates, L-BFGS-B only "feels" the **2** belonging to the binding pair — and
  the moment it separates them, a *different* pair becomes the new minimum (a kink, non-smooth).

L-BFGS-B estimates its gradient by finite differences. On this objective it mostly reads **zero**,
concludes it's already at an optimum, and **takes essentially no step** — which is exactly what the
data shows (`final_polish` at n=7 changed the gap by **0.000005**). The figure illustrates it: where
the EA leaves the best (on a flat shelf), the **true** objective (red) has no slope, while a
**smooth soft-min surrogate** (green) slopes downhill and *would* give L-BFGS-B a usable gradient.

**This is the presentable result:** *"A naive gradient polish on the raw min-distance objective is a
near-no-op, because the objective is non-smooth and flat in almost every direction. To make a hybrid
work you must polish a smooth surrogate (soft-min), as planned."* That's a genuine EA insight
(non-smooth fitness ↔ memetic local search), not a failure.

---

## ⚠️ Caveats / what must change before this is defense-ready

1. **Wrong baseline (blocking):** rebase `martin` onto `main`; set `BASELINE = SINGLE_VARIANCE`;
   confirm baseline n=10 ≈ **13%**, not 44%.
2. **No smooth surrogate:** implement the soft-min objective for the *gradient step only* (the EA
   keeps optimising the true min) — without it the hybrid can't help, so the current "no gain" is
   really "no gain *from a no-op*," a weaker claim than we can make.
3. **n-range:** extend to **n=15/20** (the regime where a precision polish would matter most).
4. **Seeds:** 25 ✓ (already the team number — good).

## How it maps to the assignment

WP5 is the headline "big change," and even as a negative it carries two real EA lessons: **memetic /
hybrid search** (global EA + local optimiser) and the **non-smoothness of the CiaS objective** (why
naive gradients don't apply, and what a surrogate fixes). With the baseline fixed and a surrogate
added, it becomes either a justified improvement *or* a well-explained, significant negative — both
satisfy Arthur's "justify the direction + show significance" rules.

See [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) (items 1–3) for WP5's row in the config
matrix and action table.
