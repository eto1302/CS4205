import matplotlib
matplotlib.use('TkAgg')

import math
from ES.evopy import EvoPy
from ES.evopy import ProgressReport
from sklearn.metrics.pairwise import euclidean_distances
import matplotlib.pyplot as plt
import numpy as np
from ES.evopy.strategy import Strategy
from matplotlib.patches import Circle
from matplotlib.colors import Normalize

###########################################################
#                                                         #
# EvoPy framework from https://github.com/evopy/evopy     #
# Read documentation on github for further information.   #
#                                                         #
# Adjustments by Renzo Scholman:                          #
#       Added evaluation counter (also in ProgressReport) #
#       Added max evaluation stopping criterion           #
#       Added random repair for solution                  #
#       Added target fitness value tolerance              #
#                                                         #
# Original license stored in LICENSE file                 #
#                                                         #
# Install required dependencies with:                     #
#       pip install -r requirements.dev.txt               #
#                                                         #
###########################################################

_N7_OPTIMAL = np.array([
    -0.325542369812990561040572795501,  -0.325542369812990561040572795501,
    0.023372890561028316878281613499,  -0.325542369812990561040572795500,
    0.325542369812990561040572795500,  -0.151084739625981122081145591001,
    -0.325542369812990561040572795500,   0.023372890561028316878281613499,
    0.023372890561028316878281613499,   0.023372890561028316878281613499,
    0.300000000000000000000000000000,   0.300000000000000000000000000000,
    -0.151084739625981122081145591001,   0.325542369812990561040572795500])

def plot_fitness_landscape(
    n_circles: int = 7,
    base: str = "optimal",
    grid_res: int = 60,
    figsize_per_cell: float = 1.5,
    cmap: str = "inferno",
    save_path: str = None,
    box_side: float = 0.6510847396259811,
):
    """Plot the pairwise-variable fitness landscape heatmap for the CiaS problem."""
    if n_circles != 7:
        raise NotImplementedError(
            "Only n_circles=7 is supported. "
            "For other n pass base='random' or extend _N7_OPTIMAL."
        )

    d = 2 * n_circles
    half_box = box_side / 2.0

    # -- 1. Base solution ------------------------------------------------
    if base == "optimal":
        sol = _N7_OPTIMAL.copy()
    elif base == "random":
        rng = np.random.default_rng(seed=0)
        sol = rng.uniform(-half_box, half_box, size=d)
    else:
        raise ValueError("base must be 'optimal' or 'random'")

    # -- 2. Compute fitness on a grid for every variable pair ------------
    grid = np.linspace(-half_box, half_box, grid_res)
    fitness_maps = {}

    for i in range(d):
        fitness_maps[i] = {}
        for j in range(d):
            ind = sol.copy()
            if i == j:
                vals = np.empty(grid_res)
                for k, v in enumerate(grid):
                    ind[i] = v
                    vals[k] = circles_in_a_square_scipy(ind)
                fitness_maps[i][j] = vals
            else:
                mat = np.empty((grid_res, grid_res))
                for ki, vi in enumerate(grid):
                    ind[i] = vi
                    for kj, vj in enumerate(grid):
                        ind[j] = vj
                        mat[ki, kj] = circles_in_a_square_scipy(ind)
                fitness_maps[i][j] = mat

    # Shared colour scale across all 2-D subplots
    all_2d = np.concatenate([
        fitness_maps[i][j].ravel()
        for i in range(d) for j in range(d) if i != j
    ])
    norm = Normalize(vmin=all_2d.min(), vmax=all_2d.max())
    line_color = "red" if base == "optimal" else "blue"

    # -- 3. Build the figure ---------------------------------------------
    fig, axes = plt.subplots(d, d, figsize=(figsize_per_cell * d, figsize_per_cell * d))
    base_label = "near-optimal" if base == "optimal" else "random"
    fig.suptitle(
        f"Fitness landscape — CiaS  n={n_circles}  ({base_label} base solution)\n"
        "Methodology: Bosman & Gallagher (2016), §3",
        fontsize=11,
    )

    for i in range(d):
        for j in range(d):
            ax = axes[i, j]
            ax.set_xticks([])
            ax.set_yticks([])

            if i == j:
                ax.plot(grid, fitness_maps[i][j], color=line_color, lw=1.2)
                ax.axvline(sol[i], color="white", lw=1.0, ls="--")
                ax.set_facecolor("#1a1a1a")
            else:
                ax.imshow(
                    fitness_maps[i][j],
                    extent=[-half_box, half_box, -half_box, half_box],
                    origin="lower",
                    aspect="auto",
                    cmap=cmap,
                    norm=norm,
                )
                ax.margins(0)
                ax.plot(
                    sol[j], sol[i],
                    "o", color="black",
                    markersize=3, markeredgewidth=0.5,
                    markeredgecolor="white"
                )

            if j == 0:
                ax.set_ylabel(f"$x_{{{i}}}$", fontsize=7, labelpad=2)

            if i == d - 1:
                ax.set_xlabel(f"$x_{{{j}}}$", fontsize=7, labelpad=2)

            ax.tick_params(
                left=False, bottom=False,
                labelleft=False, labelbottom=False
            )

    # Shared colourbar on the right
    cbar_ax = fig.add_axes([0.92, 0.15, 0.015, 0.7])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("Fitness  (min pairwise dist)", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    plt.subplots_adjust(
        left=0.05, right=0.88, top=0.88, bottom=0.05,
        wspace=0.0, hspace=0.0
    )

    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches="tight")
        print(f"Saved to {save_path}")

    plt.show()
    return fig

