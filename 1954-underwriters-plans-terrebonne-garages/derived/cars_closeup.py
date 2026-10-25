#!/usr/bin/env python3
"""Close-up on the LiDAR car detections, for a reader who wants to see that a tagged object looks
like a car and sits where a car would: one block at 10 px/m, the daytime image above the night
height raster with every detection drawn as an oriented box of its measured length and width
(red at a Terrebonne curb, orange on a private lot, grey on a cross street); then two zooms at
40 px/m, a car at the curb and a car in a driveway, with the height above ground in metres and the
height profile along the car's long axis. Usage: python3 cars_closeup.py [en|fr] [block]"""
import csv, math, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from matplotlib import transforms
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import from_EN, from_uv, CUM, NODES, STREET_U
import maps, lidar_strips as L, cars_figures as CF
HERE = os.path.dirname(os.path.abspath(__file__)); LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'; BLOCK = int(sys.argv[2]) if len(sys.argv) > 2 else 19
names = [n.split(';')[0].replace('Avenue ', '').replace('Boulevard ', '') for _, _, n in NODES]
cars = list(csv.DictReader(open(os.path.join(HERE, 'lidar_cars.csv'), encoding='utf-8')))
for c in cars:
    for k in ('u_m', 'v_m', 'length_m', 'width_m', 'mean_height_m', 'axis_deg_from_street'): c[k] = float(c[k])
COL = CF.COL; LAB = CF.LAB
def height_grid(u0, u1, v0, v1, ppm):
    CF.PPM = ppm; CF.VMAX = (v1 - v0) / 2
    # grids() is centred on v=0; build our own for an offset window
    Wo, Ho = int((u1 - u0) * ppm), int((v1 - v0) * ppm)
    us = u0 + (np.arange(Wo) + 0.5) / ppm; vs = v1 - (np.arange(Ho) + 0.5) / ppm
    lon = np.zeros((Ho, Wo)); lat = np.zeros((Ho, Wo))
    for i, v in enumerate(vs):
        for j, u in enumerate(us): lon[i, j], lat[i, j] = from_EN(*from_uv(u, v))
    return lon, lat
def mtm_grid(lon, lat):
    from mtm import mtm8
    lon0, lat0 = -73.6327, 45.4692; X0, Y0 = mtm8(lon0, lat0); e = 1e-5
    dXdl = (mtm8(lon0 + e, lat0)[0] - X0) / e; dXda = (mtm8(lon0, lat0 + e)[0] - X0) / e; dYdl = (mtm8(lon0 + e, lat0)[1] - Y0) / e; dYda = (mtm8(lon0, lat0 + e)[1] - Y0) / e
    return X0 + dXdl * (lon - lon0) + dXda * (lat - lat0), Y0 + dYdl * (lon - lon0) + dYda * (lat - lat0)
def draw_boxes(ax, u0, u1, v0, v1, lw=1.2):
    for c in cars:
        if u0 < c['u_m'] < u1 and v0 < c['v_m'] < v1:
            a = math.radians(c['axis_deg_from_street']); Lh, Wh = c['length_m'] / 2, c['width_m'] / 2
            t = transforms.Affine2D().rotate(a).translate(c['u_m'], c['v_m']) + ax.transData
            ax.add_patch(Rectangle((-Lh, -Wh), 2 * Lh, 2 * Wh, facecolor='none', edgecolor=COL[c['class']], linewidth=lw, transform=t, zorder=9))
