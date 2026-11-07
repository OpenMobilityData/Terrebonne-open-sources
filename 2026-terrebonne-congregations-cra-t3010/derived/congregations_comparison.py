#!/usr/bin/env python3
"""The congregations on rue de Terrebonne on the same T3010 lines, 2015–2024: long table, index to each one's pre-lane base, 2024 against the
pre-lane years; figures; summary.json. Inputs: congregations.csv, ../raw/open-canada/<year>/financial_*.csv (fetch_congregations.py), and the
St Monica folder's peer_comparison_changes.csv for the fabriques' reference. Run: ~/.venvs/omd/bin/python congregations_comparison.py"""
import csv, glob, os, json, statistics, datetime
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, '..', 'raw', 'open-canada'); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
SM = os.path.join(HERE, '..', '..', '2024-st-monica-cra-t3010', 'derived')
LINES = [4500, 4530, 4610, 4650, 4700, 5100, 4880, 4200, 4350]
LAB = {4500: 'tax-receipted gifts', 4530: 'other gifts (no receipt)', 4610: 'rental income', 4650: 'other revenue', 4700: 'total revenue', 5100: 'total expenditures', 4880: 'total charitable-program expenditures', 4200: 'total assets', 4350: 'total liabilities'}
C = {'130341852RR0001': '#2a78d6', '843768433RR0002': '#eb6834', '837788975RR0001': '#1baf7a', 'ink': '#0b0b0b', 'ink2': '#52514e', 'grid': '#e6e5e1', 'surf': '#fcfcfb'}
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 9, 'axes.edgecolor': C['ink2'], 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6, 'axes.axisbelow': True, 'figure.facecolor': C['surf'], 'axes.facecolor': C['surf'], 'savefig.dpi': 200, 'legend.frameon': False})
def money(s):
    s = (s or '').strip().replace(',', '').replace('$', '')
    if s in ('', '-'): return None
    try: return float(s)
    except ValueError: return None
cong = {r['bn']: r for r in csv.DictReader(open(os.path.join(HERE, 'congregations.csv'), encoding='utf-8'))}
data = {}; fpe = {}
for f in sorted(glob.glob(os.path.join(RAW, '[0-9]' * 4, 'financial*.csv'))):
    y = int(os.path.basename(os.path.dirname(f))); rows = list(csv.reader(open(f, encoding='utf-8-sig')))
    for r in rows[1:]:
        d = dict(zip(rows[0], r)); data[(r[0], y)] = {ln: money(d.get(str(ln))) for ln in LINES}; fpe[(r[0], y)] = d.get('FPE', '')
# the temple's earlier BN never appears: merge nothing, drop it from the shown set
SHOW = ['130341852RR0001', '843768433RR0002', '837788975RR0001']
years = sorted({y for _, y in data})
def v(bn, y, ln):
    x = data.get((bn, y), {}).get(ln); return x if x is not None else 0.0
