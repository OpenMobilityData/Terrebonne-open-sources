#!/usr/bin/env python3
"""Standalone image (PDF + PNG): rue de Terrebonne at night in the City's 2015 LiDAR, vegetation
removed, every surface coloured by its height above ground so that parked cars (0.9–2.3 m) stand
out, over the stretch Grand to Melrose in two rows, with a magnifier inset on one detected car.
Usage: python3 cars_hero.py [en|fr]"""
import csv, math, os, sys
import numpy as np, tifffile
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, ConnectionPatch, Patch
from matplotlib.lines import Line2D
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from frame import from_EN, from_uv, CUM, NODES, STREET_U
import maps, lidar_strips as L
from cars_closeup import height_grid, mtm_grid
HERE = os.path.dirname(os.path.abspath(__file__)); LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
MODE = sys.argv[2] if len(sys.argv) > 2 else 'cars'  # cars | parking | both
LD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/lidar-aerien-2015/derived/')
def load(name):
    with tifffile.TiffFile(LD + name) as tf:
        a = tf.asarray().astype(np.float32); p = tf.pages[0]; sc = p.tags['ModelPixelScaleTag'].value; tie = p.tags['ModelTiepointTag'].value
    a[a <= -9998] = np.nan; return a, (tie[3], tie[4], sc[0], sc[1])
NV, G = load('corridor_ndsm_noveg_max_0p2m.tif')
HS = L.hillshade(np.where(np.isnan(NV), 0, NV), G[2], az=315, alt=50)
# colour classes (height above ground, vegetation removed)
BANDS = [(-99, 0.3, '#f1ede4'), (0.3, 0.9, '#cfc9bd'), (0.9, 2.3, '#e0352b'), (2.3, 3.6, '#c9a84c'), (3.6, 99, '#5d6f8a')]
LABELS = {'en': ['ground, pavement, lawns (< 0.3 m)', 'low objects: fences, hedges, steps (0.3–0.9 m)', 'car height (0.9–2.3 m): parked cars', 'garages, sheds, vans, porches (2.3–3.6 m)', 'houses (> 3.6 m)'],
          'fr': ['sol, chaussée, pelouses (< 0,3 m)', 'objets bas : clôtures, haies, marches (0,3–0,9 m)', 'hauteur d’une voiture (0,9–2,3 m) : voitures stationnées', 'garages, remises, fourgonnettes, perrons (2,3–3,6 m)', 'maisons (> 3,6 m)']}
def colorize(h, hs):
    rgb = np.zeros(h.shape + (3,), np.float32); hh = np.nan_to_num(h, nan=0.0)
    for lo, hi, col in ([(lo, hi, ('#b8b2a6' if lo == 0.9 else c)) for lo, hi, c in BANDS] if MODE == 'parking' else BANDS):
        c = np.array([int(col[i:i + 2], 16) / 255 for i in (1, 3, 5)]); m = (hh > lo) & (hh <= hi); rgb[m] = c
    rgb *= (0.6 + 0.4 * np.nan_to_num(hs, nan=0.6))[..., None]; return np.clip(rgb, 0, 1)
cars = list(csv.DictReader(open(os.path.join(HERE, 'lidar_cars.csv'), encoding='utf-8')))
for c in cars:
    for k in ('u_m', 'v_m', 'length_m', 'width_m', 'mean_height_m', 'area_m2'): c[k] = float(c[k])
def render(u0, u1, V, ppm, vc=0.0):
    lon, lat = height_grid(u0, u1, vc - V, vc + V, ppm); X, Y = mtm_grid(lon, lat)
    return colorize(L.sample(NV, G, X, Y), L.sample(HS, G, X, Y))
