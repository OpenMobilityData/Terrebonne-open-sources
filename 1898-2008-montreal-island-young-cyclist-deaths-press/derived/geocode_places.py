#!/opt/local/bin/python3.13
"""Place of each death under 15 on the island (events.csv), put on TODAY's street file for the map.

The place printed by the newspaper is matched by hand to today's street names (table PLACES below: one line per event,
with the old name and today's where they differ), then located by program on the City's street file (géobase, file of
October 14, 2026, in ~/Terrebonne-data/third-party/montreal-opendata/). Only the place of the collision is located,
never a home address (two exceptions, marked: an item that prints only the address in front of which it happened).

Precision classes, published with each point:
  intersection   two streets named, the point is their crossing
  block          a civic number, « between » two cross streets, or « near » a cross street: within about a block
  street         only a street (or a street and a municipality) is known: the point is the middle of that street's
                 segments in the municipality named, and is drawn differently on the map
  none           no place printed: not on the map

  /opt/local/bin/python3.13 geocode_places.py  ->  places_geocoded.csv (one row per event; no names)
"""
import csv, json, os, re, sys, unicodedata, collections
from shapely.geometry import shape, Point
from shapely.ops import unary_union, nearest_points, linemerge
import pyproj
H = os.path.dirname(os.path.abspath(__file__))
GEOBASE = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/geobase_2026-10-14.json')
TO_M = pyproj.Transformer.from_crs(4326, 32188, always_xy=True).transform
TO_LL = pyproj.Transformer.from_crs(32188, 4326, always_xy=True).transform

def norm(s): return re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFD', (s or '').lower()).encode('ascii', 'ignore').decode()).strip()

