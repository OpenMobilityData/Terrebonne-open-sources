#!/usr/bin/env python3
"""Tables for the note and the web page, from buildings_geo.csv: counts by side, by sheet,
by category; dwellings and construction years from the City's assessment roll where the
building was matched. Writes summary.json and summary.txt. Counts only, no names."""
import csv, json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')))
def in_lane(r): return 'outside the lane' not in r['cross_streets']
def residential(r):
    t = r['building_type'].lower(); return not any(k in t for k in ('institutional', 'vacant')) and r['garage_1954'] in ('yes', 'no')
front = [r for r in rows if r['addressed_on'] == 'Terrebonne' and residential(r) and in_lane(r)]
corner = [r for r in rows if r['addressed_on'] not in ('Terrebonne', '') and r['garage_1954'] != 'unknown' and in_lane(r)]
other = [r for r in rows if r['addressed_on'] == 'Terrebonne' and not residential(r) and r['garage_1954'] != 'unknown' and in_lane(r)]
def pct(a, b): return round(100 * a / b, 1) if b else None
S = {}
yes = [r for r in front if r['garage_1954'] == 'yes']
S['buildings_terrebonne'] = len(front); S['with_garage'] = len(yes); S['pct'] = pct(len(yes), len(front))
for side in 'NS':
    f = [r for r in front if r['side'] == side]; y = [r for r in f if r['garage_1954'] == 'yes']
    S[f'side_{side}'] = {'buildings': len(f), 'with_garage': len(y), 'pct': pct(len(y), len(f))}
hi = [r for r in front if r['confidence'] == 'high']; hy = [r for r in hi if r['garage_1954'] == 'yes']
S['high_confidence'] = {'buildings': len(hi), 'with_garage': len(hy), 'pct': pct(len(hy), len(hi))}
S['corner_cross_street'] = {'buildings': len(corner), 'with_garage': sum(r['garage_1954'] == 'yes' for r in corner)}
S['non_residential_or_vacant'] = len(other)
acc = collections.Counter()
for r in yes:
    a = r['garage_access_presumed'].lower()
    acc['Terrebonne' if a.startswith('terrebonne') and ' or ' not in a else ('lane' if 'lane' in a else ('either street (corner)' if ' or ' in a else 'cross street'))] += 1
S['garage_access'] = dict(acc)
kind = collections.Counter(('basement' if ('bt' in r['garage_kind'].lower() or 'bast' in r['garage_kind'].lower()) else 'detached' if 'detached' in r['garage_kind'] else 'attached or in an annex') for r in yes)
S['garage_kind'] = dict(kind)
# by sheet / block face
by = collections.OrderedDict()
for r in front:
    k = (r['side'], r['sheet'], r['cross_streets']); by.setdefault(k, [0, 0]); by[k][0] += 1; by[k][1] += r['garage_1954'] == 'yes'
S['by_sheet'] = [{'side': s, 'sheet': sh, 'extent': ext, 'buildings': n, 'with_garage': y, 'pct': pct(y, n)} for (s, sh, ext), (n, y) in by.items()]
# roll: dwellings and years
m = [r for r in front if r['match'].startswith('roll') and r['logements']]
dw = sum(int(r['logements']) for r in m); dwg = sum(int(r['logements']) for r in m if r['garage_1954'] == 'yes')
S['roll'] = {'buildings_matched': len(m), 'dwellings': dw, 'dwellings_in_buildings_with_garage': dwg, 'pct_dwellings': pct(dwg, dw)}
yrs = sorted(int(r['annee']) for r in front if r['annee'] and r['annee'].isdigit() and int(r['annee']) < 9999)
dec = collections.Counter(f'{y // 10 * 10}s' for y in yrs)
S['construction_years'] = {'n': len(yrs), 'min': yrs[0] if yrs else None, 'median': yrs[len(yrs) // 2] if yrs else None, 'max': yrs[-1] if yrs else None,
                           'by_decade': dict(sorted(dec.items())), 'after_1955': sum(y > 1955 for y in yrs)}
S['types'] = dict(collections.Counter(('apartment' if 'apartment' in r['building_type'] else 'duplex' if 'duplex' in r['building_type'] else 'single' if 'single' in r['building_type'] else 'semi' if 'semi' in r['building_type'] else 'row' if 'row' in r['building_type'] else 'other') for r in front))
json.dump(S, open(os.path.join(HERE, 'summary.json'), 'w'), indent=1, ensure_ascii=False)
with open(os.path.join(HERE, 'summary.txt'), 'w') as f:
    f.write(f"Residential buildings addressed on rue de Terrebonne, west end of the lane to Girouard, sheets available: {S['buildings_terrebonne']}\n")
    f.write(f"  with a garage as built (1954-55 plans): {S['with_garage']} = {S['pct']} %\n")
    for side in 'NS': f.write(f"  {side} side: {S[f'side_{side}']['with_garage']} of {S[f'side_{side}']['buildings']} = {S[f'side_{side}']['pct']} %\n")
    f.write(f"  high-confidence readings only: {S['high_confidence']['with_garage']} of {S['high_confidence']['buildings']} = {S['high_confidence']['pct']} %\n")
    f.write(f"Corner buildings on the Terrebonne block faces addressed on the cross street (not in the share): {S['corner_cross_street']['buildings']} ({S['corner_cross_street']['with_garage']} with a garage)\n")
    f.write(f"Churches, presbytery, vacant frontages: {S['non_residential_or_vacant']}\n")
    f.write(f"Garage access (presumed from the plan): {S['garage_access']}\nGarage kind: {S['garage_kind']}\n")
    f.write(f"Dwellings (City roll, {S['roll']['buildings_matched']} buildings matched): {S['roll']['dwellings']}, of which in buildings with a garage {S['roll']['dwellings_in_buildings_with_garage']} = {S['roll']['pct_dwellings']} %\n")
    f.write(f"Construction years (City roll): {S['construction_years']}\nBuilding types (plan): {S['types']}\n\nBy block face:\n")
    for b in S['by_sheet']: f.write(f"  {b['side']} {b['sheet']:7} {b['extent']:32} {b['with_garage']:3} / {b['buildings']:3}  {b['pct']} %\n")
print(open(os.path.join(HERE, 'summary.txt')).read())
