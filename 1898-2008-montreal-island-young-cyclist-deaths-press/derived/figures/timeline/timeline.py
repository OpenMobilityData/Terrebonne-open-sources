#!/usr/bin/env python3
"""Timeline of the press record: one mark per death of a cyclist under 15 on the island of Montréal, by year, with the
number of newspaper issues the searches returned per decade beneath it (what there was to read).

Reads events.csv and screening_log.csv two folders up (or the folder given as first argument); every number on the
figure is counted at build time. Colours: the validated light-surface slots of the reference palette used in
Montreal-collisions (dataviz skill), fixed per class, never cycled; marker shape repeats the class.

  python3 timeline.py [folder with events.csv and screening_log.csv]  ->  timeline_{en,fr}.{png,svg}
"""
import csv, os, re, sys, collections
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
H = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(H, '..', '..')
SURF = '#fcfcfb'; INK = '#0b0b0b'; INK2 = '#52514e'; GRID = '#e6e5e1'; BAR = '#b9b8b3'
# class -> (colour, marker, size factor)
CL = collections.OrderedDict([
    ('truck', ('#eb6834', 's', 1.0)), ('car', ('#2a78d6', 'o', 1.0)), ('bus', ('#1baf7a', 'D', 0.85)),
    ('horse', ('#eda100', '^', 1.1)), ('tram', ('#e87ba4', 'P', 1.15)), ('fall', ('#008300', 'X', 1.1)),
    ('unknown', (INK2, 'o', 1.0))])
def klass(c):
    return ('truck' if c.startswith('truck') else 'car' if (c in ('car', 'taxi') or c.startswith('car and')) else 'bus' if c.startswith('bus') else
            'horse' if c.startswith('horse') else 'tram' if c in ('tram', 'train') else 'fall' if c.startswith('none') else 'unknown')
T = {
 'en': dict(
    title='Cyclists under 15 killed on the island of Montréal, as reported in digitized newspapers',
    sub='One mark per death, by year of the event. {n} deaths: {p} with the place printed or the streets named (filled), {i} placed on the island by inference (hollow).',
    warn='A press record, not a count of all deaths.\nCounts, not risk: how many children cycled, and how much, was not measured.',
    leg=dict(truck='Truck or other heavy motor vehicle', car='Car or taxi', bus='Bus or trolleybus', horse='Horse-drawn vehicle',
             tram='Tram', fall='A fall, no other vehicle', unknown='Vehicle not stated, or the reports differ'),
    cov='Newspaper issues returned by the {q} searches, by decade of the issue: what there was to read',
    covnote='The collection thins after the 1960s, and Le Journal de Montréal (1964 on) is absent or can be read only on BAnQ\'s premises:\nfewer marks after 1970 reflect, at least in part, fewer papers to search.',
    latest='the latest found:\nAugust 26, 2008', first='the earliest:\nApril 10, 1912', yl='deaths\nin the year', yl2='issues',
    src='Source: newspapers digitized by BAnQ numérique, {q} fixed searches, every candidate read on the page (protocol and table of events in this folder). Other vehicle as the page describes it;\nhorse-drawn only where the page says so. Not shown: deaths listed apart ({apart}), cyclists aged 15 to 17, deaths with the collision off the island.'),
 'fr': dict(
    title='Cyclistes de moins de 15 ans tués sur l\'île de Montréal, selon les journaux numérisés',
    sub='Une marque par décès, selon l\'année de l\'événement. {n} décès : {p} dont le lieu est imprimé ou les rues nommées (pleines), {i} situés sur l\'île par inférence (vides).',
    warn='Un relevé de presse, non un décompte de tous les décès.\nDes nombres, non un risque : on n\'a pas mesuré combien d\'enfants roulaient à vélo, ni combien.',
    leg=dict(truck='Camion ou autre véhicule lourd à moteur', car='Automobile ou taxi', bus='Autobus ou trolleybus', horse='Véhicule à traction animale',
             tram='Tramway', fall='Une chute, sans autre véhicule', unknown='Véhicule non précisé, ou versions divergentes'),
    cov='Numéros de journaux retournés par les {q} recherches, par décennie du numéro : ce qu\'il y avait à lire',
    covnote='La collection s\'amenuise après les années 1960, et Le Journal de Montréal (depuis 1964) est absent ou consultable seulement dans les édifices de BAnQ :\nles marques moins nombreuses après 1970 tiennent, au moins en partie, à ce qu\'il y a moins de journaux à fouiller.',
    latest='le plus récent trouvé :\n26 août 2008', first='le plus ancien :\n10 avril 1912', yl='décès\ndans l\'année', yl2='numéros',
    src='Source : journaux numérisés par BAnQ numérique, {q} recherches fixées d\'avance, chaque candidat lu sur la page (protocole et table des événements dans ce dossier). Autre véhicule tel que la page le décrit;\ntraction animale seulement lorsque la page le dit. Non montrés : les décès listés à part ({apart}), les cyclistes de 15 à 17 ans, les décès dont la collision a eu lieu hors de l\'île.'),
}
APART = {'en': {'tricycle': 'a child of 4 on a tricycle', 'drowning': 'a drowning'}, 'fr': {'tricycle': 'un enfant de 4 ans sur un tricycle', 'drowning': 'une noyade'}}

