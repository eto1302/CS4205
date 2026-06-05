import os
import csv
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from recomb_best_sigma_directed_benchmark import CASES, TREATMENTS, N_SEEDS, POPULATION, NUM_CHILDREN, MAX_EVALS
from recomb_best_sigma_directed_benchmark import run_one, get_target

RESULTS_DIR = 'results'
PER_RUN = Path(RESULTS_DIR) / 'per_run.csv'

# load existing
if PER_RUN.exists():
    df = pd.read_csv(PER_RUN)
else:
    df = pd.DataFrame()

completed = set()
for _, row in df.iterrows():
    completed.add((row['treatment'], int(row['n_circles']), row['strategy'], int(row['seed'])))

# build expected tasks
tasks = []
for n, strategy in CASES:
    for name, overrides in TREATMENTS:
        for seed in range(N_SEEDS):
            tasks.append((name, n, strategy, overrides, seed))

missing = [t for t in tasks if (t[0], t[1], t[2].name, t[4]) not in completed]
print(f'Total expected: {len(tasks)}, already completed: {len(completed)}, missing: {len(missing)}')

if not missing:
    print('Nothing to do')
    raise SystemExit(0)

# append missing sequentially
PER_RUN.parent.mkdir(parents=True, exist_ok=True)
fields = ['treatment','wp','n_circles','seed','strategy','init','selection_scheme','final_best','final_gap','total_evals','total_generations']
# detect evals_to fields from existing or default
extra = [f'evals_to_{t:.0e}' for t in [1e-2,1e-3,1e-5]]
fields += extra

# open file in append mode
with open(PER_RUN, 'a', newline='') as fh:
    writer = csv.DictWriter(fh, fieldnames=fields)
    if PER_RUN.stat().st_size == 0:
        writer.writeheader()
    for t in missing:
        label, n, strategy, overrides, seed = t
        try:
            row = run_one((label, n, strategy, overrides, seed))
        except Exception as e:
            print('Run failed for', t, '->', e)
            continue
        # ensure fields
        r = {k: row.get(k, '') for k in fields}
        writer.writerow(r)
        print('Appended', (label, n, strategy.name, seed))

print('Done')
