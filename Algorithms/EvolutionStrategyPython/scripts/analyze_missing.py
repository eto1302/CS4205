import pandas as pd
from pathlib import Path
p=Path('results')/'per_run.csv'
df=pd.read_csv(p)
# counts
counts = df.groupby(['n_circles','strategy','treatment']).size().reset_index(name='count')
print('Counts by n/strategy/treatment:')
print(counts.to_string(index=False))

# expected combinations
cases = [(7,'SINGLE_VARIANCE'),(7,'MULTIPLE_VARIANCE'),(10,'SINGLE_VARIANCE'),(10,'MULTIPLE_VARIANCE'),(15,'MULTIPLE_VARIANCE'),(20,'MULTIPLE_VARIANCE')]
treatments=['baseline','coordinate','circle_pair']
seeds=list(range(25))
rows_present=set((int(r['n_circles']),r['strategy'],r['treatment'],int(r['seed'])) for i,r in df.iterrows())
missing=[]
for n,strat in cases:
    for tr in treatments:
        for s in seeds:
            if (n,strat,tr,s) not in rows_present:
                missing.append((n,strat,tr,s))
print(f'\nTotal rows present: {len(df)}')
print(f'Expected rows: {len(cases)*len(treatments)*len(seeds)}')
print(f'Missing rows: {len(missing)}')
# show sample of missing grouped by n
from collections import defaultdict
g=defaultdict(list)
for (n,strat,tr,s) in missing:
    g[(n,strat,tr)].append(s)
print('\nMissing per (n,strategy,treatment) with counts:')
for k in sorted(g.keys()):
    print(k, 'missing seeds count', len(g[k]), 'seeds sample', g[k][:10])

# determine if missing rows concentrated
print('\nSummary of missing by n:')
from collections import Counter
print(Counter([n for n,_,_,_ in missing]))
print('\nSummary of missing by strategy:')
print(Counter([strat for _,strat,_,_ in missing]))
print('\nSummary of missing by treatment:')
print(Counter([tr for _,_,tr,_ in missing]))
