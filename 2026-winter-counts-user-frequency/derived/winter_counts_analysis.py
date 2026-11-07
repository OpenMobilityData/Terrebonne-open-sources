#!/usr/bin/env python3
"""Winter bicycle counts on rue de Terrebonne on every sensor, a user-frequency distribution, and the APC-NDG survey in context.

Reads (in place, nothing copied):
  Kensington loop hourly (request 2026-300), Kensington daily release (request 2026-581),
  Telraam King Edward / Draper hourly exports (private copy, TELRAAM_RAW), City detector det-00118 at Girouard (../raw extract),
  ECCC daily Montréal-Trudeau (2024 in ../raw, 2025–2026 in 2026-300/derived).
Writes derived/: summary.json, coverage.csv, cross_sensor_ratios.csv, kensington_winter_days.csv, band_fit.csv, survey_context.csv, figures/*.png
Usage: ~/.venvs/omd/bin/python winter_counts_analysis.py [--telraam-raw DIR] [--access-requests DIR]
"""
import os, sys, csv, json, math, re, argparse, datetime as dt, collections
import numpy as np
from scipy import optimize, special, stats
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, '..', 'raw'); FIG = os.path.join(HERE, 'figures')
ap = argparse.ArgumentParser()
ap.add_argument('--telraam-raw', default=os.environ.get('TELRAAM_RAW', os.path.expanduser('~/GitHub/Terrebonne-private/data/telraam/raw')))
ap.add_argument('--access-requests', default=os.path.expanduser('~/GitHub/Terrebonne-access-requests'))
A = ap.parse_args()
os.makedirs(FIG, exist_ok=True)
LAT, LON = 45.4702, -73.6320
W1 = (dt.date(2024, 12, 1), dt.date(2025, 3, 31)); W2 = (dt.date(2025, 12, 1), dt.date(2026, 3, 31))
CORE = (dt.date(2025, 12, 1), dt.date(2026, 2, 28))          # Kensington westbound channel sound; Draper to Jan 23
KEN_WB_END = dt.date(2026, 2, 28); DRAPER_END = dt.date(2026, 1, 23)
MIN_HOURS, MIN_UPTIME, UP_HOUR = 8, 6.0, 0.7
# validated default palette (dataviz skill, references/palette.md), fixed categorical order
C = {'ken': '#2a78d6', 'ke': '#eb6834', 'dr': '#1baf7a', 'gir': '#eda100', 'eb': '#2a78d6', 'wb': '#86b6ef',
     'daily': '#2a78d6', 'regular': '#eb6834', 'occas': '#1baf7a', 'ink': '#0b0b0b', 'ink2': '#52514e', 'grid': '#e6e5e1', 'surf': '#fcfcfb'}
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 9, 'axes.edgecolor': C['ink2'], 'axes.labelcolor': C['ink'], 'xtick.color': C['ink2'], 'ytick.color': C['ink2'],
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6, 'axes.axisbelow': True,
                     'figure.facecolor': C['surf'], 'axes.facecolor': C['surf'], 'savefig.dpi': 200, 'legend.frameon': False})
SRC = 'Sources: borough loop counter at Kensington (requests 2026-300, 2026-581); Telraam S2 sensors at King Edward and Draper (author; counts: Telraam); City detector det-00118 at Girouard (open data, CC-BY 4.0); ECCC daily, Montréal-Trudeau.'
def foot(fig, text=SRC): fig.text(0.01, 0.005, text, fontsize=6, color=C['ink2'], ha='left', va='bottom')
S = {}   # everything the documents quote

# ---------------------------------------------------------------- 1. load
def utc_offset(d):     # America/Toronto: DST from the 2nd Sunday of March to the 1st Sunday of November
    y = d.year; mar = dt.date(y, 3, 8 + (6 - dt.date(y, 3, 8).weekday()) % 7); nov = dt.date(y, 11, 1 + (6 - dt.date(y, 11, 1).weekday()) % 7)
    return -4 if mar <= d < nov else -5
def sun(d):            # NOAA sunrise/sunset, local decimal hours
    n = d.timetuple().tm_yday; g = 2 * math.pi / 365 * (n - 1 + 0.5)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = 0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g)
    la = math.radians(LAT); ha = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(dec)) - math.tan(la) * math.tan(dec)))
    rise = (720 - 4 * (LON + ha) - eq) / 60 + utc_offset(d); set_ = (720 - 4 * (LON - ha) - eq) / 60 + utc_offset(d)
    return rise, set_
def read_eccc():
    w = {}
    for f in (os.path.join(RAW, 'en_climate_daily_QC_7025251_2024_P1D.csv'),) + tuple(os.path.join(A.access_requests, '2026-300', 'derived', f'en_climate_daily_QC_7025251_{y}_P1D.csv') for y in (2025, 2026)):
        for r in csv.DictReader(open(f, encoding='utf-8-sig')):
            try: d = dt.date.fromisoformat(r['Date/Time'])
            except ValueError: continue
            fl = lambda k: None if r[k] in ('', None) else float(r[k])
            w[d] = dict(snow=fl('Total Snow (cm)'), tmean=fl('Mean Temp (°C)'), tmin=fl('Min Temp (°C)'), sog=fl('Snow on Grnd (cm)'), precip=fl('Total Precip (mm)'))
    return w
WX = read_eccc()
def read_kensington_hourly():
    ws = openpyxl.load_workbook(os.path.join(A.access_requests, '2026-300', 'raw', '26072025_11052026.xlsx'), read_only=True).worksheets[0]
    out = {}
    for t, tot, eb, wb, mv in ws.iter_rows(min_row=4, values_only=True):
        if t is None: continue
        out[t.replace(minute=0, second=0)] = (eb or 0, wb or 0, mv or 0)
    return out
def read_kensington_daily():
    out = {}
    for r in csv.DictReader(open(os.path.join(A.access_requests, '2026-581', 'derived', 'kensington_daily_borough_release_2025-07_2026-08.csv'), encoding='utf-8')):
        out[dt.date.fromisoformat(r['date'])] = (float(r['bike'] or 0), float(r['motor'] or 0))
    return out
def read_telraam(seg):
    out = {}
    for y in (2024, 2025, 2026):
        f = os.path.join(A.telraam_raw, f'raw-data-{y}{seg}60.xlsx')
        if not os.path.exists(f): continue
        ws = openpyxl.load_workbook(f, read_only=True, data_only=True).active; it = ws.iter_rows(values_only=True); hdr = next(it); ix = {h: i for i, h in enumerate(hdr)}
        for r in it:
            t = r[ix['Date and Time (Local)']]
            if t is None: continue
            if isinstance(t, str): t = dt.datetime.fromisoformat(t)
            m = re.search(r'([0-9]*\.?[0-9]+)\s*$', str(r[ix['Uptime']] or '')); up = float(m.group(1)) if m else 0.0
            out[t.replace(minute=0, second=0)] = (r[ix['Bike (A > B)']] or 0, r[ix['Bike (B > A)']] or 0, up)
    return out
