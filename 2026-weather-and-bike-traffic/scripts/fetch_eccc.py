#!/usr/bin/env python3
"""Download Environment and Climate Change Canada historical climate data for Montréal-Trudeau
(MONTREAL INTL A, climate ID 7025251, station ID 51157): daily files by year and hourly files by month,
as served by climate.weather.gc.ca (bulk CSV). Files are written unchanged to raw/eccc/.

Usage: python3 scripts/fetch_eccc.py [--start=2024-08] [--end=YYYY-MM] [--force]
A month already on disk is skipped unless it is the current or previous month (still filling) or --force.
"""
import os, sys, time, datetime as dt, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, '..', 'raw', 'eccc')
STATION = 51157
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36'
URL = 'https://climate.weather.gc.ca/climate_data/bulk_data_e.html?format=csv&stationID={s}&Year={y}&Month={m}&Day=14&timeframe={t}&submit=Download+Data'

def get(url, path):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    data = urllib.request.urlopen(req, timeout=60).read()
    if not data.startswith(b'\xef\xbb\xbf"Longitude') and not data.startswith(b'"Longitude'): raise SystemExit(f'unexpected content from {url}')
    open(path, 'wb').write(data); print('wrote', os.path.basename(path), len(data)); time.sleep(0.5)

def main(argv):
    opts = dict(a[2:].split('=', 1) for a in argv if a.startswith('--') and '=' in a); force = '--force' in argv
    today = dt.date.today()
    y0, m0 = map(int, opts.get('start', '2024-08').split('-')); y1, m1 = map(int, opts.get('end', today.strftime('%Y-%m')).split('-'))
    os.makedirs(RAW, exist_ok=True)
    recent = {(today.year, today.month), ((today.replace(day=1) - dt.timedelta(1)).year, (today.replace(day=1) - dt.timedelta(1)).month)}
    for y in range(y0, y1 + 1):
        p = os.path.join(RAW, f'en_climate_daily_QC_7025251_{y}_P1D.csv')
        if force or y >= today.year or not os.path.exists(p): get(URL.format(s=STATION, y=y, m=1, t=2), p)
    y, m = y0, m0
    while (y, m) <= (y1, m1):
        p = os.path.join(RAW, f'en_climate_hourly_QC_7025251_{m:02d}-{y}_P1H.csv')
        if force or (y, m) in recent or not os.path.exists(p): get(URL.format(s=STATION, y=y, m=m, t=1), p)
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)

if __name__ == '__main__': main(sys.argv[1:])
