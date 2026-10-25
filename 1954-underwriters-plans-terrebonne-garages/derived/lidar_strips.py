#!/usr/bin/env python3
"""Render, for each block of rue de Terrebonne, strips in the street frame from the City's 2015
airborne LiDAR (open data, CC-BY 4.0; six 1 km tiles, NAD83(CSRS)/MTM 8), rasterized by pdal
(pipeline_corridor.json, pipeline_ground.json in the data folder): left, height above ground
(nDSM, 0.2 m, max) with a hillshade of the surface; right, the mean intensity of ground returns
(0.25 m; pavement and roofs reflect differently from lawn) with the ground elevation contours.
The City's parcels and the 1954-55 reading are overlaid as in ortho_strips_qc.py.
Rasters live outside the repository; strips are written to OUTDIR.
Usage: python3 lidar_strips.py OUTDIR"""
import csv, json, math, os, sys
import numpy as np, tifffile
from PIL import Image, ImageDraw, ImageFont
from frame import to_EN, from_EN, to_uv, from_uv, NODES, CUM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mtm import mtm8
HERE = os.path.dirname(os.path.abspath(__file__))
LD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/lidar-aerien-2015/derived/')
def load(name):
    with tifffile.TiffFile(LD + name) as tf:
        a = tf.asarray().astype(np.float32); p = tf.pages[0]
        scale = p.tags['ModelPixelScaleTag'].value; tie = p.tags['ModelTiepointTag'].value
    return a, (tie[3], tie[4], scale[0], scale[1])  # x0 (left), y0 (top), dx, dy
NDSM, G1 = load('corridor_ndsm_max_0p2m.tif'); DSM, _ = load('corridor_dsm_max_0p2m.tif')
INT, G2 = load('corridor_ground_intensity_0p25m.tif'); DTM, _ = load('corridor_dtm_mean_0p25m.tif')
for a in (NDSM, DSM, INT, DTM): a[a <= -9998] = np.nan
# hillshade of the DSM
def hillshade(z, dx, az=315, alt=45):
    z = np.where(np.isnan(z), np.nanmin(z), z)
    gy, gx = np.gradient(z, dx); slope = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
    a, b = math.radians(az), math.radians(alt)
    return np.clip(math.sin(b) * np.cos(slope) + math.cos(b) * np.sin(slope) * np.cos(a - asp), 0, 1)
HS = hillshade(DSM, G1[2])
UEV = json.load(open(os.path.join(HERE, 'city_assessment_units_terrebonne_bbox.geojson')))['features']
rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')) if r['u_m']]
font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 13); fontb = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
def sample(arr, G, X, Y):
    x0, y0, dx, dy = G; c = ((X - x0) / dx).astype(int); r = ((y0 - Y) / dy).astype(int)
    ok = (c >= 0) & (c < arr.shape[1]) & (r >= 0) & (r < arr.shape[0]); out = np.full(X.shape, np.nan, np.float32); out[ok] = arr[r[ok], c[ok]]; return out
def colorize_ndsm(h, hs):
    # 0 m pale, 0.5–3.5 m (garages, cars, fences) amber, 3.5–12 m (houses) blue-grey, trees (>12) dark green; shaded
    rgb = np.zeros(h.shape + (3,), np.float32); hh = np.nan_to_num(h, nan=0)
    low = np.clip(hh / 0.5, 0, 1); mid = np.clip((hh - 0.5) / 3, 0, 1); high = np.clip((hh - 3.5) / 8.5, 0, 1)
    base = np.array([0.95, 0.94, 0.90]); amber = np.array([0.95, 0.62, 0.15]); bld = np.array([0.45, 0.55, 0.70]); tree = np.array([0.20, 0.45, 0.25])
    rgb[:] = base; rgb = rgb * (1 - low[..., None]) + amber * low[..., None]
    rgb = rgb * (1 - mid[..., None]) + bld * mid[..., None]; rgb = rgb * (1 - high[..., None]) + tree * high[..., None]
    rgb *= (0.55 + 0.45 * np.nan_to_num(hs, nan=0.5))[..., None]
    return (np.clip(rgb, 0, 1) * 255).astype(np.uint8)