def read_girouard():
    h, d = {}, {}
    for r in csv.DictReader(open(os.path.join(RAW, 'city_detector_det-00118_girouard-terrebonne_hourly_daily_2025-2026_extract_2026-10-16.csv'), encoding='utf-8')):
        if r['instance'] != 'det-00118-01': continue
        t = dt.datetime.fromisoformat(r['periode'][:16])
        if r['agg_code'] == 'h': h[t] = float(r['volume'])
        elif r['agg_code'] == 'd': d[t.date()] = float(r['volume'])
    return h, d
KH = read_kensington_hourly(); KD = read_kensington_daily(); KE = read_telraam('West'); DR = read_telraam('East'); GH, GD = read_girouard()
print(f'loaded: Kensington hourly {len(KH)}, daily {len(KD)}; Telraam KE {len(KE)}, Draper {len(DR)}; Girouard hourly {len(GH)}, daily {len(GD)}', file=sys.stderr)

def daily_frame(d0, d1):
    rows = []
    for i in range((d1 - d0).days + 1):
        d = d0 + dt.timedelta(i); r = dict(date=d, dow=d.weekday(), weekend=int(d.weekday() >= 5), holiday=int((d.month == 12 and d.day >= 22) or (d.month == 1 and d.day <= 4)))
        rise, set_ = sun(d); r['daylight_h'] = round(set_ - rise, 2)
        w = WX.get(d, {}); r.update(snow=w.get('snow'), tmean=w.get('tmean'), tmin=w.get('tmin'), sog=w.get('sog'))
        hs = [KH.get(dt.datetime.combine(d, dt.time(h))) for h in range(24)]
        r['ken_hours'] = sum(1 for x in hs if x is not None)
        r['ken_eb'] = sum(x[0] for x in hs if x) if r['ken_hours'] else None; r['ken_wb'] = sum(x[1] for x in hs if x) if r['ken_hours'] else None
        r['ken_tot'] = (r['ken_eb'] + r['ken_wb']) if r['ken_hours'] else (KD[d][0] if d in KD else None)
        r['ken_dark'] = sum((x[0] + x[1]) for h, x in enumerate(hs) if x and (h + 0.5 < rise or h + 0.5 > set_)) if r['ken_hours'] else None
        if r['ken_hours']:
            am_eb = sum(hs[h][0] for h in range(6, 10) if hs[h]); pm_wb = sum(hs[h][1] for h in range(15, 20) if hs[h]); am_wb = sum(hs[h][1] for h in range(6, 10) if hs[h]); pm_eb = sum(hs[h][0] for h in range(15, 20) if hs[h])
            r['pairs'] = min(am_eb, pm_wb) + min(am_wb, pm_eb)
        else: r['pairs'] = None
        for key, T in (('ke', KE), ('dr', DR)):
            ts = [T.get(dt.datetime.combine(d, dt.time(h))) for h in range(24)]
            n = sum(1 for x in ts if x is not None); up = sum(x[2] for x in ts if x)
            r[key + '_hours'] = n; r[key + '_uptime'] = round(up, 2); r[key + '_valid'] = int(n >= MIN_HOURS and up >= MIN_UPTIME)
            r[key + '_ab'] = sum(x[0] for x in ts if x); r[key + '_ba'] = sum(x[1] for x in ts if x); r[key + '_tot'] = r[key + '_ab'] + r[key + '_ba']
        r['gir_wb'] = GD.get(d); r['gir_hours'] = sum(1 for h in range(24) if dt.datetime.combine(d, dt.time(h)) in GH)
        r['harsh'] = int((r['snow'] or 0) >= 2.5 or (r['tmean'] is not None and r['tmean'] <= -10))
        rows.append(r)
    return rows
DF = daily_frame(dt.date(2024, 8, 15), dt.date(2026, 8, 31)); byd = {r['date']: r for r in DF}
def sel(d0, d1, pred=lambda r: True): return [r for r in DF if d0 <= r['date'] <= d1 and pred(r)]

# ---------------------------------------------------------------- 2. coverage
cov = []
for name, key, valid in (('Kensington loop (borough)', 'ken', lambda r: r['ken_tot'] is not None), ('King Edward (Telraam)', 'ke', lambda r: r['ke_valid']), ('Draper (Telraam)', 'dr', lambda r: r['dr_valid']), ('Girouard WB (City det-00118-01)', 'gir', lambda r: r['gir_wb'] is not None)):
    for wname, (a, b) in (('W1 2024-25', W1), ('W2 2025-26', W2)):
        rs = sel(a, b, valid); tot = sum((r['ken_tot'] if key == 'ken' else r['ke_tot'] if key == 'ke' else r['dr_tot'] if key == 'dr' else r['gir_wb']) for r in rs)
        cov.append(dict(sensor=name, winter=wname, valid_days=len(rs), days=(b - a).days + 1, first=min((r['date'] for r in rs), default=''), last=max((r['date'] for r in rs), default=''), passages=int(tot)))
with open(os.path.join(HERE, 'coverage.csv'), 'w', newline='') as f: w = csv.DictWriter(f, fieldnames=list(cov[0].keys())); w.writeheader(); w.writerows(cov)
S['coverage'] = cov
# figure: coverage timeline + Kensington daily series
fig, ax = plt.subplots(2, 1, figsize=(9, 5.2), height_ratios=[1.2, 2.2], sharex=True)
lanes = [('Kensington loop', 'ken', lambda r: r['ken_tot'] is not None), ('King Edward (Telraam)', 'ke', lambda r: r['ke_valid']), ('Draper (Telraam)', 'dr', lambda r: r['dr_valid']), ('Girouard WB (City)', 'gir', lambda r: r['gir_wb'] is not None)]
for i, (lab, key, v) in enumerate(lanes):
    xs = [r['date'] for r in DF if v(r)]; ax[0].scatter(xs, [i] * len(xs), s=4, color=C[key], marker='|', linewidths=0.8)
ax[0].set_yticks(range(len(lanes))); ax[0].set_yticklabels([l[0] for l in lanes]); ax[0].invert_yaxis(); ax[0].set_title('Days with data, August 2024 to August 2026', loc='left', fontsize=10, color=C['ink'])
for (a, b) in (W1, W2):
    for axx in ax: axx.axvspan(a, b, color='#f0efec', zorder=0)
