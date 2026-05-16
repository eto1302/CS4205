# Code Explanation

The code solves the **"Circles in a Square"** problem using **Evolution Strategies (ES)**.

The goal is to pack `n` circles inside a unit square (side length `1`) so they are as far apart from each other as possible — meaning you want to **maximize the minimum distance** between any two circle centers.

---

# The Fitness Functions

```python
def circles_in_a_square(individual):
    n = len(individual)
    distances = []

    for i in range(0, n - 1, 2):
        for j in range(i + 2, n, 2):
            distances.append(
                math.sqrt(
                    math.pow((individual[i] - individual[j]), 2)
                    + math.pow((individual[i + 1] - individual[j + 1]), 2)
                )
            )

    return min(distances)
```

An individual is represented as a flat list of coordinates:

```python
[x0, y0, x1, y1, ..., xn, yn]
```

Each `(x, y)` pair represents the center of one circle.

The function:

1. Computes the Euclidean distance between every pair of circles
2. Stores all distances
3. Returns the **minimum** distance

A **larger minimum distance** means a better circle packing configuration.

## Two Implementations

- **Pure Python (`circles_in_a_square`)**
  - Faster for fewer than 12 circles

- **NumPy/SciPy (`circles_in_a_square_scipy`)**
  - Faster for 12+ circles due to vectorized distance matrix computation

---

# The `CirclesInASquare` Class

## Constructor

```python
def __init__(self, n_circles, output_statistics=True,
             plot_sols=False, print_sols=False):
```

Sets up the optimization problem.

## Key Parameters

| Parameter | Description |
|---|---|
| `n_circles` | Number of circles to pack (`2–20`) |
| `output_statistics` | Print progress for each generation |
| `plot_sols` | Display a live matplotlib plot of the best solution |
| `print_sols` | Print solutions during execution |

---

# Known Optimal Values

```python
def get_target(self):
    values_to_reach = [1.414213..., 1.035276..., ...]
    return values_to_reach[self.n_circles - 2]
```

These are the known optimal minimum distances for each number of circles.

The algorithm stops early if it reaches the target value within a tolerance threshold.

---

# Running Evolution Strategies

```python
def run_evolution_strategies(self):
    evopy = EvoPy(
        circles_in_a_square,
        self.n_circles * 2,
        maximize=True,
        generations=1000,
        bounds=(0, 1),
        target_fitness_value=self.get_target(),
        max_evaluations=1e5,
    )

    best_solution = evopy.run()
```

This is the core optimization routine.

## EvoPy Configuration

| Argument | Purpose |
|---|---|
| `circles_in_a_square` | Fitness function to optimize |
| `self.n_circles * 2` | Number of variables (`x` and `y` for each circle) |
| `maximize=True` | Maximize the minimum distance |
| `generations=1000` | Maximum number of generations |
| `bounds=(0, 1)` | Keep coordinates inside the unit square |
| `target_fitness_value` | Stop early if optimal packing is reached |
| `max_evaluations=1e5` | Limit total fitness evaluations |

`EvoPy` internally handles:

- Mutation
- Selection
- Population updates
- Evolution loop execution

---

# Program Entry Point

```python
if __name__ == "__main__":
    circles = 10

    runner = CirclesInASquare(
        circles,
        plot_sols=True
    )

    best = runner.run_evolution_strategies()
```

This starts the program by:

1. Packing `10` circles
2. Enabling live plotting
3. Running the Evolution Strategies optimizer
4. Returning the best solution found