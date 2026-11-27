#!/usr/bin/env python3
"""Tables of the press record from events.csv (protocol section 6): confirmed deaths by decade and age group, with the
groups the owner has still to rule on shown separately so that either choice can be read off. Counts only, no names.

  python3 build_tables.py  ->  tables.md, table_by_decade.csv
"""
import csv, collections, os, re
H = os.path.dirname(os.path.abspath(__file__))
ev = list(csv.DictReader(open(os.path.join(H, 'events.csv'), encoding='utf-8')))
pl = list(csv.DictReader(open(os.path.join(H, 'page_log.csv'), encoding='utf-8')))
def grp(x):
    g = x['age_group']
    return g if g in ('under 10', '10 to 14', '15 to 17', 'not given') else '14 or 15 (papers differ)'
# Amendment 8 (owner's rulings, Nov 26, 2026): a row with a value in listed_apart keeps its place in events.csv and is in
# no count of cyclists; the table shows such rows in a column of their own.
def apart(x): return (x.get('listed_apart') or '').strip()
decs = sorted({x['event_date'][:3] + '0s' for x in ev})
cols = ['under 10', '10 to 14', 'under 15, place not printed', 'under 15, listed apart', '15 to 17', '15 to 17, bridge', '14 or 15 (papers differ)', 'not given']
T = collections.defaultdict(collections.Counter)
for x in ev:
    d = x['event_date'][:3] + '0s'; g = grp(x); oi = x['on_island']
    if apart(x):
        assert g in ('under 10', '10 to 14'), 'a row listed apart outside the under-15 group: extend the table'
        T[d]['under 15, listed apart'] += 1
    elif g in ('under 10', '10 to 14'):
        T[d][g if oi == 'yes' else 'under 15, place not printed'] += 1
    elif g == '15 to 17': T[d]['15 to 17' if oi == 'yes' else ('15 to 17, bridge' if oi == 'bridge' else '15 to 17')] += 1
    else: T[d][g] += 1
tot = collections.Counter()
rows = []
for d in decs:
    r = [d] + [T[d][c] for c in cols]; rows.append(r)
    for c in cols: tot[c] += T[d][c]
