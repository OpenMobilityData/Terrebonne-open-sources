#!/usr/bin/env python3
"""Parking supply and demand around rue de Terrebonne, and the APC-NDG survey's parking answers in context.
Reads in place: EXP 2023 tables (transcribed beside this script), the 1954-plans folder's summary and per-block car counts, the City assessment-roll
extract and géobase (Terrebonne-data), the survey's anonymized file (Terrebonne-data). Writes summary.json, CSVs and figures in derived/.
Usage: ~/.venvs/omd/bin/python parking_analysis.py"""
import os, sys, csv, json, math, collections, datetime as dt
import numpy as np
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
OS = os.path.abspath(os.path.join(HERE, '..', '..')); G54 = os.path.join(OS, '1954-underwriters-plans-terrebonne-garages', 'derived')
ROLL = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/unites-evaluation-fonciere/terrebonne_bbox_extract.geojson')
GEOBASE = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/geobase_2026-10-14.json')
SURVEY = os.path.expanduser('~/Terrebonne-data/survey-responses/anonymized_2026-11-07.csv'); SURVEY_ASOF = '2026-11-07'
sys.path.insert(0, G54); import frame as FR
C = {'exp': '#2a78d6', 'lidar': '#eb6834', 'optical': '#1baf7a', 'survey': '#6250d6', 'roll': '#eda100', 'ink': '#0b0b0b', 'ink2': '#52514e', 'grid': '#e6e5e1', 'surf': '#fcfcfb', 'b1': '#2a78d6', 'b2': '#86b6ef', 'b3': '#cde2fb'}
plt.rcParams.update({'font.family': 'sans-serif', 'font.size': 9, 'axes.edgecolor': C['ink2'], 'axes.labelcolor': C['ink'], 'xtick.color': C['ink2'], 'ytick.color': C['ink2'], 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6, 'axes.axisbelow': True, 'figure.facecolor': C['surf'], 'axes.facecolor': C['surf'], 'savefig.dpi': 200, 'legend.frameon': False})
def foot(fig, t): fig.text(0.01, 0.005, t, fontsize=6, color=C['ink2'], ha='left', va='bottom')
S = {}
PERIODS = ['Thu AM', 'Thu noon', 'Thu PM', 'Sat AM', 'Sat noon', 'Sat PM']; PLAB = {'Thu AM': 'Thu 7:30–8:30', 'Thu noon': 'Thu 12:30–13:30', 'Thu PM': 'Thu 18:30–19:30', 'Sat AM': 'Sat 8:00–9:00', 'Sat noon': 'Sat 12:30–13:30', 'Sat PM': 'Sat 18:30–19:30'}
SECTORS = ['residential west', 'institutional', 'residential east']; SLAB = {'residential west': 'west (St-Ignatius–Cavendish)', 'institutional': 'institutional (Cavendish–Grand)', 'residential east': 'east (Grand–Girouard)'}

# ---------------------------------------------------------------- 1. EXP 2022 parking survey (report of Sept 2023)
EXP = list(csv.DictReader(open(os.path.join(HERE, 'exp2023_parking_tables_transcribed.csv'), encoding='utf-8')))
for r in EXP: r['occ'] = float(r['occupancy_pct']) / 100; r['vac'] = float(r['vacant_places']); r['supply_est'] = r['vac'] / (1 - r['occ']) if r['occ'] < 1 else None
groups = collections.defaultdict(list)
for r in EXP: groups[(r['table'], r['sector'], r['side_or_direction'])].append(r)
sup = {k: float(np.median([r['supply_est'] for r in v])) for k, v in groups.items()}
STATED = {'terrebonne_wb': 230, 'terrebonne_eb': 248, 'terrebonne': 478, 'stubs_north': 328, 'stubs_south': 301, 'stubs': 629, 'page_supply': 40, 'table71': dict(current=475, standards=375, scenario1=161, scenario2=172, scenario3=171, page=88)}
ter_keys = [k for k in sup if k[0] == '3-2']; stub_keys = [k for k in sup if k[0] == '3-3']
S['exp'] = dict(stated=STATED, derived_supply={f'{k[1]} / {k[2]}': round(v) for k, v in sup.items()}, derived_total_terrebonne=round(sum(sup[k] for k in ter_keys)), derived_total_stubs=round(sum(sup[k] for k in stub_keys)),
                survey_days='Thursday, September 29, 2022 (7:30–8:30, 12:30–13:30, 18:30–19:30) and Saturday, October 1, 2022 (8:00–9:00, 12:30–13:30, 18:30–19:30); works between Walkley and Cumberland at the time (report p. 4)')
