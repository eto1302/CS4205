# EvolutionStrategyPython — CiaS baseline

Evolution Strategy baseline for the **Circles in a Square (CiaS)** problem,
built on the `evopy` framework. Place `n` points in `[0,1]²` so the
**minimum pairwise distance** is maximised; ground-truth optima from
[Packomania](http://www.packomania.com) (`n=2..20`).

## Quick start

```bash
python benchmark.py       # writes results/raw_*.csv + results/summary.csv
python plot_results.py    # writes plots/*.png
```

`benchmark.py` sweeps `n ∈ {7,10,15,20}` × 3 strategies × 2 init modes
× 25 seeds = 600 runs (≈ 5 h on 12 cores).

## What's logged

- **`results/raw_<n>circles_<STRATEGY>_<INIT>.csv`** — one row per
  generation per run: `generation, evaluations, best_fitness,
  avg_fitness, std_fitness, gap, seed, n_circles, strategy, config,
  init_mode`. (`gap = (target − best_fitness) / target`, relative.)
- **`results/summary.csv`** — one row per (n, strategy, init_mode), 39
  columns. Per-tolerance metrics use `_1e-02 / _1e-03 / _1e-05` suffixes
  (`success_rate_1e-02`, `ert_1e-05`, etc.) so success/ERT/FHT at any of
  the three tolerances are derivable from one set of runs.

## The four plots

Every example below uses `n=7` (easiest sweep size). Packomania optimum
for `n=7`: **0.5358**. Budget per run: `100,000` evaluations. Each
strategy curve is built from **25 independent runs** (seeds 0…24);
population = 30 individuals, num_children = 7 → 210 evaluations per
generation, ≈ 476 generations to exhaust budget.

### 1. `convergence_<n>circles.png` — median ± IQR trajectory

**What it is.** For each strategy: 25 trajectories of `best_fitness` vs.
`evaluations` collapsed into one solid line (**median across the 25
runs**) plus a shaded band (**25th–75th percentile, i.e. middle half of
runs**). Red dashed line = Packomania optimum.

**Reading it (n=7 example).** Look at `evaluations = 60,000`:

- The 25 Multiple-σ runs' best_fitness values at that x-position are
  sorted; their **median** ≈ 0.51 (orange line height there) and the
  middle 13 of the 25 runs lie roughly in [0.50, 0.52] (the narrow
  orange band). Tight band → reliable.
- The 25 Single-σ runs' values at the same x-position have median ≈
  0.50, but the band spans roughly [0.41, 0.52] — best 25% of runs hit
  0.52, worst 25% are stuck around 0.41. Wide band → coin-flip
  performance across seeds.

**What's hidden.** Best-of-25 and worst-of-25 (0th/100th percentiles)
are not shown — only the middle 50%. Single-σ's best-of-25 run actually
reaches 0.522 at the right edge, which is just below Multiple-σ's
*median*. The IQR convention (BBOB/COCO standard) deliberately avoids
cherry-picking the lucky run — the median is what you'd expect on your
next attempt, the band is the variability you should plan for.

### 2. `final_fitness_boxplots.png` — distribution at the budget

**What it is.** For each (n, strategy): a box plot of the 25 runs' final
`best_fitness` (i.e. fitness when the run terminated). Box = IQR (same
range as the convergence-curve band, just at one specific x =
MAX_EVALS). Whiskers = ~min/max of non-outliers. Black bar = median.
Red ★ = Packomania optimum.

**Reading it (n=7 example).**

- **Multiple σ box** at n=7: a small box near the top of the y-range
  (≈ 0.50–0.52), median bar at 0.511, whiskers from 0.450 to 0.532.
  Just below the ★ (0.5358). Story: every run lands in roughly the
  same neighbourhood, and that neighbourhood is close to optimum.
- **Single σ box** at n=7: a tall box from 0.41 to 0.51, median 0.50,
  whisker reaching down to 0.27. Same median as Multiple σ but
  catastrophically wider — 1-in-4 runs ended below 0.41. Story:
  unreliable, even though the "average" is OK.
- **Full Cov box** at n=7: low and tight, median 0.29, all runs in
  [0.23, 0.36]. Story: every run failed the same way (the
  `individual.py` τ / rotation bugs bite consistently).

**Why bother if convergence_07circles.png already shows this?** The
convergence plot shows it as a function of evaluations; the boxplot
shows it as a function of `n_circles` (one panel per box position),
which is the better view for "how does the EA scale with problem size?"

### 3. `success_rate.png` — fraction of runs that reached the optimum

**What it is.** Grouped bar chart. For each (n, strategy): the fraction
of the 25 runs that finished within tolerance `TARGET_TOL = 1e-5` of the
Packomania optimum.

**Reading it (n=7 example).** Every bar at zero. None of the 75
n=7 runs (3 strategies × 25 seeds) finished within `1e-5` of 0.5358.

**Why all zeros?** `1e-5` is brutally tight — within five decimal places
of the *exact* optimum. The convergence plot already showed best runs
ending around 0.522 (Single σ) and 0.532 (Multiple σ), both ≫ `1e-5`
short. So the success-at-1e-5 metric is **0% everywhere**, which is its
own kind of result: *the baseline EA cannot polish to high precision on
this problem at this budget*.

**What it would show if we used `1e-2`.** The `summary.csv` has
`success_rate_1e-02` as a separate column — at that looser tolerance,
n=7 Multiple σ has 2/25 successes (8%) under random init, 1/25 (4%)
under cluster_corner. Everything else is still zero. The plot uses 1e-5
because that's the `TARGET_TOL` constant at the top of `plot_results.py`
— change it to 1e-2 to see something non-zero.

### 4. `ert.png` — Expected Running Time

**What it is.** For each strategy: ERT(1e-5) vs `n_circles`, log y-axis.

```
ERT(ε) = (Σ evals over ALL runs) / (number of successful runs)
       = "total compute spent" / "successes obtained"
```

Answers "how many evals does it cost, on average, to produce one
success — assuming you restart on failure?"

**Reading it (n=7 example).** All lines pinned at `10⁶` — that's a
placeholder. ERT(1e-5) is mathematically *undefined* when 0 runs
succeed (divide by zero); `plot_results.py` renders inf as
`10 × MAX_EVALS = 10⁶` so it stays on the log axis.

**What a meaningful ERT looks like.** If we had used the 1e-2 metric
instead, n=7 Multiple σ would show:

```
ERT(1e-2) ≈ 25 runs × 100,000 evals / 2 successes ≈ 1.25M evals/success
```

Confirmed by `summary.csv`: `ert_1e-02 = 1,252,125` for n=7 Multiple σ
random. Interpretation: with this EA's 8% success rate, you'd expect to
restart ~12 times (each restart = 100k evals) before one attempt hits
1% tolerance.

## Init modes

Two initialization modes per (n, strategy):

- **`random`** — `warm_start=None`, EvoPy's default. `std=1` is so large
  relative to `bounds=(0,1)` that nearly every coordinate gets resampled
  uniformly by the bounds-clipping in `evopy.py:126`. Effectively
  uniform-random init across the square.
- **`cluster_corner`** — `warm_start=np.full(2n, 0.1)`, `std=0.02`. All
  individuals are seeded in a tight 0.06×0.06 cluster centred at
  (0.1, 0.1). First-generation fitness ≈ 0 (all points stacked); the EA
  must spread the points across the full square to make progress.

**Note: `cluster_corner` is not a *deceptive* trap.** A deceptive trap
is a configuration where the local fitness gradient points *away* from
the global optimum (e.g. the regular grid layout for non-square n — see
`benchmark-plan.md` §5). The cluster_corner start is a degenerate
*initialization*: fitness is near zero and any spread improves it. The
EA has a clear gradient out; it just has to walk further. So it's a
basin-escape / poor-init stress test, not a deception test. The current
plots only render `init_mode='random'`; the cluster_corner data is in
`summary.csv` and `raw_*_cluster_corner.csv` for separate analysis.

## Config knobs (top of `benchmark.py`)

| Constant | Default | Effect |
|---|---|---|
| `CIRCLE_SIZES` | `[7,10,15,20]` | which `n` to sweep |
| `STRATEGIES` | all 3 | which σ-adaptation variant(s) |
| `N_RUNS` | 25 | seeds per config (statistical strength) |
| `MAX_EVALS` | 100_000 | per-run fitness-evaluation budget |
| `POPULATION` | 30 | parents per generation |
| `TARGET_TOLS` | `[1e-2, 1e-3, 1e-5]` | tolerances reported in `summary.csv`. Early-stop is at `min(TARGET_TOLS) = 1e-5` so coarser crossings stay in the log. |
| `INIT_MODES` | `["random","cluster_corner"]` | init modes per config |
| `CONFIG_LABEL` | `"baseline"` | tag for facet plots when variants are added |
