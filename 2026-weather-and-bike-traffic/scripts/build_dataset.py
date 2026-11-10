#!/usr/bin/env python3
"""Build the daily analysis tables: one CSV per count series, each row a day with the count, its validity flags,
the weather of the day (ECCC Montréal-Trudeau), the calendar, day length and the City's snow-loading record.

Output: derived/daily_<series>.csv for west, east (Telraam), loop (Kensington), gir (City detector at Girouard), bixi, city; derived/weather_daily.csv;
derived/tables/coverage_by_month.csv (valid days per series and month).
Run after fetch_eccc.py, bixi_daily.py and city_counters_daily.py.  Usage: python3 scripts/build_dataset.py
"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_lib as L
BIXI_STATION = 'Grand Boulevard / de Terrebonne'

def cyc_year(idx):
    """Counting year starting August 15 (the first Telraam sensor's first day): '2024-25', '2025-26', '2026-27'."""
    y = np.where((idx.month > 8) | ((idx.month == 8) & (idx.day >= 15)), idx.year, idx.year - 1)
    return [f'{a}-{str(a + 1)[2:]}' for a in y]

def main():
    os.makedirs(L.TABLES, exist_ok=True); frames = {}
    for seg in ('west', 'east'):
        frames[seg] = L.telraam_daily(seg)
    k = L.loop_daily(); frames['loop'] = k
    frames['gir'] = L.girouard_daily()
    p = os.path.join(L.DERIVED, 'bixi_daily_terrebonne.csv')
    if os.path.exists(p):
        b = pd.read_csv(p, parse_dates=['date']); b = b[b.station == BIXI_STATION].set_index('date')
        b['bike'] = b.starts + b.ends; b['valid'] = 1; frames['bixi'] = b[['starts', 'ends', 'bike', 'valid']]
    p = os.path.join(L.DERIVED, 'city_counters_daily.csv')
    if os.path.exists(p):
        c = pd.read_csv(p, parse_dates=['date']).set_index('date'); c['bike'] = c.passages; c['valid'] = 1; frames['city'] = c
    L.weather_daily().round(2).to_csv(os.path.join(L.DERIVED, 'weather_daily.csv'))
    cov = {}
    for s, f in frames.items():
        d = L.design_frame(f); d['cyc_year'] = cyc_year(d.index); d.index.name = 'date'
        d.round(3).to_csv(os.path.join(L.DERIVED, f'daily_{s}.csv'))
        v = d[d.valid == 1]; cov[s] = v.groupby(v.index.strftime('%Y-%m')).size()
        print(f'{s}: {len(d)} days, {int(d.valid.sum())} valid, {d.index.min().date()} to {d.index.max().date()}')
    pd.DataFrame(cov).fillna(0).astype(int).rename_axis('month').to_csv(os.path.join(L.TABLES, 'coverage_by_month.csv'))

if __name__ == '__main__': main()