per = []
for p in PERIODS:
    row = dict(period=p, label=PLAB[p])
    for name, keys in (('terrebonne', ter_keys), ('stubs', stub_keys)):
        occ_cars = sum(groups[k][PERIODS.index(p)]['occ'] * sup[k] for k in keys); vac = sum(groups[k][PERIODS.index(p)]['vac'] for k in keys)
        row[name + '_occupied'] = round(occ_cars); row[name + '_vacant'] = round(vac); row[name + '_occupancy'] = round(occ_cars / (occ_cars + vac), 3)
    for s in SECTORS:
        kk = [k for k in ter_keys if k[1] == s]; oc = sum(groups[k][PERIODS.index(p)]['occ'] * sup[k] for k in kk); va = sum(groups[k][PERIODS.index(p)]['vac'] for k in kk)
        row[f'{s}_terrebonne_occupied'] = round(oc); row[f'{s}_terrebonne_vacant'] = round(va)
    per.append(row)
with open(os.path.join(HERE, 'exp2022_occupancy_by_period.csv'), 'w', newline='') as f: w = csv.DictWriter(f, fieldnames=list(per[0].keys())); w.writeheader(); w.writerows(per)
S['exp']['by_period'] = per; S['exp']['thu_pm'] = next(r for r in per if r['period'] == 'Thu PM'); S['exp']['max_occupancy_terrebonne'] = max(r['terrebonne_occupancy'] for r in per); S['exp']['min_vacant_terrebonne'] = min(r['terrebonne_vacant'] for r in per)
S['exp']['peak_cell'] = max(EXP, key=lambda r: r['occ']); S['exp']['peak_cell'] = {k: S['exp']['peak_cell'][k] for k in ('table', 'sector', 'side_or_direction', 'period', 'occupancy_pct', 'vacant_places')}
# figure 1: occupancy by sector and period, Terrebonne (two directions) and stubs (two sides)
fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.6), sharey=True)
x = np.arange(len(PERIODS)); cols = {'residential west': C['b1'], 'institutional': C['exp'], 'residential east': C['b1']}
mk = {'residential west': 'o', 'institutional': 's', 'residential east': '^'}; ls = {'direction west': '-', 'direction east': '--', 'cross streets north': '-', 'cross streets south': '--'}
pal = {'residential west': '#2a78d6', 'institutional': '#eb6834', 'residential east': '#1baf7a'}
for i, (tab, title) in enumerate((('3-2', 'On rue de Terrebonne, by sector and direction'), ('3-3', 'Cross-street stubs within 50 m, by sector and side'))):
    for k, v in groups.items():
        if k[0] != tab: continue
        ax[i].plot(x, [r['occ'] * 100 for r in v], ls[k[2]], marker=mk[k[1]], ms=4, lw=1.3, color=pal[k[1]], label=f'{SLAB[k[1]]}, {k[2]}')
    ax[i].axhline(80, color=C['ink2'], lw=0.6, ls=':'); ax[i].text(5.1, 81, 'EXP’s 80 % threshold', fontsize=6.5, color=C['ink2'], ha='right')
    ax[i].set_xticks(x); ax[i].set_xticklabels([PLAB[p] for p in PERIODS], fontsize=6.5, rotation=20); ax[i].set_title(title, loc='left', fontsize=9); ax[i].legend(fontsize=5.5, ncol=1, loc='lower left'); ax[i].set_ylim(0, 100)
