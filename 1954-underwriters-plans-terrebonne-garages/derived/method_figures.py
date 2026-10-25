#!/usr/bin/env python3
"""Method figures: the three sources aligned in the street frame (u along Terrebonne, v across,
north above): the Gouvernement du Québec aerial imagery (optical), the City's 2015 LiDAR as
height above ground, and the 1954-55 Underwriters' sheet, with the City's parcels and the
building markers overlaid. 'overview' = the whole street in two halves at 2.5 px/m;
'detail' = one block at 10 px/m with civic numbers. Usage: python3 method_figures.py [en|fr]"""
import csv, json, math, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import to_EN, from_EN, to_uv, from_uv, NODES, CUM, LENGTH, STREET_U
from mtm import mtm8
import maps, lidar_strips as L
HERE = os.path.dirname(os.path.abspath(__file__))
LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
QDIR = os.path.expanduser('~/Terrebonne-data/third-party/quebec-imagerie/terrebonne-blocks-2026-10-25/')
MLON = 111320 * math.cos(math.radians(45.47)); MLAT = 111132; MPP = 0.08
# the optical tiles fetched by ortho_strips_qc.py, with their bboxes recomputed from the same rule
TILES = []
for k in range(len(CUM) - 1):
    if CUM[k + 1] - CUM[k] < 20: continue
    u0, u1, vmax = CUM[k] - 14, CUM[k + 1] + 14, 40
    pts = [from_EN(*from_uv(u, v)) for u in (u0, u1) for v in (-vmax, vmax)]
    lon0, lon1 = min(p[0] for p in pts) - 0.00005, max(p[0] for p in pts) + 0.00005
    lat0, lat1 = min(p[1] for p in pts) - 0.00003, max(p[1] for p in pts) + 0.00003
    W = int((lon1 - lon0) * MLON / MPP); H = int((lat1 - lat0) * MLAT / MPP)
    f = os.path.join(QDIR, f'wms_block_{k:02d}.jpg')
    if os.path.exists(f): TILES.append((lon0, lat0, lon1, lat1, W, H, np.asarray(Image.open(f).convert('RGB'))))
def optical(u0, u1, vmax, ppm):
    Wo, Ho = int((u1 - u0) * ppm), int(2 * vmax * ppm); out = np.full((Ho, Wo, 3), 200, np.uint8)
    us = u0 + (np.arange(Wo) + 0.5) / ppm; vs = vmax - (np.arange(Ho) + 0.5) / ppm
    LON = np.zeros((Ho, Wo)); LAT = np.zeros((Ho, Wo))
    for j, u in enumerate(us):
        for i, v in enumerate(vs): LON[i, j], LAT[i, j] = from_EN(*from_uv(u, v))
    for lon0, lat0, lon1, lat1, W, H, arr in TILES:
        c = ((LON - lon0) / (lon1 - lon0) * W).astype(int); r = ((lat1 - LAT) / (lat1 - lat0) * H).astype(int)
        ok = (c >= 0) & (c < W) & (r >= 0) & (r < H); out[ok] = arr[r[ok], c[ok]]
    return out, LON, LAT
def lidar(LON, LAT):
    X = np.zeros(LON.shape); Y = np.zeros(LON.shape)
    for i in range(LON.shape[0]):
        for j in range(LON.shape[1]): X[i, j], Y[i, j] = mtm8(LON[i, j], LAT[i, j])
    h = L.sample(L.NDSM, L.G1, X, Y); hs = L.sample(L.HS, L.G1, X, Y); return L.colorize_ndsm(h, hs)
def sheet(u0, u1, vmax, ppm):
    img = maps.render_sheets(u0, u1, ppm); H = img.shape[0]; c = H // 2; d = int(vmax * ppm)
    return img[c - d:c + d]
rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')) if r['u_m']]
for r in rows: r['u'] = float(r['u_m']); r['v'] = float(r['v_m']); r['cat_today'] = maps.category_today(r)
CARS = [(float(r['u_m']), float(r['v_m'])) for r in csv.DictReader(open(os.path.join(HERE, 'lidar_cars.csv'), encoding='utf-8'))] if os.path.exists(os.path.join(HERE, 'lidar_cars.csv')) else []
UEV = json.load(open(os.path.join(HERE, 'city_assessment_units_terrebonne_bbox.geojson')))['features']
def overlay(ax, u0, u1, vmax, labels, msize):
    for pts in maps.parcels:
        if any(u0 - 5 < u < u1 + 5 and -vmax < v < vmax for u, v in pts):
            ax.plot([p[0] for p in pts] + [pts[0][0]], [p[1] for p in pts] + [pts[0][1]], color='#00d4ff', linewidth=0.5, alpha=0.8)
    if labels:
        for f in UEV:
            g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]; p = f['properties']
            pts = [to_uv(*to_EN(x, y)) for x, y in [(q[0], q[1]) for q in polys[0][0]]]
            cu = sum(q[0] for q in pts) / len(pts); cv = sum(q[1] for q in pts) / len(pts)
            if u0 < cu < u1 and abs(cv) < vmax:
                lab = (p['CIVIQUE_DEBUT'] or '').strip(); fin = (p['CIVIQUE_FIN'] or '').strip()
                if fin != lab: lab += '–' + fin[-2:]
                st = (p['NOM_RUE'] or '').replace('(MTL)', '').replace('rue de Terrebonne', '').replace('avenue ', '').replace('boulevard ', '').strip()
                ax.text(cu, cv, lab + (' ' + st[:7] if st else ''), fontsize=4.6, ha='center', va='center', color='black', bbox=dict(facecolor='white', edgecolor='none', alpha=0.75, pad=0.6))
    maps.draw_conversion(ax, u0, u1, lw=2.0)
    for key, en, fr, col, mk in maps.CATS_TODAY:
        pts = [r for r in rows if r['cat_today'] == key and u0 - 3 < r['u'] < u1 + 3 and abs(r['v']) < vmax]
        if pts: ax.scatter([r['u'] for r in pts], [r['v'] for r in pts], s=msize, c=col, marker=mk, edgecolors='black', linewidths=0.5, zorder=10)
def street_labels(ax, u0, u1, vmax):
    """cross-street names as upright boxed labels at the top of the panel, and the street's own name on its axis"""
    for name, us in STREET_U.items():
        if u0 - 2 < us < u1 + 2:
            short = name.replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '').replace("d'", '')
            ax.text(us, vmax - 2, short, ha='center', va='top', fontsize=8, color='#1a1a19', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5), zorder=20)
    ax.text(u0 + (u1 - u0) * 0.5, 0, 'rue de Terrebonne', ha='center', va='center', fontsize=8, color='#1a1a19', style='italic', bbox=dict(facecolor='white', edgecolor='none', alpha=0.75, pad=1.2), zorder=20)
SRC = {'en': ['Aerial imagery, Gouvernement du Québec (Imagerie_GQ, fetched Oct 25, 2026)', 'City of Montréal LiDAR 2015: height above ground (amber 0.5–3.5 m: cars, garages, fences; blue-grey: houses; green: trees)', "Underwriters' Survey Bureau, 1954–55 (BAnQ notice 0000174390), georeferenced"],
       'fr': ['Imagerie aérienne, Gouvernement du Québec (Imagerie_GQ, consultée le 25 oct. 2026)', 'LiDAR 2015 de la Ville de Montréal : hauteur au-dessus du sol (ambre 0,5–3,5 m : voitures, garages, clôtures; gris-bleu : maisons; vert : arbres)', 'Underwriters’ Survey Bureau, 1954–1955 (BAnQ, notice 0000174390), géoréférencé']}
