"""Read-only dataset inspection; never accesses organizer data."""
import csv
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(name):
    with (ROOT / 'dataset' / (name + '.csv')).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

if __name__ == '__main__':
    events = read('financial_events')
    if len(sys.argv) == 1:
        for name in ('requests', 'financial_profiles', 'financial_events', 'messages', 'images'):
            rows = read(name)
            print(name, len(rows))
        for key in ('event_type', 'status', 'flexibility', 'category'):
            print(key, dict(collections.Counter(e[key] for e in events)))
        print('blank amounts', [e for e in events if not e['amount']])
    for user in sys.argv[1:]:
        user = 'user_' + user.zfill(2)
        print('\nPROFILE', next(p for p in read('financial_profiles') if p['user_id'] == user))
        print('REQUEST', next(p for p in read('requests') + read('sample_requests') if p['user_id'] == user))
        groups = collections.defaultdict(list)
        for e in events:
            if e['user_id'] == user:
                groups[(e['description'], e['direction'])].append(e)
        for key, rows in groups.items():
            print('GROUP', key, 'n=', len(rows), [(e['event_id'],e['settlement_date'],e['amount'],e['status'],e['flexibility'],e['linked_event_id']) for e in rows[-3:]])
        print('MESSAGES', json.dumps([m for m in read('messages') if m['user_id'] == user], ensure_ascii=False))
