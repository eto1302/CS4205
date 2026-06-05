import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from recomb_best_sigma_directed_benchmark import run_one
from ES.evopy import Strategy
from concurrent.futures import ProcessPoolExecutor, as_completed


def main():
    n = 15
    strategy = Strategy.MULTIPLE_VARIANCE
    workers = 4
    seeds = list(range(5))
    T = [
        ('coordinate', {'recombine': True, 'recombination_mode': 'coordinate'}),
        ('circle_pair', {'recombine': True, 'recombination_mode': 'circle_pair'}),
    ]

    tasks = []
    for name, overrides in T:
        for s in seeds:
            tasks.append((name, n, strategy, overrides, s))

    print('Submitting', len(tasks), 'tasks with', workers, 'workers')
    results = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(run_one, t): t for t in tasks}
        for fut in as_completed(futures):
            t = futures[fut]
            try:
                r = fut.result()
                print('OK', t, '->', r['final_gap'])
                results.append(r)
            except Exception as e:
                print('FAIL', t, 'Exception:', e)
    print('Done. Collected', len(results), 'results')


if __name__ == '__main__':
    main()
