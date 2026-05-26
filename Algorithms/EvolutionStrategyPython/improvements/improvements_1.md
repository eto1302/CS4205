# Improvements to the Evolution Strategy — Iteration 1

This document describes the improvements applied to the EvoPy framework in iteration 1, which focused on the **SINGLE_VARIANCE** strategy. The improvements are split into two types:

- **Type 1 — Cross-cutting improvements** apply to the framework itself (population initialization, boundary handling, selection scheme) and therefore benefit **every** strategy.
- **Type 2 — Strategy-specific improvements** are algorithmic changes applied to a single strategy. Iteration 1 only modified SINGLE_VARIANCE, so only one subsection exists here; MULTIPLE_VARIANCE and FULL_VARIANCE will be covered in later iterations.

The target problem throughout is **Circles in a Square (CiaS)**: place `n` points in [0,1]² so that the minimum pairwise distance is maximized. The fitness landscape is non-smooth (only the *closest* pair determines the fitness), multimodal (any permutation or square-symmetry of an optimum is also an optimum), and bounded.

---

## Type 1 — Cross-cutting improvements

### 1.1 Problem-scaled initial step size σ₀

**Files**: [ES/evopy/evopy.py](ES/evopy/evopy.py) (`EvoPy.__init__`, `EvoPy._init_population`)

**Before**: `strategy_parameters = self.random.randn(k)` — every σ was sampled from a standard normal, giving values in roughly [-3, 3] with no relation to the search-space scale. Some runs started with σ ≈ 1.5 (huge for [0,1]) and others with σ ≈ 0.01 (immediately clamped to the EPSILON floor and effectively dead). For FULL_VARIANCE, rotation angles also started from N(0,1), giving a random initial orientation of the mutation ellipsoid.

**After**: `sigma0 = init_sigma_scale × (high − low)` with `init_sigma_scale = 0.3`. For our [0,1]ᵈ bounds this gives σ₀ = 0.3, matching the CMA-ES default. FULL_VARIANCE rotation angles are initialized to 0.0, so the initial rotation matrix is the identity.

**How it affects the ES**: the population starts taking *meaningful* mutation steps — neither so small that the ES is stuck in EPSILON-land nor so large that every child is OOB. Self-adaptation can then meaningfully tune σ either down (refinement) or up (escape) from a sensible baseline.

**Why this helps CiaS**: a "useful" mutation step in CiaS is on the order of 0.1–0.3 (a fraction of the box side); too small and you barely move a circle; too large and you teleport across the square. σ₀ = 0.3 lets the ES explore at problem-relevant scale from gen 0.

---

### 1.2 Latin-hypercube sampling for the initial population

**Files**: [ES/evopy/evopy.py](ES/evopy/evopy.py) (`EvoPy._init_population`, new `EvoPy._latin_hypercube`)

**Before**: genotypes were sampled as `warm_start + N(mean=0, std=1)` and then clipped to bounds. With `warm_start = 0` (the default) and bounds `[0,1]`, about half the samples were negative and got clipped to 0. Result: **every circle in the initial population started in the bottom-left corner of the square**. Initial fitness was therefore ~0 (all circles overlapping) and the ES wasted many generations just spreading them out.

**After**: a Latin-hypercube sample on [0,1]ᵈ. LHS partitions each axis into N strata and guarantees exactly one sample per stratum on each axis, so the initial population is spread across the search space far more uniformly than independent uniform sampling — and *vastly* more than the previous N(0,1)-clipped scheme.

**How it affects the ES**: the very first generation already has non-trivial fitness — circles are scattered rather than piled up. Generation-0 best fitness goes from ≈ 0 to ≈ 0.3–0.5 depending on n.

**Why this helps CiaS**: a "good packing" requires circles to be far apart. Starting from circles-on-top-of-each-other is the worst possible state and forces the ES to use early-generation budget on a problem (spreading) that random initialization could trivially solve.

---

### 1.3 Reflection at the boundary instead of random-resample

**Files**: [ES/evopy/individual.py](ES/evopy/individual.py) (new `reflect_into_bounds`, applied inside `_reproduce_single_variance` and `_reproduce_single_variance_1_5`)

