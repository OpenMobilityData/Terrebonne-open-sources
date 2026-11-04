#!/usr/bin/env python3
"""Allocation of the petition entries that carry only a three-character postal-code prefix (owner, Nov 4, 2026).

A signer is placed on the map only with a full six-character code. The 2024 petitions (release 2025-081) lose 228 of 1,203 lines
at that step, mostly change.org entries typed with the prefix alone; the 2026 petition loses 25 of 1,490. Here every entry with a
usable prefix (A1A, incl. full codes absent from the postal-code table) is allocated across the full codes of the SAME petition and
SAME source (2024: handwritten sheets vs the online printout; 2026: pooled, 11 entries only) within that prefix area, in proportion
to the located signers at each code. The allocation yields expected values, not counts: expected signers in the borough and in the
one-block corridor (on Terrebonne or within one block, Somerled–Monkland, the géobase rule of petition_corridor.py, applied here to
BOTH petitions). A prefix area with no located reference of that source falls back to the whole petition's located signers in the
area; with none at all, to every postal code of the area counted once (a geographic share; these areas lie outside the borough). Entries with no code or a mis-written one stay unplaced.

Inputs: the 2024 lists (~/Terrebonne-data/petition/Petition_Codes_Checked.csv, working-2025-03/ChangeOrg.csv), the 2026 merged
table (~/Terrebonne-data/petition-2026/merged_interim.csv, repeats removed by the signer key), the Service Objects points, the
City districts and géobase. Outputs (public, Terrebonne-open-sources/2026-11-02-petitions-comparison/derived/):
petition_prefix_allocation_2026-11-02.csv (per petition, source, prefix) and .json (summary). Run: python3 scripts/petition_prefix_allocation.py
"""
import csv, json, os, re, sys, collections, unicodedata
HERE = os.path.dirname(os.path.abspath(__file__)); PRV = os.path.dirname(HERE); sys.path.insert(0, HERE)
import petition_corridor as pc
from matplotlib.path import Path as MPath
HOME = os.path.expanduser('~'); D24 = os.path.join(HOME, 'Terrebonne-data/petition'); D26 = os.path.join(HOME, 'Terrebonne-data/petition-2026')
OUT = os.path.join(HOME, 'GitHub/Terrebonne-open-sources/2026-11-02-petitions-comparison/derived')
DIST = os.path.join(PRV, 'data/districts/districts-electoraux-2025.json')
raw = lambda s: re.sub(r'[^A-Z0-9]', '', (s or '').upper())
def kind(c):
    if re.fullmatch(r'[A-Z]\d[A-Z]\d[A-Z]\d', c): return 'full'
    if re.match(r'^[A-Z]\d[A-Z]', c): return 'prefix'
    return 'none'

# --- 2024 entries by source ---
hand = [raw(r['PostalCode']) for r in csv.DictReader(open(os.path.join(D24, 'Petition_Codes_Checked.csv'), encoding='utf-8-sig'))]
web = [raw(r.get('Postal_Code')) for r in csv.DictReader([l for l in open(os.path.join(D24, 'working-2025-03/ChangeOrg.csv'), encoding='utf-8-sig') if not l.startswith('```')])]
# --- 2026 entries (repeats removed; the inferred code counts as the signer's placement) ---
def skey(r):
    f = lambda s: re.sub(r'\s+', '', ''.join(c for c in unicodedata.normalize('NFD', (s or '')) if unicodedata.category(c) != 'Mn')).lower()
    e, n = f(r.get('Email')), f(r.get('First Name')) + f(r.get('Last Name'))
    return (e + '|' + n) if (e or n) else None
seen = set(); e26 = []
for r in csv.DictReader(open(os.path.join(D26, 'merged_interim.csv'), encoding='utf-8-sig')):
    k = skey(r)
    if k and k in seen: continue
    if k: seen.add(k)
    e26.append(raw(r.get('ZIP Code')) if kind(raw(r.get('ZIP Code'))) == 'full' else (raw(r.get('ZIP Inferred')) or raw(r.get('ZIP Code'))))
sets = {('2024', 'handwritten'): hand, ('2024', 'online'): web, ('2026', 'all'): e26}

# --- positions, borough membership and the one-block corridor for every full code seen ---
want = {c for lst in sets.values() for c in lst if kind(c) == 'full'}
pref_all = {c[:3] for lst in sets.values() for c in lst if kind(c) in ('full', 'prefix')}
pos = {}; area_codes = collections.defaultdict(list)   # every code of each prefix area seen, for the geographic fallback
for r in csv.DictReader(open(pc.POSTAL, encoding='utf-8', errors='replace')):
    c = r['PostalCode'].replace(' ', '').upper()
    if c[:3] in pref_all:
        try: pos[c] = (float(r['Longitude']), float(r['Latitude']))
        except ValueError: continue
        area_codes[c[:3]].append(c)