ax[0].set_ylabel('occupancy (%)')
foot(fig, 'Source: EXP, Étude de mobilité sur la rue de Terrebonne, Sept. 2023, Tables 3-2 (report p. 43) and 3-3 (p. 48); survey of Sept 29 and Oct 1, 2022.'); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'exp_occupancy_en.png')); plt.close(fig)
# figure 2: occupied and vacant places per period
fig, ax = plt.subplots(figsize=(8, 3.4))
for j, (name, lab) in enumerate((('terrebonne', 'rue de Terrebonne (both sides)'), ('stubs', 'cross-street stubs within 50 m'))):
    occ = [r[name + '_occupied'] for r in per]; vac = [r[name + '_vacant'] for r in per]
    ax.bar(x + (j - 0.5) * 0.4, occ, 0.38, color=C['b1'] if j == 0 else C['exp'], alpha=1 if j == 0 else 0.55, label=f'{lab}: occupied'); ax.bar(x + (j - 0.5) * 0.4, vac, 0.38, bottom=occ, color=C['b3'], edgecolor=C['b1'] if j == 0 else C['exp'], lw=0.6, label=f'{lab}: vacant')
    for xi, (o, v_) in enumerate(zip(occ, vac)): ax.text(xi + (j - 0.5) * 0.4, o + v_ + 5, f'{o}', ha='center', fontsize=6.5, color=C['ink'])
ax.set_xticks(x); ax.set_xticklabels([PLAB[p] for p in PERIODS], fontsize=7); ax.set_ylabel('places'); ax.legend(fontsize=6.5, ncol=2); ax.set_title('Occupied (number on the bar) and vacant places, September–October 2022', loc='left', fontsize=9)
foot(fig, 'Source: EXP 2023, Tables 3-2 and 3-3; supply per sector and side derived from the vacant places and the occupancy rate (median over the six periods), totals 478 on Terrebonne and 629 on the stubs as stated p. 40.'); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'exp_occupied_vacant_en.png')); plt.close(fig)

# ---------------------------------------------------------------- 2. cars at the curbs, 2015 LiDAR night and daytime orthophoto, per block
BL = list(csv.DictReader(open(os.path.join(G54, 'on_street_cars_by_block.csv'), encoding='utf-8')))
for b in BL:
    for k in ('length_m', 'optical_N', 'optical_S', 'lidar_by_eye_N', 'lidar_by_eye_S', 'lidar_lots_N', 'lidar_lots_S', 'lidar_cross_street_within_block', 'optical_converted_side', 'lidar_by_eye_converted_side'): b[k] = float(b[k])
    b['nominal_per_side'] = b['length_m'] / 6.0; b['sector'] = 'residential west' if int(b['block']) <= 11 else 'institutional' if int(b['block']) <= 16 else 'residential east'
tot = lambda k: int(sum(b[k] for b in BL))
S['curbs'] = dict(blocks=len(BL), lidar_night_by_eye=tot('lidar_by_eye_N') + tot('lidar_by_eye_S'), lidar_N=tot('lidar_by_eye_N'), lidar_S=tot('lidar_by_eye_S'), lidar_converted_side=tot('lidar_by_eye_converted_side'),
                  optical_day=tot('optical_N') + tot('optical_S'), optical_N=tot('optical_N'), optical_S=tot('optical_S'), optical_converted_side=tot('optical_converted_side'), lots_lidar=tot('lidar_lots_N') + tot('lidar_lots_S'),
                  nominal_capacity_both_sides=round(2 * sum(b['nominal_per_side'] for b in BL)), length_m=round(sum(b['length_m'] for b in BL)))
