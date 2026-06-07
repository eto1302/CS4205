"""Uniform-style figures for the WP1/WP2/WP3 findings guides.

Reads real data from findings/data/ (extracted from teammates' branches + Leo's
WP1 run) and renders consistent plots to findings/figs/. All gaps shown as
"% gap to optimum" (lower = better) for visual consistency across guides.

Run:  uv run --with matplotlib --with numpy --with scipy make_findings_figs.py
"""
import csv
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA = "data"
FIGS = "figs"
os.makedirs(FIGS, exist_ok=True)

# shared palette / style
C = {"baseline": "#7f7f7f", "good": "#2ca02c", "bad": "#d62728",
     "blue": "#4C72B0", "orange": "#DD8452", "green": "#55A868", "grey": "#999999"}
plt.rcParams.update({"axes.grid": True, "grid.alpha": 0.3, "axes.axisbelow": True,
                     "figure.dpi": 150, "font.size": 10})


def read(path):
    with open(path) as fh:
        return list(csv.DictReader(fh))


def median(xs):
    xs = sorted(float(x) for x in xs)
    n = len(xs)
    return None if n == 0 else (xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2)


# ── WP2 (Ivan): selection & elitist archive ─────────────────────────────────
def wp2():
    rows = read(f"{DATA}/wp2_300k.csv")
    ns = [7, 10, 15]   # n=5 is solved (0%) by everything; drop from plots

    def med_gap_pct(strategy, selection, archive, n):
        # pooled over pop∈{15,30,50} × children∈{5,10} × 4 seeds = 24 runs/cell
        v = [r["gap_pct"] for r in rows if r["strategy"] == strategy
             and r["selection_scheme"] == selection and r["archive_mode"] == archive
             and int(r["n_circles"]) == n]
        return median(v)

    x = np.arange(len(ns)); w = 0.38
    # (a) comma vs plus — the strategy-DEPENDENT story, two panels
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=False)
    for ax, strat, title in [(axes[0], "SINGLE_VARIANCE", "single-variance (1 σ)"),
                             (axes[1], "MULTIPLE_VARIANCE", "multiple-variance (n σ)")]:
        comma = [med_gap_pct(strat, "comma", "off", n) for n in ns]
        plus = [med_gap_pct(strat, "plus", "off", n) for n in ns]
        ax.bar(x - w/2, comma, w, color=C["green"], label="(μ, λ) comma")
        ax.bar(x + w/2, plus, w, color=C["bad"], label="(μ + λ) plus")
        ax.set_xticks(x); ax.set_xticklabels([f"n={n}" for n in ns])
        ax.set_title(title); ax.set_ylabel("median gap to optimum (%)")
        ax.legend()
    fig.suptitle("WP2 · (μ,λ) vs (μ+λ) depends on σ-strategy:  tied on single, "
                 "comma WINS on multiple (plus 2× worse at n=15)\n"
                 "300k evals, pooled pop/children, 4 seeds  (lower = better) — BSw95: plus hinders σ self-adaptation",
                 fontsize=10)
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp2_selection.png", bbox_inches="tight"); plt.close(fig)
    print("wp2_selection.png")

    # (b) archive modes under comma (multiple-variance) — essentially NO effect
    fig, ax = plt.subplots(figsize=(8, 4.6))
    w3 = 0.27
    for i, (mode, col, lbl) in enumerate([("off", C["grey"], "no archive"),
                                          ("bookkeeping", C["blue"], "archive (bookkeeping)"),
                                          ("reintroduction", C["orange"], "archive + reintroduction")]):
        vals = [med_gap_pct("MULTIPLE_VARIANCE", "comma", mode, n) for n in ns]
        ax.bar(x + (i-1)*w3, vals, w3, color=col, label=lbl)
    ax.set_xticks(x); ax.set_xticklabels([f"n={n}" for n in ns])
    ax.set_ylabel("median gap to optimum (%)")
    ax.set_title("WP2 · Elitist archive (under μ,λ multiple-variance): bookkeeping = IDENTICAL to off,\n"
                 "reintroduction ≈ no help (slightly worse at n=15)  — 'mostly bookkeeping', per Arthur")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp2_archive.png", bbox_inches="tight"); plt.close(fig)
    print("wp2_archive.png")


