#!/usr/bin/env python3
"""Width of the cross streets of rue de Terrebonne, from the City's 2015 airborne LiDAR (open data, CC-BY 4.0) and the City géobase
(open data, CC-BY 4.0), with the same ground raster and the same curb detector as width_profile.py.

Why: the winter layout (EXP 2023, Fig. 6-6, 10.8 m) gives the cyclist riding with traffic a 3.5 m lane between two 2.4 m parking bands,
with the contraflow lane (2.0 m) and its buffer (0.5 m) beside it. Most of the cross streets of Terrebonne are one-way with parking on
both sides and one lane shared by cars and bicycles, the same arrangement with no contraflow lane and no buffer. How wide are they?
If they are about 8.3 m (= 10.8 − 2.0 − 0.5), they are the winter layout without the contraflow lane; if they are wider, the winter
layout's shared lane is narrower than what the cross streets offer.

Method: for every intersection node of the street frame (the lane's west end to Girouard), the géobase segments that start or end at
the node and are not rue de Terrebonne are the first blocks of the cross street, north and south. Each block is followed from CLEAR m
past the node (clear of the curb returns) to LMAX m or the block's end less CLEAR, a cross-section every STEP m, VMAX m each side,
every DV m; the curb on each side is the first rise of STEP_Z m over WIN m scanning outward from the axis between MIN_HALF and
MAX_HALF m, placed at the steepest point in that window (as in width_profile.py; MIN_HALF is 2.5 m here, since a cross street may be
narrower than 7 m; for the three two-way boulevards, Cavendish, Grand and Girouard, the window runs to 11 m and the cap to 22 m). A station is kept when both curbs are found and the width lies between WMIN and WMAX m. The parking signs of the
City inventory (Signalisation – Stationnement) within 12 m of the block's axis are counted per side, with the number of poles whose
sign is « \\A EN TOUT TEMPS » (AD-TT, no parking at any time), as an indicator only.

Outputs (derived/): cross_street_profile.csv (every station), cross_street_blocks.csv (per block), cross_street_summary.json,
figures/cross_street_widths_{en,fr}.png (most frequent reading, median and p10–p90 per block, Terrebonne's 11.0 m and the 8.3 m of the winter section without
the contraflow lane and its buffer), figures/cross_street_widths_hist_{en,fr}.png (kept stations, cross streets vs Terrebonne),
figures/cross_street_widths_review_{en,fr}.png (hillshade of every block with every curb detection).
Run: /opt/local/bin/python3.13 cross_street_widths.py   (needs numpy, rasterio, matplotlib; width_profile.py's outputs for the Terrebonne histogram)
"""
import csv, json, math, os, sys
import numpy as np, rasterio
HERE = os.path.dirname(os.path.abspath(__file__)); FIG = os.path.join(HERE, 'figures'); os.makedirs(FIG, exist_ok=True)
G54 = os.path.join(os.path.dirname(os.path.dirname(HERE)), '1954-underwriters-plans-terrebonne-garages', 'derived'); sys.path.insert(0, G54)
import frame as FR; from mtm import mtm8
MTL = os.path.expanduser('~/Terrebonne-data/third-party/montreal-opendata/')
LD = MTL + 'lidar-aerien-2015/derived/'
STEP, VMAX, DV = 2.0, 14.0, 0.1
MIN_HALF, MAX_HALF, STEP_Z, WIN = 2.5, 8.0, 0.07, 0.5
WMIN, WMAX = 5.0, 13.0
CLEAR, LMAX, NODE_R = 20.0, 240.0, 15.0
WINTER_SHARED = 2.4 + 3.5 + 2.4   # EXP Fig. 6-6 without the contraflow lane (2.0) and its buffer (0.5): 8.3 m
TERREBONNE = 11.0