# np/scipy CiaS implementation is faster for higher problem dimensions, i.e, more than 11 or 12 circles.
def circles_in_a_square_scipy(individual):
   points = np.reshape(individual, (-1, 2))
   dist = euclidean_distances(points)
   np.fill_diagonal(dist, 1e10)
   return np.min(dist)

# Pure python implementation is faster for lower problem dimensions
def circles_in_a_square(individual):
    n = len(individual)
    distances = []
    for i in range(0, n-1, 2):
        for j in range(i + 2, n, 2):
            distances.append(math.sqrt(math.pow((individual[i] - individual[j]), 2)
                              + math.pow((individual[i + 1] - individual[j + 1]), 2)))
    return min(distances)

def plot_circle_pair_landscapes(
    n_circles: int = 7,
    base: str = "optimal",
    grid_res: int = 60,
    figsize_per_pair: float = 2.0,
    cmap: str = "inferno",
    save_path: str = None,
    box_side: float = 0.6510847396259811,
):
    """
    Plot 2D fitness landscapes only for paired circle coordinates:
    (x0,x1), (x2,x3), ..., (x12,x13) for n=7.
    """
    if n_circles != 7:
        raise NotImplementedError("Only n_circles=7 is supported.")

    d = 2 * n_circles
    if d % 2 != 0:
        raise ValueError("Need an even number of variables.")

    half_box = box_side / 2.0
    grid = np.linspace(-half_box, half_box, grid_res)

    if base == "optimal":
        sol = _N7_OPTIMAL.copy()
    elif base == "random":
        rng = np.random.default_rng(seed=0)
        sol = rng.uniform(-half_box, half_box, size=d)
    else:
        raise ValueError("base must be 'optimal' or 'random'")

    pair_indices = [(k, k + 1) for k in range(0, d, 2)]
    n_pairs = len(pair_indices)

    fitness_maps = []
    for i, j in pair_indices:
        mat = np.empty((grid_res, grid_res))
        ind = sol.copy()
        for gi, xi in enumerate(grid):
            ind[i] = xi
            for gj, xj in enumerate(grid):
                ind[j] = xj
                mat[gi, gj] = circles_in_a_square_scipy(ind)
        fitness_maps.append(mat)

    all_vals = np.concatenate([m.ravel() for m in fitness_maps])
    norm = Normalize(vmin=all_vals.min(), vmax=all_vals.max())
    line_color = "red" if base == "optimal" else "blue"

    fig, axes = plt.subplots(
        1,
        n_pairs,
        figsize=(figsize_per_pair * n_pairs, figsize_per_pair),
        squeeze=False,
    )
    axes = axes[0]

    base_label = "near-optimal" if base == "optimal" else "random"
    fig.suptitle(
        f"Fitness landscape for circle coordinate pairs — CiaS n={n_circles} ({base_label})",
        fontsize=11,
    )

    for idx, (i, j) in enumerate(pair_indices):
        ax = axes[idx]
        ax.imshow(
            fitness_maps[idx],
            extent=[-half_box, half_box, -half_box, half_box],
            origin="lower",
            aspect="auto",
            cmap=cmap,
            norm=norm,
        )
        ax.plot(sol[j], sol[i], "o", color="black", markersize=3,
                markeredgewidth=0.5, markeredgecolor="white")
        ax.set_title(f"($x_{{{i}}}$, $x_{{{j}}}$)", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])

    cbar_ax = fig.add_axes([0.92, 0.18, 0.015, 0.65])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cb = fig.colorbar(sm, cax=cbar_ax)
    cb.set_label("Fitness", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    plt.subplots_adjust(left=0.03, right=0.9, top=0.82, bottom=0.05, wspace=0.08)

    if save_path:
        fig.savefig(save_path, dpi=120, bbox_inches="tight")

    plt.show()
    return fig

def draw_contact_spokes(ax, points_scaled, radius, tol=1e-6):
    """
    Draw Packomania-style contact spokes:
    one radius from the circle center to every contact point.
    """
    if tol is None:
        tol = radius * 1e-3

    n = len(points_scaled)

    for i in range(n):
        x, y = points_scaled[i]

        # -------------------------
        # Circle-circle contacts
        # -------------------------
        for j in range(n):
            if i == j:
                continue

            dx = points_scaled[j, 0] - x
            dy = points_scaled[j, 1] - y

            d = np.hypot(dx, dy)

            if abs(d - 2 * radius) <= tol:
                ux = dx / d
                uy = dy / d

                # spoke from center to circumference
                ax.plot(
                    [x, x + radius/2 * ux],
                    [y, y + radius/2 * uy],
                    color="darkblue",
                    lw=1,
                    zorder=5,
                )

        # -------------------------
        # Wall contacts
        # -------------------------
        if abs(x - radius) <= tol:
            ax.plot(
                [x, x - radius/2],
                [y, y],
                color="darkblue",
                lw=1,
                zorder=5,
            )

        if abs(x - (1 - radius)) <= tol:
            ax.plot(
                [x, x + radius/2],
                [y, y],
                color="darkblue",
                lw=1,
                zorder=5,
            )

        if abs(y - radius) <= tol:
            ax.plot(
                [x, x],
                [y, y - radius/2],
                color="darkblue",
                lw=1,
                zorder=5,
            )

        if abs(y - (1 - radius)) <= tol:
            ax.plot(
                [x, x],
                [y, y + radius/2],
                color="darkblue",
                lw=1,
                zorder=5,
            )

        # center marker
        ax.plot(x, y, "wo", ms=2, mec="darkblue", mew=0.5, zorder=6)
class CirclesInASquare:
    def __init__(self, n_circles, output_statistics=True, plot_sols=False, print_sols=False):
        self.print_sols = print_sols
        self.output_statistics = output_statistics
        self.plot_best_sol = plot_sols
        self.n_circles = n_circles
        self.fig = None
        self.ax = None
        assert 2 <= n_circles <= 20

        if self.plot_best_sol:
            self.set_up_plot()

        if self.output_statistics:
            self.statistics_header()

    def set_up_plot(self):
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlabel("$x_0$")
        self.ax.set_ylabel("$x_1$")
        self.ax.set_title("Best solution in generation 0")
        self.fig.show()

    def statistics_header(self):
        if self.print_sols:
            print("Generation Evaluations Best-fitness (Best individual..)")
        else:
            print("Generation Evaluations Best-fitness")

    def statistics_callback(self, report: ProgressReport):
        output = "{:>10d} {:>11d} {:>12.8f} {:>12.8f} {:>12.8f}".format(report.generation, report.evaluations,
                                                                        report.best_fitness, report.avg_fitness,
                                                                        report.std_fitness)

        if self.print_sols:
            output += " ({:s})".format(np.array2string(report.best_genotype))
        print(output)

        if self.plot_best_sol:
            points = np.reshape(report.best_genotype, (-1, 2))
            self.ax.clear()
            # report.best_fitness is the minimal pairwise centre distance (fitness)
            # circle radius must be at most half that distance to avoid overlaps
            max_radius = float(report.best_fitness) / 2.0
            for (x, y) in points:
                # also ensure circle stays inside the unit square
                r = min(max_radius, x, y, 1.0 - x, 1.0 - y)
                circ = Circle((x, y), r, edgecolor="black", facecolor="none")
                self.ax.add_patch(circ)
            self.ax.set_xlim((0, 1))
            self.ax.set_ylim((0, 1))
            self.ax.set_aspect('equal', adjustable='box')
            self.ax.set_title("Best solution in generation {:d}".format(report.generation))
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()

    def get_target(self):
        values_to_reach = [
            1.414213562373095048801688724220,  # 2
            1.035276180410083049395595350499,  # 3
            1.000000000000000000000000000000,  # 4
            0.707106781186547524400844362106,  # 5
            0.600925212577331548853203544579,  # 6
            0.535898384862245412945107316990,  # 7
            0.517638090205041524697797675248,  # 8
            0.500000000000000000000000000000,  # 9
            0.421279543983903432768821760651,  # 10
            0.398207310236844165221512929748,
            0.388730126323020031391610191835,
            0.366096007696425085295389370603,
            0.348915260374018877918854409001,
            0.341081377402108877637121191351,
            0.333333333333333333333333333333,
            0.306153985300332915214516914060,
            0.300462606288665774426601772290,
            0.289541991994981660261698764510,
            0.286611652351681559449894454738
        ]

        return values_to_reach[self.n_circles - 2]

    # def run_evolution_strategies(self, seed=None, repair="random"):
    #     callback = self.statistics_callback if self.output_statistics else None

    #     evopy = EvoPy(
    #         circles_in_a_square if self.n_circles < 12 else circles_in_a_square_scipy,  # Fitness function
    #         self.n_circles * 2,  # Number of parameters
    #         reporter=callback,  # Prints statistics at each generation
    #         maximize=True,
    #         generations=1000,
    #         bounds=(0, 1),
    #         target_fitness_value=self.get_target(),
    #         max_evaluations=1e5,
    #         strategy=Strategy.SINGLE_VARIANCE,  # matches the OFAT baseline B
    #         num_children=7,  # lambda/mu = 210/30 = 7 (BSw95 ratio); matches benchmark.py
    #         random_seed=seed,
    #         repair=repair,
    #     )

    #     best_solution = evopy.run()

    #     if self.plot_best_sol:
    #         plt.close()

    #     return best_solution
    
    def run_evolution_strategies(self, seed=None, repair="random"):
        callback = self.statistics_callback if self.output_statistics else None

        evopy = EvoPy(
            circles_in_a_square if self.n_circles < 12 else circles_in_a_square_scipy,
            self.n_circles * 2,
            reporter=callback,
            maximize=True,
            generations=1000,
            population_size=30,
            num_children=7,           # lambda/mu = 210/30 = 7, matches benchmark
            bounds=(0, 1),
            target_fitness_value=self.get_target(),
            max_evaluations=1e5,
            strategy=Strategy.SINGLE_VARIANCE,
            selection_scheme="comma", # matches benchmark
            init="lhs",               # matches benchmark
            random_seed=seed,
            repair=repair,
        )

        best_solution = evopy.run()

        if self.plot_best_sol:
            plt.close()

        return best_solution
    

    
    def plot_final_packing(self, genotype, save_path=None):
            fitness_fn = circles_in_a_square_scipy if self.n_circles >= 12 else circles_in_a_square
            fitness = fitness_fn(genotype)
            points = np.reshape(genotype, (-1, 2))
            max_radius = fitness / (2 + 2 * fitness)
            scale = 1.0 - 2 * max_radius
            points_scaled = points * scale + max_radius

            fig, ax = plt.subplots(figsize=(6, 6))
            ax.set_aspect("equal")
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)

            for i, (x, y) in enumerate(points_scaled):
                ax.add_patch(Circle((x, y), max_radius,
                                    edgecolor="black", facecolor="steelblue", alpha=0.4))
                ax.plot(x, y, "k.", markersize=4)
                ax.text(x, y, str(i + 1), ha="center", va="center",
                        fontsize=8, fontweight="bold")
            
            draw_contact_spokes(ax, points_scaled, max_radius)

            optimum = self.get_target()
            gap = (optimum - fitness) / optimum * 100
            ax.set_title(
                f"Best packing — n={self.n_circles} circles\n"
                f"fitness={fitness:.6f}  |  optimum={optimum:.6f}  |  gap={gap:.4f}%",
                fontsize=10
            )
            ax.set_xlabel("x")
            ax.set_ylabel("y")
            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches="tight")
                plt.close(fig)
            else:
                plt.show()



