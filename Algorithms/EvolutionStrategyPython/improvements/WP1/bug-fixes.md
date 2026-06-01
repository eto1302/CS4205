# WP1 — baseline bug fixes (delivered to TA, not presented as improvements)

Branch `bugfix/ta-handoff`. These are **correctness fixes**, not algorithm
improvements: until they land, MULTIPLE_VARIANCE / FULL_VARIANCE numbers and the
25-seed statistics aren't honest. See `improvements_2.md` §4.3–§4.4 + §6 (WP1).

| # | File:line | Bug | Fix |
|---|-----------|-----|-----|
| 1 | `main.py` `run_evolution_strategies` (EvoPy default `num_children=1`) | **No selection pressure.** No `num_children` passed → default 1 → λ = μ·1 = μ, a degenerate **(μ,μ)-ES**: every child survives, so selection does nothing — "the algo is currently doing nothing … 0 selection pressure" (Leo, WhatsApp 2026-05-20 17:08; formalised in `groupwork-notes/study-guide.md` §3.6/§5). | `num_children=7` in `main.py` → λ=210, λ/μ=7 (BSw95 reference ratio); matches `benchmark.py`. |
| 2 | `individual.py` `_reproduce_multiple_variance` / `_reproduce_full_variance` | local learning rate `np.sqrt(1/2 * np.sqrt(L))` = sqrt(0.5*sqrt(L)), operator-precedence wrong (BSw95 eq. 6.18 wants `1/sqrt(2*sqrt(L))`); overshoots x3.7 at n=7, x6.3 at n=20 | `1 / np.sqrt(2 * np.sqrt(self.length))` |
| 3 | `individual.py` `_reproduce_full_variance` rotation loop | angle index `int((2L-p)(p+1)/2 - 2L + q)` → for L=4 gives `[-3,-2,-1,1,2,4]` (negatives wrap, index 0 unused, 3 skipped) | `p*(2L - p - 1)//2 + (q - p - 1)` → clean bijection `[0..L(L-1)/2-1]` over (p,q) lexicographic order |
| 4 | `individual.py` `_reproduce_multiple_variance` / `_reproduce_full_variance` returns | child created without `random_seed=self.random` → falls back to numpy's **global** RNG (`utils/random.py` returns `np.random.mtrand._rand` when seed is None) → MULTIPLE/FULL not seed-reproducible from gen 1 | pass `random_seed=self.random` to the child |

**Not a bug, deliberately left alone:** the default `selection_scheme="plus"`
((mu+lambda)) is a *feature*, not a defect. Whether (mu,lambda) or (mu+lambda)
is better for CiaS is **WP2's comparison axis**, not a WP1 correctness fix — so
WP1 does not touch the default. (An earlier draft wrongly listed this as a bug;
the real selection-related defect was the *pressure* (#1), not the *scheme*.)

## Verification

Smoke test, `n=7`, 60 gens, `num_children=7`, `np.seterr(all='raise')`
(benchmark strictness), same seed run twice per strategy:

```
SINGLE_VARIANCE    ok | seed-reproducible=True | best_min_dist=0.5256
MULTIPLE_VARIANCE  ok | seed-reproducible=True | best_min_dist=0.4573
FULL_VARIANCE      ok | seed-reproducible=True | best_min_dist=0.3172
```

- No `FloatingPointError` (the old x4–6 tau could overflow `np.exp` under
  `seterr(raise)` — see `benchmark-review` I7; resolved by fix #2).
- All three strategies now reproducible for a fixed seed (fix #4; before, only
  SINGLE_VARIANCE was).
- With `num_children=7` there is real selection pressure (fix #1) — the run
  optimises instead of random-walking to the generation cap.

## Note on the baseline / Architecture B

These fixes are baked into the frozen baseline **B** that the OFAT comparison
(see `README.md`) measures every arm against. **B pins SINGLE_VARIANCE**
(changed from FULL_VARIANCE on 2026-06-01 — WP4's σ-ablation showed single wins
at every n; multiple/full are WP4 ablation arms, not the baseline). The
**selection scheme of B** (comma vs plus) is a baseline-definition / WP2
decision, *not* fixed here. The *buggy* V0 numbers, if wanted for the narrative
ladder, are reproducible from the pre-fix commit on `main`.
