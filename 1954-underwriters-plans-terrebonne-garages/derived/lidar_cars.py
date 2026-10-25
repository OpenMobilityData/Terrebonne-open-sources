#!/usr/bin/env python3
"""Count car-sized objects in the City's 2015 LiDAR along rue de Terrebonne: returns 0.9–2.3 m
above ground, not classified building or vegetation (pipeline_cars.json), rasterized at 0.25 m;
connected components of cells with >= 2 returns, kept when 5–17 m² with a 2.8–6.5 m long side and
a 1.4–3.0 m short side (a car; two cars touching are split by area), placed in the street frame and
classed: 'terrebonne_curb' (2.2 < |v| < 7 m, along the lane), 'cross_street' (within 6 m of a
cross-street centreline), 'lot' (the rest within 45 m of the street). Writes lidar_cars.csv (one
row per object: u, v, lon, lat, area, length, width, mean height, class, block, side) and
lidar_cars_by_block.csv. Usage: python3 lidar_cars.py"""
import csv, json, math, os
import numpy as np, tifffile
from scipy import ndimage
from frame import to_EN, from_EN, to_uv, from_uv, CUM, NODES, LENGTH
from mtm import mtm8
HERE = os.path.dirname(os.path.abspath(__file__))
LD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/lidar-aerien-2015/derived/')
def load(name):
    with tifffile.TiffFile(LD + name) as tf:
        a = tf.asarray().astype(np.float32); p = tf.pages[0]; sc = p.tags['ModelPixelScaleTag'].value; tie = p.tags['ModelTiepointTag'].value
    return a, (tie[3], tie[4], sc[0], sc[1])
CNT, G = load('corridor_carband_count_0p25m.tif'); MEAN, _ = load('corridor_carband_mean_0p25m.tif')
x0, y0, dx, dy = G
mask = CNT >= 2
mask = ndimage.binary_opening(mask, structure=np.ones((2, 2)))
lab, n = ndimage.label(mask, structure=np.ones((3, 3)))
print('components', n)
# cross-street centrelines (geobase) in E,N
GB = json.load(open(os.path.join(HERE, 'geobase_terrebonne_bbox.geojson')))['features']
cross = []
for f in GB:
    if 'Terrebonne' in (f['properties'].get('ODONYME') or ''): continue
    c = f['geometry']['coordinates']; lines = c if f['geometry']['type'] == 'MultiLineString' else [c]
    for l in lines:
        pts = [to_EN(p[0], p[1]) for p in l]; cross += list(zip(pts, pts[1:]))
def dist_to_cross(E, N):
    best = 1e9
    for (a, b) in cross:
        dx_, dy_ = b[0] - a[0], b[1] - a[1]; L2 = dx_ * dx_ + dy_ * dy_
        t = 0 if L2 == 0 else max(0, min(1, ((E - a[0]) * dx_ + (N - a[1]) * dy_) / L2))
        d = math.hypot(E - (a[0] + t * dx_), N - (a[1] + t * dy_))
        if d < best: best = d
    return best
# inverse MTM by local linearization around the corridor centre (good to < 2 cm over 3 km)
E0, N0 = to_EN(-73.6327, 45.4692); X0, Y0 = mtm8(-73.6327, 45.4692)
eps = 1e-5
from frame import FR
dX_dlon = (mtm8(-73.6327 + eps, 45.4692)[0] - X0) / eps; dX_dlat = (mtm8(-73.6327, 45.4692 + eps)[0] - X0) / eps
dY_dlon = (mtm8(-73.6327 + eps, 45.4692)[1] - Y0) / eps; dY_dlat = (mtm8(-73.6327, 45.4692 + eps)[1] - Y0) / eps
Minv = np.linalg.inv(np.array([[dX_dlon, dX_dlat], [dY_dlon, dY_dlat]]))
def mtm_to_lonlat(X, Y):
    v = Minv @ np.array([X - X0, Y - Y0]); return -73.6327 + v[0], 45.4692 + v[1]
objs = ndimage.find_objects(lab)
names = [n_.split(';')[0].replace('Avenue ', '').replace('Boulevard ', '') for _, _, n_ in NODES]
def block_of(u):
    for k in range(len(CUM) - 1):
        if CUM[k] <= u < CUM[k + 1]: return k
    return -1
