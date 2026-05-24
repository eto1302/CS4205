import matplotlib
matplotlib.use('Agg')  # headless — no display required

import os
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

RESULTS_DIR = "results"
PLOTS_DIR   = "plots"
MAX_EVALS   = 100_000
TARGET_TOL  = 1e-5
INIT_MODE   = "random"                # plot the random-init baseline; cluster_corner handled separately
TOL_TAG     = f"{TARGET_TOL:.0e}"     # "1e-05" — matches the suffix in benchmark.py
SR_COL      = f"success_rate_{TOL_TAG}"
ERT_COL     = f"ert_{TOL_TAG}"

STRATEGY_NAMES  = ["SINGLE_VARIANCE", "MULTIPLE_VARIANCE", "FULL_VARIANCE"]
STRATEGY_LABELS = {
    "SINGLE_VARIANCE":   "Single σ",
    "MULTIPLE_VARIANCE": "Multiple σ",
    "FULL_VARIANCE":     "Full Cov",
}
STRATEGY_COLORS = {
    "SINGLE_VARIANCE":   "steelblue",
    "MULTIPLE_VARIANCE": "darkorange",
    "FULL_VARIANCE":     "forestgreen",
}

INIT_MODES_ALL = ["random", "cluster_corner"]
INIT_COLORS = {
    "random":         "steelblue",
    "cluster_corner": "crimson",
}

_TARGETS = [
    1.414213562373095048801688724220,  # 2
    1.035276180410083049395595350499,  # 3
    1.000000000000000000000000000000,  # 4
    0.707106781186547524400844362106,  # 5
    0.600925212577331548853203544579,  # 6
    0.535898384862245412945107316990,  # 7
    0.517638090205041524697797675248,  # 8
    0.500000000000000000000000000000,  # 9
    0.421279543983903432768821760651,  # 10
    0.398207310236844165221512929748,  # 11
    0.388730126323020031391610191835,  # 12
    0.366096007696425085295389370603,  # 13
    0.348915260374018877918854409001,  # 14
    0.341081377402108877637121191351,  # 15
    0.333333333333333333333333333333,  # 16
    0.306153985300332915214516914060,  # 17
    0.300462606288665774426601772290,  # 18
    0.289541991994981660261698764510,  # 19
    0.286611652351681559449894454738,  # 20
]


def get_target(n):
    return _TARGETS[n - 2]


def load_raw(n_circles, strategy, init_mode=INIT_MODE):
    fname = os.path.join(RESULTS_DIR, f"raw_{n_circles}circles_{strategy}_{init_mode}.csv")
    return pd.read_csv(fname) if os.path.exists(fname) else None


def plot_convergence(circle_sizes, n_runs):
    """One figure per n_circles: median best_fitness vs evaluations by strategy."""
    for n in circle_sizes:
        fig, ax = plt.subplots(figsize=(7, 5))
        target  = get_target(n)
        any_data = False

        for strat in STRATEGY_NAMES:
            df = load_raw(n, strat)
            if df is None:
                continue
            any_data = True

            eval_grid  = np.linspace(0, MAX_EVALS, 500)
            run_curves = []
            for _, run_df in df.groupby('seed'):
                evals   = run_df['evaluations'].values
                fitness = run_df['best_fitness'].values
                run_curves.append(np.interp(eval_grid, evals, fitness))

            curves = np.array(run_curves)
            median = np.median(curves, axis=0)
            p25    = np.percentile(curves, 25, axis=0)
            p75    = np.percentile(curves, 75, axis=0)

            color = STRATEGY_COLORS[strat]
            ax.plot(eval_grid, median, color=color,
                    label=STRATEGY_LABELS[strat], linewidth=1.8)
            ax.fill_between(eval_grid, p25, p75, color=color, alpha=0.18)

        if not any_data:
            plt.close(fig)
            continue

        ax.axhline(target, color='red', linestyle='--', linewidth=1.0,
                   label='Known optimal')
        ax.set_xlabel("Function evaluations")
        ax.set_ylabel("Best fitness  (min pairwise distance)")
        ax.set_title(f"Convergence — {n} circles  (median ± IQR over {n_runs} runs)")
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)

        fname = os.path.join(PLOTS_DIR, f"convergence_{n:02d}circles.png")
        fig.savefig(fname, dpi=150, bbox_inches='tight')
        plt.close(fig)
        print(f"  Saved {fname}")


