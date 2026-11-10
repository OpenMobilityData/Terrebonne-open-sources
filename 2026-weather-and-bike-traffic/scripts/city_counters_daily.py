#!/usr/bin/env python3
"""Daily totals of the City of Montréal's permanent loop bicycle counters (open data « Compteurs cyclistes
permanents », boucles magnétiques, CC BY 4.0), 2025 and 2026 files as downloaded on November 7, 2026, read from
~/Terrebonne-data/third-party/montreal-opendata/. None of these counters is on rue de Terrebonne: they are used
only as a citywide reference for the response to weather.

A counter is kept when it reports on at least MIN_SHARE of the days of the common span and never has a run of more
than MAX_ZERO_RUN consecutive zero days. The reference series is the sum, over the kept counters, of each day's
passages, on days when every kept counter reports a non-zero total (so the set of counters never changes).

Output: derived/city_counters_daily.csv (date, counters, passages), derived/tables/city_counters_kept.csv
"""
import os, sys, glob
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_lib as L
MIN_SHARE, MAX_ZERO_RUN = 0.97, 2

def main():
    fs = sorted(glob.glob(os.path.join(L.CITY_DIR, 'comptage_velo_202[56]_eco_*.csv')))
    d = pd.concat([pd.read_csv(f, dtype={'id_compteur': str}, usecols=['date', 'id_compteur', 'nb_passages', 'longitude', 'latitude']) for f in fs])
    d['id_compteur'] = d.id_compteur.str.replace(r'\.0$', '', regex=True)
    loc = d.groupby('id_compteur')[['longitude', 'latitude']].first()
    day = d.groupby(['id_compteur', 'date']).nb_passages.sum().unstack(0); day.index = pd.to_datetime(day.index); day = day.sort_index()
    span = day.index; keep = []
    for c in day.columns:
        s = day[c]; ok = (s > 0)
        z = (~ok).astype(int); run = z.groupby((z != z.shift()).cumsum()).cumsum().max()
        if ok.mean() >= MIN_SHARE and run <= MAX_ZERO_RUN: keep.append(c)
    k = day[keep]; full = (k > 0).all(axis=1)
    out = pd.DataFrame({'counters': len(keep), 'passages': k[full].sum(axis=1).astype(int)}); out.index.name = 'date'
    out.to_csv(os.path.join(L.DERIVED, 'city_counters_daily.csv'))
    t = loc.loc[keep].copy(); t['days_reporting'] = (k > 0).sum().values; t['passages'] = k.sum().astype(int).values
    os.makedirs(L.TABLES, exist_ok=True); t.to_csv(os.path.join(L.TABLES, 'city_counters_kept.csv'))
    print(len(day.columns), 'counters;', len(keep), 'kept;', int(full.sum()), 'of', len(span), 'days with all kept counters;', span.min().date(), span.max().date()); print(t.to_string())

if __name__ == '__main__': main()