def load(name):
    with rasterio.open(LD + name) as ds:
        a = ds.read(1).astype(np.float32); tr = ds.transform
    a[a <= -9998] = np.nan
    return a, (tr.c, tr.f, tr.a, -tr.e)
DTM, G = load('corridor_dtm_mean_0p25m.tif')
def sample(X, Y):
    x0, y0, dx, dy = G; c = ((X - x0) / dx).astype(int); r = ((y0 - Y) / dy).astype(int)
    ok = (c >= 0) & (c < DTM.shape[1]) & (r >= 0) & (r < DTM.shape[0]); out = np.full(X.shape, np.nan, np.float32); out[ok] = DTM[r[ok], c[ok]]; return out

TERR_ROWS = [float(r['width_curb_to_curb']) for r in csv.DictReader(open(os.path.join(HERE, 'street_width_profile.csv'), encoding='utf-8')) if r['kept'] == '1']
ARTERIAL = {'Cavendish', 'Grand', 'Girouard'}   # the boulevards and Girouard: two-way, on the arterial network, wider than the local streets
WIDE = dict(max_half=11.0, wmax=22.0)            # detector window and cap for them (local streets: MAX_HALF, WMAX)
def curb(v, z, side, max_half=None):
    max_half = MAX_HALF if max_half is None else max_half
    n = int(round(WIN / DV))
    order = range(len(v)) if side > 0 else range(len(v) - 1, -1, -1)
    for k in order:
        if not (MIN_HALF <= v[k] * side <= max_half): continue
        j = k + n if side > 0 else k - n
        if j < 0 or j >= len(v): continue
        a, b = z[k], z[j]
        if np.isnan(a) or np.isnan(b): continue
        if b - a >= STEP_Z:
            seg = z[min(k, j):max(k, j) + 1]
            if np.isnan(seg).any(): continue
            d = np.diff(seg); m = int(np.argmax(d if side > 0 else d[::-1]))
            pos = (k + m) if side > 0 else (k - m)
            return abs(v[pos]) + DV / 2
    return None

# ---------- the cross streets: géobase segments at the frame's nodes
GB = json.load(open(MTL + 'geobase_2026-10-14.json', encoding='utf-8'))['features']
def nm(name):
    n = name.split('; ')[0].replace('Avenue ', '').replace('Boulevard ', '').replace('de ', '')
    return n
class Seg:
    pass
segs = {}
order = []
for k, (lon, lat, names) in enumerate(FR.NODES):
    if not names: continue
    street = nm(names)
    if street not in order: order.append(street)
    nx, ny = mtm8(lon, lat)
    for f in GB:
        p = f['properties']
        if p['NOM_VOIE'] == 'Terrebonne' or p['ID_TRC'] in segs: continue
        cs = [mtm8(c[0], c[1]) for c in f['geometry']['coordinates']]
        d0, d1 = math.hypot(cs[0][0] - nx, cs[0][1] - ny), math.hypot(cs[-1][0] - nx, cs[-1][1] - ny)
        if min(d0, d1) > NODE_R: continue
        if d1 < d0: cs = cs[::-1]
        s = Seg(); s.id = p['ID_TRC']; s.street = street; s.name = (p.get('TYP_VOIE') or '') + ' ' + (p.get('LIE_VOIE') or '') + ' ' + p['NOM_VOIE']
        s.name = ' '.join(s.name.split()); s.sens = p['SENS_CIR']; s.classe = p['CLASSE']; s.pts = cs; s.node = (nx, ny)
        s.cum = [0.0]
        for a, b in zip(cs, cs[1:]): s.cum.append(s.cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        s.length = s.cum[-1]
        # north or south of Terrebonne: the far end's offset in the street frame
        lonf, latf = f['geometry']['coordinates'][-1] if d1 >= d0 else f['geometry']['coordinates'][0]
        _, v = FR.to_uv(*FR.to_EN(lonf, latf)); s.side = 'N' if v > 0 else 'S'
        segs[s.id] = s
print(f'{len(segs)} cross-street blocks at {len(order)} streets')

def along(s, d):
    """point and unit tangent at distance d along the block (from the Terrebonne node outward)"""
    i = max(0, min(len(s.pts) - 2, next((k for k in range(len(s.cum) - 1) if s.cum[k + 1] >= d), len(s.pts) - 2)))
    a, b = s.pts[i], s.pts[i + 1]; L = math.hypot(b[0] - a[0], b[1] - a[1]); t = (d - s.cum[i]) / L
    return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])), ((b[0] - a[0]) / L, (b[1] - a[1]) / L)