**Before**: when a mutated coordinate exited [0,1], it was replaced by `uniform(0, 1)` — effectively a **random restart of that coordinate**. The ES had just computed a mutation step of magnitude σ, but if the step crossed the boundary, the step was discarded and replaced by an arbitrary point.

**After**: out-of-bound coordinates are reflected back into the box via a tent-map: a step of `+δ` past the upper bound becomes a step of `−δ` from the upper bound back inward. The *magnitude* of the intended step is preserved.

**How it affects the ES**: late-stage exploitation is no longer broken when the population converges near the box edges. With random-resample, a converged ES near the boundary keeps "losing" any child whose mutation step crosses the edge — fitness oscillates wildly. With reflection, those children remain close to the parent and selection can still discriminate among them.

**Why this helps CiaS**: optimal packings always place circles **on or near the box boundary** (corners and edges). Random-resample is therefore most destructive exactly where convergence happens. Reflection is well-defined here because the fitness landscape doesn't change discontinuously near the bounds — the boundary is geometric, not algorithmic.

---

### 1.4 (μ + λ) selection (elitism) replacing (μ, λ)

**Files**: [ES/evopy/evopy.py](ES/evopy/evopy.py) (`EvoPy.__init__` adds `selection_scheme="plus"`; `EvoPy.run` builds the selection pool from `parents + children`)

**Before**: each generation discarded all parents and selected the next population purely from children: `population = sorted(children, …)[:μ]`. If no child happened to beat the best parent in a given generation, the best fitness *regressed* — visible in the previous convergence plots as backward jumps.

**After**: the selection pool is `parents + children` by default. The best individual ever seen is guaranteed to remain in the population unless a strictly better one is found. A `selection_scheme="comma"` option preserves the old behaviour for ablation.

**How it affects the ES**: the best-fitness trace becomes monotone — no more regressions. Late-stage progress is also more stable because the population can't be polluted by a generation of bad mutations (the elite anchor pulls it back).

