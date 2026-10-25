#!/usr/bin/env python3
"""Cars parked on rue de Terrebonne itself, block by block and by side, in the two acquisitions:
the Gouvernement du Québec aerial imagery (daytime, leaf-off spring, lane markings present so
after June 2024; counted by eye on the block strips) and the City's 2015 LiDAR (flown at night,
00:00–04:00 local by the GPS times, leaf-on; car-sized objects 0.9–2.3 m above ground detected by
lidar_cars.py). North side bars up, south side down. Usage: python3 cars_chart.py [en|fr]"""
import csv, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from frame import CUM, STREET_U, LENGTH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from maps import CAV, CONV_SHORT
HERE = os.path.dirname(os.path.abspath(__file__)); LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
rows = list(csv.DictReader(open(os.path.join(HERE, 'on_street_cars_by_block.csv'), encoding='utf-8')))
fig, axes = plt.subplots(2, 1, figsize=(12, 6.2))
spec = [('optical', '#2a78d6', 'A. Aerial imagery, daytime, spring (after June 2024: the lane markings are visible); counted by eye' if LANG == 'en' else 'A. Imagerie aérienne, de jour, au printemps (après juin 2024 : le marquage de la piste est visible); compté à l’œil'),
        ('lidar_by_eye', '#b9b0f0', 'B. City LiDAR 2015, two weeknights (Sun–Mon west of Walkley, Mon–Tue east; 00:00–03:50 local), before the lane: car-shaped objects counted by eye on the height raster (light), of which found by the automatic detector (dark)' if LANG == 'en' else 'B. LiDAR 2015 de la Ville, deux nuits de semaine (dim.–lun. à l’ouest de Walkley, lun.–mar. à l’est; 0 h–3 h 50 locale), avant la piste : objets en forme de voiture comptés à l’œil sur le raster de hauteur (clair), dont trouvés par le détecteur automatique (foncé)')]
for ax, (key, col, title) in zip(axes, spec):
    for r in rows:
        k = int(r['block']); x0, x1 = CUM[k] + 3, CUM[k + 1] - 3
        n, s = int(r[f'{key}_N']), int(r[f'{key}_S'])
        if n: ax.add_patch(Rectangle((x0, 0), x1 - x0, n, facecolor=col, edgecolor='white', linewidth=0.6))
        if s: ax.add_patch(Rectangle((x0, -s), x1 - x0, s, facecolor=col, edgecolor='white', linewidth=0.6))
        if key == 'lidar_by_eye':
            dn, ds = int(r['lidar_N']), int(r['lidar_S'])
            if dn: ax.add_patch(Rectangle((x0, 0), x1 - x0, dn, facecolor='#6250d6', edgecolor='white', linewidth=0.6))
            if ds: ax.add_patch(Rectangle((x0, -ds), x1 - x0, ds, facecolor='#6250d6', edgecolor='white', linewidth=0.6))
    ax.axhline(0, color='#52514e', linewidth=0.8)
    ax.plot([0, CAV], [0.4, 0.4], color='#e34948', linewidth=3, linestyle=(0, (4, 2)), zorder=5); ax.plot([CAV, LENGTH], [-0.4, -0.4], color='#e34948', linewidth=3, linestyle=(0, (4, 2)), zorder=5)
    for name, us in STREET_U.items():
        short = name.replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '').replace("d'", '')
        ax.axvline(us, color='#e4e1d8', linewidth=0.6, zorder=0); ax.text(us, 13.3, short, rotation=90, ha='center', va='bottom', fontsize=6, color='#52514e')
    ax.set_xlim(-10, LENGTH + 10); ax.set_ylim(-13, 13); ax.set_yticks([-12, -8, -4, 0, 4, 8, 12]); ax.set_yticklabels(['12', '8', '4', '0', '4', '8', '12'], fontsize=7)
    ax.set_ylabel('cars on Terrebonne\nsouth  |  north' if LANG == 'en' else 'voitures sur Terrebonne\nsud  |  nord', fontsize=7.5)
    import textwrap; ax.text(0, 1.3, '\n'.join(textwrap.wrap(title, 150)), transform=ax.transAxes, fontsize=9, ha='left', va='bottom')
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    ax.tick_params(axis='x', labelsize=7)
tot_o = sum(int(r['optical_N']) + int(r['optical_S']) for r in rows); tot_l = sum(int(r['lidar_by_eye_N']) + int(r['lidar_by_eye_S']) for r in rows); tot_d = sum(int(r['lidar_N']) + int(r['lidar_S']) for r in rows)
axes[0].text(0.995, 0.95, (f'{tot_o} cars' if LANG == 'en' else f'{tot_o} voitures'), transform=axes[0].transAxes, ha='right', va='top', fontsize=9, fontweight='bold')
axes[1].text(0.995, 0.95, (f'{tot_l} cars by eye, {tot_d} detected' if LANG == 'en' else f'{tot_l} voitures à l’œil, {tot_d} détectées'), transform=axes[1].transAxes, ha='right', va='top', fontsize=9, fontweight='bold')
axes[1].set_xlabel('Distance along rue de Terrebonne from the west end of the lane (m)' if LANG == 'en' else 'Distance le long de la rue de Terrebonne depuis l’extrémité ouest de la piste (m)', fontsize=8)
fig.legend(handles=[Line2D([], [], color='#e34948', linewidth=3, linestyle=(0, (4, 2)), label=CONV_SHORT[LANG])], loc='lower center', fontsize=7, frameon=False)
fig.subplots_adjust(top=0.90, bottom=0.14, left=0.07, right=0.99, hspace=0.8)
base = os.path.join(HERE, f'figures/terrebonne_on_street_cars_{LANG}'); fig.savefig(base + '.png', dpi=220); fig.savefig(base + '.pdf'); print('wrote', base)
