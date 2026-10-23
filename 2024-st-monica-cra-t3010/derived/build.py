#!/usr/bin/env python3
"""Build the tidy tables and the charts for the St Monica T3010 folder.

Inputs (all under ../raw/):
  cra-charities-listings-2024-12-06/<year>/   the CSV files e-mailed by the CRA's
      Charities Directorate on Dec 6, 2024 (fiscal years 2008–2018; financial
      section, general information, programs, schedules);
  open-canada/<year>/                          row extracts of the yearly "List of
      charities" files on open.canada.ca (written by fetch_open_data.py; fiscal
      years 2019 and later) with SOURCES.tsv giving the file, URL, hash and date;
  ../derived/manual_entries.csv                values typed by hand from the CRA's
      Charities Listings quick view (fallback only; each with its date).

Outputs (in ../derived/):
  t3010_lines.csv       long table: fiscal_year, line, value, form_id, source, as_of
  t3010_summary.csv     wide table of the checked lines by year
  figures/*.svg|png|pdf the charts, EN and FR (incl. the peer comparison, by peer_comparison.py)
  summary_table_{en,fr}.tex  the table of the notes
  st_monica_t3010_note_{en,fr}.pdf  the notes, version-stamped and compiled
  build_report.txt      what was read, what was skipped, consistency checks

Run:  python3 build.py   (from any directory; needs matplotlib)
"""
import csv, glob, io, os, re, sys, datetime, zoneinfo

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, '..', 'raw')
EMAIL = os.path.join(RAW, 'cra-charities-listings-2024-12-06')
OPEN = os.path.join(RAW, 'open-canada')
FIG = os.path.join(HERE, 'figures')
BN = '130341852RR0001'

# "As of" dates given in the CRA's reply of Dec 6, 2024 for the e-mailed data.
EMAIL_AS_OF = {2008: '2017-09-07', 2009: '2018-06-30', 2010: '2019-04-30', 2011: '2019-04-30',
               2012: '2019-04-30', 2013: '2024-04-30', 2014: '2024-04-30', 2015: '2024-04-30',
               2016: '2024-04-30', 2017: '2024-10-31', 2018: '2024-10-31'}

report = []
def log(s):
    report.append(s)

def read_csv(path):
    raw = open(path, 'rb').read()
    for enc in ('utf-8-sig', 'cp1252', 'latin-1'):
        try:
            return list(csv.reader(io.StringIO(raw.decode(enc))))
        except UnicodeDecodeError:
            continue

def money(v):
    """'$44230.00' / '44230' / '' -> float or None (text lines return None)."""
    if v is None:
        return None
    s = v.strip().replace('$', '').replace(',', '')
    if s == '':
        return None
    try:
        return float(s)
    except ValueError:
        return None

def fpe_year(s):
    m = re.match(r'(\d{4})-\d{2}-\d{2}', s.strip())
    return int(m.group(1)) if m else None

rows = []   # dicts: fiscal_year, line, value, text, form_id, source, as_of, file

def harvest(path, source, as_of, year_hint=None):
    """Take every numbered column (4-digit line) of a one-charity CSV."""
    table = read_csv(path)
    if not table or len(table) < 2:
        log(f'  skipped (empty): {os.path.relpath(path, RAW)}')
        return 0
    hdr = [h.strip() for h in table[0]]
    n = 0
    for rec in table[1:]:
        if not any(rec):
            continue
        d = dict(zip(hdr, rec))
        bn = d.get('BN') or d.get('BN/Registration Number') or ''
        if bn and bn != BN:
            continue
        fpe = d.get('FPE') or d.get('Fiscal Period End') or d.get('Fiscal period end') or ''
        year = fpe_year(fpe) or year_hint
        form_id = d.get('Form ID', '')
        for h, v in zip(hdr, rec):
            if re.fullmatch(r'\d{4}', h) and v.strip() != '':
                val = money(v)
                rows.append(dict(fiscal_year=year, line=int(h), value=val,
                                 text='' if val is not None else v.strip(),
                                 form_id=form_id, source=source, as_of=as_of,
                                 file=os.path.relpath(path, RAW)))
                n += 1
    return n

