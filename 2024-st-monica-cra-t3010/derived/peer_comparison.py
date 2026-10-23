#!/usr/bin/env python3
"""Compare the subject parish with the other Catholic parishes (fabriques) of the
same postal areas on the same T3010 lines, 2015–2024.

Inputs:  peer_parishes.csv (the subject and the peers, from the CRA's 2024
         identification file), ../raw/open-canada-peers/<year>/financial_*.csv
         (extracts written by fetch_peer_parishes.py).
Outputs: peer_comparison_long.csv     one row per parish and year: the key lines
         peer_comparison_index.csv    gifts (4500 + 4530) and total revenue (4700)
                                      indexed to each parish's 2017–2019 mean = 100
         peer_comparison_changes.csv  each parish's change 2023 -> 2024 and 2024
                                      against its 2022–2023 mean, with ranks
         figures/peers_gifts_index_{en,fr}, figures/peers_revenue_index_{en,fr},
         figures/peers_change_2024_{en,fr}  (SVG, PNG, PDF)
Gifts are the two gift lines added (4500 receipted + 4530 not receipted) because
the share receipted differs from parish to parish. Run: python3 peer_comparison.py
"""
import csv, glob, os, statistics, datetime, zoneinfo
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '..', 'raw', 'open-canada-peers')
FIG = os.path.join(HERE, 'figures')
SUBJECT = '130341852RR0001'
BASE = (2017, 2018, 2019)
SHORT = {'130341852RR0001': 'Sainte-Monique', '107362766RR0001': 'Notre-Dame-des-Neiges', '107369068RR0001': 'Saint-Kevin',
         '107362980RR0001': 'Saint-Antonin', '119232296RR0001': 'Saint-Malachie', '130365521RR0001': 'Saint-Léon',
         '131324782RR0001': 'Ascension of Our Lord', '107362659RR0001': 'Notre-Dame-de-Grâce', '118910025RR0001': 'Saint Augustine of Canterbury',
         '131158727RR0001': 'Saint-Raymond', '119232247RR0001': 'Saint-Ignace-de-Loyola', '107359119RR0001': 'Sainte-Catherine-de-Sienne',
         '118994094RR0001': 'Saint-Richard'}
LINES = [4500, 4530, 4610, 4650, 4700, 5100, 4880, 4200, 4350]

def money(s):
    s = (s or '').replace('$', '').replace(',', '').strip()
    try:
        return float(s)
    except ValueError:
        return None

peers = list(csv.DictReader(open(os.path.join(HERE, 'peer_parishes.csv'), encoding='utf-8')))
bns = [p['bn'] for p in peers]
data = {}
for f in sorted(glob.glob(os.path.join(RAW, '[0-9]' * 4, 'financial*.csv'))):
    y = int(os.path.basename(os.path.dirname(f)))
    rows = list(csv.reader(open(f, encoding='utf-8-sig')))
    for r in rows[1:]:
        d = dict(zip(rows[0], r))
        data[(r[0], y)] = {ln: money(d.get(str(ln))) for ln in LINES}
years = sorted({y for _, y in data})

def v(bn, y, ln):
    x = data.get((bn, y), {}).get(ln)
    return x if x is not None else 0.0