def block_figure(lang, k):
    u0, u1 = CUM[k] - 8, CUM[k + 1] + 8; V = 40
    lon, lat = CF.grids(u0, u1) if False else height_grid(u0, u1, -V, V, 10.0)
    opt = CF.optical_img(lon, lat); X, Y = mtm_grid(lon, lat)
    h = L.sample(L.NDSM, L.G1, X, Y); hs = L.sample(L.HS, L.G1, X, Y); lid = L.colorize_ndsm(h, hs)
    # pick a curb car and a lot car in this block for the zooms
    inb = [c for c in cars if u0 < c['u_m'] < u1 and abs(c['v_m']) < V]
    curb = max([c for c in inb if c['class'] == 'terrebonne_curb'], key=lambda c: c['area_m2'], default=None)
    # the driveway example: a lot object between 10 and 28 m from the axis, car-sized (6-12 m²), closest to 1.45 m mean height (a car's roof), ties by area
    def openness(c):  # share of cells above 3 m (tree crowns) in a 12 x 12 m window around the object: pick the clearest
        gl, ga = height_grid(c['u_m'] - 6, c['u_m'] + 6, c['v_m'] - 6, c['v_m'] + 6, 4.0); GX, GY = mtm_grid(gl, ga); gh = L.sample(L.NDSM, L.G1, GX, GY)
        return float(np.nanmean(gh > 3.0))
    cands = [c for c in inb if c['class'] == 'lot' and 10 < abs(c['v_m']) < 28 and 6 <= float(c['area_m2']) <= 12 and 1.1 <= c['mean_height_m'] <= 1.8]
    lot = min(cands, key=lambda c: (round(openness(c), 1), abs(c['mean_height_m'] - 1.45)), default=None)
    fig = plt.figure(figsize=(12, 13.2)); gs = fig.add_gridspec(3, 2, height_ratios=[1, 1, 1.05], hspace=0.12, wspace=0.12, left=0.03, right=0.97, top=0.95, bottom=0.07)
    axo = fig.add_subplot(gs[0, :]); axl = fig.add_subplot(gs[1, :])
    for ax, img in ((axo, opt), (axl, lid)):
        ax.imshow(img, extent=(u0, u1, -V, V), interpolation='bilinear'); ax.set_xlim(u0, u1); ax.set_ylim(-V, V); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        for pts in maps.parcels:
            if any(u0 - 5 < u < u1 + 5 and -V < v < V for u, v in pts): ax.plot([p[0] for p in pts] + [pts[0][0]], [p[1] for p in pts] + [pts[0][1]], color='#00d4ff', linewidth=0.5, alpha=0.8)
        maps.draw_conversion(ax, u0, u1, lw=1.6)
        for vv in (2.2, 7.0, -2.2, -7.0): ax.axhline(vv, color='white', linewidth=0.5, linestyle=':', alpha=0.9)
    CF.street_labels(axo, u0, u1) if hasattr(CF, 'street_labels') else None
    draw_boxes(axl, u0, u1, -V, V); draw_boxes(axo, u0, u1, -V, V, lw=0.8)
    axo.text(u0 + 2, -V + 2, 'Aerial imagery, daytime, after June 2024; boxes = the night LiDAR detections, for position only' if lang == 'en' else 'Imagerie aérienne, de jour, après juin 2024; boîtes = détections du LiDAR de nuit, pour la position seulement', fontsize=6.5, bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5))
    axl.text(u0 + 2, -V + 2, 'City LiDAR 2015, night: height above ground; each box has the measured length and width of the object; dotted lines: the curb band 2.2–7 m from the street axis' if lang == 'en' else 'LiDAR 2015 de la Ville, nuit : hauteur au-dessus du sol; chaque boîte a la longueur et la largeur mesurées de l’objet; pointillés : bande de bordure à 2,2–7 m de l’axe', fontsize=6.5, bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5))
    for col_i, (c, title) in enumerate(((curb, 'at the Terrebonne curb' if lang == 'en' else 'à la bordure de Terrebonne'), (lot, 'on a private lot (driveway)' if lang == 'en' else 'sur un lot privé (entrée)'))):
        ax = fig.add_subplot(gs[2, col_i])
        if c is None: ax.axis('off'); continue
        cu, cv = c['u_m'], c['v_m']; W = 7.0; zl, zlat = height_grid(cu - W, cu + W, cv - W, cv + W, 40.0); ZX, ZY = mtm_grid(zl, zlat)
        zh = L.sample(L.NDSM, L.G1, ZX, ZY)
        im = ax.imshow(zh, extent=(cu - W, cu + W, cv - W, cv + W), cmap='viridis', vmin=0, vmax=3.0, interpolation='nearest'); ax.set_aspect('equal')
        draw_boxes(ax, cu - W, cu + W, cv - W, cv + W, lw=1.8)
        ax.set_xlabel(('along the street (m)' if lang == 'en' else 'le long de la rue (m)'), fontsize=7); ax.set_ylabel(('across (m), north up' if lang == 'en' else 'en travers (m), nord en haut'), fontsize=7); ax.tick_params(labelsize=6)
        cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label('height above ground (m)' if lang == 'en' else 'hauteur au-dessus du sol (m)', fontsize=7); cb.ax.tick_params(labelsize=6)
        # profile along the long axis
        a = math.radians(c['axis_deg_from_street']); ts = np.linspace(-4, 4, 81)
        pu = cu + ts * math.cos(a); pv = cv + ts * math.sin(a)
        pl, pa = np.zeros(len(ts)), np.zeros(len(ts))
        for i in range(len(ts)): pl[i], pa[i] = from_EN(*from_uv(pu[i], pv[i]))
        PX, PY = mtm_grid(pl, pa); ph = L.sample(L.NDSM, L.G1, PX, PY)
        ax.plot(pu, pv, color='white', linewidth=0.8, linestyle='--')
        ins = ax.inset_axes([0.58, 0.72, 0.4, 0.25]); ins.plot(ts, ph, color='black', linewidth=1); ins.set_ylim(0, 3); ins.set_xlim(-4, 4); ins.tick_params(labelsize=5); ins.set_facecolor('white'); ins.patch.set_alpha(0.9)
        ins.set_title(('height along the dashed line (m)' if lang == 'en' else 'hauteur le long du trait (m)'), fontsize=5.5)
        ax.set_title(f"{title}: {c['length_m']:.1f} × {c['width_m']:.1f} m, {'mean' if lang == 'en' else 'moy.'} {c['mean_height_m']:.2f} m", fontsize=8)
    fig.suptitle((f"Block {names[k]} – {names[k+1]}: what a LiDAR car detection looks like" if lang == 'en' else f"Îlot {names[k]} – {names[k+1]} : à quoi ressemble une détection de voiture au LiDAR"), fontsize=10.5)
    handles = [Line2D([], [], marker='s', color='none', markerfacecolor='none', markeredgecolor=COL[c], markersize=7, label=LAB[lang][c]) for c in ('terrebonne_curb', 'lot', 'cross_street')] + [maps.conversion_handle(lang)]
    fig.legend(handles=handles, loc='lower center', ncol=2, fontsize=6.5, frameon=False)
    base = os.path.join(HERE, f'figures/terrebonne_parked_cars_closeup_{names[k].lower().replace(" ", "")}_{lang}'); fig.savefig(base + '.png', dpi=170); fig.savefig(base + '.pdf'); plt.close(fig); print('wrote', base)
if __name__ == '__main__':
    block_figure(LANG, BLOCK)
