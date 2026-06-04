---
title: "WP3 — Constraint Handling / Repair (Cala)"
subtitle: "Findings guide · random vs clip vs reflect repair of out-of-bounds circles"
owner: "Cala · branch `constraint_handling-improvements`"
status: "findings summary (Leo, 2026-06-02) from Cala's single-variance 10-seed run. Local working notes."
---

# WP3 — Constraint Handling (repair)

## What Arthur asked for (TA meeting, 2026-05-27)

> *Constraint handling:* move from **random repositioning** to
> **reflection / clipping**. Arthur: "**makes sense, good idea.**"

When a mutated circle lands outside `[0,1]`, the original code **resamples it
uniformly at random** — throwing away the mutation step entirely. WP3 replaces
that with two better repairs and measures them.

## The three repair modes

| mode | what it does to an out-of-bounds coordinate |
|---|---|
| **random** (baseline) | resample uniformly in `[0,1]` — discards direction *and* magnitude |
| **clip** | clamp to the nearest wall (0 or 1) — keeps direction, lands on the boundary |
| **reflect** | bounce back in by the overshoot — keeps direction *and* magnitude |

## Finding — clip & reflect **crush** random repair at large n

![repair bars](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp3_repair.png)

| n | random (baseline) | clip | reflect |
|---|---|---|---|
| 7 | 3.7% | 3.3% (ns) | 4.6% (ns) |
| 10 | 15.3% | **5.4%** ✲ | **7.8%** ✲ |
| 15 | 57.2% | **15.0%** ✲ | **17.2%** ✲ |
| 20 | 64.4% | **17.6%** ✲ | **20.5%** ✲ |

![repair forest](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp3_forest.png)

- At **n ≥ 10 both clip and reflect are highly significant** (forest: filled dots,
  A12 up to **1.0** = won every single pairwise comparison; p down to 1.8e-4).
- The effect is **huge**: at n=15/20 they cut the gap from ~57–64% to ~15–20%
  (3–4× better).
- At **n=7 neither is significant** — that instance is already nearly solved, so
  there's little room to improve (a ceiling effect, not a failure).
- **clip ≈ reflect**, with clip slightly ahead at the largest n.

**Why it works on CiaS (the justification):** optimal packings put circle centres
**on the boundary**. Random repair teleports a circle that nudged past the wall to
a random interior point — destroying the step *and* the σ self-adaptation signal,
right where the optimum lives. Clip/reflect keep the circle at the wall where it
belongs. clip's slight edge: its boundary-attraction is *helpful* here.

## Connection to the baseline (why this is now a clean result)

The shared baseline was deliberately set to **random repair** (the honest
original) — so reflection/clip show up as **measurable WP3 improvements** instead
of being silently baked in. (Reflection used to be hardcoded into single-variance;
that hid its benefit. Now it's credited to WP3, with numbers.) Baseline used here
= single-variance + LHS + (μ,λ) + random repair = the current `main` baseline. ✓

## ⚠️ Caveats

- **10 seeds** (not the framework's 25) — directional findings are clear (A12≈1.0)
  but CIs are wide; bump to 25 for the final numbers.
- n=7 not significant (near-solved) — present clip/reflect as a **large-n** win.
- An earlier full-variance run showed clip even larger and reflect weaker at large
  n; on the current single-variance baseline **clip ≈ reflect**. Recommend clip as
  the default (simplest: one `np.clip`, significant everywhere it matters).
- Her `ofat_benchmark.py` still pins the **stale `FULL_VARIANCE` BASELINE** (drop that line);
  and her "**25 seeds breaks single-variance**" report is **open / not yet root-caused** —
  reproduce it before claiming it's a bug.

> ⚠️ See [AUDIT-inconsistencies.md](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/AUDIT-inconsistencies.md) (items 3, 4, 8) for WP3's row in the
> config matrix and pre-deadline action table.

## How it maps to the assignment

This is a **justified, significant, large** improvement on a core EA front
(constraint handling), with a CiaS-specific mechanism (boundary-seeking optima),
p-values via the shared `stats.py`, and a clean scalability story (the benefit
*grows* with n — exactly the "extrapolate to wider settings" the brief rewards).