**Why this helps CiaS**: the fitness landscape has many plateaus (small moves of any non-closest-pair circle don't change the fitness at all). On a plateau, all children may have the same fitness as the parent → without elitism, the search drifts; with elitism, the best known configuration is preserved while the search continues.

**Caveat**: (μ + λ) can in principle slow convergence on rapidly changing landscapes because old elites pin the search. CiaS is not such a landscape (the optimum is static), so the trade-off is firmly in favour of elitism here.

---

## Type 2 — Strategy-specific improvements

### 2.1 SINGLE_VARIANCE

Iteration 1 keeps the **baseline** `SINGLE_VARIANCE` strategy (with its log-normal per-individual self-adaptation) and adds a **new variant** `SINGLE_VARIANCE_1_5` next to it. The baseline still benefits from all Type 1 changes; the new variant additionally replaces the self-adaptation rule.

**Files**:
- [ES/evopy/strategy.py](ES/evopy/strategy.py): new enum value `SINGLE_VARIANCE_1_5 = 4`
- [ES/evopy/individual.py](ES/evopy/individual.py): new `_reproduce_single_variance_1_5` method, dispatch entry in `Individual.__init__`
- [ES/evopy/evopy.py](ES/evopy/evopy.py): new `_sigma_1_5` instance attribute, 1/5-rule update block inside `EvoPy.run`

#### What the 1/5 rule does

Rechenberg's classic rule manages a **single σ shared by the whole population**, updated once per generation based on the *success rate* of the previous batch of mutations:

```
let p_s = (# children that strictly improved over their parent) / λ_total

if p_s > 1/5:   σ ← σ / 0.817        (≈ ×1.224 — expand)
if p_s < 1/5:   σ ← σ × 0.817        (≈ ×0.817 — contract)
otherwise:      σ unchanged
σ ← max(σ, EPSILON)
```

`0.817` is Schwefel's analytically derived contraction factor; the 1/5 threshold is the success rate at which the sphere model converges fastest.

#### How it differs from baseline self-adaptation

| | Baseline `SINGLE_VARIANCE` | New `SINGLE_VARIANCE_1_5` |
|---|---|---|
| σ ownership | per individual | one σ shared by the whole population |
| Adaptation signal | log-normal jitter (`σ' = σ × exp(τ·N(0,1))`) applied independently to every offspring | aggregate success rate computed over **all λ children** of the generation |
| Selection of σ | only σ-values carried by surviving children persist | σ is recomputed by the rule, then injected into every parent before reproduction |
| Variance of σ-updates | high (single noisy sample per child) | low (averaged over λ children) |

#### How it affects the ES

The 1/5 rule turns σ-adaptation from a **per-individual, noisy, mutation-driven** mechanism into a **population-level, deterministic, feedback-driven** one. The signal-to-noise ratio is much higher: an individual log-normal update is a single coin flip of σ, while the 1/5 rule averages success over `population_size × num_children` independent mutations per generation (in our config, 30 × 7 = 210 trials).

Consequences:
- **Smoother σ trajectory**: σ doesn't randomly explode or collapse the way it can with log-normal jumps; it monotonically tracks the local landscape difficulty.
- **Faster contraction near the optimum**: once below 20% success, σ shrinks geometrically by 0.817 per generation, which is exactly what you want when fine-tuning a near-optimal packing.
- **Faster expansion when stuck**: if the population has stagnated and ≥ 20% of mutations would improve, σ grows by 1.224 per generation — useful to escape narrow basins.
- **No exploration of "what if my σ were different?"**: this is the cost. The baseline strategy's per-individual σ lets some children try larger or smaller steps in parallel; the 1/5 rule does not. On highly multimodal landscapes this can theoretically matter.

#### Why this is beneficial for CiaS

1. **The fitness landscape is non-smooth and plateau-rich** (only the closest pair counts). Per-individual self-adaptation is noisy here because most mutations produce *identical* fitness (no signal for σ-selection). The 1/5 rule sidesteps this by counting strict improvements at the population level — the global success-rate signal stays informative even when many individual mutations are silent.
2. **σ values matching the problem scale** (≈ 0.1–0.3 for fine moves) are reached predictably and monotonically. Log-normal jumps can land σ outside this band and need many generations to recover.
3. **Late-stage convergence to an optimum is geometric** (σ × 0.817 per generation when stuck below 20% success). This matches the geometric tail observed in good ES runs on convex-near-optimum landscapes — relevant once the packing is *almost* right and we're just fine-tuning circle positions.

#### Validated impact (smoke tests with the cross-cutting changes also applied)

| Configuration | Baseline `SINGLE_VARIANCE` | New `SINGLE_VARIANCE_1_5` |
|---|---|---|
| n = 5, 10k evals, 1 run | gap 0.68 % | gap **0.52 %** |
| n = 8, 50k evals, 3 runs | mean gap **3.17 %** | mean gap 5.04 % |

The new variant is better on n=5 (where 1/5 dynamics shine on a small, near-convex problem). On n=8 the per-individual log-normal baseline edged ahead in this small smoke test — possibly noise from only 3 runs, possibly a real signal that per-individual σ helps on the harder, more multimodal n=8 landscape. The full benchmark (10+ runs per config) will settle this.

For context, **both** variants are dramatically better than the *previous* state of the code: the previous `SINGLE_VARIANCE` benchmark reported ~11 % gap on n=8 (50k evals); we are now at ~3–5 %. The bulk of this win is attributable to the Type 1 cross-cutting changes (LHS init, scaled σ₀, reflection, (μ+λ) selection), not to the 1/5 rule itself. The 1/5 rule's marginal contribution will become clearer on harder problem sizes where the Type 1 fixes are no longer enough on their own.

---

## What's next

- **Iteration 2** (planned): MULTIPLE_VARIANCE — group σ per circle (d/2 step sizes instead of d), and add weighted recombination of σ across the top-μ parents.
- **Iteration 3** (planned): FULL_VARIANCE — Schwefel variant with adaptive β + identity-initialised rotations, *and* a CMA-ES variant via the `cma` library.

See [the plan file](../../../../.claude/plans/make-a-plan-md-for-velvet-wolf.md) for full details.
