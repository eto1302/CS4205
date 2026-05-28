"""WP1 — plots for the Architecture-B OFAT comparison.

Reads `results/comparisons.csv` (from stats.py) and draws:
  * forest plot  — one row per (arm, n): effect vs baseline + bootstrap 95% CI,
    filled = significant (p<0.05) / hollow = ns, A12 label. The headline slide.
  * ladder       — stacks the SIGNIFICANT winners cumulatively (the narrative
    "climb"). NB: assumes the winners' effects add up — the lite interaction grid
    is what actually verifies that, so this is illustrative until a champion run.

Run:  uv run --with matplotlib --with numpy plot_ofat.py
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

RESULTS_DIR     = "results"
COMPARISONS_CSV = os.path.join(RESULTS_DIR, "comparisons.csv")
PLOTS_DIR       = "plots_wp1"
DEFAULT_METRIC  = "final_gap"


def load():
    with open(COMPARISONS_CSV) as fh:
        return list(csv.DictReader(fh))


def _f(x):
    return float(x) if x not in ("", None) else None


def plot_forest(rows, metric=DEFAULT_METRIC):
    """One row per (arm, n): effect vs baseline, CI whisker, sig fill, A12."""
    sel = [r for r in rows if r["metric"] == metric and r["effect"] != ""]
    if not sel:
        print(f"  forest[{metric}]: no usable rows (all insufficient/saturated)")
        return
    # order: arm, then n
    sel.sort(key=lambda r: (r["treatment"], int(r["n_circles"])))

    fig, ax = plt.subplots(figsize=(9, 0.6 * len(sel) + 2.2))
    ys = list(range(len(sel)))[::-1]            # top-to-bottom
    for y, r in zip(ys, sel):
        eff, lo, hi = _f(r["effect"]), _f(r["ci_lo"]), _f(r["ci_hi"])
        sig = r["marker"] != "ns"
        ax.plot([lo, hi], [y, y], color="#4C72B0", lw=2, alpha=0.8)
        ax.scatter([eff], [y], s=120, zorder=3, edgecolor="black",
                   facecolor="#4C72B0" if sig else "white")
        ax.annotate(f"{r['marker']}  A12={r['a12']}", (hi, y),
                    textcoords="offset points", xytext=(8, 0), va="center",
                    fontsize=8, color="#222" if sig else "#999")

    ax.axvline(0, color="black", lw=1.2)
    ax.text(0, len(sel) - 0.3, "baseline", ha="center", fontsize=9)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r['treatment']}  (n={r['n_circles']}, {r['wp']})" for r in sel],
                       fontsize=9)
    ax.set_xlabel(f"improvement in median {metric} vs baseline  (right = better)  + bootstrap 95% CI")
    ax.set_title(f"OFAT forest plot — {metric}\nfilled = significant (p<0.05),  hollow = ns",
                 fontsize=11)
    ax.grid(True, axis="x", alpha=0.3)
    handles = [mlines.Line2D([], [], marker="o", ls="", color="#4C72B0", label="significant"),
               mlines.Line2D([], [], marker="o", ls="", markerfacecolor="white",
                             markeredgecolor="black", color="white", label="ns")]
    ax.legend(handles=handles, fontsize=8, loc="lower right")

    fig.tight_layout()
    out = os.path.join(PLOTS_DIR, f"forest_{metric}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def plot_ladder(rows, metric=DEFAULT_METRIC, n=None):
    """Cumulative 'climb': baseline, then each significant winner stacked.
    ASSUMES additivity — verify with the lite interaction grid / a champion run."""
    if n is None:
        ns = sorted({int(r["n_circles"]) for r in rows})
        n = ns[len(ns) // 2]                    # a mid problem size
    sel = [r for r in rows if r["metric"] == metric and int(r["n_circles"]) == n
           and r["effect"] != "" and r["marker"] != "ns" and _f(r["effect"]) > 0]
    base_rows = [r for r in rows if r["metric"] == metric and int(r["n_circles"]) == n
                 and r["base_median"] != ""]
    if not base_rows:
        print(f"  ladder[{metric}, n={n}]: no baseline median available")
        return
    base_median = _f(base_rows[0]["base_median"])
    sel.sort(key=lambda r: _f(r["effect"]), reverse=True)   # biggest winner first

    labels = ["baseline"] + [r["treatment"] for r in sel]
    level = base_median
    levels = [level]
    for r in sel:
        level -= _f(r["effect"])                # improvement = lower gap
        levels.append(level)

    fig, ax = plt.subplots(figsize=(max(6, 1.4 * len(labels)), 5))
    x = range(len(labels))
    ax.plot(x, levels, "o-", color="#55A868", lw=2, ms=9)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
    ax.set_ylabel(f"median {metric}  (lower = better)")
    title = (f"Reconstructed ladder — {metric}, n={n}\n"
             f"cumulative stack of significant winners (assumes additivity — "
             f"confirm with the lite grid / champion run)")
    if not sel:
        title += "\n[no significant winners yet — only the baseline is shown]"
    ax.set_title(title, fontsize=10)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    out = os.path.join(PLOTS_DIR, f"ladder_{metric}_n{n}.png")
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out}")


def main():
    if not os.path.exists(COMPARISONS_CSV):
        print(f"No {COMPARISONS_CSV} — run stats.py first.")
        return
    os.makedirs(PLOTS_DIR, exist_ok=True)
    rows = load()
    metrics = sorted({r["metric"] for r in rows})
    print(f"Plotting from {COMPARISONS_CSV} ({len(rows)} comparison rows)...")
    for m in metrics:
        plot_forest(rows, m)
    plot_ladder(rows, DEFAULT_METRIC)
    print(f"Plots in '{PLOTS_DIR}/'")


if __name__ == "__main__":
    main()
