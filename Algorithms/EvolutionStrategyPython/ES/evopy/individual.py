"""Module containing the individuals of the evolutionary strategy algorithm."""
import numpy as np

from ES.evopy.strategy import Strategy
from ES.evopy.utils import random_with_seed

# Valid repair modes: kept as frozenset so the error message is always accurate
_REPAIR_MODES_ = frozenset({"random", "clip", "reflect"})

def _repair(genotype: np.ndarray, lo: float, hi: float,
            mode: str, rng) -> np.ndarray:
    """Return a copy of 'genotype' with all alleles brought back into [lo, hi].

    Parameters
    -------------
    genotype: np.ndarray
        The raw (possibly out-of-bounds) offspring genotype.
    lo, hi: float
        Lower and upper bounds of the box.
    mode: str
        One of "random", "clip", or "reflect".
    rng: numpy RandomState
        Used only by "random"mode; ignored by the other two.

    Mode explanations
    ------------------
    "random"
    Original behaviour: replace each OOB (out of bounds) allele with an independent "uniform(lo, hi)" draw.
    Discards both the direction and magnitude of the mutation step, acts as a random restart 
    for that coordinate.

    "clip"
    Clamp to the nearest boundary (np.clip). Preserves the *direction* of the step. 
    Magnitude is capped at the boundary distance (box).
    May accumulate density at the boundary, not too dangerous for CiaS because many
    optimal circle centres already lie close to the boundary.


    "reflect"
    Tent-map. An overshoot of +δ past the upper wall is brought back to (hi - δ), an 
    overshoot of -δ past the lower wall lands at (lo + δ).
    Handles arbitrarily large steps via "%(2*span)".
    Preserves *both* direction and magnitude, no boundary density bias.
    This is the theoretically preferred mode for CiaS because optimal packings concentrate near the boundary,
    where the other two modes are more disruptive to self-adaptation.  
    """

    if mode == "clip":
        return np.clip(genotype, lo, hi)
    
    if mode == "reflect":
        span = hi - lo
        v = (genotype - lo) % (2.0 * span) # shift values so the interval starts at 0, wraps into [0, 2span)
        return np.where(v > span, 2.0 * span - v, v) + lo
    
    # mode == "random" (original, default)
    oob = (genotype < lo) | (genotype > hi) #| - elementwise "or"
    n_oob = int(np.count_nonzero(oob)) #count how many values are out of bounds within a genotype
    if n_oob:
        genotype = genotype.copy() #create copy to not modify the original array
        genotype[oob] = rng.uniform(lo, hi, size = n_oob) #generate n_oob random numbers uniformly distrubuted bet lo and hi
    return genotype


# def reflect_into_bounds(x, low, high):
#     """Reflect values in ``x`` into the box [low, high] using a tent map.

#     Preserves the magnitude of the intended mutation step instead of
#     discarding it (which random-resample does).
#     """
#     range_ = high - low
#     if range_ <= 0:
#         return x
#     y = np.mod(x - low, 2.0 * range_)
#     y = np.where(y > range_, 2.0 * range_ - y, y)
#     return low + y