# ---------- parking signs per side (indicator)
signs = []
for r in csv.DictReader(open(MTL + 'signalisation-2026-10-23/signalisation_stationnement.csv', encoding='utf-8-sig')):
    if r.get('NOM_ARROND', '').startswith('Côte-des-Neiges'):
        try: signs.append((float(r['X']), float(r['Y']), r['CODE_RPA'], r['POTEAU_ID_POT']))
        except ValueError: pass
SX = np.array([s[0] for s in signs]); SY = np.array([s[1] for s in signs])
def sign_counts(s, dmax):
    """poles within 12 m of the block's axis between 0 and dmax m: per side (L/R looking away from Terrebonne), and those with AD-TT"""
    out = {'L': set(), 'R': set(), 'L_tt': set(), 'R_tt': set()}
    near = np.where((np.abs(SX - s.node[0]) < dmax + 30) & (np.abs(SY - s.node[1]) < dmax + 30))[0]
    for j in near:
        px, py = SX[j], SY[j]; best = None
        for d in np.arange(0, min(dmax, s.length), 1.0):
            (qx, qy), (tx, ty) = along(s, d); dist = math.hypot(px - qx, py - qy)
            if best is None or dist < best[0]: best = (dist, (px - qx) * ty - (py - qy) * tx)   # cross < 0 → left
        if best and best[0] <= 12.0:
            side = 'L' if best[1] < 0 else 'R'; out[side].add(signs[j][3])
            if signs[j][2] == 'AD-TT': out[side + '_tt'].add(signs[j][3])
    return {k: len(v) for k, v in out.items()}

# ---------- the profiles
rows = []; v = np.arange(-VMAX, VMAX + 1e-9, DV)
for s in segs.values():
    dmax = min(LMAX, s.length - CLEAR); s.dmax = dmax
    for d in np.arange(CLEAR, dmax + 1e-9, STEP):
        (qx, qy), (tx, ty) = along(s, d)
        X = qx - v * ty; Y = qy + v * tx     # +v = left of the direction away from Terrebonne
        z = sample(X, Y)
        wide = s.street in ARTERIAL; mh = WIDE['max_half'] if wide else MAX_HALF; wmax = WIDE['wmax'] if wide else WMAX
        cl, cr = curb(v, z, +1, mh), curb(v, z, -1, mh)
        width = (cl + cr) if (cl is not None and cr is not None) else None
        ok = width is not None and WMIN <= width <= wmax
        rows.append(dict(street=s.street, side=s.side, id_trc=s.id, dist_from_terrebonne=round(float(d), 1), x_mtm8=round(float(qx), 2), y_mtm8=round(float(qy), 2),
                         curb_L=None if cl is None else round(cl, 2), curb_R=None if cr is None else round(cr, 2),
                         width_curb_to_curb=None if width is None else round(width, 2), kept=int(ok)))
