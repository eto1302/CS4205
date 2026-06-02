import numpy as np
from ES.evopy.recombination import circular_mean_angles, recombine_individuals
from ES.evopy.individual import Individual
from ES.evopy.strategy import Strategy


def test_circular_mean_wraparound():
    eps = 1e-3
    a = np.pi - eps
    b = -np.pi + eps
    res = circular_mean_angles(a, b)
    # Expect near +/-pi (not near 0)
    assert abs(abs(float(res)) - np.pi) < 1e-2


def test_coordinate_alpha_behaviour_and_lengths():
    # For genotype length d=4, FULL_VARIANCE strategy has 4 sigmas + 6 alphas
    d = 4
    sigma_a = [0.5, 0.6, 0.7, 0.8]
    sigma_b = [0.2, 0.3, 0.4, 0.5]
    eps = 1e-3
    # 6 alpha entries for d=4; include wrap-around cases
    alpha_a = [np.pi - eps, 0.1, -0.5, 2.0, -2.5, 1.2]
    alpha_b = [-np.pi + eps, 0.2, 1.0, -2.0, 2.5, -1.2]

    strat_a = sigma_a + alpha_a
    strat_b = sigma_b + alpha_b

    geno_a = [0.0] * d
    geno_b = [1.0] * d

    parent_a = Individual(geno_a, Strategy.FULL_VARIANCE, strat_a, random_seed=123)
    parent_b = Individual(geno_b, Strategy.FULL_VARIANCE, strat_b, random_seed=456)

    rng = np.random.RandomState(42)
    child_geno_alpha, child_strat_alpha = recombine_individuals(parent_a, parent_b, mode="coordinate_alpha", random=rng)

    # Lengths preserved
    assert len(child_strat_alpha) == len(strat_a)

    # Sigma part arithmetic average
    expected_sigma = [(a + b) / 2.0 for a, b in zip(sigma_a, sigma_b)]
    assert np.allclose(child_strat_alpha[:d], expected_sigma)

    # Alpha part circular mean
    expected_alpha = circular_mean_angles(np.array(alpha_a), np.array(alpha_b))
    assert np.allclose(child_strat_alpha[d:d + len(expected_alpha)], expected_alpha)

    # Now test that regular 'coordinate' mode preserves/inherits alpha from parent_a
    rng2 = np.random.RandomState(42)
    _, child_strat_coord = recombine_individuals(parent_a, parent_b, mode="coordinate", random=rng2)
    assert np.allclose(child_strat_coord[:d], expected_sigma)
    # For non-alpha modes, rotation part should be inherited from parent_a
    assert np.allclose(child_strat_coord[d:], alpha_a)

