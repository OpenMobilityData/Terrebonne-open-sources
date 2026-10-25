#!/usr/bin/env python3
"""Join the 1954-55 reading (buildings_1954.csv) to the City's assessment-roll polygons
(unités d'évaluation foncière, CC-BY 4.0) by civic number and street, to place each building
on the map and read its dwelling count and construction year; writes buildings_geo.csv.
Unmatched rows are placed schematically along their block face (method = 'schematic')."""
import csv, json, os, re, unicodedata, math
from frame import to_EN, to_uv, from_uv, from_EN, STREET_U
HERE = os.path.dirname(os.path.abspath(__file__))
UEV = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/unites-evaluation-fonciere/terrebonne_bbox_extract.geojson')
def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()
def centroid(geom):
    """area-weighted centroid of the outer rings, computed in coordinates relative to the first vertex
    (the shoelace formula in raw longitude/latitude loses precision on lots a few metres across)"""
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    x0, y0 = polys[0][0][0][0], polys[0][0][0][1]
    A = Cx = Cy = 0.0
    for poly in polys:
        ring = [(p[0] - x0, p[1] - y0) for p in poly[0]]
        for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
            c = ax * by - bx * ay; A += c; Cx += (ax + bx) * c; Cy += (ay + by) * c
    if abs(A) < 1e-18:
        pts = [p for poly in polys for p in poly[0]]; return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    return x0 + Cx / (3 * A), y0 + Cy / (3 * A)
units = []
for f in json.load(open(UEV))['features']:
    p = f['properties']
    try: a, b = int(p['CIVIQUE_DEBUT']), int(p['CIVIQUE_FIN'])
    except Exception: continue
    lon, lat = centroid(f['geometry'])
    units.append({'street': norm(p['NOM_RUE']).replace(' mtl', '').strip(), 'a': min(a, b), 'b': max(a, b), 'lon': lon, 'lat': lat,
                  'logements': p.get('NOMBRE_LOGEMENT'), 'annee': p.get('ANNEE_CONSTRUCTION'), 'cat': p.get('CATEGORIE_UEF'), 'id': p['ID_UEV'],
                  'usage': p.get('LIBELLE_UTILISATION'), 'etages': p.get('ETAGE_HORS_SOL')})
STREETS = {'terrebonne': 'terrebonne', 'belmore': 'belmore', 'coronation': 'coronation', 'mayfair': 'mayfair', 'mariette': 'mariette', 'rosedale': 'rosedale',
           'king edward': 'king edward', 'montclair': 'montclair', 'walkley': 'walkley', 'prince of wales': 'prince of wales', 'cumberland': 'cumberland',
           'cavendish': 'cavendish', 'bessborough': 'bessborough', 'benny': 'benny', 'madison': 'madison', 'kensington': 'kensington', 'grand': 'grand',
           'beaconsfield': 'beaconsfield', 'hingston': 'hingston', 'hampton': 'hampton', 'royal': 'royal', 'draper': 'draper', 'melrose': 'melrose',
           'wilson': 'wilson', 'harvard': 'harvard', 'oxford': 'oxford', 'marcil': 'marcil', 'old orchard': 'old orchard', 'girouard': 'girouard'}
def find(street, lo, hi, side=None):
    """roll units on `street` overlapping [lo, hi]; on Terrebonne the north side has the odd numbers and the
    south side the even ones, so a row's side fixes the parity; every candidate must also lie on the row's side"""
    key = STREETS.get(street)
    if not key: return []
    out = [u for u in units if key in u['street'] and not (u['b'] < lo or u['a'] > hi)]
    if side:
        if key == 'terrebonne': out = [u for u in out if (u['a'] % 2 == 1) == (side == 'N')]
        out = [u for u in out if (UV[u['id']][1] > 0) == (side == 'N')]
    return out
UV = {}
for u in units:
    E, N = to_EN(u['lon'], u['lat']); UV[u['id']] = to_uv(E, N)
def street_u_name(name):
    name = norm(name)
    for k, uu in STREET_U.items():
        if name and name in norm(k): return uu
    return None
def corner_match(r, nums):
    """a building at a corner, numbered on Terrebonne in 1954 but on the cross street in the roll (or the reverse):
    the roll unit on the corner street, on the right side of Terrebonne and of the corner street, nearest Terrebonne"""
    m = re.match(r'yes \((.+)\)', r['corner_lot'] or '')
    cs = [c.strip() for c in r['cross_streets'].split('-')]
    if m: cands_streets = [m.group(1)]
    elif r['addressed_on'] not in ('Terrebonne', '') and r['addressed_on'] != 'cross street': cands_streets = [r['addressed_on']]
    else: cands_streets = cs
    side = 1 if r['side'] == 'N' else -1
    best = None
    for name in cands_streets:
        us = street_u_name(name); key = STREETS.get(norm(name))
        if us is None or not key: continue
        east = (norm(name) == norm(cs[0].split(' (')[0]))  # corner street is the block's west street -> building east of it
        for u in units:
            if key not in u['street']: continue
            uu, vv = UV[u['id']]
            if vv * side <= 0 or abs(vv) > 32: continue
            if nums and not (u['b'] < min(nums) or u['a'] > max(nums)): return u
            if len(cands_streets) == 1 and abs(uu - us) < 30 and ((uu - us > 0) == east or abs(uu - us) < 8):
                if best is None or abs(vv) < abs(UV[best['id']][1]): best = u
    return best
