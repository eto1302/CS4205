# WP2 — selection & elitism (what we changed, and how to run it)

Branch: `selection-elitism`. This document explains every **logical** change we
made since branching off `main`, and the practical part — **how to run the new
experiments** (mostly through Cala's benchmark, `benchmark_Cala.py`).

WP2 implements the two bullets from `improvements/improvements_2.md` §6:

1. **`(μ, λ)` vs `(μ + λ)` selection**, head-to-head, with the §3.1 justification.
2. **Elitist archive** (§4.1) in two flavours — *bookkeeping* and *bookkeeping +
   reintroduction* — and the ability to cross archive × selection to find the
   best combination.

Everything is a **no-op-by-default toggle**: with the defaults, `EvoPy` behaves
exactly as before, so no other WP's runs change.

---

## 1 · The two selection schemes — `(μ, λ)` vs `(μ + λ)`

This already existed in `EvoPy` as `selection_scheme` and needed no new code; we
made it the *comparison axis* and wrote down *why* one is preferred.

- `selection_scheme="comma"` → **`(μ, λ)`**: parents are discarded every
  generation; the next population is the best `μ` of the **children only**.
- `selection_scheme="plus"` → **`(μ + λ)`**: the next population is the best `μ`
  of **parents + children** (elites can survive indefinitely).

In code (`ES/evopy/evopy.py`, selection step in `run()`):

```python
pool = (parents + children) if self.selection_scheme == "plus" else children
population = sorted(pool, reverse=self.maximize, key=lambda ind: ind.fitness)[:self.population_size]
```

**Why `(μ, λ)` is the recommended scheme (§3.1).** BSw95 §6.4 warns that under
`(μ + λ)` a *misadapted σ can survive for many generations*, which hinders
self-adaptation; on CiaS this is worse, not better, because the landscape has
broad plateaus where no fitness signal discriminates σ values. So `(μ, λ)` is the
**principled choice** — it's what our OFAT baseline pins (`ofat_benchmark.py`
`BASELINE`) — and we treat `(μ + λ)` as the thing we *measure against* it, not a
blind pick. (The "monotone best-fitness curve" that `(μ + λ)` gives for free is a
*plotting* benefit, which the archive below recovers without breaking
self-adaptation.)

> Note: `EvoPy`'s constructor default is still `selection_scheme="plus"` — we
> deliberately did **not** change it, so any other caller is unaffected. Our
> experiments always pass the scheme explicitly (`comma` is the reference arm).

---

## 2 · The elitist archive (§4.1) — three modes

New `EvoPy` kwargs (`ES/evopy/evopy.py:26-27`):

| kwarg | default | meaning |
| --- | --- | --- |
| `archive_mode` | `"off"` | `"off"` / `"bookkeeping"` / `"reintroduction"` |
| `archive_size` | `5` | `K` — how many elites the archive keeps |
| `stagnation_generations` | `20` | for reintroduction: gens without archive-best improvement before re-injecting |

The archive is a **top-`K` side store of the best individuals ever seen**, kept
*outside* the population (lecture-5 elitist-archive idea, adapted to our
single-objective setting). It is updated each generation from the new population
and trimmed to `K` (`_update_archive`), and it is **never used for
reproduction** — children still come purely from the `(μ,λ)`/`(μ+λ)` parent pool,
so the σ self-adaptation machinery is untouched.

