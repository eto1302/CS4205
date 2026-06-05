"""Directed recombination benchmark for best sigma strategies (WP4).

Runs the specified n/strategy cases and three treatments (baseline, coordinate, circle_pair).
Writes results and comparisons and generates plots and a summary markdown into
repo-root `benchmark_wp4_results/benchmark_recomb_best_sigma_directed_100k_25seeds_<timestamp>/`.

Supports a smoke mode when env `WP4_RECOMB_SMOKE=1` is set (runs a tiny quick check).
"""
import os
import csv
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import numpy as np
import pandas as pd
from datetime import datetime
import traceback

from ES.evopy import EvoPy, Strategy

# env-overridable defaults
SMOKE = os.environ.get('WP4_RECOMB_SMOKE', '') == '1'
CASES = [
    (7, Strategy.SINGLE_VARIANCE),
    (7, Strategy.MULTIPLE_VARIANCE),
    (10, Strategy.SINGLE_VARIANCE),
    (10, Strategy.MULTIPLE_VARIANCE),
    (15, Strategy.MULTIPLE_VARIANCE),
    (20, Strategy.MULTIPLE_VARIANCE),
]
if SMOKE:
    CASES = [(7, Strategy.SINGLE_VARIANCE)]

N_SEEDS = int(os.environ.get('WP4_RECOMB_SEEDS', '25'))
MAX_EVALS = int(os.environ.get('WP4_RECOMB_EVALS', '100000'))
if SMOKE:
    N_SEEDS = int(os.environ.get('WP4_RECOMB_SEEDS', '1'))
    MAX_EVALS = int(os.environ.get('WP4_RECOMB_EVALS', '1000'))

WORKERS = os.environ.get('WP4_RECOMB_WORKERS')
if WORKERS:
    WORKERS = max(1, int(WORKERS))
else:
    try:
        cpu = os.cpu_count() or 1
        WORKERS = max(1, min(cpu - 1 if cpu > 1 else 1, 8))
    except Exception:
        WORKERS = 1

POPULATION = 30
NUM_CHILDREN = 7
TOLS = [1e-2, 1e-3, 1e-5]
RESULTS_DIR = 'results'
PER_RUN_CSV = os.path.join(RESULTS_DIR, 'per_run.csv')

# treatments per case
TREATMENTS = [
    ('baseline', {'recombine': False}),
    ('coordinate', {'recombine': True, 'recombination_mode': 'coordinate'}),
    ('circle_pair', {'recombine': True, 'recombination_mode': 'circle_pair'}),
]

_TARGETS = [
    1.4142135623730951, 1.0352761804100830, 1.0000000000000000, 0.7071067811865475,
    0.6009252125773315, 0.5358983848622454, 0.5176380902050415, 0.5000000000000000,
    0.4212795439839034, 0.3982073102368442, 0.3887301263230200, 0.3660960076964251,
    0.3489152603740189, 0.3410813774021089, 0.3333333333333333, 0.3061539853003329,
    0.3004626062886658, 0.2895419919949817, 0.2866116523516816,
]

def get_target(n_circles):
    return _TARGETS[n_circles - 2]


def fitness(individual):
    pts = np.asarray(individual).reshape(-1, 2)
    d = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))
    np.fill_diagonal(d, np.inf)
    return float(d.min())


