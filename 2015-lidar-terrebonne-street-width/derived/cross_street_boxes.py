#!/usr/bin/env python3
"""The comparison in one picture: rue de Terrebonne and one cross street from above, with three boxes drawn to scale.
  blue   11.0 m  Terrebonne from curb to curb (LiDAR 2015, this folder; the block's median, centred on the measured roadway centre)
  red     8.5 m  the part of Terrebonne from the curb opposite the contraflow lane to that lane's buffer: where the winter
                 layout puts two parking bands and the lane shared by cars and bicycles (11.0 m less the 2.0 m contraflow
                 lane and its 0.5 m buffer; EXP 2023 Fig. 6-6 draws 2.4 + 3.5 + 2.4 = 8.3 m in a 10.8 m section)
  green   the cross street from curb to curb (the block's most frequent reading, centred on the measured roadway centre)
The same 11.0 m and 8.5 m boxes are repeated on the cross street: the first overshoots its curbs, the second leaves room.
Background: the Gouvernement du Québec's aerial imagery (service Imagerie_Continue, layer Imagerie_GQ, WMS, fetched when the
script runs; the tile is kept outside the repository), and/or the LiDAR 2015 ground surface (hillshade, 0.25 m).
Usage: /opt/local/bin/python3.13 cross_street_boxes.py [--street Kensington] [--half 70] [--mpp 0.08] [--bg wms|lidar|both]
       [--to-next N|S]   (extend the frame along the cross street's whole block on that side, label the streets, and repeat the
                          green box near the far end; e.g. --street Marcil --to-next N shows Marcil from Terrebonne to Monkland)
Writes figures/cross_street_boxes[_<street>][_lidar]_{en,fr}.png (Kensington's optical pair keeps the plain name used by the note and
deck) and cross_street_boxes_<street>.json (the numbers drawn)."""
import argparse, csv, json, math, os, sys, time, urllib.request
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures')
G54 = os.path.join(os.path.dirname(os.path.dirname(HERE)), '1954-underwriters-plans-terrebonne-garages', 'derived'); sys.path.insert(0, G54)
import frame as FR; from mtm import mtm8
ap = argparse.ArgumentParser(); ap.add_argument('--street', default='Kensington'); ap.add_argument('--half', type=float, default=70.0)
ap.add_argument('--mpp', type=float, default=0.08); ap.add_argument('--no-wms', action='store_true'); ap.add_argument('--bg', choices=['wms', 'lidar', 'both'], default='wms')
ap.add_argument('--to-next', choices=['N', 'S'], default=None); ap.add_argument('--next-name', default=None, help='name of the street at the far end of the block (label)'); ap.add_argument('--contraflow', type=float, default=2.5, help='contraflow lane + buffer, m')
A = ap.parse_args()
if A.no_wms: A.bg = 'lidar'
KINDS = ['wms', 'lidar'] if A.bg == 'both' else [A.bg]
TERR_W, RESID = 11.0, round(11.0 - A.contraflow, 1)