ROWS = [(STREET_U['Boulevard Grand'], STREET_U['Avenue de Hampton']), (STREET_U['Avenue de Hampton'], STREET_U['Avenue de Melrose'])]
V = 38; PPM = 14
# magnifier target: a curb car with a clean car signature (area 8.5–11.5 m², length 4.2–4.9, height 1.3–1.55), in the second row
cands = [c for c in cars if c['class'] == 'terrebonne_curb' and ROWS[1][0] < c['u_m'] < ROWS[1][1] and 8.5 <= c['area_m2'] <= 11.5 and 4.2 <= c['length_m'] <= 4.9 and 1.3 <= c['mean_height_m'] <= 1.55]
tgt = min(cands, key=lambda c: abs(c['mean_height_m'] - 1.45)) if cands else max([c for c in cars if c['class'] == 'terrebonne_curb' and ROWS[1][0] < c['u_m'] < ROWS[1][1]], key=lambda c: c['area_m2'])
fig = plt.figure(figsize=(16, 9.6 if MODE == 'cars' else 10.4)); gs = fig.add_gridspec(2, 1, left=0.015, right=0.985, top=0.885, bottom=(0.115 if MODE == 'cars' else 0.16), hspace=0.16)
axes = []
for i, (u0, u1) in enumerate(ROWS):
    ax = fig.add_subplot(gs[i, 0]); axes.append(ax)
    ax.imshow(render(u0 - 4, u1 + 4, V, PPM), extent=(u0 - 4, u1 + 4, -V, V), interpolation='bilinear'); ax.set_xlim(u0 - 4, u1 + 4); ax.set_ylim(-V, V); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color('#9a958b')
    for pts in maps.parcels:
        if any(u0 - 5 < u < u1 + 5 and -V < v < V for u, v in pts): ax.plot([p[0] for p in pts] + [pts[0][0]], [p[1] for p in pts] + [pts[0][1]], color='white', linewidth=0.45, alpha=0.55)
    for vv in (2.2, -2.2): ax.axhline(vv, color='white', linewidth=0.6, linestyle=(0, (2, 3)), alpha=0.8)
    maps.draw_conversion(ax, u0 - 4, u1 + 4, lw=2.2)
    if MODE in ('parking', 'both'):
        for key, en_, fr_, col_, mk in maps.CATS_TODAY:
            pts = [r for r in maps.rows if r['cat_today'] == key and u0 - 4 < r['u'] < u1 + 4 and abs(r['v']) < V]
            if pts: ax.scatter([r['u'] for r in pts], [r['v'] for r in pts], s=64 if mk != 'D' else 40, c=col_, marker=mk, edgecolors='black', linewidths=0.9, zorder=11)
    for name, us in STREET_U.items():
        if u0 - 2 < us < u1 + 2:
            short = name.replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '').replace("d'", '')
            ax.text(us, V + 1.2, short, ha='center', va='bottom', fontsize=8, color='#3a3833')
    ax.text(u0 - 2, V - 1.5, ('north side' if LANG == 'en' else 'côté nord'), fontsize=7, color='#3a3833', ha='left', va='top'); ax.text(u0 - 2, -V + 1.5, ('south side' if LANG == 'en' else 'côté sud'), fontsize=7, color='#3a3833', ha='left', va='bottom')
# scale bar on the bottom row
ax = axes[0]; u0r = ROWS[0][0]; ax.plot([u0r + 6, u0r + 56], [-V + 4, -V + 4], color='#3a3833', linewidth=2.5); ax.text(u0r + 31, -V + 6, '50 m', ha='center', fontsize=8, color='#3a3833'); ax = axes[1]
# magnifier: ring on the target in the bottom row, zoom in an inset over the top-right of the bottom row's house band
cu, cv = tgt['u_m'], tgt['v_m']; r = 4.0
if MODE == 'parking': tgt = None
if tgt: ax.add_patch(Circle((cu, cv), r, facecolor='none', edgecolor='black', linewidth=1.6, zorder=12))
if tgt:
    Z = 6.0; zoom = render(cu - Z, cu + Z, Z, 50, vc=cv)  # square window ±6 m centred on the car
    ins = ax.inset_axes([0.80, 0.08, 0.19, 0.84]); ins.imshow(zoom, extent=(cu - Z, cu + Z, -Z + cv, Z + cv), interpolation='nearest')
    ins.set_xlim(cu - Z, cu + Z); ins.set_ylim(cv - Z, cv + Z); ins.set_aspect('equal'); ins.set_xticks([]); ins.set_yticks([])
    for sp in ins.spines.values(): sp.set_color('black'); sp.set_linewidth(1.6)
    ins.add_patch(Circle((cu, cv), r, facecolor='none', edgecolor='black', linewidth=1.2))
    ins.plot([cu - tgt['length_m'] / 2, cu + tgt['length_m'] / 2], [cv - 3.2, cv - 3.2], color='black', linewidth=1.2); ins.text(cu, cv - 3.5, f"{tgt['length_m']:.1f} m", ha='center', va='top', fontsize=7)
    ins.plot([cu + 3.0, cu + 3.0], [cv - tgt['width_m'] / 2, cv + tgt['width_m'] / 2], color='black', linewidth=1.2); ins.text(cu + 3.3, cv, f"{tgt['width_m']:.1f} m", ha='left', va='center', fontsize=7)
    ins.set_title((f"one detected car, {50} px/m: {tgt['length_m']:.1f} × {tgt['width_m']:.1f} m, {tgt['mean_height_m']:.2f} m high" if LANG == 'en' else f"une voiture détectée, 50 px/m : {tgt['length_m']:.1f} × {tgt['width_m']:.1f} m, {tgt['mean_height_m']:.2f} m de haut").replace('.', ',' if LANG == 'fr' else '.'), fontsize=7.5)
    con = ConnectionPatch(xyA=(cu + r * 0.7, cv + r * 0.7), coordsA=ax.transData, xyB=(cu - Z, cv - Z), coordsB=ins.transData, color='black', linewidth=0.9); ax.add_artist(con)
    con2 = ConnectionPatch(xyA=(cu + r * 0.7, cv - r * 0.7), coordsA=ax.transData, xyB=(cu - Z, cv + Z), coordsB=ins.transData, color='black', linewidth=0.9); ax.add_artist(con2)