# (event date, n-th row of that date) -> (method, arguments, hint (borough or town, '' = any), precision, note on names)
# street = (name, type or '', direction or '')
S = lambda name, typ='', d='': (name, typ, d)
PLACES = {
 ('1912-04-10', 1): ('x', [S('Saint-Jacques', 'rue'), S('Inspecteur', 'rue')], 'Sud-Ouest|Ville-Marie', 'intersection', "printed « rue des Inspecteurs »: today's rue de l'Inspecteur"),
 ('1922-08-04', 1): ('x', [S('De Maisonneuve', 'boulevard', 'Ouest'), S('Elmhurst', 'avenue')], '', 'block', "printed « avenues Western and Elmhurst » (near the corner): Western Avenue is today's boulevard De Maisonneuve Ouest"),
 ('1924-05-18', 1): ('x', [S('Alexandre-DeSève', 'rue'), S('La Fontaine', 'rue')], 'Ville-Marie', 'intersection', "printed « rue Maisonneuve »: today's rue Alexandre-DeSève"),
 ('1926-10-05', 1): ('x', [S('Rose-de-Lima', 'rue'), S('Workman', 'rue')], '', 'block', ''),
 ('1927-06-22', 1): ('s', [S('Mentana', 'rue')], 'Plateau', 'street', "printed « rue Mentana, près de la rue Johnson »: no rue Johnson crosses rue Mentana in today's street file; the cross street is not identified"),
 ('1927-07-22', 1): ('a', [S('De Chateaubriand', 'avenue'), 7415], '', 'block', ''),
 ('1928-04-10', 1): ('x', [S('La Fontaine', 'rue'), S('Cuvillier', 'rue')], '', 'intersection', ''),
 ('1928-10-06', 1): ('x', [S('Saint-Philippe', 'rue'), S('Notre-Dame', 'rue', 'Ouest')], '', 'intersection', ''),
 ('1928-10-15', 1): ('x', [S('Bellechasse', 'rue'), S('Saint-Laurent', 'boulevard')], '', 'intersection', ''),
 ('1930-08-21', 1): ('n', [], '', 'none', ''),
 ('1931-11-11', 1): ('s', [S('18e', 'avenue')], 'Lachine', 'street', ''),
 ('1932-04-22', 1): ('x', [S('Wolfe', 'rue'), S('De Maisonneuve', 'boulevard', 'Est')], '', 'intersection', "printed « rue Demontigny »: that part of rue De Montigny is today's boulevard De Maisonneuve Est"),
 ('1933-08-23', 1): ('x', [S('Parc', 'avenue'), S('Sherbrooke', 'rue', 'Ouest')], '', 'intersection', 'one paper prints avenue du Parc and rue Sherbrooke, another rue De Bleury and rue Sherbrooke: the same crossing'),
 ('1935-06-08', 1): ('x', [S('Lajeunesse', 'rue'), S('Gouin', 'boulevard', 'Est')], '', 'block', ''),
 ('1936-10-23', 1): ('a', [S('Notre-Dame', 'rue', 'Est'), 7135], '', 'block', 'printed « opposite 7135 Notre Dame street east »'),
 ('1937-04-27', 1): ('x', [S('Sainte-Catherine', 'rue', 'Est'), S('Dézéry', 'rue')], '', 'intersection', ''),
 ('1937-10-04', 1): ('x', [S('Ontario', 'rue'), S('Saint-Laurent', 'boulevard')], '', 'intersection', ''),
 ('1939-12-23', 1): ('b', [S('Lacombe', 'avenue'), S('Décarie', 'boulevard'), S('Côte-des-Neiges', 'chemin')], '', 'block', 'about halfway between the two cross streets, as printed: farther than a block from either'),
 ('1940-07-28', 1): ('x', [S('Notre-Dame', 'rue', 'Est'), S('66e', 'avenue')], 'Pointe-aux-Trembles', 'block', 'one paper prints near 66e Avenue, another at 70e Avenue'),
 ('1941-04-10', 1): ('x', [S('De Maisonneuve', 'boulevard', 'Ouest'), S('Décarie', 'boulevard')], '', 'intersection', "printed « avenue Western »: today's boulevard De Maisonneuve Ouest"),
 ('1941-05-06', 1): ('x', [S('Lajeunesse', 'rue'), S('Jean-Talon', 'rue')], '', 'intersection', ''),
 ('1941-05-26', 1): ('x', [S('Mozart', 'avenue'), S('Saint-Laurent', 'boulevard')], '', 'intersection', ''),
 ('1941-08-06', 1): ('x', [S('Rachel', 'rue', 'Est'), S('Gascon', 'avenue')], '', 'intersection', ''),
 ('1941-10-03', 1): ('x', [S("D'Argenson", 'rue'), S('Saint-Patrick', 'rue')], '', 'intersection', ''),
 ('1944-05-30', 1): ('b', [S('Girouard', 'avenue'), S('De Maisonneuve', 'boulevard', 'Ouest'), S('Sherbrooke', 'rue', 'Ouest')], '', 'block', "printed « entre les rues Western et Sherbrooke »: Western Avenue is today's boulevard De Maisonneuve Ouest"),
 ('1944-08-21', 1): ('n', [], '', 'none', ''),
 ('1945-06-14', 1): ('x', [S('Fabre', 'rue'), S('Marie-Anne', 'rue', 'Est')], '', 'block', 'a lane east of rue Fabre, north of rue Marie-Anne'),
 ('1945-07-03', 1): ('b', [S('Côte-Sainte-Catherine', 'chemin'), S('Rockland', 'avenue'), S('Courcelette', 'avenue')], '', 'block', "printed « chemin Sainte-Catherine »: today's chemin de la Côte-Sainte-Catherine"),
 ('1945-07-03', 2): ('b', [S('Côte-Sainte-Catherine', 'chemin'), S('Rockland', 'avenue'), S('Courcelette', 'avenue')], '', 'block', "printed « chemin Sainte-Catherine »: today's chemin de la Côte-Sainte-Catherine"),
 ('1946-09-16', 1): ('x', [S('Saint-Jacques', 'rue'), S('Delinelle', 'rue')], '', 'intersection', ''),
 ('1947-06-03', 1): ('x', [S('Saint-Urbain', 'rue'), S('Clermont', '')], '', 'intersection', 'printed « rues Saint-Urbain et Clermont »'),
 ('1947-07-21', 1): ('a', [S('Messier', 'rue'), 4290], '', 'block', 'the papers print no. 4290 or no. 4279, between Rachel and Marie-Anne'),
 ('1947-08-20', 1): ('x', [S('De La Roche', 'rue'), S('Gilford', 'rue')], '', 'intersection', ''),
 ('1949-04-17', 1): ('x', [S('Taillon', 'rue'), S('Hochelaga', 'rue')], '', 'intersection', ''),
 ('1950-07-27', 1): ('n', [], '', 'none', "printed « chemin Saint-Michel », Saint-Léonard-de-Port-Maurice, in front of the family home: the road is not identified in today's street file"),
 ('1951-06-19', 1): ('x', [S('Decelles', 'rue'), S('Ouimet', 'rue')], 'Saint-Laurent', 'intersection', ''),
 ('1952-06-15', 1): ('x', [S('Saint-Antoine', 'rue', 'Est'), S('Gosford', 'rue')], '', 'intersection', "printed « rue Craig »: today's rue Saint-Antoine Est"),
 ('1952-06-21', 1): ('a', [S('Notre-Dame', 'rue', 'Est'), 4451], '', 'block', 'the papers differ on the place; this is the civic number one of them prints'),
 ('1953-05-08', 1): ('a', [S('Frontenac', 'rue'), 1836], '', 'block', ''),
 ('1954-09-07', 1): ('x', [S('Outremont', 'avenue'), S('Van Horne', 'avenue')], '', 'intersection', ''),
 ('1955-01-07', 1): ('a', [S('Saint-Patrick', 'rue'), 2574], '', 'block', ''),
 ('1955-05-02', 1): ('x', [S('William', 'rue'), S('Peel', 'rue')], '', 'intersection', "printed « rue Colborne »: taken as today's rue Peel south of rue Notre-Dame (to be confirmed on a period map)"),
 ('1955-07-29', 1): ('s', [S('Émile-Duployé', 'avenue')], '', 'block', 'between rue Gauthier and rue Sherbrooke: the avenue is one short segment in parc La Fontaine'),
 ('1955-08-09', 1): ('n', [], '', 'none', ''),
 ('1955-11-08', 1): ('x', [S('René-Lévesque', 'boulevard', 'Ouest'), S('Jeanne-Mance', 'rue')], '', 'intersection', "printed « boulevard Dorchester » (today's boulevard René-Lévesque) and « rue St-Georges », taken as today's rue Jeanne-Mance south of rue Sainte-Catherine (to be confirmed on a period map)"),
 ('1956-06-19', 1): ('x', [S('Galt', 'rue'), S('Verdun', 'rue')], 'Verdun', 'intersection', ''),
 ('1956-07-21', 1): ('n', [], '', 'none', ''),
 ('1956-07-26', 1): ('a', [S('Lepailleur', 'rue'), 1840], '', 'block', 'printed as near his parents\' home, whose civic number is given'),
 ('1957-06-29', 1): ('x', [S('24e', 'avenue'), S('Saint-Antoine', 'rue')], 'Lachine', 'intersection', ''),
 ('1957-07-15', 1): ('x', [S('Saint-Laurent', 'boulevard'), S('Mont-Royal', 'avenue')], '', 'intersection', ''),
 ('1957-07-23', 1): ('x', [S('Duke', 'rue'), S('Brennan', 'rue')], '', 'intersection', ''),
 ('1960-12-05', 1): ('s', [S('Dollard', 'avenue')], 'LaSalle', 'street', "printed « en face du 378 Dollard », Ville LaSalle: today's numbers on avenue Dollard run from 1080 to 2810, so the civic number cannot be placed"),
 ('1963-05-21', 1): ('x', [S('Poirier', 'rue'), S('Dépatie', 'rue')], 'Saint-Laurent', 'intersection', ''),
 ('1963-09-25', 1): ('s', [S('Jarry', 'rue', 'Est')], 'Saint-Léonard', 'street', ''),
 ('1964-05-12', 1): ('x', [S('Lacordaire', 'boulevard'), S('Lafourcade', '')], 'Saint-Léonard', 'intersection', 'printed « Lafoureade »'),
 ('1965-10-01', 1): ('x', [S('Rouen', 'rue'), S('De Lorimier', 'avenue')], '', 'intersection', ''),
 ('1966-03-16', 1): ('x', [S('Saint-Kevin', 'avenue'), S('Lavoie', 'rue')], '', 'intersection', ''),
 ('1966-08-01', 1): ('x', [S('Notre-Dame', 'rue', 'Est'), S("Jeanne-d'Arc", 'avenue')], '', 'intersection', ''),
 ('1967-03-28', 1): ('n', [], '', 'none', "a bus road of the transit commission along the Lachine canal, at the west end of the city: not in today's street file"),
 ('1967-06-17', 1): ('x', [S('Notre-Dame', 'rue', 'Est'), S('Bilaudeau', 'avenue')], '', 'intersection', "printed « rue Bilodeau »: today's avenue Bilaudeau"),
 ('1967-12-21', 1): ('a', [S('Mayfair', 'avenue'), 4560], '', 'block', ''),
 ('1968-03-19', 1): ('a', [S('Saint-Urbain', 'rue'), 6886], '', 'block', 'behind a house whose number reads 6886 on one page and 6666 on another'),
 ('1974-09-26', 1): ('s', [S('Lavaltrie', 'rue')], 'Mercier', 'street', 'place not printed; inferred from the home address on rue Lavaltrie (amendment 7): the least certain of the placements'),
 ('1976-04-27', 1): ('x', [S('Notre-Dame', 'rue', 'Est'), S('Meese', 'avenue')], '', 'intersection', ''),
 ('1976-06-26', 1): ('x', [S('Allard', 'rue'), S('Jogues', 'rue')], '', 'intersection', ''),
 ('1984-06-28', 1): ('x', [S('Charlevoix', 'rue'), S('Grand Trunk', 'rue')], '', 'intersection', ''),
 ('1985-04-29', 1): ('x', [S('Sherbrooke', 'rue', 'Est'), S("Jeanne-d'Arc", 'avenue')], '', 'intersection', ''),
 ('1991-06-03', 1): ('x', [S('Saint-Michel', 'boulevard'), S('Louvain', 'rue', 'Est')], '', 'intersection', ''),
 ('2008-08-26', 1): ('x', [S('Saint-Laurent', 'boulevard'), S('Crémazie', 'boulevard')], '', 'block', 'south of boulevard Crémazie'),
}

