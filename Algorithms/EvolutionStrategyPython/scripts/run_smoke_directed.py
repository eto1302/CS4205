import sys
from pathlib import Path
# ensure parent dir on path so local modules import correctly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recomb_best_sigma_directed_benchmark import run_one, TREATMENTS
from ES.evopy import Strategy
import traceback

# tiny targeted smoke
n = 15
strategy = Strategy.MULTIPLE_VARIANCE
seed = 0
results = []
for name, overrides in TREATMENTS:
    if name not in ('baseline','coordinate','circle_pair'):
        continue
    task = (name, n, strategy, overrides, seed)
    print('Running task:', task)
    try:
        row = run_one(task)
        print('OK:', row)
        results.append(row)
    except Exception:
        print('ERROR for task:', task)
        traceback.print_exc()

print('Finished smoke; rows collected:', len(results))