def render(k, u0, u1, vmax, ppm, outdir, title):
    Wo, Ho = int((u1 - u0) * ppm), int(2 * vmax * ppm)
    us = u0 + (np.arange(Wo) + 0.5) / ppm; vs = vmax - (np.arange(Ho) + 0.5) / ppm
    X = np.zeros((Ho, Wo)); Y = np.zeros((Ho, Wo))
    for j, u in enumerate(us):
        for i, v in enumerate(vs):
            lon, lat = from_EN(*from_uv(u, v)); X[i, j], Y[i, j] = mtm8(lon, lat)
    h = sample(NDSM, G1, X, Y); hs = sample(HS, G1, X, Y); it = sample(INT, G2, X, Y); dt = sample(DTM, G2, X, Y)
    left = colorize_ndsm(h, hs)
    lo, hi = np.nanpercentile(it, 2), np.nanpercentile(it, 98); g = np.clip((np.nan_to_num(it, nan=lo) - lo) / (hi - lo + 1e-6), 0, 1)
    right = np.repeat((g * 255).astype(np.uint8)[..., None], 3, axis=2)
    # ground contours every 0.25 m on the intensity panel (ramps to basement garages show as tight contours)
    if np.isfinite(dt).any():
        q = np.floor(np.nan_to_num(dt, nan=0) / 0.25); edge = (np.diff(q, axis=0, prepend=q[:1]) != 0) | (np.diff(q, axis=1, prepend=q[:, :1]) != 0)
        right[edge] = (255, 140, 0)
    im = Image.new('RGB', (Wo, 2 * Ho + 30), (255, 255, 255)); im.paste(Image.fromarray(left), (0, 24)); im.paste(Image.fromarray(right), (0, Ho + 30))
    dr = ImageDraw.Draw(im, 'RGBA')
    def P(u, v, panel): return ((u - u0) * ppm, (vmax - v) * ppm + (24 if panel == 0 else Ho + 30))
    for panel in (0, 1):
        for f in UEV:
            g_ = f['geometry']; polys = g_['coordinates'] if g_['type'] == 'MultiPolygon' else [g_['coordinates']]; p = f['properties']
            for poly in polys:
                pp = [to_uv(*to_EN(x, y)) for x, y in [(q[0], q[1]) for q in poly[0]]]
                if not any(u0 - 5 < u < u1 + 5 and -vmax < v < vmax for u, v in pp): continue
                dr.line([P(u, v, panel) for u, v in pp] + [P(pp[0][0], pp[0][1], panel)], fill=(0, 200, 255, 170), width=1)
            cu = sum(q[0] for q in pp) / len(pp); cv = sum(q[1] for q in pp) / len(pp)
            if panel == 0 and u0 < cu < u1 and abs(cv) < vmax:
                lab = (p['CIVIQUE_DEBUT'] or '').strip(); fin = (p['CIVIQUE_FIN'] or '').strip()
                if fin != lab: lab += '-' + fin[-2:]
                st = (p['NOM_RUE'] or '').replace('(MTL)', '').replace('rue de Terrebonne', '').replace('avenue', '').replace('boulevard', '').strip()[:9]
                x, y = P(cu, cv, 0); dr.rectangle([x - 2, y - 2, x + 60, y + 14], fill=(255, 255, 255, 170)); dr.text((x, y - 1), lab + (' ' + st if st else ''), fill=(0, 0, 0, 255), font=font)
        for r in rows:
            u, v = float(r['u_m']), float(r['v_m'])
            if u0 - 3 < u < u1 + 3 and abs(v) < vmax:
                x, y = P(u, v, panel); col = {'yes': (40, 120, 255, 230), 'no': (240, 100, 40, 230)}.get(r['garage_1954'], (120, 120, 120, 230))
                dr.ellipse([x - 5, y - 5, x + 5, y + 5], fill=col, outline=(0, 0, 0, 255))
    dr.rectangle([0, 0, Wo, 22], fill=(255, 255, 255, 255)); dr.text((6, 3), title, fill=(0, 0, 0, 255), font=fontb)
    dr.text((6, Ho + 26 - 14), 'ground-return intensity (0.25 m) with 0.25 m ground contours', fill=(0, 0, 0, 255), font=font)
    im.save(os.path.join(outdir, f'lidar_block_{k:02d}.png'))
if __name__ == '__main__':
    outdir = sys.argv[1]; os.makedirs(outdir, exist_ok=True)
    names = [n for _, _, n in NODES]
    for k in range(len(CUM) - 1):
        if CUM[k + 1] - CUM[k] < 20: continue
        a = names[k].split(';')[0].replace('Avenue ', '').replace('Boulevard ', ''); b = names[k + 1].split(';')[0].replace('Avenue ', '').replace('Boulevard ', '')
        title = f"{k:02d} {a} – {b}  (u {CUM[k]:.0f}–{CUM[k+1]:.0f} m; north above; City LiDAR 2015: height above ground, amber 0.5–3.5 m = garages/cars/fences, blue-grey = houses)"
        render(k, CUM[k] - 14, CUM[k + 1] + 14, 40, 8.0, outdir, title); print('block', k, flush=True)