with open(os.path.join(HERE, 'cross_street_profile.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

def mode(a, w=0.2):
    """the most frequent reading: centre of the fullest w-metre bin (bins offset by half a bin so a reading sits mid-bin); the mean of the readings in that bin"""
    if not len(a): return None
    edges = np.arange(np.floor(a.min()) - w / 2, a.max() + w, w); h, _ = np.histogram(a, bins=edges); k = int(np.argmax(h))
    inb = a[(a >= edges[k]) & (a < edges[k + 1])]; return round(float(inb.mean()), 2)
def stats(vals):
    a = np.array([x for x in vals if x is not None], float)
    if not len(a): return dict(n=0, median=None, mode=None, core_share=None, p10=None, p90=None, min=None, max=None)
    m = mode(a); core = float(((a >= m - 0.5) & (a <= m + 0.5)).mean())
    return dict(n=int(len(a)), median=round(float(np.median(a)), 2), mode=m, core_share=round(core, 2), p10=round(float(np.percentile(a, 10)), 2), p90=round(float(np.percentile(a, 90)), 2), min=round(float(a.min()), 2), max=round(float(a.max()), 2))
blocks = []
for s in segs.values():
    rs = [r for r in rows if r['id_trc'] == s.id]; kept = [r for r in rs if r['kept']]
    st = stats([r['width_curb_to_curb'] for r in kept]); sc = sign_counts(s, s.dmax + CLEAR)
    blocks.append(dict(order=order.index(s.street), street=s.street, side=s.side, id_trc=s.id, geobase_name=s.name, one_way=int(s.sens != 0), classe=s.classe,
                       block_length_m=round(s.length, 1), measured_to_m=round(s.dmax, 1), stations=len(rs), stations_with_both_curbs=len(kept),
                       curb_median=st['median'], curb_mode=st['mode'], core_share=st['core_share'], curb_p10=st['p10'], curb_p90=st['p90'], curb_min=st['min'], curb_max=st['max'],
                       sign_poles_L=sc['L'], sign_poles_R=sc['R'], no_parking_any_time_poles_L=sc['L_tt'], no_parking_any_time_poles_R=sc['R_tt']))
blocks.sort(key=lambda b: (b['order'], b['side'] != 'N'))
with open(os.path.join(HERE, 'cross_street_blocks.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(blocks[0].keys())); w.writeheader(); w.writerows(blocks)

kept_rows = [r for r in rows if r['kept']]
one_way_ids = {b['id_trc'] for b in blocks if b['one_way']}
local_ids = {b['id_trc'] for b in blocks if b['street'] not in ARTERIAL}
S = dict(blocks=len(blocks), streets=len(order), stations=len(rows), kept=len(kept_rows),
         all=stats([r['width_curb_to_curb'] for r in kept_rows]),
         one_way=stats([r['width_curb_to_curb'] for r in kept_rows if r['id_trc'] in one_way_ids]),
         two_way=stats([r['width_curb_to_curb'] for r in kept_rows if r['id_trc'] not in one_way_ids]),
         local=stats([r['width_curb_to_curb'] for r in kept_rows if r['id_trc'] in local_ids]),
         terrebonne_stations=stats(TERR_ROWS),
         block_medians=stats([b['curb_median'] for b in blocks if b['curb_median'] is not None and b['stations_with_both_curbs'] >= 10]),
         block_medians_local=stats([b['curb_median'] for b in blocks if b['curb_median'] is not None and b['stations_with_both_curbs'] >= 10 and b['street'] not in ARTERIAL]),
         block_modes_local=stats([b['curb_mode'] for b in blocks if b['curb_mode'] is not None and b['stations_with_both_curbs'] >= 10 and b['street'] not in ARTERIAL]),
         blocks_local_with_10=sum(1 for b in blocks if b['stations_with_both_curbs'] >= 10 and b['street'] not in ARTERIAL),
         blocks_one_way=sum(b['one_way'] for b in blocks), blocks_two_way=sum(1 - b['one_way'] for b in blocks),
         winter_shared_without_contraflow=WINTER_SHARED, terrebonne=TERREBONNE,
         params=dict(step=STEP, vmax=VMAX, dv=DV, min_half=MIN_HALF, max_half=MAX_HALF, step_z=STEP_Z, win=WIN, wmin=WMIN, wmax=WMAX, arterial=sorted(ARTERIAL), arterial_max_half=WIDE['max_half'], arterial_wmax=WIDE['wmax'], clear=CLEAR, lmax=LMAX, node_r=NODE_R))
json.dump(S, open(os.path.join(HERE, 'cross_street_summary.json'), 'w'), indent=1)
print(json.dumps({k: S[k] for k in ('blocks', 'stations', 'kept', 'all', 'one_way', 'two_way', 'local', 'terrebonne_stations', 'block_medians_local', 'block_modes_local', 'blocks_local_with_10')}, indent=1))
for b in blocks: print(f"{b['street']:<16}{b['side']} {'1-way' if b['one_way'] else '2-way'} n={b['stations_with_both_curbs']:>3}/{b['stations']:<3} med {b['curb_median']} mode {b['curb_mode']} core {b['core_share']} ({b['curb_p10']}–{b['curb_p90']})  signs L {b['sign_poles_L']} ({b['no_parking_any_time_poles_L']} AD-TT) R {b['sign_poles_R']} ({b['no_parking_any_time_poles_R']} AD-TT)")

# ---------- figures
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
C_N, C_S, C_T, C_W = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e'
LAB = {'en': dict(t='Cross streets of rue de Terrebonne: curb-to-curb width of the first block on each side, from the City\'s 2015 LiDAR',
                  y='curb to curb (m)', n='north block', s='south block', tw='two-way (hollow)', terr='Terrebonne: 11.0 m (median of the lane\'s length)',
                  win='winter section without the contraflow lane and its buffer: 2.4 + 3.5 + 2.4 = 8.3 m', note='Marker = the block\'s most frequent reading (0.2 m bins); short tick = median; bar = 10th to 90th percentile of the stations kept; hollow = two-way block; faded = fewer than half the stations within 0.5 m of the most frequent reading;\nno marker = fewer than 10 stations kept. Streets west to east. The upper tails are driveway aprons and tree cover: where the curb is lowered or hidden, the detector reads the next rise further out.'),
       'fr': dict(t='Rues transversales de la rue de Terrebonne : largeur de bordure à bordure du premier tronçon de chaque côté, LiDAR 2015 de la Ville',
                  y='bordure à bordure (m)', n='tronçon nord', s='tronçon sud', tw='double sens (évidé)', terr='Terrebonne : 11,0 m (médiane sur la longueur de la piste)',
                  win='section hivernale sans la voie à contresens et sa zone tampon : 2,4 + 3,5 + 2,4 = 8,3 m', note='Marqueur = lecture la plus fréquente du tronçon (classes de 0,2 m) ; petit trait = médiane ; barre = 10e au 90e centile des stations retenues ; évidé = tronçon à double sens ; estompé = moins de la moitié des stations à 0,5 m de la lecture la plus fréquente ;\npas de marqueur = moins de 10 stations retenues. Rues d\'ouest en est. Les queues vers le haut sont les entrées charretières et les arbres : où la bordure est abaissée ou cachée, le détecteur lit la prochaine marche plus loin.')}
for lang, L in LAB.items():
    fig, ax = plt.subplots(figsize=(15, 6), dpi=150)
    ax.axhline(TERREBONNE, color=C_T, lw=1.2, ls='--'); ax.text(len(order) - 0.6, TERREBONNE + 0.08, L['terr'], fontsize=8.5, ha='right', va='bottom', color=C_T)
    ax.axhline(WINTER_SHARED, color=C_W, lw=1.2, ls=':'); ax.text(len(order) - 0.6, WINTER_SHARED - 0.08, L['win'], fontsize=8.5, ha='right', va='top', color=C_W)
    for b in blocks:
        if b['curb_median'] is None or b['stations_with_both_curbs'] < 10: continue
        x = b['order'] + (-0.17 if b['side'] == 'N' else 0.17); col = C_N if b['side'] == 'N' else C_S
        al = 1.0 if b['core_share'] >= 0.5 else 0.35   # low confidence: fewer than half the stations within 0.5 m of the most frequent reading
        ax.plot([x, x], [b['curb_p10'], b['curb_p90']], color=col, lw=2, solid_capstyle='round', alpha=al)
        ax.plot(x, b['curb_mode'], 'o', ms=8, mfc=col if b['one_way'] else 'white', mec=col, mew=1.8, alpha=al)
        ax.plot([x - 0.12, x + 0.12], [b['curb_median'], b['curb_median']], '-', color=col, lw=1.2, alpha=al)
    ax.set_xticks(range(len(order))); ax.set_xticklabels(order, rotation=60, ha='right', fontsize=9)
    ax.set_xlim(-0.7, len(order) - 0.3); ax.set_ylim(6, 18); ax.set_ylabel(L['y']); ax.grid(axis='y', color='0.9'); ax.set_axisbelow(True)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Line2D([], [], marker='o', color=C_N, ms=8, lw=0, label=L['n']), Line2D([], [], marker='o', color=C_S, ms=8, lw=0, label=L['s']),
                       Line2D([], [], marker='o', mfc='white', mec='0.4', ms=8, lw=0, label=L['tw'])], loc='upper left', fontsize=8.5, frameon=False)
    ax.set_title(L['t'], fontsize=10.5); fig.text(0.01, 0.004, L['note'], fontsize=7.5, color=C_W, va='bottom')
    fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(os.path.join(FIG, f'cross_street_widths_{lang}.png')); plt.close(fig)

# histogram: kept stations of the local cross streets vs Terrebonne's kept stations
terr = [float(r['width_curb_to_curb']) for r in csv.DictReader(open(os.path.join(HERE, 'street_width_profile.csv'), encoding='utf-8')) if r['kept'] == '1']
cross = [r['width_curb_to_curb'] for r in kept_rows if r['id_trc'] in local_ids]
HL = {'en': dict(t='Stations kept: the local cross streets (first block each side, two-way boulevards excluded) against rue de Terrebonne', x='curb to curb (m)', y='share of stations', a='cross streets', b='Terrebonne'),
      'fr': dict(t='Stations retenues : les rues transversales locales (premier tronçon de chaque côté, boulevards exclus) et la rue de Terrebonne', x='bordure à bordure (m)', y='part des stations', a='rues transversales', b='Terrebonne')}
bins = np.arange(6, 14.01, 0.25)
for lang, L in HL.items():
    fig, ax = plt.subplots(figsize=(10, 4.2), dpi=150)
    ax.hist(cross, bins=bins, weights=np.ones(len(cross)) / len(cross), histtype='stepfilled', color=C_N, alpha=0.35, ec=C_N, lw=1.5, label=f"{L['a']} (n={len(cross)})")
    ax.hist(terr, bins=bins, weights=np.ones(len(terr)) / len(terr), histtype='step', color=C_T, lw=1.8, label=f"{L['b']} (n={len(terr)})")
    ax.axvline(WINTER_SHARED, color=C_W, lw=1.2, ls=':'); ax.text(WINTER_SHARED, ax.get_ylim()[1] * 0.97, ' 8.3 m' if lang == 'en' else ' 8,3 m', fontsize=8.5, color=C_W, va='top')
    ax.set_xlabel(L['x']); ax.set_ylabel(L['y']); ax.set_title(L['t'], fontsize=10); ax.legend(frameon=False, fontsize=9); ax.grid(axis='y', color='0.9'); ax.set_axisbelow(True)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, f'cross_street_widths_hist_{lang}.png')); plt.close(fig)

