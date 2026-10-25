#!/usr/bin/env python3
"""Fit a similarity transform (scale, rotation, translation) for each 1954-55 sheet from
the control points in controls.csv (pixel position of each Terrebonne intersection on the
scan vs the City geobase coordinates of the same intersection), and write
sheet_transforms.json. Local metric frame: E = (lon-LON0)*M_LON, N = (lat-LAT0)*M_LAT.
Prints the residual of every control point. Usage: python3 georef.py [--check DIR]
(--check draws the City assessment-unit outlines on a downsized band of each sheet)."""
import csv, json, math, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
LON0, LAT0 = -73.6327, 45.4692
M_LON = 111320 * math.cos(math.radians(LAT0)); M_LAT = 111132
def to_EN(lon, lat): return ((lon - LON0) * M_LON, (lat - LAT0) * M_LAT)
def from_EN(E, N): return (E / M_LON + LON0, N / M_LAT + LAT0)
def fit(px, EN):
    """least-squares similarity: EN = s*R*px + t (Umeyama); px, EN: (n,2)"""
    px = np.asarray(px, float); EN = np.asarray(EN, float)
    mp, me = px.mean(0), EN.mean(0); P, Q = px - mp, EN - me
    H = P.T @ Q; U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T)); Dm = np.diag([1, d])
    R = Vt.T @ Dm @ U.T
    s = (S * [1, d]).sum() / (P ** 2).sum()
    t = me - s * R @ mp
    return s, R, t
def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 'controls.csv'))))
    sheets = {}
    for r in rows: sheets.setdefault(r['sheet'], []).append(r)
    out = {}
    for sh, rs in sheets.items():
        px = [(float(r['px']), float(r['py'])) for r in rs]
        EN = [to_EN(float(r['lon']), float(r['lat'])) for r in rs]
        if len(rs) == 2:  # exact similarity through two points
            (x1, y1), (x2, y2) = px; (E1, N1), (E2, N2) = EN
            s = math.hypot(E2 - E1, N2 - N1) / math.hypot(x2 - x1, y2 - y1)
            a = math.atan2(N2 - N1, E2 - E1) - math.atan2(-(y2 - y1), x2 - x1)
            # pixel y grows downward: use (x, -y)
            R = np.array([[math.cos(a), -math.sin(a)], [math.sin(a), math.cos(a)]])
            t = np.array([E1, N1]) - s * R @ np.array([x1, -y1])
        else:
            s, R, t = fit([(x, -y) for x, y in px], EN)
        res = []
        for (x, y), (E, N) in zip(px, EN):
            e = s * R @ np.array([x, -y]) + t; res.append(math.hypot(e[0] - E, e[1] - N))
        ang = math.degrees(math.atan2(R[1, 0], R[0, 0]))
        print(f"{sh:7} scale {1/s:6.2f} px/m  rot {ang:7.2f} deg  residuals m: " + ' '.join(f'{v:.1f}' for v in res))
        out[sh] = {'s': s, 'R': R.tolist(), 't': t.tolist(), 'px_per_m': 1 / s, 'rot_deg': ang,
                   'residuals_m': [round(v, 2) for v in res], 'streets': [r['street'] for r in rs]}
    json.dump({'frame': {'lon0': LON0, 'lat0': LAT0, 'm_lon': M_LON, 'm_lat': M_LAT}, 'sheets': out},
              open(os.path.join(HERE, 'sheet_transforms.json'), 'w'), indent=1)
    if '--check' in sys.argv:
        check(out, sys.argv[sys.argv.index('--check') + 1])
def check(tr, outdir):
    from PIL import Image, ImageDraw
    Image.MAX_IMAGE_PIXELS = None
    SRC = os.path.expanduser('~/Terrebonne-data/third-party/fire-insurance-plans-1954/174390_%s.jpg')
    uev = json.load(open(os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/unites-evaluation-fonciere/terrebonne_bbox_extract.geojson')))
    gb = json.load(open(os.path.join(os.path.dirname(HERE), '..', '..', 'Terrebonne-private', 'data/petition/terrebonne_lane_geobase.geojson')))
    os.makedirs(outdir, exist_ok=True)
    for sh, T in tr.items():
        s, R, t = T['s'], np.array(T['R']), np.array(T['t'])
        im = Image.open(SRC % sh).convert('RGB'); W, H = im.size; d = ImageDraw.Draw(im)
        Ri = np.linalg.inv(R)
        def to_px(lon, lat):
            E, N = to_EN(lon, lat); v = Ri @ ((np.array([E, N]) - t) / s); return (v[0], -v[1])
        for f in uev['features']:
            g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
            for poly in polys:
                pts = [to_px(*p[:2]) for p in poly[0]]
                if all(-500 < x < W + 500 and -500 < y < H + 500 for x, y in pts):
                    d.line(pts + [pts[0]], fill=(0, 120, 255), width=4)
        for f in gb['features']:
            c = f['geometry']['coordinates']; lines = c if f['geometry']['type'] == 'MultiLineString' else [c]
            for l in lines: d.line([to_px(*p[:2]) for p in l], fill=(255, 0, 0), width=6)
        im = im.resize((W // 3, H // 3), Image.LANCZOS); im.save(os.path.join(outdir, f'check_{sh}.png'))
        print('check', sh)
if __name__ == '__main__': main()
