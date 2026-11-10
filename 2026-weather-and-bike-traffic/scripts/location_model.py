#!/usr/bin/env python3
"""Location as a parameter: one model for the four counters on rue de Terrebonne, with a term for the location and
its interaction with every other term, and tests of whether each effect differs from one location to another.

The counters stand at different points of the street (King Edward at the west end, then Kensington, Draper and
Girouard towards the east and downtown) and are not the same instruments, so the location term absorbs both the
place and the instrument: the levels are not interpreted. What is tested is whether a relative effect (per cent per
degree, per cent on a rainy day, and so on) is the same at every location.

  pooled model   negative binomial, log link; count ~ location x (day type + Christmas period + two annual harmonics
                 + temperature with a change of slope at 20 °C + rain class + snowfall class + snow on the ground
                 + wind + snowfall of the day before) + a year term for each location that has more than one year;
                 standard errors clustered by date (the four counters share each day's weather)
  tests          Wald test that the location interactions of a term are all zero (the effect is the same everywhere)
  like for like  the two Telraam sensors are the same instrument read in the same window: Draper over King Edward on
                 the days valid at both, by season, with a block-bootstrap interval (the one location contrast that
                 does not mix in the instrument)

Output: derived/tables/location_tests.csv, location_effects.csv, location_draper_over_king_edward.csv
Usage: ~/.venvs/omd/bin/python scripts/location_model.py   (after models.py)
"""
import os, sys, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import optimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_lib as L, models as M
warnings.filterwarnings('ignore')
LOCS = ['west', 'loop', 'east', 'gir']; BP = 20.0; RNG = np.random.default_rng(20261110)