# ── WP3 (Cala): constraint-handling repair modes ────────────────────────────
def wp3():
    runs = read(f"{DATA}/wp3_per_run_single.csv")
    ns = sorted({int(r["n_circles"]) for r in runs})
    label = {"baseline": "random (baseline)", "B-repair_clip": "clip", "B-repair_reflect": "reflect"}
    color = {"baseline": C["baseline"], "B-repair_clip": C["green"], "B-repair_reflect": C["blue"]}

    def med(tr, n):
        return median([r["final_gap"] for r in runs if r["treatment"] == tr and int(r["n_circles"]) == n])

    x = np.arange(len(ns)); order = ["baseline", "B-repair_clip", "B-repair_reflect"]; w = 0.27
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for i, tr in enumerate(order):
        vals = [100*med(tr, n) for n in ns]
        ax.bar(x + (i-1)*w, vals, w, color=color[tr], label=label[tr])
    ax.set_xticks(x); ax.set_xticklabels([f"n={n}" for n in ns])
    ax.set_ylabel("median gap to optimum (%)")
    ax.set_title("WP3 · Repair: clip & reflect crush random; clip wins even at n=7\n"
                 "single-variance baseline, 25 seeds, 100k evals  (lower = better)")
    ax.legend()
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp3_repair.png", bbox_inches="tight"); plt.close(fig)
    print("wp3_repair.png")

    # forest of clip/reflect effect vs random baseline (CI + sig) from comparisons
    comp = [r for r in read(f"{DATA}/wp3_comparisons_single.csv")
            if r["metric"] == "final_gap" and r["effect"] != ""
            and r["treatment"].startswith("B-repair_")]   # repair arms only (drop WP1's B-no_lhs)
    comp.sort(key=lambda r: (r["treatment"], int(r["n_circles"])))
    fig, ax = plt.subplots(figsize=(8, 0.5*len(comp)+1.8))
    ys = list(range(len(comp)))[::-1]
    for y, r in zip(ys, comp):
        eff, lo, hi = float(r["effect"]), float(r["ci_lo"]), float(r["ci_hi"])
        sig = r["marker"] != "ns"
        ax.plot([lo, hi], [y, y], color=C["green"], lw=2, alpha=.8)
        ax.scatter([eff], [y], s=90, zorder=3, edgecolor="black",
                   facecolor=C["green"] if sig else "white")
        ax.annotate(f"{r['marker']}  A12={r['a12']}", (hi, y), textcoords="offset points",
                    xytext=(8, 0), va="center", fontsize=8, color="#222" if sig else C["grey"])
    ax.axvline(0, color="black", lw=1.2)
    ax.set_yticks(ys); ax.set_yticklabels([f"{r['treatment'].replace('B-repair_','')} (n={r['n_circles']})" for r in comp])
    ax.set_xlabel("improvement in gap vs random-repair baseline  (right = better) + bootstrap 95% CI")
    ax.set_title("WP3 · clip/reflect vs random baseline  (filled = significant p<0.05)")
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp3_forest.png", bbox_inches="tight"); plt.close(fig)
    print("wp3_forest.png")


