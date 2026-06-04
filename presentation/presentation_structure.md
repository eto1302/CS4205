# CS4205 — Presentation Structure
## Evolution Strategies for Circles in a Square

---

## Overview

| Section | Slides | Benchmark used |
|---|---|---|
| Problem & motivation | 1 | — |
| Fixed baseline + method | 2 | — |
| Individual WP results | 3–6 | OFAT (each WP vs frozen B) |
| Combined algorithm | 7 | Sequential ablation V1→V4 |
| Conclusion | 8 | — |

---

## Slide 1 — Problem: Circles in a Square

**Goal:** Pack *n* circles inside a unit square, maximising the minimum pairwise distance between centres.

**Show:**
- Visual of optimal configurations for n = 7, 10, 15, 20 (from Packomania reference values)
- Animation or side-by-side: bad random packing → known optimum
- Why it's hard: broad plateaus in the fitness landscape — only the *binding pair* of circles contributes to fitness, all other moves are silent

**One sentence framing:** *"A deceptively simple problem with a rugged landscape — the right algorithmic choices matter a lot."*

---

## Slide 2 — Fixed Baseline B + Measurement Method (WP1)

**Goal:** Define the reference point and explain how every claim is validated.

**Baseline B configuration:**

| Parameter | Value | Reason |
|---|---|---|
| Strategy | SINGLE_VARIANCE | Simplest neutral reference; WP4 ablation confirms it wins at every n |
| Selection | `(μ, λ)` | Modern ES standard (BSw95 §6.4); `(μ+λ)` hinders σ self-adaptation |
| Init | LHS | Spreads population across [0,1]²ⁿ; uniform init collapsed ~50% of coords |
| Repair | random-resample | Original behaviour; better repair = measurable WP3 improvement |
| Budget | 25 seeds × n∈{7,10,15,20} × 100k evals | Enough for Mann-Whitney to separate signal from luck |

**Measurement method — OFAT:**
- One frozen baseline B
- Each improvement = B with **exactly one thing changed**
- Effect is unconfounded — only your factor moved

**Two statistics (always reported together):**
- **Mann-Whitney p-value** — is the difference real or lucky seeds? Threshold: p < 0.05
- **A12 effect size** — "pick one baseline run and one improved run at random; how often does improved win?" 0.5 = coin flip, >0.6 = meaningful, >0.71 = large

**Show:** forest plot format (dot = median improvement, whisker = 95% CI, filled = significant)

---

## Slide 3 — WP3: Constraint Handling (Cala)

**Benchmark:** OFAT — treatments `B-repair_clip` and `B-repair_reflect` vs frozen B (random-resample)

- Why this change?
- What changed?
- OFAT plots (p + A12)
  - ✅ **Exists** — convergence curves and gap boxplots per repair mode: `benchmark_Cala.py` (`plot()` method)
  - ✅ **Exists** — forest plot row: `plot_ofat.py` from WP1 infra, reads `results/comparisons.csv`

---

## Slide 4 — WP2: Selection & Elitist Archive (Ivan)

**Benchmark:** OFAT — treatments `B+archive` and `B+plus` vs frozen B

- Why this change?
- What changed?
- OFAT plots (p + A12)
  - 🆕 **Needs new code** — fitness trace comparing `(μ,λ)` vs `(μ+λ)` vs archive (monotonicity check). No existing benchmark plots this three-way comparison.
  - 🆕 **Needs new code** — archive utilisation plot (how often the reintroduced individual becomes generation best). No existing script tracks this.
  - ✅ **Exists** — forest plot row: `plot_ofat.py` from WP1 infra

---

## Slide 5 — WP4: Recombination & σ-Strategy (Agata)

**Benchmark:** OFAT — treatments `B+recomb` (circle-pair operator) and σ-strategy arms vs frozen B