bysec = {}
for s in SECTORS:
    bb = [b for b in BL if b['sector'] == s]; supp = sum(sup[k] for k in ter_keys if k[1] == s)
    bysec[s] = dict(blocks=len(bb), lidar_night=int(sum(b['lidar_by_eye_N'] + b['lidar_by_eye_S'] for b in bb)), optical_day=int(sum(b['optical_N'] + b['optical_S'] for b in bb)), exp_supply_derived=round(supp), exp_thu_pm_occupied=S['exp']['thu_pm'][f'{s}_terrebonne_occupied'],
                    lidar_night_over_exp_supply=round(sum(b['lidar_by_eye_N'] + b['lidar_by_eye_S'] for b in bb) / supp, 3))
S['curbs']['by_sector'] = bysec; S['curbs']['lidar_night_over_exp_supply'] = round(S['curbs']['lidar_night_by_eye'] / sum(sup[k] for k in ter_keys), 3)
S['curbs']['top_blocks_lidar'] = [dict(block=b['block_name'], cars=int(b['lidar_by_eye_N'] + b['lidar_by_eye_S']), nominal=round(2 * b['nominal_per_side'])) for b in sorted(BL, key=lambda b: -(b['lidar_by_eye_N'] + b['lidar_by_eye_S']))[:5]]
fig, ax = plt.subplots(figsize=(10, 3.8)); xb = np.arange(len(BL))
ax.bar(xb - 0.2, [b['lidar_by_eye_N'] + b['lidar_by_eye_S'] for b in BL], 0.38, color=C['lidar'], label='2015 LiDAR, weeknight (by eye), both curbs')
ax.bar(xb + 0.2, [b['optical_N'] + b['optical_S'] for b in BL], 0.38, color=C['optical'], label='orthophoto, daytime (undated, before the 2024 lane), both curbs')
ax.plot(xb, [2 * b['nominal_per_side'] for b in BL], color=C['ink2'], lw=0.8, ls='--', label='nominal capacity, both curbs (block length / 6 m)')
for i, b in enumerate(BL):
    if b['converted_side'] == 'N': ax.axvspan(i - 0.5, i + 0.5, ymin=0.97, ymax=1.0, color='#e34948', alpha=0.5)
    else: ax.axvspan(i - 0.5, i + 0.5, ymin=0.0, ymax=0.03, color='#e34948', alpha=0.5)
ax.set_xticks(xb); ax.set_xticklabels([b['block_name'] for b in BL], rotation=70, fontsize=6); ax.set_ylabel('cars at the curbs'); ax.legend(fontsize=7, loc='upper left'); ax.set_title('Cars parked on rue de Terrebonne by block, west to east, before the 2024 lane (red strip: the side converted to parking in winter)', loc='left', fontsize=8.5)
foot(fig, 'Sources: City LiDAR 2015 (CC-BY 4.0) and Québec orthophoto (Imagerie_GQ), readings by the author (1954-underwriters-plans-terrebonne-garages/derived/on_street_cars_by_block.csv). Two snapshots, not a before-and-after.'); fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(os.path.join(FIG, 'curb_cars_by_block_en.png')); plt.close(fig)

# ---------------------------------------------------------------- 3. the survey's parking answers (anonymized file; categories as in the filing's methods page)
def ticks(v): return [t.strip() for t in str(v or '').split(';') if t.strip()]
DIST = {'On rue de Terrebonne': 'corridor-on', 'Sur la rue de Terrebonne': 'corridor-on', 'Within one block of Terrebonne, between Somerled and Monkland': 'corridor-block', "À moins d'un pâté de maisons de Terrebonne, entre Somerled et Monkland": 'corridor-block'}
PARK = {'Own garage, driveway or carport': 'own-offstreet', "Garage, entrée ou abri d'auto du logement": 'own-offstreet', 'On rue de Terrebonne': 'terrebonne', 'Sur la rue de Terrebonne': 'terrebonne', 'On a cross street, within one block of home': 'cross-within-block', "Sur une rue transversale, à moins d'un pâté de maisons": 'cross-within-block',
        'On a cross street, more than one block from home': 'cross-farther', "Sur une rue transversale, à plus d'un pâté de maisons": 'cross-farther', 'On Somerled or Monkland': 'somerled-monkland', 'Sur Somerled ou Monkland': 'somerled-monkland', 'Rented space elsewhere': 'rented', 'Espace loué ailleurs': 'rented'}