rows = list(csv.DictReader(open(os.path.join(HERE, 'buildings_1954.csv'), encoding='utf-8')))
out = []; unmatched = []
for r in rows:
    civ = r['civic_numbers']; nums = [int(n) for n in re.findall(r'\b(\d{4})\b', civ)]
    m = re.search(r'\d{4}\s*(?:-\d{4})?\s*([A-Za-z][A-Za-z ]+?)(?:\s*\(|,|$)', civ)
    street = norm(m.group(1)) if m and norm(m.group(1)) not in ('corner', 'small') else None
    if r['addressed_on'] != 'Terrebonne' and not street: street = norm(r['addressed_on'])
    if not street: street = 'terrebonne'
    cands = find(street, min(nums), max(nums), r['side']) if nums else []
    half = re.search(r'\((a|b)\)', civ)
    rec = dict(r); rec.update({'match': '', 'uev_id': '', 'lon': '', 'lat': '', 'u_m': '', 'v_m': '', 'logements': '', 'annee': '', 'usage': ''})
    if street == 'terrebonne' and 'outside the lane' in r['cross_streets']: cands = find('terrebonne', min(nums), max(nums), r['side'])
    if cands:
        cands.sort(key=lambda u: -u['b'])
        if half: pick = [cands[0] if half.group(1) == 'a' else cands[-1]]
        else: pick = cands
        # condominium units share a civic: aggregate
        lon = sum(u['lon'] for u in pick) / len(pick); lat = sum(u['lat'] for u in pick) / len(pick)
        logs = sum((u['logements'] or 0) for u in pick); annee = min((u['annee'] for u in pick if u['annee']), default='')
        E, N = to_EN(lon, lat); u_, v_ = to_uv(E, N)
        rec.update({'match': 'roll', 'uev_id': ';'.join(u['id'] for u in pick), 'lon': f'{lon:.6f}', 'lat': f'{lat:.6f}', 'u_m': f'{u_:.1f}', 'v_m': f'{v_:.1f}',
                    'logements': int(logs) if logs else '', 'annee': annee, 'usage': pick[0]['usage']})
    else:
        pick = corner_match(r, nums)
        if pick:
            u0 = pick; E, N = to_EN(u0['lon'], u0['lat']); u_, v_ = to_uv(E, N)
            rec.update({'match': 'roll (corner, by position)', 'uev_id': u0['id'], 'lon': f"{u0['lon']:.6f}", 'lat': f"{u0['lat']:.6f}", 'u_m': f'{u_:.1f}', 'v_m': f'{v_:.1f}',
                        'logements': int(u0['logements'] or 0) or '', 'annee': u0['annee'] or '', 'usage': u0['usage']})
        else:
            unmatched.append((r['sheet'], civ, street)); rec['match'] = 'schematic'
    out.append(rec)
# schematic placement for unmatched rows: evenly along the block face between its cross streets
from collections import defaultdict
groups = defaultdict(list)
for rec in out:
    if rec['match'] == 'schematic': groups[(rec['sheet'], rec['side'], rec['block'])].append(rec)
def street_u(name):
    name = name.strip().split(' (')[0]
    for k, u in STREET_U.items():
        if norm(name) and norm(name) in norm(k): return u
    return None
for (sh, side, blk), recs in groups.items():
    cs = recs[0]['cross_streets'].split('-'); ua = street_u(cs[0]) if cs else None; ub = street_u(cs[-1]) if len(cs) > 1 else None
    if ua is None and ub is None: ua, ub = 0, 80
    if ua is None: ua = ub - 80
    if ub is None: ub = ua + 80
    # order: numbers decrease eastward on Terrebonne
    recs.sort(key=lambda r: -max([int(n) for n in re.findall(r'\d{4}', r['civic_numbers'])] or [0]))
    n = len(recs)
    for i, rec in enumerate(recs):
        u_ = ua + (ub - ua) * (i + 1) / (n + 1); v_ = 16 if side == 'N' else -16
        E, N = from_uv(u_, v_); lon, lat = from_EN(E, N)
        rec.update({'lon': f'{lon:.6f}', 'lat': f'{lat:.6f}', 'u_m': f'{u_:.1f}', 'v_m': f'{v_:.1f}'})
w = csv.DictWriter(open(os.path.join(HERE, 'buildings_geo.csv'), 'w', encoding='utf-8'), fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print('rows', len(out), 'matched to the roll', sum(r['match'] == 'roll' for r in out), 'schematic', len(unmatched))
for x in unmatched: print('  unmatched', x)
