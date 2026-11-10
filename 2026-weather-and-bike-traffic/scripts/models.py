#!/usr/bin/env python3
"""Statistical models of daily (and, for the loop, hourly) bicycle counts against weather, daylight and snow.

Every model is fitted separately to each series; series are compared only through relative effects (rate ratios),
never through levels. Method, in order:

  M-main     negative binomial regression, log link (statsmodels GLM; the dispersion alpha is chosen so that the
             Pearson chi-square equals the residual degrees of freedom), standard errors robust to
             heteroskedasticity and autocorrelation (Newey-West, 7 lags on the series' own row order).
             count ~ day type + Christmas period + counting year + two annual harmonics
                     + daytime temperature (a line with one estimated change of slope)
                     + rain class + snowfall class + snow on the ground + daytime wind + snowfall of the day before
  M-spline   the same with temperature as a natural cubic spline (5 df): the shape, without assuming a threshold
  breakpoint profile deviance over a grid; interval from a moving-block bootstrap (14-day blocks)
  M-chill    the same with the daytime wind-chill index in place of air temperature (compared by AIC)
  blocks     deviance explained by calendar-and-season terms alone, weather alone, both (shared and unique parts)
  M-within   harmonics and year replaced by one fixed effect per calendar month: weather effects from the
             day-to-day variation inside a month only
  M-lags     winter days (Nov 16 – Mar 31): snowfall of the day and of each of the seven days before, snow loading
  events     snowfall episodes (consecutive days with at least 2 cm merged): observed count over the count expected
             from temperature, calendar and season, from 3 days before to 7 days after the episode's first day
  hourly     Kensington loop, eastbound, hours 06:00–21:59: count ~ hour x day type + month + temperature spline
             + rain/snow observed in the hour + darkness (sun below the horizon at mid-hour)
  cv         leave-one-calendar-month-out prediction error of M-main

Outputs: derived/tables/*.csv and derived/numbers.json (every figure quoted in the note and the deck).
Usage: ~/.venvs/omd/bin/python scripts/models.py [--boot=300]
"""
import os, sys, json, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import optimize, stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wx_lib as L
warnings.filterwarnings('ignore')
RNG = np.random.default_rng(20261110)
GRID = np.arange(-8.0, 26.01, 0.5)
RAIN_BINS, RAIN_LAB = [-1, 0.0, 2.0, 10.0, 1e9], ['none', 'under2', '2to10', 'over10']
SNOW_BINS, SNOW_LAB = [-1, 0.0, 2.0, 10.0, 1e9], ['none', 'under2', '2to10', 'over10']
SEAS = 's1 + c1 + s2 + c2'
MIN_YEAR_DAYS = 60
MIN_CLASS = 5   # a class or flag with fewer days than this is merged with its neighbour or left out (BIXI's season has no snow)

def CALf(d): return "C(daytype, Treatment('weekday'))" + (' + xmas' if d.xmas.sum() >= MIN_CLASS else '')
def WXf(d):
    t = ["C(rain_c, Treatment('none'))"]
    if d.snow_c.nunique() > 1: t.append("C(snow_c, Treatment('none'))")
    if MIN_CLASS <= d.sog_flag.sum() <= len(d) - MIN_CLASS: t.append('sog_flag')
    t.append('wind_day')
    if (d.snow_l1 > 0).sum() >= MIN_CLASS: t.append('snow_l1')
    return ' + '.join(t)

def merge_sparse(c, order):
    """Merge a class with fewer than MIN_CLASS days into the class below it (over10 -> 2to10 -> under2 -> none)."""
    c = c.copy()
    for hi, lo in zip(order[:0:-1], order[-2::-1]):
        if 0 < (c == hi).sum() < MIN_CLASS: c[c == hi] = lo
    return c

