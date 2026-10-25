#!/usr/bin/env python3
"""Oblique view of the City's 2015 LiDAR point cloud over one block (Hingston to Hampton), every
return coloured by what it is: ground, low objects, car height, garages and sheds, houses, trees
(vegetation by the City's classification), drawn in an oblique orthographic projection of the
street frame (looking north-north-east from above the south side), with the colour legend.
Input: block_hingston_hampton_points.csv written by pdal (pipeline_block_hingston.json) in the
LiDAR data folder. Usage: python3 lidar_oblique.py [en|fr]"""
import csv, math, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import to_EN, to_uv, from_uv, from_EN, CUM, STREET_U
from mtm import mtm8
import maps
HERE = os.path.dirname(os.path.abspath(__file__)); LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
LD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/lidar-aerien-2015/derived/')
P = np.loadtxt(LD + 'block_hingston_hampton_points.csv', delimiter=',', skiprows=1)
X, Y, Z, H, C = P[:, 0], P[:, 1], P[:, 2], P[:, 3], P[:, 4].astype(int)
# MTM -> lon/lat (local linearization) -> street frame
lon0, lat0 = -73.6327, 45.4692; X0, Y0 = mtm8(lon0, lat0); e = 1e-5
M = np.array([[(mtm8(lon0 + e, lat0)[0] - X0) / e, (mtm8(lon0, lat0 + e)[0] - X0) / e], [(mtm8(lon0 + e, lat0)[1] - Y0) / e, (mtm8(lon0, lat0 + e)[1] - Y0) / e]]); Mi = np.linalg.inv(M)
d = Mi @ np.vstack([X - X0, Y - Y0]); LON = lon0 + d[0]; LAT = lat0 + d[1]
EN = np.array([to_EN(a, b) for a, b in zip(LON, LAT)]); UV = np.array([to_uv(a, b) for a, b in EN]); U, V = UV[:, 0], UV[:, 1]
k = 19; u0, u1 = CUM[k] - 6, CUM[k + 1] + 6; keep = (U > u0) & (U < u1) & (np.abs(V) < 44) & (H > -0.5) & (H < 25)
U, V, H, C = U[keep], V[keep], H[keep], C[keep]
# colour classes
BANDS = [(-1, 0.3, '#e9e4d8'), (0.3, 0.9, '#b8b2a6'), (0.9, 2.3, '#e0352b'), (2.3, 3.6, '#c9a84c'), (3.6, 99, '#5d6f8a')]
LABELS = {'en': ['ground, pavement, lawns (< 0.3 m)', 'low objects: fences, hedges, steps (0.3–0.9 m)', 'car height (0.9–2.3 m): parked cars', 'garages, sheds, vans, porches (2.3–3.6 m)', 'houses (> 3.6 m)', 'trees and shrubs (City classification, class 5)'],
          'fr': ['sol, chaussée, pelouses (< 0,3 m)', 'objets bas : clôtures, haies, marches (0,3–0,9 m)', 'hauteur d’une voiture (0,9–2,3 m) : voitures stationnées', 'garages, remises, fourgonnettes, perrons (2,3–3,6 m)', 'maisons (> 3,6 m)', 'arbres et arbustes (classification de la Ville, classe 5)']}
col = np.empty((len(U), 3))
for lo, hi, c in BANDS:
    m = (H > lo) & (H <= hi); col[m] = [int(c[i:i + 2], 16) / 255 for i in (1, 3, 5)]
veg = C == 5; col[veg] = [0.22, 0.52, 0.30]
# oblique orthographic projection: look from the south (v < 0) toward the north, elevated; x = u, y = v*cos(tilt) + h*sin(tilt)
TILT = math.radians(55); yscr = V * math.cos(TILT) + H * math.sin(TILT)
order = np.argsort(V)[::-1]  # far (north) first, near (south) last: painter's order
# light shading by height within class for relief
shade = 0.75 + 0.25 * np.clip(H / 8, 0, 1); col = np.clip(col * shade[:, None], 0, 1)
fig, ax = plt.subplots(figsize=(14, 9.0))
ax.scatter(U[order], yscr[order], s=0.9, c=col[order], marker='s', linewidths=0, rasterized=True)
# the driving-lane boundaries and the conversion side, on the ground
for vv in (2.2, -2.2): ax.plot([u0, u1], [vv * math.cos(TILT)] * 2, color='white', linewidth=0.8, linestyle=(0, (3, 3)))
cav = maps.CAV; vs = -maps.LANE_V
ax.plot([u0, u1], [vs * math.cos(TILT)] * 2, color='#e34948', linewidth=2.5, linestyle=(0, (4, 2)))
for name, us in STREET_U.items():
    if u0 < us < u1: pass
ax.text(u0 + 1, 46 * math.cos(TILT) + 1, 'Hingston', fontsize=9, ha='left', color='#3a3833'); ax.text(u1 - 1, 46 * math.cos(TILT) + 1, 'Hampton', fontsize=9, ha='right', color='#3a3833')
ax.text(u0 + 1, -43 * math.cos(TILT) - 2, ('south side (viewer’s side)' if LANG == 'en' else 'côté sud (côté de l’observateur)'), fontsize=8, color='#3a3833', va='top')
ax.text(u0 + 1, 40 * math.cos(TILT) - 1, ('north side' if LANG == 'en' else 'côté nord'), fontsize=8, color='#3a3833', va='top')
ax.set_aspect('equal'); ax.set_xlim(u0, u1); ax.set_ylim(-46 * math.cos(TILT) - 3, 46 * math.cos(TILT) + 16); ax.set_xticks([]); ax.set_yticks([])
for sp in ax.spines.values(): sp.set_visible(False)
ax.plot([u1 - 25, u1 - 5], [-44 * math.cos(TILT)] * 2, color='#3a3833', linewidth=2.5); ax.text(u1 - 15, -44 * math.cos(TILT) - 1.2, '20 m', ha='center', va='top', fontsize=8)
T = {'en': ('The LiDAR point cloud, block Hingston to Hampton, seen obliquely from the south', f'City of Montréal airborne LiDAR 2015, night; {len(U):,} returns, each coloured by its height above ground or, for vegetation, by the City’s classification. The red boxes at the curbs and in the driveways are parked cars; the dotted lines bound the driving lanes.'),
     'fr': ('Le nuage de points LiDAR, îlot Hingston–Hampton, vu en oblique depuis le sud', f'LiDAR aéroporté de la Ville de Montréal, 2015, nuit; {len(U):,} retours, chacun coloré selon sa hauteur au-dessus du sol ou, pour la végétation, selon la classification de la Ville. Les boîtes rouges aux bordures et dans les entrées sont des voitures stationnées; les pointillés bornent les voies de circulation.')}[LANG]
fig.suptitle(T[0], fontsize=13, fontweight='bold', y=0.97); fig.text(0.5, 0.925, T[1].replace(',', ' ' if LANG == 'fr' else ','), ha='center', fontsize=8.5, color='#3a3833', wrap=True)
handles = [Patch(facecolor=c, edgecolor='#9a958b', label=l) for (lo, hi, c), l in zip(BANDS, LABELS[LANG])] + [Patch(facecolor='#388450', edgecolor='#9a958b', label=LABELS[LANG][5]), maps.conversion_handle(LANG)]
fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.02))
fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.14)
base = os.path.join(HERE, f'figures/terrebonne_lidar_oblique_hingston_{LANG}'); fig.savefig(base + '.png', dpi=200, facecolor='white'); fig.savefig(base + '.pdf', facecolor='white', dpi=200); plt.close(fig); print('wrote', base, len(U))
