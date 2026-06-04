---
title: "WP5 — How the gradient + EA hybrid works (big picture)"
subtitle: "What a 'polish' is, how the EA and the gradient loop together, and what it means"
status: "Leo's local working notes. 2026-06-03. Companion to WP5-martin.md (which has the results/audit)."
---

# WP5 — how the hybrid actually works

This is the **plain-English, big-picture** walkthrough of Martin's WP5 code: what it's
doing and *why*, with pictures. For the **results, the audit, and the bugs**, see
[WP5-martin.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP5-martin.md).

## The one-line idea

> An **Evolution Strategy (EA)** is great at searching **broadly** but slow at nailing the
> **exact** best spot. A **gradient optimiser** is the opposite — useless at searching broadly,
> but brilliant at sliding **precisely** to the bottom of whatever valley it starts in.
> WP5 **bolts them together**: let the EA find the right valley, then let the gradient find its
> exact bottom. (This combo has a name in the EA world: a **memetic algorithm**.)

---

## 1. Two kinds of search: global vs local

![global vs local](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_memetic_landscape.png)

Think of the y-axis as "how far from optimal" (lower = better) and the x-axis as "all possible
circle arrangements" squashed onto one line.

- **Left — the EA (global search):** it keeps a *population* of candidate packings scattered across
  the landscape and, generation after generation, drifts the survivors toward the good regions. It's
  good at **finding the deepest valley** even among many — but once it's roughly there, it wastes a
  lot of random mutations to inch the last little bit.
- **Right — the gradient (local search):** starting from the EA's best point, it looks at the **local
  slope** and **rolls downhill** to the exact bottom of *that* valley. Fast and precise — but it can
  only go *down from where it starts*; it can't jump to a different valley.

**Together:** the EA picks the valley, the gradient finishes the job. Each covers the other's weakness.

---

## 2. What "a polish" actually is

A **polish** = take the single best solution the EA has so far, hand it to a classical optimiser
(**L-BFGS-B**), and let that optimiser **nudge the circles a little, following the slope**, to squeeze
out a smaller gap. Then write the improved arrangement back.

**L-BFGS-B in one sentence:** it's a smart form of *gradient descent* — it estimates which direction
is "downhill" (by trying tiny test-moves), steps that way, and repeats, while keeping every circle
inside the `[0,1]` box. (The "B" = *bounded*; it respects the square.)

> Because the improved genotype is **written back** into the individual, this is the **Lamarckian**
> flavour of memetic search ("the learning is inherited"). The alternative — *Baldwinian* — would
> only use the polished *fitness* for selection but keep the original genes. Martin's code is
> Lamarckian.

---

## 3. How the EA and the gradient loop together — two modes

![the hybrid loop](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_hybrid_loop.png)

The EA runs its normal loop (blue): initialise → mutate/evaluate/select → repeat until the budget is
spent. The polish (green) is bolted on in one of **two modes**:

- **`final` mode:** let the EA run **all the way to the end**, then do **one** polish of the final best.
  (One precise nudge, right at the finish.)
- **`interleaved` mode:** **every K generations**, pause the EA, polish the current best, **drop it
  back into the population**, and carry on. (Many small nudges along the way — and a polished solution
  can then *seed* further EA search.)

This timing is the only real difference between the two:

![when each polish acts](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_when_polish.png)

`final` = the dashed line that only dips at the very end; `interleaved` = the green line with small
dips spread throughout.

---

## 4. The budget is shared (this is the fair-play rule)

The EA and the gradient **draw from the same pot of evaluations** (100,000). Every time the polish
checks a candidate, that counts as one evaluation, just like an EA fitness check. So a polish isn't
"free precision" — it **spends evaluations the EA could have used** for more generations. That's
deliberate: it forces an honest comparison ("is polishing *worth* the generations it costs?").
Martin's code does this correctly — it charges every gradient evaluation to the shared counter.

---

## 5. What it *means* (why this is a sensible "big" idea)

EAs and gradient methods are the two great families of optimisation, and they're **complementary**:
exploration vs exploitation. Hybridising them is a classic, well-respected move (memetic algorithms,
e.g. CMA-ES is sometimes paired with local search). For a packing problem like Circles-in-a-Square,
the hope is concrete: the EA gets the circles *roughly* into a good lattice, and the gradient slides
them the last fraction of a percent into the perfect positions the EA would take ages to stumble on.

---

## 6. When it helps, when it doesn't (and the catch)

There's one assumption hiding in "the gradient rolls downhill": **the landscape has to actually have a
slope.** For CiaS that depends on *where* you polish.

![why the polish stalls](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp5_why_flat.png)

CiaS fitness is the **minimum** pairwise distance — set by **one** binding pair of circles. Move any
*other* circle and the minimum doesn't change → the landscape is **flat** → the gradient is **zero**
→ L-BFGS-B takes no step. That has a sharp consequence (confirmed by the real 25-seed run):

- **A `final` polish lands on the EA's already-converged best — a flat point** → near-no-op (it moved
  the gap by 0.000005 at n=7). Same story at small n, where the EA converges anyway.
- **But `interleaved` polish fires mid-search at large n, where the EA is far from converged** (gap
  ~60%, the packing still messy with many near-binding pairs). There the landscape *isn't* flat, so
  L-BFGS-B makes real progress — and because the improved best is reinjected into the population, the
  gains compound. Result: **interleaved polish significantly improves n=15 (62%→29%) and n=20
  (64%→47%)**, while final polish doesn't.

**The remaining headroom** (the WP5 design called for it but the code skipped it): polish a **smooth
surrogate** — a "soft" version of the minimum (`soft-min`) that has a gradient *everywhere* (green
dashed above) — for the gradient step only. That would give even the flat/converged points a slope to
follow, likely rescuing `final` polish too.

**Bottom line:** the hybrid genuinely works **where the EA struggles most** (large n, via interleaved
polish); a single end-of-run polish hits the non-smooth objective's flat wall. See
[WP5-martin.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP5-martin.md)
for the measured results.
