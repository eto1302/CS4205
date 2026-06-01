import csv
from pathlib import Path
p=Path('results')
seq=list(csv.reader(open(p/'per_run_seq.csv')))
par=list(csv.reader(open(p/'per_run.csv')))
header_seq=seq[0]
header_par=par[0]
if header_seq!=header_par:
    print('DIFFERENT HEADERS')
else:
    s=set(tuple(r) for r in seq[1:])
    pset=set(tuple(r) for r in par[1:])
    only_seq=s-pset
    only_par=pset-s
    print('rows seq:',len(seq)-1,'rows par:',len(par)-1)
    print('only in seq:',len(only_seq))
    print('only in par:',len(only_par))
    if len(only_seq):
        print('Example seq-only:', next(iter(only_seq)))
    if len(only_par):
        print('Example par-only:', next(iter(only_par)))
