#!/usr/bin/env python3
"""Render, for each block of rue de Terrebonne, a strip of the City's 2022 orthophoto
(open data « Surfaces minérales et végétales 2022 », orthophoto layer, 30 cm pixels, CC-BY 4.0;
NAD83 / MTM zone 8 from its world file) in the street frame, with the City's parcels and civic
numbers overlaid, to read driveways and parking pads building by building.
Usage: python3 ortho_strips.py OUTDIR [--ppm 10]"""
import csv, json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
Image.MAX_IMAGE_PIXELS = None
from frame import to_EN, from_EN, to_uv, from_uv, LENGTH, STREET_U, NODES, CUM
HERE = os.path.dirname(os.path.abspath(__file__))
ORTHO = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/surfaces-minerales-vegetales-2022/ortho_cdn-ndg_2022')
# --- Transverse Mercator forward (GRS80), MTM zone 8: lon0 = -73.5, k0 = 0.9999, FE = 304800, FN = 0 ---
A = 6378137.0; F = 1 / 298.257222101; E2 = F * (2 - F); EP2 = E2 / (1 - E2)
def mtm8(lon, lat):
    lon0 = math.radians(-73.5); k0 = 0.9999
    phi = math.radians(lat); lam = math.radians(lon) - lon0
    N = A / math.sqrt(1 - E2 * math.sin(phi) ** 2); T = math.tan(phi) ** 2; C = EP2 * math.cos(phi) ** 2; Aa = math.cos(phi) * lam
    e4, e6 = E2 ** 2, E2 ** 3
    M = A * ((1 - E2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi - (3 * E2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * math.sin(2 * phi)
             + (15 * e4 / 256 + 45 * e6 / 1024) * math.sin(4 * phi) - (35 * e6 / 3072) * math.sin(6 * phi))
    x = 304800 + k0 * N * (Aa + (1 - T + C) * Aa ** 3 / 6 + (5 - 18 * T + T * T + 72 * C - 58 * EP2) * Aa ** 5 / 120)
    y = k0 * (M + N * math.tan(phi) * (Aa ** 2 / 2 + (5 - T + 9 * C + 4 * C * C) * Aa ** 4 / 24 + (61 - 58 * T + T * T + 600 * C - 330 * EP2) * Aa ** 6 / 720))
    return x, y
tfw = [float(v) for v in open(ORTHO + '.tfw').read().split()]
PX, PY, X0, Y0 = tfw[0], tfw[3], tfw[4], tfw[5]
img = Image.open(ORTHO + '.tif'); img.load(); W, H = img.size; print('ortho', img.size, img.mode)
arr = np.asarray(img.convert('RGB'))
def to_pix(lon, lat):
    x, y = mtm8(lon, lat); return (x - X0) / PX, (y - Y0) / PY
UEV = json.load(open(os.path.join(HERE, 'city_assessment_units_terrebonne_bbox.geojson')))['features']
rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')) if r['u_m']]
font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 13); fontb = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
def render(u0, u1, vmax, ppm, out, title):
    Wo, Ho = int((u1 - u0) * ppm), int(2 * vmax * ppm)
    us = u0 + (np.arange(Wo) + 0.5) / ppm; vs = vmax - (np.arange(Ho) + 0.5) / ppm
    cols = np.zeros((Ho, Wo), int); rws = np.zeros((Ho, Wo), int)
    for j, u in enumerate(us):
        for i, v in enumerate(vs):
            E, N = from_uv(u, v); lon, lat = from_EN(E, N); c, r = to_pix(lon, lat); cols[i, j] = int(c); rws[i, j] = int(r)
    ok = (cols >= 0) & (cols < W) & (rws >= 0) & (rws < H)
    o = np.full((Ho, Wo, 3), 200, np.uint8); o[ok] = arr[rws[ok], cols[ok]]
    im = Image.fromarray(o); d = ImageDraw.Draw(im, 'RGBA')
    def P(u, v): return ((u - u0) * ppm, (vmax - v) * ppm)
    for f in UEV:
        g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        p = f['properties']
        for poly in polys:
            pts = [to_uv(*to_EN(x, y)) for x, y in [(q[0], q[1]) for q in poly[0]]]
            if not any(u0 - 5 < u < u1 + 5 and -vmax < v < vmax for u, v in pts): continue
            d.line([P(u, v) for u, v in pts] + [P(*pts[0])], fill=(0, 200, 255, 200), width=2)
        cu = sum(q[0] for q in pts) / len(pts); cv = sum(q[1] for q in pts) / len(pts)
        if u0 < cu < u1 and abs(cv) < vmax:
            lab = (p['CIVIQUE_DEBUT'] or '').strip() + ('' if (p['CIVIQUE_FIN'] or '').strip() == (p['CIVIQUE_DEBUT'] or '').strip() else '-' + (p['CIVIQUE_FIN'] or '').strip()[-2:])
            st = (p['NOM_RUE'] or '').replace('(MTL)', '').replace('rue de Terrebonne', 'T').replace('avenue', '').replace('boulevard', '').strip()[:8]
            x, y = P(cu, cv); d.rectangle([x - 2, y - 2, x + 60, y + 14], fill=(255, 255, 255, 170)); d.text((x, y - 1), lab + ('' if st == 'T' else ' ' + st), fill=(0, 0, 0, 255), font=font)
    for r in rows:
        u, v = float(r['u_m']), float(r['v_m'])
        if u0 - 3 < u < u1 + 3 and abs(v) < vmax:
            x, y = P(u, v); col = {'yes': (40, 120, 255, 230), 'no': (240, 100, 40, 230)}.get(r['garage_1954'], (120, 120, 120, 230))
            d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col, outline=(0, 0, 0, 255))
    d.line([P(u0, 0), P(u1, 0)], fill=(255, 255, 0, 120), width=1)
    d.rectangle([0, 0, Wo, 22], fill=(255, 255, 255, 200)); d.text((6, 3), title, fill=(0, 0, 0, 255), font=fontb)
    im.save(out)
if __name__ == '__main__':
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    ppm = float(sys.argv[sys.argv.index('--ppm') + 1]) if '--ppm' in sys.argv else 10.0
    names = [n for _, _, n in NODES]
    for k in range(len(CUM) - 1):
        if CUM[k + 1] - CUM[k] < 20: continue
        a, b = names[k].split(';')[0].replace('Avenue ', '').replace('Boulevard ', ''), names[k + 1].split(';')[0].replace('Avenue ', '').replace('Boulevard ', '')
        title = f"{k:02d} {a} – {b}  (u {CUM[k]:.0f}–{CUM[k+1]:.0f} m; north side above; 2022 orthophoto, Ville de Montréal CC-BY 4.0)"
        render(CUM[k] - 12, CUM[k + 1] + 12, 42, ppm, os.path.join(outdir, f'block_{k:02d}.png'), title); print('block', k, a, b)
