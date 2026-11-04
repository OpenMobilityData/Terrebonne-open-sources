#!/usr/bin/env python3
"""Width of rue de Terrebonne along its length from the City's 2015 airborne LiDAR (open data, CC-BY 4.0) and the City's
assessment-unit outlines (open data, CC-BY 4.0), in the street frame of the 1954–55 plans work (../../1954-underwriters-plans-terrebonne-garages/derived/frame.py:
u = distance along the lane from its west end, v = signed offset, +v = north side).

For every station u (every STEP m) a cross-section is sampled on the ground raster (corridor_dtm_mean_0p25m.tif: mean elevation of
ground-class returns on a 0.25 m grid, built by pdal from the six tiles; rasters live outside the repository). Each curb is the first
rise of at least STEP_Z m over WIN m scanning outward from the axis between MIN_HALF and MAX_HALF m (the curb face, 10–15 cm in Montréal,
passes; a driveway ramp at about 1:12 rises 4 cm over that distance and does not, though a steeper apron can); the curb position is the point of steepest rise in that window. Where parked cars (the LiDAR was flown at night with cars at
the curbs) or trees left no ground returns, the profile has gaps; a station is kept only when both curbs are found and the width is
plausible (9–13 m; a wider reading means a curb was missed and a driveway ramp or a step beyond it was taken). The right-of-way is measured on the same line: the distance from the axis to the first parcel outline on each side.
Outputs (derived/): street_width_profile.csv (every station), street_width_by_block.csv (per block: n, median, p10, p90, min, max),
figures/street_width_profile_{en,fr}.png, figures/street_width_sections_{en,fr}.png (example cross-sections), summary.json.
Run: /opt/local/bin/python3.13 width_profile.py   (needs numpy, rasterio, shapely, matplotlib)
"""
import csv, json, math, os, sys
import numpy as np, rasterio
from shapely.geometry import Polygon, LineString, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
G54 = os.path.join(os.path.dirname(os.path.dirname(HERE)), '1954-underwriters-plans-terrebonne-garages', 'derived'); sys.path.insert(0, G54)
import frame as FR; from mtm import mtm8
U_WEST = 0.0   # the public street ends where the lane ends (géobase segment 1320365 ends at the campus boundary); beyond it is the campus's private roadway
def from_uv(u, v):
    P, CUM = FR.P, FR.CUM
    if u < 0: a, b = P[0], P[1]; i = 0
    else:
        i = max(0, min(len(P) - 2, next((k for k in range(len(CUM) - 1) if CUM[k + 1] >= u), len(P) - 2))); a, b = P[i], P[i + 1]
    dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy); tt = (u - CUM[i]) / L; ex, ey = dx / L, dy / L
    return a[0] + tt * dx - v * ey, a[1] + tt * dy + v * ex
LD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/lidar-aerien-2015/derived/')
STEP, VMAX, DV = 2.0, 16.0, 0.1
MIN_HALF, MAX_HALF, STEP_Z, WIN = 3.0, 8.0, 0.07, 0.5   # the curb lies 3–8 m from the axis on a 20 m right-of-way

def load(name):
    with rasterio.open(LD + name) as ds:
        a = ds.read(1).astype(np.float32); tr = ds.transform
    a[a <= -9998] = np.nan
    return a, (tr.c, tr.f, tr.a, -tr.e)   # x0 (left), y0 (top), dx, dy
DTM, G = load('corridor_dtm_mean_0p25m.tif')
def sample(X, Y):
    x0, y0, dx, dy = G; c = ((X - x0) / dx).astype(int); r = ((y0 - Y) / dy).astype(int)
    ok = (c >= 0) & (c < DTM.shape[1]) & (r >= 0) & (r < DTM.shape[0]); out = np.full(X.shape, np.nan, np.float32); out[ok] = DTM[r[ok], c[ok]]; return out

# parcels (right-of-way)
feats = json.load(open(os.path.join(G54, 'city_assessment_units_terrebonne_bbox.geojson')))['features']
polys = []
for f in feats:
    g = f['geometry']; pp = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    for poly in pp:
        try: polys.append(Polygon([FR.to_EN(*c[:2]) for c in poly[0]]).buffer(0))
        except Exception: pass
