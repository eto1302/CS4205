from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.lines as mlines

try:
    from scipy.stats import mannwhitneyu
    SCIPY_OK = True
except Exception:
    SCIPY_OK = False


ROOT = Path(
    r"C:\Users\agata\OneDrive\Pulpit\uni\! Master - StudyGuides\Q4\Evolutionary Algorithms\Assignment\CS4205"
)

RECOMB_DIR = (
    ROOT
    / "benchmark_wp4_results"
    / "benchmark_recomb_best_sigma_directed_100k_25seeds_2026-06-05_12-04-37"
)

PER_RUN = RECOMB_DIR / "per_run.csv"

if not PER_RUN.exists():
    raise FileNotFoundError(f"Could not find recombination per_run.csv:\n{PER_RUN}")

OUT = ROOT / "benchmark_wp4_results" / "slide_figures"
OUT.mkdir(parents=True, exist_ok=True)

METRIC = "final_gap"


def marker(p):
    if p is None:
        return "NA"
    return "***" if p < 1e-3 else "**" if p < 1e-2 else "*" if p < 5e-2 else "ns"


def a12_lower_is_better(arm, base):
    """
    A12 = P(arm beats baseline) + 0.5 P(tie).
    Lower final_gap is better, so arm beats base if arm < base.
    A12 > 0.5 means arm is better than baseline.
    A12 < 0.5 means arm is worse than baseline.
    """
    arm = np.asarray(arm, dtype=float)
    base = np.asarray(base, dtype=float)

    lt = sum((arm < b).sum() for b in base)
    eq = sum((arm == b).sum() for b in base)

    return (lt + 0.5 * eq) / (len(arm) * len(base))


def boot_ci(base, arm, n_boot=3000, seed=0):
    """
    Bootstrap 95% CI for:
    effect = median(base) - median(arm)

    Positive effect = recombination has lower final_gap than baseline = better.
    Negative effect = recombination has higher final_gap than baseline = worse.
    """
    rng = np.random.default_rng(seed)
    base = np.asarray(base, dtype=float)
    arm = np.asarray(arm, dtype=float)

    diffs = np.empty(n_boot)
    for i in range(n_boot):
        b = rng.choice(base, len(base), replace=True)
        a = rng.choice(arm, len(arm), replace=True)
        diffs[i] = np.median(b) - np.median(a)

    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def treatment_label(t):
    return {
        "coordinate": "coordinate",
        "circle_pair": "circle_pair",
    }.get(t, t)


def compute_recomb_rows(df, baseline_strategy, n_values):
    """
    Compare coordinate/circle_pair against baseline/no recombination
    for the same strategy and same n.
    """
    rows = []

    for n in n_values:
        base = df[
            (df["n_circles"] == n)
            & (df["strategy"] == baseline_strategy)
            & (df["treatment"] == "baseline")
        ][METRIC].dropna().to_numpy()

        if len(base) == 0:
            print(f"Missing baseline: strategy={baseline_strategy}, n={n}")
            continue

        for treatment in ["circle_pair", "coordinate"]:
            arm = df[
                (df["n_circles"] == n)
                & (df["strategy"] == baseline_strategy)
                & (df["treatment"] == treatment)
            ][METRIC].dropna().to_numpy()

            if len(arm) == 0:
                print(f"Missing arm: strategy={baseline_strategy}, n={n}, treatment={treatment}")
                continue

            effect = float(np.median(base) - np.median(arm))
            ci_lo, ci_hi = boot_ci(base, arm, seed=2000 + int(n) + (0 if treatment == "circle_pair" else 100))

            if SCIPY_OK:
                p = float(mannwhitneyu(arm, base, alternative="two-sided").pvalue)
            else:
                p = None

            rows.append({
                "treatment": treatment,
                "strategy": baseline_strategy,
                "wp": "WP4",
                "n_circles": int(n),
                "metric": METRIC,
                "n_base": len(base),
                "n_arm": len(arm),
                "base_median": float(np.median(base)),
                "arm_median": float(np.median(arm)),
                "effect": effect,
                "ci_lo": ci_lo,
                "ci_hi": ci_hi,
                "a12": a12_lower_is_better(arm, base),
                "p_value": p,
                "marker": marker(p),
            })

    return pd.DataFrame(rows)