STREET = {'terrebonne', 'cross-within-block', 'cross-farther', 'somerled-monkland'}
ST = {'10–20 min': '10-20', 'Over 20 minutes': 'gt20', 'Plus de 20 minutes': 'gt20', '10 à 20 min': '10-20', '10–20 min ': '10-20'}
WD = {'Two or more blocks away': '2plus-blocks', 'À deux pâtés de maisons ou plus': '2plus-blocks'}
SD = {'Parked more than two blocks away': '2plus-blocks', 'Garé à plus de deux pâtés de maisons': '2plus-blocks', 'Received a ticket or was towed': 'ticket-tow', 'Contravention ou remorquage': 'ticket-tow', 'Moved the car out of the neighbourhood': 'moved-out', 'Déplacé la voiture hors du quartier': 'moved-out', 'Took much longer to find a space': 'much-longer', 'Beaucoup plus long pour trouver une place': 'much-longer'}
def nveh(v): v = (v or '').strip(); return None if v == '' else 3 if v.startswith('3') else int(v)
def noff(v):
    v = (v or '').strip()
    if v == '': return None
    if v.startswith('Shared') or v.startswith('Espaces') or v.startswith('Stationnement'): return 'shared'
    if v.startswith('Does not apply') or v.startswith('Sans objet'): return 'na'
    return 3 if v.startswith('3') else int(v)
rows = list(csv.DictReader(open(SURVEY, encoding='utf-8')))
for d in rows:
    d['g'] = DIST.get(d['district'].strip(), 'other'); d['veh'] = nveh(d['vehicles']); d['offb'] = noff(d['offstreet_built']); d['offu'] = noff(d['offstreet_used'])
    d['park'] = {PARK.get(t, 'other') for t in ticks(d['parked_last_night'])}; d['street'] = bool(d['park'] & STREET)
    d['hard_typ'] = ST.get(d['search_time'].strip()) in ('10-20', 'gt20') or WD.get(d['walk_distance'].strip()) == '2plus-blocks'
    sd = {SD.get(t) for t in ticks(d['storm_days'])}; d['hard_storm'] = bool(sd & {'2plus-blocks', 'ticket-tow', 'moved-out'}); d['hard_strict'] = d['hard_typ'] or d['hard_storm']; d['hard_loose'] = d['hard_strict'] or ('much-longer' in sd)
def wilson(k, n, z=1.96):
    if not n: return (None, None)
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den; return (round(c - h, 3), round(c + h, 3))
def summarize(g, name):
    n = len(g); veh = collections.Counter(d['veh'] for d in g); withv = [d for d in g if d['veh']]
    offb = [d for d in withv if d['offb'] is not None]; offb_ge1 = sum(1 for d in offb if d['offb'] == 'shared' or (isinstance(d['offb'], int) and d['offb'] >= 1))
    offu = [d for d in withv if d['offu'] is not None]; offu_ge1 = sum(1 for d in offu if d['offu'] == 'shared' or (isinstance(d['offu'], int) and d['offu'] >= 1))
    park = collections.Counter(); 
    for d in withv:
        for t in (d['park'] or {'(blank)'}): park[t] += 1
    street = [d for d in g if d['street']]
    return dict(group=name, respondents=n, vehicles_0=veh[0], vehicles_1=veh[1], vehicles_2=veh[2], vehicles_3plus=veh[3], vehicles_blank=veh[None], with_vehicle=len(withv), vehicles_total=sum(min(d['veh'], 3) for d in withv),
                offstreet_built_answered=len(offb), offstreet_built_ge1=offb_ge1, offstreet_built_share=round(offb_ge1 / len(offb), 3) if offb else None, offstreet_built_ci=wilson(offb_ge1, len(offb)),
                offstreet_used_answered=len(offu), offstreet_used_ge1=offu_ge1, parked_own_offstreet=park['own-offstreet'], parked_terrebonne=park['terrebonne'], parked_cross_within_block=park['cross-within-block'], parked_cross_farther=park['cross-farther'], parked_somerled_monkland=park['somerled-monkland'], parked_rented=park['rented'], parked_other=park['other'],
                street_parkers=len(street), hardship_strict=sum(d['hard_strict'] for d in street), hardship_loose=sum(d['hard_loose'] for d in street), hardship_typical_evening=sum(d['hard_typ'] for d in street), hardship_storm=sum(d['hard_storm'] for d in street),
                street_parkers_no_offstreet=sum(1 for d in street if d['offb'] in (0, None)), street_parkers_more_vehicles_than_places=sum(1 for d in street if isinstance(d['offb'], int) and d['veh'] and d['veh'] > d['offb']))
