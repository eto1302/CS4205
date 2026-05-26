# Improvements — Iteration 2: review of iteration 1 + new proposals

Iteration 1 ([improvements_1.md](improvements_1.md), commit `1283baf`)
shipped four cross-cutting EvoPy changes and a `SINGLE_VARIANCE_1_5`
variant. The cross-cutting changes (`σ₀` scaling, Latin-hypercube init,
reflection at bounds) are well-grounded and produce the big gain we're
seeing. Two of the choices — `(μ + λ)` selection and the 1/5 success
rule — directly contradict Schwefel 1995 [BSw95] and lecture 3, and
should be revisited before they become baked into our headline results.

Iteration 2 proposes: keep the iteration-1 wins, revert `(μ + λ)` and
demote the 1/5 variant to an ablation, add an **elitist archive**
(lecture 5) to recover monotone "never lose the best" without poisoning
σ self-adaptation, and add an **adaptive `(μ, λ)` → `(μ + λ)` switch**
(modelled on lecture 5's MO-GOMEA / UHV-GOMEA hybrid) so we have a
clean head-to-head for the presentation.

---

## 1. TL;DR

| § | Iteration-1 change | Verdict for iter-2 |
|---|---|---|
| 1.1 | Problem-scaled σ₀ = 0.3 | ✅ Keep |
| 1.2 | Latin-hypercube init | ✅ Keep |
| 1.3 | Reflection at bounds | ✅ Keep (Bosman & Gallagher 2018 §2.3.2 validates) |
| 1.4 | `(μ + λ)` selection as default | ⚠️ Revert default to `(μ, λ)`; keep `"plus"` as ablation flag |
| 2.1 | 1/5 rule (`SINGLE_VARIANCE_1_5`) | ⚠️ Drop from headline sweep; keep code path for ablation |
| — | `diag(σ)` fix at `individual.py:156` | ✅ Correct — document it explicitly (it's the biggest correctness fix of iter-1 but isn't in `improvements_1.md`) |

| # | Iter-2 new proposal | Source |
|---|---|---|
| 2.1 | Elitist archive (single-objective adaptation) | lecture 5 + Bosman & Thierens 2003 §E |
| 2.2 | Adaptive `(μ, λ)` → `(μ + λ)` switch | lecture 5 reading: UHV-GOMEA hybrid pattern |
| 2.3 | Fix `τ` operator-precedence bug | study-guide R1, BSw95 eq. 6.18 |
| 2.4 | Fix rotation-index bug | study-guide R2, BSw95 eq. 6.21 |
| 2.5 | Restore textbook (μ, λ) selection-pressure ratio | study-guide R3, BSw95 p.11 |
| 2.6 | Add recombination on strategy parameters | study-guide R4, BSw95 p.11 (3rd precondition) |
| 2.7 | Use a more intelligent method for constraint handling | BACK & SCHWEFEL article |
| 2.8 | Try direction dependant Evolution Strategy: `σ_1` for one arbitrary direction in search space, `σ_2` for all other perpendicular directions to the first one, ⚠️ probably not the best strategy for this problem structure | BACK & SCHWEFEL article | 

---

## 2. Iteration 1 — what to keep

- **§1.1 Problem-scaled σ₀ = 0.3** — matches the CMA-ES default and
  removes the dead-population failure mode where σ collapsed to
  `_EPSILON` on generation 1. Keep as-is.
- **§1.2 Latin-hypercube init** — fixes the much larger problem we'd
  hidden inside `warm_start=zeros + std=1`: bounds-clipping at
  `evopy.py:127` was resampling ~half of all coordinates uniformly,
  which collapsed the first-generation population in unpredictable
  ways. LHS is the right answer here. Keep.
- **§1.3 Reflection at bounds** — directly validated by Bosman &
  Gallagher 2018 §2.3.2 on the CiaS problem specifically:
  random-resample (RR) was destroying the σ-adaptation signal near
  edges, exactly where the CiaS optimum lives. Their Fig. 4 shows BR
  (boundary repair / reflection) substantially outperforming RR. Keep.
- **`diag(σ)` fix at `individual.py:156`** — this is the single most
  important correctness fix in iteration 1. The line *was*
  `new_genotype = self.genotype + T @ self.random.randn(self.length)`
  — missing the `diag(σ)` scaling that BSw95 eq. 6.19 requires. Without
  it, FULL_VARIANCE was effectively random search: a 5-seed smoke test
  at `n=7` with 20k evals shows median best 0.368 → 0.481 (+31%) once
  the fix is applied. This should get its own subsection in
  `improvements_1.md` rather than landing only in code.

---

## 3. Iteration 1 — what to revise

### 3.1 Revert `(μ + λ)` to `(μ, λ)` default

Ivan's §1.4 motivates `(μ + λ)`:

> "The best individual ever seen is guaranteed to remain in the
> population unless a strictly better one is found … the best-fitness
> trace becomes monotone — no more regressions."

The motivation is right; the mechanism has costs that BSw95 §6.4 p.11
spells out **explicitly**:

> "Though it offers some theoretical advantage … this minor
> modification has the serious disadvantage that the **self-adaptation
> of strategy parameters is hindered in working effectively, because
> misadapted strategy parameters may survive for a relatively large
> number of generations**. Furthermore, the (μ+λ)-selection mechanism
> fails in case of dynamically changing environments, and it tends to
> emphasize on local rather than global search properties. **For these
> reasons, modern evolution strategies use (μ,λ)-selection, normally.**"

Lecture 3 (Notes.md lines 1066-1068) is identical in spirit:

> "Modern ES use (μ, λ)."

CiaS makes the trade-off *worse*, not better. The fitness landscape has
broad plateaus (only the *binding* pair contributes to fitness;
all other pair-moves are silent — Bosman & Gallagher §3). On a plateau
no fitness-based filter discriminates between σ values, so under
`(μ + λ)` an individual with a misadapted σ can survive arbitrarily
many generations. `(μ, λ)` removes parents every generation, so a
silent-on-plateau bad-σ individual can't accumulate weight.

Monotone fitness traces are valuable for plotting, but they're a
*plotting* concern, not an *algorithmic* one. We can recover the
monotone curve from `(μ, λ)` data by plotting `running_max(best_fitness)`
in `plot_results.py` (one-line change) instead of breaking the ES.

**Recommendation:** `selection_scheme="comma"` as the default; keep
`"plus"` as an ablation flag so we can still run the comparison.

### 3.2 Drop `SINGLE_VARIANCE_1_5` from the headline sweep

Ivan's §2.1 introduces Rechenberg's 1/5 rule as a "smoother,
deterministic" alternative to per-individual log-normal σ adaptation.
The classical literature is clear that the 1/5 rule is *theoretically
derived for the (1+1)-ES only*. BSw95 §6.3 p.7:

> "Self-adaptation as used in the (μ,λ)-strategy **definitely does not
> work in a (μ+1)-strategy**, and **it is also not clear how the
> 1/5-success rule might be applied in the (μ+1)-case, because the
> theoretical derivation only holds for the single parent strategy.**"

Lecture 3 (Notes.md line 951):

> "The 1/5-success rule (used in the (1+1)-ES of §6.2) has severe
> disadvantages — too rigid, requires elitism, doesn't generalize to
> multi-modal landscapes."

Our own [`groupwork-notes/study-guide.md`](../../../../groupwork-notes/study-guide.md)
§3.4 expands on the practical failure mode:

> "The 1/5 rule decays σ aggressively when the local topology stops
> giving 1/5 successes — which happens not only when you have
> converged but also when you are stuck on a ridge. Premature
> stagnation is common."

Ivan's own validation table backs up the prediction:

| n | runs | Baseline gap | 1/5-rule gap |
|---|---|---|---|
| 5 | 1 | 0.68 % | 0.52 % |
| 8 | **3** | **3.17 %** | **5.04 %** |

At the only multi-run datapoint, the 1/5 rule is **1.6× worse** than
the baseline. The framing in `improvements_1.md` reads it as "possibly
noise from only 3 runs, possibly a real signal that per-individual σ
helps on the harder, more multimodal n=8 landscape." BSw95 + lecture 3
predict exactly this regression *theoretically*, not "possibly".

CiaS makes it specifically worse: binding-pair plateaus mean "strict
improvement" fires only when the binding pair itself moves. The
population-level success rate is biased low (most mutations to
non-binding circles look like no-op), so the rule will systematically
contract σ even when σ is already correct.

**Recommendation:** keep the `SINGLE_VARIANCE_1_5` enum and code so we
can run it as an ablation ("we tried this, here's why it loses"), but
exclude it from the headline benchmark sweep and from the V0 → V2x
comparison table in §5.

---

## 4. Iteration 2 — new proposals

### 4.1 Elitist archive (instead of `(μ + λ)`)

Iteration 1's §1.4 had the right *goal* — don't ever lose the best
individual we've seen — and the wrong *mechanism*. The right mechanism
is lecture 5's **elitist archive**, adapted from MOEA to our
single-objective setting.

[`lectures/lecture-5/concepts/Elitist Archive.md`](../../../../lectures/lecture-5/concepts/Elitist%20Archive.md)
defines it (pp. 9-12):

> "A side-pocket set of non-dominated solutions kept *outside* the
> population so that **true elitism** is preserved across generations,
> even when the population update would otherwise lose good solutions."

Bosman & Thierens 2003
([`Reading_Material_The_balance_between.pdf`](../../../../lectures/lecture-5/Reading_Material_The_balance_between.pdf),
§E pp. 729-770):

> "In the use of elitism, the best solutions of the current generation
> are copied into the next generation. Alternatively, an external
> archive of a predefined maximum size na may be used … this **twofold
> elitism** corresponds directly to the twofold multi-objective goal."

**Single-objective CiaS adaptation:**

- Maintain a separate top-K store (K = 5 is fine for CiaS) of the
  highest-fitness individuals ever seen.
- The archive is **not used for reproduction**. Children are still
  drawn purely from the `(μ, λ)` parent pool, so the σ self-adaptation
  machinery is untouched.
- The archive *is* used for: the final returned solution, plotting the
  monotone "best so far" curve, and (optional) seeding a restart.

This gets us:
- "Never lose the best" (the iteration-1 §1.4 goal).
- Untouched `(μ, λ)` self-adaptation (BSw95-compliant).
- Monotone trace for plotting (the §1.4 visual benefit).

**Implementation sketch** (~20 lines in `evopy.py`):

```python
# in EvoPy.__init__
self.archive_size = archive_size      # new kwarg, default 5
self.archive = []                     # list of (fitness, genotype)

# inside run(), after each generation's best is computed
def _update_archive(self, best):
    self.archive.append((best.fitness, best.genotype.copy()))
    self.archive.sort(reverse=self.maximize, key=lambda t: t[0])
    del self.archive[self.archive_size:]

# at end of run()
return max(self.archive, key=lambda t: t[0])[1] if self.maximize \
       else min(self.archive, key=lambda t: t[0])[1]
```

Effort: easy bolt-on, ~20 lines.

### 4.2 Adaptive `(μ, λ)` → `(μ + λ)` switch (for the presentation)

To answer "which selection is best for CiaS?" we should run both, plus
an intelligent combination. Lecture 5's MO-GOMEA / UHV-GOMEA hybrid is
exactly the architectural pattern
([`Reading_Material_Uncrowded_Hypervolume-based.pdf`](../../../../lectures/lecture-5/Reading_Material_Uncrowded_Hypervolume-based.pdf)):

> "We construct a simple hybrid approach where we initially run
> MO-GOMEA, which we terminate when it stagnates … We then switch to
> UHV-GOMEA-Lm starting from the elitist archive E that MO-GOMEA
> obtained so far."

Transfer to our ES:

- **Phase A — `(μ, λ)`**: run with full self-adaptation until
  *stagnation* (no improvement in `best_archive_fitness` for K
  consecutive generations; K = 20 is a reasonable starting value).
  This is the "explore broadly + let σ adapt to the landscape" phase.
- **Phase B — `(μ + λ)`**: once stagnated, switch to elitist
  selection. σ continues its log-normal update; the rationale for
  switching is that by this point σ has converged to the appropriate
  scale, so the BSw95 misadapted-σ-survival concern is much smaller.
  This is the "exploit a known-good local basin" phase.

The elitist archive from §4.1 is shared between the phases — it gives
the stagnation signal *and* preserves the best solution across the
switch.

**Falsifiable hypothesis for the presentation:** hybrid > pure `(μ, λ)`
> pure `(μ + λ)` on CiaS at fixed budget. Run all three on
`n ∈ {7, 10, 15, 20}` with 25 seeds; compare via the existing
`summary.csv` SR/ERT/median-final-fitness columns. Clean
"we-tested-both-and-here's-what-won" story for the defense.

**Implementation sketch:** add `selection_scheme="hybrid"` option in
`evopy.__init__`; ~15 lines of bookkeeping in `run()` (stagnation
counter + scheme switch); one extra hyperparameter
`stagnation_threshold_generations` (default 20). Effort: medium
retrofit, ~30 lines, shares code with §4.1.

### 4.3 Fix the two outstanding `individual.py` bugs

Both are documented in
[`study-guide.md`](../../../../groupwork-notes/study-guide.md) §5
(R1 and R2) and are *correctness* fixes — not algorithm improvements.
Until they're fixed, MULTIPLE_VARIANCE and FULL_VARIANCE numbers aren't
honest baselines.

- **R1: `τ` operator precedence** at `individual.py:89, 106`. Code
  computes `np.sqrt(1 / 2 * np.sqrt(self.length))` which Python
  evaluates as `sqrt(sqrt(n)/2)`. BSw95 eq. 6.18 specifies
  `1 / sqrt(2 * sqrt(n))`. At n = 20 (individual_length = 40) the
  current code overshoots by **a factor of ~4.5×**. Single-paren fix:
  `1 / np.sqrt(2 * np.sqrt(self.length))`.
- **R2: rotation-index map** at `individual.py:119`. The formula
  `int((2 * self.length - p) * (p + 1) / 2 - 2 * self.length + q)`
  doesn't match BSw95 eq. 6.21 — index 0 is never used and one index
  is used twice for n = 4. Affects only FULL_VARIANCE.

### 4.4 Restore textbook `(μ, λ)` selection-pressure ratio

`main.py` currently uses `population_size=30` and `num_children=10`.
EvoPy's semantics make each parent produce `num_children` offspring,
so λ = 30 × 10 = 300, μ = 30. That's λ/μ = 10, which is roughly the
canonical ~7. But `benchmark.py` uses `num_children=7`, giving
λ = 210, μ = 30, λ/μ = 7 — exactly the textbook ratio.

The issue is that `main.py` and `benchmark.py` disagree on `num_children`,
and Ivan's `benchmark_Cala.py` doesn't standardize either. Proposal:
fix `main.py` to match `benchmark.py` (μ = 30, λ = 210) so all entry
points use the BSw95-recommended setting.

BSw95 p.11 lists this as the second of three preconditions for
self-adaptation:

> "not too strong selective pressure (i.e., μ has to be clearly larger
> than one)"