def load(series):
    d = pd.read_csv(os.path.join(L.DERIVED, f'daily_{series}.csv'), parse_dates=['date']).set_index('date')
    if series == 'loop':
        d = d[d.valid_eb == 1].copy(); d['y'] = d.eb          # eastbound channel, hourly workbook (2026-300), to May 10, 2026
    elif series == 'bixi':
        d = d[[(4, 15) <= (x.month, x.day) <= (11, 15) for x in d.index]].copy(); d['y'] = d.bike   # the regular BIXI season
    else:
        d = d[d.valid == 1].copy(); d['y'] = d.bike
    d = d.dropna(subset=['y', 't_day', 'rain', 'snow', 'snow_l1', 'wind_day'])
    w = 2 * np.pi * d.doy / 365.25
    d['s1'], d['c1'], d['s2'], d['c2'] = np.sin(w), np.cos(w), np.sin(2 * w), np.cos(2 * w)
    d['rain_c'] = merge_sparse(pd.cut(d.rain, RAIN_BINS, labels=RAIN_LAB).astype(str), RAIN_LAB); d['snow_c'] = merge_sparse(pd.cut(d.snow, SNOW_BINS, labels=SNOW_LAB).astype(str), SNOW_LAB)
    d['sog_flag'] = (d.sog >= 1).astype(int); d['ym'] = d.index.strftime('%Y-%m')
    d['logdaylen'] = np.log(d.daylen)
    # a counting year with fewer than MIN_YEAR_DAYS days in the series is merged with its neighbour (no separate year term)
    yrs = sorted(d.cyc_year.unique())
    for i, y in enumerate(yrs):
        if (d.cyc_year == y).sum() < MIN_YEAR_DAYS and len(yrs) > 1:
            d.loc[d.cyc_year == y, 'cyc_year'] = yrs[i + 1] if i == 0 else yrs[i - 1]
    return d

def year_term(d): return ' + C(cyc_year)' if d.cyc_year.nunique() > 1 else ''

def fit_nb(formula, d, alpha=None, hac=True):
    """NB2 GLM; alpha solved so that Pearson chi2 / df_resid = 1 unless given."""
    def run(a, robust=False):
        m = smf.glm(formula, d, family=sm.families.NegativeBinomial(alpha=a))
        return m.fit(cov_type='HAC', cov_kwds={'maxlags': 7}) if robust else m.fit()
    if alpha is None:
        f = lambda la: run(np.exp(la)).pearson_chi2 / run(np.exp(la)).df_resid - 1
        try: alpha = float(np.exp(optimize.brentq(f, np.log(1e-4), np.log(5.0), xtol=1e-3)))
        except ValueError: alpha = 1e-4 if f(np.log(1e-4)) < 0 else 5.0
    r = run(alpha, robust=hac); r.alpha_used = alpha
    return r

def aic_nb(r, d):
    """AIC from the negative binomial log-likelihood at the alpha used (one extra parameter for alpha)."""
    return -2 * r.llf + 2 * (len(r.params) + 1)

def rr(r, name):
    b, se = r.params[name], r.bse[name]
    return {'pct': 100 * (np.exp(b) - 1), 'lo': 100 * (np.exp(b - 1.96 * se) - 1), 'hi': 100 * (np.exp(b + 1.96 * se) - 1), 'p': float(r.pvalues[name])}

def hinge_formula(d, b, tvar='t_day', extra=''):
    d['hinge'] = np.maximum(d[tvar] - b, 0)
    return f'y ~ {CALf(d)}{year_term(d)} + {SEAS} + {tvar} + hinge + {WXf(d)}{extra}'

def profile(d, tvar='t_day', alpha=None, grid=GRID):
    dev = []
    for b in grid:
        f = hinge_formula(d, b, tvar); m = smf.glm(f, d, family=sm.families.NegativeBinomial(alpha=alpha)).fit(); dev.append(m.deviance)
    return np.array(dev)

