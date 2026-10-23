#!/usr/bin/env python3
"""Street conditions around the thirteen parish churches of the peer comparison: bike lanes on the
church's frontage (now, in the City's 2024 survey of the network, in its 2019–2020 survey), the
parking signs on the frontage and on the adjacent blocks of the same streets, the off-street parking
mapped next to the church, and the signs designed or installed 2019–2024.

Inputs (City of Montréal open data, CC BY 4.0, read where downloaded; not reproduced here except as the
extracts below):
  géobase (street centrelines with civic ranges)       geobase_2026-10-14.json
  Réseau cyclable (the network today)                  reseau_cyclable_2026-10-14.geojson
  Auscultation du réseau cyclable 2020 and 2024        auscultation_reseau_cyclable_{2020,2024}.gpkg
  Signalisation – Stationnement (every parking sign)   signalisation_stationnement.csv (Oct 23, 2026)
OpenStreetMap (© OpenStreetMap contributors, ODbL): one map extract per church (API 0.6 `map` call,
~650 m box), used for the church's building outline and the mapped parking lots; the extracts stay outside
the repository (named, never redistributed). `--fetch` downloads any missing extract.
  peer_streets_imagery_check.csv  the off-street parking seen on aerial imagery, by hand, with its date
Outputs: peer_streets.csv (one row per parish), peer_streets_signs.csv (every current parking-sign panel on
the frontage and adjacent blocks, with its side and dates), peer_streets_sources.tsv (file, URL, size,
SHA-256, date), figures/peer_streets_map_{en,fr}.{svg,png,pdf} (drawn by peer_streets_map.py).
Nothing here counts parking spaces: a sign says what is allowed where it stands, not how many cars fit.
Run: python3 peer_streets.py [--fetch]
"""
import csv, hashlib, json, math, os, sqlite3, struct, sys, time, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
MTL = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata')
OSM = os.path.expanduser('~/Terrebonne-data/third-party/osm/peer-parishes-2026-10-23')
FILES = {
    'geobase': (f'{MTL}/geobase_2026-10-14.json', 'https://donnees.montreal.ca/dataset/geobase', '2026-10-14'),
    'network': (f'{MTL}/reseau_cyclable_2026-10-14.geojson', 'https://donnees.montreal.ca/dataset/5ea29f40-1b5b-4f34-85b3-7c67088ff536/resource/0dc6612a-be66-406b-b2d9-59c9e1c65ebf/download/reseau_cyclable.geojson', '2026-10-14'),
    'survey2020': (f'{MTL}/auscultation-reseau-cyclable/auscultation_reseau_cyclable_2020.gpkg', 'https://donnees.montreal.ca/fr/dataset/77fe63be-109f-42b0-9e4c-3892621dcd72/resource/62e2d057-527c-4690-ab8d-6b68d6d06e0b/download/auscultation_reseau_cyclable_2020.gpkg', '2026-10-23'),
    'survey2024': (f'{MTL}/auscultation-reseau-cyclable/auscultation_reseau_cyclable_2024.gpkg', 'https://donnees.montreal.ca/fr/dataset/77fe63be-109f-42b0-9e4c-3892621dcd72/resource/eedcb5fb-f48b-4b68-bc91-e8a0e0c26291/download/auscultation_reseau_cyclable_2024.gpkg', '2026-10-23'),
    'signs': (f'{MTL}/signalisation-2026-10-23/signalisation_stationnement.csv', 'https://donnees.montreal.ca/dataset/8ac6dd33-b0d3-4eab-a334-5a6283eb7940/resource/7f1d4ae9-1a12-46d7-953e-6b9c18c78680/download/signalisation_stationnement.csv', '2026-10-23'),
}
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
SUBJECT = '130341852RR0001'
# The church building of each parish in OpenStreetMap (way id), found by name next to the address filed with the CRA.
# Saint-Raymond: the building at the filed address is tagged a place of worship without a name (checked on imagery).
# Notre-Dame-de-Grâce and Saint Augustine of Canterbury filed the same address: one church, two rows.
CHURCH = {'130341852RR0001': '159503777', '107362766RR0001': '158242591', '107369068RR0001': '1280166317',
          '107362980RR0001': '292386020', '119232296RR0001': '574623914', '130365521RR0001': '47175624',
          '131324782RR0001': '190139125', '107362659RR0001': '47332072', '118910025RR0001': '47332072',
          '131158727RR0001': '504323370', '119232247RR0001': '47331997', '107359119RR0001': '208178604',
          '118994094RR0001': '47331733'}
# A reference church outside the comparison (no T3010 figures used): the owner's suggestion of Oct 23, 2026, a church
# with large Sunday turnouts, no off-street lot and no assured street parking (Mile End, Le Plateau-Mont-Royal).
REFERENCE = [dict(bn='ref_st_michael', legal_name="Saint Michael's and Saint Anthony's (reference)", address='105 RUE SAINT-VIATEUR OUEST',
                  city='MONTREAL', role='reference', lonlat=(-73.59997, 45.52465))]