- Why this change?
- What changed?
- OFAT plots (p + A12)
  - 🆕 **Needs new code** — bar chart of median final_gap for single/multiple/full across n (σ-ablation). Not produced by any existing benchmark.
  - ✅ **Exists** — forest plot row for recombination: `plot_ofat.py` from WP1 infra

---

## Slide 6 — WP5: Gradient Hybrid (Martin)

**Benchmark:** OFAT — treatments `B+final_polish` and `B+interleaved_polish` vs frozen B. Gradient evals charged to the 100k eval budget.

- Why this change?
- What changed?
- OFAT plots (p + A12)
  - 🆕 **Needs new code** — convergence curves for pure EA vs final_polish vs interleaved_polish at n=15 and n=20. No existing benchmark covers the gradient modes.
  - ✅ **Exists** — forest plot row: `plot_ofat.py` from WP1 infra

---

## Slide 7 — Combined Algorithm: Stacking the Improvements

**Benchmark:** Sequential ablation chain — same `ofat_benchmark.py` runner, TREATMENTS replaced by V1→V4 explicit configs. Same budget: 25 seeds × n∈{7,10,15,20} × 100k evals.

### Stacking order

```
V1  →  V2  →  V3  →  V4
                ↓
               V4b (WP4 — branch, not main chain)
```

| Variant | WP | What is added |
|---|---|---|
| V1 | WP1 | Bug fixes |
| V2 | WP3 | Reflection repair |
| V3 | WP2 | Elitist archive |
| V4 | WP5 | Gradient polish |
| V4b | WP4 | Recombination (branch off V3, honest negative) |

### Plots

**Plot 1 — Convergence staircase**
One panel per n. x = evaluations, y = median best fitness. One line per variant V1→V4, Packomania reference dashed.
- ✅ **Reuse `benchmark_Cala.py`** — the `plot()` method already does exactly this: faint individual runs + bold median + Packomania reference dashed, one panel per n. The only change needed is passing V1→V4 as the sweep axis instead of strategy variants. Add a `label` field to each variant config and feed them in as the `strategies` dimension.

**Plot 2 — Gap heatmap**
Rows = variants, columns = n values, cells = median `final_gap`. Colour scale red (far) → green (close).
- 🆕 **Needs new code** — simple `matplotlib` heatmap from `per_run.csv`. Nothing in `ofat_benchmark.py`, `benchmark_Cala.py`, or `plot_ofat.py` produces a variant × n heatmap.

**Plot 3 — Attribution bar**
For each n, a stacked bar showing the fraction of total gap reduction contributed by each step (V1→V2, V2→V3, V3→V4).
- 🆕 **Needs new code** — derived from the same `per_run.csv`; compute per-step gap delta, normalise, stack. No existing script does this.

### Metrics

- Median `final_gap` ± IQR per variant per n
- Mann-Whitney p + A12 for each transition (V1→V2, V2→V3, V3→V4) — run through the existing `stats.py`, comparing adjacent variants instead of each vs baseline

---

## Slide 8 — Conclusion

**Three columns:**

| What we fixed | What improved | What didn't work |
|---|---|---|
| 4 correctness bugs (diag(σ), τ, rotation, ratio) | Reflection repair: ~3.6× gap reduction at n=15 | Naive recombination (permutation symmetry) |
| Selection pressure restored | Elitist archive: monotone traces without poisoning σ | 1/5 success rule (theoretical mismatch with (μ,λ)) |
| σ self-adaptation now functional | Gradient polish: closes final gap at hard n | LHS stratification (spreading matters, not stratification) |



---

## Appendix slides (have ready, show if asked)

- Full OFAT forest plot (all WP arms in one figure)
- Raw Mann-Whitney tables for all comparisons
- BSw95 quotes justifying `(μ,λ)` as baseline selection scheme
- Bosman & Gallagher Fig. 4 (reflection vs random-resample on CiaS)
- V0 vs V4 side-by-side circle packing visualisation for n=10 and n=20