def block_bootstrap(d, alpha, n, block=14):
    """Moving-block bootstrap of the breakpoint and of the two slopes (blocks of consecutive rows)."""
    out = []; N = len(d); starts = np.arange(0, N - block + 1); k = int(np.ceil(N / block)); coarse = np.arange(-8.0, 26.01, 1.0)
    for _ in range(n):
        ix = np.concatenate([np.arange(s, s + block) for s in RNG.choice(starts, k)])[:N]; s = d.iloc[ix].copy()
        try:
            dev = profile(s, alpha=alpha, grid=coarse); b = coarse[int(np.argmin(dev))]
            m = smf.glm(hinge_formula(s, b), s, family=sm.families.NegativeBinomial(alpha=alpha)).fit()
            out.append((b, m.params['t_day'], m.params['t_day'] + m.params['hinge']))
        except Exception: pass
    return np.array(out)

def design_rows(res, frame):
    """Design-matrix rows for new data, under the fitted model's own coding (spline knots included)."""
    spec = res.model.data.model_spec
    if hasattr(spec, 'get_model_matrix'): return np.asarray(getattr(spec, 'rhs', spec).get_model_matrix(frame), dtype=float)
    from patsy import dmatrix
    return np.asarray(dmatrix(spec, frame), dtype=float)

def dev_explained(formula, d, alpha):
    m = smf.glm(formula, d, family=sm.families.NegativeBinomial(alpha=alpha)).fit()
    n = smf.glm('y ~ 1', d, family=sm.families.NegativeBinomial(alpha=alpha)).fit()
    return 1 - m.deviance / n.deviance

