#!/usr/bin/env python3
"""Parked cars, panel by panel along the street: for each of the five panels of the maps, the
Gouvernement du Québec aerial imagery (daytime, undated, before the 2024 lane) above the City's 2015 night
LiDAR as height above ground, in the same street frame, with every object the detector counted
as a car drawn on the LiDAR row (red square: at a Terrebonne curb; orange: on a private lot;
grey: on a cross street) and the by-eye count of cars on the optical row written per block
(north | south). A reader can check each square against a car-shaped blob, and recount the
optical row. Also a plain map of the detections on the City's parcels. Usage: python3 cars_figures.py [en|fr]"""
import csv, math, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Polygon as MPoly
from scipy.interpolate import RegularGridInterpolator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import from_EN, from_uv, CUM, NODES, LENGTH, STREET_U
from mtm import mtm8
import maps, lidar_strips as L, method_figures as MF
HERE = os.path.dirname(os.path.abspath(__file__)); LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
NP, VMAX, PPM = 5, 42.0, 4.0; PANEL = LENGTH / NP
cars = list(csv.DictReader(open(os.path.join(HERE, 'lidar_cars.csv'), encoding='utf-8')))
for c in cars: c['u'] = float(c['u_m']); c['v'] = float(c['v_m'])
blocks = list(csv.DictReader(open(os.path.join(HERE, 'on_street_cars_by_block.csv'), encoding='utf-8')))
COL = {'terrebonne_curb': '#e34948', 'lot': '#eda100', 'cross_street': '#8a8884', 'terrebonne_lane': '#e34948'}
LAB = {'en': {'terrebonne_curb': 'LiDAR 2015 (night): car-sized object at a Terrebonne curb', 'lot': 'on a private lot', 'cross_street': 'on a cross street'},
       'fr': {'terrebonne_curb': 'LiDAR 2015 (nuit) : objet de la taille d’une voiture à une bordure de Terrebonne', 'lot': 'sur un lot privé', 'cross_street': 'sur une rue transversale'}}
def grids(u0, u1):
    """lon/lat (and MTM) grids for the panel, from a coarse exact grid interpolated to PPM"""
    Wo, Ho = int((u1 - u0) * PPM), int(2 * VMAX * PPM)
    cu = np.linspace(u0, u1, int((u1 - u0) / 4) + 2); cv = np.linspace(-VMAX, VMAX, int(2 * VMAX / 4) + 2)
    LON = np.zeros((len(cv), len(cu))); LAT = np.zeros_like(LON)
    for i, v in enumerate(cv):
        for j, u in enumerate(cu): LON[i, j], LAT[i, j] = from_EN(*from_uv(u, v))
    fl = RegularGridInterpolator((cv, cu), LON); fa = RegularGridInterpolator((cv, cu), LAT)
    us = u0 + (np.arange(Wo) + 0.5) / PPM; vs = VMAX - (np.arange(Ho) + 0.5) / PPM
    P = np.stack(np.meshgrid(vs, us, indexing='ij'), -1).reshape(-1, 2)
    lon = fl(P).reshape(Ho, Wo); lat = fa(P).reshape(Ho, Wo)
    return lon, lat
def optical_img(lon, lat):
    out = np.full(lon.shape + (3,), 200, np.uint8)
    for lon0, lat0, lon1, lat1, W, H, arr in MF.TILES:
        c = ((lon - lon0) / (lon1 - lon0) * W).astype(int); r = ((lat1 - lat) / (lat1 - lat0) * H).astype(int)
        ok = (c >= 0) & (c < W) & (r >= 0) & (r < H); out[ok] = arr[r[ok], c[ok]]
    return out
