# WP3 — Constraint Handling (repair modes for out-of-bounds alleles)

## What this work package does

After mutation, a circle centre coordinate can land outside `[0, 1]`.
The original code repaired this by resampling the offending allele from
`uniform(0, 1)` — discarding everything the mutation step just computed.
WP3 replaces that with two better alternatives and wires them into the
OFAT pipeline as a single new kwarg `repair=`.

---

## Background: why the original repair hurts CiaS

The CiaS fitness landscape has a structural property that makes the original
repair particularly harmful: **optimal packings always place circle centres on
or very close to the boundary**. This means the population converges into a
region where boundary violations happen constantly. Every time a coordinate
overshoots, the original repair teleports it to a random interior point —
far from the parent, far from the boundary, and useless for selection.

This has a second-order effect on self-adaptation. The step size σ is updated
based on how often children improve over parents. When boundary violations
replace genuine mutation steps with random noise, the σ feedback signal is
corrupted: the ES thinks children are failing because σ is too large, but
really they are failing because the repair destroyed the step. The result is
that σ shrinks prematurely and the ES stalls.

---

## The three repair modes

| Mode | What it does | Preserves direction | Preserves magnitude |
|---|---|---|---|
| `"random"` | Resample OOB allele from `uniform(lo, hi)` | ✗ | ✗ |
| `"clip"` | Clamp to nearest boundary (`np.clip`) | ✓ | Partial (capped) |
| `"reflect"` | Tent-map fold back into `[lo, hi]` | ✓ | ✓ |

**`"random"`** is the original behaviour and the OFAT baseline. It is kept as
the default so the change is a strict no-op when `repair=` is not passed.

**`"clip"`** pushes a coordinate that mutated slightly past the wall back to
the wall. Simple, fast, and already better than random-repair because selection
can still tell apart children that barely crossed the boundary from those that
stayed inside.

**`"reflect"`** is the tent-map / billiard-ball rule. A step of `+δ` past the
upper wall lands at `hi − δ` instead. For example, a coordinate that mutated
from `0.95` to `1.08` lands at `0.92`. The full mutation magnitude is preserved
and only the direction perpendicular to the wall is negated. This is the
theoretically preferred mode for CiaS: fine exploitation near the boundary
continues unimpeded right up to the optimum.

---

## Files changed

### `ES/evopy/individual.py`

**What changed and where:**

Three separate inline repair blocks existed — one in each `_reproduce_*`
method. Each looked like this:

```python
# BEFORE (original, in all three _reproduce_* methods)
oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
new_genotype[oob_indices] = self.random.uniform(
    self.bounds[0], self.bounds[1], size=np.count_nonzero(oob_indices))
```

All three blocks were removed and replaced by a single module-level function
`_repair(genotype, lo, hi, mode, rng)` defined at the top of the file:

```python
# AFTER — one function, three modes dispatched by string
def _repair(genotype, lo, hi, mode, rng):
    if mode == "clip":
        return np.clip(genotype, lo, hi)
    if mode == "reflect":
        span = hi - lo
        v = (genotype - lo) % (2.0 * span)
        return np.where(v > span, 2.0 * span - v, v) + lo
    # "random" — original behaviour
    oob = (genotype < lo) | (genotype > hi)
    n_oob = int(np.count_nonzero(oob))
    if n_oob:
        genotype = genotype.copy()
        genotype[oob] = rng.uniform(lo, hi, size=n_oob)
    return genotype
```

Each `_reproduce_*` method now calls `_repair` in place of the old inline block:

```python
new_genotype = _repair(new_genotype, self.bounds[0], self.bounds[1],
                       self.repair, self.random)
```

**`repair` is stored on the instance and forwarded to every child.**
This is the critical part. `Individual.__init__` gains a `repair="random"`
parameter which is stored as `self.repair`. Every `Individual(...)` constructor
call inside the three `_reproduce_*` methods passes `repair=self.repair`.
Without this, children revert to `"random"` silently after generation 0 — the
README's warned gotcha.

```python
# Each _reproduce_* method ends with:
return Individual(..., repair=self.repair)   # ← propagates through all generations
```

**Summary of changes in `individual.py`:**

