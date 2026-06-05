import sys
from pathlib import Path
import csv
import time
from datetime import datetime
import traceback

# ensure imports from parent package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recomb_best_sigma_directed_benchmark import run_one, CASES, TREATMENTS, N_SEEDS, RESULTS_DIR, write_per_run, make_plots, make_summary

# paths
repo_root = Path(__file__).resolve().parents[2]
results_dir = Path(__file__).resolve().parent / RESULTS_DIR
incomplete_benchmark_folder = repo_root / 'benchmark_wp4_results' / 'benchmark_recomb_best_sigma_directed_100k_25seeds_2026-06-05_10-53-04'
# use existing per_run.csv from results
per_run_path = results_dir / 'per_run.csv'
if not per_run_path.exists():
    raise SystemExit(f'missing base per_run.csv at {per_run_path}')

# read existing rows
import pandas as pd
existing = pd.read_csv(per_run_path)
# build present keys set
present = set((int(r['n_circles']), r['strategy'], r['treatment'], int(r['seed'])) for _, r in existing.iterrows())

# build expected tasks
expected_tasks = []
for n, strategy in CASES:
    for name, overrides in TREATMENTS:
        for seed in range(N_SEEDS):
            expected_tasks.append((name, n, strategy, overrides, seed))

# identify missing
missing = [t for t in expected_tasks if (t[1], getattr(t[2],'name',t[2]), t[0], t[4]) not in present]

# but earlier pattern shows strategy names in present are strings, ensure comparison uses strategy.name
# create normalized present keys
present_norm = set((int(r['n_circles']), r['strategy'], r['treatment'], int(r['seed'])) for _, r in existing.iterrows())
missing = [t for t in expected_tasks if (t[1], t[2].name if hasattr(t[2],'name') else str(t[2]), t[0], t[4]) not in present_norm]

# Prepare completed output folder
ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
out_folder = repo_root / 'benchmark_wp4_results' / f'benchmark_recomb_best_sigma_directed_100k_25seeds_completed_{ts}'
out_folder.mkdir(parents=True, exist_ok=True)

# save missing_before.csv
miss_path = out_folder / 'missing_before.csv'
with open(miss_path, 'w', newline='') as fh:
    writer = csv.writer(fh)
    writer.writerow(['treatment','n_circles','strategy','seed'])
    for name, n, strategy, overrides, seed in missing:
        writer.writerow([name, n, strategy.name if hasattr(strategy,'name') else str(strategy), seed])

# resume run sequentially
resume_log = out_folder / 'resume_log.txt'
rows = [r.to_dict() for _, r in existing.iterrows()]
start_time = time.time()
with open(resume_log, 'w', encoding='utf-8') as logf:
    logf.write(f'Resume started: {datetime.now().isoformat()}\n')
    logf.write(f'Found {len(rows)} existing rows; missing {len(missing)} tasks\n')
    for i, task in enumerate(missing, 1):
        name, n, strategy, overrides, seed = task
        logf.write(f'[{i}/{len(missing)}] Running {task}\n')
        logf.flush()
        try:
            r = run_one(task)
            rows.append(r)
            logf.write(f'  OK: seed={seed} n={n} treatment={name}\n')
        except Exception as e:
            tb = traceback.format_exc()
            logf.write(f'  FAIL: seed={seed} n={n} treatment={name} EXC: {e}\n')
            logf.write(tb + '\n')
        logf.flush()

# write combined per_run.csv to results and to out_folder
# determine fields same as write_per_run uses
fields = [
    'treatment','wp','n_circles','seed','strategy','init','selection_scheme',
    'final_best','final_gap','total_evals','total_generations'
]
# detect eval columns from rows
tol_cols = [c for c in rows[0].keys() if c.startswith('evals_to_')]
fields += tol_cols

# write to results/per_run.csv (overwrite) and also copy to out_folder
results_dir.mkdir(parents=True, exist_ok=True)
combined_path = results_dir / 'per_run.csv'
with open(combined_path, 'w', newline='') as fh:
    writer = csv.DictWriter(fh, fieldnames=fields)
    writer.writeheader()
    for r in rows:
        writer.writerow(r)

# copy to out_folder
import shutil
shutil.copy2(combined_path, out_folder / 'per_run.csv')

# run stats.py to produce comparisons.csv
# stats.py lives in same folder as this script
stats_path = Path(__file__).resolve().parent / 'stats.py'
if stats_path.exists():
    logf = open(resume_log, 'a', encoding='utf-8')
    logf.write('Running stats.py...\n')
    logf.flush()
    import subprocess
    subprocess.run([sys.executable, str(stats_path)], cwd=stats_path.parent)
    logf.write('stats.py finished\n')
    logf.close()

# copy comparisons.csv if present
comp_src = results_dir / 'comparisons.csv'
if comp_src.exists():
    shutil.copy2(comp_src, out_folder / 'comparisons.csv')

# make plots and summary
try:
    plots = make_plots(out_folder)
except Exception as e:
    with open(resume_log, 'a', encoding='utf-8') as logf:
        logf.write('make_plots failed: ' + repr(e) + '\n')

# make summary
try:
    runtime = time.time() - start_time
    summary_path = make_summary(out_folder, runtime)
except Exception as e:
    with open(resume_log, 'a', encoding='utf-8') as logf:
        logf.write('make_summary failed: ' + repr(e) + '\n')

# write final resume log footer
with open(resume_log, 'a', encoding='utf-8') as logf:
    logf.write(f'Finished resume at {datetime.now().isoformat()}\n')
    logf.write(f'Combined rows: {len(rows)}\n')

print('Resume complete. Output folder:', out_folder)
print('Combined rows:', len(rows))
print('Missing before saved to', miss_path)
print('Resume log saved to', resume_log)