feats = json.load(open(DIST))['features']
cdn = [f for f in feats if f['properties']['NOM_ARR'] == 'Côte-des-Neiges–Notre-Dame-de-Grâce']
def paths(f):
    g = f['geometry']; pp = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    return [MPath([tuple(c[:2]) for c in poly[0]]) for poly in pp]
cdn_paths = [p for f in cdn for p in paths(f)]
in_borough = lambda c: any(p.contains_point(pos[c]) for p in cdn_paths)
geo = json.load(open(pc.GEOBASE))['features']; lane = pc._lines(json.load(open(pc.LANE))['features']); par = {n: pc._lines(geo, n) for n in pc.SPACING}
def in_corridor(c):
    p = pos[c]; dT = pc._dist(p, lane)
    if dT > 600: return False
    dX = {k: pc._dist(p, s) for k, s in par.items()}
    on_par = min(dX.values()) <= 25
    between = any(dT + dX[k] <= pc.SPACING[k] + 35 and dX[k] > 25 for k in pc.SPACING)
    along = min(dT + dX[k] - pc.SPACING[k] for k in pc.SPACING) <= 60
    return (between and not on_par) or (on_par and along)
flag = {c: (in_borough(c), in_corridor(c)) for c in pos}

# --- allocation ---
rows = []; summary = {}
located_by_pet = collections.defaultdict(collections.Counter)
for (pet, src), lst in sets.items():
    for c in lst:
        if kind(c) == 'full' and c in pos: located_by_pet[pet][c] += 1
for (pet, src), lst in sets.items():
    located = collections.Counter(); pref = collections.Counter(); none = 0
    for c in lst:
        k = kind(c)
        if k == 'full' and c in pos: located[c] += 1
        elif k in ('full', 'prefix'): pref[c[:3]] += 1
        else: none += 1
    alloc_b = alloc_c = 0.0; no_ref = 0
    for fsa, n in sorted(pref.items()):
        ref = {c: v for c, v in located.items() if c.startswith(fsa)}; basis = 'same source'
        if not ref: ref = {c: v for c, v in located_by_pet[pet].items() if c.startswith(fsa)}; basis = 'whole petition'
        if not ref: ref = {c: 1 for c in area_codes.get(fsa, [])}; basis = 'all postal codes of the area'; no_ref += n
        tot = sum(ref.values())
        if not tot: rows.append([pet, src, fsa, n, 0, '', '', '', 0, 0, 'prefix area unknown']); continue
        sb = sum(v for c, v in ref.items() if flag[c][0]) / tot; sc = sum(v for c, v in ref.items() if flag[c][1]) / tot
        rows.append([pet, src, fsa, n, tot, basis, f'{sb:.3f}', f'{sc:.3f}', f'{n * sb:.1f}', f'{n * sc:.1f}', '']); alloc_b += n * sb; alloc_c += n * sc
    lb = sum(v for c, v in located.items() if flag[c][0]); lc = sum(v for c, v in located.items() if flag[c][1])
    summary[f'{pet} {src}'] = dict(entries=len(lst), located=sum(located.values()), prefix_only=sum(pref.values()), unusable=none, no_reference=no_ref,
                                   located_in_borough=lb, located_in_corridor_one_block_rule=lc, allocated_in_borough=round(alloc_b, 1), allocated_in_corridor=round(alloc_c, 1))
for pet in ('2024', '2026'):
    parts = [v for k, v in summary.items() if k.startswith(pet)]
    summary[pet] = {k: round(sum(p[k] for p in parts), 1) for k in parts[0]}
    summary[pet]['expected_in_borough'] = round(summary[pet]['located_in_borough'] + summary[pet]['allocated_in_borough']); summary[pet]['expected_in_corridor'] = round(summary[pet]['located_in_corridor_one_block_rule'] + summary[pet]['allocated_in_corridor'])
os.makedirs(OUT, exist_ok=True)
with open(os.path.join(OUT, 'petition_prefix_allocation_2026-11-02.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['petition', 'source', 'prefix', 'prefix_only_entries', 'located_reference_entries', 'reference_basis', 'share_in_borough', 'share_in_corridor', 'allocated_in_borough', 'allocated_in_corridor', 'note']); w.writerows(rows)
json.dump(summary, open(os.path.join(OUT, 'petition_prefix_allocation_2026-11-02.json'), 'w'), indent=1)
print(json.dumps({k: summary[k] for k in ('2024', '2026')}, indent=1))
