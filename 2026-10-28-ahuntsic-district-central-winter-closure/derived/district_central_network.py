#!/usr/bin/env python3
"""Season attributes of the District central lanes in the City's bike-network file.

Joins the City's « Réseau cyclable » GeoJSON (ID_TRC) with the géobase (NOM_VOIE, ARR_GCH/ARR_DRT)
for the streets named in the Ahuntsic-Cartierville notice of October 28, 2026, and sums the
lengths by street, lane type, separator, SAISONS4 and PROTEGE_4S. Writes district_central_network.csv.
Data: donnees.montreal.ca, « Réseau cyclable » and « Géobase » (CC BY 4.0), downloaded October 14, 2026.
Run: /opt/local/bin/python3.13 district_central_network.py [--data DIR]
"""
import argparse, collections, csv, json, os, unicodedata
ap = argparse.ArgumentParser(); ap.add_argument('--data', default=os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata'))
a = ap.parse_args()
def norm(s): return unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
gb = json.load(open(os.path.join(a.data, 'geobase_2026-10-14.json')))['features']
net = json.load(open(os.path.join(a.data, 'reseau_cyclable_2026-10-14.geojson')))['features']
STREETS = ['tolhurst', 'port-royal', 'meilleur', 'chabanel', 'legendre', 'du parc']
trc = {}
for f in gb:
    p = f['properties']
    if 'ahuntsic' in norm(str(p.get('ARR_GCH')) + str(p.get('ARR_DRT'))):
        for w in STREETS:
            if w in norm(p.get('NOM_VOIE')):
                trc[p['ID_TRC']] = (w + ' ' + str(p.get('DIR_VOIE') or '')).strip()
tot = collections.Counter()
for f in net:
    p = f['properties']
    if p.get('ID_TRC') in trc:
        tot[(trc[p['ID_TRC']], p.get('TYPE_VOIE_DESC'), p.get('SEPARATEUR_DESC') or '', p.get('SAISONS4'), p.get('PROTEGE_4S'))] += p.get('LONGUEUR') or 0
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'district_central_network.csv')
with open(out, 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['street', 'type_voie', 'separateur', 'saisons4', 'protege_4s', 'metres'])
    for k, v in sorted(tot.items()): w.writerow([*k, round(v)])
print(f'{len(trc)} géobase segments matched; {sum(tot.values()):.0f} m of network; written {out}')
