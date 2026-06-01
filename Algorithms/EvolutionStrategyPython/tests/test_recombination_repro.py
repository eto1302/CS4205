import os
import sys
os.environ['WP1_EVALS'] = '1000'
# ensure the ES package dir is importable when running from the repo root
sys.path.insert(0, os.path.join(os.getcwd(), 'Algorithms', 'EvolutionStrategyPython'))
import importlib
repo_root = os.path.dirname(os.path.abspath(__file__))
ofat_dir = os.path.join(repo_root, '..')
os.chdir(ofat_dir)
sys.path.insert(0, ofat_dir)
mod = importlib.import_module('ofat_benchmark')
run_one = mod.run_one

print('Running seed=0, first run')
row1 = run_one({"population_size": 10, "num_children": 1}, 7, 0)
print('Running seed=0, second run')
row2 = run_one({"population_size": 10, "num_children": 1}, 7, 0)
print('Running seed=1')
row3 = run_one({"population_size": 10, "num_children": 1}, 7, 1)

# compare
same12 = row1 == row2
same13 = row1 == row3
print('seed0 run1 == seed0 run2:', same12)
print('seed0 run1 == seed1 run1:', same13)
print('Row1 final_best:', row1['final_best'])
print('Row2 final_best:', row2['final_best'])
print('Row3 final_best:', row3['final_best'])