### `"off"` — no archive (original behaviour)
Returns the final *population* best, exactly as before branching. This is the
reference arm: comparing it against the two archive modes shows whether the
algorithm *actually uses* the archive (Arthur's question).

### `"bookkeeping"` — never lose the best (§4.1)
Maintains the top-`K` store and uses it **only** for the *returned* solution and
the *reported* best-so-far. **The search itself is byte-for-byte identical to
`"off"`.** We could verify this because the archive stores **clones** that share
the RNG and therefore draw **zero** random numbers:

> `Individual.clone()` (`ES/evopy/individual.py`) copies genotype + σ-parameters
> + cached fitness and passes the *existing* RNG through (like `reproduce()`
> does), so cloning never advances the random stream. Empirically,
> bookkeeping's returned fitness == the running-max of `off`'s population-best
> trace, confirming the search is unchanged.

This is the §1.4 goal ("never lose the best") and the monotone trace, **without**
the BSw95 self-adaptation cost of `(μ + λ)`.

### `"reintroduction"` — backup population / diversity preservation
Everything bookkeeping does, **plus**: when the archive-best has not improved for
`stagnation_generations` consecutive generations, the archived elites are
**re-injected into the population**, replacing its worst members
(`_maybe_reintroduce`). This restores good genetic material that `(μ, λ)` may have
dropped, then the counter resets. Unlike the other two modes, this one **does**
change the search trajectory.

Helper methods added to `EvoPy`: `_is_better`, `_update_archive`,
`_maybe_reintroduce`. New attribute `self.archive` (+ stagnation trackers). When
`archive_mode == "off"` all of this is skipped and `self.archive` stays empty.

---

## 3 · Stats path (OFAT) — `ofat_benchmark.py` + `stats.py`

For the significance-tested verdict against the frozen baseline (WP1's pipeline),
we enabled three WP2 treatments in the OFAT registry (`ofat_benchmark.py`). The
baseline already *is* the `(μ,λ)` / no-archive arm, so each line below changes
exactly one factor:

```python
("B+plus",         "WP2", {"selection_scheme": "plus"}),        # (μ+λ) vs (μ,λ) baseline (§3.1)
("B+arch_book",    "WP2", {"archive_mode": "bookkeeping"}),     # elitist archive, bookkeeping (§4.1)
("B+arch_reintro", "WP2", {"archive_mode": "reintroduction"}),  # archive + reintroduction
```

`per_run.csv` now also records an `archive_mode` column. Run the usual three
commands; `stats.py` produces the Mann–Whitney p-value + A12 for each arm vs the
baseline:

```bash
uv run --with numpy ofat_benchmark.py              # -> results/per_run.csv
uv run --with scipy --with numpy stats.py          # -> results/comparisons.csv
uv run --with matplotlib --with numpy plot_ofat.py # -> forest plot
```

> OFAT varies **one** factor at a time, so the archive arms here all sit on the
> `(μ,λ)` baseline. The full **archive × selection factorial** lives in Cala's
> benchmark (below).

---

## 4 · What we changed in Cala's benchmark (`benchmark_Cala.py`)

Cala's benchmark swept the σ-strategy but never varied selection or archive. We
made both **first-class swept axes** so we can run the full factorial and see
which *combination* wins.

**New `Benchmark(...)` constructor arguments:**

| argument | default | meaning |
| --- | --- | --- |
| `selection_schemes` | `("comma", "plus")` | list of selection schemes to sweep |
| `archive_modes` | `("off",)` | list of archive modes to sweep |
| `archive_size` | `5` | passed straight to `EvoPy` |
| `stagnation_generations` | `20` | passed straight to `EvoPy` |

These multiply into the run grid:
`n_circles × strategy × selection_scheme × archive_mode × population_size × num_children × run_id`.

**Threaded through the whole pipeline:**
- `RunResult` / `SummaryStats` gained `selection_scheme` and `archive_mode`
  fields, so they appear automatically in the **CSV** (`benchmark_results_cala.csv`).
- The **summary table** gained `sel` and `archive` columns.
- The **plots** now key each curve/box on the full
  `(strategy, selection_scheme, archive_mode)` "series", with **adaptive labels**
  (a factor only appears in the label if it actually varies in that run) and a
  consistent colour per series.
- A small **UTF-8 stdout guard** in `main()` so the table/plot prints don't crash
  on Windows `cp1252` consoles.

### How to run the WP2 experiments

The `QUICK` branch in `main()` is pre-configured as the **archive × selection
factorial** (strategy held fixed at `FULL_VARIANCE`, the Architecture-B baseline):

```python
# benchmark_Cala.py, main(), QUICK == True
Benchmark(
    n_circles_list=[5, 8],
    strategies=[Strategy.FULL_VARIANCE],
    selection_schemes=["comma", "plus"],                 # (μ,λ) vs (μ+λ)
    archive_modes=["off", "bookkeeping", "reintroduction"],
    archive_size=5,
    stagnation_generations=20,
    population_sizes=[30],
    num_children_list=[7],
    n_runs=3,
    max_evaluations=MAX_EVALS,
)
```

```bash
python benchmark_Cala.py        # QUICK=True -> the 2 selections × 3 archive modes factorial
```

This single grid answers both questions:
- **archive head-to-head:** `bookkeeping` vs `reintroduction` (vs `off`, the
  "does it even use the archive" reference);
- **best combination:** 2 selections × 3 archive modes = 6 series, so the winning
  `(selection, archive)` pair is read straight off the table / plots.

Outputs land in a timestamped folder under `benchmark_Cala_results/`: the summary
CSV plus three figures (convergence, success-rate, gap boxplot).

To run your own combination, either edit that `Benchmark(...)` block or construct
it directly, e.g. just the archive comparison under `(μ,λ)`:

```python
Benchmark(
    n_circles_list=[5, 7, 10, 15],
    strategies=[Strategy.FULL_VARIANCE],
    selection_schemes=["comma"],
    archive_modes=["off", "bookkeeping", "reintroduction"],
    n_runs=10, max_evaluations=50_000,
).run_all()
```

> `QUICK=False` runs Cala's original broader strategy/pop/children sweep; with
> `archive_modes` defaulting to `("off",)` that branch behaves as before unless
> you pass archive modes explicitly.

### Expected reading of the results (sanity checks)
- Under **`comma`**, `bookkeeping` ends at a **better** gap than `off` — the
  archive returns the best-ever that `(μ,λ)` discarded.
- Under **`plus`**, `off` and `bookkeeping` are **identical** — `(μ+λ)` already
  retains the elite, so the archive is redundant. (A clean, defensible result.)
- `reintroduction` is the only mode that can change the search; whether it helps
  is exactly what the factorial measures.

---

## 5 · Files touched (summary)

| file | change |
| --- | --- |
| `ES/evopy/individual.py` | `clone()` for storing/reintroducing elites (shares RNG, draws nothing) |
| `ES/evopy/evopy.py` | `archive_mode` / `archive_size` / `stagnation_generations` kwargs + archive logic in `run()` (`_is_better`, `_update_archive`, `_maybe_reintroduce`) |
| `benchmark_Cala.py` | `selection_schemes` + `archive_modes` swept axes; CSV/table/plot threaded through; QUICK = WP2 factorial; UTF-8 print guard |
| `ofat_benchmark.py` | `B+plus`, `B+arch_book`, `B+arch_reintro` treatments + `archive_mode` column in `per_run.csv` |

All defaults are no-ops (`selection_scheme="plus"` unchanged, `archive_mode="off"`),
so existing scripts and other WPs' runs are unaffected.
