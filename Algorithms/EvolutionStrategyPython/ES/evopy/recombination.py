"""Recombination operators for EvoPy.

Provides `recombine_individuals(parent_a, parent_b, mode)` which returns a
tuple `(genotype, strategy_parameters)` representing the recombined
pre-mutation individual. This keeps the implementation separate from
`individual.py` and allows a minimal hook in `EvoPy`.
"""
import numpy as np
from ES.evopy.strategy import Strategy


def circular_mean_angles(a, b):
    """Circular mean between angles a and b.

    Works for scalars or numpy arrays and returns values in [-pi, pi].
    """
    a_arr = np.asarray(a)
    b_arr = np.asarray(b)
    s = np.sin(a_arr) + np.sin(b_arr)
    c = np.cos(a_arr) + np.cos(b_arr)
    return np.arctan2(s, c)


def recombine_individuals(parent_a, parent_b, mode="coordinate", random=None):
    """Recombine two individuals.

    Params
    - parent_a, parent_b: Individual instances (read-only)
    - mode: "coordinate" or "circle_pair"

    Returns
    - (genotype, strategy_parameters): both are lists / numpy arrays suitable
      for creating a new `Individual` before mutation.
    """
    # allow deterministic RNG (numpy RandomState) for reproducibility
    rng = np.random if random is None else random

    # Genotypes: numpy arrays
    a_g = np.asarray(parent_a.genotype)
    b_g = np.asarray(parent_b.genotype)
    # support alpha-aware mode names by grouping
    coord_modes = ("coordinate", "coordinate_alpha")
    pair_modes = ("circle_pair", "circle_pair_alpha")

    if mode in coord_modes:
        mask = rng.randint(0, 2, size=a_g.shape, dtype=bool)
        new_genotype = np.where(mask, a_g, b_g)
    elif mode in pair_modes:
        # genotype interpreted as (x0,y0,x1,y1,...). Recombine whole pairs.
        if a_g.size % 2 != 0:
            # fall back to coordinate if odd-length
            mask = rng.randint(0, 2, size=a_g.shape, dtype=bool)
            new_genotype = np.where(mask, a_g, b_g)
        else:
            new_genotype = a_g.copy()
            pairs = a_g.size // 2
            pick = rng.randint(0, 2, size=pairs, dtype=bool)
            for i in range(pairs):
                if not pick[i]:
                    new_genotype[2 * i: 2 * i + 2] = b_g[2 * i: 2 * i + 2]
    else:
        raise ValueError("Unknown recombination mode: %s" % mode)

    # Strategy parameters: handle per-strategy behavior.
    a_s = list(parent_a.strategy_parameters)
    b_s = list(parent_b.strategy_parameters)
    a_s_arr = np.asarray(a_s)
    b_s_arr = np.asarray(b_s)

    # use module-level circular_mean_angles

    # If the parents use FULL_VARIANCE, average only the first d sigma values
    # and handle rotation angles (alpha) according to mode suffix.
    if isinstance(parent_a.strategy, Strategy) and parent_a.strategy == Strategy.FULL_VARIANCE:
        d = parent_a.length
        # safe-guard lengths
        if a_s_arr.size >= d and b_s_arr.size >= d:
            sigma_part = (a_s_arr[:d] + b_s_arr[:d]) / 2.0
            # compute rotation/alpha part if present in both parents
            a_rot = a_s_arr[d:]
            b_rot = b_s_arr[d:]
            if mode.endswith("_alpha") and a_rot.size > 0 and b_rot.size > 0:
                rot_len = min(a_rot.size, b_rot.size)
                rotation_part = circular_mean_angles(a_rot[:rot_len], b_rot[:rot_len])
                # if one parent has extra rotation entries, keep them from a
                if a_rot.size > rot_len:
                    rotation_part = np.concatenate([rotation_part, a_rot[rot_len:]])
            else:
                # inherit rotations from parent_a (preserve existing behaviour)
                rotation_part = a_rot
            new_strategy = np.concatenate([sigma_part, rotation_part])
        else:
            # fallback: average up to min length and keep remainder from a
            m = min(a_s_arr.size, b_s_arr.size)
            head = (a_s_arr[:m] + b_s_arr[:m]) / 2.0
            tail = a_s_arr[m:]
            new_strategy = np.concatenate([head, tail])
    else:
        # SINGLE_VARIANCE or MULTIPLE_VARIANCE: average all entries where possible
        if a_s_arr.size == b_s_arr.size:
            new_strategy = (a_s_arr + b_s_arr) / 2.0
        else:
            m = min(a_s_arr.size, b_s_arr.size)
            head = (a_s_arr[:m] + b_s_arr[:m]) / 2.0
            tail = a_s_arr[m:]
            new_strategy = np.concatenate([head, tail])

    return new_genotype.tolist(), new_strategy.tolist()