ev = list(csv.DictReader(open(os.path.join(D, 'events.csv'), encoding='utf-8')))
u = [e for e in ev if e['age_group'] in ('under 10', '10 to 14') and e['on_island_inferred'] == 'yes' and not e['listed_apart']]
apart = [e['listed_apart'] for e in ev if e['listed_apart']]
sl = list(csv.DictReader(open(os.path.join(D, 'screening_log.csv'), encoding='utf-8')))
nq = len({re.sub(r'b$', '', r['query']) for r in sl})
iss = {r['banq_id']: r['date'][:4] for r in sl if r['date'][:4].isdigit()}
cov = collections.Counter(int(y) // 10 * 10 for y in iss.values())
u.sort(key=lambda e: e['event_date'][:10])
stack = collections.Counter(); pts = []
for e in u:
    y = int(e['event_date'][:4]); stack[y] += 1
    pts.append((y, stack[y], klass(e['other_party_class']), e['on_island'] == 'yes'))
n, p = len(pts), sum(1 for x in pts if x[3]); X0, X1 = 1905, 2030
plt.rcParams.update({'font.family': 'Helvetica Neue', 'font.size': 10, 'svg.fonttype': 'none'})
for lang, t in T.items():
    fig, (a, b) = plt.subplots(2, 1, figsize=(13, 7.4), gridspec_kw=dict(height_ratios=[3.1, 1], hspace=0.42), facecolor=SURF)
    for ax in (a, b):
        ax.set_facecolor(SURF); ax.set_xlim(X0, X1)
        for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
        ax.spines['bottom'].set_color(INK2); ax.tick_params(colors=INK2, length=3); ax.set_xticks(range(1910, 2030, 10))
    a.set_ylim(0.3, max(stack.values()) + 1.0); a.set_yticks(range(1, max(stack.values()) + 1)); a.grid(axis='y', color=GRID, lw=0.8); a.set_axisbelow(True)
    a.set_ylabel(t['yl'], color=INK2, rotation=0, ha='right', va='center', labelpad=8)
    for y, k, c, printed in pts:
        col, mk, f = CL[c]
        a.scatter([y + 0.5], [k], s=46 * f, marker=mk, facecolor=col if printed else SURF, edgecolor=col, linewidth=1.5, zorder=3)
    y0, y1 = pts[0][0], pts[-1][0]
    a.annotate(t['first'], (y0 + 0.5, 1), (y0 + 0.5, 2.2), fontsize=8.5, color=INK2, ha='center', arrowprops=dict(arrowstyle='-', color=INK2, lw=0.7))
    a.annotate(t['latest'], (y1 + 0.5, 1), (y1 + 0.5, 2.2), fontsize=8.5, color=INK2, ha='center', arrowprops=dict(arrowstyle='-', color=INK2, lw=0.7))
    a.text(X1 - 0.5, max(stack.values()) + 0.9, t['warn'], ha='right', va='top', fontsize=10.5, color=INK, fontweight='bold', linespacing=1.35)
    used = [c for c in CL if any(x[2] == c for x in pts)]
    hs = [Line2D([], [], ls='', marker=CL[c][1], markersize=7.5 * CL[c][2] ** .5, markerfacecolor=CL[c][0], markeredgecolor=CL[c][0],
                 label=f"{t['leg'][c]} ({sum(1 for x in pts if x[2] == c)})") for c in used]
    lg = a.legend(handles=hs, loc='lower left', bbox_to_anchor=(-0.005, 1.03), frameon=False, fontsize=9.2, labelcolor=INK, handletextpad=0.2, columnspacing=1.6, borderaxespad=0, ncol=4)
    xs = sorted(cov); b.bar([x + 5 for x in xs if X0 <= x < X1], [cov[x] for x in xs if X0 <= x < X1], width=9.2, color=BAR, zorder=2)
    for x in xs:
        if X0 <= x < X1: b.text(x + 5, cov[x] + 8, str(cov[x]), ha='center', va='bottom', fontsize=8.5, color=INK2)
    b.set_ylim(0, max(cov.values()) * 1.3); b.set_yticks([]); b.set_title(t['cov'].format(q=nq), loc='left', fontsize=10, color=INK, pad=6)
    b.text(X0, -0.42, t['covnote'], transform=b.get_xaxis_transform(), fontsize=9, color=INK2, va='top', linespacing=1.35)
    fig.suptitle(t['title'], x=0.045, y=0.975, ha='left', fontsize=15, fontweight='bold', color=INK)
    fig.text(0.045, 0.915, t['sub'].format(n=n, p=p, i=n - p), fontsize=10.5, color=INK2, ha='left')
    ap = ', '.join(APART[lang].get(k, k) for k in apart) or '0'
    fig.text(0.045, 0.012, t['src'].format(q=nq, apart=ap), fontsize=7.8, color=INK2, ha='left', va='bottom', linespacing=1.3)
    fig.subplots_adjust(left=0.085, right=0.975, top=0.805, bottom=0.2)
    for ext in ('png', 'svg'): fig.savefig(os.path.join(H, f'timeline_{lang}.{ext}'), dpi=200, facecolor=SURF)
    plt.close(fig)
print(n, 'deaths;', p, 'as printed;', nq, 'queries;', dict(sorted(cov.items())))
