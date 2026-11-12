#!/usr/bin/env python3
"""The owner's street-level check of the buildings addressed on rue de Terrebonne (Nov 12, 2026) against the aerial
reading of October 25, 2026, row by row, and the figures that replace the « 89 of 123, 72 % ».

Inputs: owner_street_check.json (the owner's export, 154 lots, as exported), ../street_check_frame.csv (lot -> 1954 rows),
        ../buildings_geo.csv (1954 reading + the October 25 reading).
Outputs: comparison.csv (one row per 1954 building of the like-for-like frame), lots.csv (one row per lot, the
         owner's answer), summary.json, summary.txt.   Run: python3 compare.py
Conventions (owner, Nov 12, 2026): car access « yes » = at least one private place usable today; a lot whose parking
was converted to another use with none left = access no + converted « yes, none left »; « yes, some left » = partial.
Rulings (owner, Nov 12, 2026): 6324 (a 1954 house whose position now falls inside the school lot at 6440, no dwelling)
is dropped from the like-for-like frame (122); where the 1954-55 plans show a garage, they take priority over the
street check for conversions (« I can't see all potential parking conversions »): a 1954 garage with no parking today
is a conversion with none left; a 1954 garage, access today but no garage today, a conversion with some left. The
owner's answers are kept as given (converted_owner); the coding is in converted / converted_basis.
"""
import csv, json, os, collections
H = os.path.dirname(os.path.abspath(__file__)); P = os.path.dirname(H)
ans = {a['key']: a for a in json.load(open(os.path.join(H, 'owner_street_check.json')))['answers']}
frame = list(csv.DictReader(open(os.path.join(P, 'street_check_frame.csv'), encoding='utf-8')))
geo = list(csv.DictReader(open(os.path.join(P, 'buildings_geo.csv'), encoding='utf-8')))
def pct(a, b): return round(100 * a / b, 1) if b else None
def residential(r):
    t = r['building_type'].lower(); return not any(k in t for k in ('institutional', 'vacant')) and r['garage_1954'] in ('yes', 'no')
front = [r for r in geo if r['addressed_on'] == 'Terrebonne' and residential(r) and 'outside the lane' not in r['cross_streets']]
old = [r for r in front if r.get('driveway_today') in ('yes', 'no', 'unclear')]          # the 123 of October 25
r2k = {}
for f in frame:
    for m in filter(None, (x.strip() for x in f['rows_1954'].split(';'))):
        r2k[m] = f['key']
def a_of(key):
    a = ans.get(key, {}); acc = a.get('car_access', '') or 'not answered'
    kind = a.get('kind', '')
    if kind == 'converted to other use' and acc == 'yes':        # convention: Kind = what remains when some is left
        kind = 'converted, some left (kind not given)'
    return acc, kind, a.get('converted', ''), a.get('places_independent', ''), a.get('places_total', ''), a.get('garage', ''), a.get('basis', ''), a.get('note', '')
def coded(conv, acc, gar_today, g1954):
    if conv.startswith('yes'):
        return conv, 'street check'
    if g1954 and acc == 'no':
        return 'yes, none left', '1954-55 plans: garage as built; no parking today'
    if g1954 and acc == 'yes' and gar_today == 'no':
        return 'yes, some left', '1954-55 plans: garage as built; access today, no garage today'
    return conv, 'street check' if conv else ''
excluded = [r for r in old if not r2k.get(f"{r['sheet']} {r['side']} {r['civic_numbers']}")]
old = [r for r in old if r not in excluded]
rows = []
for r in old:
    k = r2k.get(f"{r['sheet']} {r['side']} {r['civic_numbers']}")
    acc, kind, conv, pi, pt, gar, basis, note = a_of(k) if k else ('no lot today', '', '', '', '', '', '', '')
    cf, cb = coded(conv, acc, gar, r['garage_1954'] == 'yes')
    rows.append({'sheet': r['sheet'], 'side': r['side'], 'civic_numbers': r['civic_numbers'], 'cross_streets': r['cross_streets'], 'logements': r['logements'],
                 'garage_1954': r['garage_1954'], 'driveway_oct25': r['driveway_today'], 'key': k or '', 'access_street_check': acc, 'kind': kind,
                 'converted_owner': conv, 'converted': cf, 'converted_basis': cb, 'places_independent': pi, 'places_total': pt, 'garage_today': gar, 'basis': basis, 'note': note})