SV = [summarize([d for d in rows if d['g'] == 'corridor-on'], 'on Terrebonne'), summarize([d for d in rows if d['g'] == 'corridor-block'], 'within one block'), summarize([d for d in rows if d['g'] in ('corridor-on', 'corridor-block')], 'corridor (both)'), summarize(rows, 'all respondents')]
with open(os.path.join(HERE, 'survey_parking_by_group.csv'), 'w', newline='') as f: w = csv.DictWriter(f, fieldnames=list(SV[0].keys())); w.writeheader(); w.writerows(SV)
S['survey'] = dict(asof=SURVEY_ASOF, responses=len(rows), groups={r['group']: r for r in SV}, public_filing='Nov 2, 2026 (205 responses): 108 on or within a block, 59 street parkers, 34 strict / 46 loose hardship; 18 of 34 respondents on Terrebonne with a vehicle report an off-street place')
print('survey check: corridor', SV[2]['respondents'], 'street parkers', SV[2]['street_parkers'], 'strict', SV[2]['hardship_strict'], 'loose', SV[2]['hardship_loose'], file=sys.stderr)

# ---------------------------------------------------------------- 4. off-street: the plans and imagery against the survey
G = json.load(open(os.path.join(G54, 'summary.json'))); PD = G['present_day']; RL = G['roll']
S['offstreet'] = dict(buildings_checked=PD['checked'], buildings_either=PD['garage_1954_or_driveway_today'], pct_buildings=PD['pct_either'], dwellings_checked=PD['dwellings_checked'], dwellings_either=PD['dwellings_either'], pct_dwellings=PD['pct_dwellings_either'],
                      by_side=PD['by_side'], garage_1954=G['with_garage'], buildings_1954=G['buildings_terrebonne'], pct_1954=G['pct'], dwellings_1954=RL['dwellings_in_buildings_with_garage'], dwellings_roll=RL['dwellings'],
                      buildings_ci=wilson(PD['garage_1954_or_driveway_today'], PD['checked']), dwellings_ci=wilson(PD['dwellings_either'], PD['dwellings_checked']))
fig, ax = plt.subplots(figsize=(8, 3.2))
items = [('Plans + imagery: buildings on Terrebonne with a garage or driveway today', PD['garage_1954_or_driveway_today'], PD['checked'], C['lidar']), ('Plans + imagery: dwellings in those buildings', PD['dwellings_either'], PD['dwellings_checked'], C['lidar']),
         ('Survey: on Terrebonne, households with a vehicle, at least one off-street place', SV[0]['offstreet_built_ge1'], SV[0]['offstreet_built_answered'], C['survey']), ('Survey: within one block, same', SV[1]['offstreet_built_ge1'], SV[1]['offstreet_built_answered'], C['survey']), ('Survey: corridor (both), same', SV[2]['offstreet_built_ge1'], SV[2]['offstreet_built_answered'], C['survey'])]
