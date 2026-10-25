#!/usr/bin/env python3
"""Oblique view of the LiDAR height SURFACE over one block (Hingston to Hampton by default): the
height-above-ground raster (0.2 m, resampled to 0.4 m) drawn as a lit 3-D surface seen from above the
south side, every cell coloured by its height class (ground, low objects, car height, garages and
sheds, houses) or green where the City's classification is vegetation. Two versions: with the trees,
and with the vegetation returns removed so the cars under the crowns show. Usage:
python3 lidar_oblique_surface.py [en|fr] [block] """
import csv, math, os, sys
import numpy as np, tifffile
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d import Axes3D  # noqa
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import CUM, NODES
import maps, lidar_strips as L
from cars_closeup import height_grid, mtm_grid
HERE = os.path.dirname(os.path.abspath(__file__)); LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
BLOCK = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 19
LD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/lidar-aerien-2015/derived/')
def load(name):
    with tifffile.TiffFile(LD + name) as tf:
        a = tf.asarray().astype(np.float32); p = tf.pages[0]; sc = p.tags['ModelPixelScaleTag'].value; tie = p.tags['ModelTiepointTag'].value
    a[a <= -9998] = np.nan; return a, (tie[3], tie[4], sc[0], sc[1])
NV, G = load('corridor_ndsm_noveg_max_0p2m.tif'); CL, _ = load('corridor_class_max_0p2m.tif')
names = [n.split(';')[0].replace('Avenue ', '').replace('Boulevard ', '') for _, _, n in NODES]
BANDS = [(-99, 0.3, '#ece7dc'), (0.3, 0.9, '#bdb6a9'), (0.9, 2.3, '#e0352b'), (2.3, 3.6, '#c9a84c'), (3.6, 99, '#5d6f8a')]
LABELS = {'en': ['ground, pavement, lawns (< 0.3 m)', 'low objects: fences, hedges, steps (0.3–0.9 m)', 'car height (0.9–2.3 m): parked cars', 'garages, sheds, vans, porches (2.3–3.6 m)', 'houses (> 3.6 m)', 'trees and shrubs (City classification)'],
          'fr': ['sol, chaussée, pelouses (< 0,3 m)', 'objets bas : clôtures, haies, marches (0,3–0,9 m)', 'hauteur d’une voiture (0,9–2,3 m) : voitures stationnées', 'garages, remises, fourgonnettes, perrons (2,3–3,6 m)', 'maisons (> 3,6 m)', 'arbres et arbustes (classification de la Ville)']}
