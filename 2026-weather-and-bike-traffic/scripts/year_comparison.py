#!/usr/bin/env python3
"""Year-to-year comparison in three steps, so that the part played by the weather is visible.

For each series with more than one counting year (from August 15) and each later year against the first:
  step 1  no model: the same calendar dates, valid in both years; ratio of the two totals (interval: bootstrap over
          14-day blocks of dates). This is the plain comparison; it accounts for downtime (only dates valid in both
          years) but not for a colder, wetter or snowier year.
  step 2  model with day type and time of year, without any weather term
  step 3  the main model: step 2 plus daytime temperature, rain, snowfall, snow on the ground, wind
and, on the common dates of step 1, how the weather differed between the two years.
The year terms of steps 2 and 3 use the model's years (a year with fewer than 60 days is merged with its neighbour).

Output: derived/tables/year_comparison_steps.csv, derived/tables/year_comparison_weather.csv
Usage: ~/.venvs/omd/bin/python scripts/year_comparison.py   (after models.py)
"""
import os, sys, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_lib as L, models as M
RNG = np.random.default_rng(20261110); MIN_COMMON = 30

def raw_frame(series):
    d = pd.read_csv(os.path.join(L.DERIVED, f'daily_{series}.csv'), parse_dates=['date']).set_index('date')
    if series == 'bixi': d = d[[(4, 15) <= (x.month, x.day) <= (11, 15) for x in d.index]]
    d = d[d.valid == 1].copy(); d['y'] = d.bike; d['md'] = d.index.strftime('%m-%d')
    return d

def main():
    N = json.load(open(os.path.join(L.DERIVED, 'numbers.json'))); steps, wx = [], []
    for s in ('west', 'east', 'bixi', 'city'):
        raw = raw_frame(s); years = sorted(raw.cyc_year.unique()); ref = years[0]
        d = M.load(s); b = N[s]['bp']; alpha = N[s]['alpha']
        f3 = M.hinge_formula(d, b); f2 = f"y ~ {M.CALf(d)}{M.year_term(d)} + {M.SEAS}"
        r2, r3 = M.fit_nb(f2, d, alpha=alpha), M.fit_nb(f3, d, alpha=alpha)
        for y in years[1:]:
            a, c = raw[raw.cyc_year == ref].set_index('md'), raw[raw.cyc_year == y].set_index('md')
            common = sorted(set(a.index) & set(c.index))
            row = {'series': s, 'year': y, 'reference': ref, 'common_dates': len(common)}
            if len(common) >= MIN_COMMON:
                ya, yc = a.loc[common, 'y'].values.astype(float), c.loc[common, 'y'].values.astype(float); n = len(common)
                # blocks of 14 consecutive common dates in calendar order from August 15
                order = np.argsort([(pd.Timestamp('2001-' + m) - pd.Timestamp('2001-08-15')).days % 365 for m in common]); ya, yc = ya[order], yc[order]
                boot = []
                for _ in range(2000):
                    ix = np.concatenate([np.arange(st, min(st + 14, n)) for st in RNG.integers(0, n, int(np.ceil(n / 14)))])[:n]
                    boot.append(yc[ix].sum() / ya[ix].sum())
                row.update({'step1_pct': 100 * (yc.sum() / ya.sum() - 1), 'step1_lo': 100 * (np.percentile(boot, 2.5) - 1), 'step1_hi': 100 * (np.percentile(boot, 97.5) - 1),
                            'first_common': min(common, key=lambda m: (pd.Timestamp('2001-' + m) - pd.Timestamp('2001-08-15')).days % 365), 'mean_ref': ya.mean(), 'mean_year': yc.mean()})
                w = {'series': s, 'year': y, 'reference': ref, 'common_dates': n}
                for lab, col, fn in (('daytime_temp_mean', 't_day', 'mean'), ('rain_days', 'rain', lambda v: (v >= 0.2).sum()), ('rain_mm', 'rain', 'sum'), ('snowfall_days', 'snow', lambda v: (v >= 0.2).sum()),
                                     ('snowfall_cm', 'snow', 'sum'), ('snow_on_ground_days', 'sog', lambda v: (v >= 1).sum()), ('days_below_minus10', 't_day', lambda v: (v < -10).sum())):
                    w[lab + '_ref'] = float(a.loc[common, col].agg(fn)); w[lab + '_year'] = float(c.loc[common, col].agg(fn))
                wx.append(w)
            k = f'C(cyc_year)[T.{y}]'
            for step, r in (('step2', r2), ('step3', r3)):
                if k in r.params.index:
                    e = M.rr(r, k); row.update({f'{step}_pct': e['pct'], f'{step}_lo': e['lo'], f'{step}_hi': e['hi']})
            row['model_days_in_year'] = int((d.cyc_year == y).sum())
            steps.append(row)
    pd.DataFrame(steps).round(2).to_csv(os.path.join(L.TABLES, 'year_comparison_steps.csv'), index=False)
    pd.DataFrame(wx).round(1).to_csv(os.path.join(L.TABLES, 'year_comparison_weather.csv'), index=False)
    pd.set_option('display.width', 250); print(pd.DataFrame(steps).round(1).to_string()); print(pd.DataFrame(wx).round(1).T.to_string())

if __name__ == '__main__': main()
