#!/usr/bin/env python3
"""How many cars build up behind a cyclist in a winter shared lane on rue de Terrebonne at rush hour?

In the winter layout proposed on November 2, 2026 (file 1266880005), cyclists riding with traffic share a lane about 3.5 m wide
between two rows of parked cars (EXP 2023, Figure 6-6). A driver may pass only with the clearance of art. 341 of the Highway
Safety Code (1 m at 50 km/h or less), which that lane does not leave; on a vélorue the cyclist may also ride on the full width
of the lane (art. 496.8). Either way, a driver who catches up stays behind. This script estimates how many.

Inputs (sibling repository Terrebonne-access-requests, released under the Access Act):
  - request 2026-300: the Kensington loop counter, hourly, July 26, 2025 – May 11, 2026 (motor vehicles; bicycles by direction).
    East of Cavendish Terrebonne is one-way eastbound, so the motor count is the traffic of the lane cyclists would share.
  - request 2026-634, B2: Miovision count at Terrebonne/Grand, January 29, 2025 (eastbound approach by movement), for the share
    of cars that turn off at a cross street.
  - the street frame of 1954-underwriters-plans-terrebonne-garages (géobase): distances and intersections along the axis.
Model: cars catch up with a cyclist at  lambda = q (1/v_bike - 1/v_car)  per km the cyclist rides (q = flow, veh/h; speeds in
km/h, stops included). With no passing they queue; a queued car leaves when it turns off, with probability s at each
intersection. Expected queue after x km: (lambda/mu)(1 - exp(-mu x)), mu = s × intersections per km. A Monte Carlo of the same
process (Poisson catch-ups, Bernoulli turn-offs at the actual intersections Cavendish → Girouard) gives the spread.
Writes summary.json, hourly_flows_winter_weekdays.csv, scenarios.csv, sensitivity_1km.csv and figures/*_en.png.
Usage: ~/.venvs/omd/bin/python queue_analysis.py"""
import csv, datetime as dt, json, math, os, random, statistics, sys
import openpyxl
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
GH = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))            # ~/GitHub
AR = os.path.join(GH, 'Terrebonne-access-requests')
HOURLY = os.path.join(AR, '2026-300', 'raw', '26072025_11052026.xlsx')
MIO = os.path.join(AR, '2026-634', 'raw', 'attachments', 'B2- Grand - Terrebonne1274799_01-29-2025.xlsx')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), '1954-underwriters-plans-terrebonne-garages', 'derived'))
import frame as FR
S = {}

# ---------- 1. hourly flows, winter weekdays (Dec 1 – Mar 31), Kensington
ws = openpyxl.load_workbook(HOURLY, read_only=True)['eco-counter']
rows = []
for r in ws.iter_rows(min_row=4, values_only=True):
    t, bk, be, bo, mv = r[:5]
    if isinstance(t, dt.datetime) and mv is not None: rows.append((t, mv, be or 0, bo or 0))
# The first record (09:00) follows a period start of 08:58, so time stamps mark the END of each hour; hour h = t - 1 h.
def profile(shift):
    H = {h: [] for h in range(24)}; B = {h: [] for h in range(24)}
    for t, mv, be, bo in rows:
        u = t - dt.timedelta(hours=shift)
        if u.month in (12, 1, 2, 3) and u.weekday() < 5: H[u.hour].append(mv); B[u.hour].append(be)
    return H, B
H, B = profile(1)
days = len(H[8]); prof = []
for h in range(24):
    v = sorted(H[h]); prof.append(dict(hour=h, motor_mean=round(statistics.mean(v), 1), motor_p90=v[int(0.9 * (len(v) - 1))], bikes_eb_mean=round(statistics.mean(B[h]), 2), days=len(v)))