with open(os.path.join(HERE, 'peer_comparison_long.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['bn', 'parish', 'role', 'fiscal_year'] + [f'line_{ln}' for ln in LINES] + ['gifts_4500_plus_4530', 'revenue_less_expenditures'])
    for bn in bns:
        for y in years:
            w.writerow([bn, SHORT[bn], 'subject' if bn == SUBJECT else 'peer', y] + [f'{v(bn,y,ln):.0f}' if data.get((bn, y), {}).get(ln) is not None else '' for ln in LINES]
                       + [f'{v(bn,y,4500)+v(bn,y,4530):.0f}', f'{v(bn,y,4700)-v(bn,y,5100):.0f}'])

METRICS = {'gifts': lambda bn, y: v(bn, y, 4500) + v(bn, y, 4530), 'revenue': lambda bn, y: v(bn, y, 4700)}
index = {}
for m, fn in METRICS.items():
    for bn in bns:
        base = statistics.mean(fn(bn, y) for y in BASE)
        for y in years:
            index[(m, bn, y)] = 100.0 * fn(bn, y) / base if base else None
with open(os.path.join(HERE, 'peer_comparison_index.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['metric', 'bn', 'parish', 'role'] + [str(y) for y in years])
    for m in METRICS:
        for bn in bns:
            w.writerow([m, bn, SHORT[bn], 'subject' if bn == SUBJECT else 'peer'] + [f'{index[(m,bn,y)]:.1f}' for y in years])
        med = [statistics.median(index[(m, bn, y)] for bn in bns if bn != SUBJECT) for y in years]
        w.writerow([m, '', 'median of the twelve peers', 'summary'] + [f'{x:.1f}' for x in med])

# Changes 2023 -> 2024 and 2024 vs the 2022–2023 mean.
changes = []
for bn in bns:
    row = dict(bn=bn, parish=SHORT[bn], role='subject' if bn == SUBJECT else 'peer')
    for m, fn in METRICS.items():
        a, b = fn(bn, 2023), fn(bn, 2024)
        row[f'{m}_2023'] = f'{a:.0f}'; row[f'{m}_2024'] = f'{b:.0f}'
        row[f'{m}_change_2023_2024_pct'] = f'{100*(b/a-1):.1f}' if a else ''
        mean2223 = (fn(bn, 2022) + fn(bn, 2023)) / 2
        row[f'{m}_2024_vs_2022_2023_mean_pct'] = f'{100*(b/mean2223-1):.1f}' if mean2223 else ''
    changes.append(row)
for m in METRICS:
    for key in (f'{m}_change_2023_2024_pct', f'{m}_2024_vs_2022_2023_mean_pct'):
        order = sorted([r for r in changes if r[key] != ''], key=lambda r: -float(r[key]))
        for i, r in enumerate(order, 1):
            r[key.replace('_pct', '_rank_of_' + str(len(order)))] = i
fields = list(changes[0].keys())
for r in changes:
    for k in r:
        if k not in fields: fields.append(k)
with open(os.path.join(HERE, 'peer_comparison_changes.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(changes)

# Printed summary for the note.
def med(m, y): return statistics.median(index[(m, bn, y)] for bn in bns if bn != SUBJECT)
def q(m, y, p): 
    xs = sorted(index[(m, bn, y)] for bn in bns if bn != SUBJECT); n = len(xs)
    return xs[int(round(p * (n - 1)))]
for m in METRICS:
    print(f'\n{m}: index (2017-2019 mean = 100)')
    print('  year  subject  peers median  q25  q75  min  max')
    for y in years:
        xs = sorted(index[(m, bn, y)] for bn in bns if bn != SUBJECT)
        print(f'  {y}  {index[(m,SUBJECT,y)]:6.1f}  {med(m,y):6.1f}  {q(m,y,0.25):6.1f} {q(m,y,0.75):6.1f} {xs[0]:6.1f} {xs[-1]:6.1f}')
    s = next(r for r in changes if r['bn'] == SUBJECT)
    pc = [float(r[f'{m}_change_2023_2024_pct']) for r in changes if r['role'] == 'peer' and r[f'{m}_change_2023_2024_pct'] != '']
    print(f"  2023->2024: subject {s[f'{m}_change_2023_2024_pct']} % (rank {s[f'{m}_change_2023_2024_rank_of_13']} of 13); peers median {statistics.median(pc):.1f} %, range {min(pc):.1f} to {max(pc):.1f}; peers up: {sum(1 for x in pc if x>0)}, down: {sum(1 for x in pc if x<0)}")
    pc = [float(r[f'{m}_2024_vs_2022_2023_mean_pct']) for r in changes if r['role'] == 'peer' and r[f'{m}_2024_vs_2022_2023_mean_pct'] != '']
    print(f"  2024 vs 2022-23 mean: subject {s[f'{m}_2024_vs_2022_2023_mean_pct']} % (rank {s[f'{m}_2024_vs_2022_2023_mean_rank_of_13']} of 13); peers median {statistics.median(pc):.1f} %, range {min(pc):.1f} to {max(pc):.1f}")

# Charts.
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
except ImportError:
    plt = None
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
INK, INK2, GRID, PEER = '#0b0b0b', '#52514e', '#e4e3df', '#b9b7b1'
T = {'en': dict(gifts='Gifts (lines 4500 + 4530), indexed', revenue='Total revenue (line 4700), indexed',
                sub='Each parish indexed to its own 2017–2019 mean = 100; the twelve other Catholic parishes of the area in grey, their median dashed, the middle half shaded',
                subj='Sainte-Monique (Terrebonne)', medl='Median of the twelve peers', band='Middle half of the peers', fy='Fiscal year (ending December 31)', idx='Index (2017–2019 mean = 100)',
                chg='Change from 2023 to 2024, by parish', chgsub='Percent change of gifts (lines 4500 + 4530) and of total revenue (line 4700); the subject parish in colour',
                g='Gifts', r='Total revenue', pct='Change 2023 → 2024 (%)',
                src='Source: Canada Revenue Agency, T3010 returns of the thirteen parishes (open.canada.ca, « List of charities » 2015–2024, datasets modified 2026-10-04 or earlier); build '),
     'fr': dict(gifts='Dons (lignes 4500 + 4530), en indice', revenue='Total des revenus (ligne 4700), en indice',
                sub='Chaque paroisse en indice de sa propre moyenne 2017–2019 = 100; les douze autres paroisses catholiques du secteur en gris, leur médiane en tirets, la moitié centrale en ombré',
                subj='Sainte-Monique (Terrebonne)', medl='Médiane des douze paroisses', band='Moitié centrale des paroisses', fy='Exercice (clos le 31 décembre)', idx='Indice (moyenne 2017–2019 = 100)',
                chg='Variation de 2023 à 2024, par paroisse', chgsub='Variation en pourcentage des dons (lignes 4500 + 4530) et du total des revenus (ligne 4700); la paroisse étudiée en couleur',
                g='Dons', r='Total des revenus', pct='Variation 2023 → 2024 (%)',
                src='Source : Agence du revenu du Canada, déclarations T3010 des treize paroisses (open.canada.ca, « List of charities » 2015–2024, jeux de données modifiés le 2026-10-04 ou avant); généré le ')}

def style(ax, lang, title, sub):
    ax.set_title(title, loc='left', fontsize=13, color=INK, pad=24, fontweight='bold')
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=8, color=INK2, wrap=True)
    ax.spines[['top', 'right', 'left']].set_visible(False); ax.spines['bottom'].set_color(GRID)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8); ax.set_axisbelow(True); ax.tick_params(colors=INK2, labelsize=9, length=0)

def finish(fig, lang, name):
    fig.text(0.01, 0.01, T[lang]['src'] + datetime.datetime.now(zoneinfo.ZoneInfo('America/Toronto')).strftime('%Y-%m-%d'), fontsize=7, color=INK2, wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    for ext in ('svg', 'png', 'pdf'):
        fig.savefig(os.path.join(FIG, f'{name}_{lang}.{ext}'), dpi=160)
    plt.close(fig)

if plt:
    os.makedirs(FIG, exist_ok=True)
    for lang in ('en', 'fr'):
        t = T[lang]
        for m in METRICS:
            fig, ax = plt.subplots(figsize=(9, 5))
            style(ax, lang, t[m], t['sub'])
            lo = [q(m, y, 0.25) for y in years]; hi = [q(m, y, 0.75) for y in years]
            ax.fill_between(years, lo, hi, color=GRID, alpha=0.8, label=t['band'], linewidth=0)
            for bn in bns:
                if bn != SUBJECT:
                    ax.plot(years, [index[(m, bn, y)] for y in years], color=PEER, linewidth=0.9)
            ax.plot(years, [med(m, y) for y in years], color=INK2, linestyle='--', linewidth=1.4, label=t['medl'])
            ax.plot(years, [index[(m, SUBJECT, y)] for y in years], color=PAL[1], linewidth=2.6, marker='o', markersize=4, label=t['subj'])
            ax.axhline(100, color=INK2, linewidth=0.6)
            ax.set_ylim(0, 300); ax.set_xticks(years); ax.set_ylabel(t['idx'], color=INK2, fontsize=9); ax.set_xlabel(t['fy'], color=INK2, fontsize=9)
            ax.legend(frameon=False, fontsize=8, loc='upper left', labelcolor=INK)
            finish(fig, lang, f'peers_{m}_index')
        # change chart
        fig, ax = plt.subplots(figsize=(9, 5.6))
        style(ax, lang, t['chg'], t['chgsub'])
        order = sorted(changes, key=lambda r: float(r['gifts_change_2023_2024_pct'] or 0))
        ys = range(len(order)); h = 0.38
        for i, r in enumerate(order):
            g = float(r['gifts_change_2023_2024_pct'] or 0); rv = float(r['revenue_change_2023_2024_pct'] or 0)
            subj = r['bn'] == SUBJECT
            ax.barh(i + h / 2, g, height=h, color=PAL[1] if subj else PEER, edgecolor='white')
            ax.barh(i - h / 2, rv, height=h, color=PAL[0] if subj else '#d6d4cf', edgecolor='white')
        ax.set_yticks(list(ys)); ax.set_yticklabels([r['parish'] for r in order], fontsize=8, color=INK)
        ax.axvline(0, color=INK2, linewidth=0.8); ax.xaxis.grid(True, color=GRID, linewidth=0.8); ax.yaxis.grid(False)
        ax.set_xlabel(t['pct'], color=INK2, fontsize=9)
        from matplotlib.patches import Patch
        ax.legend(handles=[Patch(color=PAL[1], label=t['g'] + ' (' + t['subj'] + ')'), Patch(color=PAL[0], label=t['r'] + ' (' + t['subj'] + ')'), Patch(color=PEER, label=t['g']), Patch(color='#d6d4cf', label=t['r'])], frameon=False, fontsize=8, loc='lower right', labelcolor=INK)
        finish(fig, lang, 'peers_change_2024')
    print('\ncharts written')
