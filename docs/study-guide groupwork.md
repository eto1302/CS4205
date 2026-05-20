---
title: "CS4205 Groupwork — Evolution Strategies Crash Course"
subtitle: "Theory of ES, walkthrough of `evopy`, and concrete improvements for Circles in a Square"
sources:
  - "Bäck & Schwefel (1995), Evolution Strategies I: Variants and computational implementation — `BSw95.pdf`"
  - "Bäck (1995), Evolution Strategies: An alternative evolutionary algorithm — lecture-3 reading"
  - "Assignment brief (CiaS topic) — `assignment-brief.pdf`, presentation rubric — `presentation-rubric.pdf`"
  - "TA meeting notes — `meetings/2026-05-12-meeting-TA.md`"
  - "Codebase — `Algorithms/EvolutionStrategyPython/`"
  - "Lecture-3 notes — `lectures/lecture-3/`"
status: "draft v1"
---

# CS4205 Groupwork — Evolution Strategies Crash Course

> This is a personal study guide for the CS4205 Assignment 2, Circles-in-a-Square (CiaS) topic. It is written to give one person — me — deep operational understanding of (a) the theory in Bäck & Schwefel 1995 (BSw95), (b) the `evopy` Python codebase the group is considering as the baseline, and (c) concrete, source-grounded improvements that move the needle on the grading rubric. It lives in `groupwork-notes/` (local, never pushed).

---

## 1 · Orientation

The assignment we picked is **Circles in a Square (CiaS)** — pack `n` points in the unit square so the minimum pairwise distance is maximised. The fitness function (assignment brief §A) is

$$
f_{\text{scatter}}(\vec x) = \min_{0 \le i < j < \ell/2} \bigl\Vert (x_{2i}, x_{2i+1}) - (x_{2j}, x_{2j+1}) \bigr\Vert_2 \tag{CiaS}
$$

with $\vec x \in [0, 1]^{\ell}$ and $\ell = 2n$. It is a *real-valued, single-objective, continuous* problem with a known global optimum table (Packomania) up to thousands of circles, so we always have a ground-truth target.

The grading split is **60 % content / 20 % presentation / 20 % defense** (`assignment-brief.pdf` p. 2). The content rubric (`presentation-rubric.pdf`) explicitly rewards: systematic research methodology, ample experiments with statistical testing, methodical interpretation, and conclusions that extrapolate to wider settings (problem and algorithm generalisation). The TA meeting (`meetings/2026-05-12-meeting-TA.md`) confirmed the meta-instruction: *pick one EA and improve it; don't compare different EAs*.

We were given two starting points: the C reference implementation of AMaLGaM (an EDA, paired with the Bosman & Gallagher 2018 paper) and a Python skeleton called `evopy` — a minimal $(\mu, \lambda)$-style Evolution Strategy with three configurable mutation models (single-σ, n-σ, full covariance). This guide assumes we are going down the Python ES path. The `evopy` codebase implements *exactly* the operators that Schwefel describes in BSw95 §6.4, so the paper-to-code mapping is unusually clean — every line of `individual.py` has a counterpart in equations (6.18) to (6.21).

BSw95 is a 21-page chapter walking from the original (1+1)-ES (Rechenberg, 1960s) up to the contemporary $(\mu, \kappa, \lambda, \rho)$-ES (Schwefel & Rudolph, 1995). I focus on §6.2 (1/5 success rule), §6.4 (the modern $(\mu, \lambda)$ algorithm with self-adaptation and correlated mutation), and §6.5 (variants worth knowing about), because the rest is either historical context or out-of-scope (parallelism, multi-objective, mixed-integer).

The rest of this guide is organised as follows. §2 walks through ES theory from (1+1) to full covariance, with worked numerical examples whenever the math turns abstract. §3 is a function-by-function walkthrough of `evopy`, with verbatim code blocks and explicit pointers back to the equations in §2. §4 is a one-page glossary. §5 is the part that actually drives the grade: a ranked list of concrete, source-justified improvements, with side-by-side code. §6 closes with open questions for the TA and known risks.

---

## 2 · Evolution Strategies — theory deep dive