def main(argv):
    opts = dict(a[2:].split('=', 1) for a in argv if a.startswith('--') and '=' in a); nboot = int(opts.get('boot', 300))
    os.makedirs(L.TABLES, exist_ok=True)
    N = {}; coef_rows, curve_rows, prof_rows, block_rows, lag_rows, event_rows, cv_rows, yoy_rows, band_rows = [], [], [], [], [], [], [], [], []
    series = [s for s in ('west', 'east', 'loop', 'bixi', 'city') if os.path.exists(os.path.join(L.DERIVED, f'daily_{s}.csv'))]
    for s in series:
        d = load(s); n = N[s] = {'n_days': int(len(d)), 'first': str(d.index.min().date()), 'last': str(d.index.max().date()), 'mean_count': float(d.y.mean())}
        print(f'--- {s}: {len(d)} days', flush=True)
        # spline model (also fixes alpha for the profile and the bootstrap)
        fs = f'y ~ {CALf(d)}{year_term(d)} + {SEAS} + cr(t_day, df=5) + {WXf(d)}'
        rs = fit_nb(fs, d); alpha = rs.alpha_used; n['alpha'] = alpha
        tg = np.arange(np.floor(d.t_day.quantile(0.01)), np.ceil(d.t_day.quantile(0.99)) + 0.1, 0.5)
        ref = d.iloc[[0]].copy(); base = pd.concat([ref] * len(tg), ignore_index=True); base['t_day'] = tg
        base20 = ref.copy(); base20['t_day'] = 20.0
        X, X0 = design_rows(rs, base), design_rows(rs, base20); D = X - X0
        eta = D @ rs.params.values; se = np.sqrt(np.einsum('ij,jk,ik->i', D, rs.cov_params().values, D))
        for t, e, q in zip(tg, eta, se): curve_rows.append({'series': s, 'temp': t, 'index_20C_100': 100 * np.exp(e), 'lo': 100 * np.exp(e - 1.96 * q), 'hi': 100 * np.exp(e + 1.96 * q)})
        # breakpoint
        dev = profile(d, alpha=alpha); b = float(GRID[int(np.argmin(dev))])
        for g, v in zip(GRID, dev): prof_rows.append({'series': s, 'breakpoint': g, 'deviance': v, 'delta': v - dev.min()})
        rm = fit_nb(hinge_formula(d, b), d, alpha=alpha); n['aic_temp'] = float(aic_nb(rm, d))
        r0 = fit_nb(f'y ~ {CALf(d)}{year_term(d)} + {SEAS} + t_day + {WXf(d)}', d, alpha=alpha); n['aic_linear'] = float(aic_nb(r0, d))
        n['aic_spline'] = float(aic_nb(fit_nb(fs, d, alpha=alpha), d))
        bs = block_bootstrap(d, alpha, nboot) if nboot else np.empty((0, 3))
        lo_s = rm.params['t_day']; hi_s = rm.params['t_day'] + rm.params['hinge']
        cv = rm.cov_params(); se_hi = np.sqrt(cv.loc['t_day', 't_day'] + cv.loc['hinge', 'hinge'] + 2 * cv.loc['t_day', 'hinge'])
        n.update({'bp': b, 'bp_lo': float(np.percentile(bs[:, 0], 2.5)) if len(bs) else None, 'bp_hi': float(np.percentile(bs[:, 0], 97.5)) if len(bs) else None, 'n_boot': int(len(bs)),
                  'slope_cold_pct': 100 * (np.exp(lo_s) - 1), 'slope_cold_lo': 100 * (np.exp(lo_s - 1.96 * rm.bse['t_day']) - 1), 'slope_cold_hi': 100 * (np.exp(lo_s + 1.96 * rm.bse['t_day']) - 1),
                  'slope_warm_pct': 100 * (np.exp(hi_s) - 1), 'slope_warm_lo': 100 * (np.exp(hi_s - 1.96 * se_hi) - 1), 'slope_warm_hi': 100 * (np.exp(hi_s + 1.96 * se_hi) - 1),
                  'hinge_p': float(rm.pvalues['hinge']), 'dev_expl_main': float(1 - rm.deviance / rm.null_deviance)})
        if len(bs):
            n.update({'slope_cold_boot_lo': 100 * (np.exp(np.percentile(bs[:, 1], 2.5)) - 1), 'slope_cold_boot_hi': 100 * (np.exp(np.percentile(bs[:, 1], 97.5)) - 1),
                      'slope_warm_boot_lo': 100 * (np.exp(np.percentile(bs[:, 2], 2.5)) - 1), 'slope_warm_boot_hi': 100 * (np.exp(np.percentile(bs[:, 2], 97.5)) - 1)})
        # does the slope change again in the cold? one more change of slope at 0 °C added to the main model
        d['cold0'] = np.minimum(d.t_day, 0.0)
        r2 = fit_nb(hinge_formula(d, b) + ' + cold0', d, alpha=alpha); hinge_formula(d, b)
        cv2 = r2.cov_params(); below = r2.params['t_day'] + r2.params['cold0']; se_b = np.sqrt(cv2.loc['t_day', 't_day'] + cv2.loc['cold0', 'cold0'] + 2 * cv2.loc['t_day', 'cold0'])
        n.update({'cold0_p': float(r2.pvalues['cold0']), 'days_below_0': int((d.t_day < 0).sum()), 'slope_below0_pct': 100 * (np.exp(below) - 1), 'slope_below0_lo': 100 * (np.exp(below - 1.96 * se_b) - 1), 'slope_below0_hi': 100 * (np.exp(below + 1.96 * se_b) - 1),
                  'slope_0_to_bp_pct': 100 * (np.exp(r2.params['t_day']) - 1), 'slope_0_to_bp_lo': 100 * (np.exp(r2.params['t_day'] - 1.96 * r2.bse['t_day']) - 1), 'slope_0_to_bp_hi': 100 * (np.exp(r2.params['t_day'] + 1.96 * r2.bse['t_day']) - 1)})
        # coefficient table (main model)
        names = {"C(rain_c, Treatment('none'))[T.under2]": 'rain_under2', "C(rain_c, Treatment('none'))[T.2to10]": 'rain_2to10', "C(rain_c, Treatment('none'))[T.over10]": 'rain_over10',
                 "C(snow_c, Treatment('none'))[T.under2]": 'snow_under2', "C(snow_c, Treatment('none'))[T.2to10]": 'snow_2to10', "C(snow_c, Treatment('none'))[T.over10]": 'snow_over10',
                 'sog_flag': 'snow_on_ground', 'snow_l1': 'snow_yesterday_per_cm', "C(daytype, Treatment('weekday'))[T.sat]": 'saturday', "C(daytype, Treatment('weekday'))[T.sunhol]": 'sunday_holiday', 'xmas': 'christmas_period'}
        for k, lab in names.items():
            if k in rm.params.index:
                e = rr(rm, k); nobs = int((d.rain_c == k.split('T.')[1][:-1]).sum()) if 'rain_c' in k else int((d.snow_c == k.split('T.')[1][:-1]).sum()) if 'snow_c' in k else int(d.sog_flag.sum()) if k == 'sog_flag' else ''
                coef_rows.append({'series': s, 'model': 'main', 'term': lab, 'days': nobs, **e})
        bw, sw = rm.params['wind_day'], rm.bse['wind_day']
        coef_rows.append({'series': s, 'model': 'main', 'term': 'wind_per_10kmh', 'days': '', 'pct': 100 * (np.exp(10 * bw) - 1), 'lo': 100 * (np.exp(10 * (bw - 1.96 * sw)) - 1), 'hi': 100 * (np.exp(10 * (bw + 1.96 * sw)) - 1), 'p': float(rm.pvalues['wind_day'])})
        for k in rm.params.index:
            if k.startswith('C(cyc_year)'):
                e = rr(rm, k); yoy_rows.append({'series': s, 'year': k.split('T.')[1][:-1], 'reference': sorted(d.cyc_year.unique())[0], 'days': int((d.cyc_year == k.split('T.')[1][:-1]).sum()), **e})
        # wind chill in place of air temperature
        dc = d.copy(); devc = profile(dc, tvar='chill_day', alpha=alpha); bc = float(GRID[int(np.argmin(devc))])
        rc = fit_nb(hinge_formula(dc, bc, 'chill_day').replace(' + wind_day', ''), dc, alpha=alpha)
        rt = fit_nb(hinge_formula(d, b).replace(' + wind_day', ''), d, alpha=alpha)
        n.update({'bp_chill': bc, 'aic_chill': float(aic_nb(rc, dc)), 'aic_temp_nowind': float(aic_nb(rt, d)), 'corr_temp_chill': float(d.t_day.corr(d.chill_day))})
        hinge_formula(d, b)
        # blocks: calendar/season, weather, both
        f_cal = f'y ~ {CALf(d)}{year_term(d)} + {SEAS}'; f_wx = f'y ~ t_day + hinge + {WXf(d)}'; f_all = hinge_formula(d, b)
        r_c, r_w, r_a = dev_explained(f_cal, d, alpha), dev_explained(f_wx, d, alpha), dev_explained(f_all, d, alpha)
        r_dl = dev_explained(f'y ~ {CALf(d)}{year_term(d)} + logdaylen', d, alpha)
        block_rows.append({'series': s, 'calendar_season_alone': r_c, 'weather_alone': r_w, 'both': r_a, 'unique_calendar_season': r_a - r_w, 'unique_weather': r_a - r_c, 'shared': r_c + r_w - r_a, 'calendar_daylength_alone': r_dl})
        # within-month model
        if d.ym.nunique() > 3:
            fw = f'y ~ {CALf(d)} + C(ym) + t_day + hinge + {WXf(d)}'; rw = fit_nb(fw, d, alpha=alpha)
            lo_w = rw.params['t_day']; hi_w = lo_w + rw.params['hinge']; cw = rw.cov_params(); se_w = np.sqrt(cw.loc['t_day', 't_day'] + cw.loc['hinge', 'hinge'] + 2 * cw.loc['t_day', 'hinge'])
            n.update({'within_cold_pct': 100 * (np.exp(lo_w) - 1), 'within_cold_lo': 100 * (np.exp(lo_w - 1.96 * rw.bse['t_day']) - 1), 'within_cold_hi': 100 * (np.exp(lo_w + 1.96 * rw.bse['t_day']) - 1),
                      'within_warm_pct': 100 * (np.exp(hi_w) - 1), 'within_warm_lo': 100 * (np.exp(hi_w - 1.96 * se_w) - 1), 'within_warm_hi': 100 * (np.exp(hi_w + 1.96 * se_w) - 1)})
            for k, lab in names.items():
                if k in rw.params.index and ('rain' in lab or 'snow' in lab): coef_rows.append({'series': s, 'model': 'within_month', 'term': lab, 'days': '', **rr(rw, k)})
        # temperature bands: observed mean count by 5-degree band, dry days without snow on the ground, weekdays (descriptive)
        dd = d[(d.daytype == 'weekday')].copy(); dd['band'] = (np.floor(dd.t_day / 5) * 5).astype(int)
        for (bnd, wet), g in dd.groupby(['band', dd.rain_c.ne('none') | dd.snow_c.ne('none')]):
            band_rows.append({'series': s, 'band_from': bnd, 'band_to': bnd + 5, 'precipitation': 'yes' if wet else 'no', 'weekdays': len(g), 'mean_count': g.y.mean(), 'median_count': g.y.median()})
        # leave-one-month-out
        f_main = hinge_formula(d, b); err, obs, pred = [], [], []
        for ym, g in d.groupby('ym'):
            tr = d[d.ym != ym]
            if tr.cyc_year.nunique() < d.cyc_year.nunique() or len(g) < 5: continue
            try:
                m = smf.glm(f_main, tr, family=sm.families.NegativeBinomial(alpha=alpha)).fit(); p = m.predict(g)
                obs += list(g.y); pred += list(p)
            except Exception: pass
        if obs:
            obs, pred = np.array(obs), np.array(pred); ins = rm.predict(d)
            cv_rows.append({'series': s, 'days_predicted': len(obs), 'median_abs_pct_error_out': 100 * float(np.median(np.abs(pred - obs) / np.maximum(obs, 1))), 'r2_log_out': float(np.corrcoef(np.log1p(obs), np.log1p(pred))[0, 1] ** 2),
                            'median_abs_pct_error_in': 100 * float(np.median(np.abs(ins - d.y) / np.maximum(d.y, 1))), 'r2_log_in': float(np.corrcoef(np.log1p(d.y), np.log1p(ins))[0, 1] ** 2)})
        # winter lag model and episodes
        wd = d[d.winter == 1].copy()
        if s in ('west', 'east', 'loop') and len(wd) > 80:
            wd = wd.dropna(subset=[f'snow_l{k}' for k in range(1, 8)])
            lagf = f"y ~ {CALf(wd)}{year_term(wd)} + t_day + C(rain_c, Treatment('none')) + sog_flag + wind_day + snow + " + ' + '.join(f'snow_l{k}' for k in range(1, 8)) + ' + loading'
            rl = fit_nb(lagf, wd); n['winter_days'] = int(len(wd)); n['winter_loading_days'] = int(wd.loading.sum()); n['winter_alpha'] = rl.alpha_used
            for k in range(0, 8):
                nm = 'snow' if k == 0 else f'snow_l{k}'; bb, ss = rl.params[nm], rl.bse[nm]
                lag_rows.append({'series': s, 'lag_days': k, 'pct_per_5cm': 100 * (np.exp(5 * bb) - 1), 'lo': 100 * (np.exp(5 * (bb - 1.96 * ss)) - 1), 'hi': 100 * (np.exp(5 * (bb + 1.96 * ss)) - 1), 'p': float(rl.pvalues[nm])})
            coef_rows.append({'series': s, 'model': 'winter_lags', 'term': 'loading_day_CDN301', 'days': int(wd.loading.sum()), **rr(rl, 'loading')})
            coef_rows.append({'series': s, 'model': 'winter_lags', 'term': 'temp_per_degree', 'days': int(len(wd)), **rr(rl, 't_day')})
            # episodes: expected count from a winter model without any snow term
            ef = f"y ~ {CALf(wd)}{year_term(wd)} + t_day + C(rain_c, Treatment('none')) + wind_day"
            re_ = fit_nb(ef, wd, alpha=rl.alpha_used); ratio = (wd.y / re_.predict(wd))
            wx = pd.read_csv(os.path.join(L.DERIVED, 'weather_daily.csv'), parse_dates=['date']).set_index('date'); sn = wx.snow.fillna(0) >= 2
            ep = []; run = None
            for day, v in sn.items():
                if v and run is None: run = [day, day]
                elif v: run[1] = day
                elif run is not None and (day - run[1]).days > 1: ep.append(tuple(run)); run = None
            for a, z in ep:
                tot = float(wx.snow[a:z].sum()); cls = '2 to 10 cm' if tot < 10 else '10 cm or more'
                for off in range(-3, 8):
                    day = a + pd.Timedelta(days=off)
                    if day in ratio.index: event_rows.append({'series': s, 'episode_start': str(a.date()), 'episode_end': str(z.date()), 'snow_cm': tot, 'class': cls, 'offset': off, 'ratio': float(ratio[day])})
    # hourly loop model
    hn = hourly_loop(); N['hourly'] = hn
    T = L.TABLES
    pd.DataFrame(coef_rows).round(4).to_csv(os.path.join(T, 'effects_main.csv'), index=False)
    pd.DataFrame(curve_rows).round(3).to_csv(os.path.join(T, 'temperature_curve.csv'), index=False)
    pd.DataFrame(prof_rows).round(3).to_csv(os.path.join(T, 'breakpoint_profile.csv'), index=False)
    pd.DataFrame(block_rows).round(4).to_csv(os.path.join(T, 'deviance_blocks.csv'), index=False)
    pd.DataFrame(lag_rows).round(3).to_csv(os.path.join(T, 'snow_lags_winter.csv'), index=False)
    ev = pd.DataFrame(event_rows); ev.round(4).to_csv(os.path.join(T, 'snow_episodes_daily.csv'), index=False)
    if len(ev):
        g = ev.groupby(['series', 'class', 'offset']).ratio.agg(['size', 'median', 'mean', lambda x: x.quantile(0.25), lambda x: x.quantile(0.75)]).reset_index()
        g.columns = ['series', 'class', 'offset', 'episodes', 'median_ratio', 'mean_ratio', 'q25', 'q75']; g.round(3).to_csv(os.path.join(T, 'snow_episodes_summary.csv'), index=False)
    pd.DataFrame(cv_rows).round(3).to_csv(os.path.join(T, 'cross_validation.csv'), index=False)
    pd.DataFrame(yoy_rows).round(3).to_csv(os.path.join(T, 'year_terms.csv'), index=False)
    pd.DataFrame(band_rows).round(1).to_csv(os.path.join(T, 'temperature_bands_weekdays.csv'), index=False)
    bk = [{'series': s, **{k: v for k, v in N[s].items()}} for s in series]; pd.DataFrame(bk).round(4).to_csv(os.path.join(T, 'model_summary.csv'), index=False)
    json.dump(N, open(os.path.join(L.DERIVED, 'numbers.json'), 'w'), indent=1, default=float)
    print(pd.DataFrame(bk).T.to_string()); print(pd.DataFrame(block_rows).round(3).to_string()); print(pd.DataFrame(coef_rows).round(1).to_string()); print(pd.DataFrame(yoy_rows).round(1).to_string()); print(pd.DataFrame(cv_rows).round(2).to_string()); print(pd.DataFrame(lag_rows).round(1).to_string()); print(json.dumps(hn, indent=1, default=float))

