import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recomb_best_sigma_directed_benchmark import run_one
from ES.evopy import Strategy
import traceback

cases = [
    ('coordinate', 15, Strategy.MULTIPLE_VARIANCE, {'recombine': True, 'recombination_mode': 'coordinate'}, 0),
    ('circle_pair', 15, Strategy.MULTIPLE_VARIANCE, {'recombine': True, 'recombination_mode': 'circle_pair'}, 0),
]
for task in cases:
    print('Running task:', task)
    try:
        row = run_one(task)
        print('OK:', row)
    except Exception:
        print('ERROR for task:', task)
        traceback.print_exc()
print('Done')
