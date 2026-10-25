#!/usr/bin/env python3
"""Two maps of the buildings fronting rue de Terrebonne, colour-coded by off-street parking as
built (1954-55 plans) and by frontage: (1) on the 1954-55 Underwriters' sheets, georeferenced
and straightened along the street (needs the scans, which are not in the repository);
(2) on a base drawn from the City's open data (geobase street centrelines and assessment-roll
parcels, CC-BY 4.0). Both use the street frame of frame.py (u along Terrebonne, v across),
cut into panels west to east. Usage: python3 maps.py [--no-sheets] [--lang en|fr]"""
import csv, json, math, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle
from matplotlib.lines import Line2D
from frame import to_EN, to_uv, from_uv, LENGTH, STREET_U, T
HERE = os.path.dirname(os.path.abspath(__file__))
LANG = sys.argv[sys.argv.index('--lang') + 1] if '--lang' in sys.argv else 'en'
SCANS = os.path.expanduser('~/Terrebonne-data/third-party/fire-insurance-plans-1954/174390_%s.jpg')
NPANEL = 5; VMAX = 62.0
PANEL = LENGTH / NPANEL
# categories: fixed order and colours (validated palette; shapes carry the frontage so colour is never alone)
CATS = [  # key, label en, label fr, colour, marker
    ('gar_terr', 'Garage as built, door on Terrebonne', 'Garage d’origine, porte sur Terrebonne', '#2a78d6', 'o'),
    ('gar_cross', 'Garage as built, door on the cross street or a lane', 'Garage d’origine, porte sur la rue transversale ou une ruelle', '#1baf7a', 'o'),
    ('none', 'No garage as built', 'Sans garage d’origine', '#eb6834', 'o'),
    ('corner', 'Corner building addressed on the cross street (garage: ring)', 'Bâtiment de coin adressé sur la rue transversale (garage : anneau)', '#8a8884', 's'),
    ('other', 'Church, presbytery, vacant lot, or sheet missing', 'Église, presbytère, terrain vacant ou feuillet manquant', '#ffffff', 'D'),
]
CATS_TODAY = [
    ('both', 'Garage as built and a driveway or apron today', 'Garage d\u2019origine et entr\u00e9e ou aire pav\u00e9e aujourd\u2019hui', '#2a78d6', 'o'),
    ('gar_only', 'Garage as built, no driveway or apron visible today', 'Garage d\u2019origine, sans entr\u00e9e visible aujourd\u2019hui', '#6250d6', 'o'),
    ('drive_only', 'No garage as built, driveway or parking pad today', 'Sans garage d\u2019origine, entr\u00e9e ou aire de stationnement aujourd\u2019hui', '#1baf7a', 'o'),
    ('neither', 'Neither', 'Ni l\u2019un ni l\u2019autre', '#eb6834', 'o'),
    ('corner', 'Corner building addressed on the cross street', 'B\u00e2timent de coin adress\u00e9 sur la rue transversale', '#8a8884', 's'),
    ('other', 'Church, presbytery, vacant lot, not checked, or sheet missing', '\u00c9glise, presbyt\u00e8re, terrain vacant, non v\u00e9rifi\u00e9 ou feuillet manquant', '#ffffff', 'D'),
]
CAV = STREET_U['Boulevard Cavendish']; LANE_V = 4.6
CONV_LABEL = {'en': 'Side where the lane is to be converted to parking each winter under the proposal (the lane running with traffic: north side west of Cavendish, south side east of it; the councillor\u2019s description, Oct. 6\u20139, 2026)',
              'fr': 'C\u00f4t\u00e9 o\u00f9 la piste serait convertie en stationnement chaque hiver selon la proposition (la piste dans le sens de la circulation\u00a0: c\u00f4t\u00e9 nord \u00e0 l\u2019ouest de Cavendish, c\u00f4t\u00e9 sud \u00e0 l\u2019est; description du conseiller, 6\u20139 oct. 2026)'}
