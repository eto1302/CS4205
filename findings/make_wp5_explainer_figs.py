"""Conceptual (non-data) figures for the WP5 'how the hybrid works' explainer.

These illustrate the IDEA of a memetic EA+gradient hybrid — global search + local
polish — not real run data. (Real WP5 numbers live in make_findings_figs.py.)

Run:  uv run --with matplotlib --with numpy make_wp5_explainer_figs.py
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

FIGS = "figs"
os.makedirs(FIGS, exist_ok=True)
C = {"ea": "#4C72B0", "grad": "#2ca02c", "bad": "#d62728", "grey": "#888888", "best": "#DD8452"}
plt.rcParams.update({"figure.dpi": 150, "font.size": 10})


def landscape(x):
    return (0.55
            - 0.34*np.exp(-((x-0.68)**2)/0.008)
            - 0.20*np.exp(-((x-0.28)**2)/0.012)
            - 0.14*np.exp(-((x-0.48)**2)/0.006)
            + 0.05*np.sin(20*x))


# ── Figure 1: global (EA) vs local (gradient) on a multi-basin landscape ─────
def fig_landscape():
    x = np.linspace(0, 1, 600)
    y = landscape(x)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), sharey=True)

    # left — EA explores globally
    ax = axes[0]
    ax.plot(x, y, color="#444", lw=2)
    pop = np.array([0.06, 0.17, 0.28, 0.40, 0.48, 0.59, 0.66, 0.80, 0.92])
    py = landscape(pop)
    best = np.argmin(py)
    ax.scatter(pop, py, s=70, color=C["grey"], edgecolor="black", zorder=3, label="EA population (candidate packings)")
    ax.scatter([pop[best]], [py[best]], s=130, color=C["ea"], edgecolor="black", zorder=4, label="current best")
    ax.set_title("Step 1 — EA searches GLOBALLY\n(spreads out, finds the right valley)")
    ax.legend(fontsize=8, loc="upper right")

    # right — gradient polishes locally
    ax = axes[1]
    ax.plot(x, y, color="#444", lw=2)
    start = 0.635                       # EA best: in the valley but not at the bottom
    bottom = x[np.argmin(y)]            # true local minimum
    ax.scatter([start], [landscape(start)], s=130, color=C["ea"], edgecolor="black", zorder=4, label="EA best (good, not exact)")
    ax.scatter([bottom], [landscape(bottom)], s=150, marker="*", color=C["grad"], edgecolor="black", zorder=5, label="after gradient polish (exact bottom)")
    ax.annotate("", xy=(bottom, landscape(bottom)+0.005), xytext=(start, landscape(start)),
                arrowprops=dict(arrowstyle="-|>", color=C["grad"], lw=2.4,
                                connectionstyle="arc3,rad=-0.25"))
    ax.text(0.70, landscape(start)-0.02, "gradient\nrolls downhill", color=C["grad"], fontsize=9)
    ax.set_title("Step 2 — gradient polishes LOCALLY\n(rolls the best to the exact bottom)")
    ax.legend(fontsize=8, loc="upper right")

    for ax in axes:
        ax.set_xlabel("space of possible packings (simplified to 1 axis)")
        ax.set_yticks([])
    axes[0].set_ylabel("gap to optimum  (lower = better)")
    fig.suptitle("The hybrid idea (memetic search): the EA finds the right valley, the gradient finds its bottom", fontsize=11)
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp5_memetic_landscape.png", bbox_inches="tight"); plt.close(fig)
    print("wp5_memetic_landscape.png")


# ── Figure 2: the hybrid loop as a flow diagram ─────────────────────────────
def fig_loop():
    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    def box(cx, cy, w, h, text, fc):
        ax.add_patch(FancyBboxPatch((cx-w/2, cy-h/2), w, h, boxstyle="round,pad=0.12",
                                    fc=fc, ec="black", lw=1.4, alpha=0.92))
        ax.text(cx, cy, text, ha="center", va="center", fontsize=8.6)

    def arrow(p, q, color="black", rad=0.0, txt=None, tx=0, ty=0):
        ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=16,
                                     lw=1.6, color=color, connectionstyle=f"arc3,rad={rad}"))
        if txt: ax.text((p[0]+q[0])/2+tx, (p[1]+q[1])/2+ty, txt, fontsize=8, color=color, ha="center")

    box(2.6, 9.1, 4.2, 1.0, "1 · Initialise population\n(LHS — spread starting points)", "#dfe7f3")
    box(2.6, 6.7, 4.6, 1.5, "2 · EA generation (GLOBAL search)\n• mutate with self-adaptive σ\n• evaluate fitness\n• keep the survivors  (μ,λ)", "#cfe0f0")
    box(7.7, 6.7, 4.0, 1.5, "INTERLEAVED mode:\nevery K generations →\nL-BFGS-B polish the best,\nput it back in the pop", "#d7efd7")
    box(2.6, 3.7, 4.6, 1.1, "3 · Budget spent?\n(gradient evals count too)", "#eee")
    box(2.6, 1.5, 4.6, 1.2, "4 · FINAL mode:\none L-BFGS-B polish of the best", "#d7efd7")
    box(7.7, 1.5, 3.6, 1.0, "5 · Return best packing", "#f3e2d2")

    arrow((2.6, 8.6), (2.6, 7.45))                                   # 1→2
    arrow((4.9, 6.7), (5.7, 6.7), color=C["grad"])                  # 2→interleaved
    arrow((5.7, 6.2), (4.9, 6.2), color=C["grad"], rad=0.0)          # interleaved→2 (back)
    arrow((2.6, 5.95), (2.6, 4.25))                                  # 2→budget
    # single elbow rail: budget(no) → left → up → back into EA box
    ax.plot([0.30, 0.15, 0.15, 0.30], [3.7, 3.7, 6.7, 6.7], color=C["ea"], lw=1.7)
    ax.add_patch(FancyArrowPatch((0.20, 6.7), (0.32, 6.7), arrowstyle="-|>", mutation_scale=16,
                                 lw=1.7, color=C["ea"]))
    ax.text(0.42, 5.2, "no → next generation", fontsize=8, color=C["ea"], rotation=90, va="center")
    arrow((2.6, 3.15), (2.6, 2.1), txt="yes", tx=0.35)              # budget→final
    arrow((4.9, 1.5), (5.9, 1.5))                                    # final→return

    ax.text(5.0, 9.8, "EA + gradient hybrid — two search modes share ONE eval budget",
            ha="center", fontsize=11, weight="bold")
    ax.text(7.7, 8.4, "GREEN = local (gradient) search\nBLUE rail = the EA loop",
            ha="center", fontsize=8.2, color="#333")
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp5_hybrid_loop.png", bbox_inches="tight"); plt.close(fig)
    print("wp5_hybrid_loop.png")


# ── Figure 3: WHEN each mode acts (intended convergence behaviour) ───────────
def fig_when():
    e = np.linspace(0, 100, 500)                      # thousands of evals
    ea = 0.05 + 0.45*np.exp(-e/16)                     # pure EA convergence
    final = ea.copy()
    final[e > 90] = ea[e > 90] - 0.018*((e[e > 90]-90)/10)   # one drop at the very end
    inter = ea.copy()
    for k in range(15, 100, 15):                       # periodic polish dips
        inter[e >= k] -= 0.012*np.exp(-(e[e >= k]-k)/4)
    fig, ax = plt.subplots(figsize=(9, 4.6))
    ax.plot(e, 100*ea, color=C["grey"], lw=2.4, label="pure EA")
    ax.plot(e, 100*final, color=C["ea"], lw=2.0, ls="--", label="EA + FINAL polish (one polish at the end)")
    ax.plot(e, 100*inter, color=C["grad"], lw=2.0, label="EA + INTERLEAVED polish (a polish every K generations)")
    ax.set_xlabel("evaluations used  (× 1000)  →  shared budget")
    ax.set_ylabel("gap to optimum (%)")
    ax.set_title("WHEN each polish acts (intended behaviour)\nfinal = one nudge at the end · interleaved = small nudges throughout")
    ax.grid(alpha=0.3); ax.legend(fontsize=8.5)
    ax.text(50, 35, "(on CiaS these nudges turn out tiny —\nsee why_flat: the objective is non-smooth)",
            fontsize=8, color=C["bad"], ha="center")
    fig.tight_layout(); fig.savefig(f"{FIGS}/wp5_when_polish.png", bbox_inches="tight"); plt.close(fig)
    print("wp5_when_polish.png")


if __name__ == "__main__":
    fig_landscape(); fig_loop(); fig_when()
    print("done")
