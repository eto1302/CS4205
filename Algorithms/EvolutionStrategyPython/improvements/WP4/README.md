# WP4 — recombination & σ-strategy selection (Agata)

Two sub-studies, both measured with the shared OFAT pipeline (`ofat_benchmark.py`
→ `stats.py` → `plot_ofat.py`). Implementation lives in `ES/evopy/recombination.py`
+ the `recombine` / `recombination_mode` kwargs on `EvoPy`.

## 1 · σ-strategy ablation (single vs multiple vs full)

**Question:** the baseline B is single-variance — does adding σ-complexity
(multiple, full) beat it, and at which n? Arms just change `strategy=`:

```python
("B+sigma_multiple", "WP4", {"strategy": Strategy.MULTIPLE_VARIANCE}),
("B+sigma_full",     "WP4", {"strategy": Strategy.FULL_VARIANCE}),
```

**Result (medium budget, 10 seeds × 20k evals):** **single wins at every n
(7,10,15,20)**, monotonically, no crossover. This is the evidence for pinning
the shared baseline B to single-variance.

> Caveat for the report: full-variance carries ≈820 strategy params at n=20 and
> is the *slowest to converge* — at 20k evals "full is worst" may be partly a
> budget artifact. The "single wins in our budget" conclusion is safe; a 100k
> check is needed before claiming full is *fundamentally* worst.

## 2 · Recombination

**Implemented** (`recombination.py`): discrete recombination on `x`
(`recombination_mode="coordinate"`), a CiaS-symmetry-aware operator that inherits
whole `(xᵢ,yᵢ)` circle-pairs (`"circle_pair"`), and intermediary averaging on σ.
Seeded/reproducible; `recombine=False` is a no-op default.

```python
("B+recomb_coord", "WP4", {"recombine": True, "recombination_mode": "coordinate"}),
("B+recomb_pair",  "WP4", {"recombine": True, "recombination_mode": "circle_pair"}),
```

**Result:** both modes **significantly HURT** (≈10× worse median gap, A12≈0,
p≈1.8e-4) on single-variance. Root cause = **CiaS permutation symmetry**: circle
index `i` is not aligned across parents, so mixing positions scrambles solutions;
`circle_pair` doesn't rescue it. Presented as an **honest negative result**:
*naive positional recombination is disruptive for CiaS.*

## 3 · "Recombine only the best strategy parameter" (Arthur) — DEFERRED

Not implemented. It only makes sense on multiple/full variance (several σ to pick
the best among), which recombination was not run on. **Team-meeting decision**
whether to build it (deadline 2026-06-07). If pursued: it needs (a) the
best-σ-selection code and (b) a full/multiple-variance recombination run, and its
effect must be measured against `B+sigma_full` (strategy held constant), **not**
the single baseline — otherwise strategy and recombination are confounded.

## 4 · ⚠️ stats.py caveat — read before trusting comparisons.csv

`stats.py` compares **every arm only against the row labelled `baseline`**. So:
- σ-ablation arms and recombination-vs-single arms get correct auto p/A12.
- But a "recombination vs B+sigma_full" comparison (the *honest* way to isolate
  recombination's effect at full-variance, if §3 is ever built) is **NOT** computed
  by the pipeline — it needs a manual pairwise Mann-Whitney. Don't read the
  recomb arm's auto-generated row as "recomb effect" if the baseline isn't the
  right reference for it.

## 5 · Integration note

`EvoPy.__init__` + the `run()` children-loop are edited by **both WP4 (recombine)
and WP3 (repair)** — those branches **conflict in `evopy.py`** and need a
hand-merge. Coordinate before merging to main.
