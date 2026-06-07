---
title: "WP4 — Recombination & σ-strategy selection (Agata)"
subtitle: "Findings guide · σ-ablation (single/multiple/full) + recombination operators on CiaS"
owner: "Agata · branch `recombination-agata`"
status: "findings summary (Leo, 2026-06-03) from Agata's committed medium runs. Local working notes."
---

# WP4 — Recombination & σ-strategy

## What Arthur asked for (TA meeting, 2026-05-27)

> *Recombination:* a justified way to pick one operator over another; does **CiaS symmetry**
> affect recombination? On strategy parameters: optimise them individually, or **"recombine only
> the best-performing strategy parameter."**
> *σ-strategy selection:* at what point does one σ-strategy (single / multiple / full) **outperform
> another?**

WP4 owns two linked questions: **which σ-strategy should the baseline use**, and **does adding
recombination help**. The first one is *why the whole team's baseline is single-variance* — so this
WP quietly underpins everyone else's comparisons.

## What Agata built

`ES/evopy/recombination.py` (audited — **correct**, no bugs):
- **`coordinate` mode** — discrete recombination: each coordinate independently inherits from
  parent A or B (`np.where(mask, a, b)`).
- **`circle_pair` mode** — CiaS-aware: whole `(xᵢ, yᵢ)` circles inherited together (keeps a circle
  intact), with a safe fallback to coordinate mode on odd-length genotypes.
- **σ recombination** — intermediary averaging `(σ_A + σ_B)/2`; for full-variance, σ's are averaged
  and rotation angles handled with a circular mean (`_alpha` modes).
- Wired into `evopy.py` with a seeded RNG (reproducible); `recombine=False` is a true no-op default,
  so the baseline is untouched unless recombination is switched on.

Two experiments, both run through the shared `stats.py` (Mann–Whitney + A12 + bootstrap CI).

---

## Finding 1 — σ-ablation: **single wins at every n** (this validates the baseline)

![sigma ablation](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp4_sigma.png)

Median gap-to-optimum, 10 seeds, ~20k-eval budget (`data/wp4_sigma_per_run.csv`):

| n | single (1 σ) | multiple (n σ) | full (n + rotations) | best |
|---|---|---|---|---|
| 7  | **4.6%**  | 12.8% | 26.6% | single |
| 10 | **7.9%**  | 22.1% | 47.5% | single |
| 15 | **18.0%** | 50.0% | 61.8% | single |
| 20 | **24.9%** | 63.1% | 66.8% | single |

- **Single is best at every n**, and the gap *widens* with n. Versus full-variance it's
  **significant**: `**` at n=7 (A12=0.85), `***` at n=10/15/20 (**A12=1.0** — single beat full in
  every single seed pairing).
- Multiple sits in between; full is the worst.

**Why (ties to ES theory — Beyer–Schwefel self-adaptation, the same BSw95 logic as [WP2](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/WP2-ivan.md)):**
each extra strategy parameter is another thing the algorithm must *self-adapt* by trial and error.
Full-variance carries ≈ *n + n(n−1)/2* parameters (step sizes **plus** rotation angles) — at n=20
that's hundreds of dials to tune from noisy fitness feedback. On a problem like CiaS that doesn't
need correlated mutations, those extra dials are pure overhead: more to misadapt, slower to
converge. **Single-variance is the parsimonious choice** → the team baseline pins it.

---

## Finding 2 — Naive recombination **hurts badly** (a clean negative)

![recombination](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp4_recomb.png)

Recombination on the single-variance baseline, 10 seeds, ~20k evals
(`data/wp4_recomb_per_run.csv`):

| n | no recomb (baseline) | coordinate recomb | circle-pair recomb |
|---|---|---|---|
| 7  | **4.6%** | 46.2% ✲✲✲ | 45.7% ✲✲✲ |
| 10 | **7.9%** | 50.6% ✲✲✲ | 52.3% ✲✲✲ |

- **Both modes are ~10× worse**, and it's as significant as it gets: **A12 = 0.00** (recombination
  lost *every* pairing), **p ≈ 1.8e-4 (`***`)** at both n.
- Circle-pair (the CiaS-aware version) **doesn't rescue it** — it's just as bad.

**Why it fails — CiaS permutation symmetry (the justification Arthur wanted):** a CiaS solution is a
*set* of circles; relabelling the circles gives the *same* packing. So "circle 3" in parent A and
"circle 3" in parent B are **semantically unrelated** points. Averaging or swapping by index mixes
two good-but-differently-labelled packings into an incoherent blob — you destroy both parents'
structure. This is a real, citable EA pitfall (recombination needs *aligned* or
*permutation-invariant* representations), and our data nails it: even the "keep a circle intact"
mode fails, because the **labels** still don't line up across parents.

**Honest framing:** present this as *"naive positional recombination is disruptive on CiaS, and we
explain why"* — a valid, well-justified negative result, **not** a failed WP.

---

## ⚠️ Caveats (surface these, per the audit)

- **10 seeds, ~20k-eval early-stop budget** (not the team's 25 seeds / 100k). The *directions* are
  bulletproof (A12 = 0.0 / 1.0), but the *magnitudes* — and especially "full is the worst σ-strategy"
  — are partly a **budget artefact**: at 20k, full-variance simply hasn't had time to adapt its
  hundreds of parameters. A **100k / 25-seed confirmation** would make this airtight.
- **σ-ablation uses full-variance as its reference row** → relabel it a neutral "single vs multiple
  vs full" comparison, not "improvement over full" (full was never our baseline).
- **Recombination was tested only on single-σ**, and **Arthur's "recombine only the best-performing
  σ-parameter" was never implemented** — so this is a verdict on *coordinate/position* recombination,
  **not** on *strategy-parameter* recombination. Flag that distinction (it's a different claim).
- **Integration risk:** Agata and Cala both edit `EvoPy.__init__` and the `run()` children-loop in
  `evopy.py` → a **merge conflict** when both branches land. Coordinate the merge order.

See [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) (items 5, 9, and the "recombine-best-σ" gap)
and the deeper code review in `../wp4-review.md`.

## How it maps to the assignment

WP4 delivers **two** of Arthur's fronts with justification + significance: the **σ-strategy answer**
(single, and *why* — self-adaptation cost) that grounds the whole team's baseline, and a
**well-explained recombination negative** (permutation symmetry) that shows we tried it, measured it,
and understand the mechanism. Both scale cleanly across n (7→20), matching the "extrapolate across
problem size" the brief rewards.
