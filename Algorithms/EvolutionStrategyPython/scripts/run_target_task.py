import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recomb_best_sigma_directed_benchmark import run_one
from ES.evopy import Strategy
import traceback

# targeted task from previous incomplete run
n = 15
strategy = Strategy.MULTIPLE_VARIANCE
name = 'coordinate'
overrides = {'recombine': True, 'recombination_mode': 'coordinate'}
seed = 0
task = (name, n, strategy, overrides, seed)
print('Running target task:', task)
try:
    row = run_one(task)
    print('OK:', row)
except Exception:
    print('ERROR for task:', task)
    traceback.print_exc()
