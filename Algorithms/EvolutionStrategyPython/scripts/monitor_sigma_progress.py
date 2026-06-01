import time
import os
import csv
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / 'results' / 'per_run.csv'

def summarize(path: Path):
    if not path.exists():
        print(f"[{datetime.datetime.now()}] No results file yet: {path}")
        return
    try:
        with path.open('r', encoding='utf8') as fh:
            rows = list(csv.reader(fh))
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Error reading file: {e}")
        return
    if len(rows) <= 1:
        print(f"[{datetime.datetime.now()}] File exists but no data rows yet (header only).")
        return
    header = rows[0]
    data = rows[1:]
    n = len(data)
    last = data[-1]
    # try to make a compact last-row display
    try:
        d = dict(zip(header, last))
        last_summary = f"treatment={d.get('treatment')}, n={d.get('n')}, seed={d.get('seed')}, final_best={d.get('final_best')[:8] if d.get('final_best') else ''}"
    except Exception:
        last_summary = ','.join(last[:6])
    print(f"[{datetime.datetime.now()}] Rows: {n}; Last: {last_summary}")

if __name__ == '__main__':
    print(f"Starting sigma monitor; polling {RESULTS} every 1800s. Ctrl+C to stop.")
    summarize(RESULTS)
    try:
        while True:
            time.sleep(1800)
            summarize(RESULTS)
    except KeyboardInterrupt:
        print('Monitor stopped by user.')
