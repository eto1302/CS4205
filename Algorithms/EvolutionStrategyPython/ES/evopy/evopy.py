"""Module used for the execution of the evolutionary algorithm."""
import time

import numpy as np

from ES.evopy.individual import Individual
from ES.evopy.progress_report import ProgressReport
from ES.evopy.strategy import Strategy
from ES.evopy.utils import random_with_seed


class EvoPy:
    """Main class of the EvoPy package."""

    _EPSILON = 1e-7
    # Rechenberg's contraction factor for the 1/5 rule.
    # success_rate > 1/5  => sigma /= _C_15 (grow)
    # success_rate < 1/5  => sigma *= _C_15 (shrink)
    _C_15 = 0.817

    def __init__(self, fitness_function, individual_length, warm_start=None, generations=100,
                 population_size=30, num_children=1, mean=0, std=1, maximize=False,
                 strategy=Strategy.SINGLE_VARIANCE, random_seed=None, reporter=None,
                 target_fitness_value=None, target_tolerance=1e-5, max_run_time=None,
                 max_evaluations=None, bounds=None, selection_scheme="plus",
                 init_sigma_scale=0.3, init="lhs", local_search="none", local_search_k=10,
                 local_search_final_budget=None):
        """Initializes an EvoPy instance.

        :param fitness_function: the fitness function on which the individuals are evaluated
        :param individual_length: the length of each individual
        :param warm_start: the individual to start from
        :param generations: the number of generations to execute
        :param population_size: the population size of each generation
        :param num_children: the number of children generated per parent individual
        :param mean: the mean for sampling the random offsets of the initial population
        :param std: the standard deviation for sampling the random offsets of the initial population
        :param maximize: whether the fitness function should be maximized or minimized
        :param strategy: the strategy used to generate offspring by individuals. For more
                         information, check the Strategy enum
        :param random_seed: the seed to use for the random number generator
        :param reporter: callback to be invoked at each generation with a ProgressReport as argument
        :param target_fitness_value: target fitness value for early stopping
        :param target_tolerance: tolerance to within target fitness value is to be acquired
        :param max_run_time: maximum time allowed to run in seconds
        :param max_evaluations: maximum allowed number of fitness function evaluations
        :param bounds: bounds for the sampling the parameters of individuals
        :param selection_scheme: "plus" for (mu+lambda) or "comma" for (mu,lambda)
        :param init_sigma_scale: initial step size as a fraction of the bounds range
        :param local_search: "none" (default), "final" (one L-BFGS-B polish after the loop),
                             or "interleaved" (polish best every local_search_k generations)
        :param local_search_k: interval in generations for "interleaved" local search
        :param local_search_final_budget: evaluations reserved for the final L-BFGS-B call;
                                          defaults to max_evaluations // 10 when None
        """
        self.fitness_function = fitness_function
        self.individual_length = individual_length
        self.warm_start = np.zeros(self.individual_length) if warm_start is None else warm_start
        self.generations = generations
        self.population_size = population_size
        self.num_children = num_children
        self.mean = mean
        self.std = std
        self.maximize = maximize
        self.strategy = strategy
        self.random_seed = random_seed
        self.random = random_with_seed(self.random_seed)
        self.reporter = reporter
        self.target_fitness_value = target_fitness_value
        self.target_tolerance = target_tolerance
        self.max_run_time = max_run_time
        self.max_evaluations = max_evaluations
        self.bounds = bounds
        self.selection_scheme = selection_scheme
        self.init_sigma_scale = init_sigma_scale
        self.init = init
        self.local_search = local_search
        self.local_search_k = local_search_k
        self.local_search_final_budget = local_search_final_budget
        self.evaluations = 0
        self._ea_max_evals = None   # set in run(); EA stops here, leaving room for polish
        self._polish_maxfun = None  # set in run(); budget handed to L-BFGS-B
        # Population-level sigma for the 1/5 rule variant (set in run()).
        self._sigma_1_5 = None

    def _check_early_stop(self, start_time, best):
        """Check whether the algorithm can stop early, based on time and fitness target.

        :param start_time: the starting time to compare against
        :param best: the current best individual
        :return: whether the algorithm should be terminated early
        """
        ea_cap = self._ea_max_evals if self._ea_max_evals is not None else self.max_evaluations
        return (self.max_run_time is not None
                and (time.time() - start_time) > self.max_run_time) \
               or \
               (self.target_fitness_value is not None
                and abs(best.fitness - self.target_fitness_value) < self.target_tolerance) \
               or (ea_cap is not None
                and self.evaluations >= ea_cap)

    def run(self):
        """Run the evolutionary strategy algorithm.

        :return: the best genotype found
        """
        if self.individual_length == 0:
            return None

        # Reserve a slice of the budget for the final L-BFGS-B call so it
        # actually gets to run (default: 10% of max_evaluations).
        if self.local_search == "final" and self.max_evaluations is not None:
            budget = self.local_search_final_budget
            if budget is None:
                budget = max(self.individual_length * 10, self.max_evaluations // 10)
            self._ea_max_evals = self.max_evaluations - budget
            self._polish_maxfun = budget
        else:
            self._ea_max_evals = None
            self._polish_maxfun = None

        start_time = time.time()

        population = self._init_population()
        # Initial evaluation of parents (needed for (mu+lambda) and 1/5 rule).
        for ind in population:
            ind.evaluate(self.fitness_function)
        self.evaluations += len(population)
        population.sort(reverse=self.maximize, key=lambda ind: ind.fitness)
        best = population[0]

        use_1_5_rule = self.strategy == Strategy.SINGLE_VARIANCE_1_5
        if use_1_5_rule:
            bounds_range = (self.bounds[1] - self.bounds[0]) if self.bounds is not None else 1.0
            self._sigma_1_5 = self.init_sigma_scale * bounds_range

        for generation in range(self.generations):
            parents = list(population)

            # Inject the population-level sigma into all parents before reproduction,
            # so every child uses the same currently-tuned step size.
            if use_1_5_rule:
                for p in parents:
                    p.strategy_parameters = [self._sigma_1_5]

            children = [parent.reproduce()
                        for parent in parents
                        for _ in range(self.num_children)]

            for child in children:
                child.evaluate(self.fitness_function)
            self.evaluations += len(children)

            # 1/5 success rule: update sigma based on the fraction of children
            # that strictly improved over their parent.
            if use_1_5_rule:
                n_success = 0
                for i, child in enumerate(children):
                    parent_fit = parents[i // self.num_children].fitness
                    improved = (child.fitness > parent_fit) if self.maximize \
                        else (child.fitness < parent_fit)
                    if improved:
                        n_success += 1
                success_rate = n_success / max(len(children), 1)
                if success_rate > 1.0 / 5.0:
                    self._sigma_1_5 /= self._C_15
                elif success_rate < 1.0 / 5.0:
                    self._sigma_1_5 *= self._C_15
                self._sigma_1_5 = max(self._sigma_1_5, self._EPSILON)

            # Selection: (mu+lambda) pools parents+children, (mu,lambda) only children.
            pool = (parents + children) if self.selection_scheme == "plus" else children
            population = sorted(pool, reverse=self.maximize, key=lambda ind: ind.fitness)
            population = population[:self.population_size]
            best = population[0]

            if self.reporter is not None:
                mean = np.mean([x.fitness for x in population])
                std = np.std([x.fitness for x in population])
                self.reporter(ProgressReport(generation, self.evaluations, best.genotype, best.fitness, mean, std))

            if self.local_search == "interleaved" and (generation + 1) % self.local_search_k == 0:
                polished_g, polished_f = self._lbfgsb_polish(best.genotype)
                improved = polished_f > best.fitness if self.maximize else polished_f < best.fitness
                if improved:
                    best.genotype = polished_g
                    best.fitness = polished_f
                    population[0] = best

            if self._check_early_stop(start_time, best):
                break

        if self.local_search == "final":
            polished_g, polished_f = self._lbfgsb_polish(best.genotype)
            best.genotype = polished_g
            best.fitness = polished_f

        return best.genotype

    def _lbfgsb_polish(self, genotype):
        """Polish a genotype with L-BFGS-B, charging all evaluations to self.evaluations."""
        from scipy.optimize import minimize

        sign = -1.0 if self.maximize else 1.0

        def objective(x):
            self.evaluations += 1
            return sign * self.fitness_function(x)

        bounds = ([(self.bounds[0], self.bounds[1])] * self.individual_length
                  if self.bounds is not None else None)
        if self._polish_maxfun is not None:
            maxfun = self._polish_maxfun
        else:
            maxfun = (max(1, self.max_evaluations - self.evaluations)
                      if self.max_evaluations is not None
                      else self.individual_length * 200)

        result = minimize(objective, genotype.copy(), method="L-BFGS-B",
                          bounds=bounds, options={"maxfun": maxfun})
        polished_fitness = -result.fun if self.maximize else result.fun
        return result.x, polished_fitness

    def _init_population(self):
        # Sensible problem-scaled initial sigma rather than randn() which can give
        # near-zero or negative values that collapse to the EPSILON floor.
        bounds_range = (self.bounds[1] - self.bounds[0]) if self.bounds is not None else 1.0
        sigma0 = self.init_sigma_scale * bounds_range
        d = self.individual_length

        if self.strategy == Strategy.SINGLE_VARIANCE:
            strategy_parameters = [sigma0]
        elif self.strategy == Strategy.MULTIPLE_VARIANCE:
            strategy_parameters = [sigma0] * d
        elif self.strategy == Strategy.FULL_VARIANCE:
            # d variances (set to sigma0) + d(d-1)/2 rotation angles (set to 0 = identity).
            strategy_parameters = [sigma0] * d + [0.0] * (d * (d - 1) // 2)
        elif self.strategy == Strategy.SINGLE_VARIANCE_1_5:
            # Placeholder; EvoPy.run() overwrites this each generation with the
            # population-level sigma maintained by the 1/5 rule.
            strategy_parameters = [sigma0]
        else:
            raise ValueError("Provided strategy parameter was not an instance of Strategy")

        # Latin-hypercube initial population: spreads samples across [low, high]^d
        # so circles are not all clustered near the centre at gen 0.
        if self.bounds is not None and self.init == "lhs":
            samples = self._latin_hypercube(self.population_size, d)
            population_parameters = self.bounds[0] + samples * bounds_range
        elif self.bounds is not None and self.init == "uniform":
            # i.i.d. uniform in the box — the un-stratified control for the LHS
            # ablation arm (same marginal as LHS, no space-filling stratification).
            population_parameters = self.random.uniform(
                self.bounds[0], self.bounds[1], size=(self.population_size, d))
        else:
            population_parameters = np.asarray([
                self.warm_start + self.random.normal(loc=self.mean, scale=self.std, size=d)
                for _ in range(self.population_size)
            ])

        return [
            Individual(
                parameters,
                self.strategy,
                list(strategy_parameters),  # one independent copy per individual
                random_seed=self.random,
                bounds=self.bounds,
            ) for parameters in population_parameters
        ]

    def _latin_hypercube(self, n_samples, n_dim):
        """Generate a Latin-hypercube sample in [0,1)^n_dim using ``self.random``."""
        samples = np.empty((n_samples, n_dim))
        for j in range(n_dim):
            perm = self.random.permutation(n_samples)
            jitter = self.random.uniform(0.0, 1.0, n_samples)
            samples[:, j] = (perm + jitter) / n_samples
        return samples