T = {'en': ("Rue de Terrebonne at night, 2015: every surface by its height, trees removed", "City of Montréal airborne LiDAR, flown on two weeknights between midnight and 4 a.m., before the bike lane; Grand to Melrose, north side above. Red = objects of car height at the curbs and in driveways. Dotted lines: the driving lanes (2.2 m either side of the axis), where a moving car would appear; dashed red: the side the proposal would turn into winter parking."),
     'fr': ("La rue de Terrebonne la nuit, en 2015 : chaque surface selon sa hauteur, arbres retirés", "LiDAR aéroporté de la Ville de Montréal, deux nuits de semaine entre minuit et 4 h, avant la piste cyclable; de Grand à Melrose, côté nord en haut. Rouge = objets à hauteur de voiture aux bordures et dans les entrées. Pointillés : les voies de circulation (2,2 m de part et d’autre de l’axe), où apparaîtrait une voiture en mouvement; tirets rouges : le côté que la proposition convertirait en stationnement l’hiver.")}[LANG]
TT = {('parking', 'en'): ("Rue de Terrebonne at night, 2015: the buildings, and which have off-street parking", "The same LiDAR surfaces (trees removed, car-height objects shown in grey here), with one marker per building: built with a garage in 1954–55 and/or a driveway or apron visible on today's aerial imagery."),
      ('parking', 'fr'): ("La rue de Terrebonne la nuit, en 2015 : les bâtiments, et lesquels ont un stationnement hors rue", "Les mêmes surfaces LiDAR (arbres retirés, objets à hauteur de voiture en gris ici), avec un repère par bâtiment : construit avec un garage en 1954–1955 et/ou entrée ou aire pavée visible sur l’imagerie aérienne d’aujourd’hui."),
      ('both', 'en'): ("Rue de Terrebonne at night, 2015: parked cars (red) and the buildings' own parking (markers)", "LiDAR surfaces by height, trees removed; red = car-height objects at the curbs and in driveways that night; one marker per building: garage as built (1954–55) and/or driveway visible today."),
      ('both', 'fr'): ("La rue de Terrebonne la nuit, en 2015 : voitures stationnées (rouge) et stationnement propre aux bâtiments (repères)", "Surfaces LiDAR selon la hauteur, arbres retirés; rouge = objets à hauteur de voiture aux bordures et dans les entrées cette nuit-là; un repère par bâtiment : garage d’origine (1954–1955) et/ou entrée visible aujourd’hui.")}
if MODE != 'cars': T = TT[(MODE, LANG)]
fig.suptitle(T[0], fontsize=15, y=0.975, fontweight='bold'); fig.text(0.5, 0.925, T[1], ha='center', va='center', fontsize=8.5, color='#3a3833', wrap=True)
handles = [Patch(facecolor=('#b8b2a6' if (MODE == 'parking' and lo == 0.9) else col), edgecolor='#9a958b', label=(lab if not (MODE == 'parking' and lo == 0.9) else ('car height (0.9–2.3 m), not emphasised here' if LANG == 'en' else 'hauteur d’une voiture (0,9–2,3 m), non soulignée ici'))) for (lo, hi, col), lab in zip(BANDS, LABELS[LANG])] + [maps.conversion_handle(LANG)]
if MODE in ('parking', 'both'):
    handles += [Line2D([], [], marker=mk, color='none', markerfacecolor=col_, markeredgecolor='black', markersize=8, label=(en_ if LANG == 'en' else fr_)) for key, en_, fr_, col_, mk in maps.CATS_TODAY if key in ('both', 'gar_only', 'drive_only', 'neither', 'corner')]
fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, 0.035))
src = {'en': "Source: Ville de Montréal, LiDAR aérien 2015 (CC-BY 4.0), height above ground from the point cloud with vegetation returns removed (pdal), 0.2 m cells, hillshaded; parcels: unités d'évaluation foncière (CC-BY 4.0). On the whole street, 183 car-height objects were counted by eye at the Terrebonne curbs that night (north 93, south 90); an automatic detector finds 85. Terrebonne-open-sources, 1954-underwriters-plans-terrebonne-garages.",
       'fr': "Source : Ville de Montréal, LiDAR aérien 2015 (CC-BY 4.0), hauteur au-dessus du sol calculée du nuage de points sans les retours de végétation (pdal), cellules de 0,2 m, ombrage; parcelles : unités d'évaluation foncière (CC-BY 4.0). Sur toute la rue, 183 objets à hauteur de voiture comptés à l'œil aux bordures de Terrebonne cette nuit-là (nord 93, sud 90); un détecteur automatique en trouve 85. Terrebonne-open-sources, 1954-underwriters-plans-terrebonne-garages."}[LANG]
fig.text(0.5, 0.012, src, ha='center', va='bottom', fontsize=6.6, color='#52514e', wrap=True)
base = os.path.join(HERE, f'figures/terrebonne_parked_cars_lidar_hero_{LANG}' if MODE == 'cars' else f'figures/terrebonne_lidar_hero_{MODE}_{LANG}'); fig.savefig(base + '.png', dpi=220, facecolor='white'); fig.savefig(base + '.pdf', facecolor='white'); plt.close(fig); print('wrote', base, 'target', (tgt['u_m'], tgt['v_m'], tgt['length_m'], tgt['width_m'], tgt['mean_height_m']) if tgt else 'none')