We satisfy this; the remaining concern is just consistency across
entry points.

### 4.5 Add recombination on strategy parameters

Third BSw95 precondition for self-adaptation (p.11):

> "recombination on strategy parameters"

Currently `evopy.py:91-92` creates children by `parent.reproduce()`
from a single parent — no mixing. BSw95 p.10 footnote 9 recommends:

- **Discrete recombination on `x`** — each component independently
  picked from one of two parents.
- **Intermediary recombination on `σ`** — component-wise average of
  two parents' σ values.
- **No recombination on `α`** (rotation angles).

Effort: medium retrofit, ~30 lines (new `_make_child` helper +
single-line change in main loop).

### 4.6 Improve Constraint Handling 

Current algorithm uses a random repair strategy, in individual.py, the same pattern appears after generating `new_genotype`, infeasible alleles are repaired in-place by resampling uniformly from the valid range `[bounds[0], bounds[1]]` :

```python

oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
new_genotype[oob_indices] = self.random.uniform(
    self.bounds[0], self.bounds[1], size=np.count_nonzero(oob_indices))

```
Its main weakness is that repaired alleles lose any directional information from the mutation step, a value that mutated slightly past the boundary is treated the same as one that overshot massively, both getting replaced with a completely random value within bounds.

It is proposed then a better alternative such as Clipping: clip out-of-bounds values to the nearest boundary