# ── WP1 (Leo): LHS ablation forest (null) — needs wp1_comparisons.csv ────────
def wp1():
    path = f"{DATA}/wp1_comparisons.csv"
    if not os.path.exists(path):
        print("wp1: comparisons.csv not ready yet — skipping (rerun this script after the WP1 run)")
        return
    comp = [r for r in read(path) if r["treatment"] == "B-no_lhs"
            and r["metric"] == "final_gap" and r["effect"] != ""]
    comp.sort(key=lambda r: int(r["n_circles"]))
    fig, ax = plt.subplots(figsize=(8, 0.6*len(comp)+1.8))
    ys = list(range(len(comp)))[::-1]
    for y, r in zip(ys, comp):
        eff, lo, hi = float(r["effect"]), float(r["ci_lo"]), float(r["ci_hi"])
        ax.plot([lo, hi], [y, y], color=C["blue"], lw=2, alpha=.8)
        ax.scatter([eff], [y], s=100, zorder=3, edgecolor="black", facecolor="white")  # all ns => hollow
        ax.annotate(f"{r['marker']}  A12={r['a12']}", (hi, y), textcoords="offset points",
                    xytext=(8, 0), va="center", fontsize=8, color=C["grey"])
    ax.axvline(0, color="black", lw=1.2)
    ax.set_yticks(ys); ax.set_yticklabels([f"remove LHS (n={r['n_circles']})" for r in comp])
    ax.set_xlabel("change in gap when LHS removed (uniform init)  + bootstrap 95% CI")
    ax.set_title("WP1 · LHS ablation: NO measurable effect at any n (all ns)\n"
                 "single-variance baseline, 25 seeds, 100k evals")
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp1_lhs_forest.png", bbox_inches="tight"); plt.close(fig)
    print("wp1_lhs_forest.png")


# ── WP4 (Agata): σ-strategy ablation + recombination ────────────────────────
def wp4_sigma():
    """Grouped bar: single/multiple/full median gap by n — single wins everywhere."""
    runs = read(f"{DATA}/wp4_sigma_per_run.csv")
    ns = sorted({int(r["n_circles"]) for r in runs})
    order = [("SINGLE_VARIANCE", C["green"], "single (1 σ)"),
             ("MULTIPLE_VARIANCE", C["blue"], "multiple (n σ)"),
             ("FULL_VARIANCE", C["bad"], "full (n + rotations)")]

    def med(strat, n):
        return median([r["final_gap"] for r in runs if r["treatment"] == strat and int(r["n_circles"]) == n])

    x = np.arange(len(ns)); w = 0.27
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for i, (strat, col, lbl) in enumerate(order):
        vals = [100*med(strat, n) for n in ns]
        ax.bar(x + (i-1)*w, vals, w, color=col, label=lbl)
    ax.set_xticks(x); ax.set_xticklabels([f"n={n}" for n in ns])
    ax.set_ylabel("median gap to optimum (%)")
    ax.set_title("WP4 · σ-strategy ablation: SINGLE wins at every n (validates the baseline switch)\n"
                 "10 seeds, ~20k-eval budget (early stop)  (lower = better) — full is worst & slowest to adapt")
    ax.legend()
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp4_sigma.png", bbox_inches="tight"); plt.close(fig)
    print("wp4_sigma.png")


def wp4_recomb():
    """Grouped bar: recombination (coord/pair) vs no-recomb baseline — both ~10× worse."""
    runs = read(f"{DATA}/wp4_recomb_per_run.csv")
    ns = sorted({int(r["n_circles"]) for r in runs})
    order = [("baseline", C["baseline"], "no recombination (baseline)"),
             ("sigma_single_recomb_coord", C["bad"], "coordinate recomb"),
             ("sigma_single_recomb_pair", C["orange"], "circle-pair recomb")]

    def med(tr, n):
        return median([r["final_gap"] for r in runs if r["treatment"] == tr and int(r["n_circles"]) == n])

    x = np.arange(len(ns)); w = 0.27
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for i, (tr, col, lbl) in enumerate(order):
        vals = [100*med(tr, n) for n in ns]
        ax.bar(x + (i-1)*w, vals, w, color=col, label=lbl)
        if tr != "baseline":
            for xi, v in zip(x + (i-1)*w, vals):
                ax.annotate("***", (xi, v), textcoords="offset points", xytext=(0, 2),
                            ha="center", fontsize=9, color="#222")
    ax.set_xticks(x); ax.set_xticklabels([f"n={n}" for n in ns])
    ax.set_ylabel("median gap to optimum (%)")
    ax.set_title("WP4 · Naive recombination HURTS badly (A12=0, p≈1.8e-4 everywhere)\n"
                 "single-variance, 10 seeds, ~20k evals  — CiaS permutation symmetry: circle i unaligned across parents")
    ax.legend()
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp4_recomb.png", bbox_inches="tight"); plt.close(fig)
    print("wp4_recomb.png")


