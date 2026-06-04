---
title: "WP1 — Honest Baseline + Measurement Framework (Leo)"
subtitle: "Findings guide · bug fixes, the OFAT/stats pipeline, the baseline definition, and the LHS ablation"
owner: "Leo · branch `bugfix/ta-handoff` (merged to main)"
status: "findings summary (2026-06-02). Local working notes."
---

# WP1 — Baseline + Framework

## What Arthur asked for (TA meeting, 2026-05-27)

> *Initialisation* (already done): Latin-hypercube is "**very reasonable**."
> *Rules of engagement:* report **p-value tests almost everywhere** (baseline vs
> improvement); **bugs ≠ improvements** — bug fixes are *delivered* to the TA but
> **not presented** as results.

WP1 is the **substrate** the other work packages stand on: a *correct* baseline +
the machinery that turns everyone's change into a significance-tested verdict.

## Part 1 — Bug fixes (delivered, **not** presented as improvements)

Four correctness bugs made the original baseline dishonest. Fixing them is what
lets WP2–WP5 measure anything meaningful.

| # | bug | effect | fix |
|---|-----|--------|-----|
| 1 | **No selection pressure** — `num_children=1` ⇒ λ=μ, a degenerate (μ,μ)-ES where every child survives | the EA was "doing nothing" | `num_children=7` (λ=210, λ/μ=7) |
| 2 | **τ operator precedence** in multiple/full variance | learning rate ×3.7–6.3 too large; `np.exp` overflow | `1/√(2√n)` (BSw95 eq. 6.18) |
| 3 | **rotation angle-index** map (full variance) | wrong/duplicate angles | correct bijection |
| 4 | **RNG not propagated** to multiple/full children | not seed-reproducible | pass `random_seed` to children |

These are tracked in `improvements/WP1/bug-fixes.md` and handed to the TA — per
Arthur's "bugs ≠ improvements" rule.

## Part 2 — The measurement framework (this *is* "p-values everywhere")

![pipeline](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp1_pipeline.png)

**OFAT (one-factor-at-a-time):** one frozen baseline **B**; every improvement = B
with exactly one thing changed, compared against the same B. Pipeline:
`ofat_benchmark.py` → `per_run.csv` → `stats.py` (**Mann–Whitney U + A12 effect
size + bootstrap 95% CI**) → `comparisons.csv` → `plot_ofat.py` (forest plots).
Each WP adds **one line** to a registry; the stats are identical for everyone.
This is what delivers Arthur's "significance almost everywhere" — every forest
dot in the WP2/WP3 guides comes out of this pipeline.

## Part 3 — The baseline definition (and *why* each choice)

**B = single-variance · LHS init · (μ,λ) · random-resample repair · pop 30 · 7 children · 100k evals · 25 seeds.**

- **single-variance** — simplest, cheapest, most standard ES default = a neutral
  reference. (multiple/full are WP4 *ablation arms*, not the baseline.)
- **(μ,λ)** — the strategy-robust selection (WP2 shows (μ+λ) hurts self-adaptation
  on multi-σ strategies).
- **random repair** — the *honest original*, so that better repair (reflect/clip)
  is a **measurable WP3 improvement** instead of being silently baked in.
- **LHS init** — kept; but measured (below).

## Part 4 — WP1's own result: LHS is an **honest negative**

![lhs forest](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp1_lhs_forest.png)

Latin-hypercube init was the candidate WP1 "improvement." Measured by ablation
(B vs B with plain uniform init), **25 seeds × n∈{7,10,15,20}**: **not significant
at any n** (A12 ≈ 0.4–0.6, all p > 0.1). LHS's *stratification* buys nothing
measurable over plain uniform random init.

**Interpretation (don't overclaim):** the iteration-1 "LHS win" was really
*spreading out* (uniform **or** LHS) beating the old *clustered* warm-start — not
stratification. So WP1's genuine contributions are the **bug fixes + the
framework**, and LHS is reported honestly as "we measured it; no effect."

## ⚠️ Caveat on the baseline

B = single-variance is the **simplest neutral reference**, chosen for parsimony.
[WP4's σ-ablation](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP4-agata.md) (all-random repair, all n) actually shows **single
winning at every n** — but at a **~20k early-stop budget**; whether multiple/full
would catch up at a much larger budget is untested. So the honest claim is *"single
is the parsimonious choice and wins in our runs,"* not *"single is provably optimal
at any budget."* The baseline is a **reference**, not a trophy.

> ⚠️ See [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) for where WP1 sits in the cross-WP
> config matrix (WP1 = the only WP already merged + at 25 seeds / 100k).

## How it maps to the assignment

WP1 embodies two of Arthur's explicit rules: **bugs delivered-not-presented**, and
**p-values almost everywhere** (the whole stats pipeline). It also gives the
project a *reproducible, scalable* test harness across n — the backbone for every
other WP's results.
