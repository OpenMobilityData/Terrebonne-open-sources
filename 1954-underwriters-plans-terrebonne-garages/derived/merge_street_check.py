#!/usr/bin/env python3
"""Join the street-level check of November 12, 2026 (street_check/comparison.csv, one row per building of the
October 25 frame, keyed by sheet + side + civic_numbers) onto buildings_geo.csv: adds access_street_check
(yes / no / cannot tell / no dwelling today), converted_street_check (no / yes, none left / yes, some left /
cannot tell; the 1954-55 plans taking priority, owner's ruling) and converted_basis. The October 25 columns are
kept as they were (the record of that reading). Rows outside that frame stay blank."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
cmp_ = {(r['sheet'], r['side'], r['civic_numbers']): r for r in csv.DictReader(open(os.path.join(HERE, 'street_check', 'comparison.csv'), encoding='utf-8'))}
rows = list(csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')))
new = ['access_street_check', 'converted_street_check', 'converted_basis']
n = 0
for r in rows:
    for k in new: r[k] = ''
    c = cmp_.get((r['sheet'], r['side'], r['civic_numbers']))
    if c:
        r['access_street_check'] = c['access_street_check']; r['converted_street_check'] = c['converted']; r['converted_basis'] = c['converted_basis']; n += 1
    elif r['addressed_on'] == 'Terrebonne' and r.get('driveway_today') in ('yes', 'no', 'unclear'):
        r['access_street_check'] = 'no dwelling today'; n += 1      # 6324: now inside the school lot at 6440 (owner's ruling: dropped)
fields = list(rows[0].keys())
with open(os.path.join(HERE, 'buildings_geo.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
print('joined', n, 'rows of the street check onto', len(rows))
print('OK merge_street_check')