TREE = np.array([0.25, 0.50, 0.30])
def surface(u0, u1, V, step, trees):
    lon, lat = height_grid(u0, u1, -V, V, 1 / step); X, Y = mtm_grid(lon, lat)
    h = L.sample(L.NDSM if trees else NV, L.G1 if trees else G, X, Y); cls = L.sample(CL, L.G1, X, Y)
    h = np.nan_to_num(h, nan=0.0); h = np.clip(h, 0, 22)
    # light smoothing of the ground noise only (keeps edges of cars and houses)
    from scipy.ndimage import median_filter, grey_opening
    # grey opening with a 3 x 3 window (1.2 m) removes anything narrower than a car: overhead wires, poles, isolated needles
    h = grey_opening(h, size=(3, 3)); cls = median_filter(cls, size=3)
    hm = median_filter(h, size=3); low = h < 0.5; h = np.where(low, hm, h)
    Ho, Wo = h.shape; us = u0 + (np.arange(Wo) + 0.5) * step; vs = V - (np.arange(Ho) + 0.5) * step
    U, VV = np.meshgrid(us, vs)
    rgb = np.zeros(h.shape + (3,), np.float32)
    for lo, hi, col in BANDS:
        m = (h > lo) & (h <= hi); rgb[m] = [int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    if trees: rgb[(cls == 5) & (h > 0.9)] = TREE
    # lighting from the north-west, high
    gy, gx = np.gradient(h, step); nx, ny, nz = -gx, -gy, np.ones_like(h); n = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    lx, ly, lz = math.cos(math.radians(40)) * math.cos(math.radians(135)), math.cos(math.radians(40)) * math.sin(math.radians(135)), math.sin(math.radians(40))
    shade = np.clip((nx * lx + ny * ly + nz * lz) / n, 0, 1); shade = 0.45 + 0.55 * shade
    return U, VV, h, np.clip(rgb * shade[..., None], 0, 1)
def draw(trees, lang):
    k = BLOCK; u0, u1 = CUM[k] - 6, CUM[k + 1] + 6; V = 40; step = 0.4
    U, VV, h, rgb = surface(u0, u1, V, step, trees)
    fig = plt.figure(figsize=(16, 9.4)); ax = fig.add_subplot(111, projection='3d', computed_zorder=False)
    fc = np.concatenate([rgb[:-1, :-1], np.ones(rgb[:-1, :-1].shape[:2] + (1,))], axis=2)
    ax.plot_surface(U, VV, h, rstride=1, cstride=1, facecolors=fc, shade=False, linewidth=0, antialiased=False)
    # ground lines: driving lanes and the conversion side
    for vv in (2.2, -2.2): ax.plot([u0, u1], [vv, vv], [0.15, 0.15], color='white', linewidth=0.9, linestyle=(0, (2, 3)))
    vs_ = -maps.LANE_V if (CUM[k] > maps.CAV) else maps.LANE_V
    ax.plot([u0, u1], [vs_, vs_], [0.25, 0.25], color='#e34948', linewidth=2.5, linestyle=(0, (4, 2)))
    ax.set_box_aspect((u1 - u0, 2 * V, 22 * 1.0), zoom=1.5); ax.view_init(elev=42, azim=-90)
    ax.set_xlim(u0, u1); ax.set_ylim(-V, V); ax.set_zlim(0, 22); ax.set_axis_off()
    ax.text(u0 + 2, V - 2, 16, names[k], fontsize=9, color='#3a3833'); ax.text(u1 - 12, V - 2, 16, names[k + 1], fontsize=9, color='#3a3833')
    ax.text(u0 + 1, -V + 1, 0.5, ('south side (viewer’s side)' if lang == 'en' else 'côté sud (côté de l’observateur)'), fontsize=8, color='#3a3833')
    ax.text(u0 + 1, V - 6, 0.5, ('north side' if lang == 'en' else 'côté nord'), fontsize=8, color='#3a3833')
    tl = {('en', True): 'The LiDAR surface, block Hingston to Hampton, seen obliquely from the south (trees on)', ('en', False): 'The LiDAR surface, block Hingston to Hampton, seen obliquely from the south, vegetation removed: the parked cars stand out',
          ('fr', True): 'La surface LiDAR, îlot Hingston–Hampton, vue en oblique depuis le sud (avec les arbres)', ('fr', False): 'La surface LiDAR, îlot Hingston–Hampton, vue en oblique depuis le sud, végétation retirée : les voitures stationnées ressortent'}[(lang, trees)]
    sub = {'en': 'City of Montréal airborne LiDAR 2015, flown at night before the lane; height above ground on a 0.4 m grid, lit from the north-west, every cell coloured by its height class. Red = objects of car height at the curbs and in the driveways; dotted lines = the driving lanes; dashed red = the side the proposal would turn into winter parking.',
           'fr': 'LiDAR aéroporté de la Ville de Montréal, 2015, vol de nuit avant la piste; hauteur au-dessus du sol sur une grille de 0,4 m, éclairée du nord-ouest, chaque cellule colorée selon sa classe de hauteur. Rouge = objets à hauteur de voiture aux bordures et dans les entrées; pointillés = les voies de circulation; tirets rouges = le côté que la proposition convertirait en stationnement l’hiver.'}[lang]
    fig.suptitle(tl, fontsize=14, fontweight='bold', y=0.97); fig.text(0.5, 0.925, sub, ha='center', fontsize=8.5, color='#3a3833', wrap=True)
    handles = [Patch(facecolor=c, edgecolor='#9a958b', label=l) for (lo, hi, c), l in zip(BANDS, LABELS[lang])] + ([Patch(facecolor=TREE, edgecolor='#9a958b', label=LABELS[lang][5])] if trees else []) + [maps.conversion_handle(lang)]
    fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, 0.02))
    fig.subplots_adjust(left=0.0, right=1.0, top=0.99, bottom=0.09)
    base = os.path.join(HERE, f'figures/terrebonne_lidar_oblique_surface_{names[k].lower().replace(" ", "")}_{"trees" if trees else "notrees"}_{lang}')
    fig.savefig(base + '.png', dpi=200, facecolor='white'); fig.savefig(base + '.pdf', facecolor='white', dpi=200); plt.close(fig); print('wrote', base)
if __name__ == '__main__':
    draw(True, LANG); draw(False, LANG)