tree = STRtree(polys)

# blocks from the frame's nodes
NODES = FR.NODES; CUM = FR.CUM
def nm(i):
    n = NODES[i][2].split('; ')[0].replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '')
    return n if n else 'west end'
def block_of(u):
    if u < 0: return -1, 'stub west of the lane (to the campus entrance)'
    for i in range(len(CUM) - 1):
        if CUM[i] <= u < CUM[i + 1]: return i, f"{nm(i)} – {nm(i + 1)}"
    return len(CUM) - 2, f"{nm(len(CUM) - 2)} – {nm(len(CUM) - 1)}"

def curb(v, z, side):
    """the first rise of at least STEP_Z m over WIN m scanning outward from the axis (+1 north, -1 south) between MIN_HALF and MAX_HALF:
    a curb face (10–15 cm over a few cm) passes, a driveway ramp (about 1:12, 2.5 cm over 0.3 m) does not; returns |v| of the steepest
    point in that window, or None (a depressed curb at a driveway, or no ground returns under a parked car)"""
    n = int(round(WIN / DV))
    order = range(len(v)) if side > 0 else range(len(v) - 1, -1, -1)
    for k in order:
        if not (MIN_HALF <= v[k] * side <= MAX_HALF): continue
        j = k + n if side > 0 else k - n
        if j < 0 or j >= len(v): continue
        a, b = z[k], z[j]
        if np.isnan(a) or np.isnan(b): continue
        if b - a >= STEP_Z:
            seg = z[min(k, j):max(k, j) + 1]
            if np.isnan(seg).any(): continue
            d = np.diff(seg); m = int(np.argmax(d if side > 0 else d[::-1]))
            pos = (k + m) if side > 0 else (k - m)
            return abs(v[pos]) + DV / 2
    return None

rows = []
v = np.arange(-VMAX, VMAX + 1e-9, DV)
for u in np.arange(U_WEST, FR.LENGTH + 1e-9, STEP):
    E, N = zip(*[from_uv(u, vv) for vv in v]); E, N = np.array(E), np.array(N)
    lon, lat = zip(*[FR.from_EN(e, n) for e, n in zip(E, N)])
    X, Y = zip(*[mtm8(lo, la) for lo, la in zip(lon, lat)]); X, Y = np.array(X), np.array(Y)
    z = sample(X, Y)
    cn, cs = curb(v, z, +1), curb(v, z, -1)
    # right-of-way: nearest parcel on each side along the section line
    E0, N0 = from_uv(u, 0.0); line = LineString([from_uv(u, -VMAX - 4), from_uv(u, VMAX + 4)])
    rn = rs = None
    for j in tree.query(line, predicate='intersects'):
        inter = polys[j].intersection(line)
        geoms = inter.geoms if hasattr(inter, 'geoms') else [inter]
        for gg in geoms:
            for c in gg.coords:
                _, vv = FR.to_uv(c[0], c[1])
                if vv > 0: rn = vv if rn is None else min(rn, vv)
                elif vv < 0: rs = -vv if rs is None else min(rs, -vv)
    i, bname = block_of(u); lo, la = FR.from_EN(E0, N0)
    width = (cn + cs) if (cn is not None and cs is not None) else None
    ok = width is not None and 9.0 <= width <= 13.0
    rows.append(dict(u=round(float(u), 1), lon=round(lo, 6), lat=round(la, 6), block_index=i, block=bname,
                     curb_N=None if cn is None else round(cn, 2), curb_S=None if cs is None else round(cs, 2), width_curb_to_curb=None if width is None else round(width, 2), kept=int(ok),
                     row_N=None if rn is None else round(rn, 2), row_S=None if rs is None else round(rs, 2), right_of_way=None if (rn is None or rs is None) else round(rn + rs, 2),
                     sidewalk_N=None if (rn is None or cn is None) else round(rn - cn, 2), sidewalk_S=None if (rs is None or cs is None) else round(rs - cs, 2)))