out = []
for i, sl in enumerate(objs, 1):
    if sl is None: continue
    sub = lab[sl] == i; area = sub.sum() * dx * dy
    if area < 5 or area > 60: continue
    ys, xs = np.nonzero(sub); ys = ys + sl[0].start; xs = xs + sl[1].start
    # principal axes for length/width
    P = np.stack([xs * dx, -ys * dy], 1).astype(float); mu = P.mean(0); P -= mu
    w, V = np.linalg.eigh(np.cov(P.T)); proj = P @ V
    ext = proj.max(0) - proj.min(0); length, width = ext.max() + dx, ext.min() + dx
    if not (1.4 <= width <= 3.0): continue
    if 2.8 <= length <= 6.5 and area <= 17: pieces = [(0.0, length, area)]
    elif 6.5 < length <= 30 and area / length > 1.2:  # a row of cars parked bumper to bumper: split along the major axis
        n = max(2, round(length / 5.2)); step = length / n
        pieces = [((i + 0.5) * step - length / 2, step, area / n) for i in range(n)]
    else: continue
    ax_ = V[:, 1] if w[1] >= w[0] else V[:, 0]
    for off, plen, parea in pieces:
      cxm = mu[0] + off * ax_[0]; cym = mu[1] + off * ax_[1]
      cx = x0 + cxm + 0.5 * dx; cy = y0 + cym - 0.5 * dy
      length, area = plen, parea
      lon, lat = mtm_to_lonlat(cx, cy); E, N = to_EN(lon, lat); u, v = to_uv(E, N)
      # long axis in E,N: ax_ is in raster (x, -y) = (E, N) orientation; street direction at u
      E1, N1 = from_uv(u + 1, v); sd = math.atan2(N1 - N, E1 - E); ad = math.atan2(ax_[1], ax_[0])
      ang = (math.degrees(ad - sd) + 90) % 180 - 90
      if u < -5 or u > LENGTH + 5 or abs(v) > 45: continue
      h = float(np.nanmean(np.where(MEAN[sl][sub] > -9000, MEAN[sl][sub], np.nan)))
      if 2.2 < abs(v) < 7.0 and 0 <= u <= LENGTH: cls = 'terrebonne_curb'
      elif dist_to_cross(E, N) < 6.0: cls = 'cross_street'
      elif abs(v) <= 2.2: cls = 'terrebonne_lane'
      else: cls = 'lot'
      k = block_of(u)
      out.append({'u_m': round(u, 1), 'v_m': round(v, 1), 'lon': round(lon, 6), 'lat': round(lat, 6), 'area_m2': round(area, 1), 'length_m': round(length, 1), 'width_m': round(width, 1),
                  'mean_height_m': round(h, 2), 'axis_deg_from_street': round(ang, 1), 'class': cls, 'block': k, 'block_name': (names[k] + '–' + names[k + 1]) if 0 <= k < len(names) - 1 else '', 'side': 'N' if v > 0 else 'S'})
w = csv.DictWriter(open(os.path.join(HERE, 'lidar_cars.csv'), 'w', encoding='utf-8'), fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
import collections
tot = collections.Counter(o['class'] for o in out); print('objects kept', len(out), dict(tot))
byb = collections.OrderedDict()
for o in out:
    key = (o['block'], o['block_name']); byb.setdefault(key, collections.Counter())[(o['class'], o['side'])] += 1
with open(os.path.join(HERE, 'lidar_cars_by_block.csv'), 'w', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['block', 'block_name', 'curb_N', 'curb_S', 'lot_N', 'lot_S', 'cross_street', 'lane'])
    for (k, nm), c in sorted(byb.items()):
        w.writerow([k, nm, c[('terrebonne_curb', 'N')], c[('terrebonne_curb', 'S')], c[('lot', 'N')], c[('lot', 'S')], c[('cross_street', 'N')] + c[('cross_street', 'S')], c[('terrebonne_lane', 'N')] + c[('terrebonne_lane', 'S')]])
print('curb N', sum(1 for o in out if o['class'] == 'terrebonne_curb' and o['side'] == 'N'), 'curb S', sum(1 for o in out if o['class'] == 'terrebonne_curb' and o['side'] == 'S'))
print('curb west of Cavendish N/S:', sum(1 for o in out if o['class'] == 'terrebonne_curb' and o['u_m'] < 891 and o['side'] == 'N'), sum(1 for o in out if o['class'] == 'terrebonne_curb' and o['u_m'] < 891 and o['side'] == 'S'))
