"""Regenerate `benchmark_gap_boxplot.png` for THIS results folder only.

The boxplot produced by benchmark_Cala.py labels every box on each subplot's
x-axis, repeated once per problem size — with 12 experiment categories that
text is unreadable. This standalone script rebuilds the same figure but drops
the per-subplot x labels and adds ONE shared legend mapping colour -> category.

It reads only `benchmark_results_cala.csv` next to it and overwrites
`benchmark_gap_boxplot.png` in place. It does NOT import or modify
benchmark_Cala.py, so running a fresh experiment still produces the original
plots; this fix is local to this folder.

Run:  python replot_boxplot.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

HERE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(HERE, "benchmark_results_cala.csv")
OUT_PATH = os.path.join(HERE, "benchmark_gap_boxplot.png")


def load_rows():
    with open(CSV_PATH, newline="") as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["n_circles"] = int(r["n_circles"])
        r["gap_pct"] = float(r["gap_pct"])
    return rows


def main():
    rows = load_rows()

    n_circles_list = sorted({r["n_circles"] for r in rows})
    # One "series" per (strategy, selection_scheme, archive_mode) — matches
    # benchmark_Cala.plot(); population_size/num_children are pooled into the box.
    series = sorted({(r["strategy"], r["selection_scheme"], r["archive_mode"])
                     for r in rows})

    # Only name the axes that actually vary, so labels stay short.
    vary_strat = len({s[0] for s in series}) > 1
    vary_scheme = len({s[1] for s in series}) > 1
    vary_arch = len({s[2] for s in series}) > 1

    def series_label(sc):
        parts = []
        if vary_strat:
            parts.append(sc[0])
        if vary_scheme:
            parts.append(sc[1])
        if vary_arch:
            parts.append(sc[2])
        return " / ".join(parts) if parts else sc[0]

    # tab20 gives up to 20 visually distinct colours (the default cycle only has
    # 10, which would repeat for 12 series and break the colour->category map).
    cmap = plt.get_cmap("tab20")
    series_color = {sc: cmap(i % 20) for i, sc in enumerate(series)}

    n_cols = len(n_circles_list)
    fig, axes = plt.subplots(1, n_cols,
                             figsize=(max(7, n_cols * 3.2), 5.5),
                             squeeze=False)
    fig.suptitle("Distribution of final gap % from optimum", fontsize=13)

    for idx, n in enumerate(n_circles_list):
        ax = axes[0][idx]
        data = []
        for strat, scheme, arch in series:
            data.append([r["gap_pct"] for r in rows
                         if r["n_circles"] == n and r["strategy"] == strat
                         and r["selection_scheme"] == scheme
                         and r["archive_mode"] == arch])

        bp = ax.boxplot(data, positions=range(1, len(series) + 1),
                        patch_artist=True, widths=0.6)
        for patch, sc in zip(bp["boxes"], series):
            patch.set_facecolor(series_color[sc])
            patch.set_alpha(0.8)

        ax.set_title(f"{n} circles")
        ax.set_xticks([])                       # identity comes from the shared legend
        ax.set_ylabel("Gap from optimum (%)" if idx == 0 else "")
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--")

    # One shared legend for the whole figure (replaces the per-subplot labels).
    handles = [mpatches.Patch(facecolor=series_color[sc], alpha=0.8,
                              label=series_label(sc)) for sc in series]
    ncol = min(4, len(series))
    fig.legend(handles=handles, loc="lower center", ncol=ncol, fontsize=8,
               frameon=True, bbox_to_anchor=(0.5, -0.01),
               title="Experiment  (strategy / selection / archive)")

    # Leave room at the bottom for the legend.
    fig.tight_layout(rect=[0, 0.12, 1, 1])
    fig.savefig(OUT_PATH, dpi=150, bbox_inches="tight")
    print(f"wrote {OUT_PATH}  ({len(series)} categories, single shared legend)")


if __name__ == "__main__":
    main()