xs = [r['date'] for r in DF if r['ken_tot'] is not None]; ax[1].plot(xs, [byd[d]['ken_tot'] for d in xs], color=C['ken'], lw=0.9, label='Kensington loop, both directions')
xs = [r['date'] for r in DF if r['ke_valid']]; ax[1].plot(xs, [byd[d]['ke_tot'] for d in xs], color=C['ke'], lw=0.7, alpha=0.9, label='King Edward (Telraam, daylight)')
xs = [r['date'] for r in DF if r['dr_valid']]; ax[1].plot(xs, [byd[d]['dr_tot'] for d in xs], color=C['dr'], lw=0.7, alpha=0.9, label='Draper (Telraam, daylight)')
xs = [r['date'] for r in DF if r['gir_wb'] is not None]; ax[1].plot(xs, [byd[d]['gir_wb'] for d in xs], color=C['gir'], lw=0.7, alpha=0.9, label='Girouard, westbound only (City)')
ax[1].set_yscale('log'); ax[1].set_ylabel('bicycle passages per day (log scale)'); ax[1].legend(loc='lower left', fontsize=7, ncol=2); ax[1].set_ylim(1, 2000)
ax[1].text(W1[0], 1500, 'winter 2024–25', fontsize=7, color=C['ink2']); ax[1].text(W2[0], 1500, 'winter 2025–26', fontsize=7, color=C['ink2'])
foot(fig); fig.tight_layout(rect=(0, 0.02, 1, 1)); fig.savefig(os.path.join(FIG, 'coverage_and_series_en.png')); plt.close(fig)

# ---------------------------------------------------------------- 3. cross-sensor comparison on matched hours
def matched(T, d0, d1, hours=range(8, 17), minup=UP_HOUR):
    out = []
    for t, (ab, ba, up) in T.items():
        if d0 <= t.date() <= d1 and t.hour in hours and up >= minup and t in KH: out.append((t, ab, ba, KH[t][0], KH[t][1]))
    return out
ratios = []
def ratio_row(label, T, d0, d1, hours=range(8, 17)):
    m = matched(T, d0, d1, hours); 
    if not m: return None
    a, b, e, w_ = (sum(x[i] for x in m) for i in (1, 2, 3, 4))
    r = dict(sensor=label, start=d0, end=d1, hours=f'{hours.start}-{hours.stop - 1}', matched_hours=len(m), days=len({x[0].date() for x in m}), telraam_ab=a, telraam_ba=b, telraam=a + b, ken_eb=e, ken_wb=w_, ken=e + w_, ratio=round((a + b) / (e + w_), 3) if e + w_ else None)
    ratios.append(r); return r
months = [(dt.date(2025, m, 1), dt.date(2025, m, 28 if m == 2 else 30 if m in (4, 6, 9, 11) else 31)) for m in range(8, 13)] + [(dt.date(2026, m, 1), dt.date(2026, m, 28 if m == 2 else 30 if m in (4, 6, 9, 11) else 31)) for m in range(1, 5)]
for lab, T in (('King Edward', KE), ('Draper', DR)):
    for a, b in months: ratio_row(lab, T, a, b)
    ratio_row(lab, T, dt.date(2025, 9, 1), dt.date(2025, 10, 31)); ratio_row(lab, T, CORE[0], min(CORE[1], DRAPER_END) if lab == 'Draper' else CORE[1])
# by hour of day, autumn vs winter core
hour_ratio = {}
for lab, T in (('King Edward', KE), ('Draper', DR)):
    for per, (a, b) in (('autumn', (dt.date(2025, 9, 1), dt.date(2025, 10, 31))), ('winter', (CORE[0], min(CORE[1], DRAPER_END) if lab == 'Draper' else CORE[1]))):
        m = matched(T, a, b, range(6, 20)); acc = collections.defaultdict(lambda: [0, 0, 0])
        for t, ab, ba, e, w_ in m: acc[t.hour][0] += ab + ba; acc[t.hour][1] += e + w_; acc[t.hour][2] += 1
        hour_ratio[(lab, per)] = {h: (v[0], v[1], v[2]) for h, v in sorted(acc.items())}
# direction mapping: correlation of hourly A>B with Kensington EB / WB (Sept–Oct 2025, uptime >= 0.7)
dirmap = {}
for lab, T in (('King Edward', KE), ('Draper', DR)):
    m = matched(T, dt.date(2025, 9, 1), dt.date(2025, 10, 31), range(6, 20)); ab = np.array([x[1] for x in m], float); ba = np.array([x[2] for x in m], float); e = np.array([x[3] for x in m], float); w_ = np.array([x[4] for x in m], float)
    dirmap[lab] = dict(n=len(m), r_ab_eb=round(float(np.corrcoef(ab, e)[0, 1]), 3), r_ab_wb=round(float(np.corrcoef(ab, w_)[0, 1]), 3), r_ba_eb=round(float(np.corrcoef(ba, e)[0, 1]), 3), r_ba_wb=round(float(np.corrcoef(ba, w_)[0, 1]), 3), ab_share=round(float(ab.sum() / (ab.sum() + ba.sum())), 3), ken_eb_share=round(float(e.sum() / (e.sum() + w_.sum())), 3))
    dirmap[lab]['ab_is'] = 'EB' if dirmap[lab]['r_ab_eb'] - dirmap[lab]['r_ab_wb'] > dirmap[lab]['r_ba_eb'] - dirmap[lab]['r_ba_wb'] else 'WB'
S['direction_mapping'] = dirmap
# Girouard WB vs Kensington WB, daily, common days (Kensington WB sound to Feb 28)
gir = []
for a, b in [(dt.date(2025, 11, 1), dt.date(2025, 11, 30)), (dt.date(2025, 12, 1), dt.date(2025, 12, 31)), (dt.date(2026, 1, 1), dt.date(2026, 1, 31)), (dt.date(2026, 2, 1), dt.date(2026, 2, 28))]:
    rs = sel(a, b, lambda r: r['gir_wb'] is not None and r['ken_wb'] is not None and r['gir_hours'] >= 20)
    if rs: gir.append(dict(month=a.strftime('%Y-%m'), days=len(rs), girouard_wb=int(sum(r['gir_wb'] for r in rs)), ken_wb=int(sum(r['ken_wb'] for r in rs)), ratio=round(sum(r['gir_wb'] for r in rs) / sum(r['ken_wb'] for r in rs), 3)))