def plot_final_fitness_boxplots(circle_sizes, n_runs):
    """Grouped box plots of final best fitness, one group per n_circles."""
    n_g  = len(circle_sizes)
    n_s  = len(STRATEGY_NAMES)
    w    = 0.22
    offs = np.linspace(-(n_s - 1) * w / 2, (n_s - 1) * w / 2, n_s)
    x    = np.arange(n_g)

    fig, ax = plt.subplots(figsize=(max(10, n_g * 1.6), 5))

    legend_handles = []
    for si, strat in enumerate(STRATEGY_NAMES):
        data_per_n = []
        pos_per_n  = []
        for i, n in enumerate(circle_sizes):
            df = load_raw(n, strat)
            if df is None:
                continue
            finals = df.groupby('seed')['best_fitness'].last().values
            data_per_n.append(finals)
            pos_per_n.append(float(x[i] + offs[si]))

        if not data_per_n:
            continue

        color = STRATEGY_COLORS[strat]
        ax.boxplot(
            data_per_n,
            positions=pos_per_n,
            widths=w * 0.85,
            patch_artist=True,
            boxprops=dict(facecolor=color, alpha=0.55),
            medianprops=dict(color='black', linewidth=1.8),
            whiskerprops=dict(color=color),
            capprops=dict(color=color),
            flierprops=dict(marker='o', markersize=3,
                            markerfacecolor=color, alpha=0.5, linestyle='none'),
            manage_ticks=False,
        )
        legend_handles.append(
            Patch(facecolor=color, alpha=0.55, label=STRATEGY_LABELS[strat])
        )

    # Mark known optima
    for i, n in enumerate(circle_sizes):
        ax.plot(x[i], get_target(n), 'r*', markersize=10, zorder=5)
    legend_handles.append(
        mlines.Line2D([], [], marker='*', color='r', markersize=10,
                      label='Known optimal', linestyle='None')
    )

    ax.set_xticks(x)
    ax.set_xticklabels([str(n) for n in circle_sizes])
    ax.set_xlim(-0.6, n_g - 0.4)
    ax.set_xlabel("Number of circles")
    ax.set_ylabel("Final best fitness")
    ax.set_title(f"Final fitness distribution  ({n_runs} runs each,  ★ = known optimal)")
    ax.legend(handles=legend_handles, fontsize=9)
    ax.grid(True, axis='y', alpha=0.3)

    fname = os.path.join(PLOTS_DIR, "final_fitness_boxplots.png")
    fig.savefig(fname, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {fname}")


def plot_success_rate(summary_df, circle_sizes, n_runs):
    """Grouped bar chart: fraction of runs that reached the known optimum."""
    n_g  = len(circle_sizes)
    n_s  = len(STRATEGY_NAMES)
    w    = 0.22
    offs = np.linspace(-(n_s - 1) * w / 2, (n_s - 1) * w / 2, n_s)
    x    = np.arange(n_g)

    fig, ax = plt.subplots(figsize=(max(10, n_g * 1.6), 5))

    for si, strat in enumerate(STRATEGY_NAMES):
        rates    = []
        strat_df = summary_df[summary_df['strategy'] == strat]
        for n in circle_sizes:
            row = strat_df[strat_df['n_circles'] == n]
            rates.append(float(row[SR_COL].values[0]) if len(row) else 0.0)

        color = STRATEGY_COLORS[strat]
        ax.bar(x + offs[si], rates, width=w * 0.85,
               color=color, alpha=0.8, label=STRATEGY_LABELS[strat])

    ax.set_xticks(x)
    ax.set_xticklabels([str(n) for n in circle_sizes])
    ax.set_ylim(0, 1.12)
    ax.set_xlabel("Number of circles")
    ax.set_ylabel("Success rate")
    ax.set_title(
        f"Success rate  (reached known optimal ± {TARGET_TOL:.0e},  {n_runs} runs each)"
    )
    ax.legend(fontsize=9)
    ax.grid(True, axis='y', alpha=0.3)

    fname = os.path.join(PLOTS_DIR, "success_rate.png")
    fig.savefig(fname, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {fname}")


def plot_random_vs_cluster(circle_sizes, n_runs):
    """4×3 grid: rows = problem size, cols = strategy. Each cell overlays
    random vs cluster_corner convergence curves (median + IQR)."""
    n_rows = len(circle_sizes)
    n_cols = len(STRATEGY_NAMES)
    fig, axes = plt.subplots(n_rows, n_cols,
                             figsize=(4.2 * n_cols, 2.8 * n_rows),
                             sharex=True)
    if n_rows == 1:
        axes = axes.reshape(1, -1)

    for i, n in enumerate(circle_sizes):
        target = get_target(n)
        for j, strat in enumerate(STRATEGY_NAMES):
            ax = axes[i, j]
            any_data = False

            for init in INIT_MODES_ALL:
                df = load_raw(n, strat, init_mode=init)
                if df is None:
                    continue
                any_data = True

                eval_grid  = np.linspace(0, MAX_EVALS, 500)
                run_curves = []
                for _, run_df in df.groupby('seed'):
                    evals   = run_df['evaluations'].values
                    fitness = run_df['best_fitness'].values
                    run_curves.append(np.interp(eval_grid, evals, fitness))

                curves = np.array(run_curves)
                median = np.median(curves, axis=0)
                p25    = np.percentile(curves, 25, axis=0)
                p75    = np.percentile(curves, 75, axis=0)

                color = INIT_COLORS[init]
                ax.plot(eval_grid, median, color=color,
                        label=init, linewidth=1.5)
                ax.fill_between(eval_grid, p25, p75, color=color, alpha=0.18)

            if any_data:
                ax.axhline(target, color='black', linestyle='--', linewidth=0.7, alpha=0.6)

            ax.grid(True, alpha=0.3)
            if i == 0:
                ax.set_title(STRATEGY_LABELS[strat], fontsize=10)
            if j == 0:
                ax.set_ylabel(f"n={n}\nbest fitness", fontsize=9)
            if i == n_rows - 1:
                ax.set_xlabel("evaluations", fontsize=9)
            if i == 0 and j == n_cols - 1:
                ax.legend(fontsize=8, loc='lower right')

    fig.suptitle(
        f"Convergence — random vs cluster_corner init  "
        f"(median ± IQR over {n_runs} runs;  dashed = Packomania optimum)",
        fontsize=11, y=1.00,
    )
    fig.tight_layout()
    fname = os.path.join(PLOTS_DIR, "random_vs_cluster.png")
    fig.savefig(fname, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {fname}")


def plot_ert(summary_df, circle_sizes):
    """ERT vs n_circles on a log-scale y-axis, one line per strategy."""
    fig, ax = plt.subplots(figsize=(8, 5))

    for strat in STRATEGY_NAMES:
        strat_df = summary_df[summary_df['strategy'] == strat].sort_values('n_circles')
        ns, erts = [], []
        for n in circle_sizes:
            row = strat_df[strat_df['n_circles'] == n]
            if not len(row):
                continue
            ert = float(row[ERT_COL].values[0])
            ns.append(n)
            # Replace inf with 10× budget so it still shows on log scale
            erts.append(ert if not np.isinf(ert) else MAX_EVALS * 10)

        if not ns:
            continue

        color = STRATEGY_COLORS[strat]
        ax.plot(ns, erts, marker='o', color=color,
                label=STRATEGY_LABELS[strat], linewidth=1.8)

    ax.axhline(MAX_EVALS, color='gray', linestyle=':', linewidth=1.2,
               label=f'Budget ({MAX_EVALS:,} evals)')
    ax.set_yscale('log')
    ax.set_xlabel("Number of circles")
    ax.set_ylabel("ERT  (total evals / successes,  log scale)")
    ax.set_title("Expected Running Time by problem size and strategy")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fname = os.path.join(PLOTS_DIR, "ert.png")
    fig.savefig(fname, dpi=150, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved {fname}")


def main():
    summary_path = os.path.join(RESULTS_DIR, "summary.csv")
    if not os.path.exists(summary_path):
        print(f"No summary.csv found in '{RESULTS_DIR}/'. Run benchmark.py first.")
        return

    os.makedirs(PLOTS_DIR, exist_ok=True)

    summary_df   = pd.read_csv(summary_path)
    # Filter to the baseline init mode for the existing 4 plots; cluster_corner
    # gets its own pipeline (or facet plots) in a follow-up.
    summary_df   = summary_df[summary_df['init_mode'] == INIT_MODE].copy()
    circle_sizes = sorted(summary_df['n_circles'].unique().astype(int).tolist())

    # Infer n_runs from any available raw CSV
    n_runs = 25
    for n in circle_sizes:
        for strat in STRATEGY_NAMES:
            df = load_raw(n, strat)
            if df is not None:
                n_runs = int(df['seed'].nunique())
                break
        else:
            continue
        break

    print(f"Generating plots for {len(circle_sizes)} problem sizes, "
          f"{n_runs} runs each ...\n")

    plot_convergence(circle_sizes, n_runs)
    plot_final_fitness_boxplots(circle_sizes, n_runs)
    plot_success_rate(summary_df, circle_sizes, n_runs)
    plot_ert(summary_df, circle_sizes)
    plot_random_vs_cluster(circle_sizes, n_runs)

    print(f"\nAll plots saved to '{PLOTS_DIR}/'")


if __name__ == "__main__":
    main()
