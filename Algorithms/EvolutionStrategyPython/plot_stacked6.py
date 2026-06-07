"""Final 6-variant stacked-improvements convergence plots (best-so-far + current-gen
median), reading results/STACKED{tag}/ and writing PNGs into that folder's plots/.

  STK_EVALS=100000 python plot_stacked6.py     # results/STACKED/plots/
  STK_EVALS=200000 python plot_stacked6.py     # results/STACKED_200k/plots/

best-so-far source: traces.csv (+traces_fpolish.csv) if present, else accumulate(traces_raw.csv).
current-gen source: traces_raw.csv (per-generation best, no accumulate) if present.
"""
import os, csv, math, numpy as np
import stacked_benchmark as sb
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, matplotlib.ticker as mticker

MAX_EVALS = int(os.environ.get("STK_EVALS", "100000"))
TAG = "" if MAX_EVALS == 100000 else f"_{MAX_EVALS // 1000}k"
D = os.path.join(sb.REPO_ROOT, "results", "STACKED" + TAG)
PLOTS = os.path.join(D, "plots"); os.makedirs(PLOTS, exist_ok=True)

ORDER = [("baseline","baseline","#7f7f7f",False),
         ("+clip","baseline + clip","#1f77b4",False),
         ("+clip+f-polish","baseline + clip + f-polish","#ff7f0e",False),
         ("+clip+polish","baseline + clip + k-polish","#2ca02c",False),
         ("+clip+f-polish+bookkeeping","baseline + clip + f-polish + bookkeeping","#d62728",True),
         ("+clip+polish+archive","baseline + clip + k-polish + bookkeeping","#9467bd",False)]

def load(files, accumulate):
    tmp = {}
    for fn in files:
        p = os.path.join(D, fn)
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p)):
            tmp.setdefault((r["variant"], int(r["n_circles"]), int(r["seed"]), fn), []).append(
                (float(r["evaluations"]), float(r["best_fitness"])))
    out = {}
    for (v, n, _s, _f), pts in tmp.items():
        pts.sort(); ev = np.array([p[0] for p in pts]); bf = np.array([p[1] for p in pts])
        if accumulate and len(bf): bf = np.maximum.accumulate(bf)
        out.setdefault((v, n), []).append((ev, bf))
    return out

def draw(traces, title, out):
    n_list = sorted({n for _, n in traces}); nc = min(2, len(n_list)); nr = math.ceil(len(n_list)/nc)
    fig, axes = plt.subplots(nr, nc, figsize=(7*nc, 4.3*nr), squeeze=False)
    fig.suptitle(title, fontsize=15)
    yt = [0.01,0.02,0.03,0.05,0.1,0.2,0.3,0.5,0.7,1.0]; handles = labels = None
    for i, n in enumerate(n_list):
        ax = axes[i//nc][i%nc]; tgt = sb.ofat.get_target(n); grid = np.linspace(1, MAX_EVALS, 200)
        for v, disp, col, dash in ORDER:
            st = traces.get((v, n))
            if not st: continue
            ax.plot(grid, sb._median_gap_grid(st, tgt, grid), color=col,
                    lw=(6.6 if v=="+clip" else 2.2), ls=("--" if dash else "-"), label=disp)
        ax.set_yscale("log"); ax.yaxis.set_major_locator(mticker.FixedLocator(yt))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y,_:f"{y:g}"))
        ax.yaxis.set_minor_formatter(mticker.NullFormatter())
        ax.set_title(f"{n} circles"); ax.set_xlabel("Evaluations")
        ax.set_ylabel("Median relative gap to optimum"); ax.grid(True, which="both", alpha=0.25)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x,_:f"{int(x):,}"))
        if handles is None: handles, labels = ax.get_legend_handles_labels()
    for j in range(len(n_list), nr*nc): axes[j//nc][j%nc].set_visible(False)
    fig.legend(handles, labels, loc="lower center", ncol=3, fontsize=11, frameon=False, bbox_to_anchor=(0.5,0.0))
    fig.tight_layout(rect=[0,0.08,1,0.96]); fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print("saved", out)

bsf = load(["traces.csv","traces_fpolish.csv"], accumulate=False)
if not bsf: bsf = load(["traces_raw.csv"], accumulate=True)
draw(bsf, "Stacked Improvements", os.path.join(PLOTS, "convergence_stacked_improvements.png"))

cur = load(["traces_raw.csv"], accumulate=False)
if cur: draw(cur, "Stacked Improvements (current-gen median, not best-so-far)",
             os.path.join(PLOTS, "convergence_current_median.png"))