S['girouard_vs_kensington_wb'] = gir
# Girouard hourly profile vs Kensington WB, winter core weekdays
gp = collections.defaultdict(lambda: [0.0, 0.0, 0]); 
for r in sel(CORE[0], CORE[1], lambda r: r['gir_hours'] >= 20 and r['ken_hours'] == 24 and not r['weekend']):
    for h in range(24):
        t = dt.datetime.combine(r['date'], dt.time(h)); gp[h][0] += GH.get(t, 0); gp[h][1] += KH[t][1]; gp[h][2] += 1
S['girouard_profile_days'] = gp[8][2] if gp else 0
# snapshots: Sept 19, 2024 and Jan 29, 2025 (Miovision at Grand and Cavendish; Telraam at King Edward and Draper)
def tel_day(T, d, hours):
    xs = [T.get(dt.datetime.combine(d, dt.time(h))) for h in hours]; 
    return dict(ab=sum(x[0] for x in xs if x), ba=sum(x[1] for x in xs if x), hours=sum(1 for x in xs if x), uptime=round(sum(x[2] for x in xs if x), 2))
SNAP = {'2024-09-19': dict(grand_axis_6h=452, grand_all_6h=707, grand_axis_12h=667, grand_all_12h=1047, cav_axis_6h=319, cav_all_6h=354, cav_axis_12h=503, cav_all_12h=566, src='2026-581 bundle 01 pp. 127 and 106 (miovision_counts_by_mode_2026-581.csv)'),
        '2025-01-29': dict(grand_axis_6h=8, grand_all_6h=12, grand_axis_12h=12, grand_all_12h=None, grand_eb_6h=8, grand_wb_6h=0, cav_axis_6h=10, cav_all_6h=12, cav_axis_12h=18, cav_all_12h=20, cav_eb_6h=5, cav_wb_6h=5, src='2026-581 bundle 01 pp. 85 and 155; 2026-634 workbooks B2 (by approach)')}
for ds in SNAP:
    d = dt.date.fromisoformat(ds)
    for key, T in (('king_edward', KE), ('draper', DR)):
        SNAP[ds][key + '_peak6h'] = tel_day(T, d, [7, 8, 9, 16, 17, 18]); SNAP[ds][key + '_12h'] = tel_day(T, d, range(7, 19)); SNAP[ds][key + '_day'] = tel_day(T, d, range(24))
    SNAP[ds]['weather'] = WX.get(d)
S['snapshots'] = SNAP
with open(os.path.join(HERE, 'cross_sensor_ratios.csv'), 'w', newline='') as f: w = csv.DictWriter(f, fieldnames=list(ratios[0].keys())); w.writeheader(); w.writerows(ratios)
S['ratios'] = ratios
# figure: ratio by month and by hour
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6))
for lab, key in (('King Edward', 'ke'), ('Draper', 'dr')):
    rs = [r for r in ratios if r['sensor'] == lab and (r['end'] - r['start']).days < 32 and r['ratio'] and r['days'] >= 10]
    ax[0].plot([r['start'] + dt.timedelta(14) for r in rs], [r['ratio'] for r in rs], 'o-', color=C[key], lw=1.5, ms=4, label=f'{lab} (Telraam) / Kensington loop')
if gir: ax[0].plot([dt.date.fromisoformat(g['month'] + '-15') for g in gir], [g['ratio'] for g in gir], 's--', color=C['gir'], lw=1.5, ms=4, label='Girouard WB (City) / Kensington WB')
ax[0].axhline(1, color=C['ink2'], lw=0.6); ax[0].set_ylabel('ratio of passages, same hours and days'); ax[0].set_title('By month (Telraam: 8–16 h, uptime ≥ 0.7)', loc='left', fontsize=9); ax[0].legend(fontsize=6.5, loc='upper left')
for (lab, per), hr in hour_ratio.items():
    hs = [h for h in hr if hr[h][1] >= 30]; ax[1].plot(hs, [hr[h][0] / hr[h][1] for h in hs], ('-' if per == 'winter' else ':'), color=C['ke' if lab == 'King Edward' else 'dr'], lw=1.5, label=f'{lab}, {per}')
ax[1].axhline(1, color=C['ink2'], lw=0.6); ax[1].set_xlabel('hour of day'); ax[1].set_title('By hour of day (autumn = Sept–Oct 2025; winter = Dec 2025–Feb 2026)', loc='left', fontsize=9); ax[1].legend(fontsize=6.5)
foot(fig); fig.tight_layout(rect=(0, 0.03, 1, 1)); fig.savefig(os.path.join(FIG, 'cross_sensor_ratios_en.png')); plt.close(fig)
# figure: snapshot days
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.4))
for i, ds in enumerate(('2024-09-19', '2025-01-29')):
    s = SNAP[ds]; pts = ['King Edward\n(Telraam, 12 h)', 'Cavendish\n(Miovision, 12 h, axis)', 'Grand\n(Miovision, 12 h, axis)', 'Draper\n(Telraam, 12 h)']
    vals = [s['king_edward_12h']['ab'] + s['king_edward_12h']['ba'], s['cav_axis_12h'], s['grand_axis_12h'], (s['draper_12h']['ab'] + s['draper_12h']['ba']) if s['draper_12h']['hours'] else None]
    cols = [C['ke'], C['ink2'], C['ink2'], C['dr']]
    for j, v in enumerate(vals):
        if v is None: ax[i].text(j, 1, 'not yet\ninstalled', ha='center', fontsize=7, color=C['ink2']); continue
        ax[i].bar(j, v, color=cols[j], width=0.6); ax[i].text(j, v, f'{v:.0f}', ha='center', va='bottom', fontsize=8, color=C['ink'])
    ax[i].set_xticks(range(4)); ax[i].set_xticklabels(pts, fontsize=7); ax[i].set_title(f'{ds}: bicycles over 12 hours, west to east', loc='left', fontsize=9); ax[i].set_ylabel('passages, 7–19 h')
foot(fig, SRC + ' Miovision: one-day camera counts (request 2026-581, pp. 85, 106, 127, 155; by approach: request 2026-634). Telraam hours with uptime shown in summary.json.'); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'snapshot_days_en.png')); plt.close(fig)

# ---------------------------------------------------------------- 4. Kensington winter structure
core = sel(CORE[0], CORE[1], lambda r: r['ken_hours'] == 24); w2 = sel(W2[0], W2[1], lambda r: r['ken_tot'] is not None)
with open(os.path.join(HERE, 'kensington_winter_days.csv'), 'w', newline='') as f:
    keys = ['date', 'dow', 'weekend', 'holiday', 'harsh', 'snow', 'tmean', 'tmin', 'sog', 'daylight_h', 'ken_eb', 'ken_wb', 'ken_tot', 'ken_dark', 'pairs', 'ke_tot', 'ke_valid', 'dr_tot', 'dr_valid', 'gir_wb']
    w = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore'); w.writeheader(); w.writerows(w2)