def lidar_img(lon, lat):
    # MTM by local linearization (mtm8 is smooth; error < 2 cm over the corridor)
    lon0, lat0 = -73.6327, 45.4692; X0, Y0 = mtm8(lon0, lat0); e = 1e-5
    dXdl = (mtm8(lon0 + e, lat0)[0] - X0) / e; dXda = (mtm8(lon0, lat0 + e)[0] - X0) / e; dYdl = (mtm8(lon0 + e, lat0)[1] - Y0) / e; dYda = (mtm8(lon0, lat0 + e)[1] - Y0) / e
    X = X0 + dXdl * (lon - lon0) + dXda * (lat - lat0); Y = Y0 + dYdl * (lon - lon0) + dYda * (lat - lat0)
    h = L.sample(L.NDSM, L.G1, X, Y); hs = L.sample(L.HS, L.G1, X, Y); return L.colorize_ndsm(h, hs)
def street_labels(ax, u0, u1, vmax=None):
    vmax = VMAX if vmax is None else vmax
    """cross-street names as upright boxed labels at the top of the panel, and the street's own name on its axis"""
    for name, us in STREET_U.items():
        if u0 - 2 < us < u1 + 2:
            short = name.replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '').replace("d'", '')
            ax.text(us, vmax - 2, short, ha='center', va='top', fontsize=8, color='#1a1a19', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1.5), zorder=20)
    ax.text(u0 + (u1 - u0) * 0.5, 0, 'rue de Terrebonne', ha='center', va='center', fontsize=8, color='#1a1a19', style='italic', bbox=dict(facecolor='white', edgecolor='none', alpha=0.75, pad=1.2), zorder=20)
def strips(lang):
    fig, axes = plt.subplots(2 * NP, 1, figsize=(12, 2 * NP * 1.85 + 1.4))
    for k in range(NP):
        u0, u1 = k * PANEL, (k + 1) * PANEL; lon, lat = grids(u0, u1)
        for row, img in enumerate((optical_img(lon, lat), lidar_img(lon, lat))):
            ax = axes[2 * k + row]; ax.imshow(img, extent=(u0, u1, -VMAX, VMAX), interpolation='bilinear'); ax.set_xlim(u0, u1); ax.set_ylim(-VMAX, VMAX)
            ax.set_xticks([]); ax.set_yticks([]); ax.set_aspect('equal'); maps.draw_conversion(ax, u0, u1, lw=1.6)
            if row == 0:
                street_labels(ax, u0, u1)
                for b in blocks:
                    kk = int(b['block']); um = (CUM[kk] + CUM[kk + 1]) / 2
                    if u0 < um < u1 and CUM[kk + 1] - CUM[kk] > 30:
                        ax.text(um, -VMAX + 3, f"{b['optical_N']} | {b['optical_S']}", fontsize=5.5, ha='center', va='bottom', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1))
                ax.text(u0 + 2, VMAX - 2, ('Aerial imagery, daytime, undated, before the 2024 lane; by-eye count of cars on Terrebonne per block: north | south' if lang == 'en' else 'Imagerie aérienne, de jour, non datée, avant la piste de 2024; compte à l’œil des voitures sur Terrebonne par îlot : nord | sud'), fontsize=5.5, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1))
            else:
                for cls, col in COL.items():
                    pts = [c for c in cars if c['class'] == cls and u0 < c['u'] < u1 and abs(c['v']) < VMAX]
                    if pts: ax.scatter([c['u'] for c in pts], [c['v'] for c in pts], s=18, facecolors='none', edgecolors=col, linewidths=0.9, marker='s', zorder=9)
                ax.text(u0 + 2, VMAX - 2, ('City LiDAR 2015, night: height above ground; squares = objects counted as cars' if lang == 'en' else 'LiDAR 2015 de la Ville, nuit : hauteur au-dessus du sol; carrés = objets comptés comme voitures'), fontsize=5.5, ha='left', va='top', bbox=dict(facecolor='white', edgecolor='none', alpha=0.85, pad=1))
    fig.suptitle('Parked cars in the two acquisitions, panel by panel (north above; west at left)' if lang == 'en' else 'Voitures stationnées dans les deux acquisitions, panneau par panneau (nord en haut; ouest à gauche)', fontsize=10, y=0.995)
    handles = [Line2D([], [], marker='s', color='none', markerfacecolor='none', markeredgecolor=COL[c], markersize=7, label=LAB[lang][c]) for c in ('terrebonne_curb', 'lot', 'cross_street')] + [maps.conversion_handle(lang)]
    fig.legend(handles=handles, loc='lower center', ncol=2, fontsize=6.5, frameon=False)
    fig.subplots_adjust(top=0.965, bottom=0.05, left=0.01, right=0.99, hspace=0.08)
    base = os.path.join(HERE, f'figures/terrebonne_parked_cars_strips_{lang}'); fig.savefig(base + '.png', dpi=150); fig.savefig(base + '.pdf'); plt.close(fig); print('wrote', base)