# review figure: hillshade of every block with every curb detection
def hill(z, dx=0.25):
    zz = np.where(np.isnan(z), np.nanmedian(z), z); gy, gx = np.gradient(zz, dx); slope = np.arctan(np.hypot(gx, gy)); asp = np.arctan2(-gx, gy)
    a, b = math.radians(315), math.radians(40)
    return np.clip(math.sin(b) * np.cos(slope) + math.cos(b) * np.sin(slope) * np.cos(a - asp), 0, 1)
def strip(s, d0, d1, vmax=10.0, du=0.25):
    dd = np.arange(d0, d1, du); vv = np.arange(-vmax, vmax, du); Z = np.full((len(vv), len(dd)), np.nan, np.float32)
    for j, d in enumerate(dd):
        if d > s.length: break
        (qx, qy), (tx, ty) = along(s, d); Z[:, j] = sample(qx - vv * ty, qy + vv * tx)
    return dd, vv, Z
RV = {'en': dict(t='Review figure: the LiDAR ground surface along the first block of every cross street (hillshade, 0.25 m), looking away from rue de Terrebonne (left of travel up); red = left curb, blue = right curb, grey ticks = station dropped', x='distance from the Terrebonne axis (m)'),
      'fr': dict(t='Figure de contrôle : la surface du sol LiDAR le long du premier tronçon de chaque rue transversale (ombrage, 0,25 m), en s\'éloignant de la rue de Terrebonne (gauche en haut) ; rouge = bordure gauche, bleu = bordure droite, traits gris = station rejetée', x='distance depuis l\'axe de Terrebonne (m)')}