Example of implementation:

```python
new_genotype = np.clip(new_genotype, self.bounds[0], self.bounds[1])
```
This preserves the direction of the mutation, which random repair throws away. A circle that mutated slightly past the wall gets pushed back to the wall, not teleported somewhere random.

### 4.7 Only 2 std deviations: direction dependant search

In the paper Evolution Strategies I: Variants and their computational implementation Thomas Back1 and Hans-Paul Schwefel, an additional Evolution Strategy is presented besides the Single Variance, Multiple Variance and Full covariance strategies already present in the algorithm.

This new strategy is direction dependant: `a = (x_1, ..., x_n, σ_1, σ_2, α_1, ..., α_{n-1} )`
Where, in one arbitrary direction of the search space, the search is performed with variance `(σ_1)^2`, whereas `(σ_2)^2` is the variance in all directions perpendicular to the first one. 

the standard deviations `σ_1` and `σ_2`, determine the relation of the lengths of the main axes of the hyperellipsoid,
and `α_{12}` represents the rotation angle of the hyperellipsoid. In the general case of correlated mutations, the mutation hyperellipsoid may align itself arbitrarily in the n-dimensional search space.

Why would this Strategy would offer an improvement?

This strategy would be worth trying on problems where:

* The landscape has one dominant ridge or valley
* Full Variance is too expensive (very high n)
* We want more expressiveness than Multiple Variance without the O(n²) cost of Full Variance.