def run_one(case_strategy_overrides):
    # args: (label, n, strategy, overrides, seed)
    label, n, strategy, overrides, seed = case_strategy_overrides
    try:
        trace = []
        def reporter(r):
            trace.append((r.evaluations, r.best_fitness))
        kwargs = dict(
            strategy=strategy,
            selection_scheme='comma',
            init='lhs',
            population_size=POPULATION,
            num_children=NUM_CHILDREN,
        )
        kwargs.update(overrides)
        # instantiate EvoPy so we can inspect state on exception
        ep = EvoPy(
            fitness, n * 2,
            reporter=reporter, maximize=True, bounds=(0, 1),
            generations=100000, max_evaluations=MAX_EVALS, random_seed=seed,
            **kwargs,
        )
        ep.run()

        evals = np.array([e for e, _ in trace])
        best = np.array([b for _, b in trace])
        final_best = float(best[-1])
        row = {
            'treatment': label,
            'wp': 'WP4',
            'n_circles': n,
            'seed': seed,
            'strategy': kwargs['strategy'].name,
            'init': kwargs['init'],
            'selection_scheme': kwargs['selection_scheme'],
            'final_best': round(final_best, 8),
            'final_gap': round((get_target(n) - final_best) / get_target(n), 8),
            'total_evals': int(evals[-1]),
            'total_generations': len(trace),
        }
        for tol in TOLS:
            hit = np.where(np.abs(best - get_target(n)) < tol)[0]
            row[f'evals_to_{tol:.0e}'] = int(evals[hit[0]]) if len(hit) else ''
        return row
    except Exception:
        msg = f"Exception in worker run_one — treatment={label}, n={n}, strategy={getattr(strategy,'name',strategy)}, seed={seed}, overrides={overrides}\n"
        tb = traceback.format_exc()
        print(msg)
        print(tb)
        try:
            # ensure results dir exists
            Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)
            with open(os.path.join(RESULTS_DIR, 'worker_errors.log'), 'a', encoding='utf-8') as fh:
                fh.write(f"TIME: {datetime.now().isoformat()}\n")
                fh.write(msg)
                fh.write(tb)
                # include trace summary if available
                try:
                    fh.write('TRACE_LAST= ' + repr(trace[-5:]) + '\n')
                except Exception:
                    fh.write('TRACE_LAST= none\n')
                # include EvoPy state summary if available
                try:
                    ep_attrs = {
                        'strategy': getattr(ep.strategy, 'name', repr(ep.strategy)),
                        'recombine': getattr(ep, 'recombine', None),
                        'recombination_mode': getattr(ep, 'recombination_mode', None),
                        'population_size': getattr(ep, 'population_size', None),
                        'num_children': getattr(ep, 'num_children', None),
                        'individual_length': getattr(ep, 'individual_length', None),
                    }
                    fh.write('EVOPY_STATE: ' + repr(ep_attrs) + '\n')
                    # try to materialize an init population to inspect shapes
                    try:
                        pop = ep._init_population()
                        fh.write('INIT_POP sample sizes: ' + ','.join(str((len(getattr(i,'genotype',i.parameters)), len(getattr(i,'strategy_parameters',[])))) for i in pop[:3]) + '\n')
                    except Exception as e2:
                        fh.write('INIT_POP failed: ' + repr(e2) + '\n')
                except Exception as e1:
                    fh.write('EVOPY_STATE_INSPECT_FAILED: ' + repr(e1) + '\n')
                fh.write('\n')
        except Exception:
            # best-effort logging; don't mask original exception
            print('Failed to write worker error log:', traceback.format_exc())
        raise


def write_per_run(rows, results_dir=RESULTS_DIR):
    os.makedirs(results_dir, exist_ok=True)
    fields = [
        'treatment','wp','n_circles','seed','strategy','init','selection_scheme',
        'final_best','final_gap','total_evals','total_generations'
    ] + [f'evals_to_{t:.0e}' for t in TOLS]
    with open(os.path.join(results_dir, 'per_run.csv'), 'w', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _get_workers():
    return WORKERS


def run_parallel():
    tasks = []
    for n, strategy in CASES:
        for name, overrides in TREATMENTS:
            for seed in range(N_SEEDS):
                tasks.append((name, n, strategy, overrides, seed))
    n_total = len(tasks)
    workers = _get_workers()
    print('=== Directed recomb-best sigma benchmark ===')
    print('cases:', CASES)
    print('treatments:', [t[0] for t in TREATMENTS])
    print(f'seeds: {N_SEEDS}, total runs: {n_total}, eval budget per run: {MAX_EVALS}, workers: {workers}')

    t0 = time.time()
    rows = []
    completed = 0
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(run_one, task): task for task in tasks}
        for fut in as_completed(futures):
            try:
                row = fut.result()
            except Exception as e:
                task = futures[fut]
                name, n, strat, overrides, seed = task
                print(f"Task failed for n={n}, strategy={getattr(strat,'name',str(strat))}, treatment={name}, seed={seed}")
                print('Exception:', e)
                print(traceback.format_exc())
                continue
            rows.append(row)
            completed += 1
            if completed % 10 == 0 or completed == n_total:
                elapsed = time.time() - t0
                avg = elapsed / completed
                remaining = n_total - completed
                eta = avg * remaining
                def fmt_s(s):
                    m, s = divmod(int(s), 60)
                    h, m = divmod(m, 60)
                    return f"{h:02d}:{m:02d}:{s:02d}"
                print(f'Completed {completed}/{n_total} runs; ETA {fmt_s(eta)}')

    rows.sort(key=lambda r: (r['treatment'], int(r['n_circles']), int(r['seed'])))
    write_per_run(rows)
    dt = time.time() - t0
    print(f'Wrote {PER_RUN_CSV}. Collected {len(rows)} rows in {dt:.1f}s')
    return dt


def run_stats_and_archive(timestamp):
    # run stats.py to produce comparisons.csv
    here = Path(__file__).resolve().parent
    stats_path = here / 'stats.py'
    if stats_path.exists():
        print('Running stats.py to compute comparisons...')
        os.system(f'python "{stats_path}"')
    else:
        print('Missing stats.py; skipping comparisons generation')

    # copy artifacts to repo-root benchmark folder
    repo_root = Path(__file__).resolve().parents[2]
    out_folder = repo_root / 'benchmark_wp4_results' / f'benchmark_recomb_best_sigma_directed_100k_25seeds_{timestamp}'
    out_folder.mkdir(parents=True, exist_ok=True)
    # copy per_run and comparisons
    for name in ['per_run.csv','comparisons.csv']:
        src = Path(RESULTS_DIR) / name
        if src.exists():
            dst = out_folder / src.name
            dst.write_bytes(src.read_bytes())
    return out_folder


