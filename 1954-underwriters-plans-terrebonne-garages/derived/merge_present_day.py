#!/usr/bin/env python3
"""Join the present-day reading (present_day_check.csv, read from the Québec government's
aerial imagery, one row per building keyed by sheet + civic_numbers) onto buildings_geo.csv:
adds driveway_today, vehicle_or_pad_on_lot, garage_door_visible, access_today, check_confidence,
check_notes. Rows not checked stay blank."""
import csv, os
HERE = os.path.dirname(os.path.abspath(__file__))
chk = {(r['sheet'], r['civic_numbers']): r for r in csv.DictReader(open(os.path.join(HERE, 'present_day_check.csv'), encoding='utf-8'))}
rows = list(csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')))
new = ['driveway_today', 'vehicle_or_pad_on_lot', 'garage_door_visible', 'access_today', 'check_confidence', 'check_notes']
n = 0
for r in rows:
    c = chk.get((r['sheet'], r['civic_numbers']))
    for k in new: r[k] = ''
    if c:
        r['driveway_today'] = c['driveway_today']; r['vehicle_or_pad_on_lot'] = c['vehicle_or_pad_on_lot']; r['garage_door_visible'] = c['garage_door_visible']
        r['access_today'] = c['access_today']; r['check_confidence'] = c['confidence']; r['check_notes'] = c['notes']; n += 1
fields = [k for k in rows[0].keys()]
w = csv.DictWriter(open(os.path.join(HERE, 'buildings_geo.csv'), 'w', encoding='utf-8'), fieldnames=fields); w.writeheader(); w.writerows(rows)
print('joined', n, 'checked rows onto', len(rows))
