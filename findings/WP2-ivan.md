---
title: "WP2 — Selection & Elitism (Ivan)"
subtitle: "Findings guide · (μ,λ) vs (μ+λ) and the elitist archive"
owner: "Ivan · branch `selection-elitism`"
status: "findings summary (Leo, 2026-06-02) from Ivan's committed 300k-eval factorial. Local working notes."
---

# WP2 — Selection & Elitism

## What Arthur asked for (TA meeting, 2026-05-27)

> *Selection schemes:* compare `(μ,λ)` vs `(μ+λ)` — and if we pick specific
> operators we need a **reason**, otherwise compare all.
> *Elitism (nuanced):* a plain elitist archive is "mostly **bookkeeping**" if the
> algorithm converges anyway — *is it really an improvement?* More interesting:
> **reinsert** archived solutions when the run **stalls** (archive as a diversity
> backup). Deliver one plot for the plain archive, one for reintroduction.

WP2 answers exactly these two questions.

## What Ivan built

- **Selection** is the existing `selection_scheme` kwarg: `"comma"` = (μ,λ),
  `"plus"` = (μ+λ).
- **Elitist archive** (new, in `evopy.py`): `archive_mode ∈ {off, bookkeeping,
  reintroduction}`, a top-K store (`archive_size=5`) of best-ever individuals;
  `reintroduction` re-injects archived members after `stagnation_generations=20`
  with no archive-best improvement. Archived genotypes are independent `clone()`s.

## Finding 1 — (μ,λ) vs (μ+λ) is **strategy-dependent** (the interesting result)

![selection](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp2_selection.png)

| n | single-variance comma / plus | multiple-variance comma / plus |
|---|---|---|
| 7 | 3.6% / 3.8% (tie) | 3.1% / 3.4% (tie) |
| 10 | 7.9% / 5.1% (plus better) | 10.5% / **19.4%** (comma better) |
| 15 | 16.6% / 13.6% (plus better) | 21.7% / **45.9%** (comma **2× better**) |

- **Single-variance:** (μ+λ) is *as good or slightly better* than (μ,λ).
- **Multiple-variance:** (μ,λ) **decisively wins** — (μ+λ) is ~2× worse at n=15.

**Why (the reason Arthur wanted):** this is textbook BSw95 — (μ+λ) lets
*misadapted strategy parameters survive*, which hinders σ self-adaptation. That
hurts **more when there are more σ parameters to misadapt** (multiple-variance, n
of them) and barely matters with a single σ. So the *mechanism* predicts exactly
this crossover. **(μ,λ) is the safe default** because it's the strategy-robust
choice — which is why the shared baseline pins comma.

## Finding 2 — the elitist archive is "mostly bookkeeping" (Arthur was right)

![archive](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp2_archive.png)

| n (multiple-var, comma) | off | bookkeeping | reintroduction |
|---|---|---|---|
| 7 | 3.1% | 3.1% | 3.8% |
| 10 | 10.5% | 10.5% | 10.6% |
| 15 | 21.7% | 21.7% | 23.3% |

- **Bookkeeping = identical to off** — the plain archive changes nothing about the
  result here.
- **Reintroduction ≈ no help** (slightly *worse* at n=15).

This is precisely Arthur's prediction: if the algorithm converges anyway, a plain
archive is just bookkeeping and **not an improvement**; reintroduction didn't earn
its keep at these sizes/budget either. A clean, honest negative result.

## ⚠️ Caveats (must fix before these are "final")

Ivan's run is a **factorial via `benchmark_Cala.py`**, not the shared OFAT pipeline,
and it differs from the team baseline:
- **Only 4 seeds** per cell → underpowered; **no Mann–Whitney p-values yet**
  (Arthur mandated significance — needs `stats.py`).
- **300k evals** (not the shared 100k) and **n ∈ {5,7,10,15}** (no n=20).
- His `ofat_benchmark.py` BASELINE was left at the **stale FULL_VARIANCE**.
- Numbers above pool over pop∈{15,30,50} × children∈{5,10} (baseline is pop30/7).

**To finalise:** rerun the two headline comparisons through the shared
`ofat_benchmark.py` → `stats.py` on the current baseline (single-variance, random
repair, 100k, 25 seeds) so the selection + archive arms get real p-values + A12.

> ⚠️ See [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) (items 3, 4, 6, 7) for where WP2 sits
> in the cross-WP config matrix and its row in the pre-deadline action table.

## How it maps to the assignment

Selection pressure and elitism are core EA levers; the brief wants *justified*
improvements with *statistical significance*. WP2 has the justification (BSw95
mechanism, confirmed by the strategy crossover) and two clean deliverables (the
selection crossover plot + the archive-null plot) — it just needs the p-value pass
on the shared baseline to be defense-ready.
