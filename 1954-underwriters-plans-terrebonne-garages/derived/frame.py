"""Shared helpers: local metric frame (E,N) and the street frame (u = distance along rue de
Terrebonne from the west end of the lane, v = signed offset, +v = north side)."""
import csv, json, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, 'sheet_transforms.json')))
FR = T['frame']
def to_EN(lon, lat): return ((lon - FR['lon0']) * FR['m_lon'], (lat - FR['lat0']) * FR['m_lat'])
def from_EN(E, N): return (E / FR['m_lon'] + FR['lon0'], N / FR['m_lat'] + FR['lat0'])
NODES = [(float(r['lon']), float(r['lat']), r['cross_streets']) for r in csv.DictReader(open(os.path.join(HERE, 'terrebonne_intersections_geobase.csv')))]
P = [to_EN(lon, lat) for lon, lat, _ in NODES]
CUM = [0.0]
for a, b in zip(P, P[1:]): CUM.append(CUM[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
LENGTH = CUM[-1]
STREET_U = {}
for (lon, lat, name), u in zip(NODES, CUM):
    for n in name.split('; '):
        if n: STREET_U.setdefault(n, u)
def to_uv(E, N):
    best = None
    for i, (a, b) in enumerate(zip(P, P[1:])):
        dx, dy = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dy * dy
        t = ((E - a[0]) * dx + (N - a[1]) * dy) / L2
        tc = min(1, max(0, t)); px, py = a[0] + tc * dx, a[1] + tc * dy
        d = math.hypot(E - px, N - py)
        if best is None or d < best[0]:
            L = math.sqrt(L2); v = ((N - a[1]) * dx - (E - a[0]) * dy) / L  # +v = left of travel = north side
            best = (d, CUM[i] + t * L, v)
    return best[1], best[2]
def from_uv(u, v):
    u = min(max(u, -50), LENGTH + 50)
    i = max(0, min(len(P) - 2, next((k for k in range(len(CUM) - 1) if CUM[k + 1] >= u), len(P) - 2)))
    a, b = P[i], P[i + 1]; dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
    t = (u - CUM[i]) / L; ex, ey = dx / L, dy / L
    return a[0] + t * dx - v * ey, a[1] + t * dy + v * ex