for i, (lab, k, n, col) in enumerate(items):
    lo, hi = wilson(k, n); ax.plot([100 * lo, 100 * hi], [i, i], color=col, lw=2); ax.plot(100 * k / n, i, 'o', color=col, ms=6); ax.text(100 * hi + 1.5, i, f'{k} of {n} ({100 * k / n:.0f} %)', va='center', fontsize=7.5, color=C['ink'])
ax.set_yticks(range(len(items))); ax.set_yticklabels([it[0] for it in items], fontsize=7); ax.invert_yaxis(); ax.set_xlim(0, 100); ax.set_xlabel('share with off-street parking (%), 95 % Wilson interval'); ax.set_title('Off-street parking: the external reading against the survey’s answers', loc='left', fontsize=9)
foot(fig, f'Sources: 1954-underwriters-plans-terrebonne-garages (BAnQ plans; City LiDAR 2015; Québec orthophoto; City roll); APC-NDG survey, anonymized file as of {SURVEY_ASOF}.'); fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(FIG, 'offstreet_share_en.png')); plt.close(fig)
# figure: where corridor respondents parked last night, by group
fig, ax = plt.subplots(figsize=(8, 3.2)); cats = [('parked_own_offstreet', 'own garage, driveway or carport'), ('parked_terrebonne', 'on rue de Terrebonne'), ('parked_cross_within_block', 'cross street, within a block'), ('parked_cross_farther', 'cross street, farther'), ('parked_somerled_monkland', 'Somerled or Monkland'), ('parked_rented', 'rented space'), ('parked_other', 'other / free text')]
yy = np.arange(len(cats))
for j, (g, col) in enumerate(((SV[0], C['b1']), (SV[1], C['b2']))):
    ax.barh(yy + (j - 0.5) * 0.38, [g[k] for k, _ in cats], 0.36, color=col, label=f"{g['group']} ({g['with_vehicle']} households with a vehicle)")
    for i, (k, _) in enumerate(cats): ax.text(g[k] + 0.4, i + (j - 0.5) * 0.38, str(g[k]), va='center', fontsize=7)
ax.set_yticks(yy); ax.set_yticklabels([c for _, c in cats], fontsize=7.5); ax.invert_yaxis(); ax.set_xlabel('respondents (a respondent may tick more than one)'); ax.legend(fontsize=7); ax.set_title('Where the vehicle was parked last night, corridor respondents', loc='left', fontsize=9)
foot(fig, f'Source: APC-NDG survey, anonymized file as of {SURVEY_ASOF}; autumn nights (October 15 to November 7, 2026).'); fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(FIG, 'survey_parked_last_night_en.png')); plt.close(fig)

# ---------------------------------------------------------------- 5. dwellings on Terrebonne and in the band (City roll), survey coverage
gb = json.load(open(GEOBASE)); offs = {}
for name in ('Somerled', 'Monkland'):
    vs = []
    for ft in gb['features']:
        if ft['properties'].get('NOM_VOIE') != name: continue
        for lon, lat in ft['geometry']['coordinates']:
            u, v = FR.to_uv(*FR.to_EN(lon, lat))
            if 0 <= u <= FR.LENGTH: vs.append(v)
    offs[name] = dict(median_v=round(float(np.median(vs)), 1), n=len(vs))
north = max(offs['Somerled']['median_v'], offs['Monkland']['median_v']); south = min(offs['Somerled']['median_v'], offs['Monkland']['median_v'])
roll = json.load(open(ROLL))['features']; units = []
for ft in roll:
    p = ft['properties']; lon, lat = p['_lon'], p['_lat']; u, v = FR.to_uv(*FR.to_EN(lon, lat))
    if not (-30 <= u <= FR.LENGTH + 30): continue
    log = float(p.get('NOMBRE_LOGEMENT') or 0); on_t = 'Terrebonne' in (p.get('NOM_RUE') or '')
    units.append(dict(id=p['ID_UEV'], u=u, v=v, dwellings=log, on_terrebonne=on_t, street=(p.get('NOM_RUE') or '').strip(), usage=p.get('LIBELLE_UTILISATION')))