# 1. The e-mailed files (financial section only: the lines 4000–5999 live there;
#    the general-information file carries the yes/no questions, kept as text).
log('E-mailed CRA files (reply of Dec 6, 2024):')
for ydir in sorted(glob.glob(os.path.join(EMAIL, '[12][0-9][0-9][0-9]'))):
    year = int(os.path.basename(ydir))
    for f in sorted(glob.glob(os.path.join(ydir, '*.csv'))):
        base = os.path.basename(f)
        if base.startswith('Financial Section') or base == 'T3010 Return.csv':
            n = harvest(f, 'cra_email_2024-12-06', EMAIL_AS_OF.get(year, ''), year)
            log(f'  {year}: {base}: {n} fields')

# 2. Open Canada extracts (fetch_open_data.py writes them with SOURCES.tsv).
src_path = os.path.join(OPEN, 'SOURCES.tsv')
if os.path.exists(src_path):
    log('Open Canada extracts:')
    for s in csv.DictReader(open(src_path, encoding='utf-8'), delimiter='\t'):
        f = os.path.join(OPEN, s['local_file'])
        if 'financial' in os.path.basename(f).lower() and os.path.exists(f):
            n = harvest(f, 'open_canada_' + s['year'], s.get('dataset_modified') or s['downloaded_utc'][:10], int(s['year']))
            log(f"  {s['year']}: {s['local_file']}: {n} fields")
else:
    log('Open Canada extracts: none yet (raw/open-canada/SOURCES.tsv absent)')

# 3. Manual entries (fallback).
man = os.path.join(HERE, 'manual_entries.csv')
nman = 0
for m in csv.DictReader(open(man, encoding='utf-8')):
    if not m.get('fiscal_year'):
        continue
    rows.append(dict(fiscal_year=int(m['fiscal_year']), line=int(m['line']), value=money(m['value']),
                     text='', form_id='', source='manual:' + m['source'], as_of=m['date_viewed'],
                     file='manual_entries.csv'))
    nman += 1
log(f'Manual entries: {nman}')

# Resolve one value per (year, line): CRA file first, then manual.
def rank(r):
    return 0 if r['source'].startswith('cra_email') else 1 if r['source'].startswith('open_canada') else 2
best = {}
for r in sorted(rows, key=rank):
    k = (r['fiscal_year'], r['line'])
    if k not in best:
        best[k] = r
dups = [k for k in best if sum(1 for r in rows if (r['fiscal_year'], r['line']) == k) > 1]
if dups:
    conflicts = []
    for k in dups:
        vals = {(r['source'], r['value']) for r in rows if (r['fiscal_year'], r['line']) == k}
        if len({v for _, v in vals}) > 1:
            conflicts.append((k, sorted(vals)))
    log(f'Lines present in more than one source: {len(dups)}; with different values: {len(conflicts)}')
    for k, v in conflicts:
        log(f'  {k}: {v}')

years = sorted({k[0] for k in best if k[0]})
log(f'Fiscal years covered: {years[0]}–{years[-1]} ({len(years)} years)' if years else 'No years')

