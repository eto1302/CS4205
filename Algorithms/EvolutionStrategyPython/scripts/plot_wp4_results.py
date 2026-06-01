import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


def safe_read(path):
    if not os.path.exists(path):
        print(f"Missing file: {path}")
        return None
    return pd.read_csv(path)


def ensure_dir(d):
    os.makedirs(d, exist_ok=True)


def plot_sigma_boxplot(df, out_path):
    treatments = ['SINGLE_VARIANCE', 'MULTIPLE_VARIANCE', 'FULL_VARIANCE']
    df_f = df[df['treatment'].isin(treatments)].copy()
    if df_f.empty:
        print('No sigma rows for boxplot')
        return
    df_f['n_circles'] = df_f['n_circles'].astype(int)
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df_f, x='n_circles', y='final_gap', hue='treatment')
    plt.title('Sigma final_gap by n_circles')
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()


def plot_sigma_median_lines(df, out_path):
    treatments = ['SINGLE_VARIANCE', 'MULTIPLE_VARIANCE', 'FULL_VARIANCE']
    df_f = df[df['treatment'].isin(treatments)].copy()
    if df_f.empty:
        print('No sigma rows for median lines')
        return
    df_f['n_circles'] = df_f['n_circles'].astype(int)
    med = df_f.groupby(['n_circles', 'treatment'])['final_gap'].median().reset_index()
    pivot = med.pivot(index='n_circles', columns='treatment', values='final_gap')
    plt.figure(figsize=(8, 5))
    for col in pivot.columns:
        plt.plot(pivot.index, pivot[col], marker='o', label=col)
    plt.xlabel('n_circles')
    plt.ylabel('median final_gap')
    plt.title('Sigma strategy ablation across CiaS sizes')
    plt.legend()
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()


def plot_recomb_effect_bar(df, out_path):
    # expects baseline SINGLE and arms in same df
    if df is None:
        print('Missing recomb df')
        return
    df['n_circles'] = df['n_circles'].astype(int)
    # baseline medians
    baseline = df[df['treatment'] == 'SINGLE_VARIANCE'].groupby('n_circles')['final_gap'].median()
    arms = df[df['treatment'].isin(['sigma_single_recomb_coord', 'sigma_single_recomb_pair'])]
    if arms.empty:
        print('No recomb arm rows')
        return
    med_arms = arms.groupby(['n_circles', 'treatment'])['final_gap'].median().reset_index()
    med_arms['baseline'] = med_arms['n_circles'].map(baseline)
    med_arms['effect'] = med_arms['baseline'] - med_arms['final_gap']
    plt.figure(figsize=(8, 5))
    sns.barplot(data=med_arms, x='n_circles', y='effect', hue='treatment')
    plt.axhline(0, color='k', linestyle='--')
    plt.ylabel('effect (baseline median - arm median)')
    plt.title('Recombination effect vs SINGLE baseline')
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()


def plot_recomb_final_gap_box(df, out_path):
    names = ['SINGLE_VARIANCE', 'sigma_single_recomb_coord', 'sigma_single_recomb_pair']
    df_f = df[df['treatment'].isin(names)].copy()
    if df_f.empty:
        print('No recomb rows for boxplot')
        return
    df_f['n_circles'] = df_f['n_circles'].astype(int)
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df_f, x='n_circles', y='final_gap', hue='treatment')
    plt.title('Recombination on best sigma strategy')
    plt.savefig(out_path, bbox_inches='tight')
    plt.close()


def main():
    root = os.path.join(os.getcwd(), 'benchmark_wp4_results')
    sigma_dir = os.path.join(root, 'benchmark_sigma_alln_medium_2026-06-01_11-57-29')
    recomb_dir = os.path.join(root, 'benchmark_recomb_single_medium_2026-05-30_14-17-34')
    out = os.path.join(root, 'wp4_plots')
    ensure_dir(out)

    sigma_per = safe_read(os.path.join(sigma_dir, 'per_run_sigma.csv'))
    sigma_cmp = safe_read(os.path.join(sigma_dir, 'comparisons_sigma.csv'))
    recomb_per = safe_read(os.path.join(recomb_dir, 'per_run_recomb_single.csv'))
    recomb_cmp = safe_read(os.path.join(recomb_dir, 'comparisons_recomb_single.csv'))

    # Plot 1
    if sigma_per is not None:
        plot_sigma_boxplot(sigma_per, os.path.join(out, 'sigma_final_gap_boxplot.png'))
        plot_sigma_median_lines(sigma_per, os.path.join(out, 'sigma_median_final_gap_lines.png'))
    else:
        print('Skipping sigma plots: missing data')

    # Plot 2/3
    if recomb_per is not None:
        plot_recomb_effect_bar(recomb_per, os.path.join(out, 'recomb_effect_barplot.png'))
        plot_recomb_final_gap_box(recomb_per, os.path.join(out, 'recomb_final_gap_boxplot.png'))
    else:
        print('Skipping recombination plots: missing data')

    print('WP4 plots written to', out)


if __name__ == '__main__':
    main()