prof = {k: np.zeros(24) for k in ('wd_eb', 'wd_wb', 'we_eb', 'we_wb')}; nwd = nwe = 0
for r in core:
    k = 'we' if r['weekend'] else 'wd'; (nwe if r['weekend'] else nwd)
    for h in range(24): x = KH[dt.datetime.combine(r['date'], dt.time(h))]; prof[k + '_eb'][h] += x[0]; prof[k + '_wb'][h] += x[1]
    if r['weekend']: nwe += 1
    else: nwd += 1
for k in prof: prof[k] /= (nwe if k.startswith('we') else nwd)
S['profile_days'] = dict(weekdays=nwd, weekend=nwe); S['profile'] = {k: [round(float(x), 2) for x in v] for k, v in prof.items()}
wd = [r for r in core if not r['weekend']]; we = [r for r in core if r['weekend']]
q = lambda xs, p: float(np.percentile(xs, p))
tot_wd = [r['ken_tot'] for r in wd]; tot_we = [r['ken_tot'] for r in we]
S['core'] = dict(start=str(CORE[0]), end=str(CORE[1]), days=len(core), passages=int(sum(r['ken_tot'] for r in core)), eb=int(sum(r['ken_eb'] for r in core)), wb=int(sum(r['ken_wb'] for r in core)),
                 weekday=dict(n=len(wd), mean=round(np.mean(tot_wd), 1), median=q(tot_wd, 50), p10=q(tot_wd, 10), p25=q(tot_wd, 25), p75=q(tot_wd, 75), p90=q(tot_wd, 90), min=min(tot_wd), max=max(tot_wd)),
                 weekend=dict(n=len(we), mean=round(np.mean(tot_we), 1), median=q(tot_we, 50), min=min(tot_we), max=max(tot_we)),
                 pairs=dict(mean=round(np.mean([r['pairs'] for r in wd]), 2), median=float(np.median([r['pairs'] for r in wd])), p10=q([r['pairs'] for r in wd], 10), p90=q([r['pairs'] for r in wd], 90), share_of_weekday_passages=round(2 * sum(r['pairs'] for r in wd) / sum(tot_wd), 3)),
                 dark_share=round(sum(r['ken_dark'] for r in core) / sum(r['ken_tot'] for r in core), 3),
                 weekday_by_weather={k: dict(n=len(v), mean=round(np.mean(v), 1), min=min(v)) for k, v in (('mild', [r['ken_tot'] for r in wd if not r['harsh'] and not r['holiday']]), ('harsh', [r['ken_tot'] for r in wd if r['harsh'] and not r['holiday']]), ('holiday', [r['ken_tot'] for r in wd if r['holiday']])) if v},
                 weekend_by_weather={k: dict(n=len(v), mean=round(np.mean(v), 1)) for k, v in (('mild', [r['ken_tot'] for r in we if not r['harsh']]), ('harsh', [r['ken_tot'] for r in we if r['harsh']])) if v})
S['w2'] = dict(days=len(w2), passages=int(sum(r['ken_tot'] for r in w2)), eb=int(sum(r['ken_eb'] for r in w2 if r['ken_eb'] is not None)), wb=int(sum(r['ken_wb'] for r in w2 if r['ken_wb'] is not None)), max_day=max(r['ken_tot'] for r in w2), max_day_date=str(max(w2, key=lambda r: r['ken_tot'])['date']), min_day=min(r['ken_tot'] for r in w2), days_ge_40=sum(1 for r in w2 if r['ken_tot'] >= 40))
# negative-binomial regression of daily totals on calendar and weather (core, 24-h days)
def nb_loglik(y, mu, r_):
    return float(np.sum(special.gammaln(y + r_) - special.gammaln(r_) - special.gammaln(y + 1) + r_ * np.log(r_ / (r_ + mu)) + y * np.log(mu / (r_ + mu))))
Xcols = ['intercept', 'weekend', 'holiday', 'snow_cm', 'tmean_c', 'snow_on_ground_cm', 'daylight_h', 'days_since_dec1']
Xm = np.array([[1, r['weekend'], r['holiday'], r['snow'] or 0, r['tmean'] if r['tmean'] is not None else -5, r['sog'] or 0, r['daylight_h'], (r['date'] - CORE[0]).days] for r in core], float); y = np.array([r['ken_tot'] for r in core], float)
mu_x, sd_x = Xm[:, 1:].mean(0), Xm[:, 1:].std(0); Xs = Xm.copy(); Xs[:, 1:] = (Xm[:, 1:] - mu_x) / sd_x
def negll(th): b, lr = th[:-1], th[-1]; mu = np.exp(Xs @ b); return -nb_loglik(y, mu, np.exp(lr))
th0 = np.zeros(Xs.shape[1] + 1); th0[0] = np.log(y.mean()); th0[-1] = 1.0
res = optimize.minimize(negll, th0, method='BFGS'); H = res.hess_inv; se = np.sqrt(np.diag(H))
reg = []
for i, c in enumerate(Xcols):
    b = res.x[i]; s_ = se[i]
    if i == 0: reg.append(dict(term=c, coef=round(float(b), 3), se=round(float(s_), 3), effect='mean on an average day: %.1f passages' % math.exp(b)))
    else: reg.append(dict(term=c, coef=round(float(b / sd_x[i - 1]), 4), se=round(float(s_ / sd_x[i - 1]), 4), effect=('%+.0f %% per unit' if c not in ('weekend', 'holiday') else '%+.0f %%') % (100 * (math.exp(b / sd_x[i - 1]) - 1))))
S['nb_regression'] = dict(n=len(y), terms=reg, dispersion_r=round(float(math.exp(res.x[-1])), 2), loglik=round(-res.fun, 1), note='Negative-binomial (NB2) regression of daily passages at Kensington, Dec 1, 2025 to Feb 28, 2026, on calendar and ECCC weather; coefficients per unit of the raw variable; standard errors from the BFGS inverse Hessian (approximate).')
# residual autocorrelation (weekdays)
mu_hat = np.exp(Xs @ res.x[:-1]); resid = (y - mu_hat) / np.sqrt(mu_hat + mu_hat ** 2 / math.exp(res.x[-1])); wdmask = np.array([not r['weekend'] for r in core])
rw = resid[wdmask]; S['nb_regression']['lag1_autocorr_weekday_residuals'] = round(float(np.corrcoef(rw[:-1], rw[1:])[0, 1]), 3)
# figures: profiles; weather scatter; pairs series
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.4), sharey=True)
for i, k in enumerate(('wd', 'we')):
    ax[i].bar(np.arange(24) - 0.2, prof[k + '_eb'], width=0.4, color=C['eb'], label='eastbound'); ax[i].bar(np.arange(24) + 0.2, prof[k + '_wb'], width=0.4, color=C['wb'], label='westbound')
    ax[i].set_title(('Weekdays' if k == 'wd' else 'Weekend days') + f' (n = {nwd if k == "wd" else nwe}), Dec 1, 2025 to Feb 28, 2026', loc='left', fontsize=9); ax[i].set_xlabel('hour'); ax[i].set_xticks(range(0, 24, 3))
    rise, set_ = sun(dt.date(2026, 1, 15)); ax[i].axvspan(-0.5, rise, color='#f0efec', zorder=0); ax[i].axvspan(set_, 23.5, color='#f0efec', zorder=0)