with open(os.path.join(HERE, 'congregations_long.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['bn', 'congregation', 'class', 'year', 'fiscal_period_end'] + [f'line_{ln}' for ln in LINES] + ['gifts_4500_plus_4530', 'revenue_less_expenditures'])
    for bn in SHOW:
        for y in years:
            if (bn, y) not in data: continue
            w.writerow([bn, cong[bn]['short'], cong[bn]['class'], y, fpe[(bn, y)]] + [f'{v(bn, y, ln):.0f}' if data[(bn, y)].get(ln) is not None else '' for ln in LINES] + [f'{v(bn, y, 4500) + v(bn, y, 4530):.0f}', f'{v(bn, y, 4700) - v(bn, y, 5100):.0f}'])
# pre-lane base: the lane was built May–June 2024, so fiscal years ending in 2024 are the first with the lane (Sept 30, 2024 for the Deliverance church: four months)
BASE = {'130341852RR0001': [2019, 2020, 2021, 2022, 2023], '843768433RR0002': [2022, 2023], '837788975RR0001': [2019, 2020, 2021, 2022, 2023]}
S = {'years': years, 'congregations': {}}
for bn in SHOW:
    ys = [y for y in years if (bn, y) in data]; base = [y for y in BASE[bn] if (bn, y) in data]
    rec = dict(short=cong[bn]['short'], cls=cong[bn]['class'], years=ys, base_years=base, fpe_2024=fpe.get((bn, 2024), ''), series={str(y): dict(revenue=v(bn, y, 4700), gifts=v(bn, y, 4500) + v(bn, y, 4530), receipted=v(bn, y, 4500), rental=v(bn, y, 4610), expenditures=v(bn, y, 5100), surplus=v(bn, y, 4700) - v(bn, y, 5100), assets=v(bn, y, 4200)) for y in ys})
    for m in ('revenue', 'gifts', 'expenditures'):
        b = [rec['series'][str(y)][m] for y in base]; bm = statistics.mean(b) if b else None
        rec[m + '_base_mean'] = bm; rec[m + '_2024'] = rec['series']['2024'][m] if '2024' in rec['series'] else None
        rec[m + '_2024_vs_base_pct'] = round(100 * (rec[m + '_2024'] / bm - 1), 1) if bm and rec[m + '_2024'] is not None else None
        rec[m + '_base_min'] = min(b) if b else None; rec[m + '_base_max'] = max(b) if b else None
        rec[m + '_2024_within_base_range'] = (rec[m + '_base_min'] <= rec[m + '_2024'] <= rec[m + '_base_max']) if b and rec[m + '_2024'] is not None else None
        rec[m + '_2023'] = rec['series']['2023'][m] if '2023' in rec['series'] else None
        rec[m + '_2024_vs_2023_pct'] = round(100 * (rec[m + '_2024'] / rec[m + '_2023'] - 1), 1) if rec[m + '_2023'] else None
    S['congregations'][bn] = rec
# the fabriques' reference (St Monica folder): median change 2023 -> 2024 in gifts and revenue among the 12 peers
ref = {}
try:
    ch = list(csv.DictReader(open(os.path.join(SM, 'peer_comparison_changes.csv'), encoding='utf-8')))
    S['peer_changes_header'] = list(ch[0].keys()) if ch else []
    for m in ('gifts', 'revenue'):
        for k, lab in ((f'{m}_change_2023_2024_pct', 'change_2023_2024'), (f'{m}_2024_vs_2022_2023_mean_pct', '2024_vs_2022_2023_mean')):
            vals = [float(r[k]) for r in ch if r.get('role') == 'peer' and r.get(k) not in ('', None)]
            if vals: ref[f'{m}_{lab}'] = dict(median_pct=round(statistics.median(vals), 1), n=len(vals), min=round(min(vals), 1), max=round(max(vals), 1))
        sm = [r for r in ch if r.get('role') == 'subject']
        if sm: ref[f'{m}_subject_change_2023_2024_pct'] = sm[0].get(f'{m}_change_2023_2024_pct'); ref[f'{m}_subject_rank_of_13'] = sm[0].get(f'{m}_change_2023_2024_rank_of_13')
except FileNotFoundError: pass
S['fabriques_reference'] = ref
# figures: one panel per congregation, revenue, gifts and expenditures by fiscal year; the first lane year shaded
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.6))
for ax, bn in zip(axes, SHOW):
    rec = S['congregations'][bn]; ys = rec['years']
    ax.plot(ys, [rec['series'][str(y)]['revenue'] / 1000 for y in ys], 'o-', color=C[bn], lw=1.6, ms=4, label='total revenue (4700)')
    ax.plot(ys, [rec['series'][str(y)]['gifts'] / 1000 for y in ys], 's--', color=C[bn], lw=1.2, ms=3.5, alpha=0.75, label='gifts (4500 + 4530)')
    ax.plot(ys, [rec['series'][str(y)]['expenditures'] / 1000 for y in ys], '^:', color=C['ink2'], lw=1.0, ms=3.5, label='total expenditures (5100)')
    ax.axvspan(2023.5, 2024.5, color='#f0efec', zorder=0); ax.text(2024, ax.get_ylim()[1] * 0.98 if ax.get_ylim()[1] > 0 else 1, 'first\nlane year', ha='center', va='top', fontsize=6.5, color=C['ink2'])
    ax.set_title(f"{rec['short']}\n{cong[bn]['address']}", loc='left', fontsize=8.5); ax.set_xticks(ys[::2] if len(ys) > 6 else ys); ax.tick_params(axis='x', labelsize=7); ax.set_ylim(bottom=0)
axes[0].set_ylabel('thousand dollars, fiscal year'); axes[0].legend(fontsize=6.5, loc='lower left')
fig.text(0.01, 0.005, 'Source: CRA, T3010 returns as published in the « List of charities » open-data files 2015–2024 (open.canada.ca), lines as labelled; fiscal years end Dec 31 (St Monica, temple) and Sept 30 (Deliverance church). The lane was built May–June 2024.', fontsize=6, color=C['ink2'])
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'terrebonne_congregations_series_en.png')); plt.close(fig)
S['generated'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
json.dump(S, open(os.path.join(HERE, 'summary.json'), 'w'), indent=1, default=str)
for bn in SHOW:
    r = S['congregations'][bn]; print(r['short'], r['years'], 'FPE 2024', r['fpe_2024'])
    for m in ('revenue', 'gifts', 'expenditures'): print('  ', m, {y: round(r['series'][str(y)][m]) for y in r['years']}, 'base mean', round(r[m + '_base_mean'] or 0), '2024 vs base %', r[m + '_2024_vs_base_pct'], 'within range', r[m + '_2024_within_base_range'], '2024 vs 2023 %', r[m + '_2024_vs_2023_pct'])
print('ref', ref, S.get('peer_changes_header'))