CHURCH['ref_st_michael'] = '353024298'
SHORT = {'ref_st_michael': "Saint Michael's and Saint Anthony's", '130341852RR0001': 'Sainte-Monique', '107362766RR0001': 'Notre-Dame-des-Neiges', '107369068RR0001': 'Saint-Kevin',
         '107362980RR0001': 'Saint-Antonin', '119232296RR0001': 'Saint-Malachie', '130365521RR0001': 'Saint-Léon',
         '131324782RR0001': 'Ascension of Our Lord', '107362659RR0001': 'Notre-Dame-de-Grâce', '118910025RR0001': 'Saint Augustine of Canterbury',
         '131158727RR0001': 'Saint-Raymond', '119232247RR0001': 'Saint-Ignace-de-Loyola', '107359119RR0001': 'Sainte-Catherine-de-Sienne',
         '118994094RR0001': 'Saint-Richard'}
FRONT_M = 35          # a street segment within this distance of the church's outline is a frontage
FRONT_M_FALLBACK = 60  # used when no segment is that close (churches set back from the street)
POLE_M = 25           # a sign pole is assigned to its nearest segment within this distance
ALONG = 0.6           # a lane piece lies along a segment when this share of its vertices is within 15 m of it
PARALLEL = 0.85       # ... and runs in the same direction (|cos| of the angle between the two)
FRONT_POLE_M = 80     # a pole on a frontage segment farther than this from the church counts with the adjacent blocks
CHANGE_YEARS = range(2019, 2025)
SUNDAY_M = 150       # radius of the Sunday-morning curb measure, metres from the church's outline
LATER_YEARS = range(2025, 2027)


# ---- geometry (local metres; the area is small enough for an equirectangular projection) ----
def xy(lon, lat):
    return ((lon + 73.63) * 111320 * math.cos(math.radians(45.47)), (lat - 45.47) * 110574)

def seg_proj(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L2))
    q = (a[0] + t * dx, a[1] + t * dy)
    return math.dist(p, q), (dx * (p[1] - a[1]) - dy * (p[0] - a[0]))

def line_dist(p, line):
    """Distance from p to a polyline and the side (+1 left, -1 right of the line's direction)."""
    best = min(seg_proj(p, line[i], line[i + 1]) for i in range(len(line) - 1)) if len(line) > 1 else (math.dist(p, line[0]), 0)
    return best[0], (1 if best[1] > 0 else -1)

def lines_dist(A, B):
    return min(min(line_dist(a, B)[0] for a in A), min(line_dist(b, A)[0] for b in B))

def along(piece, line, d=15):
    return sum(line_dist(p, line)[0] <= d for p in piece) / len(piece)

def parallel(A, B):
    a = (A[-1][0] - A[0][0], A[-1][1] - A[0][1]); b = (B[-1][0] - B[0][0], B[-1][1] - B[0][1])
    na, nb = math.hypot(*a), math.hypot(*b)
    return na > 0 and nb > 0 and abs(a[0] * b[0] + a[1] * b[1]) / (na * nb) >= PARALLEL

def uniq(items):
    return list(dict.fromkeys(items))

def centroid(poly):
    return (sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly))


# ---- readers ----
def gpkg_lines(fn):
    def wkb(b, o):
        bo = '<' if b[o] == 1 else '>'; t = struct.unpack(bo + 'I', b[o + 1:o + 5])[0] % 1000; o += 5
        n = struct.unpack(bo + 'I', b[o:o + 4])[0]; o += 4
        if t == 2:
            return [[struct.unpack(bo + 'dd', b[o + 16 * i:o + 16 * i + 16]) for i in range(n)]], o + 16 * n
        out = []
        for _ in range(n):
            g, o = wkb(b, o); out += g
        return out, o
    con = sqlite3.connect(fn)
    table = con.execute("select table_name from gpkg_contents where data_type='features'").fetchone()[0]
    cur = con.execute(f'select * from "{table}"'); cols = [d[0] for d in cur.description]; rows = []
    for r in cur:
        d = dict(zip(cols, r)); g = d.pop('geom'); env = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(g[3] >> 1) & 7]
        d['lines'] = [[xy(*p) for p in L] for L in wkb(g, 8 + env)[0]]; rows.append(d)
    return rows