def hourly_loop():
    """Hourly model of the loop's eastbound channel: the effect of darkness at a given clock hour, temperature and day type held."""
    h = L.loop_hourly(); wx = L.eccc_hourly()
    d = h.join(wx[['temp', 'wind', 'chill', 'rain_h', 'snow_h', 'obs']], how='inner')
    d = d[(d.index.hour >= 6) & (d.index.hour <= 21)].copy()
    day = d.index.normalize(); cal = L.calendar_frame(pd.DatetimeIndex(sorted(set(day))));
    d['daytype'] = cal.daytype.reindex(day).values; d['sunrise'] = cal.sunrise.reindex(day).values; d['sunset'] = cal.sunset.reindex(day).values
    mid = d.index.hour + 0.5
    d['dark'] = ((mid < d.sunrise) | (mid > d.sunset)).astype(int)
    d['dark_eve'] = ((mid > d.sunset)).astype(int); d['dark_morn'] = ((mid < d.sunrise)).astype(int)
    d['wkd'] = (d.daytype == 'weekday').astype(int); d['hour'] = d.index.hour; d['ym'] = d.index.strftime('%Y-%m'); d['y'] = d.eb
    full = d.groupby(day).y.transform('size') == 16; d = d[full.values]
    d = d[~d.index.normalize().strftime('%Y-%m-%d').isin(L.LOOP_EXCLUDE)]
    daily = L.eccc_daily(); d['sog_flag'] = (daily.sog.reindex(d.index.normalize()).fillna(0).values >= 1).astype(int)
    f = 'y ~ C(hour):C(wkd) + C(ym) + cr(temp, df=4) + rain_h + snow_h + sog_flag + dark_eve + dark_morn'
    def run(a): return smf.glm(f, d, family=sm.families.NegativeBinomial(alpha=a)).fit()
    g = lambda la: run(np.exp(la)).pearson_chi2 / run(np.exp(la)).df_resid - 1
    alpha = float(np.exp(optimize.brentq(g, np.log(1e-3), np.log(5.0), xtol=1e-2)))
    r = smf.glm(f, d, family=sm.families.NegativeBinomial(alpha=alpha)).fit(cov_type='HAC', cov_kwds={'maxlags': 16})
    out = {'n_hours': int(len(d)), 'n_days': int(len(d) / 16), 'first': str(d.index.min().date()), 'last': str(d.index.max().date()), 'alpha': alpha,
           'dark_hours': int(d.dark.sum()), 'dark_evening_hours': int(d.dark_eve.sum()), 'dark_morning_hours': int(d.dark_morn.sum())}
    for k in ('dark_eve', 'dark_morn', 'rain_h', 'snow_h', 'sog_flag'): out[k] = rr(r, k)
    # the hours 17:00-18:59 on weekdays, by light or dark, October-November vs the rest: descriptive table
    e = d[(d.wkd == 1) & (d.hour.isin([17, 18]))]
    t = e.groupby([e.index.strftime('%Y-%m'), 'dark_eve']).agg(hours=('y', 'size'), mean_count=('y', 'mean'), mean_temp=('temp', 'mean')).reset_index()
    t.columns = ['month', 'dark', 'hours', 'mean_count', 'mean_temp']; t.round(2).to_csv(os.path.join(L.TABLES, 'loop_evening_hours_light_dark.csv'), index=False)
    # share of the 24-hour total inside the 08:00-16:00 window, by month (both directions)
    hh = L.loop_hourly(); dd = hh.index.normalize(); nn = hh.groupby(dd).size(); fulld = nn[nn == 24].index
    hh = hh[dd.isin(fulld)]; w = hh[(hh.index.hour >= L.WIN[0]) & (hh.index.hour < L.WIN[1])]
    sh = (w.groupby(w.index.strftime('%Y-%m')).bike.sum() / hh.groupby(hh.index.strftime('%Y-%m')).bike.sum()).rename('share_08_16')
    dl = hh.groupby(hh.index.strftime('%Y-%m')).bike.sum().rename('bicycles_24h')
    pd.concat([dl, sh], axis=1).round(3).rename_axis('month').to_csv(os.path.join(L.TABLES, 'loop_window_share_by_month.csv'))
    out['window_share_min'] = float(sh.min()); out['window_share_max'] = float(sh.max())
    return out

if __name__ == '__main__': main(sys.argv[1:])
