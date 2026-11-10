#!/usr/bin/env python3
"""Daily BIXI trips at the stations along rue de Terrebonne, from BIXI Montréal's open trip history.

Source: https://bixi.com/en/open-data/ (yearly ZIP files; the City's open-data portal lists the dataset under
CC BY 4.0, « la paternité des données doit être attribuée à BIXI Montréal »). The ZIP files are read from
~/Terrebonne-data/third-party/bixi/ and are not redistributed here; only the daily totals below are published.

A station is kept when it lies within RADIUS metres of the lane's axis (west end to Girouard). For each station and
day (local date of the trip's start, America/Toronto): trips starting there, trips ending there. Also written: the
whole system's trips per day (a citywide reference). A day on which a station records no trip does not appear:
BIXI does not publish station service dates, so absence is not a zero.

Output: derived/bixi_daily_terrebonne.csv, derived/bixi_daily_system.csv, derived/tables/bixi_stations.csv
Usage: python3 scripts/bixi_daily.py
"""
import os, sys, glob, zipfile, math, collections
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_lib as L
AXIS = [(45.45974, -73.64080), (45.46354, -73.63784), (45.46674, -73.63524), (45.46990, -73.63231), (45.47054, -73.63175), (45.47334, -73.62936), (45.47405, -73.62872), (45.47833, -73.62487)]
RADIUS = 120.0
KX, KY = 111200 * math.cos(math.radians(45.47)), 111200

def dist_to_axis(lat, lon):
    x, y = lon * KX, lat * KY; best = np.full(len(x), 1e9)
    for (a, b), (c, d) in zip(AXIS[:-1], AXIS[1:]):
        ax, ay, bx, by = b * KX, a * KY, d * KX, c * KY; vx, vy = bx - ax, by - ay
        t = np.clip(((x - ax) * vx + (y - ay) * vy) / (vx * vx + vy * vy), 0, 1)
        best = np.minimum(best, np.hypot(x - ax - t * vx, y - ay - t * vy))
    return best

def main():
    starts, ends, system = collections.Counter(), collections.Counter(), collections.Counter(); stations = {}
    for z in sorted(glob.glob(os.path.join(L.BIXI_DIR, 'DonneesOuvertes20*.zip'))):
        zf = zipfile.ZipFile(z); name = zf.namelist()[0]; print(os.path.basename(z), flush=True)
        for ch in pd.read_csv(zf.open(name), chunksize=2_000_000, usecols=['STARTSTATIONNAME', 'STARTSTATIONLATITUDE', 'STARTSTATIONLONGITUDE', 'ENDSTATIONNAME', 'ENDSTATIONLATITUDE', 'ENDSTATIONLONGITUDE', 'STARTTIMEMS']):
            day = pd.to_datetime(ch.STARTTIMEMS, unit='ms', utc=True).dt.tz_convert('America/Toronto').dt.strftime('%Y-%m-%d')
            for d, n in day.value_counts().items(): system[d] += int(n)
            for side, acc in (('START', starts), ('END', ends)):
                la, lo = ch[f'{side}STATIONLATITUDE'].astype(float), ch[f'{side}STATIONLONGITUDE'].astype(float)
                box = la.between(45.455, 45.482) & lo.between(-73.650, -73.618)
                if not box.any(): continue
                sub = ch[box]; dd = dist_to_axis(la[box].values, lo[box].values); keep = dd <= RADIUS
                if not keep.any(): continue
                s = sub[keep]; nm = s[f'{side}STATIONNAME']
                for (n_, d_), c in pd.Series(1, index=pd.MultiIndex.from_arrays([nm.values, day[box][keep].values])).groupby(level=[0, 1]).sum().items(): acc[(n_, d_)] += int(c)
                for n_, a, b, m in zip(nm.values, la[box][keep].values, lo[box][keep].values, dd[keep]): stations.setdefault(n_, (round(a, 5), round(b, 5), round(float(m))))
    keys = sorted(set(starts) | set(ends), key=lambda k: (k[0], k[1]))
    pd.DataFrame([{'station': k[0], 'date': k[1], 'starts': starts[k], 'ends': ends[k]} for k in keys]).to_csv(os.path.join(L.DERIVED, 'bixi_daily_terrebonne.csv'), index=False)
    pd.DataFrame([{'date': d, 'trips': n} for d, n in sorted(system.items())]).to_csv(os.path.join(L.DERIVED, 'bixi_daily_system.csv'), index=False)
    t = pd.DataFrame([{'station': n, 'latitude': v[0], 'longitude': v[1], 'metres_from_lane_axis': v[2],
                       'first_day': min(k[1] for k in keys if k[0] == n), 'last_day': max(k[1] for k in keys if k[0] == n),
                       'days_with_trips': sum(1 for k in keys if k[0] == n), 'starts': sum(starts[k] for k in keys if k[0] == n), 'ends': sum(ends[k] for k in keys if k[0] == n)} for n, v in sorted(stations.items())])
    os.makedirs(L.TABLES, exist_ok=True); t.to_csv(os.path.join(L.TABLES, 'bixi_stations.csv'), index=False); print(t.to_string())

if __name__ == '__main__': main()
