---
title: "WP4 recombination — 100k / 25-seed data note"
subtitle: "Higher-power confirmation of the recombination negative result + a data-quality caveat"
owner: "Leo (filed the data; source run = Agata's `recombination-agata` branch)"
status: "data + plots only — Agata's recombination CODE is NOT merged to main yet (see §3)"
---

# WP4 recombination — 100k / 25-seed run

This adds a **higher-budget, higher-power** version of the recombination ablation
to main, on top of the existing 10-seed × 20k data
(`findings/data/wp4_recomb_per_run.csv`). It does **not** change the conclusion:
**naive coordinate / circle-pair recombination significantly hurts.**

Source: `origin/recombination-agata`,
`benchmark_wp4_results/benchmark_recomb_best_sigma_directed_100k_25seeds_2026-06-05_12-04-37/per_run.csv`.

## Files added

| file | what |
|------|------|
| `data/wp4_recomb_100k_25seeds_per_run.csv` | **raw** per-run data, as committed by Agata (see §1 caveat) |
| `data/wp4_recomb_100k_25seeds_comparisons.csv` | stats over the raw file, **all n** — ⚠️ confounded at n=15/20 (§1) |
| `data/wp4_recomb_100k_25seeds_SINGLE_n7n10_comparisons.csv` | **clean** stats, single-variance only, n=7/10 |
| `figs/wp4_recomb_100k_25seeds_forest.png` | forest, all n — **not** a clean single-variance plot (§1) |
| `figs/wp4_recomb_100k_25seeds_SINGLE_n7n10_forest.png` | **clean** forest, single-variance n=7/10 — the presentable one |

## 1 · ⚠️ Data-quality caveat — the raw file mixes σ-strategies

The raw `per_run.csv` is **not** a clean single-variance OFAT run:

| n | baseline strategy present |
|---|---------------------------|
| 7  | SINGLE (25) **+** MULTIPLE (25) |
| 10 | SINGLE (25) **+** MULTIPLE (25) |
| 15 | **MULTIPLE only** (no single) |
| 20 | **MULTIPLE only** (no single) |

`stats.py` groups arms only by `(treatment, n_circles)` and **ignores the
`strategy` column**, so:

- **n=7/10** → the "baseline" median is a single+multiple blend.
- **n=15/20** → the comparison is silently against a **multiple-variance**
  baseline, not the canonical single-variance B.

So `..._comparisons.csv` / `..._forest.png` (all-n) are **directional only**.
The honest, presentable result is the **`SINGLE_n7n10`** pair.

**To extend cleanly to n=15/20:** rerun just those two cells at single-variance
(baseline + 2 recomb arms, 100k, 25 seeds) — a *partial* run, not the full sweep.

## 2 · Result (clean, single-variance, n=7/10)

| arm | n | base gap | arm gap | effect | A12 | p |
|-----|---|----------|---------|--------|-----|---|
| coordinate  | 7  | 0.052 | 0.44 | −0.39 | 0.0   | 1.4e-9 |
| coordinate  | 10 | 0.13  | 0.55 | −0.41 | 0.062 | 1.2e-7 |
| circle_pair | 7  | 0.052 | 0.46 | −0.41 | 0.0   | 1.4e-9 |
| circle_pair | 10 | 0.13  | 0.53 | −0.40 | 0.086 | 5.6e-7 |

Same direction and magnitude as the 10-seed data, now at 25 seeds / 100k —
recombination loses essentially every paired comparison (A12 ≈ 0). Honest
negative result: *naive positional recombination is disruptive for CiaS
(permutation symmetry).*

## 3 · Integration status — DATA ONLY

This is **data + plots only**. Agata's recombination *code*
(`ES/evopy/recombination.py` + the `recombine` / `recombination_mode` kwargs and
the `run()` hook) is **NOT merged** — her branch is ~84 commits behind main and
`evopy.py` conflicts with the WP2/WP3/WP5 work already on main. So these numbers
are **not reproducible on main** until the code lands too. See `WP4-agata.md` and
the merge-conflict analysis before merging the branch.