def osm_extract(bn, lonlat):
    fn = os.path.join(OSM, f'{bn}.osm')
    if not os.path.exists(fn):
        if '--fetch' not in sys.argv:
            sys.exit(f'missing {fn}: run with --fetch')
        lon, lat = lonlat
        url = f'https://api.openstreetmap.org/api/0.6/map?bbox={lon-0.0042:.5f},{lat-0.003:.5f},{lon+0.0042:.5f},{lat+0.003:.5f}'
        os.makedirs(OSM, exist_ok=True)
        open(fn, 'wb').write(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=120).read())
        time.sleep(2)
    root = ET.parse(fn).getroot(); nodes, ways = {}, {}
    for e in root:
        tags = {x.get('k'): x.get('v') for x in e.findall('tag')}
        if e.tag == 'node':
            nodes[e.get('id')] = (xy(float(e.get('lon')), float(e.get('lat'))), tags)
        elif e.tag == 'way':
            ways[e.get('id')] = ([x.get('ref') for x in e.findall('nd')], tags)
    shape = lambda w: [nodes[n][0] for n in ways[w][0] if n in nodes]
    return nodes, ways, shape


def classify(desc):
    """Plain reading of a sign's text (the City's RPA description) in four classes."""
    d = desc.upper()
    if d.startswith('\\A'):
        return 'no stopping at any time' if 'EN TOUT TEMPS' in d else 'no stopping, some hours'
    if d.startswith('\\P'):
        if 'HANDICAP' in d or 'DEBARCADERE' in d or 'CORBILLARD' in d:
            return 'reserved (disabled / drop-off)'
        return 'no parking at any time' if 'EN TOUT TEMPS' in d else 'no parking, some hours (street cleaning or peak)'
    if d.startswith('P '):
        return 'permit or time-limited parking'
    return 'other'


DAYS = ['LUN', 'MAR', 'MER', 'JEU', 'VEN', 'SAM', 'DIM']
MONTHS = {'JANV': 1, 'FEV': 2, 'FÉV': 2, 'MARS': 3, 'AVRIL': 4, 'AVR': 4, 'MAI': 5, 'JUIN': 6, 'JUIL': 7, 'AOUT': 8, 'AOÛT': 8,
          'SEPT': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12, 'DÉC': 12}


def sunday(desc, month, t0=10.0, t1=12.0):
    """What a sign means for a visitor without a permit on a Sunday between 10:00 and 12:00 in the given month:
    'excluded' (no stopping or parking, residents' permit only, or reserved for others), 'limited' (a time limit
    under two hours), or 'open' (the sign does not apply then). Read from the sign's text (the City's RPA
    description): days (none named = every day; « jours d'école » = weekdays), hours (none = all day), months."""
    import re
    d = desc.upper().replace('.', ' ').replace('  ', ' ')
    ban, lim = d.startswith('\\A') or d.startswith('\\P'), d.startswith('P ')
    if not (ban or lim):
        return 'open'
    m = re.search(r'(\d+)\s*(JANV|FEV|FÉV|MARS|AVRIL|AVR|MAI|JUIN|JUIL|AOUT|AOÛT|SEPT|OCT|NOV|DEC|DÉC)\w*\s+(?:AU|A)\s+(\d+)?\s*(JANV|FEV|FÉV|MARS|AVRIL|AVR|MAI|JUIN|JUIL|AOUT|AOÛT|SEPT|OCT|NOV|DEC|DÉC)', d) \
        or re.search(r'()(SEPT|OCT|NOV)\w*\s+A\s+()(JUIN)', d)
    if m:
        a, b = MONTHS[m.group(2)], MONTHS[m.group(4)]
        inside = a <= month <= b if a <= b else (month >= a or month <= b)
        if not inside:
            return 'open'
    days = set()
    for x, y in re.findall(r'\b(LUN|MAR|MER|JEU|VEN|SAM|DIM)\w*\s+(?:AU|A)\s+(LUN|MAR|MER|JEU|VEN|SAM|DIM)', d):
        days |= set(DAYS[DAYS.index(x):DAYS.index(y) + 1])
    for w in re.findall(r'\b(LUNDI|MARDI|MERCREDI|JEUDI|VENDREDI|SAMEDI|DIMANCHE|LUN|MAR|MER|JEU|VEN|SAM|DIM)\b', d):
        days.add(w[:3])
    if "JOURS D'ECOLE" in d or 'JOURS DE CLASSE' in d:
        days |= set(DAYS[:5])
    if days and 'DIM' not in days:
        return 'open'
    hours = re.findall(r'(\d{1,2})\s*H?\s*(\d{2})?\s*-\s*(\d{1,2})\s*H\s*(\d{2})?', d)
    if hours:
        hit = False
        for h0, m0, h1, m1 in hours:
            a, b = int(h0) + int(m0 or 0) / 60, int(h1) + int(m1 or 0) / 60
            hit |= (a < t1 and b > t0) if a < b else (b > t0 or a < t1)  # overnight spans
        if not hit:
            return 'open'
    if ban:
        return 'excluded'
    if 'RESERVE' in d or 'SEULEMENT' in d:
        return 'excluded'
    mm = re.search(r'P\s+(\d+)\s*MIN', d); hh = re.search(r'P\s+0?(\d)\s*H\b', d)
    minutes = int(mm.group(1)) if mm else (int(hh.group(1)) * 60 if hh else 999)
    return 'limited' if minutes < 120 else 'open'


