import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

root = os.path.join(os.getcwd(), '..', '..')
# path to benchmark folder created by last run
bench_dir = os.path.join(root, 'benchmark_wp4_results', 'benchmark_sigma_alln_medium_2026-06-04_20-13-50')
out_dir = os.path.join(root, 'benchmark_wp4_results', 'wp4_plots')
os.makedirs(out_dir, exist_ok=True)

per_run_path = os.path.join(bench_dir, 'per_run.csv')
if not os.path.exists(per_run_path):
    print('Missing', per_run_path)
    raise SystemExit(1)

df = pd.read_csv(per_run_path)
df['n_circles'] = df['n_circles'].astype(int)

# Boxplot
plt.figure(figsize=(10,6))
sns.boxplot(data=df[df['treatment'].isin(['SINGLE_VARIANCE','MULTIPLE_VARIANCE','baseline','FULL_VARIANCE'])], x='n_circles', y='final_gap', hue='treatment')
plt.title('Sigma final_gap by n_circles')
plt.savefig(os.path.join(out_dir, 'sigma_final_gap_boxplot_highres.png'), dpi=300, bbox_inches='tight')
plt.close()

# Median lines
med = df[df['treatment'].isin(['SINGLE_VARIANCE','MULTIPLE_VARIANCE','baseline','FULL_VARIANCE'])].groupby(['n_circles','treatment'])['final_gap'].median().reset_index()
pivot = med.pivot(index='n_circles', columns='treatment', values='final_gap')
plt.figure(figsize=(10,6))
for col in pivot.columns:
    plt.plot(pivot.index, pivot[col], marker='o', label=col)
plt.xlabel('n_circles')
plt.ylabel('median final_gap')
plt.title('Sigma strategy ablation across sizes')
plt.legend()
plt.savefig(os.path.join(out_dir, 'sigma_median_final_gap_lines_highres.png'), dpi=300, bbox_inches='tight')
plt.close()

print('Wrote plots to', out_dir)
