#!/usr/bin/env python3
"""Build the poster "Rue de Terrebonne in winter: the numbers on one page" in English and French from the data.

Inputs (sibling clones of the OpenMobilityData repositories, paths overridable with --access=, --telraam=):
  Terrebonne-access-requests/2026-581/derived/kensington_daily_borough_release_2025-07_2026-08.csv   (counter, daily)
  Terrebonne-access-requests/2026-581/derived/figures/kensington-monthly/*.svg, kensington-violins/*winter*.svg  (charts, copied)
  Terrebonne-access-requests/2026-300/derived/en_climate_daily_QC_7025251_{2025,2026}_P1D.csv          (Environment Canada)
  Terrebonne-access-requests/2026-300/derived/exposure_tables.txt                                       (snow-loading days, share outside)
  Terrebonne-telraam/derived/speeds_by_season.csv, daily.csv                                            (telraam_summaries.py)
  timeline.csv (hand-curated, EN/FR), manual_facts.json (numbers from analyses outside this build, with sources)
Templates: templates/poster_en.html, templates/poster_fr.html ({{key}} placeholders; the prose lives there).
Outputs: poster_terrebonne_winter_numbers_{en,fr}.html, .pdf (one sheet, needs Google Chrome), .png (preview).
Usage: python3 build_poster.py [--no-render]
"""
import csv, os, sys, json, re, shutil, subprocess, tempfile, datetime as dt, statistics as st, collections
HERE = os.path.dirname(os.path.abspath(__file__))
opts = dict(a[2:].split('=', 1) if '=' in a else (a[2:], '1') for a in sys.argv[1:] if a.startswith('--'))
ACC = opts.get('access', os.path.join(HERE, '..', '..', 'Terrebonne-access-requests'))
TEL = opts.get('telraam', os.path.join(HERE, '..', '..', 'Terrebonne-telraam'))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
Y0, Y1 = dt.date(2025, 7, 26), dt.date(2026, 7, 25); W0, W1 = dt.date(2025, 12, 1), dt.date(2026, 3, 31)
MONTHS = {'en': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
          'fr': ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.']}

def num(v, lang, dec=0):
    s = f'{v:,.{dec}f}'
    return s if lang == 'en' else s.replace(',', ' ').replace('.', ',')

def ffloat(x):
    try: return float(x)
    except (TypeError, ValueError): return None

def main():
    F = {}
    # --- counter
    rows = [(dt.date.fromisoformat(r['date']), int(r['bike'] or 0), int(r['motor'] or 0)) for r in csv.DictReader(open(os.path.join(ACC, '2026-581', 'derived', 'kensington_daily_borough_release_2025-07_2026-08.csv'), encoding='utf-8-sig'))]
    year = [r for r in rows if Y0 <= r[0] <= Y1]; winter = [r for r in year if W0 <= r[0] <= W1]; rest = [r for r in year if not (W0 <= r[0] <= W1)]
    wb = [b for _, b, _ in winter]
    F['year_total'] = sum(b for _, b, _ in year); F['year_per_day'] = F['year_total'] / len(year)
    F['motor_per_day'] = sum(c for _, _, c in year) / len(year)
    F['winter_total'] = sum(wb); F['winter_days'] = len(wb); F['winter_per_day'] = F['winter_total'] / len(wb)
    F['winter_min'] = min(wb); F['winter_max'] = max(wb); F['winter_25_75'] = sum(1 for b in wb if 25 <= b <= 75)
    F['rest_per_day'] = sum(b for _, b, _ in rest) / len(rest)
    F['drop_per_day_pct'] = 100 * (1 - F['winter_per_day'] / F['rest_per_day'])
    F['share_year_pct'] = 100 * F['winter_total'] / F['year_total']; F['ratio_per_day_pct'] = 100 * F['winter_per_day'] / F['rest_per_day']
    F['ratio_annual_pct'] = 100 * F['winter_per_day'] / F['year_per_day']; F['const_share_pct'] = 100 * len(wb) / len(year); F['rest_days'] = len(rest)
    F['counter_last'] = max(r[0] for r in rows)
    bym = collections.defaultdict(list)
    for d, b, c in rows:
        if dt.date(2025, 8, 1) <= d <= dt.date(2026, 7, 31): bym[(d.year, d.month)].append((b, c))
    F['_months'] = [(k, st.median(x[0] for x in v), st.mean(x[0] for x in v), st.mean(x[1] for x in v)) for k, v in sorted(bym.items())]
    # --- speeds
    sp = {(r['segment'], r['season']): r for r in csv.DictReader(open(os.path.join(TEL, 'derived', 'speeds_by_season.csv'), encoding='utf-8'))}
    for seg, tag in (('west', 'ke'), ('east', 'dr')):
        for s in ('winter', 'summer'):
            r = sp[(seg, s)]; F[f'{tag}_{s}_v85'] = round(float(r['v85_median'])); F[f'{tag}_{s}_o30'] = round(float(r['share_over_30'])); F[f'{tag}_{s}_o40'] = round(float(r['share_over_40']))
    tl = [r for r in csv.DictReader(open(os.path.join(TEL, 'derived', 'daily.csv'), encoding='utf-8'))]
    F['telraam_last'] = max(r['date'] for r in tl)
    for seg, tag in (('west', 'ke'), ('east', 'dr')):
        F[f'{tag}_jan29'] = next(int(r['bikes']) for r in tl if r['segment'] == seg and r['date'] == '2025-01-29')
        F[f'{tag}_jan28'] = next(int(r['bikes']) for r in tl if r['segment'] == seg and r['date'] == '2025-01-28')
    # --- weather
    wx = []
    for y in (2025, 2026):
        wx += list(csv.DictReader(open(os.path.join(ACC, '2026-300', 'derived', f'en_climate_daily_QC_7025251_{y}_P1D.csv'), encoding='utf-8-sig')))
    col = lambda r, k: next(r[c] for c in r if k in c)
    ww = [r for r in wx if '2025-12-01' <= r['Date/Time'] <= '2026-03-31']
    snow = [ffloat(col(r, 'Total Snow')) for r in ww]; tmin = [ffloat(col(r, 'Min Temp')) for r in ww]
    F['snow_total_cm'] = sum(s for s in snow if s); F['snow_days_25'] = sum(1 for s in snow if s and s >= 2.5); F['snow_days_10'] = sum(1 for s in snow if s and s >= 10)
    F['cold_days_m20'] = sum(1 for t in tmin if t is not None and t <= -20); F['coldest'] = min(t for t in tmin if t is not None)
    j = next(r for r in wx if r['Date/Time'] == '2025-01-29')
    F['j29_snow'] = ffloat(col(j, 'Total Snow')); F['j29_max'] = ffloat(col(j, 'Max Temp')); F['j29_min'] = ffloat(col(j, 'Min Temp')); F['j29_gust'] = ffloat(col(j, 'Spd of Max Gust'))
    # --- snow loading (first block of exposure_tables.txt = Dec 1 – Mar 31)
    txt = open(os.path.join(ACC, '2026-300', 'derived', 'exposure_tables.txt'), encoding='utf-8').read()
    F['loading_days'] = int(re.search(r'Sector CDN-301 loading days.*?days\s+(\d+)', txt).group(1))
    F['outside_pct'] = 100 - int(re.search(r'From triggering snowfall through CDN-301 loading.*?(\d+)%', txt).group(1))
    # --- manual facts
    M = json.load(open(os.path.join(HERE, 'manual_facts.json'), encoding='utf-8'))
    F['camera_sept'] = M['camera_sept_count']['value']; F['camera_jan'] = M['camera_jan_count']['value']; F['cars_drop'] = M['camera_cars_drop_pct']['value']; F['peds_drop'] = M['camera_peds_drop_pct']['value']
    F['like_for_like'] = M['like_for_like_pct']['value']; F['djma_2022'] = M['djma_2022']['value']; F['lane_width'] = M['lane_width_m']['value']
    # --- charts
    os.makedirs(os.path.join(HERE, 'poster_assets'), exist_ok=True)
    for lang in ('en', 'fr'):
        for src in (os.path.join(ACC, '2026-581', 'derived', 'figures', 'kensington-monthly', f'kensington_monthly_2025-26_{lang}.svg'),
                    os.path.join(ACC, '2026-581', 'derived', 'figures', 'kensington-violins', f'kensington_daily_violin_winter_{lang}.svg')):
            shutil.copy(src, os.path.join(HERE, 'poster_assets', os.path.basename(src)))
    # --- timeline
    tlr = list(csv.DictReader(open(os.path.join(HERE, 'timeline.csv'), encoding='utf-8')))
    built = dt.date.today()
    for lang in ('en', 'fr'):
        V = {}
        for k, v in F.items():
            if k.startswith('_'): continue
            if isinstance(v, float): V[k] = num(v, lang, 1 if k in ('coldest', 'j29_snow', 'j29_max', 'j29_min', 'share_year_pct', 'ratio_per_day_pct', 'ratio_annual_pct') else 0)
            elif isinstance(v, int): V[k] = num(v, lang)
            else: V[k] = str(v)
        V['lane_width'] = num(F['lane_width'], lang, 1)
        V['loading_rank'] = M['loading_season_rank'][lang]
        V['month_rows'] = ''.join(f'<tr{" class=w" if k[1] in (12, 1, 2, 3) else ""}><td>{MONTHS[lang][k[1]-1]}{" " + str(k[0]) if k[1] in (8, 1) else ""}</td><td>{num(med, lang)}</td><td>{num(mean, lang)}</td><td>{num(motor, lang)}</td></tr>' for k, med, mean, motor in F['_months'])
        V['timeline_items'] = ''.join(f'<li class="{r["class"]}"><b>{r["date_fr"] if lang == "fr" else r["date"]}</b>{r[lang]}</li>' for r in tlr)
        V['built'] = built.strftime('%B %-d, %Y') if lang == 'en' else f'{built.day} {["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"][built.month]} {built.year}'
        V['counter_last'] = F['counter_last'].strftime('%B %-d, %Y') if lang == 'en' else f'{F["counter_last"].day} {["", "janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"][F["counter_last"].month]} {F["counter_last"].year}'
        V['lang'] = lang
        V['css'] = open(os.path.join(HERE, 'templates', 'poster.css'), encoding='utf-8').read()
        tpl = open(os.path.join(HERE, 'templates', f'poster_{lang}.html'), encoding='utf-8').read()
        missing = sorted(set(re.findall(r'{{(\w+)}}', tpl)) - set(V))
        assert not missing, f'{lang}: placeholders without values: {missing}'
        out = re.sub(r'{{(\w+)}}', lambda m: V[m.group(1)], tpl)
        html_path = os.path.join(HERE, f'poster_terrebonne_winter_numbers_{lang}.html')
        open(html_path, 'w', encoding='utf-8').write(out)
        print('wrote', os.path.basename(html_path))
        if 'no-render' in opts or not os.path.exists(CHROME): continue
        pdf = html_path[:-5] + '.pdf'
        subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--print-to-pdf={pdf}', f'file://{html_path}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        with tempfile.TemporaryDirectory() as td:
            light = os.path.join(td, 'light.html')
            open(light, 'w', encoding='utf-8').write(out.replace(f'<html lang="{lang}">', f'<html lang="{lang}" data-theme="light">').replace('src="poster_assets/', f'src="file://{HERE}/poster_assets/'))
            subprocess.run([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--window-size=1100,2200', f'--screenshot={html_path[:-5]}.png', f'file://{light}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
        print('rendered', os.path.basename(pdf), 'and .png')
    print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in F.items() if not k.startswith('_')})

if __name__ == '__main__':
    main()
