#!/opt/local/bin/python3.13
"""Map of the press record by era: where the deaths of cyclists under 15 on the island of Montréal took place, as far as
the newspapers print it, on a schematic base that holds for every decade.

Base: the island's outline and today's boroughs and towns (City of Montréal, « Limites administratives »), with a few
long-standing streets from the City's street file (géobase). It is TODAY's geometry; the built-up area of each era is
not shown. Points come from places_geocoded.csv (geocode_places.py: old street names matched by hand to today's).
Colour and marker shape = the other party, as on the timeline. The map is turned 34 degrees clockwise so that the
island lies along the page; a north arrow is drawn.

  /opt/local/bin/python3.13 map_by_era.py [folder with events.csv and places_geocoded.csv]  ->  map_by_era_{en,fr}.{png,svg}
"""
import csv, json, math, os, re, sys, collections
import geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely import affinity
from shapely.geometry import Point, box
from shapely.ops import unary_union
H = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, '..', '..')
OD = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata')
SURF = '#fcfcfb'; INK = '#0b0b0b'; INK2 = '#52514e'; LAND = '#f0efea'; EDGE = '#d3d2cc'; ROAD = '#bdbcb6'; WATER = SURF
CL = collections.OrderedDict([
    ('truck', ('#eb6834', 's', 1.0)), ('car', ('#2a78d6', 'o', 1.0)), ('bus', ('#1baf7a', 'D', 0.85)),
    ('horse', ('#eda100', '^', 1.1)), ('tram', ('#e87ba4', 'P', 1.15)), ('fall', ('#008300', 'X', 1.1)),
    ('unknown', (INK2, 'o', 1.0))])
def klass(c):
    return ('truck' if c.startswith('truck') else 'car' if (c in ('car', 'taxi') or c.startswith('car and')) else 'bus' if c.startswith('bus') else
            'horse' if c.startswith('horse') else 'tram' if c in ('tram', 'train') else 'fall' if c.startswith('none') else 'unknown')
ERAS = [(1900, 1939), (1940, 1949), (1950, 1959), (1960, 1969), (1970, 2029)]
ROADS = [('Sherbrooke', 'rue', 'Sherbrooke'), ('Notre-Dame', 'rue', 'Notre-Dame'), ('Saint-Laurent', 'boulevard', 'Saint-Laurent'),
         ('Saint-Denis', 'rue', None), ('Papineau', 'avenue', 'Papineau'), ('Pie-IX', 'boulevard', 'Pie-IX'),
         ('Côte-des-Neiges', 'chemin', 'Côte-des-Neiges'), ('Gouin', 'boulevard', 'Gouin'), ('Wellington', 'rue', None),
         ('Saint-Jacques', 'rue', None), ('Mont-Royal', 'avenue', None), ('Jean-Talon', 'rue', 'Jean-Talon'), ('Ontario', 'rue', None)]
T = {
 'en': dict(title='Where the newspapers place the deaths of cyclists under 15, island of Montréal, by era',
    sub='{n} of the {N} deaths in the press record have a place that can be put on a map; one mark each. Colour and shape: the other party, as on the timeline.',
    era=['1912 to 1939', '1940 to 1949', '1950 to 1959', '1960 to 1969', '1970 to 2008'], cnt='{k} located of {m}',
    leg=dict(truck='Truck or other heavy motor vehicle', car='Car or taxi', bus='Bus or trolleybus', horse='Horse-drawn vehicle',
             tram='Tram', fall='A fall, no other vehicle', unknown='Vehicle not stated, or the reports differ'),
    prec=['Crossing of two streets, a civic number, or within about a block', 'Only the street is known: the mark sits at the middle of it'],
    notes='The base is today\'s geometry: the island\'s outline, today\'s boroughs and towns,\nand a few long-standing streets, named on the first panel. The built-up\narea of each era is not shown. Old street names were matched by hand\nto today\'s (table in this folder).\n\nA press record, not a count of all deaths. Counts, not risk.\n\nThe west of the island, where no located death falls, is outside the frame.',
    north='N'),
 'fr': dict(title='Où les journaux situent les décès de cyclistes de moins de 15 ans, île de Montréal, par époque',
    sub='{n} des {N} décès du relevé de presse ont un lieu qui peut être porté sur une carte; une marque chacun. Couleur et forme : l\'autre véhicule, comme sur la chronologie.',
    era=['1912 à 1939', '1940 à 1949', '1950 à 1959', '1960 à 1969', '1970 à 2008'], cnt='{k} situés sur {m}',
    leg=dict(truck='Camion ou autre véhicule lourd à moteur', car='Automobile ou taxi', bus='Autobus ou trolleybus', horse='Véhicule à traction animale',
             tram='Tramway', fall='Une chute, sans autre véhicule', unknown='Véhicule non précisé, ou versions divergentes'),
    prec=['Croisement de deux rues, numéro civique, ou à un pâté de maisons près', 'Seule la rue est connue : la marque est placée en son milieu'],
    notes='Le fond est la géométrie d\'aujourd\'hui : le contour de l\'île, les arrondissements\net villes actuels et quelques rues anciennes, nommées sur le premier\npanneau. Le territoire bâti de chaque époque n\'est pas montré. Les anciens\nnoms de rues ont été appariés à la main aux noms actuels (table du dossier).\n\nUn relevé de presse, non un décompte de tous les décès. Des nombres, non un risque.\n\nL\'ouest de l\'île, où aucun décès situé ne tombe, est hors du cadre.',
    north='N'),
}
FRAC = {'Sherbrooke': 0.9, 'Notre-Dame': 0.1, 'Saint-Laurent': 0.85, 'Papineau': 0.9, 'Pie-IX': 0.75, 'Côte-des-Neiges': 0.5, 'Gouin': 0.5, 'Jean-Talon': 0.15}
ROT = 34.0; ORIGIN = (300000, 5040000)
def rot(g): return affinity.rotate(g, ROT, origin=ORIGIN)   # positive = counter-clockwise in shapely, so the map turns... see below
# The island's long axis runs south-west to north-east; turning the MAP clockwise by 34 degrees means rotating the
# geometry by -34 degrees (shapely's positive angle is counter-clockwise).
def rot(g): return affinity.rotate(g, -ROT, origin=ORIGIN)