def figure(ranges, vmax, ppm, labels, msize, name, title, fig_w):
    nR = len(ranges); fig, axes = plt.subplots(3 * nR, 1, figsize=(fig_w, nR * 3 * (fig_w * 2 * vmax / (ranges[0][1] - ranges[0][0] + 12)) + 0.6 * nR + 0.8))
    axes = np.atleast_1d(axes)
    for ri, (u0, u1) in enumerate(ranges):
        opt, LON, LAT = optical(u0, u1, vmax, ppm); lid = lidar(LON, LAT); sh = sheet(u0, u1, vmax, ppm)
        for si, (img, lab) in enumerate(zip((opt, lid, sh), SRC[LANG])):
            ax = axes[ri * 3 + si]; ax.imshow(img, extent=(u0, u1, -vmax, vmax), interpolation='bilinear'); ax.set_xlim(u0, u1); ax.set_ylim(-vmax, vmax)
            ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect('equal')
            overlay(ax, u0, u1, vmax, labels and si == 0, msize)
            ax.text(u0 + 2, -vmax + 2, lab, fontsize=6, ha='left', va='bottom', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5))
            if si == 0: street_labels(ax, u0, u1, vmax)
            if si == 1 and CARS: ax.scatter([c[0] for c in CARS if u0 < c[0] < u1 and abs(c[1]) < vmax], [c[1] for c in CARS if u0 < c[0] < u1 and abs(c[1]) < vmax], s=msize * 1.6, facecolors='none', edgecolors='#e34948', linewidths=0.9, marker='s', zorder=9)
    import textwrap; fig.suptitle('\n'.join(textwrap.wrap(title, 150)), fontsize=9.5, y=0.995)
    handles = [Line2D([], [], marker=mk, color='none', markerfacecolor=col, markeredgecolor='black', markersize=6, label=(en if LANG == 'en' else fr)) for key, en, fr, col, mk in maps.CATS_TODAY]
    handles.append(Line2D([], [], marker='s', color='none', markerfacecolor='none', markeredgecolor='#e34948', markersize=7, label=('Car-sized object detected in the LiDAR (0.9–2.3 m), flown at night' if LANG == 'en' else 'Objet de la taille d’une voiture détecté au LiDAR (0,9–2,3 m), vol de nuit'))); handles.append(maps.conversion_handle(LANG)); fig.legend(handles=handles, loc='lower center', ncol=2, fontsize=6.5, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(top=0.93, bottom=0.10, left=0.04, right=0.99, hspace=0.05)
    base = os.path.join(HERE, 'figures', f'{name}_{LANG}'); fig.savefig(base + '.png', dpi=110); fig.savefig(base + '.pdf'); plt.close(fig); print('wrote', base)
if __name__ == '__main__':
    half = LENGTH / 2
    figure([(0, half), (half, LENGTH)], 42, 2.5, False, 9, 'method_overview',
           'The three sources along the whole street, aligned in the street frame (north above; west half, then east half)' if LANG == 'en' else 'Les trois sources le long de toute la rue, alignées dans le repère de la rue (nord en haut; moitié ouest, puis moitié est)', 12)
    k = 19; figure([(CUM[k] - 10, CUM[k + 1] + 10)], 40, 10, True, 30, 'method_detail_hingston_hampton',
           'One block, Hingston to Hampton: aprons and parked cars (optical), the same cars and the garages as 0.5–3.5 m objects (LiDAR), the « Autos Bast » marks of 1954 (sheet 787-5 north, 787-7 south)' if LANG == 'en' else 'Un îlot, Hingston–Hampton : aires pavées et voitures (optique), les mêmes voitures et les garages comme objets de 0,5–3,5 m (LiDAR), les mentions « Autos Bast » de 1954 (feuillets 787-5 nord, 787-7 sud)', 12)
    k = 6; figure([(CUM[k] - 10, CUM[k + 1] + 10)], 40, 10, True, 30, 'method_detail_rosedale_kingedward',
           'One block, Rosedale to King-Edward: detached rear garages of 1954 (sheet 789-14) seen in the LiDAR as 2.5–3.5 m boxes; aprons and a parked car on the optical image' if LANG == 'en' else 'Un îlot, Rosedale–King-Edward : garages détachés de 1954 (feuillet 789-14) visibles au LiDAR comme des boîtes de 2,5–3,5 m; aires pavées et une voiture sur l’image optique', 12)