ax[0].set_ylabel('passages per hour, mean per day'); ax[0].legend(fontsize=7)
foot(fig, SRC + ' Shaded: before sunrise / after sunset on January 15.'); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'kensington_hourly_profile_en.png')); plt.close(fig)
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6))
for r in core:
    ax[0].scatter(r['tmean'], r['ken_tot'], s=14 if (r['snow'] or 0) < 2.5 else 34, marker='o' if not r['weekend'] else 's', facecolor=(C['ken'] if not r['weekend'] else C['wb']) if (r['snow'] or 0) < 2.5 else 'none', edgecolor=C['ken'] if not r['weekend'] else C['wb'], lw=1)
ax[0].set_xlabel('mean temperature (°C), ECCC Trudeau'); ax[0].set_ylabel('passages per day'); ax[0].set_title('Daily passages against temperature; hollow = snow ≥ 2.5 cm; squares = weekend', loc='left', fontsize=8.5)
xs = [r['date'] for r in wd]; ax[1].plot(xs, [r['pairs'] for r in wd], color=C['ken'], lw=1.2, label='matched AM/PM round trips (pairs) per weekday'); ax[1].plot(xs, [r['ken_tot'] - 2 * r['pairs'] for r in wd], color=C['ke'], lw=1.0, label='passages not in a matched pair'); ax[1].legend(fontsize=7); ax[1].set_ylabel('per weekday'); ax[1].set_title('Weekdays: matched round trips and the rest', loc='left', fontsize=9)
foot(fig); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'kensington_weather_pairs_en.png')); plt.close(fig)

# ---------------------------------------------------------------- 5. model-free bounds on distinct users
def maxday(rs, key): 
    r = max(rs, key=lambda r: r[key] or 0); return r[key], str(r['date'])
bounds = {}
for name, key, rs in (('kensington', 'ken_tot', w2), ('king_edward', 'ke_tot', sel(W2[0], W2[1], lambda r: r['ke_valid'])), ('draper', 'dr_tot', sel(W2[0], W2[1], lambda r: r['dr_valid'])), ('girouard_wb', 'gir_wb', sel(W2[0], W2[1], lambda r: r['gir_wb'] is not None))):
    v, d = maxday(rs, key); bounds[name] = dict(max_day=v, date=d, people_ge_m2=math.ceil(v / 2), people_ge_m4=math.ceil(v / 4))
for name, key, rs in (('kensington_core', 'ken_tot', core),): v, d = maxday(rs, key); bounds[name] = dict(max_day=v, date=d, people_ge_m2=math.ceil(v / 2), people_ge_m4=math.ceil(v / 4))
S['bounds'] = bounds

# ---------------------------------------------------------------- 6. frequency-band model (Kensington, core period)
TEMPLATES = {
 'base': dict(desc='daily: 80 % of mild weekdays, 65 % harsh, 40 % holiday weekdays, 5 % weekend days, 2 passages per riding day, 80 % as matched pairs; regular: 35 % / 16 % / 20 % / 15 %, 2 passages, 60 % paired; occasional: 10 % mild / 3 % harsh (weekday and weekend alike), 1.5 passages, 30 % paired',
              daily=dict(wd=.80, wd_h=.65, hol=.40, we=.05, we_h=.03, c=2.0, pair=.8), regular=dict(wd=.35, wd_h=.16, hol=.20, we=.15, we_h=.06, c=2.0, pair=.6), occas=dict(wd=.10, wd_h=.03, hol=.08, we=.12, we_h=.03, c=1.5, pair=.3)),
 'one_way': dict(desc='as base, but fewer passages per riding day (daily 1.8, regular 1.6, occasional 1.2: more one-way trips through the point)',
              daily=dict(wd=.80, wd_h=.65, hol=.40, we=.05, we_h=.03, c=1.8, pair=.7), regular=dict(wd=.35, wd_h=.16, hol=.20, we=.15, we_h=.06, c=1.6, pair=.5), occas=dict(wd=.10, wd_h=.03, hol=.08, we=.12, we_h=.03, c=1.2, pair=.25)),
 'weather_sensitive': dict(desc='as base, but the regular and occasional bands drop more on harsh days (regular 10 %, occasional 1.5 %) and the daily band less (70 %)',
              daily=dict(wd=.80, wd_h=.70, hol=.40, we=.05, we_h=.03, c=2.0, pair=.8), regular=dict(wd=.35, wd_h=.10, hol=.20, we=.15, we_h=.04, c=2.0, pair=.6), occas=dict(wd=.10, wd_h=.015, hol=.08, we=.12, we_h=.015, c=1.5, pair=.3)),
 'survey_literal': dict(desc='riding days taken from the survey categories at face value: most weekdays = 90 % of weekdays; one to three days a week = 2 of 5 weekdays; a few times a month = 2.5 days a month spread over all days; weather and holiday factors as base',
              daily=dict(wd=.90, wd_h=.75, hol=.45, we=.05, we_h=.03, c=2.0, pair=.8), regular=dict(wd=.40, wd_h=.18, hol=.24, we=.10, we_h=.04, c=2.0, pair=.6), occas=dict(wd=.082, wd_h=.025, hol=.07, we=.082, we_h=.025, c=1.5, pair=.3)),
}
def q_of(tpl, r):
    if r['weekend']: return tpl['we_h'] if r['harsh'] else tpl['we']
    if r['holiday']: return tpl['hol']
    return tpl['wd_h'] if r['harsh'] else tpl['wd']