# ── Mann–Whitney explainer: why a rank test, not a t-test ────────────────────
def mw_hist():
    """Histogram of the baseline n=10 gap — bimodal/skewed ⇒ mean misleads, use ranks."""
    runs = read(f"{DATA}/wp1_per_run.csv")
    vals = np.array([100*float(r["final_gap"]) for r in runs
                     if r["treatment"] == "baseline" and int(r["n_circles"]) == 10])
    mean, med = vals.mean(), np.median(vals)
    fig, ax = plt.subplots(figsize=(8, 4.4))
    ax.hist(vals, bins=np.arange(0, 60, 4), color=C["blue"], alpha=.8, edgecolor="white")
    ax.axvline(med, color=C["green"], lw=2, label=f"median = {med:.1f}% (what MW/A12 use)")
    ax.axvline(mean, color=C["bad"], lw=2, ls="--", label=f"mean = {mean:.1f}% (what a t-test uses — dragged up by 3 outliers)")
    ax.set_xlabel("final gap to optimum (%)  ·  one bar = a count of seeds")
    ax.set_ylabel("number of seeds (out of 25)")
    ax.set_title("Why NOT a t-test: the baseline n=10 gap is bimodal\n"
                 "22 seeds converge (~7–20%), 3 get stuck (~54%) — the mean lies, the median/rank doesn't")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(f"{FIGS}/mw_hist.png", bbox_inches="tight"); plt.close(fig)
    print("mw_hist.png")


# ── WP5 (Martin): gradient local-search hybrid ──────────────────────────────
def wp5_results():
    """Bars + forest: baseline vs final/interleaved polish across n — REAL 25-seed merged run."""
    runs = read(f"{DATA}/wp5_per_run.csv")
    comp = [r for r in read(f"{DATA}/wp5_comparisons.csv")
            if r["metric"] == "final_gap" and r["treatment"].startswith("B+")]
    ns = sorted({int(r["n_circles"]) for r in runs})
    arms = [("baseline", C["baseline"], "pure EA (baseline)"),
            ("B+final_polish", C["blue"], "EA + final polish"),
            ("B+interleaved_polish", C["orange"], "EA + interleaved polish")]

    def med(tr, n):
        return median([r["final_gap"] for r in runs if r["treatment"] == tr and int(r["n_circles"]) == n])

    def cstat(tr, n):
        r = next((rr for rr in comp if rr["treatment"] == tr and int(rr["n_circles"]) == n), None)
        return (r["marker"], r["a12"]) if r else ("", "")

    # (a) grouped bars with marker/A12 annotations
    x = np.arange(len(ns)); w = 0.27
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for i, (tr, col, lbl) in enumerate(arms):
        vals = [100*med(tr, n) for n in ns]
        ax.bar(x + (i-1)*w, vals, w, color=col, label=lbl)
        if tr != "baseline":
            for xi, n, v in zip(x + (i-1)*w, ns, vals):
                mk, a12 = cstat(tr, n)
                ax.annotate(f"{mk}\nA12={a12}", (xi, v), textcoords="offset points",
                            xytext=(0, 2), ha="center", fontsize=7, color=C["grey"])
    ax.set_xticks(x); ax.set_xticklabels([f"n={n}" for n in ns])
    ax.set_ylabel("median gap to optimum (%)")
    n_sig = sum(1 for r in comp if r["marker"] != "ns")
    verdict = "NO significant gain at any n" if n_sig == 0 else f"significant at {n_sig}/{len(comp)} cells"
    ax.set_title(f"WP5 · Gradient polish vs pure EA — {verdict}\n"
                 "single-variance + random baseline, 25 seeds, 100k evals  (lower = better)")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp5_results.png", bbox_inches="tight"); plt.close(fig)
    print("wp5_results.png")

    # (b) forest of polish effect vs baseline (CI + sig)
    comp.sort(key=lambda r: (r["treatment"], int(r["n_circles"])))
    fig, ax = plt.subplots(figsize=(8, 0.5*len(comp)+1.6))
    ys = list(range(len(comp)))[::-1]
    for y, r in zip(ys, comp):
        eff, lo, hi = float(r["effect"]), float(r["ci_lo"]), float(r["ci_hi"])
        sig = r["marker"] != "ns"
        col = C["blue"] if "final" in r["treatment"] else C["orange"]
        ax.plot([lo, hi], [y, y], color=col, lw=2, alpha=.8)
        ax.scatter([eff], [y], s=90, zorder=3, edgecolor="black",
                   facecolor=col if sig else "white")
        ax.annotate(f"{r['marker']}  A12={r['a12']}", (max(hi, 0), y), textcoords="offset points",
                    xytext=(8, 0), va="center", fontsize=8, color="#222" if sig else C["grey"])
    ax.axvline(0, color="black", lw=1.2)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{r['treatment'].replace('B+','').replace('_',' ')} (n={r['n_circles']})" for r in comp])
    ax.set_xlabel("improvement in gap vs pure-EA baseline  (right = better) + bootstrap 95% CI")
    ax.set_title("WP5 · polish effect vs baseline  (filled = significant p<0.05)")
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp5_forest.png", bbox_inches="tight"); plt.close(fig)
    print("wp5_forest.png")