band = [x for x in units if south - 25 <= x['v'] <= north + 25 and x['dwellings'] > 0]
on_t = [x for x in band if x['on_terrebonne']]; blk = [x for x in band if not x['on_terrebonne']]
S['roll'] = dict(band=dict(north_street='Somerled' if offs['Somerled']['median_v'] > offs['Monkland']['median_v'] else 'Monkland', north_offset_m=north, south_offset_m=south, margin_m=25, note='units with a centroid between the two streets (their own frontages included), along the lane from its west end to Girouard; bounding-box extract, clipped near the east end on the north side'),
                 terrebonne=dict(units=len(on_t), dwellings=int(sum(x['dwellings'] for x in on_t))), within_block=dict(units=len(blk), dwellings=int(sum(x['dwellings'] for x in blk))), band_total=dict(units=len(band), dwellings=int(sum(x['dwellings'] for x in band))), offsets=offs)
S['roll']['coverage'] = dict(on_terrebonne=round(SV[0]['respondents'] / S['roll']['terrebonne']['dwellings'], 3), within_block=round(SV[1]['respondents'] / S['roll']['within_block']['dwellings'], 3), corridor=round(SV[2]['respondents'] / S['roll']['band_total']['dwellings'], 3))

# ---------------------------------------------------------------- 6. five winters of snow-related constraint (decision model appendix; City snow-removal transactions + ECCC)
WINTERS = [('2021–22', 27, 26, 36, 36, 46), ('2022–23', 27, 25, 34, 33, 48), ('2023–24', 12, 10, 18, 17, 31), ('2024–25', 27, 25, 32, 32, 57), ('2025–26', 24, 30, 36, 44, 54)]
S['winters'] = dict(rows=[dict(winter=w, loading_borough=a, loading_sector=b, storm_to_loading_borough=c, storm_to_loading_sector=d, snow_days=e) for w, a, b, c, d, e in WINTERS], mean_loading_sector=round(np.mean([w[2] for w in WINTERS]), 1), mean_storm_to_loading_sector=round(np.mean([w[4] for w in WINTERS]), 1), days=121,
                    source='Terrebonne-private decision model, appendix « Five winters of snow-related parking constraint » (scripts/winter_constraint_nights.py): loading night = >= 100 truckloads hauled in the borough or >= 40 in sector CDN-301; storm-to-loading adds the days from a triggering snowfall (>= 2.5 cm) to the loading; December 1 to March 31')
fig, ax = plt.subplots(figsize=(7, 3)); xw = np.arange(len(WINTERS))
ax.bar(xw - 0.2, [w[4] for w in WINTERS], 0.38, color=C['b2'], label='snow removal pending or under way (storm-to-loading), sector CDN-301'); ax.bar(xw + 0.2, [w[2] for w in WINTERS], 0.38, color=C['b1'], label='loading nights, sector CDN-301')
ax.set_xticks(xw); ax.set_xticklabels([w[0] for w in WINTERS]); ax.set_ylabel('nights, Dec 1 – Mar 31 (121)'); ax.legend(fontsize=7); ax.set_title('Nights with a snow-removal constraint on parking, five winters', loc='left', fontsize=9)
foot(fig, 'Sources: City of Montréal snow-removal transactions (CC-BY 4.0); ECCC daily, Montréal-Trudeau; computed in the author’s decision model.'); fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(FIG, 'winter_constraint_nights_en.png')); plt.close(fig)

S['generated'] = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
json.dump(S, open(os.path.join(HERE, 'summary.json'), 'w'), indent=1, default=str); print('summary.json written', file=sys.stderr)