ES is the branch of evolutionary computation that was *born real-valued*. From the very first variant in 1964 (Rechenberg's pipe-bending experiments at TU Berlin, [BSw95 §6.1]), the object variables were continuous and mutation was Gaussian. That design choice is the reason ES skips most of the encoding pathologies GAs suffer on continuous problems — the Hamming-cliff complexity blow-up (`O(l^q \cdot \ln l)` worst case, see `lectures/lecture-3/concepts/hamming-cliff-complexity.md`) simply does not arise, because we never go through a bit string at all.

### 2.1 The (1+1)-ES and the 1/5 success rule

The simplest ES has a single parent and a single offspring per generation. The individual is $\vec a = (\vec x, \sigma) \in \mathbb{R}^n \times \mathbb{R}_+$ — object variables plus one scalar step size. Mutation is

$$
\tilde x_i = x_i + z_i, \quad z_i \sim \mathcal{N}_i(0, \tilde\sigma^2) \tag{BSw95 6.7}
$$

with **deterministic** step-size control given by Rechenberg's *1/5 success rule* (`BSw95` eq. 6.6):

$$
\tilde\sigma = \mathbf{mu}_\sigma(\sigma) = \begin{cases}
\sigma / \sqrt[n]{c} & \text{if } p_s > 1/5 \\
\sigma \cdot \sqrt[n]{c} & \text{if } p_s < 1/5 \\
\sigma     & \text{if } p_s = 1/5
\end{cases} \tag{BSw95 6.6}
$$

where $p_s$ is the empirically measured *success probability* — the fraction of recent mutations that produced offspring better than the parent. Schwefel derived $c = 0.817$ for the sphere model; the algorithmic constant most often quoted (BSw95 p. 5) is $c = 0.85$, applied as: *after every $n$ mutations, look back over the previous $10n$; if fewer than $2n$ succeeded, multiply $\sigma$ by 0.85; if more than $2n$ succeeded, divide by 0.85.*

The intuition is purely empirical. On the sphere model, Schwefel showed that the success rate that maximises convergence velocity is around 1/5. If we are succeeding more than 1/5 of the time, we are too cautious — step out further; if less, we are too aggressive — step in. The rule is "deterministic" because $\sigma$ is updated by a closed-form function of measured statistics, not by inheritance from offspring.

The selection operator $\mathbf{sel}_1^2$ (BSw95 eq. 6.8) takes the better of $\{\vec a, \tilde{\vec a}\}$ — this is by definition an elitist (plus) selection.

**Why (1+1)-ES is not enough.** It is a local-search stochastic-gradient method (BSw95 §6.2 closing paragraph likens it to simulated annealing, citing [Rud93]). Two problems:

1. The 1/5 rule decays $\sigma$ aggressively when the local topology stops giving 1/5 successes — which happens not only when you have converged but also when you are stuck on a ridge. Premature stagnation is common.
2. Self-adaptation (§2.3 below) "definitely does not work in a $(\mu+1)$-strategy", as BSw95 §6.3 puts it — you need a *population* of strategy parameters competing in parallel to make Schwefel-style self-adaptation work.

So the (1+1)-ES is mostly a teaching object now. Practically it is replaced by $(\mu, \lambda)$-ES.

### 2.2 From (μ+1) through (μ,λ) and (μ+λ)

The first multimembered ES, the (μ+1)-ES, introduced *recombination* (BSw95 §6.3): pick $\rho$ random parents from a population of $\mu$, mix them into one offspring, mutate, and replace the worst parent if the offspring is at least as good. This is the same as "steady-state" GA selection (`[Whi89]`). It did not really catch on, because the step-size question was left unsolved.

Modern ES uses one of two selection schemes:

- **(μ + λ)-ES** — the next parent set is the $\mu$ best out of $\mu$ parents *and* $\lambda$ children combined. Elitist.
- **(μ, λ)-ES** — the next parent set is the $\mu$ best out of *only* the $\lambda$ children. Non-elitist; requires $\lambda \ge \mu$ (with equality forcing $\mu = 1$).

The main loops are equations (6.24) and (6.23) in BSw95. The crucial design choice is whether to let *misadapted strategy parameters* persist across generations. With (μ+λ), an individual with a small $\sigma$ that happens to land on a good $\vec x$ can survive forever — even though its $\sigma$ is now too small to make progress. BSw95 (p. 11) is unambiguous:

> Though it offers some theoretical advantage, this minor modification has the serious disadvantage that the self-adaptation of strategy parameters is hindered in working effectively, because misadapted strategy parameters may survive for a relatively large number of generations. Furthermore, the (μ+λ)-selection mechanism fails in case of dynamically changing environments, and it tends to emphasize on local rather than global search properties. For these reasons, modern evolution strategies use (μ,λ)-selection, normally.

The three empirically-required conditions for successful self-adaptation (BSw95 p. 11, citing `[Sch92]`) are:

1. **(μ, λ)-selection** (non-elitist).
2. **Not too strong selective pressure**: $\mu$ "clearly larger than one"; the textbook reference setting is $\mu = 15$, $\lambda = 100$ — a ratio $\lambda / \mu \approx 7$.
3. **Recombination on strategy parameters**.

Each of these is a knob the assignment can turn. *None of them is satisfied in the current `evopy` default* — the default `population_size = 30, num_children = 1` collapses to a degenerate (μ, μ)-ES where every child survives (so selection does nothing), the strategy default is SINGLE_VARIANCE, and there is no recombination operator at all. We come back to this in §5.

### 2.3 Self-adaptation of σ — the central trick

The whole reason $(\mu, \lambda)$-ES exists in its modern form is to *replace* the deterministic 1/5 rule with an **evolutionary** mechanism. The standard deviation $\sigma$ becomes part of the individual:

$$
I = \mathbb{R}^n \times \mathbb{R}_+^{n_\sigma} \times [-\pi, \pi]^{n_\alpha} \tag{BSw95 6.16}
$$

so an individual carries object variables $\vec x$, a vector of standard deviations $\vec\sigma$ (length $1 \le n_\sigma \le n$), and optionally a vector of inclination angles $\vec\alpha$ (length $n_\alpha = (n - n_\sigma/2)(n_\sigma - 1)$ — note that with $n_\sigma = 1$ or $n_\sigma = n$ no half-integer issue arises). The mutation operator is a composition (BSw95 eq. 6.17):

$$
\mathbf{mut} = \mathbf{mu}_x \circ (\mathbf{mu}_\sigma \times \mathbf{mu}_\alpha)
$$

— **mutate the strategy parameters first, then mutate $\vec x$ using the new strategy**. The ordering matters. It is what makes the link between $\sigma$ and fitness *indirect*: a child first chooses how to mutate, and is then judged by what that choice produced. Children whose new $\sigma$ values happen to align well with the local landscape will produce fit $\vec x$ values and will be selected, *carrying their $\sigma$ values forward into the next parent set*. Nobody computes "the best $\sigma$" analytically. The population finds it by trial and error in the joint $(\vec x, \vec\sigma)$ space.

#### 2.3.1 Single-σ case ($n_\sigma = 1$)

When $n_\sigma = 1$, there is no per-component anisotropy. The $\sigma$ update is *log-normal*:

$$
\sigma' = \sigma \cdot \exp(z_0), \quad z_0 \sim \mathcal{N}(0, \tau_0^2), \quad \tau_0 = \frac{1}{\sqrt{n}} \tag{Bäck §2 eq. 8}
$$

(Note Bäck 1995 writes the *variance* as $\tau_0^2 = 1/n$ in the *Alternative* paper; the recommended *standard deviation* of the log-normal is therefore $\tau_0 = 1/\sqrt n$ — these are the same statement.)

Three "naturally reasonable" reasons for log-normal (BSw95 p. 10 and Bäck §2):

1. *Positivity preservation* — a multiplicative process keeps $\sigma > 0$ forever.
2. *Symmetry under neutrality* — the median of $\exp(z_0)$ is 1, so multiplying by $c$ has the same probability density as multiplying by $1/c$. Without selection, $\sigma$ executes an unbiased random walk on a log scale.
3. *Small modifications more likely than large* — the lognormal has its mode near 1 and decays for large multiplicative jumps in either direction.

**Worked example.** Take $n = 20$ (the CiaS instance for $n_{\text{circles}} = 10$ used in `main.py`), $\sigma = 0.5$, and a draw $z_0 = -0.3$. Then $\tau_0 = 1/\sqrt{20} \approx 0.2236$, so $z_0 / \tau_0 \approx -1.34$ — a moderately rare downward draw (about 1.34 standard deviations below zero). The new step size is

$$
\sigma' = 0.5 \cdot \exp(-0.3) \approx 0.5 \cdot 0.7408 \approx 0.3704.
$$

A child then mutates its object variables with $\tilde x_i = x_i + 0.3704 \cdot z_i$, $z_i \sim \mathcal{N}(0, 1)$. If this child outperforms its parent, the $\sigma' = 0.3704$ is what is inherited into the next round — the population *learned* that smaller steps were doing better at this point in the search.

The implementation (`individual.py:73`) uses $\tau_0 = \sqrt{1/(2 n)}$ rather than $1/\sqrt n$ — i.e. $1/\sqrt{2n}$. This is the "two-level" form Bäck calls $\tau'$ in §2 of *Alternative* and is consistent with BSw95 eq. 6.18 even for the single-σ case. The factor $\sqrt 2$ in the denominator slightly reduces the per-generation drift; it does not change the qualitative behaviour.

#### 2.3.2 N-σ case ($n_\sigma = n$)

When each object variable gets its own step size, the σ-update has the famous two-level structure of BSw95 eq. 6.18:

$$
\tilde\sigma_i = \hat\sigma_i \cdot \exp(z_0 + z_i), \quad z_0 \sim \mathcal{N}(0, \tau'^2), \quad z_i \sim \mathcal{N}(0, \tau^2) \tag{BSw95 6.18}
$$

with $z_0$ drawn *once per individual* (shared across all $n$ components) and $z_i$ drawn *once per component*. Schwefel's recommended *standard deviations* of these two normals are

$$
\tau' = \frac{1}{\sqrt{2n}}, \qquad \tau = \frac{1}{\sqrt{2\sqrt n}}
$$

(BSw95 cites this as a learning-rate parameterisation; Bäck §2 writes the variances as $\tau'^2 = 1/(2n)$, $\tau^2 = 1/(2\sqrt n)$). The split is deliberate:

- **$z_0$ is the global breathing**. Shared across all $n_\sigma$ components, it rescales the *entire* $\vec\sigma$ vector up or down together. This is how the algorithm learns whether *all* directions should mutate more aggressively or more cautiously.
- **$z_i$ is the local anisotropy**. Independent per component, it lets the algorithm learn that some directions need bigger steps than others — e.g. a long valley aligned with one axis.

A floor $\varepsilon_\sigma$ is enforced to stop $\sigma_i$ from collapsing to numerical zero (BSw95 p. 9 — "a minimal value of $\varepsilon_\sigma$ is algorithmically enforced for all $i$"). In `evopy` this is `_EPSILON = 0.01` (`individual.py:20`).

**Worked example.** Same setup as before: $n = 20$, start with $\vec\sigma = (0.5, 0.5, \ldots, 0.5)$. Draw $z_0 = +0.1$ and the first three component draws $z_1 = 0.4, z_2 = -0.5, z_3 = 0.0$. With the recommended $\tau' = 1/\sqrt{40} \approx 0.158$ and $\tau = 1/\sqrt{2 \cdot \sqrt{20}} \approx 0.334$, all draws are within roughly half a standard deviation of zero (a typical update). The new per-component step sizes are

$$
\tilde\sigma_1 = 0.5 \cdot e^{0.1 + 0.4} = 0.5 \cdot e^{0.5} \approx 0.5 \cdot 1.649 \approx 0.824
$$
$$
\tilde\sigma_2 = 0.5 \cdot e^{0.1 - 0.5} = 0.5 \cdot e^{-0.4} \approx 0.5 \cdot 0.670 \approx 0.335
$$
$$
\tilde\sigma_3 = 0.5 \cdot e^{0.1 + 0.0} = 0.5 \cdot e^{0.1} \approx 0.5 \cdot 1.105 \approx 0.553
$$

so dimension 1 has stretched, dimension 2 has shrunk, and dimension 3 has gone slightly up. The global $e^{z_0} = e^{0.1} \approx 1.105$ factor is visible in every entry — that is the "all directions are mutating slightly more" signal.

This is the heart of why anisotropic ES is so much more powerful than isotropic on landscapes with very different curvatures along different axes. The classic Schwefel test function $F(\vec x) = \sum_i i \cdot x_i^2$ has optimal $\sigma_i^* \propto 1/\sqrt i$, and a $(\mu, 100)$-ES with $n_\sigma = n$ self-adaptive step sizes finds this ratio automatically — Bäck §2 Fig. 5 plots the result.

#### 2.3.3 Full covariance case ($n_\sigma = n, n_\alpha = n(n-1)/2$)

When mutations need to be *correlated* — e.g. there is a diagonal ridge in the landscape and stepping along it requires moving in $x_1$ and $x_2$ together with positive correlation — the per-component $\vec\sigma$ is not enough. We need the full $n \times n$ covariance matrix of the mutation distribution.

Schwefel's representation (BSw95 §6.4) encodes $\mathbf{C}$ via $n$ standard deviations $\sigma_i$ and $n(n-1)/2$ *rotation angles* $\alpha_j$ (technically called *inclination angles* in the paper). The angles parametrise an orthogonal matrix $\mathbf{T}$ as a product of plane (Givens) rotations:

$$
\mathbf{T} = \prod_{p=1}^{n-1} \prod_{q=p+1}^{n} \mathbf{T}_{pq}(\tilde\alpha_j) \tag{BSw95 6.21}
$$

with index map $j = \tfrac{1}{2}(2n - p)(p + 1) - 2n + q$. The matrix $\mathbf{T}_{pq}(\theta)$ is the identity except for the four entries at positions $(p,p), (p,q), (q,p), (q,q)$ which form a 2D rotation by angle $\theta$ in the $(p, q)$ plane:

$$
\mathbf{T}_{pq}(\theta)_{pp} = \mathbf{T}_{pq}(\theta)_{qq} = \cos\theta, \quad \mathbf{T}_{pq}(\theta)_{pq} = -\mathbf{T}_{pq}(\theta)_{qp} = -\sin\theta
$$

An object-variable mutation is then $\tilde{\vec x} = \hat{\vec x} + \mathbf{T} \vec z$ where $z_i \sim \mathcal{N}(0, \tilde\sigma_i^2)$. The columns of $\mathbf{T}$ are the *principal axes* of the mutation ellipsoid; the $\tilde\sigma_i$ are the lengths of the semi-axes; the $\tilde\alpha_j$ rotate the whole ellipsoid in $\mathbb{R}^n$.

The angles themselves mutate by a *normal* (additive, not multiplicative) update:

$$
\tilde\alpha_j = \hat\alpha_j + z_j, \quad z_j \sim \mathcal{N}(0, \beta^2), \quad \beta \approx 0.0873 \text{ rad} \approx 5° \tag{BSw95 6.19}
$$

with circular wrap-around when an angle leaves $[-\pi, \pi]$. The value $\beta = 0.0873$ is the same constant that appears as `_BETA = 0.0873` in `individual.py:19` — exact correspondence to the paper.

**Worked example for $n = 2$ (the geometric picture).** Take $\vec\sigma = (0.4, 0.1)$ and $\alpha_{12} = 30° = \pi/6 \approx 0.524$ rad. The mutation covariance is the matrix

$$
\mathbf{C} = \mathbf{T} \begin{pmatrix} \sigma_1^2 & 0 \\ 0 & \sigma_2^2 \end{pmatrix} \mathbf{T}^\top, \quad \mathbf{T} = \begin{pmatrix} \cos 30° & -\sin 30° \\ \sin 30° & \cos 30° \end{pmatrix} \approx \begin{pmatrix} 0.866 & -0.5 \\ 0.5 & 0.866 \end{pmatrix}
$$

so

$$
\mathbf{C} \approx \begin{pmatrix} 0.124 & 0.065 \\ 0.065 & 0.048 \end{pmatrix}.
$$

The mutation ellipsoid (the level set of equal density) is a tilted ellipse with semi-axis lengths $0.4$ and $0.1$, rotated $30°$ counter-clockwise. A draw $\vec z = (0.7, -0.2)^\top$ from $\mathcal{N}(0, \text{diag}(\sigma_1^2, \sigma_2^2))$ produces an additive mutation $\mathbf{T} \vec z \approx (0.706, 0.177)^\top$ — most of the step is along the long, tilted axis, as designed.

The number of angles grows as $n(n-1)/2$, which is why the full-covariance ES is rarely worth using for $n \gtrsim 50$. For CiaS at $n_{\text{circles}} = 10$ we have $n = 20$ object variables and $190$ angles per individual — borderline but not prohibitive.

### 2.4 What recombination adds

Recombination in ES is more general than in GA: $\rho$ random parents ($1 \le \rho \le \mu$) produce one offspring. The standard four types (BSw95 eq. 6.11–6.13, distinguishing $\omega \in \{0, 1, 2, 3\}$) are *no recombination*, *global intermediary* (average over all parents), *local intermediary* (average over two), and *discrete* (per-component random pick from two or all parents). Each component of an individual — $\vec x$, $\vec\sigma$, $\vec\alpha$ — can use a *different* recombination operator. The canonical default (BSw95 p. 10 footnote 9) is

$$
\vec\omega = (3, 2, 0), \quad \vec\rho = (\mu, \mu, 1)
$$

— discrete on $\vec x$ (from two random parents), local intermediary on $\vec\sigma$ (averaging two parents per component), nothing on $\vec\alpha$. The asymmetry is deliberate: averaging *step sizes* gives a smooth consensus mutation scale, while averaging *object variables* would collapse the population to a centroid (premature convergence). The concept note `lectures/lecture-3/concepts/local-intermediary-recombination.md` works through the table of all four operators in detail.

Importantly: **the `evopy` baseline has no recombination operator at all**. Every child in `evopy/evopy.py:91-92` is generated by a single parent calling `.reproduce()`. This violates the third of Schwefel's three empirical preconditions for successful self-adaptation. Adding recombination is on the §5 list.

### 2.5 Cross-reference to CMA-ES

The Covariance Matrix Adaptation ES (Hansen & Ostermeier, late 1990s) is the natural endpoint of the trajectory described in BSw95. It addresses the same problem as the full-covariance ES — learning a tilted, anisotropic mutation ellipsoid — but does so *non-locally*: instead of having each individual carry $n + n(n-1)/2$ strategy parameters that are self-adapted independently, CMA-ES maintains a *single, global* covariance matrix $\mathbf{C}^{(t)}$ that is updated each generation from two *evolution paths* — vectors that accumulate the recent successful steps. The result is a derandomised, low-population-size algorithm that converges much faster on poorly-conditioned problems than the classical full-covariance ES.

CMA-ES is out of scope for the `evopy` codebase per se, but BSw95 §6.5 already foreshadows it ("derandomized mutative step-size control" by Ostermeier, Gawelczyk, Hansen, ref `[OGH94]`). If the team wants a *stretch* improvement that is well-justified by sources, switching `_reproduce_full_variance` from the classical Schwefel rotation-angle scheme to a CMA-ES-style global $\mathbf{C}^{(t)}$ update is the most ambitious credible move. See §5.

---

## 3 · Annotated `evopy` walkthrough

This section reads the codebase top-down. For every non-trivial method I quote the actual lines verbatim, then explain what it implements and which BSw95 equation it corresponds to. Code pointers in the prose use the form `file.py:start-end`.

### 3.1 Repository layout

```
EvolutionStrategyPython/
├── main.py                       # driver, defines the CiaS fitness + EvoPy config
├── Readme.md                     # empty
├── LICENSE
├── requirements.dev.txt
└── ES/
    ├── Readme.md                 # short explanation of CiaS + main.py
    └── evopy/
        ├── __init__.py           # re-exports EvoPy, Strategy, ProgressReport
        ├── evopy.py              # the EvoPy class — algorithm shell
        ├── individual.py         # the Individual class — mutation lives here
        ├── strategy.py           # the Strategy enum (3 mutation models)
        ├── progress_report.py    # plain data carrier for the reporter callback
        └── utils/
            └── random.py         # seed-handling helper
```

Renzo Scholman's note in `main.py:11-27` documents the local modifications to the upstream `evopy` library (https://github.com/evopy/evopy): an evaluation counter, a `max_evaluations` stopping criterion, "random repair for solution" (the uniform-resample bounds enforcement we'll critique in §5), and a target-fitness tolerance.

### 3.2 `main.py` — the driver

`main.py` defines the CiaS fitness function in two flavours and wires `EvoPy` up to it. The pure-Python fitness (`main.py:37-44`) is

```python
def circles_in_a_square(individual):
    n = len(individual)
    distances = []
    for i in range(0, n-1, 2):
        for j in range(i + 2, n, 2):
            distances.append(math.sqrt(math.pow((individual[i] - individual[j]), 2)
                              + math.pow((individual[i + 1] - individual[j + 1]), 2)))
    return min(distances)
```

— exactly equation `(CiaS)` from §1. The scipy variant (`main.py:30-34`) is the vectorised version using `sklearn.metrics.pairwise.euclidean_distances`, which is faster for $n_{\text{circles}} \ge 12$. The crossover point is a matter of Python loop overhead vs. NumPy array setup cost.

The `CirclesInASquare.run_evolution_strategies` method (`main.py:120-139`) constructs the `EvoPy` instance:

```python
evopy = EvoPy(
    circles_in_a_square if self.n_circles < 12 else circles_in_a_square_scipy,
    self.n_circles * 2,                       # individual_length = 2n_circles
    reporter=callback,
    maximize=True,
    generations=1000,
    bounds=(0, 1),
    target_fitness_value=self.get_target(),
    max_evaluations=1e5,
)
best_solution = evopy.run()
```

Notice what is *not* passed: `population_size`, `num_children`, `strategy`. They fall back to the `EvoPy.__init__` defaults — `population_size = 30`, `num_children = 1`, `strategy = Strategy.SINGLE_VARIANCE`. The `bounds=(0, 1)` argument is passed down to every `Individual` so that the box-constraint enforcement runs on every mutation.

The known-optimum table (`main.py:96-118`) is verbatim from Packomania up to $n = 20$. The early-stop criterion uses `target_tolerance=1e-5` by default (`evopy.py:18`), so the algorithm halts as soon as the best fitness comes within $10^{-5}$ of the known optimum.

### 3.3 `evopy/utils/random.py` — seed handling

A two-line helper (`utils/random.py:5-16`):

```python
def random_with_seed(seed):
    if seed is None:
        return np.random.mtrand._rand
    if isinstance(seed, int):
        return np.random.RandomState(seed)
    if isinstance(seed, np.random.RandomState):
        return seed
    raise ValueError('Seed must either be an integer or an instance of numpy.random.RandomState')
```

Nothing controversial — but worth noting that `np.random.mtrand._rand` is the *global* default RNG, so passing `random_seed=None` makes runs non-reproducible. For the experiment-heavy parts of the assignment (the rubric explicitly rewards "ample experiments performed, hypotheses statistically tested") we will want to pass a real seed for every run and rotate it across the 30 repetitions.

### 3.4 `evopy/strategy.py` — the strategy enum

```python
class Strategy(Enum):
    """Enum used to distinguish different types of strategies.

    These strategies are used to determine the mechanism which each individual can use to control
    its own mutability. The three strategies which are included are:

    - SINGLE_VARIANCE: the same variance is used for each allele, no covariancesprogr
    - MULTIPLE_VARIANCE: each allele has its own variance, no covariances
    - FULL VARIANCE: each allele has its own variance, complete variances
                     (encoded as rotation angles)
    """
    SINGLE_VARIANCE = 1
    MULTIPLE_VARIANCE = 2
    FULL_VARIANCE = 3
```

These three values correspond exactly to the three configurations of $(n_\sigma, n_\alpha)$ in BSw95 §6.4: $(1, 0)$, $(n, 0)$, and $(n, n(n-1)/2)$ — the first three rows of the "four common configurations" table in my §2.3 above. The fourth (BSw95) configuration — *one privileged direction* ($n_\sigma = 2, n_\alpha = n - 1$) — is not implemented; it would be unusual but not pointless if there is a known dominant search direction on CiaS.

(There is a harmless typo `no covariancesprogr` on line 11 of the docstring — flag in PR review.)

### 3.5 `evopy/individual.py` — mutation lives here

This is the file where the BSw95 equations actually run. Constants:

```python
class Individual:
    _BETA = 0.0873      # individual.py:19  — rotation-angle mutation strength, BSw95 eq. 6.19
    _EPSILON = 0.01     # individual.py:20  — σ floor, BSw95 §6.4 “minimal value of ε_σ”
```

Both constants match BSw95 exactly (BSw95 p. 9: $\beta \approx 0.0873$ rad ≈ 5°; the $\varepsilon_\sigma$ value is left to the implementer, $0.01$ is a reasonable default for problems normalised on $[0, 1]$).

The constructor (`individual.py:22-49`) dispatches on the strategy enum to bind the right reproduction method:

```python
if strategy == Strategy.SINGLE_VARIANCE and len(strategy_parameters) == 1:
    self.reproduce = self._reproduce_single_variance
elif strategy == Strategy.MULTIPLE_VARIANCE and len(strategy_parameters) == self.length:
    self.reproduce = self._reproduce_multiple_variance
elif strategy == Strategy.FULL_VARIANCE and len(strategy_parameters) == self.length * (
        self.length + 1) / 2:
    self.reproduce = self._reproduce_full_variance
else:
    raise ValueError("The length of the strategy parameters was not correct.")
```

The length check on the FULL_VARIANCE branch is suspicious: `length * (length + 1) / 2` equals $n(n+1)/2$, but the expected count is $n$ variances plus $n(n-1)/2$ angles = $n(n+1)/2$. So the arithmetic is right, just spelled in a way that hides what it means. (Improvement: rename and split.)

#### 3.5.1 `_reproduce_single_variance` — the (1+1)-style mutation, in evolved form

```python
def _reproduce_single_variance(self):
    new_genotype = self.genotype + self.strategy_parameters[0] * self.random.randn(self.length)
    # Randomly sample out of bounds indices
    oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
    new_genotype[oob_indices] = self.random.uniform(self.bounds[0], self.bounds[1],
                                                    size=np.count_nonzero(oob_indices))
    scale_factor = self.random.randn() * np.sqrt(1 / (2 * self.length))
    new_parameters = [max(self.strategy_parameters[0] * np.exp(scale_factor), self._EPSILON)]
    return Individual(new_genotype, self.strategy, new_parameters,
                      bounds=self.bounds, random_seed=self.random)
```

(`individual.py:61-74`)

Line 68: object-variable mutation $\tilde x_i = x_i + \sigma \cdot z_i$, $z_i \sim \mathcal{N}(0, 1)$ — exactly BSw95 eq. 6.7 with the single shared $\sigma$. ↳ implemented at `individual.py:68`.

Lines 70-71: the "random repair" bounds enforcement Renzo added — out-of-bounds components are *re-sampled uniformly* inside the bounds. This is mentioned but not endorsed by BSw95 §6.4 ("constraint handling consists in repeating the processes of recombination and mutation as often as necessary to create λ feasible offspring", BSw95 p. 11). Critique in §5.

Line 72: $\sigma$ update is *log-normal* with learning rate $\tau_0 = \sqrt{1/(2n)}$, i.e. BSw95 eq. 6.18 in its single-σ specialisation (only the global $z_0$ term, no per-component $z_i$). ↳ implemented at `individual.py:72-73`.

Line 73: the $\varepsilon_\sigma$ floor ($0.01$) prevents $\sigma$ collapse. ↳ implemented at `individual.py:73`.

A subtlety: the order is *mutate $\vec x$ first, then update $\sigma$*. BSw95 prescribes the *opposite* order (eq. 6.17: $\mathbf{mut} = \mathbf{mu}_x \circ (\mathbf{mu}_\sigma \times \mathbf{mu}_\alpha)$). For the single-σ case this is mathematically irrelevant — the child still ends up with a (genotype, σ) pair both drawn from the right distributions — but for multi-σ and full-covariance it matters (next subsections).

#### 3.5.2 `_reproduce_multiple_variance` — n-σ self-adaptation

```python
def _reproduce_multiple_variance(self):
    new_genotype = self.genotype + [self.strategy_parameters[i] * self.random.randn()
                                    for i in range(self.length)]
    # Randomly sample out of bounds indices
    oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
    new_genotype[oob_indices] = self.random.uniform(self.bounds[0], self.bounds[1],
                                                    size=np.count_nonzero(oob_indices))
    global_scale_factor = self.random.randn() * np.sqrt(1 / (2 * self.length))
    scale_factors = [self.random.randn() * np.sqrt(1 / 2 * np.sqrt(self.length))
                     for _ in range(self.length)]
    new_parameters = [max(np.exp(global_scale_factor + scale_factors[i])
                          * self.strategy_parameters[i], self._EPSILON)
                      for i in range(self.length)]
    return Individual(new_genotype, self.strategy, new_parameters, bounds=self.bounds)
```

(`individual.py:76-94`)

Line 83-84: object-variable mutation $\tilde x_i = x_i + \sigma_i \cdot z_i$, $z_i \sim \mathcal{N}(0, 1)$ — BSw95 eq. 6.20 in its uncorrelated specialisation ($\mathbf{T} = \mathbf{I}$). ↳ implemented at `individual.py:83-84`.

Line 88: the **global** scale factor $\tau' = \sqrt{1/(2n)}$ — this is the $z_0$ term in BSw95 eq. 6.18, drawn *once per individual*. ↳ implemented at `individual.py:88`.

Line 89-90: the **per-component** scale factor. This is supposed to be $\tau = 1/\sqrt{2\sqrt n}$ — i.e. `np.sqrt(1 / (2 * np.sqrt(self.length)))`. But Python's operator precedence parses `1 / 2 * np.sqrt(self.length)` *left-to-right*: first `1/2 = 0.5`, then `0.5 * sqrt(n)`, then the outer `sqrt`. So the code is actually computing

$$
\tau_{\text{code}} = \sqrt{\tfrac{1}{2} \sqrt n}
$$

instead of the intended

$$
\tau_{\text{intended}} = \sqrt{\tfrac{1}{2 \sqrt n}}.
$$

For $n = 20$ this gives $\tau_{\text{code}} \approx 1.495$ vs. $\tau_{\text{intended}} \approx 0.334$ — a 4.5× overstep. **This is a bug** that drives per-component σ much faster than Schwefel's analysis predicts. Fix and benchmark; see §5. ↳ bug at `individual.py:89`.

Line 91-93: $\tilde\sigma_i = \hat\sigma_i \cdot \exp(z_0 + z_i)$ with floor — exactly BSw95 eq. 6.18. ↳ implemented at `individual.py:91-93`.

Once again, the order is "mutate $\vec x$ first, then update $\sigma$" — opposite of BSw95 eq. 6.17. In the multi-σ case this means the *child's* $\sigma_i$ values are not the ones that produced the child's $\vec x$ values. The selection signal still flows correctly (a good child's $\sigma$ survives and is used by the *next* generation), so the self-adaptive loop still closes, but the within-generation accounting is off. Recommendation: swap the order to match BSw95 exactly. Low-risk, easy.

#### 3.5.3 `_reproduce_full_variance` — full covariance

```python
def _reproduce_full_variance(self):
    global_scale_factor = self.random.randn() * np.sqrt(1 / (2 * self.length))
    scale_factors = [self.random.randn() * np.sqrt(1 / 2 * np.sqrt(self.length))
                     for _ in range(self.length)]
    new_variances = [max(np.exp(global_scale_factor + scale_factors[i])
                         * self.strategy_parameters[i], self._EPSILON)
                     for i in range(self.length)]
    new_rotations = [self.strategy_parameters[i] + self.random.randn() * self._BETA
                     for i in range(self.length, len(self.strategy_parameters))]
    new_rotations = [rotation if abs(rotation) < np.pi
                     else rotation - np.sign(rotation) * 2 * np.pi
                     for rotation in new_rotations]
    T = np.identity(self.length)
    for p in range(self.length - 1):
        for q in range(p + 1, self.length):
            j = int((2 * self.length - p) * (p + 1) / 2 - 2 * self.length + q)
            T_pq = np.identity(self.length)
            T_pq[p][p] = T_pq[q][q] = np.cos(new_rotations[j])
            T_pq[p][q] = -np.sin(new_rotations[j])
            T_pq[q][p] = -T_pq[p][q]
            T = np.matmul(T, T_pq)
    new_genotype = self.genotype + T @ self.random.randn(self.length)
    # Randomly sample out of bounds indices
    oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
    new_genotype[oob_indices] = self.random.uniform(self.bounds[0], self.bounds[1],
                                                    size=np.count_nonzero(oob_indices))
    return Individual(new_genotype, self.strategy, new_variances + new_rotations, bounds=self.bounds)
```

(`individual.py:97-129`)

This time the order is right: variances are updated first (105-110), then rotations (111-115), then $\mathbf{T}$ is built (116-124), then $\vec x$ is mutated (125). The structure of $\mathbf{T}$ as a left-to-right product of Givens rotations $\mathbf{T}_{pq}(\alpha_j)$ is exactly BSw95 eq. 6.21. ↳ implemented at `individual.py:116-124`.

The rotation update (111-115) implements BSw95 eq. 6.19: $\tilde\alpha_j = \hat\alpha_j + z_j$, $z_j \sim \mathcal{N}(0, \beta^2)$ with circular wrap to $[-\pi, \pi]$. Note: the wrap is implemented as $\alpha \to \alpha - \text{sign}(\alpha) \cdot 2\pi$, which only fires when $|\alpha| > \pi$ — fine, this matches the paper's "kept feasible by circularly mapping them into the feasible range". ↳ implemented at `individual.py:111-115`.

**However**, line 119 — the index map `j = int((2 * self.length - p) * (p + 1) / 2 - 2 * self.length + q)` — is **wrong**. BSw95's formula (after eq. 6.21) is *1-based*: $j_{\text{paper}} = \tfrac{1}{2}(2n - p)(p + 1) - 2n + q$ with $p, q \in \{1, \ldots, n\}$. Translating to the code's 0-based loop variables $p_c = p - 1, q_c = q - 1$ and a 0-based array index $j_c = j - 1$ should give

$$
j_c = \tfrac{1}{2}(2n - p_c - 1)(p_c + 2) - 2n + q_c
$$

but the code uses

$$
j_{\text{code}} = \tfrac{1}{2}(2n - p_c)(p_c + 1) - 2n + q_c.
$$

For $n = 4$ the code produces $j$ values $\{-3, -2, -1, 1, 2, 4\}$ — which Python interprets as `{3, 4, 5, 1, 2, 4}` via negative-index wrap-around. Index 0 is never accessed; index 4 is accessed twice. **Two pairs $(p, q)$ share the same rotation angle, and one angle is never used.** This is a real semantic bug — correlated mutations are not actually building the matrix the paper specifies. Fix and benchmark; see §5. ↳ bug at `individual.py:119`.

The bug also propagates to the multiple-variance side via the same off-by-one in `scale_factors` (`individual.py:106`).

### 3.6 `evopy/evopy.py` — the algorithm shell

The constructor (`evopy.py:15-59`) takes 15+ keyword arguments. The defaults worth remembering:

| Parameter | Default | What it controls |
| --- | --- | --- |
| `generations` | 100 | hard generation cap (`main.py` overrides to 1000) |
| `population_size` | 30 | $\mu$ |
| `num_children` | **1** | $\lambda / \mu$ — number of children *per parent per generation* |
| `mean`, `std` | 0, 1 | parameters of the initial perturbation around `warm_start` |
| `maximize` | False | sort direction (CiaS sets True) |
| `strategy` | `SINGLE_VARIANCE` | which mutation model |
| `target_tolerance` | 1e-5 | $\|f_{\text{best}} - f_{\text{target}}\| < \text{tol}$ stops early |

The main loop is `evopy.py:76-107`:

```python
def run(self):
    if self.individual_length == 0:
        return None

    start_time = time.time()

    population = self._init_population()
    best = sorted(population, reverse=self.maximize,
                  key=lambda individual: individual.evaluate(self.fitness_function))[0]

    for generation in range(self.generations):
        children = [parent.reproduce() for _ in range(self.num_children)
                    for parent in population]
        population = sorted(children, reverse=self.maximize,
                            key=lambda individual: individual.evaluate(self.fitness_function))
        self.evaluations += len(population)
        population = population[:self.population_size]
        best = population[0]

        if self.reporter is not None:
            mean = np.mean([x.fitness for x in population])
            std = np.std([x.fitness for x in population])
            self.reporter(ProgressReport(generation, self.evaluations,
                                         best.genotype, best.fitness, mean, std))

        if self._check_early_stop(start_time, best):
            break

    return best.genotype
```

Two things to notice. First, the children list comprehension (`evopy.py:91-92`) loops `num_children` times *over* `population`, so the total number of children per generation is $\lambda = \mu \cdot \text{num\_children}$. With the default `num_children=1` and `population_size=30`, *every generation produces exactly 30 children, sorts them by fitness, and keeps the top 30*. The selection step does **nothing**: every child survives. This is a degenerate $(\mu, \mu)$-ES — call it $(30, 30)$-ES. There is no selection pressure at all on the object variables; the only signal driving the population is the random walk of $\sigma$ self-adaptation. ↳ degenerate selection at `evopy.py:91-96`.

Second, `population = sorted(children, ...)` (line 93-94) discards the parent set entirely — this is *comma* selection, not plus selection. The implementation hard-codes (μ, λ)-style selection regardless of any user flag. Good — that matches BSw95's recommendation — but worth noting that "switch to (μ + λ)" is not exposed.

The early-stop check (`evopy.py:61-74`):

```python
def _check_early_stop(self, start_time, best):
    return (self.max_run_time is not None
            and (time.time() - start_time) > self.max_run_time) \
           or \
           (self.target_fitness_value is not None
            and abs(best.fitness - self.target_fitness_value) < self.target_tolerance) \
           or (self.max_evaluations is not None
            and self.evaluations >= self.max_evaluations)
```

Three OR'd conditions: wall-clock time exceeded, target fitness reached within tolerance, or evaluation budget exhausted. The CiaS driver in `main.py` uses the last two (target = Packomania optimum, budget = $10^5$ evaluations).

The init-population (`evopy.py:109-139`):

```python
def _init_population(self):
    if self.strategy == Strategy.SINGLE_VARIANCE:
        strategy_parameters = self.random.randn(1)
    elif self.strategy == Strategy.MULTIPLE_VARIANCE:
        strategy_parameters = self.random.randn(self.individual_length)
    elif self.strategy == Strategy.FULL_VARIANCE:
        strategy_parameters = self.random.randn(
            int((self.individual_length + 1) * self.individual_length / 2))
    else:
        raise ValueError("Provided strategy parameter was not an instance of Strategy")
    population_parameters = np.asarray([
        self.warm_start + self.random.normal(loc=self.mean, scale=self.std, size=self.individual_length)
        for _ in range(self.population_size)
    ])
    if self.bounds is not None:
        oob_indices = (population_parameters < self.bounds[0]) | (population_parameters > self.bounds[1])
        population_parameters[oob_indices] = self.random.uniform(self.bounds[0], self.bounds[1],
                                                                  size=np.count_nonzero(oob_indices))
    return [
        Individual(parameters, self.strategy, strategy_parameters,
                   random_seed=self.random, bounds=self.bounds)
        for parameters in population_parameters
    ]
```

The strategy parameters (`strategy_parameters` on lines 110-117) are sampled *once* and then passed to *every* individual in the population. This means in the initial generation **all individuals share the same** $\vec\sigma$ — they only diverge from generation 1 onward when reproduction stochastically perturbs σ. A tiny issue: not catastrophic (within 2-3 generations there is plenty of σ diversity), but it contradicts BSw95's "sufficiently large diversity of internal models in the parent population" (p. 11) as a precondition for good self-adaptation. Cheap fix: draw `strategy_parameters` per-individual. ↳ shared σ at `evopy.py:109-118`.

Also: those initial strategy parameters are drawn from `randn` — i.e. zero-mean unit-variance normal. So roughly half the initial σ values are *negative*, which is then trivially fixed by the `_EPSILON` floor on first reproduction. Drawing from `np.abs(randn)` or from a log-normal would be cleaner.

The bounds enforcement at lines 124-127 uses the same "random uniform resample" repair as in `Individual` — same critique applies.

### 3.7 `evopy/progress_report.py`

```python
class ProgressReport:
    def __init__(self, generation, evaluations, best_genotype, best_fitness, avg_fitness, std_fitness):
        self.generation = generation
        self.evaluations = evaluations
        self.best_genotype = best_genotype
        self.best_fitness = best_fitness
        self.avg_fitness = avg_fitness
        self.std_fitness = std_fitness
```

(`progress_report.py:4-19`) A plain data container handed to the `reporter` callback every generation. Not worth more discussion.

### 3.8 Summary of code↔theory pointers

| Concept (§2 above) | BSw95 eq. | Implementation |
| --- | --- | --- |
| Object-variable Gaussian mutation $\tilde x_i = x_i + \sigma_i z_i$ | (6.7) / (6.20) | `individual.py:68, 83-84, 125` |
| Single-σ log-normal update $\sigma' = \sigma e^{z_0}$ | (6.18) specialised | `individual.py:72-73` |
| n-σ two-level log-normal update | (6.18) | `individual.py:88-93` |
| Per-component σ-update local factor τ | (6.18) | **buggy** at `individual.py:89, 106` |
| Rotation-angle additive update | (6.19) | `individual.py:111-115` |
| Givens-rotation product $\mathbf{T}$ | (6.21) | `individual.py:116-124` |
| Rotation index map $j(p, q)$ | (6.21) text | **buggy** at `individual.py:119` |
| (μ, λ)-selection main loop | (6.23) | `evopy.py:91-96` (degenerate when `num_children=1`) |
| σ floor $\varepsilon_\sigma$ | §6.4 p. 9 | `individual.py:20, 73, 92, 108` |
| Box-constraint handling | §6.4 p. 11 | `evopy.py:124-127`, `individual.py:70-71, 86-87, 127-128` |
| Recombination | (6.10), (6.22) | **missing** |

---

## 4 · Glossary

The ordering is alphabetical; entries that exist in BSw95 carry an equation pointer.

- **α (alpha)** — *Inclination angle*. A rotation angle in $[-\pi, \pi]$ used to parametrise the full-covariance mutation matrix $\mathbf{T}$ as a product of Givens rotations. There are $n(n-1)/2$ of them per individual in the FULL_VARIANCE strategy. BSw95 eq. 6.19.
- **β (beta)** — The standard deviation of the additive normal perturbation applied to $\alpha_j$ in BSw95 eq. 6.19. Empirically $\beta \approx 0.0873$ rad ≈ 5°. Stored as `_BETA` in `individual.py:19`.
- **CMA-ES** — *Covariance Matrix Adaptation Evolution Strategy*. The modern derandomised successor to the classical full-covariance ES, with a global $\mathbf{C}^{(t)}$ updated from evolution paths rather than per-individual self-adapted rotation angles. Not implemented in `evopy`.
- **Comma selection / (μ, λ)** — The next-generation parent set is the $\mu$ best out of *only* the $\lambda$ children. Non-elitist; requires $\lambda \ge \mu$. BSw95 eq. 6.23.
- **Discrete recombination** — Per-component random pick from two or more parents. The BSw95-recommended operator for object variables $\vec x$. BSw95 eq. 6.13 ($\omega = 3$).
- **ε_σ (epsilon-sigma)** — The minimum-σ floor enforced after every $\sigma$ update to prevent numerical collapse to zero. Stored as `_EPSILON = 0.01` in `individual.py:20`. BSw95 §6.4 p. 9.
- **Evolution path** — A CMA-ES concept; a vector that accumulates successful step directions over generations to bias the covariance update. Not in BSw95, not in `evopy`.
- **Generation gap** — The fraction of the population replaced per generation. (μ, λ) has generation gap 1 (full replacement); (μ + λ) has gap $\lambda / (\mu + \lambda) < 1$.
- **Givens rotation** — A rotation matrix that acts non-trivially in a single 2D plane within $\mathbb{R}^n$, leaving the other $n - 2$ axes fixed. The building block of the full-covariance $\mathbf{T}$. BSw95 eq. 6.21.
- **Global intermediary recombination** — Arithmetic mean over all $\mu$ parents, per component. BSw95 eq. 6.11 ($\omega = 1$).
- **κ (kappa)** — *Maximum life span*. The number of reproductive cycles an individual is allowed to survive in the $(\mu, \kappa, \lambda, \rho)$-ES (BSw95 §6.6). $\kappa = 1$ recovers (μ, λ); $\kappa = \infty$ recovers (μ + λ).
- **λ (lambda)** — Number of children produced per generation. Schwefel's reference setting is $\lambda = 100$.
- **Local intermediary recombination** — Convex combination of two random parents, per component. Standard for $\vec\sigma$. BSw95 eq. 6.12 ($\omega = 2$). See `lectures/lecture-3/concepts/local-intermediary-recombination.md`.
- **Log-normal perturbation** — A multiplicative update of the form $\sigma \to \sigma \cdot e^z$, $z \sim \mathcal{N}(0, \tau^2)$. Used for σ self-adaptation. Preserves positivity, neutral under no-selection, biased toward small jumps. BSw95 eq. 6.18; rationale on p. 10.
- **μ (mu)** — Parent population size. BSw95 reference setting is $\mu = 15$.
- **Mutative step-size control** — Rechenberg's $\sigma \to \sigma \cdot c_0$ or $\sigma / c_0$ with $c_0 \approx 1.3$ at random. A predecessor of full self-adaptation. BSw95 eq. 6.25, §6.5.
- **Object variables** — The components of $\vec x$ that go into the objective function. Distinct from *strategy parameters*.
- **ω (omega)** — Recombination type index, $\omega \in \{0, 1, 2, 3\}$ → {none, global intermediary, local intermediary, discrete}. BSw95 eq. 6.11-6.13.
- **Plus selection / (μ + λ)** — The next parent set is the $\mu$ best out of $\mu$ parents *and* $\lambda$ children combined. Elitist. Penalised by BSw95 p. 11 ("misadapted strategy parameters may survive"). BSw95 eq. 6.24.
- **ρ (rho)** — Number of parents involved in a single recombination event, $1 \le \rho \le \mu$.
- **(1+1)-ES** — Single parent, single child, deterministic 1/5 success rule. BSw95 §6.2.
- **(μ+1)-ES** — Multimembered, steady-state, replace worst parent if beaten. BSw95 §6.3.
- **Self-adaptation** — Coevolution of object variables and strategy parameters, exploiting the indirect link between fitness and strategy. The defining feature of modern ES. Bäck (1995) §2.
- **σ (sigma)** — Standard deviation of the Gaussian mutation on object variables. Either scalar ($n_\sigma = 1$, isotropic), per-component ($n_\sigma = n$, anisotropic axis-aligned), or implicitly via $\mathbf{C}$ ($n_\sigma = n, n_\alpha = n(n-1)/2$, fully correlated).
- **Strategy parameters** — The $\vec\sigma$ and $\vec\alpha$ vectors that parametrise the mutation distribution. Stored *with* each individual and evolved alongside $\vec x$. BSw95 eq. 6.16.
- **τ (tau)** — Standard deviation of the *per-component* normal $z_i$ in the σ-update. Recommended $\tau = 1/\sqrt{2 \sqrt n}$. BSw95 eq. 6.18.
- **τ' (tau-prime)** — Standard deviation of the *global* normal $z_0$ in the σ-update. Recommended $\tau' = 1/\sqrt{2 n}$. BSw95 eq. 6.18.
- **τ_0 (tau-zero)** — Standard deviation of the single-σ update. Recommended $\tau_0 = 1/\sqrt n$ (Bäck §2 eq. 8) or $\tau_0 = 1/\sqrt{2n}$ (the form `evopy` uses).
- **1/5 success rule** — Rechenberg's deterministic step-size update for the (1+1)-ES: shrink σ if the recent success rate is below 1/5, grow if above. Constant $c = 0.85$. BSw95 eq. 6.6.

---

## 5 · Improvement ideas — ranked

This is the section that should most directly drive the rubric. The ranking is by my estimate of *expected impact on grade* — a function of (a) how clearly the source justifies the change, (b) how interpretable the resulting graph/table will be, and (c) how easy it is to run statistical tests on. Every entry names the current code, the proposed code, and the source that says it should help.

### Rank 1 — Fix the τ operator precedence bug (`individual.py:89, 106`)

**Current code.**

```python
scale_factors = [self.random.randn() * np.sqrt(1 / 2 * np.sqrt(self.length))
                 for _ in range(self.length)]
```

Computes $\tau_{\text{code}} = \sqrt{(1/2) \cdot \sqrt n}$ instead of the intended $\tau_{\text{intended}} = \sqrt{1/(2\sqrt n)}$ (BSw95 eq. 6.18, Schwefel learning rate).

**Proposed code.**

```python
scale_factors = [self.random.randn() * np.sqrt(1 / (2 * np.sqrt(self.length)))
                 for _ in range(self.length)]
```

**Justification.** BSw95 eq. 6.18 prescribes the per-component learning rate $\tau = 1/\sqrt{2 \sqrt n}$ (equivalently variance $1/(2\sqrt n)$ as Bäck §2 writes it). For $n = 20$, the current code has $\tau \approx 1.495$ vs. intended $\approx 0.334$ — a 4.5× overstep that drives per-component σ much faster than Schwefel's analysis assumes. This will manifest as σ values that oscillate wildly across generations, harming the self-adaptive signal.

**Expected effect.** Significantly faster and more stable convergence on MULTIPLE_VARIANCE and FULL_VARIANCE runs. On CiaS the effect should be largest in higher $n$ (more dimensions means more accumulated noise from the inflated τ). Cheap experiment: 30 runs per (buggy, fixed) at $n_{\text{circles}} \in \{5, 10, 15, 20\}$, paired Wilcoxon signed-rank on best fitness — should be highly significant.

### Rank 2 — Fix the rotation-index bug (`individual.py:119`)

**Current code.**

```python
j = int((2 * self.length - p) * (p + 1) / 2 - 2 * self.length + q)
```

Produces $j$ values like $\{-3, -2, -1, 1, 2, 4\}$ for $n = 4$ — index 0 is never used, index 4 is used twice, and three negative indices wrap around. *The matrix $\mathbf{T}$ constructed in the full-variance reproduction does not match BSw95 eq. 6.21.*

**Proposed code.**

```python
j = int((2 * self.length - p - 1) * (p + 2) / 2 - 2 * self.length + q)
```

(derived by translating BSw95's 1-based formula into 0-based loop variables and 0-based array indexing). For $n = 4$ this gives $\{0, 1, 2, 3, 4, 5\}$ — a clean permutation of the rotation-angle indices.

**Justification.** BSw95 eq. 6.21 and the text immediately following it (citing Rudolph 1992a) specify the rotation indexing exactly. The fix restores Schwefel's full-covariance mutation as designed.

**Expected effect.** Hard to predict without running. The full-covariance ES is rarely used in `evopy` because the SINGLE_VARIANCE default works well enough on cheap problems, but if we want to demonstrate FULL_VARIANCE on CiaS, this bug currently makes the comparison apples-to-oranges. Fixing it is a prerequisite for any honest claim about correlated mutations.

### Rank 3 — Make selection actually select (`evopy.py:91-96`, `main.py:123`)

**Current state.** With `num_children=1` (the default), the main loop generates $\mu$ children, sorts them, and keeps the top $\mu$ — a degenerate $(\mu, \mu)$-ES with zero selection pressure. The TA assignment explicitly asks us to "improve an EA" and Schwefel's three preconditions for self-adaptation include "λ clearly larger than μ".

**Proposed code.** Either change the call site in `main.py:123` to pass `num_children=7`, or change the EvoPy default in `evopy.py:16` from `num_children=1` to `num_children=7`. The textbook reference setting is $(\mu, \lambda) = (15, 100)$, ratio $\lambda/\mu \approx 7$.

```python
evopy = EvoPy(
    circles_in_a_square if self.n_circles < 12 else circles_in_a_square_scipy,
    self.n_circles * 2,
    reporter=callback,
    maximize=True,
    generations=1000,
    bounds=(0, 1),
    target_fitness_value=self.get_target(),
    max_evaluations=1e5,
    population_size=15,        # μ
    num_children=7,            # λ/μ → λ = 105
)
```

**Justification.** BSw95 p. 11: "$\mu$ has to be chosen clearly larger than one, e.g. $\mu = 15$… a ratio $\lambda / \mu \approx 7$ is recommended as a good setting". The current default violates this directly.

**Expected effect.** Probably the single most impactful change to the algorithm. With *real* selection pressure, good $\sigma$ values can actually outcompete bad ones, the self-adaptive loop closes, and convergence accelerates. Caveat: $\lambda = 105$ instead of $30$ means each generation costs $3.5\times$ more evaluations, so the wall-clock comparison must use the same evaluation budget (the assignment fixes this at $10^5$, so it is automatic).

### Rank 4 — Add recombination (`evopy.py` main loop, new method on `Individual`)

**Current state.** `evopy/evopy.py:91-92` generates children by `parent.reproduce()` — one parent, no mixing. BSw95 calls recombination on strategy parameters one of three empirically-required conditions for successful self-adaptation.

**Proposed change.** Add an optional `recombination` parameter to `EvoPy.__init__` and implement the canonical BSw95 setting $\vec\omega = (3, 2, 0)$, $\vec\rho = (\mu, \mu, 1)$:

```python
def _make_child(self, population):
    # discrete recombination on x: pick two parents, per-component random
    p1, p2 = self.random.choice(population, size=2, replace=False)
    x_child = np.where(self.random.rand(self.individual_length) < 0.5,
                       p1.genotype, p2.genotype)
    # local intermediary recombination on sigma: average two random parents per component
    q1, q2 = self.random.choice(population, size=2, replace=False)
    sigma_child = 0.5 * (q1.strategy_parameters + q2.strategy_parameters)
    # build a placeholder individual, then mutate it (mut(rec(P)))
    proto = Individual(x_child, self.strategy, sigma_child,
                       bounds=self.bounds, random_seed=self.random)
    return proto.reproduce()
```

and replace `parent.reproduce()` in the main loop with `self._make_child(population)`.

**Justification.** BSw95 §6.4 p. 11 lists "recombination on strategy parameters" as the third empirical condition; BSw95 p. 10 footnote 9 explicitly recommends discrete on $\vec x$, intermediary on $\vec\sigma$, none on $\vec\alpha$. Bäck §3 emphasises this is what distinguishes ES recombination from GA crossover in flexibility (1 to $\mu$ parents per descendant, different operators per component).

**Expected effect.** Improved σ self-adaptation, particularly with the (μ, λ) selection from Rank 3. Recombination on $\sigma$ also reduces the variance of the "step-size scale" the population is using at any moment — it acts as a noise filter. Concrete prediction: with recombination, the σ trajectory across generations should be visibly smoother in our plots.

### Rank 5 — Replace destructive uniform-resample bounds repair (`individual.py:70-71, 86-87, 127-128`; `evopy.py:124-127`)

**Current code.**

```python
oob_indices = (new_genotype < self.bounds[0]) | (new_genotype > self.bounds[1])
new_genotype[oob_indices] = self.random.uniform(self.bounds[0], self.bounds[1],
                                                size=np.count_nonzero(oob_indices))
```

If any component of the mutated child lands outside $[0, 1]$, it is *replaced with a uniform random sample* over the whole interval. This destroys the entire gradient/learning signal for that component — a child that was 0.001 too high becomes a completely fresh random value somewhere in $[0, 1]$.

**Proposed code (option A: reflection).**

```python
new_genotype = np.where(new_genotype < self.bounds[0],
                        2 * self.bounds[0] - new_genotype, new_genotype)
new_genotype = np.where(new_genotype > self.bounds[1],
                        2 * self.bounds[1] - new_genotype, new_genotype)
new_genotype = np.clip(new_genotype, self.bounds[0], self.bounds[1])  # safety
```

(Reflect once; clamp to handle the unlikely case where the reflected value still lands out of bounds, e.g. a huge σ near a bound.)

**Proposed code (option B: clamp, simplest).**

```python
new_genotype = np.clip(new_genotype, self.bounds[0], self.bounds[1])
```

**Justification.** BSw95 §6.4 p. 11 prefers *rejection* ("repeating the processes of recombination and mutation as often as necessary"), which is expensive when σ is large. Reflection preserves the local-search structure: a step that would have overshot is bounced back into the feasible region with the same step length. Clamping is the simplest variant — it preserves the gradient direction but loses the step magnitude. The current uniform-resample is the worst of all three: it *throws away the directional information* and replaces it with noise, which directly fights the self-adaptive σ machinery (σ values that *should* be small are being forced to look big when their offspring keep getting resampled).

**Expected effect.** Especially significant near the bounds, which is most of the CiaS search space — the optimum has points clustered near the corners and edges of the unit square. Expect smoother σ trajectories and faster convergence.

### Rank 6 — Vectorise population evaluation (`evopy.py:91-94`, `individual.py:51-59`)

**Current state.** The evaluation `sorted(children, key=lambda individual: individual.evaluate(...))` calls the fitness function $\lambda$ times in a Python loop. Each `Individual.evaluate` is a single fitness call.

**Proposed change.** Allow `fitness_function` to be batch-callable: if it accepts a 2D array $(λ, n)$, call it once per generation. Add a `vectorized=True` flag. Update `circles_in_a_square_scipy` to compute *all* λ children's fitnesses with a single `euclidean_distances`-on-stacked-points call.

**Justification.** The fitness landscape itself does not change, but the wall-clock budget per evaluation drops. This matters because the assignment fixes the *evaluation* budget at $10^5$, so we want each evaluation to be informative, but it also matters for *experiment turnaround* — we need 30 reps × several configurations.

**Expected effect.** Pure engineering — does not change algorithm semantics, but lets us run more experiments and get tighter confidence intervals. Cite: BSw95 §6.5 on parallel evaluation, though the actual modern reference is Hansen's CMA-ES code.

### Rank 7 — Per-individual initial σ (`evopy.py:109-118`)

**Current state.** All individuals in generation 0 share the same `strategy_parameters` — the same σ vector. Diversity only emerges from generation 1 onward.

**Proposed change.**

```python
return [
    Individual(parameters, self.strategy,
               self._sample_initial_strategy_parameters(),  # fresh per individual
               random_seed=self.random, bounds=self.bounds)
    for parameters in population_parameters
]
```

with `_sample_initial_strategy_parameters` returning a fresh draw each time (and using `np.abs(randn)` instead of `randn` to avoid the half-of-them-are-negative issue).

**Justification.** BSw95 p. 11 names "sufficiently large diversity of internal models in the parent population" as a precondition for self-adaptation. Sharing the initial σ across all $\mu$ parents violates this for at least the first generation.

**Expected effect.** Modest — within 2-3 generations the σ diversity catches up — but it costs nothing to fix.

### Rank 8 — Fitness shaping / rank-based scaling

**Current state.** The CiaS fitness $f_{\min}$ has a very narrow dynamic range (between 0 and $\sqrt 2$) and the *minimum* operator creates a non-smooth landscape — only the closest pair of points contributes to the gradient. Most pairs are inactive.

**Proposed change.** Use a *smoothed* surrogate during selection. The classic choice is a soft-min:

$$
f_{\text{smooth}}(\vec x; \beta) = -\frac{1}{\beta} \log \sum_{i < j} \exp\bigl(-\beta \cdot d_{ij}(\vec x)\bigr)
$$

with $\beta \to \infty$ recovering the true min. Use $f_{\text{smooth}}$ to *rank* individuals for selection but evaluate true $f_{\min}$ for early-stopping. Alternatively (cheaper): rank-based selection ignoring fitness magnitudes (already partially baked into ES — sorted selection cares only about order — so this may not move the needle).

**Justification.** Not directly in BSw95 — the paper assumes smooth $f$. But the Bosman & Gallagher 2018 paper on CiaS (`docs/BosmanGallager Paper.pdf`) flags exactly this issue and discusses how AMaLGaM's covariance estimation suffers when only one pair of points is binding the fitness. The risk: we are *changing the objective*, which the rubric will scrutinise. Document carefully.

**Expected effect.** Plausibly large on early generations (when many pairs are close to binding), tapering off as the algorithm converges and a single pair dominates.

### Rank 9 — Restart strategy (IPOP-style)

**Current state.** When the algorithm gets stuck (no improvement for $k$ generations), it just keeps running until budget. The (μ, λ) selection cannot escape on its own once σ has collapsed.

**Proposed change.** Implement a CMA-ES-style **IPOP** restart: if no improvement over $K$ generations, restart with $\mu \leftarrow 2\mu$, $\lambda \leftarrow 2\lambda$, and a freshly randomised population. Run multiple restarts within the same evaluation budget.

**Justification.** Not in BSw95 (predates IPOP-CMA-ES by ~10 years), but Bäck §5 mentions restart as the standard fix for premature convergence. The Bosman & Gallagher 2018 paper uses a restart variant on CiaS specifically.

**Expected effect.** Improved worst-case behaviour across 30 reps — fewer catastrophic failures. Should narrow the inter-quartile range of the final fitness distribution.

### Rank 10 — Switch to CMA-ES (stretch)

**Current state.** Full-variance `evopy` uses the classical Schwefel rotation-angle encoding, which has $O(n^2)$ strategy parameters per individual and requires self-adaptation to learn the right covariance from scratch in every individual.

**Proposed change.** Replace `_reproduce_full_variance` with a CMA-ES update: a single global $\mathbf{C}^{(t)}$ updated each generation from evolution paths, drawn samples generated by Cholesky-factorising $\mathbf{C}^{(t)}$ once per generation.

**Justification.** Foreshadowed by BSw95 §6.5 (Ostermeier-Hansen "derandomized mutative step-size control"). Highest expected impact but also highest risk (it is a substantial rewrite that may eat into the time budget). Also, CMA-ES is precisely one of the algorithms the assignment brief warns *not* to use as an improvement that was already tried in the Bosman & Gallagher 2018 paper — so we would need to identify a *novel* CMA-ES variant or restrict our claim to "porting CMA-ES to `evopy`'s framework", not "novel improvement".

**Verdict.** Out-of-scope unless the team has at least 1.5 weeks left for experimentation.

---

## 6 · Open questions and risks

This section captures what I genuinely don't know yet, what I think might be wrong with the code or its surrounding assumptions, and where the assignment brief is ambiguous.

**Verification with the TA.** Three things to confirm directly:

1. The two bugs (`individual.py:89` τ precedence; `individual.py:119` rotation index map) — is it possible the original `evopy` upstream is correct and the local copy in our repo was accidentally regressed? Worth a quick `git log` and `git diff` against https://github.com/evopy/evopy. If upstream has the same bugs, that is *also* a point worth raising in the presentation — "we identified two bugs in the canonical reference implementation". If upstream is correct, we should still cite the discrepancy in our improvements section.
2. The "is this a meaningful improvement?" rubric — for example, fixing the τ bug is *technically* a bug fix rather than an algorithmic improvement; will the supervisor still credit it as "improving the EA"?
3. The Bosman & Gallagher 2018 list of *already-tried improvements* on CiaS — does the brief mean only the AMaLGaM/CMA-ES specifics, or does it cover any of: (μ, λ) ratio tuning, recombination, restarts? We need a clear list of what is "off the table".

**Statistical test choice.** The rubric rewards statistical testing but does not name a test. The default for paired comparisons (same set of seeds, two algorithm variants, 30 runs each) is the **Wilcoxon signed-rank test** (non-parametric, paired). For *unpaired* comparisons across multiple algorithms the **Friedman + post-hoc Nemenyi** is standard (this is what `autorank` automates, cited in the brief). We should pick one early and stick with it.

**CiaS-specific risk: the min-fitness ridge.** The fitness is $\min_{i<j} d_{ij}$. At any point in the search space the gradient is determined by *exactly one pair* of nearby points — the binding pair. Small mutations on any other component leave the fitness unchanged. This means: the per-component σ self-adaptation has very little signal to learn from (most components see flat fitness). Correlated mutations may or may not help — they let the algorithm tilt the mutation ellipsoid along the binding pair's direction, but that direction *changes* as soon as a different pair becomes binding. The smoothed-fitness improvement (Rank 8) is partly motivated by this; document the reasoning.

**Order of mutations in `_reproduce_single_variance` and `_reproduce_multiple_variance`.** BSw95 eq. 6.17 prescribes "mutate σ first, then $\vec x$ using the new σ". The code (`individual.py:68` then `individual.py:72`, and `individual.py:83-84` then `individual.py:88-93`) does the opposite. The selection signal still flows correctly (a good child's σ survives), but the within-generation accounting differs from the paper. Easy fix, low-risk; document as a paper-faithfulness improvement.

**Reproducibility.** `EvoPy(random_seed=None)` uses the global NumPy RNG. For the experiments we must always pass an integer seed and log it with every run. The reporter callback should be augmented to record the seed in the output.

**Out-of-scope rabbit holes to avoid.** The CMA-ES rewrite (Rank 10), implementing the $(\mu, \kappa, \lambda, \rho)$-ES with life span (BSw95 §6.6), multi-population / island models (§6.5), and the multi-objective Kursawe variant (§6.5). All interesting; none deliverable in our remaining time. The Bosman 2009 *empirical memory design* paper (the AMaLGaM lineage) is interesting if we end up wanting to compare against the C reference, but is not relevant to improving `evopy`.

---

*End of study guide. Sources cross-referenced: `BSw95.pdf` §6.1-6.6, `assignment-brief.pdf` §A-D (CiaS), `presentation-rubric.pdf`, `lectures/lecture-3/` (Notes.md is empty; the heavy lifting is in `reading-material/summary.md` and the two concept notes), `meetings/2026-05-11-meeting-01.md`, `meetings/2026-05-12-meeting-TA.md`, and the entire `EvolutionStrategyPython/` source tree.*
