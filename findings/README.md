---
title: "CS4205 Group Project — Findings Guides (all 5 WPs)"
subtitle: "What each work package found, tied to Arthur's TA-meeting and the assignment scope"
status: "Leo's local working notes (groupwork-notes/, NOT the team repo). Updated 2026-06-03."
---

# Findings — WP1 … WP5

Readable, plot-backed summaries of what we've actually found so far, each tied
back to **Arthur's TA-meeting (2026-05-27)** and the **assignment scope**. These
are *local working notes* — the team-facing docs live in `improvements/` on the
branches.

> **Start here for the cross-WP picture:**
> - 🔍 [**AUDIT-inconsistencies.md**](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) — branch-by-branch sweep:
>   config matrix, every inconsistency ranked, and a **pre-deadline action list** per WP.
> - 📊 [**mann-whitney-explained.md**](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/mann-whitney-explained.md) — plain-English guide to the
>   p-values / A12 / CIs we report (we all have to present these to Arthur).

## The assignment, in one line

Take the baseline **Evolution Strategy** for **Circles-in-a-Square** (place *n*
points in the unit square to **maximise the minimum pairwise distance**) and
**improve it** — with every improvement **justified** (no blind trying) and shown
**statistically significant** (Arthur: "p-values almost everywhere"). CiaS is
**scalable** in *n*, so results should hold/extrapolate across problem size.

## Arthur's fronts → who owns what

The TA meeting laid out several fronts; we split them into work packages:

| Front Arthur named | WP | Owner | Guide |
|---|---|---|---|
| Initialisation ("LHS very reasonable") + rules (p-values, bugs≠improvements) | **WP1** | Leo | [WP1-leo.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP1-leo.md) |
| Selection `(μ,λ)` vs `(μ+λ)` + elitist archive (bookkeeping vs reintroduction) | **WP2** | Ivan | [WP2-ivan.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP2-ivan.md) |
| Constraint handling (random → reflection/clipping) | **WP3** | Cala | [WP3-cala.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP3-cala.md) |
| Recombination + σ-strategy selection | **WP4** | Agata | [WP4-agata.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP4-agata.md) |
| "Big" change: gradient + EA hybrid | **WP5** | Martin | [WP5-martin.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP5-martin.md) |

## Headline findings (the three covered here)

| WP | Question | Finding | Significant? |
|---|---|---|---|
| **WP1** | Does Latin-hypercube init help? | **No** — stratification ≈ plain uniform. Real WP1 value = bug fixes + the stats framework. | LHS: ns (honest null) |
| **WP2** | `(μ,λ)` vs `(μ+λ)`? Archive? | **Strategy-dependent:** tied on single-σ, **comma wins big on multi-σ** (plus 2× worse). Archive = "mostly bookkeeping" (no gain), reintroduction ≈ no help. | ⚠️ p-values pending (4 seeds) |
| **WP3** | Better out-of-bounds repair? | **clip & reflect crush random at n≥10** (3–4× smaller gap, A12 up to 1.0). clip ≈ reflect; clip simplest. | ✓ *** at n≥10 |
| **WP4** | Which σ-strategy? Does recombination help? | **Single-variance wins at every n** (grounds the team baseline); **naive recombination hurts ~10×** (CiaS permutation symmetry). | ✓ σ: *** ; recomb: *** (worse) |
| **WP5** | Does a gradient local-polish hybrid beat pure EA? | **No significant gain** — and we know *why*: the polish optimises the **non-smooth** min-distance (flat gradient) instead of a surrogate → near-no-op. Also ran on a **stale full-variance baseline** (rerun needed). | ⚠️ ns (explained) |

## The shared baseline everything is measured against

**B = single-variance · LHS · (μ,λ) · random repair · pop 30 · 7 children · 100k evals · 25 seeds** (on `main`).
Each improvement changes **one** factor vs B and gets a Mann–Whitney p-value + A12
effect size + bootstrap CI (forest plots). See [WP1-leo.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP1-leo.md) for the
framework.

## Cross-cutting honesty notes (for the defense)

The full, ranked version is in [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md). The essentials:

- **The experiments aren't apples-to-apples yet** — seeds differ (25 / 10 / 4), budgets differ
  (100k / ~20k / 300k), and two branches still pin a stale `FULL_VARIANCE` baseline. The *code*
  is clean; we just need one agreed (25 seeds, 100k, n∈{7,10,15,20}) sweep per WP.
- **WP2 needs a rerun on the shared baseline** (it used 300k evals / 4 seeds / n=5 / no p-values)
  before its numbers are final.
- **WP3 should bump 10 → 25 seeds** for tight CIs (direction is already clear); and **reproduce**
  the "25 seeds breaks single-variance" report before stating it as fact.
- **WP4's "single is best" holds in the data we have** (σ-ablation, all n) — but at a **~20k
  early-stop budget**; a 100k confirmation is pending. So say "single is the *parsimonious* choice
  and wins in our runs," not "single is provably optimal at any budget." The baseline is a
  **neutral reference**, chosen for simplicity.
- **WP5 (Martin)** ran on a **stale full-variance baseline** (explains the n=10 0.44-vs-0.13 anomaly)
  and its polish lacks the smooth surrogate it needs → rerun on single-variance + add the surrogate.
- Every figure here is regenerated from real run data by `make_findings_figs.py` (data in `data/`,
  plots in `figs/`); budgets/seeds differ per WP and are annotated on each plot.
