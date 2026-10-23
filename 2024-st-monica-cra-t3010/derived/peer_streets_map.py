#!/usr/bin/env python3
"""Map of the street conditions around the thirteen parish churches (twelve buildings): an overview of the
area with the City's bike network and the churches, then one panel per church (400 m square) with the
street centrelines, the lanes of today's network (protected all year / painted, shared or designated), the
church's outline and the parking lots mapped in OpenStreetMap; each panel's subtitle gives the row of
peer_streets.csv (lane on the frontage, new since the 2024 survey, off-street lot seen on imagery).
Inputs: as peer_streets.py (City of Montréal open data, CC BY 4.0; OpenStreetMap extracts, ODbL), the
City's administrative limits (limadmin.json), and peer_streets.csv.
Outputs: figures/peer_streets_map_{en,fr}.{svg,png,pdf}. Run after peer_streets.py.
"""
import csv, datetime, json, os, zoneinfo
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Polygon
import peer_streets as ps

HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures')
LIMADMIN = os.path.join(ps.MTL, 'limadmin', 'limadmin.json')
PROT, PAINT = '#2a78d6', '#eb6834'
INK, INK2, GRID, STREET, LOT = '#0b0b0b', '#52514e', '#e4e3df', '#c9c7c1', '#d6d4cf'
HALF = 200  # half-width of a panel, metres
T = {'en': dict(title='Bike lanes and off-street parking at the thirteen parish churches',
                sub='Lanes of the City of Montréal\'s network today, by kind; church outline in black; parking lots mapped in OpenStreetMap shaded.\nNotre-Dame-de-Grâce and Saint Augustine of Canterbury filed the same address (one church, panel 8). Each panel is 400 m square.',
                prot='Lane protected all year', paint='Painted, shared or designated lane', church='Church', lot='Parking lot (OpenStreetMap)', other='Other parish churches',
                lane={'protected': 'protected lane on the frontage', 'painted or shared': 'painted lane on the frontage', 'none': 'no lane on the frontage'},
                new=' (new since the 2024 survey)', lot_={'yes': 'off-street lot', 'no': 'no off-street lot', 'not checked': 'lot not checked'},
                overview='The area (dashed: municipal and borough limits); numbers as in the panels', scale='100 m',
                src='Sources: Ville de Montréal open data (géobase, Réseau cyclable as of 2026-10-14, Auscultation du réseau cyclable 2020 and 2024, Signalisation – Stationnement as of 2026-10-23, limites administratives; CC BY 4.0); © OpenStreetMap contributors (ODbL); off-street lots seen on Google Maps satellite imagery 2026-10-23; drawn '),
     'fr': dict(title='Voies cyclables et stationnement hors rue aux treize églises paroissiales',
                sub='Voies du réseau cyclable de la Ville de Montréal aujourd\'hui, par type; contour de l\'église en noir; stationnements cartographiés dans OpenStreetMap en ombré.\nNotre-Dame-de-Grâce et Saint Augustine of Canterbury déclarent la même adresse (une seule église, vignette 8). Chaque vignette fait 400 m de côté.',
                prot='Voie protégée quatre saisons', paint='Bande, voie partagée ou chaussée désignée', church='Église', lot='Stationnement (OpenStreetMap)', other='Autres églises de la comparaison',
                lane={'protected': 'voie protégée en façade', 'painted or shared': 'bande en façade', 'none': 'aucune voie en façade'},
                new=' (nouvelle depuis le relevé 2024)', lot_={'yes': 'stationnement hors rue', 'no': 'aucun stationnement hors rue', 'not checked': 'stationnement non vérifié'},
                overview='Le secteur (tirets : limites des villes et arrondissements); numéros des vignettes', scale='100 m',
                src='Sources : données ouvertes de la Ville de Montréal (géobase, Réseau cyclable au 2026-10-14, Auscultation du réseau cyclable 2020 et 2024, Signalisation – Stationnement au 2026-10-23, limites administratives; CC BY 4.0); © les contributeurs d\'OpenStreetMap (ODbL); stationnements hors rue vus sur l\'imagerie satellite de Google Maps le 2026-10-23; généré le ')}


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, 'peer_streets.csv'), encoding='utf-8')))
    rows = [r for r in rows if r['bn'] != '118910025RR0001' and r['role'] != 'reference']  # same church as Notre-Dame-de-Grâce; the reference church is in the tables only
    G = [[ps.xy(*c) for c in f['geometry']['coordinates']] for f in json.load(open(ps.FILES['geobase'][0], encoding='utf-8'))['features']]
    NET = []
    for f in json.load(open(ps.FILES['network'][0], encoding='utf-8'))['features']:
        g = f['geometry']; Ls = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
        for L in Ls:
            NET.append((f['properties']['PROTEGE_4S'] == 'Oui', [ps.xy(*c[:2]) for c in L]))
    LIM = []
    for f in json.load(open(LIMADMIN, encoding='utf-8'))['features']:
        if f['properties']['NOM'] in ('Côte-des-Neiges-Notre-Dame-de-Grâce', 'Westmount', 'Côte-Saint-Luc', 'Hampstead', 'Montréal-Ouest', 'Mont-Royal', 'Outremont'):
            g = f['geometry']; polys = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
            LIM.append((f['properties']['NOM'], [[ps.xy(*c[:2]) for c in ring] for poly in polys for ring in poly[:1]]))
    sites = []
    for r in rows:
        nodes, ways, shape = ps.osm_extract(r['bn'], None)
        C = shape(ps.CHURCH[r['bn']]); cc = ps.centroid(C)
        lots = [shape(w) for w, (nds, t) in ways.items() if t.get('amenity') == 'parking' and len(nds) > 2 and ps.lines_dist(C, shape(w)) <= 60]
        sites.append((r, C, cc, lots))

    os.makedirs(FIG, exist_ok=True)
    for lang in ('en', 'fr'):
        t = T[lang]
        fig = plt.figure(figsize=(11, 15.5))
        gs = fig.add_gridspec(5, 3, height_ratios=[1.35, 1, 1, 1, 1], hspace=0.42, wspace=0.08)
        fig.subplots_adjust(left=0.06, right=0.97, top=0.9, bottom=0.05)
        # overview: x range widened to the panel's shape so the map fills it
        ax = fig.add_subplot(gs[0, :])
        xs = [s[2][0] for s in sites]; ys = [s[2][1] for s in sites]
        y0, y1 = min(ys) - 500, max(ys) + 500
        pos = ax.get_position(); ratio = pos.width * fig.get_figwidth() / (pos.height * fig.get_figheight())
        xc, w = (min(xs) + max(xs)) / 2, (y1 - y0) * ratio
        x0, x1 = xc - w / 2, xc + w / 2
        for name, rings in LIM:
            for ring in rings:
                ax.add_patch(Polygon(ring, closed=True, fill=False, edgecolor=INK2, linewidth=0.8, linestyle=(0, (4, 2))))
        for prot, L in NET:
            if any(x0 < p[0] < x1 and y0 < p[1] < y1 for p in L):
                ax.plot(*zip(*L), color=PROT if prot else PAINT, linewidth=1.4 if prot else 0.9, solid_capstyle='round', zorder=2)
        for k, (r, C, cc, lots) in enumerate(sites, 1):
            subj = r['role'] == 'subject'
            ax.plot(*cc, marker='o', markersize=11 if subj else 8, color=INK, markeredgecolor='white', markeredgewidth=2, zorder=4)
            ax.annotate(f"{k}", cc, xytext=(6, 4), textcoords='offset points', fontsize=7.5 if not subj else 8.5,
                        fontweight='bold' if subj else 'normal', color=INK, zorder=5,
                        bbox=dict(boxstyle='round,pad=0.15', fc='white', ec='none', alpha=0.8))
        ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values(): s.set_color(GRID)
        ax.set_title(t['overview'], loc='left', fontsize=9, color=INK2)
        # panels
        for k, (r, C, cc, lots) in enumerate(sites):
            ax = fig.add_subplot(gs[1 + k // 3, k % 3])
            bx0, bx1, by0, by1 = cc[0] - HALF, cc[0] + HALF, cc[1] - HALF, cc[1] + HALF
            inbox = lambda L: any(bx0 - 50 < p[0] < bx1 + 50 and by0 - 50 < p[1] < by1 + 50 for p in L)
            for L in G:
                if inbox(L):
                    ax.plot(*zip(*L), color=STREET, linewidth=0.8, zorder=1)
            for P in lots:
                ax.add_patch(Polygon(P, closed=True, facecolor=LOT, edgecolor='white', linewidth=1, zorder=2))
            for prot, L in NET:
                if inbox(L):
                    ax.plot(*zip(*L), color=PROT if prot else PAINT, linewidth=2.4, solid_capstyle='round', zorder=3)
            ax.add_patch(Polygon(C, closed=True, facecolor=INK, edgecolor='white', linewidth=1, zorder=4))
            for r2, C2, cc2, _ in sites:
                if r2 is not r and bx0 < cc2[0] < bx1 and by0 < cc2[1] < by1:
                    ax.add_patch(Polygon(C2, closed=True, facecolor=INK2, edgecolor='white', linewidth=1, zorder=4))
            ax.set_xlim(bx0, bx1); ax.set_ylim(by0, by1); ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
            for s in ax.spines.values(): s.set_color(GRID)
            subj = r['role'] == 'subject'
            name = r['parish'] + (' (+ St Augustine)' if r['bn'] == '107362659RR0001' else '')
            ax.set_title(f"{k + 1}  {name}", loc='left', fontsize=8.5, color=INK, fontweight='bold', pad=22)
            line = t['lane'][r['frontage_lane']] + (t['new'] if r['frontage_lane_new_since_2024_survey'] == 'yes' else '') + '\n' + t['lot_'][r['off_street_lot']]
            ax.text(0, 1.015, line, transform=ax.transAxes, fontsize=6.6, color=INK2)
            if subj:
                for s in ax.spines.values(): s.set_color(INK); s.set_linewidth(1.2)
            ax.plot([bx0 + 15, bx0 + 115], [by0 + 15, by0 + 15], color=INK2, linewidth=1.5, solid_capstyle='butt', zorder=5)
            ax.text(bx0 + 65, by0 + 22, t['scale'], fontsize=6, color=INK2, ha='center', zorder=5)
        fig.suptitle(t['title'], x=0.06, y=0.99, ha='left', fontsize=14, fontweight='bold', color=INK)
        fig.text(0.06, 0.968, t['sub'], fontsize=8.5, color=INK2, va='top', linespacing=1.4)
        fig.legend(handles=[Line2D([], [], color=PROT, linewidth=2.4, label=t['prot']), Line2D([], [], color=PAINT, linewidth=2.4, label=t['paint']),
                            Patch(facecolor=INK, label=t['church']), Patch(facecolor=INK2, label=t['other']), Patch(facecolor=LOT, label=t['lot'])],
                   loc='upper left', bbox_to_anchor=(0.055, 0.948), ncol=3, frameon=False, fontsize=8, labelcolor=INK)
        fig.text(0.06, 0.012, __import__('textwrap').fill(t['src'] + datetime.datetime.now(zoneinfo.ZoneInfo('America/Toronto')).strftime('%Y-%m-%d'), 190), fontsize=6.5, color=INK2)
        for ext in ('svg', 'png', 'pdf'):
            fig.savefig(os.path.join(FIG, f'peer_streets_map_{lang}.{ext}'), dpi=160)
        plt.close(fig)
    print('figures/peer_streets_map_{en,fr}.{svg,png,pdf}')


if __name__ == '__main__':
    main()
