#!/usr/bin/env /opt/local/bin/python3.13
"""Where each counter stands on rue de Terrebonne: position along the street, distance to downtown, and the resident
population around it (2021 Census, dissemination areas, area-weighted within RADIUS metres).

Sources: counter positions from the City's géobase intersections (as in Terrebonne-access-requests
2026-300/derived/terrebonne_sector.py); Statistics Canada, 2021 Census, dissemination-area boundary file
lda_000a21a_e and Census Profile 98-401-X2021006 (Statistics Canada Open Licence), read from
~/Terrebonne-data/third-party/statcan-census-2021/ (not redistributed).
Downtown reference point: avenue McGill College at rue Sainte-Catherine Ouest (45.5019, -73.5714).

Output: derived/tables/location_context.csv        Usage: /opt/local/bin/python3.13 scripts/location_context.py
"""
import os, csv, math
import geopandas as gpd, pandas as pd
from shapely.geometry import Point
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
C = os.path.expanduser('~/Terrebonne-data/third-party/statcan-census-2021')
SHP = os.path.join(C, 'boundaries/lda_000a21a_e/lda_000a21a_e.shp')
PROFILE = os.path.join(C, '98-401-X2021006_Quebec_DA/98-401-X2021006_English_CSV_data_Quebec.csv')
INDEX = os.path.join(C, '98-401-X2021006_Quebec_DA/98-401-X2021006_Geo_starting_row_Quebec.CSV')
RADIUS = 500.0; WEST_END = (45.45974, -73.64080); DOWNTOWN = (45.5019, -73.5714)
SITES = [('west', 'King Edward', 45.46354, -73.63784, 'westbound', 'CDN-301', 'Loyola'), ('loop', 'Kensington loop', 45.47022, -73.63204, 'eastbound', 'CDN-301', 'Notre-Dame-de-Grâce'),
         ('bixi', 'BIXI station (Grand Boulevard)', 45.47054, -73.63166, 'eastbound', 'CDN-301', 'Notre-Dame-de-Grâce'), ('east', 'Draper', 45.47405, -73.62872, 'eastbound', 'CDN-111', 'Notre-Dame-de-Grâce'),
         ('gir', 'Girouard detector', 45.47833, -73.62487, 'eastbound', 'CDN-111', 'Notre-Dame-de-Grâce')]

def km(a, b):
    return math.hypot((a[0] - b[0]) * 111.2, (a[1] - b[1]) * 111.2 * math.cos(math.radians(45.47)))

crs = gpd.read_file(SHP, rows=1).crs
pts = gpd.GeoSeries([Point(lon, lat) for _, _, lat, lon, _, _, _ in SITES], crs=4326).to_crs(crs)
da = gpd.read_file(SHP, mask=pts.buffer(RADIUS + 50).union_all())
ids = set(da['DGUID']); start = {}
for r in csv.DictReader(open(INDEX, encoding='latin-1')):
    if r['Geo Code'] in ids: start[int(r['Line Number'])] = r['Geo Code']
wanted = {ln + k: g for ln, g in start.items() for k in range(8)}; pop = {}
with open(PROFILE, encoding='latin-1') as fh:
    for n, line in enumerate(fh, 1):
        if n in wanted:
            r = next(csv.reader([line]))
            if len(r) >= 12 and r[1] == wanted[n] and r[8] == '1':
                try: pop[r[1]] = float(r[11])
                except ValueError: pass
        if n > max(wanted): break
da['pop'] = da['DGUID'].map(pop); rows = []
for (slug, name, lat, lon, way, sector, district), p in zip(SITES, pts):
    buf = p.buffer(RADIUS); inter = da[da.intersects(buf)].copy()
    share = inter.geometry.intersection(buf).area / inter.geometry.area
    people = float((inter['pop'].fillna(0) * share).sum()); area_km2 = buf.area / 1e6
    rows.append({'series': slug, 'location': name, 'latitude': lat, 'longitude': lon, 'km_from_lane_west_end': round(km((lat, lon), WEST_END), 2),
                 'km_to_downtown_reference': round(km((lat, lon), DOWNTOWN), 1), 'motor_traffic_one_way': way, 'snow_sector_2025_26': sector, 'borough_district': district,
                 'residents_within_500m_2021': int(round(people, -1)), 'residents_per_km2_within_500m': int(round(people / area_km2, -2)), 'dissemination_areas_touched': int(len(inter))})
t = pd.DataFrame(rows); t.to_csv(os.path.join(ROOT, 'derived', 'tables', 'location_context.csv'), index=False); print(t.to_string())