feats = []
for f in json.load(open(GEOBASE))['features']:
    p = f['properties']; g = shape(f['geometry'])
    from shapely.ops import transform
    feats.append((p, transform(TO_M, g)))
def area(p): return ' '.join(str(p.get(k) or '') for k in ('ARR_GCH', 'ARR_DRT', 'LIM_GCH', 'LIM_DRT'))
def segs(st, hint=''):
    name, typ, d = st; out = []
    for p, g in feats:
        if norm(p['NOM_VOIE']) != norm(name): continue
        if typ and norm(p['TYP_VOIE']) != norm(typ): continue
        if d and norm(p['DIR_VOIE'] or '') != norm(d): continue
        if hint and not any(norm(h) in norm(area(p)) for h in hint.split('|')): continue
        out.append((p, g))
    return out
def cross(a, b, hint):
    A, B = segs(a, hint), segs(b, hint)
    if not A or not B: return None, f"not found: {'/'.join(x[0] for x, y in ((a, A), (b, B)) if not y)}"
    best = None
    for pa, ga in A:
        for pb, gb in B:
            dd = ga.distance(gb)
            if best is None or dd < best[0]: best = (dd, ga, gb, pa)
    if best[0] > 250: return None, f'the two streets do not meet (nearest {best[0]:.0f} m)'
    p1, p2 = nearest_points(best[1], best[2])
    return (Point((p1.x + p2.x) / 2, (p1.y + p2.y) / 2), best[3]), ('' if best[0] <= 25 else f"the two streets no longer meet in today's street file: the point is midway between their nearest ends, {best[0]:.0f} m apart")
