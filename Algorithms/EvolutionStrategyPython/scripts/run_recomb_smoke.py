import os
from pathlib import Path
import sys
os.environ['WP4_RECOMB_EVALS'] = '1000'
os.environ['WP4_RECOMB_SEEDS'] = '1'
os.environ['WP4_RECOMB_WORKERS'] = '1'

# Ensure parent dir (module source) is importable when running from scripts/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recomb_best_sigma_directed_benchmark import run_one
from ES.evopy import Strategy

tasks = [
    ('baseline', 15, Strategy.MULTIPLE_VARIANCE, {'recombine': False}, 0),
    ('coordinate', 15, Strategy.MULTIPLE_VARIANCE, {'recombine': True, 'recombination_mode': 'coordinate'}, 0),
    ('circle_pair', 15, Strategy.MULTIPLE_VARIANCE, {'recombine': True, 'recombination_mode': 'circle_pair'}, 0),
]

for t in tasks:
    print('==== Running', t[0], '====')
    try:
        row = run_one(t)
        print('OK ->', row)
    except Exception as e:
        import traceback
        print('FAILED ->', e)
        print(traceback.format_exc())