def wp5_why_flat():
    """Illustrative: the true min-distance objective is FLAT (zero gradient) where the EA
    leaves the best, so finite-difference L-BFGS-B can't move — a smooth surrogate can."""
    x = np.linspace(0, 1, 400)
    # ONE other pair sets a constant floor (0.30); the moved circle's neighbour-distance dips near 0.62
    floor = 0.30
    d_self = np.sqrt((x - 0.62)**2 + 0.006)          # distance of the moved circle to a neighbour
    true_min = np.minimum(floor, d_self)
    beta = 13.0                                       # soft-min temperature (→∞ recovers true min)
    stack = np.vstack([np.full_like(x, floor), d_self])
    soft_min = -1.0/beta * np.log(np.sum(np.exp(-beta*stack), axis=0))
    x0 = 0.33                                          # where the EA left the best (on the flat shelf)

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    ax.plot(x, 100*true_min, color=C["bad"], lw=2.6, label="true fitness = min pairwise distance (what L-BFGS-B optimises)")
    ax.plot(x, 100*soft_min, color=C["green"], lw=2.2, ls="--", label="smooth soft-min surrogate (what the spec asked for)")
    ax.axvline(x0, color=C["grey"], lw=1.1)
    ax.scatter([x0], [100*np.interp(x0, x, true_min)], s=80, zorder=5, color=C["bad"], edgecolor="black")
    ax.scatter([x0], [100*np.interp(x0, x, soft_min)], s=80, zorder=5, color=C["green"], edgecolor="black")
    ax.annotate("EA leaves the best here:\nRED is FLAT → gradient ≈ 0 → L-BFGS-B takes no step",
                (x0, 30.2), xytext=(x0+0.04, 25.5), fontsize=8.5, color=C["bad"],
                arrowprops=dict(arrowstyle="->", color=C["bad"]))
    ax.annotate("GREEN slopes downhill here →\na surrogate gives a usable gradient",
                (x0, 100*np.interp(x0, x, soft_min)), xytext=(x0+0.05, 17.5), fontsize=8.5, color=C["green"],
                arrowprops=dict(arrowstyle="->", color=C["green"]))
    ax.set_xlim(0.05, 0.95)
    ax.set_xlabel("position of one circle along a slice (other circles fixed)")
    ax.set_ylabel("min pairwise distance (%)")
    ax.set_title("WP5 · WHY the polish does nothing (illustrative)\n"
                 "min-distance is non-smooth: only the binding pair has a gradient → most directions are flat")
    ax.legend(fontsize=8, loc="lower center")
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp5_why_flat.png", bbox_inches="tight"); plt.close(fig)
    print("wp5_why_flat.png")


if __name__ == "__main__":
    wp2(); wp3(); wp1(); wp4_sigma(); wp4_recomb(); mw_hist(); wp5_results(); wp5_why_flat()
    print("done")