def addr(st, civic, hint):
    best = None
    for p, g in segs(st, hint):
        for a, b in ((p['DEB_GCH'], p['FIN_GCH']), (p['DEB_DRT'], p['FIN_DRT'])):
            try: a, b = int(a), int(b)
            except (TypeError, ValueError): continue
            if a <= 0 or b <= 0: continue
            lo, hi = min(a, b), max(a, b)
            gap = 0 if lo <= civic <= hi else min(abs(civic - lo), abs(civic - hi))
            par = (lo % 2 == civic % 2)
            key = (gap, not par)
            if best is None or key < best[0]:
                fr = 0.5 if hi == lo else min(1, max(0, (civic - a) / (b - a)))
                best = (key, g.interpolate(fr, normalized=True), p, gap)
    if best is None: return None, 'street not found'
    if best[3] > 60: return None, f'no block with that number (nearest range {best[3]} away)'
    return (best[1], best[2]), ('' if best[3] == 0 else f'number {best[3]} outside the nearest range')
def mid(st, hint):
    S_ = segs(st, hint)
    if not S_: return None, 'street not found'
    u = unary_union([g for _, g in S_]); c = u.centroid; p, _ = nearest_points(u, c)
    return (p, S_[0][0]), f'{len(S_)} segments, {u.length:.0f} m'