with open(os.path.join(HERE, 'hourly_flows_winter_weekdays.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(prof[0])); w.writeheader(); w.writerows(prof)
am = max((p for p in prof if 6 <= p['hour'] <= 9), key=lambda p: p['motor_mean']); pm = max((p for p in prof if 14 <= p['hour'] <= 18), key=lambda p: p['motor_mean'])
H0, _ = profile(0); am0 = max(statistics.mean(H0[h]) for h in range(6, 10))
S['flows'] = dict(source='request 2026-300, Kensington loop counter, hourly, winter weekdays Dec 1 – Mar 31 2025-26', weekdays=days,
                  am_peak=am, pm_peak=pm, am_peak_if_stamps_mark_start=round(am0, 1), daily_mean=round(sum(p['motor_mean'] for p in prof)))

# ---------- 2. turning off at Grand (Miovision, Jan 29, 2025)
rws = list(openpyxl.load_workbook(MIO, read_only=True)['Légers'].iter_rows(values_only=True))
h1, h2, h3 = rws[11], rws[12], rws[13]; app = dirn = None; cols = {}
for j in range(1, len(h3)):
    app = h1[j] or app; dirn = h2[j] or dirn
    if h3[j]: cols[(app, dirn, h3[j])] = j
data = [r for r in rws[14:] if isinstance(r[0], str) and ':' in r[0]]
def tot(mv, hours=None):
    j = cols[('Terrebonne', 'Direction Est', mv)]
    return sum(r[j] or 0 for r in data if hours is None or int(r[0].split(':')[0]) in hours)
g = {k: dict(through=tot('Tout droit', hk), right=tot('Tourner à droite', hk), left=tot('Tourner à gauche', hk)) for k, hk in (('07-09', (7, 8)), ('12h', None))}
for v in g.values(): v['turn_share'] = round((v['right'] + v['left']) / (v['right'] + v['left'] + v['through']), 3); v['cars'] = v['right'] + v['left'] + v['through']
S['grand'] = dict(source='request 2026-634, B2, Miovision Terrebonne/Grand, January 29, 2025, light vehicles, eastbound approach', **g,
                  am_flow_per_hour=round(g['07-09']['cars'] / 2, 1))

# ---------- 3. geometry Cavendish → Girouard
names = [n for _, _, n in FR.NODES]; ic = next(i for i, n in enumerate(names) if 'Cavendish' in n); ig = next(i for i, n in enumerate(names) if 'Girouard' in n)
xs = [round((FR.CUM[i] - FR.CUM[ic]) / 1000, 3) for i in range(ic + 1, ig + 1)]          # intersections after Cavendish, km
S['geometry'] = dict(cavendish_to_girouard_km=xs[-1], intersections=len(xs), per_km=round(len(xs) / xs[-1], 1), west_end_to_cavendish_km=round(FR.CUM[ic] / 1000, 2),
                     note='géobase frame of 1954-underwriters-plans-terrebonne-garages; counted at each cross street after Cavendish up to and including Girouard')

# ---------- 4. model
def expected(q, vb, vc, s, x, per_km):
    lam = q * (1 / vb - 1 / vc); mu = s * per_km
    return lam * x if mu == 0 else lam / mu * (1 - math.exp(-mu * x)), lam * x
SC = {'low':     dict(q=100, vb=18, vc=22, s=0.12, label='light traffic, fast cyclist, slow cars, many cars turn off'),
      'central': dict(q=round(am['motor_mean']), vb=15, vc=25, s=0.07, label='mean winter morning peak, 15 km/h cyclist, 25 km/h cars'),
      'high':    dict(q=am['motor_p90'], vb=12, vc=28, s=0.04, label='busy morning (90th percentile), slow cyclist on snow, few cars turn off')}
DIST = [0.5, 1.0, xs[-1]]
def simulate(p, x_end, n=20000, seed=7):
    rnd = random.Random(seed); lam = p['q'] * (1 / p['vb'] - 1 / p['vc']); ints = [x for x in xs if x <= x_end + 1e-9]
    out = []; tmean = []
    for _ in range(n):
        x = 0.0; qn = 0; area = 0.0; k = 0
        while True:
            dx = rnd.expovariate(lam) if lam > 0 else math.inf
            nxt = ints[k] if k < len(ints) else math.inf
            step = min(x + dx, nxt, x_end)
            area += qn * (step - x); x = step
            if x >= x_end - 1e-12: break
            if x == nxt:
                qn = sum(1 for _ in range(qn) if rnd.random() > p['s']); k += 1
            else:
                qn += 1
        out.append(qn); tmean.append(area / x_end)
    out.sort()
    return dict(mean=round(statistics.mean(out), 2), median=out[len(out) // 2], p10=out[int(0.1 * n)], p90=out[int(0.9 * n)],
                share_zero=round(sum(1 for v in out if v == 0) / n, 3), time_avg=round(statistics.mean(tmean), 2))
sc_rows = []
for k, p in SC.items():
    p['caught_per_km'] = round(p['q'] * (1 / p['vb'] - 1 / p['vc']), 2)
    p['by_distance'] = {}
    for x in DIST:
        e, c = expected(p['q'], p['vb'], p['vc'], p['s'], x, S['geometry']['per_km'])
        mc = simulate(p, x)
        p['by_distance'][f'{x:g}'] = dict(expected_queue=round(e, 1), caught=round(c, 1), **mc)
        sc_rows.append(dict(scenario=k, km=x, q=p['q'], v_bike=p['vb'], v_car=p['vc'], turn_off=p['s'], expected_queue=round(e, 2), caught=round(c, 2), **mc))
    p['max_delay_min_per_km'] = round((1 / p['vb'] - 1 / p['vc']) * 60, 2)
with open(os.path.join(HERE, 'scenarios.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(sc_rows[0])); w.writeheader(); w.writerows(sc_rows)
S['scenarios'] = SC
c = SC['central']; bikes = am['bikes_eb_mean']
S['drivers'] = dict(cyclists_eb_peak_hour=bikes, cars_caught_per_cyclist_1km=c['caught_per_km'], cars_caught_per_peak_hour=round(bikes * c['caught_per_km'], 1),
                    share_of_peak_hour_cars=round(bikes * c['caught_per_km'] / c['q'], 3), max_delay_min_1km=c['max_delay_min_per_km'])
# sensitivity at 1 km, central flow and turn-off
VB = [10, 12, 14, 16, 18, 20]; VC = [20, 22, 24, 26, 28, 30]; sens = []
for vb in VB:
    for vc in VC:
        e = expected(c['q'], vb, vc, c['s'], 1.0, S['geometry']['per_km'])[0] if vc > vb else 0.0
        sens.append(dict(v_bike=vb, v_car=vc, expected_queue_1km=round(e, 2)))
with open(os.path.join(HERE, 'sensitivity_1km.csv'), 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(sens[0])); w.writeheader(); w.writerows(sens)
S['sensitivity_1km'] = dict(min=min(r['expected_queue_1km'] for r in sens), max=max(r['expected_queue_1km'] for r in sens))
S['assumptions'] = dict(speeds='average speeds including stops; cars 22–28 km/h on a 30 km/h street with all-way stops and signals; cyclists 12–18 km/h in winter; not measured on Terrebonne',
                        turn_off='share of queued cars leaving at each cross street: 4–12 %, below the 17.5 % measured at Grand (a boulevard) between 07:00 and 09:00',
                        no_passing='drivers stay behind (no lawful 1 m pass in a 3.5 m lane between parked cars; on a vélorue the cyclist may take the lane); art. 496.3 would let a driver pass where judged safe, which would shorten the queue at the cost of closer passes')
json.dump(S, open(os.path.join(HERE, 'summary.json'), 'w'), indent=1, ensure_ascii=False)

# ---------- 5. figures (validated default palette, dataviz skill; fixed order)
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
C = {'low': '#86b6ef', 'central': '#2a78d6', 'high': '#184f95', 'bike': '#eb6834', 'ink': '#0b0b0b', 'ink2': '#52514e', 'grid': '#e6e5e1', 'surf': '#fcfcfb'}
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 9, 'axes.edgecolor': C['ink2'], 'axes.labelcolor': C['ink'], 'xtick.color': C['ink2'], 'ytick.color': C['ink2'],
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6,
                     'figure.facecolor': C['surf'], 'axes.facecolor': C['surf'], 'savefig.dpi': 200, 'legend.frameon': False})
def foot(fig, text): fig.text(0.01, 0.005, text, fontsize=6.5, color=C['ink2'], ha='left', va='bottom', wrap=True)
SRC = 'Sources: borough loop counter at Terrebonne/Kensington, hourly (request 2026-300); Miovision at Grand, Jan 29, 2025 (request 2026-634, B2); City géobase. Model and assumptions in the note.'
# (a) hourly flows: two panels, one axis each
fig, ax = plt.subplots(1, 2, figsize=(9, 3.2)); hrs = [p['hour'] for p in prof]
ax[0].bar(hrs, [p['motor_mean'] for p in prof], width=0.8, color=C['central'], label='mean'); ax[0].plot(hrs, [p['motor_p90'] for p in prof], color=C['high'], lw=2, marker='o', ms=3, label='busy day (90th percentile)')
ax[0].set_title('Motor vehicles per hour (eastbound, the shared lane\'s traffic)', fontsize=9, loc='left'); ax[0].set_xlabel('hour of day'); ax[0].legend(fontsize=7.5, loc='upper left')
ax[1].bar(hrs, [p['bikes_eb_mean'] for p in prof], width=0.8, color=C['bike']); ax[1].set_title('Bicycles per hour, eastbound (mean)', fontsize=9, loc='left'); ax[1].set_xlabel('hour of day')
for a in ax: a.set_xticks(range(0, 24, 3)); a.set_axisbelow(True)
foot(fig, SRC + f' Winter weekdays, Dec 1 – Mar 31, 2025-26 ({days} days).'); fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(os.path.join(FIG, 'hourly_flows_en.png')); plt.close(fig)
# (b) queue by distance
fig, ax = plt.subplots(figsize=(7.5, 3.8)); xx = [i / 100 for i in range(0, int(xs[-1] * 100) + 1)]
for k in ('low', 'central', 'high'):
    p = SC[k]; ax.plot(xx, [expected(p['q'], p['vb'], p['vc'], p['s'], x, S['geometry']['per_km'])[0] for x in xx], color=C[k], lw=2, label=f"{k}: {p['q']} veh/h, cyclist {p['vb']} km/h, cars {p['vc']} km/h, {round(100 * p['s'])} % turn off")
    for x in DIST:
        d = p['by_distance'][f'{x:g}']; off = {'low': -0.025, 'central': 0.0, 'high': 0.025}[k]
        ax.plot([x + off, x + off], [d['p10'], d['p90']], color=C[k], lw=1.2, alpha=0.7); ax.plot(x + off, d['mean'], 'o', ms=4.5, color=C[k], mec=C['surf'], mew=1.5)
ax.set_xlabel('distance ridden in the shared lane from Cavendish (km)'); ax.set_ylabel('cars queued behind the cyclist'); ax.set_xlim(0, xs[-1] + 0.05); ax.set_ylim(0, None)
ax.set_title('Cars queued behind one cyclist, winter morning peak', fontsize=9, loc='left'); ax.legend(fontsize=7, loc='upper left')
foot(fig, 'Lines: expected queue. Dots and bars: simulation mean and 10th–90th percentiles (20,000 runs). ' + SRC); fig.tight_layout(rect=(0, 0.06, 1, 1)); fig.savefig(os.path.join(FIG, 'queue_by_distance_en.png')); plt.close(fig)
# (c) sensitivity: one-hue sequential grid
import numpy as np
M = np.array([[next(r['expected_queue_1km'] for r in sens if r['v_bike'] == vb and r['v_car'] == vc) for vc in VC] for vb in VB])
fig, ax = plt.subplots(figsize=(5.6, 3.9)); from matplotlib.colors import LinearSegmentedColormap
cm = LinearSegmentedColormap.from_list('blue', ['#eef4fd', '#86b6ef', '#2a78d6', '#184f95'])
im = ax.imshow(M, cmap=cm, origin='lower', aspect='auto'); ax.grid(False)
ax.set_xticks(range(len(VC)), VC); ax.set_yticks(range(len(VB)), VB); ax.set_xlabel('average car speed, stops included (km/h)'); ax.set_ylabel('average cyclist speed (km/h)')
for i in range(len(VB)):
    for j in range(len(VC)): ax.text(j, i, f'{M[i, j]:.1f}', ha='center', va='center', fontsize=7.5, color=C['ink'] if M[i, j] < M.max() * 0.55 else 'white')
ax.set_title(f"Expected queue after 1 km, {c['q']} veh/h, {round(100 * c['s'])} % turn off per cross street", fontsize=8.5, loc='left')
fig.colorbar(im, ax=ax, shrink=0.8).set_label('cars')
foot(fig, 'Model: queue = (λ/μ)(1 − e^(−μx)), λ = flow × (1/v_bike − 1/v_car), μ = turn-off share × cross streets per km.'); fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(FIG, 'sensitivity_1km_en.png')); plt.close(fig)
print(json.dumps({k: (v if k != 'scenarios' else {kk: vv['by_distance'] for kk, vv in v.items()}) for k, v in S.items() if k in ('flows', 'grand', 'geometry', 'drivers', 'scenarios')}, ensure_ascii=False, indent=0)[:3000])
