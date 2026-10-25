#!/usr/bin/env python3
"""Distribution of off-street parking along rue de Terrebonne, block face by block face:
top, the 1954-55 reading (garage as built / none); bottom, the present-day combination
(garage and driveway / garage only / driveway only / neither). North side bars grow upward,
south side bars downward; x = distance along the street from the west end of the lane;
the south face missing in 1954-55 (sheet 787-8) is hatched. Usage: python3 overview_chart.py [en|fr]"""
import csv, os, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from frame import CUM, NODES, STREET_U, LENGTH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from maps import CATS, CATS_TODAY, category, category_today, CAV, CONV_SHORT
HERE = os.path.dirname(os.path.abspath(__file__))
LANG = sys.argv[1] if len(sys.argv) > 1 else 'en'
rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')) if r['u_m']]
for r in rows: r['u'] = float(r['u_m']); r['cat'] = category(r); r['cat_today'] = category_today(r)
def block_of(u):
    for k in range(len(CUM) - 1):
        if CUM[k] <= u < CUM[k + 1]: return k
    return len(CUM) - 2
C54 = [('gar', 'Garage as built (1954–55)', 'Garage d’origine (1954–1955)', '#2a78d6'), ('none', 'No garage as built', 'Sans garage d’origine', '#eb6834')]
def cat54(r): return None if r['cat'] in (None, 'corner', 'other') else ('gar' if r['garage_1954'] == 'yes' else 'none')
CTD = [(k, en, fr, col) for k, en, fr, col, mk in CATS_TODAY if k in ('both', 'gar_only', 'drive_only', 'neither')]
def tally(fn, keys):
    T = {}
    for r in rows:
        c = fn(r)
        if c not in keys: continue
        T.setdefault((block_of(r['u']), r['side']), {}).setdefault(c, 0); T[(block_of(r['u']), r['side'])][c] += 1
    return T
HAMPTON, MELROSE = STREET_U['Avenue de Hampton'], STREET_U['Avenue de Melrose']
def panel(ax, T, cats, title):
    for (k, side), d in T.items():
        x0, x1 = CUM[k] + 3, CUM[k + 1] - 3; sgn = 1 if side == 'N' else -1; base = 0
        for key, en, fr, col in cats:
            n = d.get(key, 0)
            if n: ax.add_patch(Rectangle((x0, base if sgn > 0 else base - n), x1 - x0, n, facecolor=col, edgecolor='white', linewidth=0.6)); base += sgn * n
    ax.add_patch(Rectangle((HAMPTON + 3, -9.5), MELROSE - HAMPTON - 6, 9.5, facecolor='none', edgecolor='#8a8884', hatch='////', linewidth=0.6))
    ax.axhline(0, color='#52514e', linewidth=0.8)
    ax.plot([0, CAV], [0.35, 0.35], color='#e34948', linewidth=3, linestyle=(0, (4, 2)), zorder=5); ax.plot([CAV, LENGTH], [-0.35, -0.35], color='#e34948', linewidth=3, linestyle=(0, (4, 2)), zorder=5)
    for name, us in STREET_U.items():
        short = name.replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '').replace("d'", '')
        ax.axvline(us, color='#e4e1d8', linewidth=0.6, zorder=0); ax.text(us, 10.3, short, rotation=90, ha='center', va='bottom', fontsize=6, color='#52514e')
    ax.set_xlim(-10, LENGTH + 10); ax.set_ylim(-10, 10); ax.set_yticks([-8, -4, 0, 4, 8]); ax.set_yticklabels(['8', '4', '0', '4', '8'], fontsize=7)
    ax.set_ylabel(('buildings\nsouth  |  north' if LANG == 'en' else 'bâtiments\nsud  |  nord'), fontsize=7.5)
    ax.text(0, 1.42, title, transform=ax.transAxes, fontsize=9.5, ha='left', va='bottom')
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    ax.tick_params(axis='x', labelsize=7)
    handles = [Rectangle((0, 0), 1, 1, facecolor=col, edgecolor='white', label=(en if LANG == 'en' else fr)) for key, en, fr, col in cats]
    handles.append(Rectangle((0, 0), 1, 1, facecolor='none', edgecolor='#8a8884', hatch='////', label=('Sheet 787-8 missing (south, Hampton–Melrose)' if LANG == 'en' else 'Feuillet 787-8 manquant (sud, Hampton–Melrose)')))
    from matplotlib.lines import Line2D
    handles.append(Line2D([], [], color='#e34948', linewidth=3, linestyle=(0, (4, 2)), label=CONV_SHORT[LANG]))
    ax.legend(handles=handles, loc='lower left', ncol=2, fontsize=6.8, frameon=False, bbox_to_anchor=(0, -0.62))
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 7.6))
panel(a1, tally(cat54, {'gar', 'none'}), C54, 'A. 1954–55 plans: buildings with a Terrebonne address, by block face' if LANG == 'en' else 'A. Plans de 1954–1955 : bâtiments adressés sur Terrebonne, par face d’îlot')
panel(a2, tally(lambda r: r['cat_today'], {k for k, *_ in CTD}), CTD, 'B. Garage as built and driveway or apron today (aerial imagery, October 2026)' if LANG == 'en' else 'B. Garage d’origine et entrée ou aire pavée aujourd’hui (imagerie aérienne, octobre 2026)')
a2.set_xlabel('Distance along rue de Terrebonne from the west end of the lane (m); west at left, Girouard at right' if LANG == 'en' else 'Distance le long de la rue de Terrebonne depuis l’extrémité ouest de la piste (m); ouest à gauche, Girouard à droite', fontsize=8)
fig.subplots_adjust(top=0.88, bottom=0.17, left=0.06, right=0.99, hspace=1.35)
base = os.path.join(HERE, f'figures/terrebonne_garages_distribution_{LANG}')
fig.savefig(base + '.png', dpi=220); fig.savefig(base + '.pdf'); print('wrote', base)