CONV_SHORT = {'en': 'Side where the lane would become parking each winter (the proposal, as the councillor described it)',
              'fr': 'C\u00f4t\u00e9 o\u00f9 la piste deviendrait du stationnement chaque hiver (la proposition, telle que d\u00e9crite par le conseiller)'}
def draw_conversion(ax, u0, u1, lw=3.0):
    a, b = max(u0, 0), min(u1, CAV)
    if b > a: ax.plot([a, b], [LANE_V, LANE_V], color='#e34948', linewidth=lw, linestyle=(0, (4, 2)), solid_capstyle='butt', zorder=6)
    a, b = max(u0, CAV), min(u1, LENGTH)
    if b > a: ax.plot([a, b], [-LANE_V, -LANE_V], color='#e34948', linewidth=lw, linestyle=(0, (4, 2)), solid_capstyle='butt', zorder=6)
def conversion_handle(lang): return Line2D([], [], color='#e34948', linewidth=3, linestyle=(0, (4, 2)), label=CONV_SHORT[lang])
def category_today(r):
    c = category(r)
    if c in (None, 'corner', 'other'): return c
    d = r.get('driveway_today', '')
    if d not in ('yes', 'no'): return 'other'
    g = r['garage_1954'] == 'yes'
    return 'both' if g and d == 'yes' else 'gar_only' if g else 'drive_only' if d == 'yes' else 'neither'
def category(r):
    if 'outside the lane' in r['cross_streets']: return None
    if r['addressed_on'] != 'Terrebonne': return 'corner' if r['garage_1954'] != 'unknown' else 'other'
    t = r['building_type'].lower()
    if 'institutional' in t or 'vacant' in t or r['garage_1954'] in ('unknown', 'n/a', ''): return 'other'
    if r['garage_1954'] == 'no': return 'none'
    acc = r['garage_access_presumed'].lower()
    return 'gar_terr' if acc.startswith('terrebonne') and ' or ' not in acc else 'gar_cross'
rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')) if r['u_m']]
for r in rows: r['cat'] = category(r); r['cat_today'] = category_today(r); r['u'] = float(r['u_m']); r['v'] = float(r['v_m'])
rows = [r for r in rows if r['cat']]
# ---------- base data in the street frame ----------
def poly_uv(coords): return [to_uv(*to_EN(x, y)) for x, y in [(p[0], p[1]) for p in coords]]
UEV = json.load(open(os.path.join(HERE, 'city_assessment_units_terrebonne_bbox.geojson')))['features']
GB = json.load(open(os.path.join(HERE, 'geobase_terrebonne_bbox.geojson')))['features']
LANE = json.load(open(os.path.join(HERE, 'terrebonne_lane_geobase.geojson')))['features']
parcels = []
for f in UEV:
    g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        pts = poly_uv(poly[0])
        if any(-VMAX - 40 < v < VMAX + 40 for u, v in pts): parcels.append(pts)
streets = []
for f in GB:
    c = f['geometry']['coordinates']; lines = c if f['geometry']['type'] == 'MultiLineString' else [c]
    for l in lines: streets.append((poly_uv(l), f['properties'].get('ODONYME') or ''))