However it is worth to mention that Circles in a Square does not necessarely adapt well with this strategy since each circle repels all others equally in all directions. The useful correlations in the search space involve pairs of circle coordinates (x_i, y_i together), not a single global preferred direction.

---

## 5. Proposed presentation benchmark suite

A single comparison the team can show, with all variants run on the
same `n ∈ {7, 10, 15, 20}` × 25 seeds × 100k evals grid:

| Variant | Selection | Init | Bugs fixed | Archive | Recomb |
|---|---|---|---|---|---|
| V0 baseline | `(μ, μ)` ratio bug | warm_start=0 (random) | none | no | no |
| V1 iter-1 (Ivan) | `(μ + λ)` | LHS, σ₀=0.3, reflect | `diag(σ)` only | no | no |
| V2a iter-2 fixes | `(μ, λ)` | (same as V1) | `+ τ + rotation` | no | no |
| V2b iter-2 archive | `(μ, λ)` | (same) | (same as V2a) | **K=5** | no |
| V2c iter-2 hybrid | `(μ, λ) → (μ + λ)` | (same) | (same) | **K=5** | no |
| V2d iter-2 full | `(μ, λ) → (μ + λ)` | (same) | (same) | **K=5** | **yes** |

Headline plot: 6-row × 4-column grid (variants × n) of median ± IQR
convergence curves with the Packomania reference line. Pattern reuses
the existing `plot_random_vs_cluster()` skeleton in `plot_results.py` —
same code shape, different facet variable.