if __name__ == "__main__":
    ### WP3 Results ###################################################################
    # # # Clip — best seed is 0
    # runner_clip = CirclesInASquare(15, output_statistics=False)
    # best_clip = runner_clip.run_evolution_strategies(seed=0, repair="clip")
    # runner_clip.plot_final_packing(best_clip, save_path="best_packing_n15_clip_seed0.png")

    # # # Reflect — best seed is 7
    # runner_reflect = CirclesInASquare(15, output_statistics=False)
    # best_reflect = runner_reflect.run_evolution_strategies(seed=7, repair="reflect")
    # runner_reflect.plot_final_packing(best_reflect, save_path="best_packing_n15_reflect_seed7.png")

    # #Random — best seed is 7
    # runner_reflect = CirclesInASquare(15, output_statistics=False)
    # best_reflect = runner_reflect.run_evolution_strategies(seed=17, repair="random")
    # runner_reflect.plot_final_packing(best_reflect, save_path="best_packing_n15_random_seed17.png")

    # --- Option B: plot the fitness landscape (Bosman & Gallagher Fig 2 style) ---
    plot_fitness_landscape(
        n_circles=7,
        base="optimal",   # or "random"
        grid_res=60,      # lower (30) for a quick preview
        save_path="landscape_n7_optimal.png",   # e.g. "landscape_n7_optimal.png"
    )

    plot_circle_pair_landscapes(
    n_circles=7,
    base="optimal",      # or "random"
    grid_res=60,         # quick preview
    save_path="pair_landscape_n7_optimal.png",
    )