# ---------- the 1954 underlay ----------
def render_sheets(u0, u1, ppm=4.0):
    W = int((u1 - u0) * ppm); H = int(2 * VMAX * ppm)
    out = np.full((H, W, 3), 245, np.uint8); score = np.full((H, W), -1e9)
    us = u0 + (np.arange(W) + 0.5) / ppm; vs = VMAX - (np.arange(H) + 0.5) / ppm
    EN = np.array([[from_uv(u, v) for u in us] for v in vs])  # H,W,2
    E, N = EN[..., 0], EN[..., 1]
    for sh, tr in T['sheets'].items():
        side = next(r['side'] for r in csv.DictReader(open(os.path.join(HERE, 'controls.csv'))) if r['sheet'] == sh)
        s, R, t = tr['s'], np.array(tr['R']), np.array(tr['t']); Ri = np.linalg.inv(R)
        X = (Ri[0, 0] * (E - t[0]) + Ri[0, 1] * (N - t[1])) / s; Y = -(Ri[1, 0] * (E - t[0]) + Ri[1, 1] * (N - t[1])) / s
        cache = render_sheets.cache.setdefault(sh, None)
        if cache is None:
            from PIL import Image; Image.MAX_IMAGE_PIXELS = None
            im = Image.open(SCANS % sh).convert('RGB'); im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
            cache = render_sheets.cache[sh] = np.asarray(im)
        h, w = cache.shape[:2]; xi = (X / 2).astype(int); yi = (Y / 2).astype(int)
        inside = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
        sc = np.minimum(np.minimum(xi, w - 1 - xi), np.minimum(yi, h - 1 - yi)).astype(float)
        vgrid = vs[:, None] * np.ones((1, W))
        if side == 'N': sc = np.where(vgrid >= -11, sc, sc - 1e6)
        elif side == 'S': sc = np.where(vgrid <= 11, sc, sc - 1e6)
        take = inside & (sc > score)
        out[take] = cache[yi[take], xi[take]]; score[take] = sc[take]
    return out
render_sheets.cache = {}
# ---------- drawing ----------
def titles(kind, lang):
    title = {('sheets', 'en'): "Buildings fronting rue de Terrebonne: off-street parking as built, on the 1954–55 fire-insurance plans",
             ('modern', 'en'): "Buildings fronting rue de Terrebonne: off-street parking as built (1954–55), on today's parcels",
             ('sheets', 'fr'): "Bâtiments en façade de la rue de Terrebonne : stationnement hors rue d’origine, sur les plans d’assurance-incendie de 1954–1955",
             ('modern', 'fr'): "Bâtiments en façade de la rue de Terrebonne : stationnement hors rue d’origine (1954–1955), sur le cadastre d’aujourd’hui",
             ('today', 'en'): "Buildings fronting rue de Terrebonne: garage as built (1954–55) and driveway or apron today (aerial imagery, 2026)",
             ('today', 'fr'): "Bâtiments en façade de la rue de Terrebonne : garage d’origine (1954–1955) et entrée ou aire pavée aujourd’hui (imagerie aérienne, 2026)"}[(kind, lang)]
    return title
def sources(kind, lang):
    src = {('sheets', 'en'): "Underlay: Underwriters' Survey Bureau, Insurance plan of the city of Montreal, vol. 7, sheets 739, 775, 784, 785, 787, 789, 798 (Nov. 1954–Dec. 1955), georeferenced on the City's geobase and straightened along the street; north side above, south side below; sheet 787-8 (Hampton–Melrose, south) is missing from the series. Markers: the author's reading of each building (buildings_geo.csv), positioned on the City's assessment-roll parcels (CC-BY 4.0). West (Belmore) at left, east (Girouard) at right.",
           ('modern', 'en'): "Base: Ville de Montréal open data, CC-BY 4.0 (géobase street centrelines; unités d'évaluation foncière parcels), drawn in a frame straightened along rue de Terrebonne; north side above, south side below. Markers: the author's reading of the 1954–55 Underwriters' Survey Bureau plans, one per building (buildings_geo.csv). West (Belmore) at left, east (Girouard) at right.",
           ('sheets', 'fr'): "Fond : Underwriters' Survey Bureau, plan d’assurance de la ville de Montréal, vol. 7, feuillets 739, 775, 784, 785, 787, 789, 798 (nov. 1954–déc. 1955), géoréférencés sur la géobase de la Ville et redressés le long de la rue; côté nord en haut, côté sud en bas; le feuillet 787-8 (Hampton–Melrose, sud) manque à la série. Repères : lecture de chaque bâtiment par l’auteur (buildings_geo.csv), placés sur les unités d’évaluation de la Ville (CC-BY 4.0). Ouest (Belmore) à gauche, est (Girouard) à droite.",
           ('modern', 'fr'): "Fond : données ouvertes de la Ville de Montréal, CC-BY 4.0 (géobase; unités d’évaluation foncière), dans un repère redressé le long de la rue de Terrebonne; côté nord en haut, côté sud en bas. Repères : lecture par l’auteur des plans de l’Underwriters' Survey Bureau de 1954–1955, un par bâtiment (buildings_geo.csv). Ouest (Belmore) à gauche, est (Girouard) à droite.",
           ('today', 'en'): "Base: Ville de Montréal open data, CC-BY 4.0 (géobase; assessment-roll parcels), straightened along the street; north side above. Markers: the author's reading of the 1954–55 plans combined with a reading of the Gouvernement du Québec's aerial imagery (service Imagerie_GQ, fetched October 25, 2026): a driveway, paved apron or parking pad on the lot, or none (buildings_geo.csv, columns driveway_today, vehicle_or_pad_on_lot). What a garage is used for inside cannot be seen from above.",
           ('today', 'fr'): "Fond : données ouvertes de la Ville de Montréal, CC-BY 4.0 (géobase; unités d’évaluation), redressé le long de la rue; côté nord en haut. Repères : lecture des plans de 1954–1955 par l’auteur, combinée à une lecture de l’imagerie aérienne du Gouvernement du Québec (service Imagerie_GQ, consulté le 25 octobre 2026) : entrée, aire pavée ou aire de stationnement sur le lot, ou rien (buildings_geo.csv). L’usage intérieur d’un garage ne se voit pas du ciel."}[(kind, lang)]
    return src