with open(os.path.join(H, 'table_by_decade.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['decade'] + cols); w.writerows(rows); w.writerow(['all'] + [tot[c] for c in cols])
u15 = [x for x in ev if grp(x) in ('under 10', '10 to 14') and x['on_island'] == 'yes' and not apart(x)]
AP = collections.Counter(apart(x) for x in ev if apart(x))
ap_txt = ', '.join(f'{v} ({k})' for k, v in AP.most_common()) or 'none'
veh = collections.Counter(x['other_party_class'] for x in u15)
ROAD = ('truck or other heavy motor vehicle', 'car', 'taxi', 'bus or trolleybus', 'horse-drawn vehicle', 'car and horse-drawn vehicle', 'vehicle, kind not stated')
def split(c):
    road = sum(c[k] for k in ROAD); rest = [(k, v) for k, v in c.most_common() if k not in ROAD]
    return f"{road} with a road vehicle ({', '.join(f'{c[k]} {k}' for k in ROAD if c[k])})" + ''.join(f'; {v} {k}' for k, v in rest)
# Amendment 7 (owner, Nov 26, 2026): where the municipality is not printed it is inferred from the street names and the
# paper's scope; the printed placement stays in on_island, the inferred one in on_island_inferred with its basis.
unc = [x for x in ev if grp(x) in ('under 10', '10 to 14') and x['on_island'] == 'unclear' and not apart(x)]
inf_yes = [x for x in unc if x['on_island_inferred'] == 'yes']; inf_no = [x for x in unc if x['on_island_inferred'] == 'no']
assert len(inf_yes) + len(inf_no) == len(unc), 'a row with the place not printed has no inferred placement'
u15i = u15 + inf_yes; veh_i = collections.Counter(x['other_party_class'] for x in u15i)
ID = collections.defaultdict(collections.Counter)
for x in u15: ID[x['event_date'][:3] + '0s']['p'] += 1
for x in inf_yes: ID[x['event_date'][:3] + '0s']['y'] += 1
for x in inf_no: ID[x['event_date'][:3] + '0s']['n'] += 1
res = collections.Counter()
for x in pl:
    c, k, i = x['cyclist'], x['killed'], x['on_island']
    res['cyclist killed, collision on the island' if (c, k, i) == ('yes', 'yes', 'yes') else
        'cyclist killed, off the island' if (c, k, i) == ('yes', 'yes', 'no') else
        'cyclist killed, place unclear or a bridge' if (c, k) == ('yes', 'yes') else
        'cyclist not killed (injured, or outcome not stated)' if c == 'yes' else
        'not a cyclist' if c == 'no' else 'mode not stated'] += 1
L = ['# Tables of the press record (built by build_tables.py from events.csv and page_log.csv)', '',
     'A record of what the digitized newspapers reported, not a census. The collection thins sharply after the 1960s: the later decades are a floor.', '',
     '## Confirmed deaths by decade of the event and age group', '',
     '| Decade | ' + ' | '.join(cols) + ' |', '|---|' + '---:|' * len(cols)]
for r in rows: L.append('| ' + r[0] + ' | ' + ' | '.join(str(v) if v else '' for v in r[1:]) + ' |')
L += ['| **All** | ' + ' | '.join(f'**{tot[c]}**' for c in cols) + ' |', '',
      f"Under 15 with the collision on the island: **{len(u15)}** ({tot['under 10']} under 10, {tot['10 to 14']} aged 10 to 14): {split(veh)}. "
      f"Listed apart by the owner's rulings (protocol amendment 8) and in no count: {ap_txt}. Horse-drawn vehicles are counted only where the page says so; "
      "in the 1910s and 1920s « camion » was also used of a horse-drawn dray, so their number is a minimum. "
      f"For {sum(1 for x in u15 if (x.get('note') or '').lower().startswith('pushing a bicycle'))} of these deaths (March 28, 1967) the reports differ on whether he was riding or walking beside his bicycle; kept in the count (amendment 8e).", '',
      '## Under 15, with the municipality inferred where it is not printed (protocol amendment 7)', '',
      f"Of the {len(unc)} deaths under 15 whose item does not print where the collision took place, {len(inf_yes)} are placed on the island and {len(inf_no)} off it, "
      "from the street names, the hospital and the home towns printed; the basis of each is in `events.csv`, column `inference_basis`. Both counts are kept.", '',
      '| Decade | Place printed or streets named | Inferred on the island | Both | Inferred off the island |', '|---|---:|---:|---:|---:|'] + [
      f"| {d} | {ID[d]['p'] or ''} | {ID[d]['y'] or ''} | {(ID[d]['p'] + ID[d]['y']) or ''} | {ID[d]['n'] or ''} |" for d in decs if ID[d]] + [
      f"| **All** | **{len(u15)}** | **{len(inf_yes)}** | **{len(u15i)}** | **{len(inf_no)}** |", '',
      f"With the inferred rows: **{len(u15i)}** under 15 on the island: {split(veh_i)}.", '',
      '## The other party, deaths under 15 with the collision on the island (column `other_party_class` of `events.csv`, assigned from what the page prints)', '',
      '| Other party | As printed | With the inferred rows |', '|---|---:|---:|'] + [f'| {k} | {veh[k] or ""} | {v} |' for k, v in veh_i.most_common()] + [f'| **All** | **{len(u15)}** | **{len(u15i)}** |', '',
      f'## What the {len({x["banq_id"] for x in pl})} issues opened showed ({len(pl)} rows: an issue can hold two events)', '',
      '| Result on the page | Rows |', '|---|---:|'] + [f'| {k} | {v} |' for k, v in res.most_common()] + ['']
open(os.path.join(H, 'tables.md'), 'w', encoding='utf-8').write('\n'.join(L))
print(len(ev), 'events;', len(u15), 'under 15 on the island as printed;', len(u15i), 'with the inferred rows'); print(dict(veh_i)); print(dict(res))
