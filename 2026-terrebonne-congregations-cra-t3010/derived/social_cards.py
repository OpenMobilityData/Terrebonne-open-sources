#!/usr/bin/env python3
"""Two social cards (1600x900 PNG) from summary.json and the St Monica folder's 2025 manual entries. Usage: python3 social_cards.py"""
import json, os, csv
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures'); SM = os.path.join(HERE, '..', '..', '2024-st-monica-cra-t3010', 'derived')
S = json.load(open(os.path.join(HERE, 'summary.json'))); P = S['congregations']['130341852RR0001']; T = S['congregations']['843768433RR0002']; REF = S['fabriques_reference']
man = {int(r['fiscal_year']): {} for r in csv.DictReader(open(os.path.join(SM, 'manual_entries.csv'), encoding='utf-8'))}
for r in csv.DictReader(open(os.path.join(SM, 'manual_entries.csv'), encoding='utf-8')):
    if r['value']: man[int(r['fiscal_year'])][r['line']] = float(r['value'])
m25 = man.get(2025, {}); rev25 = m25.get('4700'); gifts25 = (m25.get('4500') or 0) + (m25.get('4530') or 0)
INK, INK2, SURF, GRID = '#0b0b0b', '#52514e', '#fcfcfb', '#e6e5e1'
plt.rcParams.update({'font.family': 'sans-serif', 'axes.edgecolor': INK2, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'axes.axisbelow': True, 'figure.facecolor': SURF, 'axes.facecolor': SURF, 'legend.frameon': False})
# card 1: St Monica 2015–2025
fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
ys = P['years']; rev = [P['series'][str(y)]['revenue'] / 1000 for y in ys]; gf = [P['series'][str(y)]['gifts'] / 1000 for y in ys]
ax.axvspan(2023.5, 2025.6, color='#f0efec', zorder=0); ax.text(2024.55, 395, 'with the bike lane\n(built May–June 2024)', ha='center', va='top', fontsize=15, color=INK2)
ax.plot(ys, rev, 'o-', color='#2a78d6', lw=3, ms=9, label='total revenue (line 4700)'); ax.plot(ys, gf, 's--', color='#86b6ef', lw=2.5, ms=8, label='gifts (lines 4500 + 4530)')
if rev25: ax.plot([2024, 2025], [rev[-1], rev25 / 1000], 'o-', color='#2a78d6', lw=3, ms=9, mfc='white'); ax.plot([2024, 2025], [gf[-1], gifts25 / 1000], 's--', color='#86b6ef', lw=2.5, ms=8, mfc='white'); ax.text(2025, rev25 / 1000 + 12, f'${rev25/1000:.0f}k\nhighest since 2016', ha='center', fontsize=14, color=INK)
for y, v in zip(ys, rev):
    if y in (2015, 2019, 2021, 2024): ax.text(y, v + 12, f'${v:.0f}k', ha='center', fontsize=13, color=INK)
ax.set_xticks(list(range(2015, 2026))); ax.tick_params(labelsize=14); ax.set_ylim(0, 410); ax.set_ylabel('thousand dollars, fiscal year ending Dec 31', fontsize=15); ax.legend(fontsize=15, loc='lower left')
ax.set_title("St Monica's parish (6405 rue de Terrebonne): what its charity returns show, 2015–2025", loc='left', fontsize=22, color=INK, pad=14)
fig.text(0.01, 0.01, 'Source: Canada Revenue Agency, T3010 returns (open data 2015–2024; the 2025 return as displayed by the CRA Charities Listings, read Nov 5, 2026: hollow markers).\nAnalysis and data: github.com/OpenMobilityData/Terrebonne-open-sources (folders 2024-st-monica-cra-t3010 and 2026-terrebonne-congregations-cra-t3010).', fontsize=11, color=INK2)
fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(os.path.join(FIG, 'social_card_1_st_monica_2015_2025.png')); plt.close(fig)
# card 2: both frontage congregations, first lane year against their own record
fig, ax = plt.subplots(figsize=(16, 9), dpi=100)
items = [("St Monica, revenue\n2024 vs 2019–2023 mean", P['revenue_2024_vs_base_pct'], '#2a78d6'), ("St Monica, gifts\n2024 vs 2019–2023 mean", P['gifts_2024_vs_base_pct'], '#86b6ef'),
         ("Yuen Kwok Buddhist Temple, revenue\n2024 vs 2022–2023", T['revenue_2024_vs_base_pct'], '#eb6834'), ("Yuen Kwok Buddhist Temple, expenditures\n2024 vs 2022–2023", T['expenditures_2024_vs_base_pct'], '#f0a07a')]
yy = range(len(items))
ax.barh(list(yy), [i[1] for i in items], color=[i[2] for i in items], height=0.55)
for i, (lab, v, c) in enumerate(items): ax.text(v + (1.0 if v >= 0 else -1.0), i, f'{v:+.0f} %', va='center', ha='left' if v >= 0 else 'right', fontsize=18, color=INK, bbox=dict(boxstyle='round,pad=0.15', fc=SURF, ec='none'))
ax.set_yticks(list(yy)); ax.set_yticklabels([i[0] for i in items], fontsize=15); ax.axvline(0, color=INK2, lw=1)
ref = REF.get('revenue_2024_vs_2022_2023_mean', {}).get('median_pct')
if ref is not None: ax.axvline(ref, color=INK2, lw=1.5, ls='--'); ax.text(ref + 0.6, -0.62, f'median of 12 other Catholic parishes of the area,\nrevenue 2024 vs 2022–23: {ref:+.0f} %', fontsize=12, color=INK2, va='top')
ax.set_xlim(-15, 32); ax.set_ylim(3.6, -1.1); ax.tick_params(axis='x', labelsize=14); ax.set_xlabel('change in the first year with the lane (2024), per cent', fontsize=15)
ax.set_title('The two places of worship with a frontage on rue de Terrebonne:\nthe first year with the lane (2024) against each one\u2019s own record', loc='left', fontsize=21, color=INK, pad=14)
fig.text(0.01, 0.01, "Source: CRA T3010 open data 2015–2024. The temple's returns begin in 2022 and its 2022 and 2023 figures are identical to the dollar. A third registered charity files from a\nresidential unit at 6350 (returns under $12k a year, nil in 2024). Analysis and data: github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/2026-terrebonne-congregations-cra-t3010", fontsize=10.5, color=INK2)
fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(os.path.join(FIG, 'social_card_2_first_lane_year.png')); plt.close(fig)
print('cards written')
