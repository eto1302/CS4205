import csv
import os
import sys

def filter_per_run(src, dst, treatments):
    with open(src, newline='') as f_in, open(dst, 'w', newline='') as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row.get('treatment') in treatments:
                writer.writerow(row)

def filter_comparisons(src, dst, treatments):
    with open(src, newline='') as f_in, open(dst, 'w', newline='') as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.DictWriter(f_out, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row.get('treatment') in treatments:
                writer.writerow(row)

def main():
    if len(sys.argv) < 2:
        print('Usage: make_recomb_single_artifacts.py <dest_dir>')
        sys.exit(1)
    dest = sys.argv[1]
    os.makedirs(dest, exist_ok=True)
    src_per = os.path.join('results', 'per_run.csv')
    src_cmp = os.path.join('results', 'comparisons.csv')
    dst_per = os.path.join(dest, 'per_run_recomb_single.csv')
    dst_cmp = os.path.join(dest, 'comparisons_recomb_single.csv')
    treatments = {'baseline', 'sigma_single_recomb_coord', 'sigma_single_recomb_pair'}
    filter_per_run(src_per, dst_per, treatments)
    filter_comparisons(src_cmp, dst_cmp, treatments)
    print('Wrote', dst_per)
    print('Wrote', dst_cmp)

if __name__ == '__main__':
    main()
