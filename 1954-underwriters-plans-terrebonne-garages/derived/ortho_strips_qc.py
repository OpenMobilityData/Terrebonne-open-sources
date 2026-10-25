#!/usr/bin/env python3
"""Fetch, for each block of rue de Terrebonne, the Gouvernement du Québec continuous aerial
imagery (service Imagerie_Continue, layer Imagerie_GQ, WMS 1.1.1; the most recent imagery in the
provincial mosaic as served on the date of the run), and render it in the street frame with the
City's parcels and civic numbers and the 1954-55 reading overlaid, for the present-day check of
driveways and garage access. Images are written OUTSIDE the repository (OUTDIR), one per block,
plus the raw WMS tile. Usage: python3 ortho_strips_qc.py OUTDIR [--mpp 0.08]"""
import csv, json, math, os, sys, time, urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from frame import to_EN, from_EN, to_uv, from_uv, NODES, CUM
HERE = os.path.dirname(os.path.abspath(__file__))
WMS = 'https://servicesmatriciels.mern.gouv.qc.ca/erdas-iws/ogc/wms/Imagerie_Continue?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=Imagerie_GQ&STYLES=&SRS=EPSG:4326&FORMAT=image/jpeg&BBOX={w},{s},{e},{n}&WIDTH={W}&HEIGHT={H}'
UEV = json.load(open(os.path.join(HERE, 'city_assessment_units_terrebonne_bbox.geojson')))['features']
rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')) if r['u_m']]
font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14); fontb = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
MLON = 111320 * math.cos(math.radians(45.47)); MLAT = 111132
def fetch(lon0, lat0, lon1, lat1, mpp, path):
    W = int((lon1 - lon0) * MLON / mpp); H = int((lat1 - lat0) * MLAT / mpp)
    if not os.path.exists(path):
        url = WMS.format(w=f'{lon0:.6f}', s=f'{lat0:.6f}', e=f'{lon1:.6f}', n=f'{lat1:.6f}', W=W, H=H)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'})
        data = urllib.request.urlopen(req, timeout=180).read(); open(path, 'wb').write(data); time.sleep(0.5)
    return Image.open(path).convert('RGB'), (lon0, lat0, lon1, lat1, W, H)
def render(k, u0, u1, vmax, mpp, outdir, title):
    pts = [from_EN(*from_uv(u, v)) for u in (u0, u1) for v in (-vmax, vmax)]
    lon0, lon1 = min(p[0] for p in pts) - 0.00005, max(p[0] for p in pts) + 0.00005
    lat0, lat1 = min(p[1] for p in pts) - 0.00003, max(p[1] for p in pts) + 0.00003
    im, (a, b, c, d, W, H) = fetch(lon0, lat0, lon1, lat1, mpp, os.path.join(outdir, f'wms_block_{k:02d}.jpg'))
    arr = np.asarray(im); ppm = 1 / mpp
    Wo, Ho = int((u1 - u0) * ppm), int(2 * vmax * ppm)
    us = u0 + (np.arange(Wo) + 0.5) / ppm; vs = vmax - (np.arange(Ho) + 0.5) / ppm
    cols = np.zeros((Ho, Wo), int); rws = np.zeros((Ho, Wo), int)
    for j, u in enumerate(us):
        for i, v in enumerate(vs):
            lon, lat = from_EN(*from_uv(u, v)); cols[i, j] = int((lon - a) / (c - a) * W); rws[i, j] = int((d - lat) / (d - b) * H)
    ok = (cols >= 0) & (cols < W) & (rws >= 0) & (rws < H)
    o = np.full((Ho, Wo, 3), 180, np.uint8); o[ok] = arr[rws[ok], cols[ok]]
    out = Image.fromarray(o); dr = ImageDraw.Draw(out, 'RGBA')
    def P(u, v): return ((u - u0) * ppm, (vmax - v) * ppm)
    for f in UEV:
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]; p = f['properties']
        for poly in polys:
            pp = [to_uv(*to_EN(x, y)) for x, y in [(q[0], q[1]) for q in poly[0]]]
            if not any(u0 - 5 < u < u1 + 5 and -vmax < v < vmax for u, v in pp): continue
            dr.line([P(u, v) for u, v in pp] + [P(*pp[0])], fill=(0, 220, 255, 190), width=2)
        cu = sum(q[0] for q in pp) / len(pp); cv = sum(q[1] for q in pp) / len(pp)
        if u0 < cu < u1 and abs(cv) < vmax:
            lab = (p['CIVIQUE_DEBUT'] or '').strip(); fin = (p['CIVIQUE_FIN'] or '').strip()
            if fin != lab: lab += '-' + fin[-2:]
            st = (p['NOM_RUE'] or '').replace('(MTL)', '').replace('rue de Terrebonne', '').replace('avenue', '').replace('boulevard', '').strip()[:9]
            x, y = P(cu, cv); dr.rectangle([x - 2, y - 2, x + 64, y + 15], fill=(255, 255, 255, 180)); dr.text((x, y - 1), lab + (' ' + st if st else ''), fill=(0, 0, 0, 255), font=font)
    for r in rows:
        u, v = float(r['u_m']), float(r['v_m'])
        if u0 - 3 < u < u1 + 3 and abs(v) < vmax:
            x, y = P(u, v); col = {'yes': (40, 120, 255, 230), 'no': (240, 100, 40, 230)}.get(r['garage_1954'], (120, 120, 120, 230))
            dr.ellipse([x - 6, y - 6, x + 6, y + 6], fill=col, outline=(0, 0, 0, 255))
    dr.rectangle([0, 0, Wo, 22], fill=(255, 255, 255, 200)); dr.text((6, 3), title, fill=(0, 0, 0, 255), font=fontb)
    out.save(os.path.join(outdir, f'strip_block_{k:02d}.png'))
if __name__ == '__main__':
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    mpp = float(sys.argv[sys.argv.index('--mpp') + 1]) if '--mpp' in sys.argv else 0.08
    names = [n for _, _, n in NODES]
    for k in range(len(CUM) - 1):
        if CUM[k + 1] - CUM[k] < 20: continue
        a = names[k].split(';')[0].replace('Avenue ', '').replace('Boulevard ', ''); b = names[k + 1].split(';')[0].replace('Avenue ', '').replace('Boulevard ', '')
        title = f"{k:02d} {a} – {b}  (u {CUM[k]:.0f}–{CUM[k+1]:.0f} m; north above; Imagerie_GQ, Gouv. du Québec, fetched {time.strftime('%Y-%m-%d')})"
        render(k, CUM[k] - 14, CUM[k + 1] + 14, 40, mpp, outdir, title); print('block', k, a, b, flush=True)