lim = gpd.read_file(os.path.join(OD, 'limadmin', 'limadmin.json')).to_crs(32188)
land = [rot(g) for g in lim.geometry]
gb = gpd.read_file(os.path.join(OD, 'geobase_2026-10-14.json')).to_crs(32188)
roads = []
for name, typ, label in ROADS:
    sel = gb[(gb['NOM_VOIE'] == name) & (gb['TYP_VOIE'] == typ)]
    if len(sel): roads.append((rot(unary_union(list(sel.geometry))), label))
ev = list(csv.DictReader(open(os.path.join(D, 'events.csv'), encoding='utf-8')))
u = [e for e in ev if e['age_group'] in ('under 10', '10 to 14') and e['on_island_inferred'] == 'yes' and not e['listed_apart']]
seen = collections.Counter(); cls = {}
for e in u:
    d = e['event_date'][:10]; seen[d] += 1; cls[(d, str(seen[d]))] = klass(e['other_party_class'])
import pyproj
TO_M = pyproj.Transformer.from_crs(4326, 32188, always_xy=True).transform
P = []
pl = list(csv.DictReader(open(os.path.join(D, 'places_geocoded.csv'), encoding='utf-8')))
assert len(pl) == len(u), 'places_geocoded.csv is not in step with events.csv: run geocode_places.py'
for r in pl:
    if not r['lon']: continue
    g = rot(Point(*TO_M(float(r['lon']), float(r['lat']))))
    P.append((int(r['event_date'][:4]), g.x, g.y, cls[(r['event_date'], r['row_of_that_date'])], r['precision'], r['placement']))
xs = [p[1] for p in P]; ys = [p[2] for p in P]
mx, my = 2600, 2600
x0, x1, y0, y1 = min(xs) - mx, max(xs) + mx, min(ys) - my, max(ys) + my
# keep the panels' aspect: 3 columns on a 13 in page
W, Hh = x1 - x0, y1 - y0
frame = box(x0, y0, x1, y1)
plt.rcParams.update({'font.family': 'Helvetica Neue', 'font.size': 10, 'svg.fonttype': 'none'})
def jitter(pts):
    """Marks that fall on the same spot are set side by side (two deaths in one collision)."""
    out = []; at = collections.Counter()
    for p in pts:
        k = (round(p[1], -1), round(p[2], -1)); out.append((p, at[k])); at[k] += 1
    return out
