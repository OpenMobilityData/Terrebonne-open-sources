#!/usr/bin/env python3
"""Which cycling facilities on the streets named in this folder lie on the City's administrative arterial network.

Joins two City of Montréal open-data files (CC BY 4.0) on the géobase segment id (ID_TRC):
  - « Réseau artériel administratif (2023) » (GPKG, last modified 2023-12-20): one row per géobase segment, ARTERE = 1
    where the segment is on the arterial network defined by by-law 02-003;
  - « Réseau cyclable » as downloaded on October 14, 2026 (GeoJSON): one row per cycling facility on a segment, with its
    type, its length (LONGUEUR, metres) and whether it is in the protected four-season network (PROTEGE_4S).
Writes arterial_check.csv: one row per street and facility type, with the metres on arterial and on non-arterial segments.

Limits: the arterial layer is the 2023 version (by-law 02-003 was amended on October 19, 2026); a facility whose segment
id is absent from the arterial layer is counted under « no match »; lengths are those of the cycling file, by facility.

  python3 arterial_check.py [arterial.gpkg] [cycling.geojson]     (needs geopandas)
"""
import os, sys, csv, warnings
import geopandas as gpd
warnings.filterwarnings('ignore')
H = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/')
A = sys.argv[1] if len(sys.argv) > 1 else D + 'reseau-arteriel-administratif/reseau-arteriel-administratif-2023.gpkg'
C = sys.argv[2] if len(sys.argv) > 2 else D + 'reseau_cyclable_2026-10-14.geojson'
art = gpd.read_file(A)[['ID_TRC', 'NOM_VOIE', 'ARRONDISSEMENT_O_G', 'ARRONDISSEMENT_O_D', 'ARTERE']]
cyc = gpd.read_file(C).drop(columns='geometry')
m = cyc.merge(art, on='ID_TRC', how='left')
# (label, street name in the arterial layer, borough as written in the layer)
STREETS = [('rue de Terrebonne', 'Terrebonne', 'Côte-des-Neiges-Notre-Dame-de-Grâce'),
           ('avenue du Parc', 'Parc', 'Ahuntsic-Cartierville'), ('rue Meilleur', 'Meilleur', 'Ahuntsic-Cartierville'),
           ('rue de Port-Royal', 'Port-Royal', 'Ahuntsic-Cartierville'), ('rue Tolhurst', 'Tolhurst', 'Ahuntsic-Cartierville'),
           ('rue Legendre', 'Legendre', 'Ahuntsic-Cartierville'), ('rue Chabanel', 'Chabanel', 'Ahuntsic-Cartierville'),
           ('avenue Lajoie', 'Lajoie', 'Outremont')]
rows = []
for label, name, boro in STREETS:
    s = m[(m['NOM_VOIE'].fillna('').str.contains(name, case=False)) & ((m['ARRONDISSEMENT_O_G'] == boro) | (m['ARRONDISSEMENT_O_D'] == boro))]
    for (typ, p4), g in s.groupby(['TYPE_VOIE_DESC', 'PROTEGE_4S']):
        rows.append(dict(street=label, borough=boro, facility_type=typ, protected_four_season=p4, facilities=len(g),
                         metres_on_arterial_segments=round(g.loc[g['ARTERE'] == 1, 'LONGUEUR'].sum()),
                         metres_on_other_segments=round(g.loc[g['ARTERE'] == 0, 'LONGUEUR'].sum())))
with open(os.path.join(H, 'arterial_check.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('cycling facilities:', len(cyc), '; without a match in the arterial layer:', int(m['ARTERE'].isna().sum()))
for r in rows: print(r)
