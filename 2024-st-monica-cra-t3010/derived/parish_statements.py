#!/usr/bin/env python3
"""The parish's own financial statements, as published in its weekly bulletins
(parish website, bulletin archive), set beside the T3010 returns.

Input:   parish_statements_monthly.csv  one row per month or year-end for which a
         bulletin carried a statement (2017–2023), read by eye from the bulletins:
         Sunday and online collections of the month, year-to-date revenue and
         expenses, the balance as printed and as computed, the bulletin's date and
         file name, a note on every oddity. No bulletin is reproduced (they name
         individuals); only these figures are.
Outputs: figures/parish_monthly_collections_{en,fr}  monthly collections 2017–2023
         figures/parish_ytd_{en,fr}                    year-to-date revenue and expenses by year
         statements_vs_returns_{en,fr}.tex             the year-ends beside lines 4700 / 5100
Run: python3 parish_statements.py (also run by build.py).
"""
import csv, os, datetime, zoneinfo
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, 'figures')
rows = [r for r in csv.DictReader(open(os.path.join(HERE, 'parish_statements_monthly.csv'), encoding='utf-8'))]
summary = {int(r['fiscal_year']): r for r in csv.DictReader(open(os.path.join(HERE, 't3010_summary.csv'), encoding='utf-8'))}

def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None

months = [r for r in rows if r['month'] and f(r['sunday_collections']) is not None]
yearends = [r for r in rows if r['month'] == '12' and f(r['ytd_revenue']) is not None]

# Cross-check table: year-end statements vs the return.
T = {'en': dict(h=['Fiscal year', 'Statement: revenue', 'Statement: expenses', 'Return 4700', 'Return 5100', 'Difference, revenue', 'Difference, expenses', 'Statement published'],
                mc='Monthly collections, as published in the bulletins', mcsub='Sunday (plate and envelopes) and online collections of each month with a published statement, 2017–2023; months without a statement are blank',
                sun='Sunday collections', onl='Online collections', k='$ thousand', mo='Month',
                ytd='Year-to-date revenue and expenses, by year', ytdsub='From the monthly statements; each year drawn from January; the year-end statements of 2018, 2019, 2020 and 2022 close each line',
                rev='Revenue', exp='Expenses',
                src='Source: the parish\'s weekly bulletins (parish website), financial statements of 2017–2023 as read from the bulletins listed in parish_statements_monthly.csv; build '),
     'fr': dict(h=['Exercice', 'État : revenus', 'État : dépenses', 'Déclaration 4700', 'Déclaration 5100', 'Écart, revenus', 'Écart, dépenses', 'État publié le'],
                mc='Quêtes mensuelles, telles que publiées dans les bulletins', mcsub='Quêtes du dimanche (panier et enveloppes) et en ligne de chaque mois ayant un état publié, 2017–2023; les mois sans état sont vides',
                sun='Quêtes du dimanche', onl='Quêtes en ligne', k='k$', mo='Mois',
                ytd='Revenus et dépenses cumulés depuis janvier, par année', ytdsub='D\'après les états mensuels; chaque année tracée depuis janvier; les états de fin d\'année 2018, 2019, 2020 et 2022 ferment chaque courbe',
                rev='Revenus', exp='Dépenses',
                src='Source : les bulletins hebdomadaires de la paroisse (site web de la paroisse), états financiers 2017–2023 lus dans les bulletins listés dans parish_statements_monthly.csv; généré le ')}

def money_tex(v, lang):
    v = round(v)
    s = f'{abs(v):,.0f}'.replace(',', '\\,')
    return ('$-$' if v < 0 else '') + s

for lang in ('en', 'fr'):
    t = T[lang]
    with open(os.path.join(HERE, f'statements_vs_returns_{lang}.tex'), 'w', encoding='utf-8') as out:
        out.write('\\begin{tabular}{@{}lrrrrrrl@{}}\\toprule\n' + ' & '.join(t['h']) + ' \\\\\\midrule\n')
        for r in yearends:
            y = int(r['year']); sr, se = f(r['ytd_revenue']), f(r['ytd_expenses'])
            rr, re_ = f(summary[y]['total_revenue']), f(summary[y]['total_expenditures'])
            out.write(f"{y} & {money_tex(sr, lang)} & {money_tex(se, lang)} & {money_tex(rr, lang)} & {money_tex(re_, lang)} & {money_tex(sr - rr, lang)} & {money_tex(se - re_, lang)} & {r['bulletin_date']} \\\\\n")
        out.write('\\bottomrule\\end{tabular}\n')

try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
except ImportError:
    plt = None
PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'

def style(ax, lang, title, sub):
    ax.set_title(title, loc='left', fontsize=13, color=INK, pad=24, fontweight='bold')
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=8, color=INK2)
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
    years = list(range(2017, 2024))
    for lang in ('en', 'fr'):
        t = T[lang]
        # 1. Monthly collections on one time axis.
        fig, ax = plt.subplots(figsize=(10, 4.6))
        style(ax, lang, t['mc'], t['mcsub'])
        xs = [(int(r['year']) - 2017) * 12 + int(r['month']) - 1 for r in months]
        sun = [f(r['sunday_collections']) / 1000 for r in months]; onl = [f(r['online_collections']) / 1000 if f(r['online_collections']) is not None else 0 for r in months]
        ax.bar(xs, sun, width=0.8, color=PAL[0], label=t['sun'], edgecolor='white', linewidth=0.6)
        ax.bar(xs, onl, width=0.8, bottom=sun, color=PAL[3], label=t['onl'], edgecolor='white', linewidth=0.6)
        ax.set_xticks([(y - 2017) * 12 for y in years]); ax.set_xticklabels([str(y) for y in years])
        ax.set_xlim(-1, 7 * 12); ax.set_ylabel(t['k'], color=INK2, fontsize=9)
        ax.legend(frameon=False, fontsize=8, loc='upper right', labelcolor=INK)
        finish(fig, lang, 'parish_monthly_collections')
        # 2. YTD revenue and expenses by year.
        fig, ax = plt.subplots(figsize=(9, 5))
        style(ax, lang, t['ytd'], t['ytdsub'])
        for i, y in enumerate(years):
            pts = sorted([(int(r['month']), f(r['ytd_revenue']), f(r['ytd_expenses'])) for r in rows if r['year'] == str(y) and r['month'] and f(r['ytd_revenue']) is not None and (int(r['year']) != 2023)], key=lambda p: p[0])
            if not pts: continue
            c = PAL[i % len(PAL)]
            ax.plot([0] + [p[0] for p in pts], [0] + [p[1] / 1000 for p in pts], color=c, linewidth=1.8, marker='o', markersize=3, label=f'{y} {t["rev"]}')
            ax.plot([0] + [p[0] for p in pts], [0] + [p[2] / 1000 for p in pts], color=c, linewidth=1.2, linestyle='--', marker='o', markersize=3, markerfacecolor='white', label=f'{y} {t["exp"]}')
        ax.set_xticks(range(0, 13)); ax.set_xlabel(t['mo'], color=INK2, fontsize=9); ax.set_ylabel(t['k'], color=INK2, fontsize=9)
        ax.legend(frameon=False, fontsize=7, loc='upper left', ncol=2, labelcolor=INK)
        finish(fig, lang, 'parish_ytd')
    print('parish statements: charts and tables written')