def address_point(G, address):
    """Interpolate the filed civic number on its géobase segment (the matching side's range)."""
    import re, unicodedata
    n = lambda s: unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('-', ' ').replace("'", ' ')
    parts = address.split(); num = int(parts[0].split('-')[-1])
    st = re.sub(r'^(rue de |rue |av |ch de la |ch |de )', '', n(' '.join(parts[1:])))
    st = re.sub(r' (ave|ouest)$', '', st); st = {'maisonneuve': 'de maisonneuve'}.get(st, st)
    for f in G:
        p = f['properties']
        if n(p['NOM_VOIE'] or '') != st:
            continue
        for side in ('GCH', 'DRT'):
            lo, hi = p['DEB_' + side], p['FIN_' + side]
            if lo and hi and min(lo, hi) <= num <= max(lo, hi) and lo % 2 == num % 2:
                c = f['geometry']['coordinates']; k = round((num - lo) / (hi - lo) * (len(c) - 1)) if hi != lo else 0
                return c[k]
    sys.exit(f'address not found in the géobase: {address}')


def main():
    peers = list(csv.DictReader(open(os.path.join(HERE, 'peer_parishes.csv'), encoding='utf-8'))) + REFERENCE
    G = json.load(open(FILES['geobase'][0], encoding='utf-8'))['features']
    for f in G:
        f['xy'] = [xy(*c) for c in f['geometry']['coordinates']]
    trc_name = {f['properties']['ID_TRC']: f['properties']['ODONYME'].strip() for f in G}
    NET = []
    for f in json.load(open(FILES['network'][0], encoding='utf-8'))['features']:
        g = f['geometry']; Ls = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for L in Ls:
            NET.append((f['properties'], [xy(*c[:2]) for c in L]))
    S20, S24 = gpkg_lines(FILES['survey2020'][0]), gpkg_lines(FILES['survey2024'][0])
    signs = []
    for r in csv.DictReader(open(FILES['signs'][0], encoding='utf-8-sig')):
        if r['Latitude'] and 45.44 < float(r['Latitude']) < 45.54 and -73.68 < float(r['Longitude']) < -73.58:
            r['xy'] = xy(float(r['Longitude']), float(r['Latitude'])); signs.append(r)
    imagery = {r['bn']: r for r in csv.DictReader(open(os.path.join(HERE, 'peer_streets_imagery_check.csv'), encoding='utf-8'))} \
        if os.path.exists(os.path.join(HERE, 'peer_streets_imagery_check.csv')) else {}

    rows, sign_rows, geo = [], [], {}
    for p in peers:
        bn = p['bn']; lonlat = p.get('lonlat') or address_point(G, p['address'])
        nodes, ways, shape = osm_extract(bn, lonlat)
        C = shape(CHURCH[bn]); cc = centroid(C)
        near = [f for f in G if math.dist(f['xy'][0], cc) < 800]
        dist = [(lines_dist(C, f['xy']), f) for f in near if not (f['properties']['ODONYME'] or '').startswith('Autoroute')]
        front = [(d, f) for d, f in dist if d <= FRONT_M] or [(d, f) for d, f in dist if d <= FRONT_M_FALLBACK]
        front.sort(key=lambda x: x[0]); front_ids = {f['properties']['ID_TRC'] for _, f in front}
        # adjacent blocks: same street, sharing an end with a frontage segment
        adj = []
        for _, f in front:
            for g in near:
                gp = g['properties']
                if gp['ID_TRC'] in front_ids or gp['ID_TRC'] in {a['properties']['ID_TRC'] for a in adj}:
                    continue
                if gp['NOM_VOIE'] == f['properties']['NOM_VOIE'] and min(math.dist(a, b) for a in (g['xy'][0], g['xy'][-1]) for b in (f['xy'][0], f['xy'][-1])) < 3:
                    adj.append(g)

        def lanes_on(f):
            """Lane pieces of today's network on segment f: by the segment id, else lying along it (not just crossing its end)."""
            out = []
            for q, L in NET:
                if math.dist(L[0], f['xy'][0]) > 500:
                    continue
                if q['ID_TRC'] == f['properties']['ID_TRC'] or (not q['ID_TRC'] and parallel(L, f['xy']) and along(L, f['xy']) >= ALONG and along(f['xy'], L, 20) >= 0.5):
                    out.append(q)
            return out

        def survey_on(S, f):
            hits = []
            for r in S:
                for L in r['lines']:
                    if math.dist(L[0], f['xy'][0]) < 500 and parallel(L, f['xy']) and along(L, f['xy']) >= ALONG and along(f['xy'], L, 20) >= 0.5:
                        hits.append(r)
            return hits

        fr_desc, now_desc, s24_desc, s20_desc, change = [], [], [], [], []
        for d, f in front:
            fp = f['properties']; name = fp['ODONYME'].strip()
            fr_desc.append(f'{name} ({d:.0f} m; segment {fp["ID_TRC"]})')
            now = lanes_on(f); s24 = survey_on(S24, f); s20 = survey_on(S20, f)
            n_ = sorted({f"{q['TYPE_VOIE_DESC']} ({q['TYPE_VOIE2_DESC']}; protected all year: {q['PROTEGE_4S']}; separator: {q['SEPARATEUR_DESC'] or 'none'})" for q in now})
            a_ = sorted({r['type_voie'] for r in s24}); b_ = sorted({r['type_voie'] for r in s20})
            if n_: now_desc.append(f'{name}: ' + '; '.join(n_))
            if a_: s24_desc.append(f'{name}: ' + '; '.join(a_))
            if b_: s20_desc.append(f'{name}: ' + '; '.join(b_))
            today = sorted({q['TYPE_VOIE_DESC'] for q in now})
            # a change: two layers that both record the segment disagree, or one of the two recent layers lacks it;
            # absence from the 2019–2020 survey alone is not a change (that survey covered part of the network only)
            if (today != a_) or (b_ and a_ and b_ != a_):
                change.append(f'{name}: 2019–2020 survey {", ".join(b_) or "not recorded"}; 2024 survey {", ".join(a_) or "not recorded"}; today {", ".join(today) or "no lane"}')
        # nearest lane of today's network
        nd, nq = min(((lines_dist(C, L), q) for q, L in NET if math.dist(L[0], cc) < 1500), key=lambda x: x[0])
        nearest = f"{nd:.0f} m: {nq['TYPE_VOIE_DESC']}, {trc_name.get(int(nq['ID_TRC'] or 0), 'off-street path') if nq['ID_TRC'] else 'off-street path'}"

        # parking signs on the frontage and the adjacent blocks; each pole goes to its nearest segment
        church_side = {f['properties']['ID_TRC']: line_dist(cc, f['xy'])[1] for _, f in front}
        segs = [f for _, f in front] + adj
        by_side = {}
        for r in signs:
            if min(math.dist(r['xy'], f['xy'][0]) for f in segs) > 400:
                continue
            dd = [(line_dist(r['xy'], f['xy']), f) for f in near]
            (dmin, side), f = min(dd, key=lambda x: x[0][0])
            if dmin > POLE_M or f not in segs:
                continue
            fp = f['properties']; tid = fp['ID_TRC']
            if tid in front_ids and line_dist(r['xy'], C)[0] <= FRONT_POLE_M:
                where = 'frontage, church side' if side == church_side[tid] else 'frontage, opposite side'
            else:
                where = 'adjacent block or same street beyond the frontage'
            cls = classify(r['DESCRIPTION_RPA'])
            sign_rows.append(dict(bn=bn, parish=SHORT[bn], street=fp['ODONYME'].strip(), segment=tid, where=where, pole=r['POTEAU_ID_POT'],
                                  panel=r['PANNEAU_ID_PAN'], text=r['DESCRIPTION_RPA'], code=r['CODE_RPA'], reading=cls, arrow=r['FLECHE_PAN'],
                                  status=r['DESCRIPTION_REP'], pole_version_date=r['DATE_CONCEPTION_POT'], action=r['DESCRIPTION_RAC'],
                                  action_date=r['DATE_EXECUTION_ACT'], lon=r['Longitude'], lat=r['Latitude'],
                                  face=f"{tid}{'L' if side > 0 else 'R'}", church_side_of_street='yes' if side == line_dist(cc, f['xy'])[1] else 'no',
                                  dist_church_m=f"{line_dist(r['xy'], C)[0]:.0f}",
                                  sunday_june=sunday(r['DESCRIPTION_RPA'], 6), sunday_february=sunday(r['DESCRIPTION_RPA'], 2)))
            if r['DESCRIPTION_REP'] == 'Réel':
                by_side.setdefault(where, {}).setdefault(cls, set()).add(r['POTEAU_ID_POT'])
        def summary(where):
            d = by_side.get(where)
            return '; '.join(f'{k}: {len(v)} pole(s)' for k, v in sorted(d.items())) if d else ''
        mine = [s for s in sign_rows if s['bn'] == bn]
        def changes(years):
            ch, rm = {}, set()
            for s in mine:
                if not (s['where'].startswith('frontage') and s['action_date'][:4].isdigit() and int(s['action_date'][:4]) in years):
                    continue
                if s['status'] == 'Réel' and s['action'] in ('Installer', 'Corr.: Installer', 'Changer'):
                    ch.setdefault((s['action_date'][:7], s['reading']), set()).add(s['pole'])
                elif s['status'] == 'Enlevé':
                    rm.add((s['action_date'][:7], s['reading'], s['pole']))
            out = [f'{m}: {k} installed or changed ({len(v)} pole(s))' for (m, k), v in sorted(ch.items())]
            out += [f'{m}: {k} removed (pole {p})' for m, k, p in sorted(rm)]
            return '; '.join(out)
        sign_change, sign_later = changes(CHANGE_YEARS), changes(LATER_YEARS)
        in_city_signs = any(r for r in signs if math.dist(r['xy'], cc) < 300)

        # Sunday morning, 10:00-12:00: every street face (segment x side) within SUNDAY_M of the church. A face is closed
        # to a visitor when every pole on it carries a sign excluding a visitor then, or when a residents' permit sign
        # (S3R) applies then; open otherwise (a face with no sign is open under the general rules). Length-weighted.
        sunday_cols = {}
        if in_city_signs:
            zone = [f for f in near if not (f['properties']['ODONYME'] or '').startswith('Autoroute') and lines_dist(C, f['xy']) <= SUNDAY_M]
            poles = {}
            for r in signs:
                if r['DESCRIPTION_REP'] != 'Réel' or min(math.dist(r['xy'], f['xy'][0]) for f in zone) > 500:
                    continue
                (dmin, side), f = min(((line_dist(r['xy'], g['xy']), g) for g in near), key=lambda x: x[0][0])
                if dmin <= POLE_M and f in zone:
                    poles.setdefault((f['properties']['ID_TRC'], side), {}).setdefault(r['POTEAU_ID_POT'], []).append(r['DESCRIPTION_RPA'])
            for month, tag in ((6, 'june'), (2, 'february')):
                total = closed = permit = 0.0
                for f in zone:
                    L = sum(math.dist(f['xy'][i], f['xy'][i + 1]) for i in range(len(f['xy']) - 1))
                    for side in (1, -1):
                        P = poles.get((f['properties']['ID_TRC'], side), {})
                        st = {pid: [sunday(t, month) for t in texts] for pid, texts in P.items()}
                        is_permit = any('S3R' in t.upper() and sunday(t, month) == 'excluded' for texts in P.values() for t in texts)
                        all_closed = bool(st) and all('excluded' in v for v in st.values())
                        total += L
                        if is_permit or all_closed:
                            closed += L
                            permit += L if is_permit else 0
                sunday_cols[f'sunday_{tag}_curb_closed_pct'] = f'{100 * closed / total:.0f}' if total else ''
                sunday_cols[f'sunday_{tag}_curb_permit_pct'] = f'{100 * permit / total:.0f}' if total else ''
            sunday_cols['sunday_curb_m'] = f'{total:.0f}'
        lots = []
        for w, (nds, t) in ways.items():
            if t.get('amenity') == 'parking' and len(nds) > 2:
                P = shape(w)
                if len(P) > 2 and lines_dist(C, P) <= 30:
                    area = abs(sum(P[i][0] * P[i + 1][1] - P[i + 1][0] * P[i][1] for i in range(len(P) - 1))) / 2
                    lots.append(f"way {w}, {lines_dist(C, P):.0f} m, ~{area:.0f} m², access={t.get('access', 'not tagged')}, fee={t.get('fee', 'not tagged')}")
        im = imagery.get(bn, {})
        geo[bn] = dict(church=C, front=[f['xy'] for _, f in front], lonlat=lonlat)
        rows.append(dict(
            bn=bn, parish=SHORT[bn], role=p['role'], address_filed=f"{p['address']}, {p['city']}", church_osm=f"way {CHURCH[bn]} ({ways[CHURCH[bn]][1].get('name', 'no name in OSM')})",
            frontage_streets=' | '.join(uniq(fr_desc)),
            lane_on_frontage_now=' | '.join(uniq(now_desc)) or 'none',
            lane_on_frontage_survey_2024=' | '.join(uniq(s24_desc)) or 'none recorded',
            lane_on_frontage_survey_2019_2020=' | '.join(uniq(s20_desc)) or 'none recorded',
            lane_change_since_2019=' | '.join(uniq(change)) or 'none in these layers',
            nearest_lane_today=nearest,
            signs_frontage_church_side=summary('frontage, church side') or ('no sign on record' if in_city_signs else 'not in the City dataset (another municipality)'),
            signs_frontage_opposite_side=summary('frontage, opposite side') or ('no sign on record' if in_city_signs else 'not in the City dataset (another municipality)'),
            signs_adjacent_blocks=summary('adjacent block or same street beyond the frontage') or ('no sign on record' if in_city_signs else 'not in the City dataset (another municipality)'),
            sign_changes_frontage_2019_2024=sign_change or ('none on record' if in_city_signs else 'not in the City dataset (another municipality)'),
            sign_changes_frontage_2025_2026=sign_later or ('none on record' if in_city_signs else 'not in the City dataset (another municipality)'),
            parking_lot_osm=' | '.join(lots) or 'none mapped within 30 m',
            parking_lot_imagery=im.get('seen', 'not checked'), imagery_checked=im.get('checked', ''), imagery_source=im.get('source', ''),
            note=im.get('note', ''), **{k: sunday_cols.get(k, 'not in the City dataset') for k in ('sunday_curb_m', 'sunday_june_curb_closed_pct', 'sunday_june_curb_permit_pct', 'sunday_february_curb_closed_pct', 'sunday_february_curb_permit_pct')}))
        r = rows[-1]
        protected = 'protected all year: Oui' in r['lane_on_frontage_now']
        r['frontage_lane'] = 'protected' if protected else ('painted or shared' if r['lane_on_frontage_now'] != 'none' else 'none')
        r['frontage_lane_new_since_2024_survey'] = 'yes' if any('2024 survey' in c and not c.split('2024 survey ')[1].startswith(c.split('today ')[1]) for c in uniq(change)) else 'no'
        lot = im.get('seen', '')
        r['off_street_lot'] = 'not checked' if not lot else ('no' if lot.startswith('no ') else 'yes')
        r['shares_subject_situation'] = 'subject' if bn == SUBJECT else ('yes' if protected and r['frontage_lane_new_since_2024_survey'] == 'yes' and r['off_street_lot'] == 'no' else 'no')

    cols = list(rows[0])
    with open(os.path.join(HERE, 'peer_streets.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, cols); w.writeheader(); w.writerows(rows)
    with open(os.path.join(HERE, 'peer_streets_signs.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, list(sign_rows[0])); w.writeheader(); w.writerows(sign_rows)
    with open(os.path.join(HERE, 'peer_streets_sources.tsv'), 'w', encoding='utf-8') as f:
        f.write('name\tfile\turl\tbytes\tsha256\tdownloaded\tlicence\n')
        for k, (fn, url, d) in FILES.items():
            f.write(f"{k}\t{os.path.basename(fn)}\t{url}\t{os.path.getsize(fn)}\t{hashlib.sha256(open(fn, 'rb').read()).hexdigest()}\t{d}\tCC BY 4.0 (Ville de Montréal)\n")
        for bn in CHURCH:
            fn = os.path.join(OSM, f'{bn}.osm')
            f.write(f"osm_{bn}\t{os.path.basename(fn)}\thttps://api.openstreetmap.org/api/0.6/map (box around the filed address)\t{os.path.getsize(fn)}\t{hashlib.sha256(open(fn, 'rb').read()).hexdigest()}\t{time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(fn)))}\tODbL (© OpenStreetMap contributors), not redistributed\n")
    write_tables(rows, sign_rows)
    print(f'{len(rows)} parishes, {len(sign_rows)} sign panels -> peer_streets.csv, peer_streets_signs.csv, peer_streets_table_{{en,fr}}.tex')
    for r in rows:
        print(f"\n{r['parish']}: {r['frontage_streets']}\n  now: {r['lane_on_frontage_now']}\n  2024: {r['lane_on_frontage_survey_2024']}\n  2019-20: {r['lane_on_frontage_survey_2019_2020']}\n  change: {r['lane_change_since_2019']}\n  CLASS: lane={r['frontage_lane']} new={r['frontage_lane_new_since_2024_survey']} lot={r['off_street_lot']} shares={r['shares_subject_situation']}\n  nearest: {r['nearest_lane_today']}\n  church side: {r['signs_frontage_church_side']}\n  opposite: {r['signs_frontage_opposite_side']}\n  adjacent: {r['signs_adjacent_blocks']}\n  sign changes: {r['sign_changes_frontage_2019_2024']}\n  2025-26: {r['sign_changes_frontage_2025_2026']}\n  lots (OSM): {r['parking_lot_osm']}")


KIND = {'en': {'Piste cyclable sur rue': 'protected lane', 'Bande cyclable': 'painted lane', 'Chaussée désignée': 'designated roadway', 'Piste cyclable en site propre': 'off-street path'},
        'fr': {'Piste cyclable sur rue': 'piste protégée', 'Bande cyclable': 'bande cyclable', 'Chaussée désignée': 'chaussée désignée', 'Piste cyclable en site propre': 'piste en site propre'}}
TT = {'en': dict(head=['', 'Parish', 'Lane on the frontage today', '2024 / 2019--20 surveys', 'Off-street lot', 'No-stopping poles'],
                 none='none', nr='--', yes='yes', no='no', other='not in the City data', same='same', lot={'yes': 'yes', 'no': 'no', 'not checked': 'not checked'}),
      'fr': dict(head=['', 'Paroisse', 'Voie en façade aujourd\'hui', 'Relevés 2024 / 2019--20', 'Stationnement hors rue', 'Poteaux «\\,arrêt interdit\\,»'],
                 none='aucune', nr='--', yes='oui', no='non', other='hors données de la Ville', same='idem', lot={'yes': 'oui', 'no': 'non', 'not checked': 'non vérifié'})}


SU = {'en': dict(head=['Church', 'Lane on the frontage', 'Off-street lot', 'Curb within 150~m (m)', 'Closed to a visitor', 'of which residents\' permit'],
                 prot='protected', paint='painted', new=' (new)', ref='(reference, outside the comparison)'),
      'fr': dict(head=['Église', 'Voie en façade', 'Stationnement hors rue', 'Bordure à moins de 150~m (m)', 'Fermée à un visiteur', 'dont vignette de résident'],
                 prot='protégée', paint='bande', new=' (nouvelle)', ref='(référence, hors comparaison)')}


def tex_escape(x):
    return x.replace('&', '\\&').replace('%', '\\%').replace('_', '\\_')


def write_tables(rows, sign_rows):
    """The table of the note's subsection: one row per parish (the two at one address on one row each)."""
    import re
    for lang in ('en', 'fr'):
        t = TT[lang]; k = KIND[lang]
        out = ['\\begin{tabular}{@{}r>{\\raggedright\\arraybackslash}p{3.4cm}>{\\raggedright\\arraybackslash}p{4.2cm}>{\\raggedright\\arraybackslash}p{4.4cm}>{\\raggedright\\arraybackslash}p{1.7cm}r@{}}\\toprule', ' & '.join(t['head']) + ' \\\\\\midrule']
        i = 0
        for r in [r for r in rows if r['role'] != 'reference']:
            i += 0 if r['bn'] == '118910025RR0001' else 1  # same church as Notre-Dame-de-Grâce: same number as on the map
            def lanes(field):
                if r[field] in ('none', 'none recorded'):
                    return []
                return uniq(f"{seg.split(': ')[0].replace('Avenue ', 'av. ').replace('Rue ', 'rue ').replace('Boulevard ', 'boul. ')}, {k.get(seg.split(': ')[1].split(' (')[0], seg.split(': ')[1].split(' (')[0])}" for seg in r[field].split(' | '))
            now = lanes('lane_on_frontage_now'); s24 = lanes('lane_on_frontage_survey_2024'); s20 = lanes('lane_on_frontage_survey_2019_2020')
            surveys = ('; '.join(s24) or t['none']) + ' / ' + ('; '.join(s20) or t['none'])
            if s24 == now and s20 == now and now:
                surveys = t['same'] + ' / ' + t['same']
            mine = [x for x in sign_rows if x['bn'] == r['bn'] and x['where'].startswith('frontage') and x['status'] == 'Réel'
                    and x['reading'] == 'no stopping at any time' and x['action'] in ('Installer', 'Corr.: Installer', 'Changer')
                    and x['action_date'][:4].isdigit() and int(x['action_date'][:4]) in CHANGE_YEARS]
            poles = len({x['pole'] for x in mine})
            if r['signs_frontage_church_side'].startswith('not in the City'):
                poles_s = t['nr']
            else:
                poles_s = str(poles)
            name = r['parish'] + ('$^{*}$' if r['bn'] in ('107362659RR0001', '118910025RR0001') else '')
            if r['role'] == 'subject':
                name = '\\textbf{' + name + '}'
            out.append(' & '.join([str(i), name, tex_escape('; '.join(now) or t['none']), tex_escape(surveys), t['lot'][r['off_street_lot']], poles_s]) + ' \\\\')
        out.append('\\bottomrule\n\\end{tabular}')
        open(os.path.join(HERE, f'peer_streets_table_{lang}.tex'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
        # the Sunday-morning table: every row with the measure, the reference church last
        u = SU[lang]
        out = ['\\begin{tabular}{@{}>{\\raggedright\\arraybackslash}p{4.6cm}>{\\raggedright\\arraybackslash}p{2.6cm}>{\\raggedright\\arraybackslash}p{1.7cm}rrr@{}}\\toprule', ' & '.join(u['head']) + ' \\\\\\midrule']
        lane = {'protected': u['prot'], 'painted or shared': u['paint'], 'none': t['none']}
        for r in sorted([r for r in rows if r['role'] != 'reference' and r['sunday_curb_m'][:1].isdigit() and r['bn'] != '118910025RR0001'],
                        key=lambda r: -int(r['sunday_june_curb_closed_pct'])) + [r for r in rows if r['role'] == 'reference']:
            name = r['parish'] + (' ' + u['ref'] if r['role'] == 'reference' else '') + (' (+ St Augustine)' if r['bn'] == '107362659RR0001' else '')
            if r['role'] == 'subject':
                name = '\\textbf{' + name + '}'
            if r['role'] == 'reference':
                out.append('\\midrule')
            out.append(' & '.join([name, lane[r['frontage_lane']] + (u['new'] if r['frontage_lane_new_since_2024_survey'] == 'yes' else ''), t['lot'][r['off_street_lot']],
                                   f"{int(r['sunday_curb_m']):,}".replace(',', '\\,'), r['sunday_june_curb_closed_pct'] + '~\\%', r['sunday_june_curb_permit_pct'] + '~\\%']) + ' \\\\')
        out.append('\\bottomrule\n\\end{tabular}')
        open(os.path.join(HERE, f'peer_streets_sunday_table_{lang}.tex'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')


if __name__ == '__main__':
    main()