Y = np.array([r['ken_tot'] for r in core], float); P = np.array([r['pairs'] for r in core if not r['weekend']], float)
def fit_bands(T):
    Q = np.array([[q_of(T[b], r) * T[b]['c'] for b in ('daily', 'regular', 'occas')] for r in core]); Qp = np.array([[q_of(T[b], r) * T[b]['pair'] for b in ('daily', 'regular', 'occas')] for r in core if not r['weekend']])
    def nll(th, fixed=None):
        N = np.exp(th[:3]).copy()
        if fixed is not None: N[fixed[0]] = fixed[1]
        mu = Q @ N + 1e-9; mp = Qp @ N + 1e-9
        return -(nb_loglik(Y, mu, np.exp(th[3])) + nb_loglik(P, mp, np.exp(th[4])))
    best = None
    for start in ([2.5, 2.5, 4.5, 1.5, 1.5], [1.5, 3.5, 3.5, 1.5, 1.5], [3.0, 1.0, 5.5, 1.5, 1.5]):
        r_ = optimize.minimize(nll, np.array(start), method='Nelder-Mead', options=dict(maxiter=4000, xatol=1e-4, fatol=1e-4))
        if best is None or r_.fun < best.fun: best = r_
    N = np.exp(best.x[:3]); ll = -best.fun
    # profile-likelihood 95 % intervals (Δ = 1.92) by grid on each N_b
    prof_ci = {}; curves = {}
    for i, b in enumerate(('daily', 'regular', 'occas')):
        grid = np.concatenate([[0.0], np.exp(np.linspace(math.log(0.5), math.log(600), 70))]); vals = []
        for g in grid:
            th = best.x.copy(); th[i] = math.log(max(g, 1e-6))
            def nll_f(th2): th3 = th.copy(); th3[[j for j in range(5) if j != i]] = th2; return nll(th3, fixed=(i, g))
            rr = optimize.minimize(nll_f, np.delete(best.x, i), method='Nelder-Mead', options=dict(maxiter=2000, xatol=1e-3, fatol=1e-3)); vals.append(-rr.fun)
        vals = np.array(vals); ok = grid[vals >= ll - 1.92]; prof_ci[b] = (float(ok.min()) if len(ok) else None, float(ok.max()) if len(ok) else None); curves[b] = (grid.tolist(), (vals - ll).tolist())
    mu = Q @ N; days = len(core)
    per_person = {b: float(sum(q_of(T[b], r) * T[b]['c'] for r in core)) for b in ('daily', 'regular', 'occas')}
    riding_days = {b: float(sum(q_of(T[b], r) for r in core)) for b in ('daily', 'regular', 'occas')}
    passages = {b: float(N[i] * per_person[b]) for i, b in enumerate(('daily', 'regular', 'occas'))}
    return dict(N={b: round(float(N[i]), 1) for i, b in enumerate(('daily', 'regular', 'occas'))}, ci=prof_ci, loglik=round(ll, 1), passages_by_band={b: round(v) for b, v in passages.items()}, share_by_band={b: round(v / sum(passages.values()), 3) for b, v in passages.items()},
                per_person_passages={b: round(v, 1) for b, v in per_person.items()}, riding_days_per_person={b: round(v, 1) for b, v in riding_days.items()}, fitted_total=round(float(mu.sum())), observed_total=int(Y.sum()), dispersion=dict(y=round(float(math.exp(best.x[3])), 2), pairs=round(float(math.exp(best.x[4])), 2)), curves=curves,
                fitted_by_type={k: round(float(np.mean(mu[[j for j, r in enumerate(core) if f(r)]])), 1) for k, f in (('weekday_mild', lambda r: not r['weekend'] and not r['harsh'] and not r['holiday']), ('weekday_harsh', lambda r: not r['weekend'] and r['harsh'] and not r['holiday']), ('weekend', lambda r: r['weekend']), ('holiday_weekday', lambda r: r['holiday'] and not r['weekend']))},
                observed_by_type={k: round(float(np.mean(Y[[j for j, r in enumerate(core) if f(r)]])), 1) for k, f in (('weekday_mild', lambda r: not r['weekend'] and not r['harsh'] and not r['holiday']), ('weekday_harsh', lambda r: not r['weekend'] and r['harsh'] and not r['holiday']), ('weekend', lambda r: r['weekend']), ('holiday_weekday', lambda r: r['holiday'] and not r['weekend']))})
BF = {}
for name, T in TEMPLATES.items():
    BF[name] = fit_bands(T); BF[name]['desc'] = T['desc']; print(name, BF[name]['N'], BF[name]['ci'], file=sys.stderr)
S['band_fit'] = {k: {kk: vv for kk, vv in v.items() if kk != 'curves'} for k, v in BF.items()}
with open(os.path.join(HERE, 'band_fit.csv'), 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['template', 'band', 'people', 'ci95_low', 'ci95_high', 'riding_days_per_person', 'passages_per_person', 'passages', 'share_of_passages'])
    for name, v in BF.items():
        for b in ('daily', 'regular', 'occas'): w.writerow([name, b, v['N'][b], v['ci'][b][0], v['ci'][b][1], v['riding_days_per_person'][b], v['per_person_passages'][b], v['passages_by_band'][b], v['share_by_band'][b]])
# the frequent core, whatever the split: daily + regular people and their passages (base), and a tail table: tail passages / per-person passages for a range of tail frequencies
tail = BF['base']['passages_by_band']['occas']; S['tail_table'] = [dict(rides_per_winter=k, passages_per_person=round(k * 1.5, 1), people=round(tail / (k * 1.5))) for k in (2, 3, 4, 6, 8, 12)]
# figure: fit and profile curves
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6))
b_ = BF['base']; types = ['weekday_mild', 'weekday_harsh', 'holiday_weekday', 'weekend']; xs_ = np.arange(len(types))
ax[0].bar(xs_ - 0.18, [b_['observed_by_type'][t] for t in types], width=0.36, color=C['ken'], label='observed, mean per day'); ax[0].bar(xs_ + 0.18, [b_['fitted_by_type'][t] for t in types], width=0.36, color='#9ec5f4', label='fitted (base templates)')
ax[0].set_xticks(xs_); ax[0].set_xticklabels(['weekday, mild', 'weekday, harsh', 'holiday weekday', 'weekend'], fontsize=8); ax[0].set_ylabel('passages per day'); ax[0].legend(fontsize=7); ax[0].set_title('Kensington, Dec 1, 2025 to Feb 28, 2026: observed and fitted', loc='left', fontsize=9)
for b, lab in (('daily', 'most weekdays'), ('regular', '1–3 days a week'), ('occas', 'a few times a month')):
    g, v = b_['curves'][b]; ax[1].plot(g, v, color=C[b], lw=1.5, label=lab)
ax[1].axhline(-1.92, color=C['ink2'], lw=0.6, ls='--'); ax[1].set_xscale('symlog', linthresh=10); ax[1].set_ylim(-8, 0.5); ax[1].set_xlim(0, 600); ax[1].set_xlabel('people in the band'); ax[1].set_ylabel('profile log-likelihood − maximum'); ax[1].legend(fontsize=7); ax[1].set_title('How well the counts pin down each band (95 % interval above the dashed line)', loc='left', fontsize=8.5)
foot(fig); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'band_fit_en.png')); plt.close(fig)

