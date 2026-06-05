import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
from ES.evopy.individual import Individual
from ES.evopy.strategy import Strategy
from ES.evopy.recombination import recombine_individuals

# create two MULTIPLE_VARIANCE individuals with d=6
d = 6
geno_a = np.arange(d)
geno_b = np.arange(d) + 10
sig_a = [0.5] * d
sig_b = [1.5] * d
pa = Individual(geno_a, Strategy.MULTIPLE_VARIANCE, sig_a, random_seed=1)
pb = Individual(geno_b, Strategy.MULTIPLE_VARIANCE, sig_b, random_seed=2)

for mode in ('coordinate','circle_pair'):
    print('\nMODE:', mode)
    g,s = recombine_individuals(pa,pb,mode=mode,random=np.random.RandomState(0))
    print('type(strategy_child):', type(s))
    print('strategy_child:', s)
    import numpy as _np
    s_arr = _np.asarray(s)
    print('np.asarray(strategy_child).shape:', s_arr.shape)
    # Check if any element is a list
    any_list = any(isinstance(x, list) for x in (s if hasattr(s,'__iter__') else [s]))
    print('any element is list:', any_list)
    # check all scalar numeric
    all_numeric = all((isinstance(x, (int,float,_np.floating,_np.integer)) ) for x in s_arr.flatten())
    print('all elements numeric scalars:', all_numeric)

print('\nDone')
