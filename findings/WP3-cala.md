---
title: "WP3 — Constraint Handling / Repair (Cala)"
subtitle: "Findings guide · random vs clip vs reflect repair of out-of-bounds circles"
owner: "Cala · branch `constraint_handling-improvements`"
status: "findings summary (Leo, updated 2026-06-04) from Cala's FINAL 25-seed single-variance run (merged to main). Local working notes."
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

## Finding — clip & reflect **crush** random repair; clip wins at *every* n

*(Final numbers: 25 seeds, single-variance + random baseline, 100k evals — the run that's now on `main`.)*

![repair bars](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp3_repair.png)

| n | random (baseline) | clip | reflect |
|---|---|---|---|
| 7 | 5.2% | **2.9%** ** | 4.2% (ns) |
| 10 | 13.4% | **6.3%** *** | **8.5%** *** |
| 15 | 61.9% | **14.8%** *** | **17.2%** *** |
| 20 | 64.2% | **17.5%** *** | **22.6%** *** |

![repair forest](courses/CS4205-evolutionary-algorithms/assignments/groupwork/findings/figs/wp3_forest.png)

- **clip is significant at EVERY n** — `**` at n=7 (A12 0.76) and `***` at n≥10, up to
  **A12 = 1.0** at n=20 (clip won every single pairwise comparison; p down to 1.4e-9).
- **reflect is significant at n ≥ 10** (`***`) but **not at n=7** (A12 0.63, p=0.13).
- The effect is **huge** at scale: at n=15/20 clip cuts the gap from ~62–64% to ~15–18%
  (**~4× better**).
- **clip beats reflect everywhere** — clearest at n=7, where clip's small edge is real but
  reflect's isn't. → **clip is the recommended default** (simplest too: one `np.clip`).

> 📈 **What changed at 25 seeds:** the earlier 10-seed run called n=7 "not significant for
> either." With the full 25 seeds, **clip's small n=7 win becomes detectable** (`**`) — a power
> effect, exactly the reason we standardised on 25 seeds. reflect at n=7 stays ns.

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

## ✅ Status — all earlier caveats resolved

This WP is **done and defense-ready**:
- **25 seeds** on the shared single-variance + random baseline (was 10) — CIs are now tight,
  p-values down to 1e-9. ✓
- The stale `FULL_VARIANCE` BASELINE line is **fixed** (single-variance) and the run is **merged
  to `main`**. ✓
- The earlier "**25 seeds breaks single-variance**" worry **did not reproduce** in the final run —
  it ran cleanly at 25 seeds. ✓

Only judgement call left: **clip vs reflect as the headline.** Both are large and significant at
n≥10; clip additionally wins at n=7 and is the simplest (`np.clip`), so **lead with clip**, mention
reflect as the close runner-up.

## How it maps to the assignment

This is a **justified, significant, large** improvement on a core EA front
(constraint handling), with a CiaS-specific mechanism (boundary-seeking optima),
p-values via the shared `stats.py`, and a clean scalability story (the benefit
*grows* with n — exactly the "extrapolate to wider settings" the brief rewards).