with open(os.path.join(H, 'comparison.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
g1954 = {f"{r['sheet']} {r['side']} {r['civic_numbers']}": r['garage_1954'] == 'yes' for r in geo}
lots = []
for f in frame:
    acc, kind, conv, pi, pt, gar, basis, note = a_of(f['key'])
    g = any(g1954.get(m.strip(), False) for m in f['rows_1954'].split(';') if m.strip())
    cf, cb = coded(conv, acc, gar, g)
    lots.append({**{k: f[k] for k in ('n', 'key', 'civic_lo', 'civic_hi', 'roll_street', 'side', 'dwellings', 'large', 'year_built', 'rows_1954')},
                 'garage_1954_any': 'yes' if g else ('no' if f['rows_1954'] else 'not in the 1954 table'),
                 'access': acc, 'kind': kind, 'converted_owner': conv, 'converted': cf, 'converted_basis': cb, 'places_independent': pi, 'places_total': pt, 'garage_today': gar, 'basis': basis, 'note': note})
with open(os.path.join(H, 'lots.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(lots[0])); w.writeheader(); w.writerows(lots)

S = {}
# like for like: the October 25 frame
dec = [r for r in rows if r['access_street_check'] in ('yes', 'no')]
S['like_for_like'] = {
    'oct25_frame_read': len(rows) + len(excluded), 'excluded_no_dwelling_today': [f"{r['civic_numbers']} {r['side']}" for r in excluded],
    'oct25_frame': len(rows), 'decided': len(dec),
    'undecided': dict(collections.Counter(r['access_street_check'] for r in rows if r['access_street_check'] not in ('yes', 'no'))),
    'oct25_driveway_yes': sum(r['driveway_oct25'] == 'yes' for r in rows),
    'oct25_either': sum(r['driveway_oct25'] == 'yes' or r['garage_1954'] == 'yes' for r in rows),
    'access_yes': sum(r['access_street_check'] == 'yes' for r in dec),
    'either_garage1954_or_access': sum(r['access_street_check'] == 'yes' or r['garage_1954'] == 'yes' for r in dec),
    'converted_none_left': sum(r['converted'] == 'yes, none left' for r in dec),
    'converted_some_left': sum(r['converted'] == 'yes, some left' for r in dec),
    'garage1954_and_converted_none_left': sum(r['garage_1954'] == 'yes' and r['converted'] == 'yes, none left' for r in dec),
    'converted_by_basis': dict(collections.Counter(f"{r['converted']} | {r['converted_basis']}" for r in dec if r['converted'].startswith('yes'))),
    'crosstab_oct25_vs_street': {f"{a} -> {b}": n for (a, b), n in sorted(collections.Counter((r['driveway_oct25'], r['access_street_check']) for r in rows).items())},
    'dwellings_decided': sum(int(r['logements'] or 0) for r in dec), 'dwellings_access': sum(int(r['logements'] or 0) for r in dec if r['access_street_check'] == 'yes'),
}
L = S['like_for_like']; L['pct_access'] = pct(L['access_yes'], L['decided']); L['pct_either'] = pct(L['either_garage1954_or_access'], L['decided'])
L['pct_oct25_driveway'] = pct(L['oct25_driveway_yes'], L['oct25_frame']); L['pct_oct25_either'] = pct(L['oct25_either'], L['oct25_frame'])
L['pct_dwellings_access'] = pct(L['dwellings_access'], L['dwellings_decided'])
# the whole street: every lot
dl = [l for l in lots if l['access'] in ('yes', 'no')]; small = [l for l in dl if l['large'] != 'True']
def num(x): return int(x) if str(x).strip().isdigit() else 0
S['whole_street'] = {
    'lots': len(lots), 'decided': len(dl), 'undecided': dict(collections.Counter(l['access'] for l in lots if l['access'] not in ('yes', 'no'))),
    'access_yes': sum(l['access'] == 'yes' for l in dl), 'pct_access': pct(sum(l['access'] == 'yes' for l in dl), len(dl)),
    'converted_none_left': sum(l['converted'] == 'yes, none left' for l in dl), 'converted_some_left': sum(l['converted'] == 'yes, some left' for l in dl),
    'converted_cannot_tell': sum(l['converted'] == 'cannot tell' for l in dl),
    'converted_by_basis': dict(collections.Counter(f"{l['converted']} | {l['converted_basis']}" for l in dl if l['converted'].startswith('yes'))),
    'converted_dwellings_none_left': sum(int(float(l['dwellings'])) for l in dl if l['converted'] == 'yes, none left'),
    'kind': dict(collections.Counter(l['kind'] for l in dl)),
    'small_decided': len(small), 'small_access': sum(l['access'] == 'yes' for l in small),
    'small_places_independent': sum(num(l['places_independent']) for l in small), 'small_places_total': sum(num(l['places_total']) for l in small),
    'small_dwellings': sum(int(float(l['dwellings'])) for l in small),
    'large_lots': sum(l['large'] == 'True' for l in lots), 'large_with_underground_garage': sum(l['large'] == 'True' and l['kind'] == 'parking lot' for l in lots),
    'small_places_missing_count': sum(1 for l in small if l['access'] == 'yes' and not str(l['places_independent']).strip()),
}
W = S['whole_street']; W['pct_small_access'] = pct(W['small_access'], W['small_decided'])
json.dump(S, open(os.path.join(H, 'summary.json'), 'w'), indent=1, ensure_ascii=False)
with open(os.path.join(H, 'summary.txt'), 'w', encoding='utf-8') as f:
    f.write(json.dumps(S, indent=1, ensure_ascii=False) + '\n')
print(json.dumps(S, indent=1, ensure_ascii=False))
print('OK compare')
