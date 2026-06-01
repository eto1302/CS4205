import time, subprocess, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEQ = ROOT / 'sigma_ablation.py'
PAR = ROOT / 'sigma_ablation_parallel.py'

def run(cmd_path):
    print('Running', cmd_path)
    t0 = time.time()
    subprocess.check_call([os.environ.get('PYTHON','python'), str(cmd_path)])
    dt = time.time() - t0
    print('Elapsed', dt)
    return dt

if __name__ == '__main__':
    # run sequential then parallel (1 and 4 workers) as examples
    os.environ.setdefault('WP1_SEEDS','3')
    os.environ.setdefault('WP1_NS','20')
    os.environ.setdefault('WP1_EVALS','20000')

    # Sequential
    seq_time = run(SEQ)

    # Parallel 1 worker
    os.environ['WP1_WORKERS'] = '1'
    par1_time = run(PAR)

    # Parallel 4 workers
    os.environ['WP1_WORKERS'] = '4'
    par4_time = run(PAR)

    print('\nSummary:')
    print('seq_time', seq_time)
    print('par1_time', par1_time)
    print('par4_time', par4_time)
    if par4_time:
        print('speedup (seq/par4)=', seq_time / par4_time)
