#!/usr/bin/env python3
"""Two further maps for the 2026 petition page (owner's request, Oct 27, 2026).

1. Small-cell aggregation (candidate public form, issue #38): adjacent postal-code polygons are merged until every
   cell with signatures holds at least MIN_CELL signers. Greedy, deterministic: take the cell with the fewest signers
   (ties: smallest area); among the cells touching it, merge with the one with the fewest signers that brings the
   total to MIN_CELL, else the one with the most signers, else the smallest zero-signer neighbour; repeat. Codes with
   signatures but no polygon in the cache are attached to the nearest polygon first. Cells that cannot reach the
   threshold (no neighbour left inside the borough) are reported.
2. PRIVATE monitoring figure: the 2026 petition beside the 2024 opposition petition (release 2025-081), both by
   six-character postal code on the same colour scale. Not small-cell redacted; never published.

Inputs: the per-code tables written by petition_2026_map.py (~/Terrebonne-data/petition-2026/petition_2026_by_postal_code_<stamp>.csv)
and by the 2025-081 work (Terrebonne-access-requests/2025-081/derived/petition_signatures_by_postal_code.csv); the CanMap polygon
cache; districts 2025; the lane. Usage: python3 scripts/petition_2026_map_merged.py [--stamp=interim] [--asof=YYYY-MM-DD] [--min=5]
"""
import csv, json, math, os, sys, re, datetime as dt, collections
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.path import Path
from shapely.geometry import Polygon, MultiPolygon, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE = os.path.dirname(os.path.abspath(__file__)); PRV = os.path.dirname(HERE)
D = os.path.expanduser('~/Terrebonne-data/petition-2026'); FIGS = os.path.join(PRV, 'figs', 'petition-2026')
opt = lambda k, d: next((a.split('=', 1)[1] for a in sys.argv[1:] if a.startswith(f'--{k}=')), d)
stamp = opt('stamp', 'interim'); asof = opt('asof', dt.date.today().isoformat()); MIN_CELL = int(opt('min', '5')); MIN_POP = int(opt('minpop', '300'))   # a cell needs both: signers (privacy) and residents (a usable denominator; owner, Nov 4, 2026)
D26 = (dt.date.fromisoformat(asof) - dt.date(2026, 10, 21)).days + 1   # launched Oct 21, 2026
D24 = (dt.date(2024, 2, 5) - dt.date(2024, 1, 12)).days + 1            # online Jan 12 to the Feb 5, 2024 supplement; paper sheets undated
T2026 = os.path.join(D, f'petition_2026_by_postal_code_{stamp}.csv')
T2024 = os.path.expanduser('~/GitHub/Terrebonne-access-requests/2025-081/derived/petition_signatures_by_postal_code.csv')
POSTAL = os.path.expanduser('~/Terrebonne-data/third-party/serviceobjects-2024-03/CanadianPostalCodes202403.csv')
LDU = os.path.join(PRV, 'data/petition/ldu_polygons_area.json'); DIST = os.path.join(PRV, 'data/districts/districts-electoraux-2025.json'); LANE = os.path.join(PRV, 'data/petition/terrebonne_lane_geobase.geojson')
LAT0 = 45.47; MX = 111320 * math.cos(math.radians(LAT0)); MY = 111320
def xy(lon, lat): return ((lon + 73.63) * MX, (lat - LAT0) * MY)
X0, X1, Y0, Y1 = -3800, 2900, -2400, 2900

def read_counts(p):
    c = collections.Counter()
    for r in csv.DictReader(open(p, encoding='utf-8')):
        code = re.sub(r'[^A-Z0-9]', '', r['postal_code'].upper())
        if len(code) == 6: c[code] += int(r['entries'])
    return c