| What | Where |
|---|---|
| Added `_repair()` module-level function | Top of file, before the class |
| Added `_REPAIR_MODES` frozenset for validation | Top of file |
| Added `repair="random"` parameter to `__init__` | `Individual.__init__` signature |
| Store `self.repair = repair` | `Individual.__init__` body |
| Replace inline oob block with `_repair(...)` call | `_reproduce_single_variance` |
| Replace inline oob block with `_repair(...)` call | `_reproduce_multiple_variance` |
| Replace inline oob block with `_repair(...)` call | `_reproduce_full_variance` |
| Pass `repair=self.repair` to returned `Individual` | All three `_reproduce_*` methods |

---

### `ES/evopy/evopy.py`

**What changed and where:**

One new kwarg added to `EvoPy.__init__`:

```python
# BEFORE
def __init__(self, ..., bounds=None):

# AFTER
def __init__(self, ..., bounds=None, repair="random"):
```

Stored on the instance:

```python
self.repair = repair
```

Passed to every `Individual` constructed in `_init_population`:

```python
# BEFORE
Individual(parameters, self.strategy, strategy_parameters,
           random_seed=self.random, bounds=self.bounds)

# AFTER
Individual(parameters, self.strategy, strategy_parameters,
           random_seed=self.random, bounds=self.bounds,
           repair=self.repair)     # ← threads the mode down to the population
```

The initialisation population itself always uses `"random"` repair regardless
of the kwarg. At initialisation there is no mutation step to preserve, so all
three modes are equivalent — the inline random-repair block in `_init_population`
is left unchanged.

**Summary of changes in `evopy.py`:**

| What | Where |
|---|---|
| Added `repair="random"` to `__init__` signature | `EvoPy.__init__` last parameter |
| Store `self.repair = repair` | `EvoPy.__init__` body |
| Pass `repair=self.repair` when building population | `_init_population` |

---

### `ofat_benchmark.py`

**What changed and where:**

Two lines uncommented / added to the `TREATMENTS` list:

```python
# BEFORE
TREATMENTS = [
    ("baseline",  "WP1", {}),
    ("B-no_lhs",  "WP1", {"init": "uniform"}),
    # ("B-clip",   "WP3", {"repair": "clip"}),    ← commented out
    ...
]

# AFTER
TREATMENTS = [
    ("baseline",  "WP1", {}),
    ("B-no_lhs",  "WP1", {"init": "uniform"}),
    ("B+repair_clip",    "WP3", {"repair": "clip"}),      # ← arm 1
    ("B+repair_reflect", "WP3", {"repair": "reflect"}),   # ← arm 2
    ...
]
```

No other changes. The `repair` kwarg flows into `EvoPy` automatically because
`run_one` does `kwargs.update(overrides)` and then passes `**kwargs` to `EvoPy`.

Optionally, add `repair` as a logged column so it is explicit in the CSV:

```python
# In run_one, add to the row dict:
"repair": kwargs.get("repair", "random"),

# In main, add to the fields list:
fields = [..., "selection_scheme", "repair", "final_best", ...]
```

---

## How the OFAT pipeline sees these changes

Each arm is the frozen baseline with exactly one thing different:

```
B+repair_clip    = BASELINE  +  repair="clip"
B+repair_reflect = BASELINE  +  repair="reflect"
```

Both arms are compared against the same `baseline` row in `stats.py`.
Because only `repair` changes, any measured difference in `final_gap` or
`evals_to_*` is attributable to the repair mode alone.

**What to look for in the results:**

- `final_gap` — quality. Expect `reflect` and `clip` to beat `random` on hard
  `n` (15, 20), where the population spends most of the budget near the
  boundary. On easy `n` (7) everyone converges and this metric saturates.
- `evals_to_*` — speed. Expect `reflect` to converge in fewer evaluations on
  `n ≥ 10`, where optimal packings are boundary-heavy. The σ self-adaptation
  receives a cleaner feedback signal when steps are preserved rather than
  discarded.
- A12 > 0.5 and p < 0.05 together constitute a real result per the WP1 rule.

---

## Running the pipeline

```bash
# Rebase onto the fixed baseline first
git fetch origin
git rebase origin/bugfix/ta-handoff

# Full sweep (25 seeds × n ∈ {7,10,15,20} × 100k evals)
uv run --with numpy ofat_benchmark.py

# Smoke test (fast, just checks plumbing)
WP1_SEEDS=3 WP1_NS=7 WP1_EVALS=4000 uv run --with numpy ofat_benchmark.py

# Statistics
uv run --with scipy --with numpy stats.py

# Forest plot
uv run --with matplotlib --with numpy plot_ofat.py
```

Output files: `results/per_run.csv`, `results/comparisons.csv`,
`plots_wp1/forest_*.png`.