def detections_map(lang):
    fig, axes = plt.subplots(NP, 1, figsize=(12, 2.05 * NP + 1.4))
    for k, ax in enumerate(axes):
        u0, u1 = k * PANEL, (k + 1) * PANEL
        ax.set_xlim(u0 - 6, u1 + 6); ax.set_ylim(-VMAX, VMAX); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor('#fbfaf7')
        for pts in maps.parcels:
            if any(u0 - 60 < u < u1 + 60 for u, v in pts): ax.add_patch(MPoly(pts, closed=True, facecolor='#ebe8df', edgecolor='white', linewidth=0.5, zorder=1))
        for pts, name in maps.streets: ax.plot([p[0] for p in pts], [p[1] for p in pts], color='#d6d1c6', linewidth=7, solid_capstyle='round', zorder=2)
        maps.draw_conversion(ax, u0 - 6, u1 + 6); street_labels(ax, u0, u1)
        for cls, col in COL.items():
            pts = [c for c in cars if c['class'] == cls and u0 - 6 < c['u'] < u1 + 6 and abs(c['v']) < VMAX]
            if pts: ax.scatter([c['u'] for c in pts], [c['v'] for c in pts], s=22, c=col, marker='s', edgecolors='black', linewidths=0.4, zorder=9)
        ax.text(u0 - 4, -VMAX + 3, f"{u0:.0f}–{u1:.0f} m", fontsize=7, color='#52514e', ha='left', va='bottom', bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1.5))
    fig.suptitle(('Car-sized objects in the City’s 2015 LiDAR (night), on today’s parcels: %d at the Terrebonne curbs, %d on lots, %d on cross streets' % (sum(c['class'] == 'terrebonne_curb' for c in cars), sum(c['class'] == 'lot' for c in cars), sum(c['class'] == 'cross_street' for c in cars))) if lang == 'en' else
                 ('Objets de la taille d’une voiture dans le LiDAR 2015 de la Ville (nuit), sur le cadastre d’aujourd’hui : %d aux bordures de Terrebonne, %d sur les lots, %d sur les rues transversales' % (sum(c['class'] == 'terrebonne_curb' for c in cars), sum(c['class'] == 'lot' for c in cars), sum(c['class'] == 'cross_street' for c in cars))), fontsize=10, y=0.995)
    handles = [Line2D([], [], marker='s', color='none', markerfacecolor=COL[c], markeredgecolor='black', markersize=7, label=LAB[lang][c]) for c in ('terrebonne_curb', 'lot', 'cross_street')] + [maps.conversion_handle(lang)]
    fig.legend(handles=handles, loc='lower center', ncol=2, fontsize=7, frameon=False)
    fig.subplots_adjust(top=0.955, bottom=0.07, left=0.02, right=0.98, hspace=0.42)
    base = os.path.join(HERE, f'figures/terrebonne_parked_cars_lidar_map_{lang}'); fig.savefig(base + '.png', dpi=200); fig.savefig(base + '.pdf'); plt.close(fig); print('wrote', base)
if __name__ == '__main__':
    detections_map(LANG); strips(LANG)