def draw_axis(ax, k, kind, lang, cats, catkey, scalebar):
    u0, u1 = k * PANEL, (k + 1) * PANEL
    ax.set_xlim(u0 - 6, u1 + 6); ax.set_ylim(-VMAX, VMAX); ax.set_aspect('equal')
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_color('#cfcac0')
    if kind == 'sheets':
        img = render_sheets(u0 - 6, u1 + 6)
        ax.imshow(img, extent=(u0 - 6, u1 + 6, -VMAX, VMAX), interpolation='bilinear', zorder=0)
    else:
        ax.set_facecolor('#fbfaf7')
        for pts in parcels:
            if any(u0 - 60 < u < u1 + 60 for u, v in pts):
                ax.add_patch(MPoly(pts, closed=True, facecolor='#ebe8df', edgecolor='white', linewidth=0.5, zorder=1))
        for pts, name in streets:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color='#d6d1c6', linewidth=7, solid_capstyle='round', zorder=2)
        for f in LANE:
            c = f['geometry']['coordinates']; lines = c if f['geometry']['type'] == 'MultiLineString' else [c]
            for l in lines:
                pts = poly_uv(l); ax.plot([p[0] for p in pts], [p[1] for p in pts], color='#bdb7aa', linewidth=1.2, zorder=3)
    draw_conversion(ax, u0 - 6, u1 + 6)
    for name, us in STREET_U.items():
        if u0 - 2 < us < u1 + 2:
            short = name.replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '').replace("d'", '')
            ax.text(us, VMAX + 2, short, rotation=90, ha='center', va='bottom', fontsize=6.5, color='#52514e')
    for key, len_, lfr, col, mk in cats:
        pts = [r for r in rows if r[catkey] == key and u0 - 6 <= r['u'] <= u1 + 6]
        if not pts: continue
        ax.scatter([r['u'] for r in pts], [r['v'] for r in pts], s=34 if mk != 'D' else 26, c=col, marker=mk,
                   edgecolors='black', linewidths=0.6, zorder=10)
        if key == 'corner' and kind != 'today':
            g = [r for r in pts if r['garage_1954'] == 'yes']
            ax.scatter([r['u'] for r in g], [r['v'] for r in g], s=90, facecolors='none', marker='s', edgecolors='#2a78d6', linewidths=1.2, zorder=9)
    ax.text(u0 - 4, -VMAX + 3, f"{u0:.0f}\u2013{u1:.0f} m", fontsize=7, color='#52514e', ha='left', va='bottom',
            bbox=dict(facecolor='white', edgecolor='none', alpha=0.8, pad=1.5))
    if scalebar:
        ax.plot([u1 - 110, u1 - 10], [-VMAX + 8, -VMAX + 8], color='black', linewidth=2)
        ax.text(u1 - 60, -VMAX + 11, '100 m', ha='center', fontsize=7)
        ang = math.radians(31); ax.annotate('N', xy=(u1 - 130 + 22 * math.cos(ang), -VMAX + 12 + 22 * math.sin(ang)), xytext=(u1 - 130, -VMAX + 12),
                                             arrowprops=dict(arrowstyle='-|>', color='black', lw=1.2), fontsize=8, ha='center', va='center')