def plot_forest(rows, out_name, baseline_strategy):
    if rows.empty:
        raise ValueError(f"No rows to plot for {out_name}")

    # Original-style ordering: treatment, then n
    treatment_order = {"circle_pair": 0, "coordinate": 1}
    rows = rows.copy()
    rows["treatment_rank"] = rows["treatment"].map(treatment_order)
    rows = rows.sort_values(["treatment_rank", "n_circles"], ascending=[True, True])

    fig, ax = plt.subplots(figsize=(7.4, max(3.2, 0.46 * len(rows) + 1.7)))
    ys = list(range(len(rows)))[::-1]

    for y, (_, r) in zip(ys, rows.iterrows()):
        sig = r["marker"] != "ns"

        ax.plot(
            [r["ci_lo"], r["ci_hi"]],
            [y, y],
            color="#4C72B0",
            lw=2.4,
            alpha=0.85,
        )
        ax.scatter(
            [r["effect"]],
            [y],
            s=105,
            zorder=3,
            edgecolor="black",
            facecolor="#4C72B0" if sig else "white",
            linewidth=1.1,
        )

        ax.annotate(
            f"{r['marker']}  A12={r['a12']:.3g}",
            (r["ci_hi"], y),
            textcoords="offset points",
            xytext=(7, 0),
            va="center",
            fontsize=9,
            color="#222" if sig else "#888",
        )

    ax.axvline(0, color="black", lw=1.2)

    ax.annotate(
        "baseline",
        xy=(0, 1.015),
        xycoords=("data", "axes fraction"),
        ha="center",
        va="bottom",
        fontsize=9,
    )

    ax.set_yticks(ys)
    ax.set_yticklabels(
        [
            f"{treatment_label(r['treatment'])}  (n={int(r['n_circles'])})"
            for _, r in rows.iterrows()
        ],
        fontsize=10,
    )

    ax.set_xlabel(
        f"improvement in median {METRIC} vs baseline  (right = better)",
        fontsize=10,
    )

    ax.set_title(
        f"OFAT forest plot — {METRIC}\n"
        f"baseline = {baseline_strategy}, filled = significant (p<0.05), hollow = ns",
        fontsize=10.5,
        pad=10,
    )

    ax.grid(True, axis="x", alpha=0.25)

    handles = [
        mlines.Line2D([], [], marker="o", ls="", color="#4C72B0", label="significant"),
        mlines.Line2D(
            [], [], marker="o", ls="", markerfacecolor="white",
            markeredgecolor="black", color="white", label="ns"
        ),
    ]
    ax.legend(handles=handles, fontsize=8, loc="lower right")

    fig.tight_layout()

    out = OUT / out_name
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"saved {out}")


df = pd.read_csv(PER_RUN)

required = {"treatment", "strategy", "n_circles", METRIC}
missing = required - set(df.columns)
if missing:
    raise ValueError(f"Missing required columns: {missing}")

df["treatment"] = df["treatment"].astype(str).str.strip()
df["strategy"] = df["strategy"].astype(str).str.strip()
df["n_circles"] = df["n_circles"].astype(int)

print(f"Using: {PER_RUN}")
print("\nCounts:")
print(df.groupby(["strategy", "treatment", "n_circles"]).size())

# Plot 1: MULTIPLE baseline, all n
multiple_rows = compute_recomb_rows(
    df=df,
    baseline_strategy="MULTIPLE_VARIANCE",
    n_values=[7, 10, 15, 20],
)
multiple_rows.to_csv(OUT / "recomb_forest_multiple_baseline_values.csv", index=False)
plot_forest(
    multiple_rows,
    out_name="recomb_forest_multiple_baseline.png",
    baseline_strategy="MULTIPLE_VARIANCE",
)

# Plot 2: SINGLE baseline, n=7 and n=10 only
single_rows = compute_recomb_rows(
    df=df,
    baseline_strategy="SINGLE_VARIANCE",
    n_values=[7, 10],
)
single_rows.to_csv(OUT / "recomb_forest_single_baseline_values.csv", index=False)
plot_forest(
    single_rows,
    out_name="recomb_forest_single_baseline.png",
    baseline_strategy="SINGLE_VARIANCE",
)

print("\nDone.")
print(f"Output folder: {OUT}")