with open(os.path.join(HERE, 'street_width_profile.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
# per block
blocks = {}
for r in rows: blocks.setdefault((r['block_index'], r['block']), []).append(r)
def stats(vals):
    a = np.array([x for x in vals if x is not None], float)
    if not len(a): return dict(n=0)
    return dict(n=int(len(a)), median=round(float(np.median(a)), 2), p10=round(float(np.percentile(a, 10)), 2), p90=round(float(np.percentile(a, 90)), 2), min=round(float(a.min()), 2), max=round(float(a.max()), 2))
bl = []
for (i, name), rs_ in sorted(blocks.items()):
    kept = [r for r in rs_ if r['kept']]
    sc = stats([r['width_curb_to_curb'] for r in kept]); sr = stats([r['right_of_way'] for r in rs_]); sn = stats([r['sidewalk_N'] for r in kept]); ss = stats([r['sidewalk_S'] for r in kept])
    bl.append(dict(block_index=i, block=name, u_start=round(CUM[i] if i >= 0 else U_WEST, 1), u_end=round((CUM[i + 1] if i + 1 < len(CUM) else FR.LENGTH) if i >= 0 else 0.0, 1), stations=len(rs_), stations_with_both_curbs=len(kept),
                   curb_median=sc.get('median'), curb_p10=sc.get('p10'), curb_p90=sc.get('p90'), curb_min=sc.get('min'), curb_max=sc.get('max'),
                   row_median=sr.get('median'), row_p10=sr.get('p10'), row_p90=sr.get('p90'), sidewalk_N_median=sn.get('median'), sidewalk_S_median=ss.get('median')))
with open(os.path.join(HERE, 'street_width_by_block.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(bl[0].keys())); w.writeheader(); w.writerows(bl)
kept = [r for r in rows if r['kept']]
S = dict(stations=len(rows), step_m=STEP, kept=len(kept), length_m=round(FR.LENGTH, 1), curb=stats([r['width_curb_to_curb'] for r in kept]), right_of_way=stats([r['right_of_way'] for r in rows]),
         sidewalk_N=stats([r['sidewalk_N'] for r in kept]), sidewalk_S=stats([r['sidewalk_S'] for r in kept]), params=dict(min_half=MIN_HALF, step_z=STEP_Z, win=WIN, vmax=VMAX, dv=DV))
json.dump(S, open(os.path.join(HERE, 'summary.json'), 'w'), indent=1)
print(json.dumps(S, indent=1))
for b in bl: print(f"{b['block']:<32} n={b['stations_with_both_curbs']:>3}/{b['stations']:<3} curb {b['curb_median']} ({b['curb_p10']}–{b['curb_p90']})  ROW {b['row_median']}  sw N {b['sidewalk_N_median']} S {b['sidewalk_S_median']}")

# ---------- figures (EN/FR)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
LAB = {'en': dict(t1='Rue de Terrebonne: width of the roadway along the lane, from the City\'s 2015 LiDAR', y1='curb to curb (m)', y2='right-of-way and sidewalk zones (m)',
                  l_pts='station every 2 m (both curbs found)', l_med='block median', l_plan='10.8 m: the winter cross-section of EXP 2023, Fig. 6-6 (2.4 + 3.5 + 2.4 + 0.5 + 2.0)',
                  l_row='right-of-way (parcel line to parcel line)', l_sn='north: parcel line to curb', l_ss='south: parcel line to curb', x='distance along the lane from its west end (m)',
                  src='Ground elevation: Ville de Montréal, LiDAR aérien 2015 (CC-BY 4.0), ground returns averaged on a 0.25 m grid; parcels: Ville de Montréal, unités d\'évaluation foncière (CC-BY 4.0). Curb = the first rise of 7 cm over 0.5 m outward from the axis, between 3 and 8 m. Stations where a parked car or a tree hid a curb are left out.',
                  t2='Cross-sections at six stations: ground elevation across the street and the curbs found', xs='offset from the lane axis (m; north to the right)', ys='elevation above the axis (m)', cu='curb'),
       'fr': dict(t1='Rue de Terrebonne : largeur de la chaussée le long de la piste, d\'après le LiDAR 2015 de la Ville', y1='de bordure à bordure (m)', y2='emprise et zones de trottoir (m)',
                  l_pts='station aux 2 m (les deux bordures trouvées)', l_med='médiane du tronçon', l_plan='10,8 m : la coupe hivernale d\'EXP 2023, fig. 6-6 (2,4 + 3,5 + 2,4 + 0,5 + 2,0)',
                  l_row='emprise (limite de lot à limite de lot)', l_sn='nord : limite de lot à bordure', l_ss='sud : limite de lot à bordure', x='distance le long de la piste depuis son extrémité ouest (m)',
                  src='Altitude du sol : Ville de Montréal, LiDAR aérien 2015 (CC-BY 4.0), retours « sol » moyennés sur une grille de 0,25 m ; lots : Ville de Montréal, unités d\'évaluation foncière (CC-BY 4.0). Bordure = première montée de 7 cm en 0,5 m, à 3–8 m de l\'axe. Les stations où une voiture stationnée ou un arbre cache une bordure sont omises.',
                  t2='Coupes à six stations : altitude du sol en travers de la rue et bordures trouvées', xs='décalage par rapport à l\'axe de la piste (m ; nord à droite)', ys='altitude par rapport à l\'axe (m)', cu='bordure')}
us = np.array([r['u'] for r in kept]); ws = np.array([r['width_curb_to_curb'] for r in kept])
for lang, L in LAB.items():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(16, 8.5), dpi=150, sharex=True, gridspec_kw=dict(height_ratios=[3, 2]))
    a1.scatter(us, ws, s=7, color='#1f77b4', alpha=0.6, label=L['l_pts'], zorder=3)
    for b in bl:
        if b['curb_median'] is not None: a1.hlines(b['curb_median'], b['u_start'], b['u_end'], color='#d62728', lw=2.2, zorder=4)
    a1.hlines(10.8, U_WEST, FR.LENGTH, color='0.3', ls='--', lw=1, label=L['l_plan']); a1.axvline(0, color='0.3', lw=1)
    a1.plot([], [], color='#d62728', lw=2.2, label=L['l_med'])
    for i, c in enumerate(CUM): a1.axvline(c, color='0.85', lw=0.7, zorder=1); a2.axvline(c, color='0.85', lw=0.7, zorder=1)
    for i in range(len(CUM)):
        a1.text(CUM[i], 13.05, nm(i), rotation=90, fontsize=6.5, ha='center', va='bottom', color='0.35')
    a1.set_ylim(9.5, 13.0); a1.set_ylabel(L['y1']); a1.legend(loc='lower right', fontsize=8, ncol=3); a1.set_title(L['t1'], fontsize=12, pad=60)
    ur = np.array([r['u'] for r in rows if r['right_of_way'] is not None]); rw = np.array([r['right_of_way'] for r in rows if r['right_of_way'] is not None])
    a2.plot(ur, rw, color='0.2', lw=1, label=L['l_row'])
    a2.plot([r['u'] for r in kept if r['sidewalk_N'] is not None], [r['sidewalk_N'] for r in kept if r['sidewalk_N'] is not None], '.', ms=3, color='#ff7f0e', label=L['l_sn'])
    a2.plot([r['u'] for r in kept if r['sidewalk_S'] is not None], [r['sidewalk_S'] for r in kept if r['sidewalk_S'] is not None], '.', ms=3, color='#2ca02c', label=L['l_ss'])
    a2.set_ylim(0, 24); a2.set_ylabel(L['y2']); a2.set_xlabel(L['x']); a2.legend(loc='center right', fontsize=8); a2.set_xlim(U_WEST, FR.LENGTH)
    fig.text(0.01, 0.005, L['src'], fontsize=7, color='0.35'); fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(os.path.join(FIG, f'street_width_profile_{lang}.png')); plt.close(fig)
    # cross-sections
    picks = [k for k in np.linspace(0.08, 0.92, 6)]
    fig, axes = plt.subplots(2, 3, figsize=(16, 7.5), dpi=150); axes = axes.ravel()
    for ax, f in zip(axes, picks):
        r = min(kept, key=lambda q: abs(q['u'] - f * FR.LENGTH)); u = r['u']
        E, N = zip(*[from_uv(u, vv) for vv in v]); lon, lat = zip(*[FR.from_EN(e, n) for e, n in zip(E, N)])
        X, Y = zip(*[mtm8(lo, la) for lo, la in zip(lon, lat)]); z = sample(np.array(X), np.array(Y)); z0 = np.nanmedian(z[(v > -1) & (v < 1)])
        ax.plot(v, z - z0, color='#1f77b4', lw=1.2); ax.axvline(r['curb_N'], color='#d62728', ls='--', lw=1); ax.axvline(-r['curb_S'], color='#d62728', ls='--', lw=1)
        if r['row_N']: ax.axvline(r['row_N'], color='0.5', ls=':', lw=1)
        if r['row_S']: ax.axvline(-r['row_S'], color='0.5', ls=':', lw=1)
        ax.set_title(f"u = {u:.0f} m, {r['block']}: {r['width_curb_to_curb']} m {L['cu']}–{L['cu']}", fontsize=9); ax.set_xlim(-12, 12); ax.set_ylim(-0.3, 0.6); ax.grid(alpha=0.3)
        ax.set_xlabel(L['xs'], fontsize=8); ax.set_ylabel(L['ys'], fontsize=8)
    fig.suptitle(L['t2'], fontsize=12); fig.tight_layout(rect=(0, 0, 1, 0.96)); fig.savefig(os.path.join(FIG, f'street_width_sections_{lang}.png')); plt.close(fig)
print('figures written')

# ---------- overhead review figure: the ground surface (hillshade) in the street frame with every curb detection
def hill(z, dx=0.25):
    zz = np.where(np.isnan(z), np.nanmedian(z), z); gy, gx = np.gradient(zz, dx); slope = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
    a, b = math.radians(315), math.radians(40)
    return np.clip(math.sin(b) * np.cos(slope) + math.cos(b) * np.sin(slope) * np.cos(a - asp), 0, 1)
def strip(u0, u1, vmax=10.0, du=0.25):
    uu = np.arange(u0, u1, du); vv = np.arange(-vmax, vmax, du)
    E = np.empty((len(vv), len(uu))); N = np.empty_like(E)
    for j, u in enumerate(uu):
        for i, v_ in enumerate(vv): E[i, j], N[i, j] = from_uv(u, v_)
    lon, lat = np.vectorize(FR.from_EN)(E, N); X, Y = np.vectorize(mtm8)(lon, lat)
    return uu, vv, sample(X, Y)
OV = {'en': dict(t='Review figure: the LiDAR ground surface in the street frame (hillshade, 0.25 m) with every curb detection; red = north curb, blue = south curb, grey ticks on the axis = station dropped (no ground under a parked car or a tree, or a width outside 9–13 m)', x='distance along the lane (m)', y='offset (m; north up)'),
      'fr': dict(t='Figure de contrôle : la surface du sol LiDAR dans le repère de la rue (ombrage, 0,25 m) avec chaque bordure détectée ; rouge = bordure nord, bleu = bordure sud, traits gris sur l\'axe = station rejetée (pas de sol sous une voiture stationnée ou un arbre, ou largeur hors 9–13 m)', x='distance le long de la piste (m)', y='décalage (m ; nord en haut)')}
PANELS = [(0, 440), (440, 880), (880, 1320), (1320, 1760), (1760, 2200), (2200, FR.LENGTH)]
strips = [strip(a, b) for a, b in PANELS]
for lang, L in OV.items():
    fig, axes = plt.subplots(len(PANELS), 1, figsize=(18, 2.3 * len(PANELS)), dpi=130)
    for ax, (a, b), (uu, vv, z) in zip(axes, PANELS, strips):
        ax.imshow(hill(z), cmap='gray', extent=(uu[0], uu[-1], vv[0], vv[-1]), origin='lower', aspect='equal', vmin=0.2, vmax=1.0)
        kp = [r for r in rows if a <= r['u'] < b]
        ax.plot([r['u'] for r in kp if r['kept']], [r['curb_N'] for r in kp if r['kept']], '.', ms=4, color='#d62728')
        ax.plot([r['u'] for r in kp if r['kept']], [-r['curb_S'] for r in kp if r['kept']], '.', ms=4, color='#1f77b4')
        ax.plot([r['u'] for r in kp if not r['kept']], [0] * sum(1 for r in kp if not r['kept']), '|', ms=6, color='0.6')
        for i, c in enumerate(CUM):
            if a <= c < b: ax.axvline(c, color='#ff7f0e', lw=0.6); ax.text(c, 9.0, nm(i), fontsize=6.5, color='#ff7f0e', ha='center', va='top')
        if a <= 0 < b: ax.axvline(0, color='#ff7f0e', lw=0.6); ax.text(0, 9.0, 'west end of the lane' if lang == 'en' else 'extrémité ouest de la piste', fontsize=6.5, color='#ff7f0e', ha='center', va='top')
        ax.set_xlim(a, b); ax.set_ylim(-10, 10); ax.set_ylabel(L['y'], fontsize=8); ax.tick_params(labelsize=7)
    axes[-1].set_xlabel(L['x'], fontsize=8); fig.suptitle(L['t'], fontsize=9.5, y=0.995); fig.tight_layout(rect=(0, 0, 1, 0.985))
    fig.savefig(os.path.join(FIG, f'street_width_overhead_{lang}.png')); plt.close(fig)
# close-up of the west end (the stub and the first blocks)
uu, vv, z = strip(0, 200, vmax=12.0, du=0.25)
for lang, L in OV.items():
    fig, ax = plt.subplots(figsize=(18, 5), dpi=150)
    ax.imshow(hill(z), cmap='gray', extent=(uu[0], uu[-1], vv[0], vv[-1]), origin='lower', aspect='equal', vmin=0.2, vmax=1.0)
    kp = [r for r in rows if 0 <= r['u'] < 200]
    ax.plot([r['u'] for r in kp if r['kept']], [r['curb_N'] for r in kp if r['kept']], 'o', ms=4, color='#d62728'); ax.plot([r['u'] for r in kp if r['kept']], [-r['curb_S'] for r in kp if r['kept']], 'o', ms=4, color='#1f77b4')
    for r in kp:
        if r['kept'] and int(r['u']) % 20 == 0: ax.text(r['u'], 11.2, f"{r['width_curb_to_curb']:.1f}", fontsize=6.5, ha='center', color='0.1')
    ax.plot([r['u'] for r in kp if not r['kept']], [0] * sum(1 for r in kp if not r['kept']), '|', ms=8, color='0.6')
    for i, c in enumerate(CUM):
        if 0 < c < 200: ax.axvline(c, color='#ff7f0e', lw=0.8); ax.text(c, -11.2, nm(i), fontsize=7.5, color='#ff7f0e', ha='center', va='top')
    ax.axvline(0, color='#ff7f0e', lw=0.8); ax.text(0, -11.2, 'west end of the lane' if lang == 'en' else 'extrémité ouest de la piste', fontsize=7.5, color='#ff7f0e', ha='center', va='top')
    ax.set_xlim(0, 200); ax.set_ylim(-12, 12); ax.set_xlabel(L['x']); ax.set_ylabel(L['y'])
    ax.set_title(('The west end (the public street ends at the Loyola campus boundary): the first 200 m, curb-to-curb width written every 20 m' if lang == 'en' else 'L\'extrémité ouest : le tronçon vers l\'entrée du campus Loyola et les premiers tronçons ; largeur de bordure à bordure inscrite aux 20 m'), fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, f'street_width_west_end_{lang}.png')); plt.close(fig)
print('overhead figures written')