n26, n24 = read_counts(T2026), read_counts(T2024)
need = set(n26) | set(n24)
cent = {}
with open(POSTAL, encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        c = r['PostalCode'].replace(' ', '').upper()
        if c in need:
            try: cent[c] = xy(float(r['Longitude']), float(r['Latitude']))
            except (ValueError, TypeError): pass
districts = json.load(open(DIST, encoding='utf-8'))['features']
cdn = [f for f in districts if f['properties']['NOM_ARR'] == 'Côte-des-Neiges–Notre-Dame-de-Grâce']
def geoms(f):
    g = f['geometry']; pp = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
    return [Polygon([xy(*c[:2]) for c in poly[0]], [[xy(*c[:2]) for c in h] for h in poly[1:]]) for poly in pp]
borough = unary_union([g for f in cdn for g in geoms(f)])
lane_xy = []
for f in json.load(open(LANE, encoding='utf-8'))['features']:
    g = f['geometry']; lines = [g['coordinates']] if g['type'] == 'LineString' else g['coordinates']
    for line in lines: lane_xy.append([xy(*c[:2]) for c in line])

# --- polygons in the borough (centroid test, as the main map) ---
raw = json.load(open(LDU, encoding='utf-8'))['polygons']
poly = {}
for code, rings in raw.items():
    shp = [Polygon([xy(lon, lat) for lon, lat in ring]).buffer(0) for ring in rings]
    shp = unary_union(shp) if len(shp) > 1 else shp[0]
    if shp.is_empty or not borough.contains(shp.representative_point()): continue
    poly[code] = shp
codes = list(poly); tree = STRtree([poly[c] for c in codes])
adj = {c: set() for c in codes}
for i, c in enumerate(codes):
    for j in tree.query(poly[c], predicate='touches'):
        if codes[j] != c: adj[c].add(codes[j]); adj[codes[j]].add(c)
    for j in tree.query(poly[c], predicate='intersects'):   # slivers overlapping by a hair count as neighbours too
        if codes[j] != c and poly[c].intersection(poly[codes[j]]).length > 1: adj[c].add(codes[j]); adj[codes[j]].add(c)

CENSUS = os.path.join(PRV, 'data/census/da_2021_cdnndg.geojson')
das = []
if os.path.exists(CENSUS):
    for f in json.load(open(CENSUS, encoding='utf-8'))['features']:
        g = f['geometry']; pp = [g['coordinates']] if g['type'] == 'Polygon' else g['coordinates']
        shp = unary_union([Polygon([xy(*c[:2]) for c in pl[0]], [[xy(*c[:2]) for c in h] for h in pl[1:]]).buffer(0) for pl in pp])
        pv = f['properties'].get('pop_2021')
        if pv is None or shp.is_empty: continue
        das.append((shp, float(pv), shp.area))
dtree = STRtree([d[0] for d in das]) if das else None
def population(cells):
    """Census 2021 population of each cell: the dissemination areas' populations apportioned by the area of overlap (an estimate)."""
    out = {}
    if not dtree: return out, 0.0
    for r, shp in cells.items():
        tot = 0.0
        for j in dtree.query(shp, predicate='intersects'):
            dshp, pv, a = das[j]; inter = shp.intersection(dshp).area
            if inter > 0 and a > 0: tot += pv * inter / a
        out[r] = tot
    return out, sum(out.values())
pop_code, _ = population(poly)   # residents per postal-code polygon, summed into the cells by the merge

def attach_orphans(counts):
    """Signatures at codes with no polygon (or a polygon outside the borough): moved to the nearest borough polygon."""
    out = collections.Counter(); moved = 0
    for c, n in counts.items():
        if c in poly: out[c] += n; continue
        if c not in cent: continue
        p = Point(cent[c])
        if not borough.contains(p): continue
        j = tree.nearest(p); out[codes[j]] += n; moved += n
    return out, moved

def merge(count_sets, min_cell, min_pop):
    """count_sets: one Counter per petition. Step 1: every polygon without signers (in any set) joins the nearest polygon with
    signers (centroid distance), so the borough is partitioned into compact seed cells. Step 2: greedy threshold merge among
    touching cells: take the cell that fails a threshold with the fewest signers (summed over the sets; ties: fewest
    residents, then smallest area); among its touching neighbours, join the one giving the smallest merged area among those
    that bring it to >= min_cell signers IN EACH SET and >= min_pop residents, else the neighbour with the smallest area;
    repeat until every cell meets every threshold or no neighbour is left. With two sets, both petitions get the same cells
    and each keeps its own privacy floor (owner, Nov 4, 2026). Returns members, a list of per-set counts, residents, stuck, steps."""
    K = len(count_sets)
    seeds = [c for c in codes if any(cs.get(c, 0) > 0 for cs in count_sets)]
    if not seeds: return {c: {c} for c in codes}, [{c: 0 for c in codes} for _ in count_sets], {c: 0.0 for c in codes}, set(), 0
    seed_tree = STRtree([poly[c].centroid for c in seeds])
    region_of = {}; members = {c: {c} for c in seeds}
    for c in codes:
        if c in members: region_of[c] = c; continue
        r = seeds[seed_tree.nearest(poly[c].centroid)]; region_of[c] = r; members[r].add(c)
    cnt = [{r: cs.get(r, 0) for r in members} for cs in count_sets]; area = {r: sum(poly[a].area for a in members[r]) for r in members}
    popr = {r: sum(pop_code.get(a, 0.0) for a in members[r]) for r in members}
    tot = lambda r: sum(ck[r] for ck in cnt)
    ok = lambda r: all(ck[r] >= min_cell for ck in cnt) and popr[r] >= min_pop
    def neighbours(r): return {region_of[b] for a in members[r] for b in adj[a]} - {r}
    stuck = set(); steps = 0
    while True:
        small = [r for r in members if not ok(r) and r not in stuck]
        if not small: break
        r = min(small, key=lambda k: (tot(k), popr[k], area[k]))
        nb = neighbours(r)
        if not nb: stuck.add(r); continue
        reach = [q for q in nb if all(ck[q] + ck[r] >= min_cell for ck in cnt) and popr[q] + popr[r] >= min_pop]
        q = min(reach, key=lambda k: area[k]) if reach else min(nb, key=lambda k: area[k])
        for a in members[q]: region_of[a] = r
        members[r] |= members.pop(q); area[r] += area.pop(q); popr[r] += popr.pop(q); steps += 1
        for ck in cnt: ck[r] += ck.pop(q)
    # islands with no touching neighbour (stuck): attached to the nearest other cell by centroid distance, so no cell is left
    # below a floor (the stuck set is returned for the record; the cells it names no longer exist as such)
    for r in sorted(stuck, key=lambda k: (tot(k), area[k])):
        others = [q for q in members if q != r]
        if not others: break
        c = unary_union([poly[a] for a in members[r]]).centroid
        q = min(others, key=lambda k: unary_union([poly[a] for a in members[k]]).centroid.distance(c))
        for a in members[r]: region_of[a] = q
        members[q] |= members.pop(r); area[q] += area.pop(r); popr[q] += popr.pop(r); steps += 1
        for ck in cnt: ck[q] += ck.pop(r)
    return members, cnt, popr, stuck, steps

n26b, moved26 = attach_orphans(n26)
members, (mcnt,), pop_cell, stuck, steps = merge([n26b], MIN_CELL, MIN_POP)
cells = {r: unary_union([poly[a] for a in m]) for r, m in members.items()}
pop_total = sum(pop_cell.values())
with_sig = [r for r in members if mcnt[r] > 0]
# --- population per cell: census 2021 dissemination areas (scripts/census_da_cdnndg.py), area-weighted into the cells ---
sizes = sorted(len(members[r]) for r in with_sig)
os.makedirs(FIGS, exist_ok=True)
with open(os.path.join(D, f'petition_2026_merged_cells_{stamp}.csv'), 'w', encoding='utf-8') as out:
    out.write('cell,signers,postal_codes_in_cell,codes_with_signers,area_ha,below_threshold,pop_2021_est,signers_per_1000,codes\n')
    for r in sorted(with_sig, key=lambda k: -mcnt[k]):
        ws = sum(1 for a in members[r] if n26b.get(a, 0) > 0)
        pc = pop_cell.get(r); pcs = f'{pc:.0f}' if pc is not None else ''; rates = f'{1000 * mcnt[r] / pc:.1f}' if pc else ''
        out.write(f'{r},{mcnt[r]},{len(members[r])},{ws},{cells[r].area/1e4:.1f},{int(mcnt[r] < MIN_CELL)},{pcs},{rates},{" ".join(sorted(members[r]))}\n')
summary = dict(min_cell=MIN_CELL, min_pop=MIN_POP, codes_in_borough=len(codes), codes_with_signers=sum(1 for c in codes if n26b.get(c, 0) > 0), signers_in_borough_polygons=sum(n26b.values()),
               moved_from_codes_without_polygon=moved26, cells_with_signers=len(with_sig), merges=steps, cells_below_threshold=len(stuck),
               single_code_cells=sum(1 for s in sizes if s == 1), median_codes_per_cell=(sizes[len(sizes)//2] if sizes else 0), max_codes_per_cell=(max(sizes) if sizes else 0),
               median_signers_per_cell=sorted(mcnt[r] for r in with_sig)[len(with_sig)//2] if with_sig else 0)
json.dump(summary, open(os.path.join(FIGS, f'petition_2026_merged_summary_{stamp}.json'), 'w'), indent=1)

# --- drawing ---
VMAX = max(max(n26.values(), default=20), max(n24.values(), default=20), 20)
levels = [0, 1, 2, 3, 5, 10, 20, VMAX + 1]
base = plt.get_cmap('YlOrRd')(np.linspace(0.12, 1.0, len(levels) - 2))
cmap = ListedColormap(np.vstack([[0.90, 0.90, 0.90, 1.0], base])); norm = BoundaryNorm(levels, cmap.N)
TICKS = [0.5, 1.5, 2.5, 4, 7.5, 15, (20 + VMAX + 1) / 2]; TLAB = ['0', '1', '2', '3–4', '5–9', '10–19', f'20–{VMAX}']
def fill(ax, shp, color, lw=0.25, ec='0.35', z=2):
    parts = shp.geoms if isinstance(shp, MultiPolygon) else [shp]
    for p in parts:
        xs, ys = p.exterior.xy; ax.fill(xs, ys, color=color, lw=0, zorder=z); ax.plot(xs, ys, color=ec, lw=lw, zorder=z + 1)
        for h in p.interiors: hx, hy = h.xy; ax.fill(hx, hy, color='white', lw=0, zorder=z); ax.plot(hx, hy, color=ec, lw=lw, zorder=z + 1)
def frame(ax, title):
    parts = borough.geoms if isinstance(borough, MultiPolygon) else [borough]
    for p in parts: xs, ys = p.exterior.xy; ax.plot(xs, ys, color='0.15', lw=1.3, zorder=6)
    for f in cdn:
        g = geoms(f)[0]; c = g.representative_point()
        if X0 < c.x < X1 and Y0 < c.y < Y1: ax.text(c.x, c.y + 250, f['properties']['NOM_DISTRICT'], fontsize=11, color='0.15', ha='center', va='center', weight='bold', zorder=7)
    for line in lane_xy: ax.plot([q[0] for q in line], [q[1] for q in line], color='#1f77b4', lw=3.0, solid_capstyle='round', zorder=7)
    ax.set_aspect('equal'); ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_title(title, fontsize=11.5)
    ax.set_xlabel('metres east of 73.63° W'); ax.set_ylabel('metres north of 45.47° N')
CREDIT = 'Postal-code boundaries: DMTI Spatial Inc., CanMap Postal Code Suite v2024.3; clipped to the borough. Districts: Ville de Montréal 2025 (CC-BY). Lane: Ville de Montréal géobase (CC-BY).'

# 1. merged map: cells of unequal size, so the fill is the density (signers per km2 of cell), the label the count
DLEV = [0, 10, 25, 50, 100, 200, 300, 600]
dcmap = ListedColormap(plt.get_cmap('YlOrRd')(np.linspace(0.04, 1.0, len(DLEV) - 1))); dnorm = BoundaryNorm(DLEV, dcmap.N)
fig, ax = plt.subplots(figsize=(15, 12.5), dpi=150)
for r, shp in cells.items():
    n = mcnt[r]; dens = n / (shp.area / 1e6)
    fill(ax, shp, dcmap(dnorm(dens)), lw=(0.6 if n > 0 else 0.2), ec=('0.2' if n > 0 else '0.55'))
    if n > 0:
        c = shp.representative_point(); ax.text(c.x, c.y, str(n), fontsize=7, ha='center', va='center', color='black' if dens < 100 else 'white', zorder=8, clip_on=True)
frame(ax, f'Petition « Gardons la piste Terrebonne toute l\'année » (2026, as of {asof}): postal codes merged into cells of at least {MIN_CELL} signers\n'
          f'Fill: signers per km² of cell; label: signers. {summary["codes_with_signers"]} codes with signatures → {summary["cells_with_signers"]} cells covering the borough\n'
          f'(median {summary["median_codes_per_cell"]} codes and {summary["median_signers_per_cell"]} signers per cell; {summary["cells_below_threshold"]} left below {MIN_CELL}); {summary["signers_in_borough_polygons"]} signers in the borough\'s polygons')
sm = plt.cm.ScalarMappable(cmap=dcmap, norm=dnorm); cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.01, ticks=[(a + b) / 2 for a, b in zip(DLEV[:-1], DLEV[1:])])
cb.ax.set_yticklabels(['under 10', '10–24', '25–49', '50–99', '100–199', '200–299', '300+']); cb.set_label('signers per km² of cell', fontsize=11)
ax.text(0.005, 0.005, CREDIT + f'\nMerge rule: empty codes join the nearest code with signers; then, smallest cell first, join the touching cell that reaches {MIN_CELL} with the least area, else the smallest neighbour.\nLarge cells in the north hold few signers spread over a wide area. Candidate public form (issue #38).', transform=ax.transAxes, fontsize=7.5, color='0.3', zorder=9)
fig.tight_layout(); fig.savefig(os.path.join(FIGS, f'petition_2026_map_merged_{stamp}.png')); plt.close(fig)

# 1b. count map: the fill is the number of signers in the cell (cells of unequal size: read with the density map)
CLEV = [0, 1, 5, 8, 11, 15, 20, 1000]
ccmap = ListedColormap(plt.get_cmap('YlOrRd')(np.linspace(0.04, 1.0, len(CLEV) - 1))); cnorm = BoundaryNorm(CLEV, ccmap.N)
fig, ax = plt.subplots(figsize=(15, 12.5), dpi=150)
for r, shp in cells.items():
    n = mcnt[r]
    fill(ax, shp, ccmap(cnorm(n)), lw=(0.6 if n > 0 else 0.2), ec=('0.2' if n > 0 else '0.55'))
    if n > 0:
        c = shp.representative_point(); ax.text(c.x, c.y, str(n), fontsize=7, ha='center', va='center', color='black' if n < 11 else 'white', zorder=8, clip_on=True)
frame(ax, f'Petition « Gardons la piste Terrebonne toute l\'année » (2026, as of {asof}): postal codes merged into cells of at least {MIN_CELL} signers\n'
          f'Fill and label: signers in the cell. {summary["codes_with_signers"]} codes with signatures → {summary["cells_with_signers"]} cells; {summary["signers_in_borough_polygons"]} signers in the borough\'s polygons\n'
          f'Cells differ in size: a count map favours large cells; see the density and per-capita maps for the same cells')
sm = plt.cm.ScalarMappable(cmap=ccmap, norm=cnorm); cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.01, ticks=[(a + b) / 2 for a, b in zip(CLEV[:-1], CLEV[1:])])
cb.ax.set_yticklabels(['0', '1–4', '5–7', '8–10', '11–14', '15–19', '20+']); cb.set_label('signers in the cell', fontsize=11)
ax.text(0.005, 0.005, CREDIT + f'\nSame cells as the density map (merge rule: empty codes join the nearest code with signers; then the smallest cell joins the touching cell that reaches {MIN_CELL} with the least area).', transform=ax.transAxes, fontsize=7.5, color='0.3', zorder=9)
fig.tight_layout(); fig.savefig(os.path.join(FIGS, f'petition_2026_map_merged_count_{stamp}.png')); plt.close(fig)

# 1c. per-capita map: signers per 1,000 residents (census 2021 DA populations, area-weighted into the cells)
PLEV = [0, 2, 5, 10, 20, 40, 80, 100000]
pcmap = ListedColormap(plt.get_cmap('YlOrRd')(np.linspace(0.04, 1.0, len(PLEV) - 1))); pnorm = BoundaryNorm(PLEV, pcmap.N)
PTICKS = [(a + b) / 2 for a, b in zip(PLEV[:-2], PLEV[1:-1])] + [90]; PLAB = ['under 2', '2–4', '5–9', '10–19', '20–39', '40–79', '80+']
POPCREDIT = 'Population: Statistics Canada, Census of Population 2021, dissemination areas (Statistics Canada Open Licence), apportioned to the cells by area; a cell\'s population is an estimate.'
def label_spot(shp, half):
    """Where a label of half-height `half` metres fits: the cell eroded by `half`; None if nothing is left (the thin strips)."""
    core = shp.buffer(-half)
    return None if core.is_empty else core.representative_point()
def percapita_panel(ax, cells_, cnt_, pop_, title, fontsize=6.5, half=25.0):
    """One per-capita map: fill = signers per 1,000 residents; label = signers, only where the cell can hold the label (eroded
    by `half` metres; owner, Nov 4, 2026: the labels overlapped on the thin block-face cells), with a white halo, placed in
    the wide part of the cell. Cells under 150 residents grey with the count only (same rule). Returns the number of such cells."""
    import matplotlib.patheffects as pe
    halo = [pe.withStroke(linewidth=1.6, foreground='white', alpha=0.85)]
    thin = 0
    for r, shp in cells_.items():
        n = cnt_[r]; pc = pop_.get(r, 0.0); spot = label_spot(shp, half) if n > 0 else None
        if n > 0 and pc < 150:
            fill(ax, shp, (0.85, 0.85, 0.85), lw=0.6, ec='0.2'); thin += 1
            if spot: ax.text(spot.x, spot.y, f'{n}*', fontsize=fontsize, ha='center', va='center', color='black', zorder=8, clip_on=True, path_effects=halo)
            continue
        rate = 1000 * n / pc if pc > 0 else 0.0
        fill(ax, shp, pcmap(pnorm(rate)), lw=(0.6 if n > 0 else 0.2), ec=('0.2' if n > 0 else '0.55'))
        if spot: ax.text(spot.x, spot.y, str(n), fontsize=fontsize, ha='center', va='center', color='black', zorder=8, clip_on=True, path_effects=halo)
    frame(ax, title)
    return thin
if pop_cell:
    fig, ax = plt.subplots(figsize=(15, 12.5), dpi=150)
    thin = percapita_panel(ax, cells, mcnt, pop_cell,
              f'Petition « Gardons la piste Terrebonne toute l\'année » (2026, as of {asof}): signers per 1,000 residents, cells of at least {MIN_CELL} signers and {MIN_POP} residents\n'
              f'Fill: signers per 1,000 residents (Census 2021 population of the dissemination areas, area-weighted into the cells); label: signers\n'
              f'{summary["signers_in_borough_polygons"]} signers in the borough\'s polygons; {pop_total:,.0f} residents in the cells; label: signers; cells too narrow for a label are unlabelled')
    sm = plt.cm.ScalarMappable(cmap=pcmap, norm=pnorm); cb = fig.colorbar(sm, ax=ax, fraction=0.03, pad=0.01, ticks=PTICKS)
    cb.ax.set_yticklabels(PLAB); cb.set_label('signers per 1,000 residents', fontsize=11)
    ax.text(0.005, 0.005, CREDIT + '\n' + POPCREDIT, transform=ax.transAxes, fontsize=7.5, color='0.3', zorder=9)
    fig.tight_layout(); fig.savefig(os.path.join(FIGS, f'petition_2026_map_merged_percapita_{stamp}.png')); plt.close(fig)
    summary['population_in_cells_2021'] = round(pop_total); summary['cells_under_150_residents'] = thin

# 1d. the two petitions side by side, same cells rule and same per-capita scale (owner, Nov 4, 2026): the 2024 opposition
# petitions (release 2025-081) run through the same orphan attachment, the same merge to cells of at least MIN_CELL signers
# and the same census apportioning. Small-cell redacted like 1c, so it can take the same public form.
    n24b, moved24 = attach_orphans(n24)
    members24, (mcnt24, mcnt26s), pop24, stuck24, steps24 = merge([n24b, n26b], MIN_CELL, MIN_POP)   # ONE set of cells for both petitions
    cells24 = {r: unary_union([poly[a] for a in m]) for r, m in members24.items()}
    pop24_total = sum(pop24.values())
    with24 = [r for r in members24 if mcnt24[r] > 0 or mcnt26s[r] > 0]
    with open(os.path.join(D, f'petition_2024_2026_shared_cells_{stamp}.csv'), 'w', encoding='utf-8') as out:
        out.write('cell,signers_2024,signers_2026,postal_codes_in_cell,area_ha,below_threshold,pop_2021_est,per_1000_2024,per_1000_2026,codes\n')
        for r in sorted(with24, key=lambda k: -(mcnt24[k] + mcnt26s[k])):
            pc = pop24.get(r) or 0.0
            out.write(f'{r},{mcnt24[r]},{mcnt26s[r]},{len(members24[r])},{cells24[r].area/1e4:.1f},0,{pc:.0f},{(1000 * mcnt24[r] / pc) if pc else 0:.1f},{(1000 * mcnt26s[r] / pc) if pc else 0:.1f},{" ".join(sorted(members24[r]))}\n')
    fig, axes = plt.subplots(1, 2, figsize=(24, 11), dpi=130)
    t24 = percapita_panel(axes[0], cells24, mcnt24, pop24, fontsize=5.5, half=50.0, title=
              f'2024 petitions against the lane (release 2025-081): online from Jan 12, 2024, deposited Feb 2 and 5, {D24} days; paper sheets undated\n'
              f'{sum(n24b.values())} signatures in the borough\'s polygons; {len(with24)} shared cells, each with at least {MIN_CELL} signers of each petition and {MIN_POP} residents')
    t26 = percapita_panel(axes[1], cells24, mcnt26s, pop24, fontsize=5.5, half=50.0, title=
              f'2026 petition « Gardons la piste Terrebonne toute l\'année »: launched Oct 21, 2026, {D26} days to {asof}\n'
              f'{summary["signers_in_borough_polygons"]} signatures in the borough\'s polygons; the same {len(with24)} cells')
    sm = plt.cm.ScalarMappable(cmap=pcmap, norm=pnorm); cb = fig.colorbar(sm, ax=axes, fraction=0.015, pad=0.01, ticks=PTICKS); cb.ax.set_yticklabels(PLAB)
    cb.set_label('signers per 1,000 residents (same scale on both panels)', fontsize=11)
    fig.suptitle(f'The two petitions on rue de Terrebonne: signers per 1,000 residents, postal codes merged into one set of cells with at least {MIN_CELL} signers of each petition and {MIN_POP} residents (same cells and scale on both panels)', fontsize=13, y=0.98)
    fig.text(0.12, 0.04, CREDIT + ' ' + POPCREDIT, fontsize=8, color='0.3')
    fig.savefig(os.path.join(FIGS, f'petition_compare_2024_2026_percapita_{stamp}.png'), bbox_inches='tight'); plt.close(fig)
    summary['compare_2024'] = dict(signers_in_borough_polygons=sum(n24b.values()), moved_from_codes_without_polygon=moved24, shared_cells=len(with24), cells_with_signers=len(with24), cells_below_threshold=len(stuck24), cells_under_150_residents=t24, population_in_cells_2021=round(pop24_total))
    json.dump(summary, open(os.path.join(FIGS, f'petition_2026_merged_summary_{stamp}.json'), 'w'), indent=1)

# 2. PRIVATE comparison, six-character codes, same scale
fig, axes = plt.subplots(1, 2, figsize=(24, 11), dpi=130)
for ax, counts, title in ((axes[0], n24, f'2024 petitions against the lane (release 2025-081): online from Jan 12, 2024, deposited Feb 2 and 5, {D24} days; paper sheets undated\n{sum(v for c, v in n24.items() if c in poly)} signatures in the borough\'s polygons'),
                          (axes[1], n26, f'2026 petition « Gardons la piste Terrebonne toute l\'année »: launched Oct 21, 2026, {D26} days to {asof}\n{sum(v for c, v in n26.items() if c in poly)} signatures in the borough\'s polygons')):
    for c in codes: fill(ax, poly[c], cmap(norm(counts.get(c, 0))))
    for c, n in counts.items():
        if c not in poly and c in cent and X0 < cent[c][0] < X1 and Y0 < cent[c][1] < Y1: ax.scatter([cent[c][0]], [cent[c][1]], s=22, color=cmap(norm(n)), edgecolor='0.2', lw=0.5, zorder=4)
    frame(ax, title)
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm); cb = fig.colorbar(sm, ax=axes, fraction=0.015, pad=0.01, ticks=TICKS); cb.ax.set_yticklabels(TLAB); cb.set_label('signatures per postal code (same scale on both panels)', fontsize=11)
fig.suptitle('PRIVATE, monitoring only: the two petitions by six-character postal code, same colour scale (not small-cell redacted)', fontsize=13, color='#a00000', y=0.98)
fig.text(0.12, 0.04, CREDIT + ' Codes without a boundary: Service Objects centroids, March 2024.', fontsize=8, color='0.3')
fig.savefig(os.path.join(FIGS, f'petition_compare_2024_2026_{stamp}.png'), bbox_inches='tight'); plt.close(fig)
print(json.dumps(summary)); print('written', os.path.join(FIGS, f'petition_2026_map_merged_{stamp}.png'), '(+ _count, _percapita and petition_compare_2024_2026_percapita when the census cache exists) and', os.path.join(FIGS, f'petition_compare_2024_2026_{stamp}.png'))
if stuck: print('cells below threshold (no neighbour):', ', '.join(sorted(stuck)))