class Individual:
    """The individual of the evolutionary strategy algorithm.

    This class handles the reproduction of the individual, using both the genotype and the specified
    strategy.

    For the full variance reproduction strategy, we adopt the implementation as described in:
    [1] Schwefel, Hans-Paul. (1995). Evolution Strategies I: Variants and their computational
        implementation. G. Winter, J. Perieaux, M. Gala, P. Cuesta (Eds.), Proceedings of Genetic
        Algorithms in Engineering and Computer Science, John Wiley & Sons.
    """
    _BETA = 0.0873
    _EPSILON = 1e-7

    def __init__(self, genotype, strategy, strategy_parameters, bounds=None, random_seed=None, repair="random"):
        """Initialize the Individual.

        Parameters
        ----------
        genotype : array-like
            The genotype of the individual.
        strategy : Strategy
            Reproduction strategy. See the Strategy enum.
        strategy_parameters : list
            Parameters required for the chosen strategy.
        bounds : tuple(float, float) or None
            (lo, hi) box constraint applied during reproduction.
        random_seed : int or numpy RandomState, optional
            Seed for the RNG.
        repair : str, optional
            Constraint-repair mode used after mutation.  Must be one of
            ``"random"`` (default, original behaviour), ``"clip"``, or
            ``"reflect"``.  The value is forwarded to every child produced
            by ``reproduce()`` so it stays consistent across generations.
        """
        self.genotype = genotype
        self.length = len(genotype)
        self.random_seed = random_seed
        self.random = random_with_seed(self.random_seed)
        self.fitness = None
        self.constraint = None
        self.bounds = bounds
        self.strategy = strategy
        self.strategy_parameters = strategy_parameters
        self.repair = repair #propagated to every child below

        if not isinstance(strategy, Strategy):
            raise ValueError("Provided strategy parameter was not an instance of Strategy.")
        if strategy == Strategy.SINGLE_VARIANCE and len(strategy_parameters) == 1:
            self.reproduce = self._reproduce_single_variance
        elif strategy == Strategy.MULTIPLE_VARIANCE and len(strategy_parameters) == self.length:
            self.reproduce = self._reproduce_multiple_variance
        elif strategy == Strategy.FULL_VARIANCE and len(strategy_parameters) == self.length * (
                self.length + 1) / 2:
            self.reproduce = self._reproduce_full_variance
        elif strategy == Strategy.SINGLE_VARIANCE_1_5 and len(strategy_parameters) == 1:
            self.reproduce = self._reproduce_single_variance_1_5
        else:
            raise ValueError("The length of the strategy parameters was not correct.")
        
    # ── fitness evaluation ────────────────────────────────────────────────────

    def evaluate(self, fitness_function):
        """Evaluate the genotype of the individual using the provided fitness function.

        :param fitness_function: the fitness function to evaluate the individual with
        :return: the value of the fitness function using the individuals genotype
        """
        self.fitness = fitness_function(self.genotype)

        return self.fitness
    
    # ── reproduction methods ──────────────────────────────────────────────────

    def _reproduce_single_variance(self):
        """Create a single offspring individual from the set genotype and strategy parameters.

        This function uses the single variance strategy.

        :return: an individual which is the offspring of the current instance
        """
        new_genotype = (self.genotype
                         + self.strategy_parameters[0] * self.random.randn(self.length))
        
        new_genotype = _repair(new_genotype,
                               self.bounds[0], self.bounds[1],
                               self.repair, self.random)  #unified repair
        
        scale_factor = self.random.randn() * np.sqrt(1 / (2 * self.length))
        new_parameters = [max(self.strategy_parameters[0] * np.exp(scale_factor), self._EPSILON)]

        return Individual(new_genotype, self.strategy, new_parameters,
                           bounds=self.bounds, 
                           random_seed=self.random,
                           repair = self.repair) # <- thread through


    def _reproduce_multiple_variance(self):
        """Create a single offspring individual from the set genotype and strategy.

        This function uses the multiple variance strategy.

        :return: an individual which is the offspring of the current instance
        """
        new_genotype = (self.genotype + [self.strategy_parameters[i] * self.random.randn()
                                        for i in range(self.length)])
        
        new_genotype = _repair(new_genotype,
                               self.bounds[0], self.bounds[1],
                               self.repair, self.random) #unified repair
        
        global_scale_factor = self.random.randn() * np.sqrt(1 / (2 * self.length))
        scale_factors = [self.random.randn() / np.sqrt(2 * np.sqrt(self.length))
                         for _ in range(self.length)]
        new_parameters = [max(np.exp(global_scale_factor + scale_factors[i])
                              * self.strategy_parameters[i], self._EPSILON)
                          for i in range(self.length)]
        return Individual(new_genotype, self.strategy, new_parameters, 
                          bounds=self.bounds, 
                          random_seed=self.random,
                          repair = self.repair)  #<- thread through

    # pylint: disable=invalid-name
    def _reproduce_full_variance(self):
        """Create a single offspring individual from the set genotype and strategy.

        This function uses the full variance strategy, as described in [1]. To emphasize this, the
        variable names of [1] are used in this function.

        :return: an individual which is the offspring of the current instance
        """
        global_scale_factor = self.random.randn() * np.sqrt(1 / (2 * self.length))
        scale_factors = [self.random.randn() / np.sqrt(2 * np.sqrt(self.length))
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
                j = p * (2 * self.length - p - 1) // 2 + (q - p - 1)
                T_pq = np.identity(self.length)
                T_pq[p][p] = T_pq[q][q] = np.cos(new_rotations[j])
                T_pq[p][q] = -np.sin(new_rotations[j])
                T_pq[q][p] = -T_pq[p][q]
                T = np.matmul(T, T_pq)
        # new_genotype = self.genotype + T @ self.random.randn(self.length)
        new_genotype = self.genotype + T @ (np.array(new_variances) * self.random.randn(self.length))

        new_genotype = _repair(new_genotype,
                               self.bounds[0], self.bounds[1],
                               self.repair, self.random) #unified repair
   
        return Individual(new_genotype, self.strategy, new_variances + new_rotations,
                         bounds=self.bounds, 
                         random_seed=self.random,
                         repair = self.repair) # <- thread through
