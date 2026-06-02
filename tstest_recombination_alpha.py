[1mdiff --git a/Algorithms/EvolutionStrategyPython/ES/evopy/recombination.py b/Algorithms/EvolutionStrategyPython/ES/evopy/recombination.py[m
[1mindex 5a5917c..019fc78 100644[m
[1m--- a/Algorithms/EvolutionStrategyPython/ES/evopy/recombination.py[m
[1m+++ b/Algorithms/EvolutionStrategyPython/ES/evopy/recombination.py[m
[36m@@ -9,6 +9,18 @@[m [mimport numpy as np[m
 from ES.evopy.strategy import Strategy[m
 [m
 [m
[32m+[m[32mdef circular_mean_angles(a, b):[m
[32m+[m[32m    """Circular mean between angles a and b.[m
[32m+[m
[32m+[m[32m    Works for scalars or numpy arrays and returns values in [-pi, pi].[m
[32m+[m[32m    """[m
[32m+[m[32m    a_arr = np.asarray(a)[m
[32m+[m[32m    b_arr = np.asarray(b)[m
[32m+[m[32m    s = np.sin(a_arr) + np.sin(b_arr)[m
[32m+[m[32m    c = np.cos(a_arr) + np.cos(b_arr)[m
[32m+[m[32m    return np.arctan2(s, c)[m
[32m+[m
[32m+[m
 def recombine_individuals(parent_a, parent_b, mode="coordinate", random=None):[m
     """Recombine two individuals.[m
 [m
[36m@@ -26,11 +38,14 @@[m [mdef recombine_individuals(parent_a, parent_b, mode="coordinate", random=None):[m
     # Genotypes: numpy arrays[m
     a_g = np.asarray(parent_a.genotype)[m
     b_g = np.asarray(parent_b.genotype)[m
[32m+[m[32m    # support alpha-aware mode names by grouping[m
[32m+[m[32m    coord_modes = ("coordinate", "coordinate_alpha")[m
[32m+[m[32m    pair_modes = ("circle_pair", "circle_pair_alpha")[m
 [m
[31m-    if mode == "coordinate":[m
[32m+[m[32m    if mode in coord_modes:[m
         mask = rng.randint(0, 2, size=a_g.shape, dtype=bool)[m
         new_genotype = np.where(mask, a_g, b_g)[m
[31m-    elif mode == "circle_pair":[m
[32m+[m[32m    elif mode in pair_modes:[m
         # genotype interpreted as (x0,y0,x1,y1,...). Recombine whole pairs.[m
         if a_g.size % 2 != 0:[m
             # fall back to coordinate if odd-length[m
[36m@@ -52,15 +67,27 @@[m [mdef recombine_individuals(parent_a, parent_b, mode="coordinate", random=None):[m
     a_s_arr = np.asarray(a_s)[m
     b_s_arr = np.asarray(b_s)[m
 [m
[32m+[m[32m    # use module-level circular_mean_angles[m
[32m+[m
     # If the parents use FULL_VARIANCE, average only the first d sigma values[m
[31m-    # and inherit rotation angles (alpha) from parent_a. For SINGLE_VARIANCE[m
[31m-    # and MULTIPLE_VARIANCE, average all strategy parameters element-wise.[m
[32m+[m[32m    # and handle rotation angles (alpha) according to mode suffix.[m
     if isinstance(parent_a.strategy, Strategy) and parent_a.strategy == Strategy.FULL_VARIANCE:[m
         d = parent_a.length[m
         # safe-guard lengths[m
         if a_s_arr.size >= d and b_s_arr.size >= d:[m
             sigma_part = (a_s_arr[:d] + b_s_arr[:d]) / 2.0[m
[31m-            rotation_part = a_s_arr[d:][m
[32m+[m[32m            # compute rotation/alpha part if present in both parents[m
[32m+[m[32m            a_rot = a_s_arr[d:][m
[32m+[m[32m            b_rot = b_s_arr[d:][m
[32m+[m[32m            if mode.endswith("_alpha") and a_rot.size > 0 and b_rot.size > 0:[m
[32m+[m[32m                rot_len = min(a_rot.size, b_rot.size)[m
[32m+[m[32m                rotation_part = circular_mean_angles(a_rot[:rot_len], b_rot[:rot_len])[m
[32m+[m[32m                # if one parent has extra rotation entries, keep them from a[m
[32m+[m[32m                if a_rot.size > rot_len:[m
[32m+[m[32m                    rotation_part = np.concatenate([rotation_part, a_rot[rot_len:]])[m
[32m+[m[32m            else:[m
[32m+[m[32m                # inherit rotations from parent_a (preserve existing behaviour)[m
[32m+[m[32m                rotation_part = a_rot[m
             new_strategy = np.concatenate([sigma_part, rotation_part])[m
         else:[m
             # fallback: average up to min length and keep remainder from a[m