ev = list(csv.DictReader(open(os.path.join(H, 'events.csv'), encoding='utf-8')))
seen = collections.Counter(); out = []; problems = []
for e in ev:
    if e['age_group'] not in ('under 10', '10 to 14') or e['on_island_inferred'] != 'yes' or e['listed_apart']: continue
    d = e['event_date'][:10]; seen[d] += 1; key = (d, seen[d])
    if key not in PLACES: problems.append(f'{key}: no line in PLACES'); continue
    m, a, hint, prec, note = PLACES[key]; res, msg = None, ''
    if m == 'x': res, msg = cross(a[0], a[1], hint)
    elif m == 'a': res, msg = addr(a[0], a[1], hint)
    elif m == 's': res, msg = mid(a[0], hint)
    elif m == 'b':
        r1, m1 = cross(a[0], a[1], hint); r2, m2 = cross(a[0], a[2], hint)
        if r1 and r2: res = (Point((r1[0].x + r2[0].x) / 2, (r1[0].y + r2[0].y) / 2), r1[1])
        else: msg = m1 or m2
    if m != 'n' and res is None: problems.append(f'{key}: {msg}')
    lon = lat = ''; where = ''
    if res:
        lon, lat = TO_LL(res[0].x, res[0].y); lon, lat = f'{lon:.5f}', f'{lat:.5f}'
        p = res[1]; where = p['ARR_GCH'] if p['ARR_GCH'] not in (None, 'N/A') else p['LIM_GCH']
    out.append({'event_date': d, 'row_of_that_date': seen[d], 'age': re.match(r'\d+', e['age']).group(0) if re.match(r'\d+', e['age']) else '',
                'place_as_recorded': e['place'], 'placement': 'as printed' if e['on_island'] == 'yes' else 'inferred',
                'method': {'x': 'crossing of two streets', 'a': 'civic number', 's': 'middle of the street', 'b': 'between two cross streets', 'n': 'none'}[m],
                'precision': ('block' if (prec == 'intersection' and 'no longer meet' in msg) else prec) if (res or m == 'n') else 'none', 'lon': lon, 'lat': lat, 'borough_or_town_today': where,
                'name_note': note, 'program_note': msg})
unused = set(PLACES) - {(r['event_date'], r['row_of_that_date']) for r in out}
with open(os.path.join(H, 'places_geocoded.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
c = collections.Counter(r['precision'] for r in out)
print(len(out), 'events;', dict(c)); print('by borough or town:', collections.Counter(r['borough_or_town_today'] for r in out if r['lon']).most_common())
for p in problems: print('PROBLEM', p)
if unused: print('PLACES lines with no event:', sorted(unused))
