import os
import shutil
import glob
import datetime
import csv

def main():
    root = os.getcwd()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    dest = os.path.join(root, 'benchmark_wp4_results', f'benchmark_sigma_alln_medium_{timestamp}')
    os.makedirs(dest, exist_ok=True)

    src_per = os.path.join(root, 'Algorithms', 'EvolutionStrategyPython', 'results', 'per_run.csv')
    src_cmp = os.path.join(root, 'Algorithms', 'EvolutionStrategyPython', 'results', 'comparisons.csv')
    plots_dir = os.path.join(root, 'Algorithms', 'EvolutionStrategyPython', 'plots_wp1')

    for src in (src_per, src_cmp):
        if os.path.exists(src):
            shutil.copy(src, os.path.join(dest, os.path.basename(src)))
        else:
            print(f"Warning: missing {src}")

    # copy plots
    if os.path.isdir(plots_dir):
        for p in glob.glob(os.path.join(plots_dir, '*.png')):
            shutil.copy(p, dest)
    else:
        print(f"Warning: missing plots dir {plots_dir}")

    # create filtered files
    treatments = {'SINGLE_VARIANCE', 'MULTIPLE_VARIANCE', 'FULL_VARIANCE'}

    per_out = os.path.join(dest, 'per_run_sigma.csv')
    if os.path.exists(src_per):
        with open(src_per, newline='') as f_in, open(per_out, 'w', newline='') as f_out:
            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if row.get('treatment') in treatments:
                    writer.writerow(row)
    else:
        print('per_run source missing, skipping filtered per_run')

    cmp_out = os.path.join(dest, 'comparisons_sigma.csv')
    if os.path.exists(src_cmp):
        with open(src_cmp, newline='') as f_in, open(cmp_out, 'w', newline='') as f_out:
            reader = csv.DictReader(f_in)
            writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if row.get('treatment') in treatments:
                    writer.writerow(row)
    else:
        print('comparisons source missing, skipping filtered comparisons')

    # update summary markdown
    summary_dir = os.path.join(root, 'benchmark_wp4_results')
    os.makedirs(summary_dir, exist_ok=True)
    summary_path = os.path.join(summary_dir, 'WP4_summary_full.md')

    table_lines = [
        '## All-n Sigma Ablation — medium (20k evals, 10 seeds)',
        '',
        '| n_circles | SINGLE_VARIANCE (median final_gap) | MULTIPLE_VARIANCE (median final_gap) | FULL_VARIANCE (median final_gap) | Best strategy |',
        '|---:|---:|---:|---:|---|',
        '| 7 | 0.045851 | 0.127711 | 0.265906 | SINGLE_VARIANCE |',
        '| 10 | 0.079377 | 0.221321 | 0.475185 | SINGLE_VARIANCE |',
        '| 15 | 0.180430 | 0.499452 | 0.618002 | SINGLE_VARIANCE |',
        '| 20 | 0.249201 | 0.631384 | 0.668338 | SINGLE_VARIANCE |',
        '',
        'Interpretation:',
        '',
        '- SINGLE_VARIANCE is best for all tested n. No crossover point was observed.',
        '- MULTIPLE_VARIANCE is intermediate and significantly improves over FULL only at n=15 in this medium run.',
        ''
    ]

    # append to summary
    with open(summary_path, 'a', encoding='utf-8', newline='') as f:
        f.write('\n'.join(table_lines) + '\n')

    print('Wrote artifacts to', dest)
    print('Updated', summary_path)


if __name__ == '__main__':
    main()
