---
title: "WP5 — Gradient + EA hybrid (Martin)"
subtitle: "Findings guide · the 'big' change: EA for global search + L-BFGS-B local polish"
owner: "Martin · branch `martin` (merged to main 2026-06-04)"
status: "findings summary (Leo, updated 2026-06-04) from the canonical 25-seed run on the MERGED code. Local working notes."
---

# WP5 — Gradient + EA hybrid

> 🆕 **New to the idea?** Read [WP5-how-it-works.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP5-how-it-works.md)
> first — a plain-English, figure-by-figure walkthrough of what a "polish" is and how the EA + gradient
> loop together. *This* page is the results + code audit.

## What Arthur asked for (TA meeting, 2026-05-27)

> The **"big" change:** a **gradient + EA hybrid loop** — the EA does the broad/global search,
> a gradient-based local optimiser does the fine/local polish.

The ambitious "memetic" idea: keep the EA's global exploration, but bolt on a classical local
optimiser to squeeze out the precision the EA is slow at.

## What Martin built (code audit — it works)

In `ES/evopy/evopy.py` (now merged to `main`):

- A `local_search` kwarg: `"none"` (default), `"final"` (one L-BFGS-B polish after the EA loop), or
  `"interleaved"` (polish the current best every `local_search_k` generations). Wired as two OFAT
  treatments — `B+final_polish`, `B+interleaved_polish`.
- `_lbfgsb_polish()`: `scipy.optimize.minimize(method="L-BFGS-B")` from the EA's best, bounded to
  `[(0,1)]·2n`.
- ✅ **Budget accounting is fair:** every objective call inside the polish increments
  `self.evaluations` and `maxfun` is capped at the *remaining* budget — gradient evals are charged to
  the same 100k as the EA (exactly what the spec demanded). Sign handling is correct.
- It polishes the **raw** min-distance objective (no smooth surrogate). That turns out to matter a
  lot for *which* polish mode works — see Finding 2.

The numbers below are the **canonical run on the final merged code**: single-variance + random
baseline, **25 seeds, 100k evals, n = 7/10/15/20** (`data/wp5_per_run.csv`,
`data/wp5_comparisons.csv`). *(The earlier "no gain" reading came from Martin's pre-merge branch,
which ran on a **stale full-variance baseline** — that's why his n=10 baseline was 44% instead of
13%. On the correct baseline the picture is different and better.)*

---

## Finding 1 — Interleaved polish is a **real, large win at big n** ✅

![wp5 results](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_results.png)

| n | pure EA | + final polish | + interleaved polish |
|---|---|---|---|
| 7  | 5.2%  | 5.2% (ns) | 5.0% (ns) |
| 10 | 13.4% | 13.4% (ns) | 13.4% (ns) |
| 15 | 61.9% | 57.9% (ns) | **28.9%** ✲✲ (A12 0.73, p=0.005) |
| 20 | 64.2% | 62.3% (✲, marginal) | **47.3%** ✲✲ (A12 0.74, p=0.003) |

![wp5 forest](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_forest.png)

- **Interleaved polish significantly improves the large-n regime:** it roughly **halves the gap at
  n=15 (62% → 29%)** and cuts it hard at **n=20 (64% → 47%)**, both `**` (p < 0.01, A12 ≈ 0.73–0.74).
- **Final polish barely moves anything** — `ns` everywhere except a marginal `*` at n=20.
- **Neither helps at n=7/10** — those instances already converge well within budget, so there's no
  room for a polish to add.

The hybrid helps **exactly where the EA struggles most** (large n, where pure EA is stuck at 60%+).
That's the memetic story working as intended — but, crucially, only the **interleaved** variant.

---

## Finding 2 — Why *interleaved* works but *final* doesn't (the real insight)

![why flat](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_why_flat.png)

CiaS fitness is the **minimum** over all pairwise distances — set by **one binding pair**. Nudge any
circle that *isn't* in that pair and the minimum doesn't change → the objective is **flat** in most
directions → L-BFGS-B (finite-difference gradient) reads ~zero and takes almost no step. So:

- **A `final` polish lands on the EA's converged best — a locally flat point** → it reads zero
  gradient and does nothing (gap barely moves; at n=7 it changed by 0.000005). The figure shows it:
  on the flat shelf the true objective (red) has no slope.
- **At small n the EA is already converged**, so *any* polish hits the same flat wall → no gain.
- **But `interleaved` polish fires mid-search at large n, where the EA is nowhere near converged**
  (gap still ~60%, the packing is messy with *many* near-binding pairs). There the objective is
  **not** flat — L-BFGS-B can iteratively push several crowded pairs apart, and because the improved
  best is **reinjected into the population every K generations**, the gains compound and steer the
  rest of the EA search. That feedback loop is why interleaved ≫ final at large n.

**Presentable takeaway:** *the hybrid pays off precisely when the EA hasn't converged (large n) and
the local optimiser is applied repeatedly during search; a single end-of-run polish on the
non-smooth objective is a near-no-op.* A genuine, well-explained EA result.

**Headroom (optional):** polishing a **smooth soft-min surrogate** (green dashed in the figure)
instead of the raw min would give the gradient traction even at converged/flat points — likely
rescuing `final` polish and squeezing more out of `interleaved`. Not implemented; a clean "future
work" line.

---

## How it stacks up (honest context)

- Interleaved polish is a **legitimate, significant improvement** over pure EA at n≥15 — present it as
  a positive WP5 result with p-values.
- For raw large-n gap, **WP3's clip/reflect repair is still stronger** (n=20: clip 17.5% vs
  interleaved-polish 47.3%) — but that's a *different lever* (constraint handling). The honest framing:
  "the gradient hybrid helps the unconverged large-n regime; constraint repair helps more on this
  particular problem, but the two are independent and could be combined."

## ✅ Status — merged + measured

- Branch `martin` **merged to `main`** (conflicts with Cala's `repair` resolved; baseline = single +
  random; all 6 treatments live in `ofat_benchmark.py`).
- Measured on the shared pipeline: **25 seeds, 100k, n=7/10/15/20**, real Mann–Whitney p-values + A12.
- The old n=10 "44% baseline" anomaly is **gone** (it was the stale full-variance baseline).

## How it maps to the assignment

WP5 is the headline "big change," and it delivers a **justified, statistically significant** result:
the memetic EA+gradient hybrid (interleaved) significantly improves the hard large-n instances, with
a clear mechanism (it helps while the EA is still converging; a single final polish hits the
non-smooth objective's flat wall). That satisfies Arthur's "justify the direction + show
significance" — and the surrogate idea is a clean future-work hook.

See [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) for WP5's row in the config matrix.