def main():
    fr = []
    for s in LOCS:
        d = M.load(s).copy(); d['loc'] = s; d['hinge'] = np.maximum(d.t_day - BP, 0)
        yrs = sorted(d.cyc_year.unique())
        for k, y in enumerate(yrs[1:], 2): d[f'yr_{s}_{k}'] = (d.cyc_year == y).astype(int)
        fr.append(d.reset_index())
    p = pd.concat(fr, ignore_index=True).fillna({c: 0 for f_ in fr for c in f_.columns if c.startswith('yr_')})
    ycols = [c for c in p.columns if c.startswith('yr_')]
    for c in ycols: p[c] = p[c].fillna(0)
    p['snow_c'] = p.snow_c.replace({'over10': '2to10'}); p['rain_c'] = p.rain_c
    terms = {'temperature below 20 °C (per degree)': ['t_day'], 'temperature above 20 °C (change of slope)': ['hinge'],
             'rain, under 2 mm': ["C(rain_c, Treatment('none'))[T.under2]"], 'rain, 2 to 10 mm': ["C(rain_c, Treatment('none'))[T.2to10]"], 'rain, over 10 mm': ["C(rain_c, Treatment('none'))[T.over10]"],
             'snowfall, under 2 cm': ["C(snow_c, Treatment('none'))[T.under2]"], 'snowfall, 2 cm or more': ["C(snow_c, Treatment('none'))[T.2to10]"], 'snow on the ground': ['sog_flag'],
             'wind (per 10 km/h)': ['wind_day'], 'Saturday': ["C(daytype, Treatment('weekday'))[T.sat]"], 'Sunday or holiday': ["C(daytype, Treatment('weekday'))[T.sunhol]"],
             'time of year (four harmonic terms)': ['s1', 'c1', 's2', 'c2']}
    rhs = "C(daytype, Treatment('weekday')) + xmas + s1 + c1 + s2 + c2 + t_day + hinge + C(rain_c, Treatment('none')) + C(snow_c, Treatment('none')) + sog_flag + wind_day + snow_l1"
    f = f"y ~ C(loc, Treatment('west')) * ({rhs}) + " + ' + '.join(ycols)
    def run(a): return smf.glm(f, p, family=sm.families.NegativeBinomial(alpha=a)).fit()
    g = lambda la: run(np.exp(la)).pearson_chi2 / run(np.exp(la)).df_resid - 1
    alpha = float(np.exp(optimize.brentq(g, np.log(1e-3), np.log(2.0), xtol=1e-2)))
    groups = pd.factorize(p.date)[0]
    r = smf.glm(f, p, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type='cluster', cov_kwds={'groups': groups})
    names = list(r.params.index); tests = []
    for lab, base in terms.items():
        idx = [i for i, n in enumerate(names) if n.startswith("C(loc, Treatment('west'))[T.") and any(n.endswith(':' + b) for b in base)]
        R = np.zeros((len(idx), len(names)))
        for k, i in enumerate(idx): R[k, i] = 1
        w = r.wald_test(R, scalar=True, use_f=False)
        tests.append({'term': lab, 'chi2': float(w.statistic), 'df': len(idx), 'p': float(w.pvalue)})
    # effect at each location, from the pooled model (baseline + interaction), with clustered intervals
    eff = []; cov = r.cov_params().values; par = r.params.values
    for lab, base in terms.items():
        if len(base) != 1: continue
        b = base[0]; scale = 10 if b == 'wind_day' else 1
        for s in LOCS:
            v = np.zeros(len(names)); v[names.index(b)] = 1
            if s != 'west': v[names.index(f"C(loc, Treatment('west'))[T.{s}]:{b}")] = 1
            if b == 'hinge':            # slope above the change = t_day + hinge
                v[names.index('t_day')] = 1
                if s != 'west': v[names.index(f"C(loc, Treatment('west'))[T.{s}]:t_day")] = 1
            est = scale * float(v @ par); se = scale * float(np.sqrt(v @ cov @ v))
            eff.append({'term': lab if b != 'hinge' else 'temperature above 20 °C (per degree)', 'series': s, 'pct': 100 * (np.exp(est) - 1), 'lo': 100 * (np.exp(est - 1.96 * se) - 1), 'hi': 100 * (np.exp(est + 1.96 * se) - 1)})
    T = pd.DataFrame(tests); T['n_days'] = len(p); T['alpha'] = alpha; T.round(4).to_csv(os.path.join(L.TABLES, 'location_tests.csv'), index=False)
    pd.DataFrame(eff).round(2).to_csv(os.path.join(L.TABLES, 'location_effects.csv'), index=False)
    # like for like: Draper over King Edward
    w, e = M.load('west'), M.load('east'); j = w[['y', 'winter', 'daytype']].join(e[['y']], rsuffix='_e', how='inner'); rows = []
    for lab, m in (('all days valid at both', j.index == j.index), ('winter (Nov 16 – Mar 31)', j.winter == 1), ('rest of the year', j.winter == 0), ('weekdays', j.daytype == 'weekday'), ('Saturdays, Sundays, holidays', j.daytype != 'weekday')):
        s = j[m]; n = len(s); a, b = s.y.values.astype(float), s.y_e.values.astype(float); boot = []
        for _ in range(2000):
            ix = np.concatenate([np.arange(st, min(st + 14, n)) for st in RNG.integers(0, n, int(np.ceil(n / 14)))])[:n]; boot.append(b[ix].sum() / a[ix].sum())
        rows.append({'days': lab, 'n_days': n, 'king_edward_mean': a.mean(), 'draper_mean': b.mean(), 'draper_over_king_edward': b.sum() / a.sum(), 'lo': np.percentile(boot, 2.5), 'hi': np.percentile(boot, 97.5), 'first': str(s.index.min().date()), 'last': str(s.index.max().date())})
    pd.DataFrame(rows).round(3).to_csv(os.path.join(L.TABLES, 'location_draper_over_king_edward.csv'), index=False)
    pd.set_option('display.width', 250); print(T.round(3).to_string()); print(pd.DataFrame(eff).pivot(index='term', columns='series', values='pct').round(1)[LOCS].to_string()); print(pd.DataFrame(rows).round(2).to_string())

if __name__ == '__main__': main()