def make_plots(out_folder):
    try:
        import seaborn as sns
        import matplotlib.pyplot as plt
    except Exception:
        print('matplotlib/seaborn not available; skipping plots')
        return []
    df = pd.read_csv(os.path.join(RESULTS_DIR, 'per_run.csv'))
    df['n_circles'] = df['n_circles'].astype(int)
    plots = []
    # boxplot
    plt.figure(figsize=(10,6))
    sns.boxplot(data=df, x='n_circles', y='final_gap', hue='treatment')
    plt.title('Recombination final_gap by n & treatment')
    p1 = out_folder / 'recomb_directed_final_gap_boxplot.png'
    plt.savefig(p1, bbox_inches='tight')
    plt.close()
    plots.append(p1)
    # median lines
    med = df.groupby(['n_circles','treatment'])['final_gap'].median().reset_index()
    pivot = med.pivot(index='n_circles', columns='treatment', values='final_gap')
    plt.figure(figsize=(10,6))
    for col in pivot.columns:
        plt.plot(pivot.index, pivot[col], marker='o', label=col)
    plt.legend()
    plt.title('Median final_gap by n')
    p2 = out_folder / 'recomb_directed_median_final_gap_lines.png'
    plt.savefig(p2, bbox_inches='tight')
    plt.close()
    plots.append(p2)
    # effect barplot: baseline vs each arm per n
    # baseline label is 'baseline'
    baseline = df[df['treatment']=='baseline'].groupby('n_circles')['final_gap'].median()
    arms = df[df['treatment'].isin(['coordinate','circle_pair'])]
    med_arms = arms.groupby(['n_circles','treatment'])['final_gap'].median().reset_index()
    med_arms['baseline'] = med_arms['n_circles'].map(baseline)
    med_arms['effect'] = med_arms['baseline'] - med_arms['final_gap']
    plt.figure(figsize=(10,6))
    sns.barplot(data=med_arms, x='n_circles', y='effect', hue='treatment')
    plt.axhline(0, color='k', linestyle='--')
    plt.title('Effect (baseline median - arm median)')
    p3 = out_folder / 'recomb_directed_effect_barplot.png'
    plt.savefig(p3, bbox_inches='tight')
    plt.close()
    plots.append(p3)
    print('Wrote plots to', out_folder)
    return plots


def make_summary(out_folder, runtime):
    per = pd.read_csv(os.path.join(RESULTS_DIR, 'per_run.csv'))
    comps = pd.read_csv(os.path.join(RESULTS_DIR, 'comparisons.csv')) if os.path.exists(os.path.join(RESULTS_DIR, 'comparisons.csv')) else None
    rows = []
    for (n, strategy), group in per.groupby(['n_circles','strategy']):
        for treatment, g2 in group.groupby('treatment'):
            rows.append((n, strategy, treatment, g2['final_gap'].median(), g2['final_gap'].quantile(0.25), g2['final_gap'].quantile(0.75)))
    dfm = pd.DataFrame(rows, columns=['n','strategy','treatment','median_final_gap','q1','q3'])
    # write markdown
    md = []
    md.append('# Directed recombination benchmark — best sigma strategies')
    md.append(f'- runtime: {runtime:.1f}s')
    md.append(f'- output folder: {out_folder}')
    md.append(f'- rows in per_run.csv: {len(per)}')
    md.append('\n## Median final_gap by n, strategy, treatment')
    md.append(dfm.to_markdown(index=False))
    if comps is not None:
        md.append('\n## Comparisons (from stats.py)')
        md.append(comps.to_markdown(index=False))
    path = out_folder / 'WP4_recomb_best_sigma_directed_summary.md'
    path.write_text('\n\n'.join(md))
    print('Wrote summary to', path)
    return path


def git_status_short():
    try:
        import subprocess
        p = subprocess.run(['git','status','--porcelain'], cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True)
        return p.stdout.strip()
    except Exception:
        return 'git unavailable'


def main():
    ts = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    t0 = time.time()
    runtime = run_parallel()
    out_folder = run_stats_and_archive(ts)
    plots = make_plots(out_folder)
    summary = make_summary(out_folder, runtime)
    gs = git_status_short()
    print('\nFINAL REPORT')
    print('output folder:', out_folder)
    print('rows in per_run.csv:', len(pd.read_csv(os.path.join(RESULTS_DIR, 'per_run.csv'))))
    print('summary:', summary)
    print('plots:', plots)
    print('git status --short:\n', gs)

if __name__ == '__main__':
    main()