# Write the long table.
labels = {int(r['line']): r for r in csv.DictReader(open(os.path.join(HERE, 'line_labels.csv'), encoding='utf-8'))}
with open(os.path.join(HERE, 't3010_lines.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['fiscal_year', 'line', 'value', 'text', 'label_en', 'label_status', 'form_id', 'source', 'as_of', 'file'])
    for (y, ln), r in sorted(best.items()):
        lab = labels.get(ln, {})
        w.writerow([y, ln, '' if r['value'] is None else f"{r['value']:.2f}", r['text'],
                    lab.get('label_en', ''), lab.get('status', ''), r['form_id'], r['source'], r['as_of'], r['file']])

def val(y, ln):
    r = best.get((y, ln))
    return r['value'] if r and r['value'] is not None else 0.0

def has(y, ln):
    r = best.get((y, ln))
    return bool(r and r['value'] is not None)

# Summary (checked lines + a few groupings).
SUMMARY = [('total_revenue', 4700), ('receipted_gifts', 4500), ('other_gifts_no_receipt', 4530),
           ('other_revenue_4650', 4650), ('rental_income_4610', 4610), ('interest_4580', 4580), ('governments_4540_4550_4560', None), ('total_expenditures', 5100),
           ('compensation', 4880), ('occupancy', 4850), ('office', 4840), ('professional_fees', 4860),
           ('other_expenditures_4920', 4920), ('cash_and_short_term', 4100), ('long_term_investments', 4140),
           ('total_assets', 4200), ('total_liabilities', 4350)]
with open(os.path.join(HERE, 't3010_summary.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['fiscal_year'] + [n for n, _ in SUMMARY] + ['land_and_buildings', 'surplus_deficit', 'source', 'as_of'])
    for y in years:
        land = val(y, 4155) if has(y, 4155) else val(y, 4160)
        src = best.get((y, 4700), {}).get('source', '')
        asof = best.get((y, 4700), {}).get('as_of', '')
        w.writerow([y] + [f'{(val(y, ln) if ln else val(y,4540)+val(y,4550)+val(y,4560)):.0f}' for _, ln in SUMMARY] +
                   [f'{land:.0f}', f'{val(y, 4700) - val(y, 5100):.0f}', src, asof])

# Consistency checks.
for y in years:
    if has(y, 4950) and has(y, 5100) and abs(val(y, 4950) + val(y, 5050) - val(y, 5100)) > 5:
        log(f'  check: {y} 4950 {val(y,4950):.0f} + 5050 {val(y,5050):.0f} != 5100 {val(y,5100):.0f}')
    assets = sum(val(y, ln) for ln in (4100, 4110, 4120, 4130, 4140, 4150, 4155, 4160, 4165, 4170))
    if has(y, 4200) and abs(assets - val(y, 4200)) > 5:
        log(f'  check: {y} asset lines sum to {assets:.0f}, line 4200 is {val(y,4200):.0f}')

# ---------------------------------------------------------------- charts
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
except ImportError:
    log('matplotlib not available: no charts')
    plt = None

PAL = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300']  # fixed order
INK, INK2, GRID = '#0b0b0b', '#52514e', '#e4e3df'
T = {
 'en': dict(rev='Revenue and expenditures', revsub='Total revenue (line 4700) and total expenditures (line 5100), by fiscal year',
            revcat='Revenue by line', revcatsub='Lines of Section D / Schedule 6 of form T3010; « other » = the total less the lines shown',
            expcat='Expenditures by line', expcatsub='Lines of Section D / Schedule 6 of form T3010; « other » = the total less the lines shown',
            assets='Assets by line', assetssub='Lines of Section D / Schedule 6; total liabilities (line 4350) as a marker',
            revenue='Revenue', expend='Expenditures', k='$ thousand', fy='Fiscal year (ending December 31)',
            src='Source: Canada Revenue Agency, registered charity information returns (T3010) of the Fabrique de la paroisse de Sainte-Monique, BN 130341852RR0001, as released ',
            r4500='Tax-receipted gifts (4500)', r4530='Other gifts, no receipt (4530)', r4650='Other revenue (4650)', r4610='Rental income (4610)', rgov='Governments (4540–4560)', rother='Other lines',
            e4880='Compensation (4880)', e4850='Occupancy (4850)', e4840='Office (4840)', e4860='Professional fees (4860)', e4920='Other expenditures (4920)', eother='Other lines',
            a4100='Cash and short-term (4100)', a4140='Long-term investments (4140)', aland='Land and buildings (4155)', aother='Other assets', liab='Total liabilities (4350)',
            o4650='Other revenue (line 4650), the line that named masses, funerals and weddings', o4650sub='Line 4650 of Schedule 6, $ thousand; the description filed on line 4655 where there is one; « none » = no value filed',
            onone='none'),
 'fr': dict(rev='Revenus et dépenses', revsub='Total des revenus (ligne 4700) et total des dépenses (ligne 5100), par exercice',
            revcat='Revenus par ligne', revcatsub='Lignes de la section D / annexe 6 du formulaire T3010; « autres » = le total moins les lignes montrées',
            expcat='Dépenses par ligne', expcatsub='Lignes de la section D / annexe 6 du formulaire T3010; « autres » = le total moins les lignes montrées',
            assets='Actif par ligne', assetssub='Lignes de la section D / annexe 6; total du passif (ligne 4350) en repère',
            revenue='Revenus', expend='Dépenses', k='k$', fy='Exercice (clos le 31 décembre)',
            src='Source : Agence du revenu du Canada, déclarations de renseignements des organismes de bienfaisance (T3010) de la Fabrique de la paroisse de Sainte-Monique, NE 130341852RR0001, telles que communiquées ',
            r4500='Dons avec reçu (4500)', r4530='Autres dons, sans reçu (4530)', r4650='Autres revenus (4650)', r4610='Revenus de location (4610)', rgov='Gouvernements (4540–4560)', rother='Autres lignes',
            e4880='Rémunération (4880)', e4850='Occupation (4850)', e4840='Bureau (4840)', e4860='Honoraires (4860)', e4920='Autres dépenses (4920)', eother='Autres lignes',
            a4100='Encaisse et court terme (4100)', a4140='Placements à long terme (4140)', aland='Terrains et immeubles (4155)', aother='Autres actifs', liab='Total du passif (4350)',
            o4650='Autres revenus (ligne 4650), la ligne qui nommait messes, funérailles et mariages', o4650sub='Ligne 4650 de l\'annexe 6, k$; la description déclarée à la ligne 4655 lorsqu\'il y en a une; « aucune » = aucune valeur déclarée',
            onone='aucune'),
}

def srcline(lang):
    asofs = sorted({best[(y, 4700)]['as_of'] for y in years if (y, 4700) in best and best[(y, 4700)]['as_of'] and not best[(y, 4700)]['source'].startswith('manual')})
    span = f'{asofs[0]} … {asofs[-1]}' if asofs else ''
    manual = sorted({y for y in years if (y, 4700) in best and best[(y, 4700)]['source'].startswith('manual')})
    flag = ''
    if manual:
        flag = (f"{manual[0]}–{manual[-1]} (hatched): typed from the CRA's quick view (Dec 2024), pending the open-data files; " if lang == 'en'
                else f"{manual[0]}–{manual[-1]} (hachuré) : saisis à la main depuis l'aperçu de l'ARC (déc. 2024), en attendant les fichiers de données ouvertes; ")
    return T[lang]['src'] + (f'({span}); ' if span else '') + flag + ('build ' if lang == 'en' else 'généré le ') + \
        datetime.datetime.now(zoneinfo.ZoneInfo('America/Toronto')).strftime('%Y-%m-%d')

def style(ax, lang, title, sub):
    ax.set_title(title, loc='left', fontsize=13, color=INK, pad=22, fontweight='bold')
    ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9, color=INK2)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.spines['bottom'].set_color(GRID)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(colors=INK2, labelsize=9, length=0)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f'{v/1000:,.0f}'.replace(',', ' ' if lang == 'fr' else ',')))
    ax.set_ylabel(T[lang]['k'], color=INK2, fontsize=9)
    ax.set_xlabel(T[lang]['fy'], color=INK2, fontsize=9)
    ax.set_xticks(years)
    ax.set_xticklabels([str(y) for y in years], fontsize=8)

def finish(fig, ax, lang, name):
    fig.text(0.01, 0.01, srcline(lang), fontsize=7, color=INK2, wrap=True)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    for ext in ('svg', 'png', 'pdf'):
        fig.savefig(os.path.join(FIG, f'{name}_{lang}.{ext}'), dpi=160)
    plt.close(fig)

def stacked(ax, series, lang):
    """series: list of (label, values[]) in fixed palette order; 2 px gaps via white edges."""
    bottom = [0.0] * len(years)
    for i, (lab, vals) in enumerate(series):
        bars = ax.bar(years, vals, bottom=bottom, width=0.72, color=PAL[i], label=lab, edgecolor='white', linewidth=1.2)
        for b, y in zip(bars, years):
            if (y, 4700) in best and best[(y, 4700)]['source'].startswith('manual'):
                b.set_hatch('////')
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.legend(frameon=False, fontsize=8, loc='upper right', ncol=2, labelcolor=INK)

if plt and years:
    os.makedirs(FIG, exist_ok=True)
    for lang in ('en', 'fr'):
        t = T[lang]
        # 1. Revenue vs expenditures: two thin bars side by side.
        fig, ax = plt.subplots(figsize=(9, 4.8))
        style(ax, lang, t['rev'], t['revsub'])
        w = 0.36
        b1 = ax.bar([y - w/2 for y in years], [val(y, 4700) for y in years], width=w, color=PAL[0], label=t['revenue'], edgecolor='white', linewidth=1.2)
        b2 = ax.bar([y + w/2 for y in years], [val(y, 5100) for y in years], width=w, color=PAL[1], label=t['expend'], edgecolor='white', linewidth=1.2)
        for bb in (b1, b2):
            for b, y in zip(bb, years):
                if (y, 4700) in best and best[(y, 4700)]['source'].startswith('manual'):
                    b.set_hatch('////')
        ax.legend(frameon=False, fontsize=9, loc='upper right', labelcolor=INK)
        finish(fig, ax, lang, 'revenue_and_expenditures')
        # 2. Revenue by line.
        fig, ax = plt.subplots(figsize=(9, 5))
        style(ax, lang, t['revcat'], t['revcatsub'])
        shown = [(t['r4500'], [val(y, 4500) for y in years]), (t['r4530'], [val(y, 4530) for y in years]),
                 (t['r4650'], [val(y, 4650) for y in years]), (t['r4610'], [val(y, 4610) for y in years]), (t['rgov'], [val(y,4540)+val(y,4550)+val(y,4560) for y in years])]
        other = [max(0.0, val(y, 4700) - sum(s[1][i] for s in shown)) for i, y in enumerate(years)]
        stacked(ax, shown + [(t['rother'], other)], lang)
        finish(fig, ax, lang, 'revenue_by_line')
        # 3. Expenditures by line.
        fig, ax = plt.subplots(figsize=(9, 5))
        style(ax, lang, t['expcat'], t['expcatsub'])
        shown = [(t['e4880'], [val(y, 4880) for y in years]), (t['e4850'], [val(y, 4850) for y in years]),
                 (t['e4840'], [val(y, 4840) for y in years]), (t['e4860'], [val(y, 4860) for y in years]),
                 (t['e4920'], [val(y, 4920) for y in years])]
        other = [max(0.0, val(y, 5100) - sum(s[1][i] for s in shown)) for i, y in enumerate(years)]
        stacked(ax, shown + [(t['eother'], other)], lang)
        finish(fig, ax, lang, 'expenditures_by_line')
        # 4. Assets by line, liabilities as markers.
        fig, ax = plt.subplots(figsize=(9, 5))
        style(ax, lang, t['assets'], t['assetssub'])
        land = [val(y, 4155) if has(y, 4155) else val(y, 4160) for y in years]
        shown = [(t['aland'], land), (t['a4140'], [val(y, 4140) for y in years]), (t['a4100'], [val(y, 4100) for y in years])]
        other = [max(0.0, val(y, 4200) - sum(s[1][i] for s in shown)) for i, y in enumerate(years)]
        stacked(ax, shown + [(t['aother'], other)], lang)
        ax.plot(years, [val(y, 4350) for y in years], linestyle='none', marker='D', markersize=5, color=INK, label=t['liab'])
        ax.legend(frameon=False, fontsize=8, loc='upper right', ncol=2, labelcolor=INK)
        finish(fig, ax, lang, 'assets_by_line')
        # 5. Line 4650 on its own, with the text of line 4655 where filed.
        fig, ax = plt.subplots(figsize=(9, 4.8))
        style(ax, lang, t['o4650'], t['o4650sub'])
        vals = [val(y, 4650) for y in years]
        ax.bar(years, vals, width=0.72, color=PAL[2], edgecolor='white', linewidth=1.2)
        top = max(vals) if vals else 0
        for y, v in zip(years, vals):
            if has(y, 4650):
                ax.text(y, v + top * 0.015, f'{v/1000:,.1f}'.replace(',', ' ' if lang == 'fr' else ','), ha='center', va='bottom', fontsize=7, color=INK2)
            else:
                ax.text(y, top * 0.015, t['onone'], ha='center', va='bottom', fontsize=7, color=INK2, rotation=90)
        k = 0
        for y in years:
            txt = best.get((y, 4655), {}).get('text', '').strip()
            if txt:
                v = val(y, 4650)
                ax.annotate(f'{y}: « ' + ' '.join(txt.split()).rstrip('-').strip() + ' »', xy=(y, v + top * 0.07), xytext=(y - (1.5 if y > years[-3] else 0), top * (1.17 + 0.1 * (k % 2))), textcoords='data',
                            ha='center', va='bottom', fontsize=7, color=INK, arrowprops=dict(arrowstyle='-', color=INK2, lw=0.6))
                k += 1
        ax.set_ylim(0, top * 1.4)
        finish(fig, ax, lang, 'other_revenue_4650')
    log(f'Charts written to figures/ for {len(years)} years (five charts, EN and FR)')


# ---------------------------------------------------------------- LaTeX note
if years:
    def money_tex(v):
        return f'{v:,.0f}'.replace(',', '\\,')
    TABLE = {'en': [('Line', None), ('4700 Total revenue', 4700), ('4500 Tax-receipted gifts', 4500), ('4530 Other gifts', 4530), ('4610 Rental income', 4610),
                    ('4650 Other revenue', 4650), ('5100 Total expenditures', 5100), ('4880 Compensation', 4880),
                    ('4850 Occupancy', 4850), ('4200 Total assets', 4200), ('4100 Cash and short-term', 4100),
                    ('4140 Long-term investments', 4140), ('4155 Land and buildings', 4155), ('4350 Total liabilities', 4350), ('Revenue less expenditures', 'diff')],
             'fr': [('Ligne', None), ('4700 Total des revenus', 4700), ('4500 Dons avec reçu', 4500), ('4530 Autres dons', 4530), ('4610 Revenus de location', 4610),
                    ('4650 Autres revenus', 4650), ('5100 Total des dépenses', 5100), ('4880 Rémunération', 4880),
                    ('4850 Occupation', 4850), ('4200 Total de l\'actif', 4200), ('4100 Encaisse et court terme', 4100),
                    ('4140 Placements à long terme', 4140), ('4155 Terrains et immeubles', 4155), ('4350 Total du passif', 4350), ('Revenus moins dépenses', 'diff')]}
    for lang, rows_ in TABLE.items():
        with open(os.path.join(HERE, f'summary_table_{lang}.tex'), 'w', encoding='utf-8') as f:
            f.write('\\begin{tabular}{@{}l' + 'r' * len(years) + '@{}}\\toprule\n')
            f.write(rows_[0][0] + ' & ' + ' & '.join((str(y) + ('*' if best.get((y, 4700), {}).get('source', '').startswith('manual') else '')) for y in years) + ' \\\\\\midrule\n')
            for lab, ln in rows_[1:-1]:
                f.write(lab + ' & ' + ' & '.join(money_tex(val(y, ln)) if has(y, ln) else '--' for y in years) + ' \\\\\n')
            f.write(rows_[-1][0] + ' & ' + ' & '.join(money_tex(val(y, 4700) - val(y, 5100)) for y in years) + ' \\\\\\bottomrule\n')
            f.write('\\end{tabular}\n')
    if plt:
        pass
    import subprocess, shutil
    # Peer comparison (peer_parishes.csv + raw/open-canada-peers/): tables and three more charts.
    if os.path.exists(os.path.join(RAW, 'open-canada-peers', 'SOURCES.tsv')):
        r = subprocess.run([sys.executable, os.path.join(HERE, 'peer_comparison.py')], capture_output=True, text=True, errors='replace')
        log('Peer comparison: ' + ('done (peer_comparison_*.csv, figures/peers_*)' if r.returncode == 0 else 'FAILED ' + r.stderr[-800:]))
    # Detection threshold (needs peer_comparison_long.csv): table and the abstract's sentence, EN and FR.
    if os.path.exists(os.path.join(HERE, 'peer_comparison_long.csv')):
        r = subprocess.run([sys.executable, os.path.join(HERE, 'detection_threshold.py')], capture_output=True, text=True, errors='replace')
        log('Detection threshold: ' + ('done (detection_threshold.csv, detection_threshold_*.tex, detection_sentence_*.tex)' if r.returncode == 0 else 'FAILED ' + r.stderr[-800:]))
    # The parish's own statements (parish_statements_monthly.csv): two charts and the cross-check table.
    if os.path.exists(os.path.join(HERE, 'parish_statements_monthly.csv')):
        r = subprocess.run([sys.executable, os.path.join(HERE, 'parish_statements.py')], capture_output=True, text=True, errors='replace')
        log('Parish statements: ' + ('done (statements_vs_returns_*.tex, figures/parish_*)' if r.returncode == 0 else 'FAILED ' + r.stderr[-800:]))
    stamp = datetime.datetime.now(zoneinfo.ZoneInfo('America/Toronto')).strftime('%Y-%m-%d-%H-%M-%S')
    for tex in [os.path.join(HERE, f'st_monica_t3010_note_{lang}.tex') for lang in ('en', 'fr')]:
        if not (os.path.exists(tex) and shutil.which('pdflatex')):
            continue
        s = open(tex, encoding='utf-8').read()
        s = re.sub(r'\\newcommand\{\\docversion\}\{[^}]*\}', '\\\\newcommand{\\\\docversion}{' + stamp + '}', s)
        open(tex, 'w', encoding='utf-8').write(s)
        for _ in range(3):
            r = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', os.path.basename(tex)], cwd=HERE, capture_output=True, text=True, errors='replace')
        if r.returncode == 0:
            log(f'Note compiled: {os.path.basename(tex)[:-4]}.pdf, version {stamp}')
            for ext in ('aux', 'log', 'out'):
                p = os.path.join(HERE, os.path.basename(tex)[:-4] + '.' + ext)
                if os.path.exists(p): os.remove(p)
        else:
            log(f'LaTeX failed ({os.path.basename(tex)}): ' + r.stdout[-1500:])

with open(os.path.join(HERE, 'build_report.txt'), 'w', encoding='utf-8') as f:
    f.write('\n'.join(report) + '\n')
print('\n'.join(report))