for lang, t in T.items():
    pw = 4.15; ph = pw * Hh / W
    fig = plt.figure(figsize=(13, 1.25 + 2 * ph + 0.75), facecolor=SURF)
    FH = fig.get_figheight()
    axes = []
    for i in range(6):
        r, c = divmod(i, 3)
        ax = fig.add_axes([0.02 + c * (pw + 0.13) / 13, 1 - (1.25 + (r + 1) * ph + r * 0.42) / FH, pw / 13, ph / FH]); axes.append(ax)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_facecolor(WATER)
        for s in ax.spines.values(): s.set_color(EDGE)
    for i, (a, b) in enumerate(ERAS):
        ax = axes[i]; ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal')
        gpd.GeoSeries(land).plot(ax=ax, facecolor=LAND, edgecolor=EDGE, linewidth=0.5, zorder=1)
        for g, label in roads:
            gpd.GeoSeries([g]).plot(ax=ax, color=ROAD, linewidth=0.55, zorder=2)
            gg = g.intersection(frame.buffer(-900))
            if label and i == 0 and not gg.is_empty:
                big = gg if gg.geom_type == 'LineString' else max(getattr(gg, 'geoms', [gg]), key=lambda q: q.length)
                pt = big.interpolate(FRAC.get(label, 0.5), normalized=True)
                ax.text(pt.x, pt.y, label, fontsize=5.6, color=INK2, ha='center', va='center', zorder=2.5,
                        bbox=dict(boxstyle='round,pad=0.12', fc=LAND, ec='none', alpha=0.85))
        pts = [p for p in P if a <= p[0] <= b]; m = sum(1 for e in u if a <= int(e['event_date'][:4]) <= b)
        for p, k in jitter(pts):
            col, mk, f = CL[p[3]]; x = p[1] + k * 520
            if p[4] == 'street': ax.scatter([x], [p[2]], s=230, marker='o', facecolor='none', edgecolor=col, linewidth=0.9, linestyle=(0, (2, 1.5)), zorder=3)
            ax.scatter([x], [p[2]], s=42 * f, marker=mk, facecolor=col if p[5] == 'as printed' else SURF, edgecolor=col, linewidth=1.4, zorder=4)
        ax.set_title(t['era'][i], loc='left', fontsize=11.5, fontweight='bold', color=INK, pad=5)
        ax.set_title(t['cnt'].format(k=len(pts), m=m), loc='right', fontsize=9, color=INK2, pad=5)
    # north arrow on the first panel: north is up-left by 34 degrees after the clockwise turn
    ax = axes[0]; ang = math.radians(90 - ROT); L = 1500; nx, ny = x0 + 2200, y1 - 3600
    ax.annotate('', (nx + L * math.cos(ang), ny + L * math.sin(ang)), (nx, ny), arrowprops=dict(arrowstyle='-|>', color=INK2, lw=1), zorder=5)
    ax.text(nx + (L + 500) * math.cos(ang), ny + (L + 500) * math.sin(ang), t['north'], fontsize=8, color=INK2, ha='center', va='center')
    ax.plot([x1 - 7400, x1 - 2400], [y0 + 1100, y0 + 1100], color=INK2, lw=1.2, zorder=5); ax.text(x1 - 4900, y0 + 1500, '5 km', fontsize=7.5, color=INK2, ha='center')
    lx = axes[5]; lx.axis('off'); lx.set_xlim(0, 1); lx.set_ylim(0, 1)
    used = [c for c in CL if any(p[3] == c for p in P)]
    hs = [Line2D([], [], ls='', marker=CL[c][1], markersize=7.5 * CL[c][2] ** .5, markerfacecolor=CL[c][0], markeredgecolor=CL[c][0],
                 label=t['leg'][c]) for c in used]
    hs += [Line2D([], [], ls='', marker='o', markersize=7, markerfacecolor=INK2, markeredgecolor=INK2, label=t['prec'][0]),
           Line2D([], [], ls='', marker='o', markersize=13, markerfacecolor='none', markeredgecolor=INK2, markeredgewidth=0.9, label=t['prec'][1])]
    lx.legend(handles=hs, loc='upper left', bbox_to_anchor=(0.0, 1.0), frameon=False, fontsize=8.4, labelcolor=INK, handletextpad=0.4, labelspacing=0.55, borderaxespad=0)
    lx.text(0.0, 0.0, t['notes'], fontsize=8.2, color=INK2, va='bottom', ha='left', linespacing=1.35)
    fig.text(0.02, 1 - 0.42 / FH, t['title'], fontsize=15, fontweight='bold', fontfamily='Helvetica', color=INK, ha='left', va='center')
    fig.text(0.02, 1 - 0.78 / FH, t['sub'].format(n=len(P), N=len(u)), fontsize=10, color=INK2, ha='left', va='center')
    for ext in ('png', 'svg'): fig.savefig(os.path.join(H, f'map_by_era_{lang}.{ext}'), dpi=200, facecolor=SURF)
    plt.close(fig)
print(len(P), 'located of', len(u), '; frame', round(W), 'x', round(Hh), 'm')