# ---------- the intersection node and the street directions
node_i = next(i for i, (lon, lat, names) in enumerate(FR.NODES) if A.street in names)
lon0, lat0 = FR.NODES[node_i][0], FR.NODES[node_i][1]; E0, N0 = FR.to_EN(lon0, lat0)
# Terrebonne's direction at the node (mean of the two adjacent legs)
def unit(a, b): d = (b[0] - a[0], b[1] - a[1]); L = math.hypot(*d); return (d[0] / L, d[1] / L)
P = FR.P; t1 = unit(P[node_i - 1], P[node_i]); t2 = unit(P[node_i], P[node_i + 1]); tT = unit((0, 0), (t1[0] + t2[0], t1[1] + t2[1]))
nT = (-tT[1], tT[0])   # left of travel (west→east) = north side
u_node = FR.CUM[node_i]
# the cross street's blocks (from cross_street_blocks.csv / profile) and their axes from the géobase
blocks = [b for b in csv.DictReader(open(os.path.join(HERE, 'cross_street_blocks.csv'), encoding='utf-8')) if b['street'] == A.street]
prof_x = [r for r in csv.DictReader(open(os.path.join(HERE, 'cross_street_profile.csv'), encoding='utf-8')) if r['street'] == A.street and r['kept'] == '1']
prof_t = [r for r in csv.DictReader(open(os.path.join(HERE, 'street_width_profile.csv'), encoding='utf-8')) if r['kept'] == '1']
GB = json.load(open(os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/geobase_2026-10-14.json'), encoding='utf-8'))['features']
seg = {f['properties']['ID_TRC']: f for f in GB}
def pick(rows, key, target, tol):
    best = min(rows, key=lambda r: abs(float(r[key]) - target)); return best if abs(float(best[key]) - target) <= tol else None
def typical(rows, key, target, tol, kN, kS, width):
    """the box to draw near `target`: the block's typical width (`width`, the block median for Terrebonne, the most frequent reading for a
    cross street) centred on the median roadway centre of the kept stations within `tol` m (a single station can sit on a driveway apron)"""
    win = [r for r in rows if abs(float(r[key]) - target) <= tol]
    off = float(np.median([(float(r[kN]) - float(r[kS])) / 2 for r in win])) if win else 0.0
    return width / 2 + off, width / 2 - off      # curb offsets (left/north, right/south) that give the typical width about the measured centre
BT = {b['block']: b for b in csv.DictReader(open(os.path.join(HERE, 'street_width_by_block.csv'), encoding='utf-8'))}

# ---------- the boxes (metres from the node; +E east, +N north)
def rect(centre, along, across, length_across, length_along):
    """corners of a box centred at `centre`, `length_across` long in the `across` direction, `length_along` in `along`"""
    cx, cy = centre; ax_, ay_ = along; bx, by = across
    return [(cx + s * length_along / 2 * ax_ + t * length_across / 2 * bx, cy + s * length_along / 2 * ay_ + t * length_across / 2 * by) for s, t in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
def shift(centre, direction, d): return (centre[0] + d * direction[0], centre[1] + d * direction[1])
BOXES = []   # (corners, colour, label, label_pos)
C_T, C_R, C_X = '#2a78d6', '#e34948', '#1baf7a'
# Terrebonne: a station 26 m west of the node, curbs from the profile; the 11.0 box from curb to curb, the residual box from the south curb (east of Cavendish the contraflow lane is on the north side)
offs = []
for d_along, sign in ((-26.0, -1), (26.0, 1)):
    st = pick(prof_t, 'u', u_node + d_along, 6.0); blk = BT.get(st['block']) if st else None
    cn, cs = typical(prof_t, 'u', u_node + d_along, 15.0, 'curb_N', 'curb_S', float(blk['curb_median']) if blk else TERR_W)
    axis_pt = (d_along * tT[0], d_along * tT[1])      # on the géobase axis
    centre = shift(axis_pt, nT, (cn - cs) / 2)         # the roadway's centre
    BOXES.append((rect(centre, tT, nT, cn + cs, 7.0), C_T, f'{cn + cs:.1f} m', 'T'))
    south_curb = shift(axis_pt, nT, -cs); c2 = shift(shift(south_curb, nT, RESID / 2), tT, sign * 8.0)
    BOXES.append((rect(c2, tT, nT, RESID, 7.0), C_R, f'{RESID:.1f} m', 'T'))
    offs.append(cn + cs)
# the cross street: north and south blocks, a station 30 m from the node, the curbs from its profile; then the two Terrebonne boxes repeated
for b in blocks:
    f = seg[int(b['id_trc'])]; cs_ = [FR.to_EN(c[0], c[1]) for c in f['geometry']['coordinates']]
    if math.hypot(cs_[-1][0] - E0, cs_[-1][1] - N0) < math.hypot(cs_[0][0] - E0, cs_[0][1] - N0): cs_ = cs_[::-1]
    tX = unit(cs_[0], cs_[1]); nX = (-tX[1], tX[0])    # along = away from Terrebonne; across = left of that
    rs = [r for r in prof_x if r['id_trc'] == b['id_trc']]
    cl, cr = typical(rs, 'dist_from_terrebonne', 30.0, 15.0, 'curb_L', 'curb_R', float(b['curb_mode']))
    d0 = 30.0; axis_pt = (cs_[0][0] - E0 + d0 * tX[0], cs_[0][1] - N0 + d0 * tX[1]); centre = shift(axis_pt, nX, (cl - cr) / 2)
    BOXES.append((rect(centre, tX, nX, cl + cr, 7.0), C_X, f'{cl + cr:.1f} m', 'X'))
    BOXES.append((rect(shift(centre, tX, 8.0), tX, nX, TERR_W, 7.0), C_T, f'{TERR_W:.1f} m', 'X'))
    BOXES.append((rect(shift(centre, tX, 16.0), tX, nX, RESID, 7.0), C_R, f'{RESID:.1f} m', 'X'))
    offs.append(cl + cr)

# ---------- the frame: the node ± half, extended along the chosen block to its far end
xmin, xmax, ymin, ymax = -A.half, A.half, -A.half, A.half; LABELS = []   # (x, y, text, angle)
def ang_of(t):
    a = math.degrees(math.atan2(t[1], t[0]))
    return a - 180 if a > 90 else (a + 180 if a < -90 else a)
if A.to_next:
    b = next(b for b in blocks if b['side'] == A.to_next)
    f = seg[int(b['id_trc'])]; cs_ = [FR.to_EN(c[0], c[1]) for c in f['geometry']['coordinates']]
    if math.hypot(cs_[-1][0] - E0, cs_[-1][1] - N0) < math.hypot(cs_[0][0] - E0, cs_[0][1] - N0): cs_ = cs_[::-1]
    far = (cs_[-1][0] - E0, cs_[-1][1] - N0); tX = unit(cs_[0], cs_[1]); tF = unit(cs_[-2], cs_[-1]); nX = (-tX[1], tX[0])
    M = 40.0; xmin, xmax = min(xmin, far[0] - M), max(xmax, far[0] + M); ymin, ymax = min(ymin, far[1] - M), max(ymax, far[1] + M)
    # the green box again near the far end, inside the measured length
    d1 = float(b['measured_to_m']) - 30.0; rs = [r for r in prof_x if r['id_trc'] == b['id_trc']]
    cl, cr = typical(rs, 'dist_from_terrebonne', d1, 15.0, 'curb_L', 'curb_R', float(b['curb_mode']))
    # the point d1 along the géobase polyline
    acc = 0.0; pt = None; tl = tX
    for a_, b_ in zip(cs_, cs_[1:]):
        L = math.hypot(b_[0] - a_[0], b_[1] - a_[1])
        if acc + L >= d1: tl = unit(a_, b_); q = (d1 - acc) / L; pt = (a_[0] + q * (b_[0] - a_[0]) - E0, a_[1] + q * (b_[1] - a_[1]) - N0); break
        acc += L
    nl = (-tl[1], tl[0]); centre = shift(pt, nl, (cl - cr) / 2)
    BOXES.append((rect(centre, tl, nl, cl + cr, 7.0), C_X, f'{cl + cr:.1f} m', 'X')); offs.append(cl + cr)
    FAR_BOX = dict(dist_from_terrebonne=d1, width=round(cl + cr, 2))
    # street names
    mid = (far[0] * 0.5, far[1] * 0.5); LABELS.append((*shift(mid, nX, 9.0), f'avenue {A.street}', ang_of(tX)))
    if A.next_name: LABELS.append((*shift(shift(far, tF, 4.0), (-tF[1], tF[0]), -0.0), A.next_name, ang_of((-tF[1], tF[0]))))
    LABELS.append((*shift((80 * tT[0], 80 * tT[1]), nT, 10.0), 'rue de Terrebonne', ang_of(tT)))
else: FAR_BOX = None
xmin, xmax, ymin, ymax = [round(v) for v in (xmin, xmax, ymin, ymax)]

# ---------- backgrounds
def bg_wms():
    W, H = int(round((xmax - xmin) / A.mpp)), int(round((ymax - ymin) / A.mpp))
    lonW, lonE = lon0 + xmin / FR.FR['m_lon'], lon0 + xmax / FR.FR['m_lon']; latS, latN = lat0 + ymin / FR.FR['m_lat'], lat0 + ymax / FR.FR['m_lat']
    QDIR = os.path.expanduser('~/Terrebonne-data/third-party/quebec-imagerie/intersections/'); os.makedirs(QDIR, exist_ok=True)
    name = A.street.lower().replace(chr(39), '')
    tile = os.path.join(QDIR, f'wms_{name}_{A.half:.0f}m_{A.mpp}.jpg' if (xmin, xmax, ymin, ymax) == (-A.half, A.half, -A.half, A.half)
                        else f'wms_{name}_{xmin}_{xmax}_{ymin}_{ymax}_{A.mpp}.jpg')
    if not os.path.exists(tile):
        url = ('https://servicesmatriciels.mern.gouv.qc.ca/erdas-iws/ogc/wms/Imagerie_Continue?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=Imagerie_GQ'
               f'&STYLES=&SRS=EPSG:4326&FORMAT=image/jpeg&BBOX={lonW:.7f},{latS:.7f},{lonE:.7f},{latN:.7f}&WIDTH={W}&HEIGHT={H}')
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as r, open(tile, 'wb') as f: f.write(r.read())
            open(tile + '.txt', 'w').write(f'{url}\nfetched {time.strftime("%Y-%m-%d %H:%M")}\n')
        except Exception as e: print('WMS failed:', e)
    if os.path.exists(tile) and os.path.getsize(tile) > 20000:
        from PIL import Image; return np.asarray(Image.open(tile).convert('RGB')), 'upper', None
    return None
def bg_lidar():
    import rasterio
    LD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/lidar-aerien-2015/derived/')
    with rasterio.open(LD + 'corridor_dtm_mean_0p25m.tif') as ds:
        a = ds.read(1).astype(np.float32); tr = ds.transform
    a[a <= -9998] = np.nan; x0, y0, dx, dy = tr.c, tr.f, tr.a, -tr.e
    # local metres → MTM-8: an affine fit on the frame's corners and centre (exact to well under a centimetre over a few hundred metres)
    pts = [(xmin, ymin), (xmax, ymin), (xmin, ymax), (xmax, ymax), (0.0, 0.0)]
    Aa = np.array([[e, n, 1.0] for e, n in pts]); XY = np.array([mtm8(*FR.from_EN(E0 + e, N0 + n)) for e, n in pts])
    cx_, *_ = np.linalg.lstsq(Aa, XY[:, 0], rcond=None); cy_, *_ = np.linalg.lstsq(Aa, XY[:, 1], rcond=None)
    ee = np.arange(xmin, xmax, 0.25); nn = np.arange(ymin, ymax, 0.25); EE, NN = np.meshgrid(ee, nn)   # row 0 = south
    X = cx_[0] * EE + cx_[1] * NN + cx_[2]; Y = cy_[0] * EE + cy_[1] * NN + cy_[2]
    c = ((X - x0) / dx).astype(int); r = ((y0 - Y) / dy).astype(int); ok = (c >= 0) & (c < a.shape[1]) & (r >= 0) & (r < a.shape[0])
    Z = np.full(EE.shape, np.nan, np.float32); Z[ok] = a[r[ok], c[ok]]
    zz = np.where(np.isnan(Z), np.nanmedian(Z), Z); gy, gx = np.gradient(zz, 0.25); slope = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
    hs = np.clip(math.sin(math.radians(40)) * np.cos(slope) + math.cos(math.radians(40)) * np.sin(slope) * np.cos(math.radians(315) - asp), 0, 1)
    return hs, 'lower', dict(cmap='gray', vmin=0.2, vmax=1.0)

# ---------- draw
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt; from matplotlib.patches import Polygon; import matplotlib.patheffects as pe
LAB = {'en': dict(t=f'Rue de Terrebonne and avenue {A.street}' + (f' (to {A.next_name})' if A.next_name else '') + ': three widths to scale', blue=f'Terrebonne, curb to curb (LiDAR 2015: {TERR_W:.1f} m along the lane; the block\'s median drawn)',
                  red=f'{RESID:.1f} m: Terrebonne less the contraflow lane and its buffer ({A.contraflow:.1f} m), where the December layout puts parking, the shared lane and parking',
                  green=f'{A.street}, curb to curb (LiDAR 2015; the block\'s most frequent reading' + (f'; drawn near Terrebonne and near {A.next_name.split()[-1]}' if FAR_BOX else '') + ')', rep='the same 11.0 m and 8.5 m boxes repeated on the cross street',
                  src={'wms': 'Aerial imagery: Gouvernement du Québec (Imagerie_GQ), fetched ' + time.strftime('%b %d, %Y') + '; before the 2024 lane. Curbs and widths: City of Montréal LiDAR 2015 (open data, CC-BY 4.0). North up.',
                       'lidar': 'Background: City of Montréal LiDAR 2015 (open data, CC-BY 4.0), ground surface as a hillshade (0.25 m); buildings and trees removed, curbs show as fine lines. Curbs and widths from the same survey. North up.'}),
       'fr': dict(t=f'Rue de Terrebonne et avenue {A.street}' + (f' (jusqu\'à {A.next_name})' if A.next_name else '') + ' : trois largeurs à l\'échelle', blue=f'Terrebonne, de bordure à bordure (LiDAR 2015 : ' + f'{TERR_W:.1f}'.replace('.', ',') + f' m le long de la piste ; médiane du tronçon dessinée)',
                  red=f'{RESID:.1f}'.replace('.', ',') + f' m : Terrebonne moins la voie à contresens et sa zone tampon (' + f'{A.contraflow:.1f}'.replace('.', ',') + ' m)' + f', où l\'aménagement de décembre met stationnement, voie partagée et stationnement',
                  green=f'{A.street}, de bordure à bordure (LiDAR 2015 ; lecture la plus fréquente du tronçon' + (f' ; dessinée près de Terrebonne et près de {A.next_name.split()[-1]}' if FAR_BOX else '') + ')', rep='les mêmes boîtes de 11,0 m et 8,5 m reportées sur la rue transversale',
                  src={'wms': 'Imagerie aérienne : Gouvernement du Québec (Imagerie_GQ), consultée le ' + time.strftime('%Y-%m-%d') + ' ; antérieure à la piste de 2024. Bordures et largeurs : LiDAR 2015 de la Ville de Montréal (données ouvertes, CC-BY 4.0). Nord en haut.',
                       'lidar': 'Fond : LiDAR 2015 de la Ville de Montréal (données ouvertes, CC-BY 4.0), surface du sol en ombrage (0,25 m) ; bâtiments et arbres retirés, les bordures apparaissent en traits fins. Bordures et largeurs : même levé. Nord en haut.'})}
slug = A.street.lower().replace(chr(39), '').replace(' ', '-')
DRAWN = []
for kind in KINDS:
  got = bg_wms() if kind == 'wms' else bg_lidar()
  if got is None: print('no background for', kind); continue
  img, origin, kw = got; src = kind; DRAWN.append(kind)
  base = 'cross_street_boxes' + ('' if (A.street == 'Kensington' and not A.to_next) else '_' + slug) + ('' if kind == 'wms' else '_lidar')
  for lang, L in LAB.items():
    fw = 10.0; fh = (fw * (ymax - ymin) / (xmax - xmin) + 1.2) if (ymax - ymin) == (xmax - xmin) else 0.8 * fw * (ymax - ymin) / (xmax - xmin) + 1.9
    fig, ax = plt.subplots(figsize=(fw, fh), dpi=150)
    ax.imshow(img, extent=(xmin, xmax, ymin, ymax), origin=origin, interpolation='bilinear', **(kw or {}))
    for corners, col, lab, _k in BOXES:
        ax.add_patch(Polygon(corners, closed=True, fc=col, ec='white', lw=1.4, alpha=0.55))
        cx = sum(c[0] for c in corners) / 4; cy = sum(c[1] for c in corners) / 4
        ang = math.degrees(math.atan2(corners[2][1] - corners[1][1], corners[2][0] - corners[1][0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        ax.text(cx, cy, lab.replace('.', ',') if lang == 'fr' else lab, color='white', fontsize=11, fontweight='bold', ha='center', va='center', rotation=ang, rotation_mode='anchor', path_effects=[pe.withStroke(linewidth=2.5, foreground='black')])
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    # scale bar
    ax.plot([xmin + 6, xmin + 26], [ymin + 6, ymin + 6], color='white', lw=3, path_effects=[pe.withStroke(linewidth=5, foreground='black')]); ax.text(xmin + 16, ymin + 8.5, '20 m', color='white', ha='center', fontsize=9, path_effects=[pe.withStroke(linewidth=2.5, foreground='black')])
    for x_, y_, txt, an in LABELS:
        ax.text(x_, y_, txt, color='white', fontsize=10, fontstyle='italic', ha='center', va='center', rotation=an, rotation_mode='anchor', path_effects=[pe.withStroke(linewidth=2.5, foreground='black')])
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(fc=C_T, ec='white', alpha=0.7, label=L['blue']), Patch(fc=C_R, ec='white', alpha=0.7, label=L['red']), Patch(fc=C_X, ec='white', alpha=0.7, label=L['green'])],
              loc='upper center', bbox_to_anchor=(0.5, -0.005), fontsize=8.6, frameon=False, ncol=1)
    ax.set_title(L['t'], fontsize=11.5); fig.text(0.5, 0.012, L['src'][src], fontsize=7.2, color='0.3', ha='center', wrap=True)
    fig.tight_layout(rect=(0, 0.035, 1, 1)); fig.savefig(os.path.join(FIG, f'{base}_{lang}.png'), **(dict(bbox_inches='tight', pad_inches=0.15) if A.to_next else {})); print('wrote', f'{base}_{lang}.png'); plt.close(fig)
json.dump(dict(street=A.street, node=[lon0, lat0], background=DRAWN, frame_m=[xmin, xmax, ymin, ymax], far_box=FAR_BOX, terrebonne_curb_to_curb=TERR_W, residual=RESID, contraflow_plus_buffer=A.contraflow,
               drawn=dict(terrebonne_west=round(offs[0], 2), terrebonne_east=round(offs[1], 2), cross=[round(o, 2) for o in offs[2:]])),
          open(os.path.join(HERE, f'cross_street_boxes_{A.street.lower()}.json'), 'w'), indent=1)
print('backgrounds', DRAWN, 'drawn widths', [round(o, 2) for o in offs])