def legend_handles(cats, lang):
    return [Line2D([], [], marker=mk, color='none', markerfacecolor=col, markeredgecolor='black', markersize=7, label=(len_ if lang == 'en' else lfr)) for key, len_, lfr, col, mk in cats] + [conversion_handle(lang)]
def outbase(kind, lang):
    return os.path.join(HERE, f'figures/terrebonne_garages_1954_map_{"underwriters" if kind == "sheets" else "today" if kind == "today" else "city"}_{lang}')
def draw(kind, lang):
    cats = CATS_TODAY if kind == 'today' else CATS; catkey = 'cat_today' if kind == 'today' else 'cat'
    fig_h = 2.05 * NPANEL + 1.6
    fig, axes = plt.subplots(NPANEL, 1, figsize=(12, fig_h))
    for k, ax in enumerate(axes): draw_axis(ax, k, kind, lang, cats, catkey, k == NPANEL - 1)
    fig.suptitle(titles(kind, lang), fontsize=11, y=0.992)
    fig.legend(handles=legend_handles(cats, lang), loc='lower center', ncol=2, fontsize=7.5, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.text(0.5, 0.075, sources(kind, lang), fontsize=6.2, color='#52514e', ha='center', va='bottom', wrap=True)
    fig.subplots_adjust(top=0.945, bottom=0.11, left=0.02, right=0.98, hspace=0.42)
    base = outbase(kind, lang); os.makedirs(os.path.dirname(base), exist_ok=True)
    fig.savefig(base + '.png', dpi=220); fig.savefig(base + '.pdf'); plt.close(fig); print('wrote', base)
def draw_panels(kind, lang):
    """one PDF per panel (for the note's landscape pages) and the legend as its own small PDF"""
    cats = CATS_TODAY if kind == 'today' else CATS; catkey = 'cat_today' if kind == 'today' else 'cat'
    d = os.path.join(HERE, 'figures/panels'); os.makedirs(d, exist_ok=True)
    stem = {"sheets": "underwriters", "today": "today", "modern": "city"}[kind]
    for k in range(NPANEL):
        fig, ax = plt.subplots(1, 1, figsize=(12, 2.35))
        draw_axis(ax, k, kind, lang, cats, catkey, k == NPANEL - 1)
        fig.subplots_adjust(top=0.82, bottom=0.02, left=0.01, right=0.99)
        fig.savefig(os.path.join(d, f'{stem}_{lang}_p{k + 1}.pdf'), bbox_inches='tight', pad_inches=0.03); plt.close(fig)
    fig = plt.figure(figsize=(12, 1.0)); fig.legend(handles=legend_handles(cats, lang), loc='center', ncol=2, fontsize=8, frameon=False)
    fig.savefig(os.path.join(d, f'{stem}_{lang}_legend.pdf'), bbox_inches='tight', pad_inches=0.03); plt.close(fig); print('panels', stem, lang)
if __name__ == '__main__':
    for kind in (['modern', 'today'] + ([] if '--no-sheets' in sys.argv else ['sheets'])):
        draw(kind, LANG); draw_panels(kind, LANG)