BN = [b for b in blocks if b['side'] == 'N']; BS = [b for b in blocks if b['side'] == 'S']
nrow = max(len(BN), len(BS))
strips = {b['id_trc']: strip(segs[b['id_trc']], 0, LMAX + CLEAR) for b in blocks}
for lang, L in RV.items():
    fig, axes = plt.subplots(nrow, 2, figsize=(20, 0.95 * nrow + 1.2), dpi=100)
    for col, BB in enumerate((BN, BS)):
        for i in range(nrow):
            ax = axes[i, col]
            if i >= len(BB): ax.axis('off'); continue
            b = BB[i]; dd, vv, Z = strips[b['id_trc']]
            ax.imshow(hill(Z), cmap='gray', extent=(dd[0], dd[-1], vv[0], vv[-1]), origin='lower', aspect='equal', vmin=0.2, vmax=1.0)
            rs = [r for r in rows if r['id_trc'] == b['id_trc']]
            ax.plot([r['dist_from_terrebonne'] for r in rs if r['kept']], [r['curb_L'] for r in rs if r['kept']], '.', ms=3, color='#d62728')
            ax.plot([r['dist_from_terrebonne'] for r in rs if r['kept']], [-r['curb_R'] for r in rs if r['kept']], '.', ms=3, color='#1f77b4')
            ax.plot([r['dist_from_terrebonne'] for r in rs if not r['kept']], [0] * sum(1 for r in rs if not r['kept']), '|', ms=5, color='0.6')
            ax.set_xlim(0, LMAX + CLEAR); ax.set_ylim(-10, 10); ax.set_yticks([]); ax.tick_params(labelsize=6)
            lab = f"{b['street']} {'N' if b['side'] == 'N' else 'S'} · {'1-way' if b['one_way'] else '2-way'} · {b['curb_mode'] if b['curb_mode'] is not None else '–'} m (n={b['stations_with_both_curbs']})"
            ax.text(2, 8.6, lab, fontsize=7, va='top', color='0.1', bbox=dict(fc='white', ec='none', alpha=0.7, pad=1))
            if i < nrow - 1: ax.set_xticklabels([])
        axes[nrow - 1, col].set_xlabel(L['x'], fontsize=8)
    fig.suptitle(L['t'], fontsize=10, y=0.998); fig.tight_layout(rect=(0, 0, 1, 0.99), h_pad=0.15)
    fig.savefig(os.path.join(FIG, f'cross_street_widths_review_{lang}.png')); plt.close(fig)
print('figures written')
