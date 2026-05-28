# Constraint Handling Improvements for EvoPy / CiaS

## Background

The Circles-in-a-Square (CiaS) problem asks: _given n unit circles, find the arrangement inside a
1×1 square that maximises the minimum pairwise distance between circle centres._ Every candidate
solution is a flat vector of 2n coordinates, all of which must stay in **[0, 1]** — the box
constraint.

The current EvoPy codebase enforces this constraint with a **random-repair** strategy: after
mutation generates a new genotype, any allele that has left `[0, 1]` is replaced by an
independent `uniform(0, 1)` draw.

```python
# current approach — individual.py (same block appears in all three reproduce methods)
oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
new_genotype[oob_indices] = self.random.uniform(
    self.bounds[0], self.bounds[1],
    size=np.count_nonzero(oob_indices)
)
```

This works well enough as a correctness guarantee, but it discards structural information that
the mutation step just computed. The two techniques described below are drop-in replacements that
preserve more of that information.

---

## Why the current approach hurts CiaS in particular

Optimal CiaS packings **always** place circles on or very close to the box boundary (corners and
edges). This means the ES population converges into a region of the search space where boundary
violations are routine. Every generation, a non-trivial fraction of children will have one or
more coordinates that overshot slightly. Random-repair teleports those alleles to a uniformly
random position inside the box — far from the parent — making selection unable to discriminate
between a child that moved a tiny bit and one that landed anywhere at random. The result is that
fitness stagnates and variance is artificially inflated precisely where fine-grained exploitation
is needed most.

---

## Technique 1 — Clipping

### What it does

Clip each out-of-bound allele to the nearest boundary:

```python
# replacement for the random-repair block
new_genotype = np.clip(new_genotype, self.bounds[0], self.bounds[1])
```

### How to apply it

Replace every random-repair block in `individual.py` (three occurrences, one in each
`_reproduce_*` method) with the single `np.clip` call above. The change is identical in all
three methods.

**Before (in `_reproduce_single_variance`):**
```python
new_genotype = self.genotype + self.strategy_parameters[0] * self.random.randn(self.length)
oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
new_genotype[oob_indices] = self.random.uniform(
    self.bounds[0], self.bounds[1], size=np.count_nonzero(oob_indices))
```

**After:**
```python
new_genotype = self.genotype + self.strategy_parameters[0] * self.random.randn(self.length)
new_genotype = np.clip(new_genotype, self.bounds[0], self.bounds[1])
```

Apply the same substitution to `_reproduce_multiple_variance` and `_reproduce_full_variance`.

The same pattern also appears in `evopy.py` inside `_init_population`. You may optionally apply
clipping there too for consistency, though the initialisation step is less performance-critical.

### Why it is better than random-repair for CiaS

| Property | Random-repair | Clipping |
|---|---|---|
| Direction of mutation preserved | ✗ | ✓ |
| Magnitude partially preserved | ✗ | ✓ (capped, not discarded) |
| Implementation complexity | Low | Lower |
| Risk of bias toward boundary | None | Mild — see note below |

A coordinate that mutated only slightly past a wall is moved back to the wall — not scattered
somewhere random. Selection can still tell apart children whose parents were near the boundary:
the child that nearly stayed in place lands on the boundary; the child that overshot massively
also lands on the boundary, but its other alleles will differ. The fitness signal is not
destroyed.

**Note on boundary bias:** Clipping accumulates probability mass at exactly `bounds[0]` and
`bounds[1]`. For CiaS this is actually fine — many optimal circle centres do sit on the boundary
— but for other problems this could cause premature convergence to the edge. Keep this in mind
if you reuse the code on different problem classes.

---

## Technique 2 — Reflection

### What it does

Rather than clamping to the boundary or resampling randomly, reflect the overshoot back into the
domain like a billiard ball bouncing off a wall.

```python
def _reflect(value, lo, hi):
    """Reflect `value` into [lo, hi] using a tent-map / mirror rule."""
    span = hi - lo
    # Shift so the interval starts at 0
    v = value - lo
    # Fold using modulo over 2*span (one full "bounce")
    v = v % (2 * span)
    if v > span:
        v = 2 * span - v
    return v + lo
```

Vectorised NumPy version suitable for direct use in `individual.py`:

```python
def _reflect_into_bounds(genotype, lo, hi):
    span = hi - lo
    v = (genotype - lo) % (2 * span)
    v = np.where(v > span, 2 * span - v, v)
    return v + lo
```

### How to apply it

1. Add the helper function `_reflect_into_bounds` as a module-level function (or a static method
   of `Individual`) in `individual.py`.

2. Replace every random-repair block with a call to the helper:

**Before:**
```python
new_genotype = self.genotype + self.strategy_parameters[0] * self.random.randn(self.length)
oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
new_genotype[oob_indices] = self.random.uniform(
    self.bounds[0], self.bounds[1], size=np.count_nonzero(oob_indices))
```

**After:**
```python
new_genotype = self.genotype + self.strategy_parameters[0] * self.random.randn(self.length)
new_genotype = _reflect_into_bounds(new_genotype, self.bounds[0], self.bounds[1])
```

Apply identically to `_reproduce_multiple_variance` and `_reproduce_full_variance`.

### Why it is better than random-repair for CiaS

Reflection is the most physically motivated repair for a geometric packing problem. When a circle
centre is pushed slightly past a wall by mutation, reflection brings it back to exactly the
mirrored position — the step magnitude σ is fully preserved, only the direction component
perpendicular to the wall is negated.

| Property | Random-repair | Reflection |
|---|---|---|
| Direction of mutation preserved | ✗ | ✓ (reflected, not discarded) |
| Magnitude fully preserved | ✗ | ✓ |
| Boundary density bias | None | None |
| Handles large overshoots | Uniformly random | Folds repeatedly via tent-map |
| Implementation complexity | Low | Moderate |

**Why magnitude preservation matters for ES:** the step-size σ is adapted across generations to
match the curvature of the fitness landscape. If children that cross the boundary have their step
effectively zeroed out (random-repair), the 1/5-success-rule feedback is corrupted — σ is
adapted to a mix of genuine steps and random noise. With reflection, every child is a true
product of the adapted σ, so the self-adaptation mechanism receives clean gradient information
and can converge correctly.

**Why this specifically helps near CiaS optima:** the optimal packings for most n place circles
in corners and along edges. The ES spends the bulk of its budget in this region. With
random-repair, late-stage convergence near the boundary is systematically broken. With
reflection, fine exploitation continues unimpeded right up to the optimum.

---

## Comparison summary

| | Random-repair (current) | Clipping | Reflection |
|---|---|---|---|
| Preserves mutation direction | ✗ | ✓ | ✓ |
| Preserves mutation magnitude | ✗ | Partial | ✓ |
| Unbiased density inside [0,1] | ✓ | ✗ (mass at edges) | ✓ |
| Self-adaptation signal quality | Poor near boundary | Good | Best |
| Code change required | — | 1 line per method | ~10 lines + helper |
| Best suited for CiaS | No | Yes | Yes (preferred) |

For the CiaS problem both alternatives outperform random-repair, with reflection being the
theoretically sounder choice. Clipping is an easy, low-risk first step; reflection is the
recommended final implementation.

---

## Files to modify

| File | What changes |
|---|---|
| `individual.py` | Replace all three random-repair blocks; optionally add `_reflect_into_bounds` helper |
| `evopy.py` | Optionally update `_init_population` for consistency |

No changes are needed to `main.py`, `strategy.py`, `progress_report.py`, or `__init__.py`.