# year-over-year at the Telraam points on common calendar dates (valid days both years), W1 vs W2, daylight totals
yoy = {}
for key, lab in (('ke', 'King Edward'), ('dr', 'Draper')):
    pairs_ = []
    for r in sel(W2[0], W2[1]):
        d1 = r['date']; d0 = dt.date(d1.year - 1, d1.month, d1.day) if not (d1.month == 2 and d1.day == 29) else None
        if d0 and d0 in byd and byd[d0][key + '_valid'] and r[key + '_valid']: pairs_.append((byd[d0][key + '_tot'], r[key + '_tot']))
    if pairs_: yoy[lab] = dict(common_days=len(pairs_), w1=int(sum(p[0] for p in pairs_)), w2=int(sum(p[1] for p in pairs_)), ratio_w2_w1=round(sum(p[1] for p in pairs_) / max(1, sum(p[0] for p in pairs_)), 3))
S['year_over_year'] = yoy

# ---------------------------------------------------------------- 7. corridor scaling (bounds)
rk = {r['sensor']: r for r in ratios if (r['end'] - r['start']).days > 40 and r['start'] == CORE[0]}
ke_r = rk['King Edward']['ratio'] if 'King Edward' in rk else None; dr_r = rk['Draper']['ratio'] if 'Draper' in rk else None
gir_r = (sum(g['girouard_wb'] for g in gir if g['month'] >= '2025-12') / sum(g['ken_wb'] for g in gir if g['month'] >= '2025-12')) if gir else None
S['corridor'] = dict(king_edward_over_kensington=ke_r, draper_over_kensington=dr_r, girouard_wb_over_kensington_wb=round(gir_r, 3) if gir_r else None,
                     trips_crossing_any_point_lower=round(max(1.0, dr_r or 0, gir_r or 0), 2), trips_crossing_any_point_upper=round(1.0 + (ke_r or 0) + (dr_r or 0) + (gir_r or 0), 2),
                     note='ratios of passages at each point to Kensington on matched hours (Telraam) or days (Girouard WB), winter core; trips crossing at least one point lie between the largest point and the sum of the points, in units of the Kensington count')

# ---------------------------------------------------------------- 8. the survey in context
SURVEY = dict(responses=205, kept=161, winter_cyclists=87, weekly=36, less_than_weekly=51, child_winter=27, src='Terrebonne-open-sources/2026-11-02-apc-survey-filing (public figures of the Nov 2, 2026 filing)')
weeks = 121 / 7
sv = []
for lab, n, days_lo, days_c, days_hi in (('at least weekly (36)', 36, 1 * weeks, 2.5 * weeks, 5 * weeks), ('less than weekly (51)', 51, 4, 8, 12)):
    for cpd_lab, cpd in (('1', 1.0), ('1.5', 1.5), ('2', 2.0)):
        sv.append(dict(band=lab, people=n, riding_days_low=round(days_lo), riding_days_central=round(days_c), riding_days_high=round(days_hi), passages_per_riding_day=cpd, passages_low=round(n * days_lo * cpd), passages_central=round(n * days_c * cpd), passages_high=round(n * days_hi * cpd)))
with open(os.path.join(HERE, 'survey_context.csv'), 'w', newline='') as f: w = csv.DictWriter(f, fieldnames=list(sv[0].keys())); w.writeheader(); w.writerows(sv)
central = sum(x['passages_central'] for x in sv if x['passages_per_riding_day'] == 1.5); lo = sum(x['passages_low'] for x in sv if x['passages_per_riding_day'] == 1.0); hi = sum(x['passages_high'] for x in sv if x['passages_per_riding_day'] == 2.0)
S['survey'] = SURVEY; S['survey_implied'] = dict(passages_central=central, passages_low=lo, passages_high=hi, counted_w2=S['w2']['passages'], counted_core=S['core']['passages'], ratio_central=round(central / S['w2']['passages'], 2), ratio_low=round(lo / S['w2']['passages'], 2), ratio_high=round(hi / S['w2']['passages'], 2))
# coverage of the modelled bands by the survey (Kensington point; corridor bounds)
bb = BF['base']; freq_people = bb['N']['daily'] + bb['N']['regular']
S['survey_coverage'] = dict(weekly_survey=36, frequent_modelled_kensington=round(freq_people, 1), frequent_ci=(round((bb['ci']['daily'][0] or 0) + (bb['ci']['regular'][0] or 0)), round((bb['ci']['daily'][1] or 0) + (bb['ci']['regular'][1] or 0))), occasional_survey=51, occasional_modelled_kensington=bb['N']['occas'], occasional_ci=bb['ci']['occas'],
                            corridor_factor=(S['corridor']['trips_crossing_any_point_lower'], S['corridor']['trips_crossing_any_point_upper']))
# figure: survey-implied passages vs counted
fig, ax = plt.subplots(figsize=(7, 3.2))
labs = ['survey, low\n(1 passage/day, fewest days)', 'survey, central\n(1.5 passages/day)', 'survey, high\n(2 passages/day, most days)', 'counted at Kensington\nDec 1 – Mar 31 (lower bound)']
vals = [lo, central, hi, S['w2']['passages']]; cols = ['#9ec5f4', '#2a78d6', '#184f95', C['ke']]
ax.barh(range(4), vals, color=cols, height=0.6)
for i, v in enumerate(vals): ax.text(v + 60, i, f'{v:,}', va='center', fontsize=8, color=C['ink'])
ax.set_yticks(range(4)); ax.set_yticklabels(labs, fontsize=7.5); ax.invert_yaxis(); ax.set_xlabel('bicycle passages over the winter'); ax.set_title('Passages the 87 survey respondents would produce at one point, if every trip crossed it, against the count', loc='left', fontsize=8.5)
foot(fig, 'Sources: APC-NDG survey filing of Nov 2, 2026 (public figures: 87 winter cyclists, 36 at least weekly); borough loop counter at Kensington (request 2026-581). Riding-day assumptions in survey_context.csv.'); fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(FIG, 'survey_vs_count_en.png')); plt.close(fig)

S['generated'] = dt.datetime.now().strftime('%Y-%m-%d %H:%M'); S['templates'] = {k: v['desc'] for k, v in TEMPLATES.items()}
json.dump(S, open(os.path.join(HERE, 'summary.json'), 'w'), indent=1, default=str)
print('summary.json written', file=sys.stderr)