Secondary plot: SR@1e-2, SR@1e-3, ERT vs `n` per variant (bar chart or
heatmap). Lets us claim "iteration 2 improves success rate from X% to
Y% at the strictest tolerance the algorithm reaches".

---

## 6. Chat message draft

```
heads up — wrote up an iteration-2 review in
Algorithms/EvolutionStrategyPython/improvements/improvements_2.md

short version:
- ivan's σ₀ scaling, LHS init, and reflection-at-bounds are clear wins,
  keep them. the FULL_VARIANCE diag(σ) fix at individual.py:156 is the
  single biggest correctness fix of iter-1 and we should call it out
  explicitly (it's in his code but not in his doc).
- two things i think we should revisit before they get baked in:
  (a) the (μ+λ) default — BSw95 p.11 is pretty unambiguous that "modern
      ES use (μ, λ), normally" and lists three concrete reasons; CiaS
      plateaus make the misadapted-σ-survival problem worse, not better.
  (b) the 1/5 rule variant — BSw95 §6.3 p.7 says the derivation "only
      holds for the single parent strategy". Ivan's own n=8 table
      already shows it 1.6× worse than baseline.
- proposed iter-2 additions for the presentation:
  - elitist archive (lecture 5) — gets us "never lose the best" without
    poisoning σ self-adaptation. Replaces (μ+λ) cleanly.
  - adaptive (μ, λ) → (μ + λ) switch (modelled on lecture 5's MO-GOMEA /
    UHV-GOMEA hybrid) — gives us a clean head-to-head: pure comma vs
    pure plus vs hybrid, all three in one figure.
  - fix the remaining τ + rotation bugs (study-guide R1+R2).
  - add recombination (BSw95's 3rd precondition for self-adaptation).

let's discuss wednesday — happy to be wrong on any of this, the
critique is grounded in the lecture notes + Schwefel paper so worth
arguing through together.
```
