#!/usr/bin/env python3
"""Shared loaders and helpers for the weather-and-bike-traffic component.

Series (never pooled, never compared in level):
  west, east   two citizen-operated Telraam S2 sensors (King Edward, Draper): daylight counts, hourly, from the Telraam API
               copy in the sibling clone Terrebonne-telraam/data/api/ (not published: Telraam owns the counts)
  loop         the borough's Eco-Counter loop at Kensington, 24 h: hourly by direction (access request 2026-300,
               released June 4, 2026, to May 11, 2026) and daily totals (request 2026-581, released October 9, 2026,
               to August 31, 2026), both in the sibling clone Terrebonne-access-requests
  gir          the City's detector at Girouard (det-00118-01), bicycles westbound on Terrebonne, 24 h, from October 24, 2025
               (City open data « Compteurs cyclistes permanents », files downloaded October 16, 2026)
  bixi         BIXI trips starting or ending at the station « Grand Boulevard / de Terrebonne » (BIXI Montréal open data)
  city         the City's permanent loop counters elsewhere in Montréal (City open data), as a reference
Weather: Environment and Climate Change Canada, Montréal-Trudeau (climate ID 7025251), raw/eccc/.
"""
import os, glob, math, datetime as dt
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..'))
GH = os.path.abspath(os.path.join(ROOT, '..', '..'))
TELRAAM_API = os.environ.get('TELRAAM_API', os.path.join(GH, 'Terrebonne-telraam', 'data', 'api'))
LOOP_HOURLY = os.path.join(GH, 'Terrebonne-access-requests', '2026-300', 'raw', '26072025_11052026.xlsx')
LOOP_DAILY = os.path.join(GH, 'Terrebonne-access-requests', '2026-581', 'derived', 'kensington_daily_borough_release_2025-07_2026-08.csv')
LOADING = os.path.join(GH, 'Terrebonne-access-requests', '2026-300', 'derived', 'loading_daily.csv')
DATA = os.path.expanduser(os.environ.get('TERREBONNE_DATA', '~/Terrebonne-data'))
BIXI_DIR = os.path.join(DATA, 'third-party', 'bixi'); CITY_DIR = os.path.join(DATA, 'third-party', 'montreal-opendata')
DERIVED = os.path.join(ROOT, 'derived'); TABLES = os.path.join(DERIVED, 'tables'); FIGS = os.path.join(DERIVED, 'figures')

LAT, LON = 45.4702, -73.6320            # the Kensington counter
WIN = (8, 16)                           # fixed clock window, hours 08:00–15:59: daylight on every day of the year at this latitude
MIN_HOURS, MIN_UPTIME, WIN_UPTIME = 8, 6.0, 0.5
# the City's snow-removal sector that contains each counter (2025-26 sectors): CDN-301 runs from the lane's west end to Royal,
# CDN-111 from Draper to Girouard
LOAD_SECTOR = {'west': 'CDN-301', 'loop': 'CDN-301', 'east': 'CDN-111', 'gir': 'CDN-111'}
LOOP_EXCLUDE = {'2026-05-29', '2026-05-30', '2026-05-31', '2026-06-07', '2026-06-08', '2026-06-09'}  # outage (zeros), counter-fault value, days missing from the Oct 9 table
WB_DEGRADED_FROM = '2026-03-01'
SERIES = {  # slug: (label EN, label FR, colour)
    'west': ('King Edward (Telraam, 08:00–16:00)', 'King Edward (Telraam, 8 h–16 h)', '#2a78d6'),
    'east': ('Draper (Telraam, 08:00–16:00)', 'Draper (Telraam, 8 h–16 h)', '#eb6834'),
    'loop': ('Kensington loop (24 h)', 'Boucle Kensington (24 h)', '#1baf7a'),
    'gir': ('Girouard detector (westbound, 24 h)', 'Détecteur Girouard (vers l\u2019ouest, 24 h)', '#c9930a'),
    'bixi': ('BIXI station Grand / Terrebonne (trips)', 'Station BIXI Grand / Terrebonne (trajets)', '#6250d6'),
    'city': ('City counters elsewhere (24 h, reference)', 'Compteurs de la Ville ailleurs (24 h, référence)', '#5f6b74'),
}
INK, MUTED, GRID, AXIS = '#1f2428', '#5f6b74', '#e2e4e1', '#c9cdd2'

# ---------------------------------------------------------------- sun
def sun_times(date, lat=LAT, lon=LON):
    """(sunrise, sunset, day length in hours) in local clock time, NOAA solar equations (accuracy about a minute)."""
    from zoneinfo import ZoneInfo
    n = date.timetuple().tm_yday; g = 2 * math.pi / 365.0 * (n - 1 + 0.5)
    eqt = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g) - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    dec = 0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g)
    ha = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(math.radians(lat)) * math.cos(dec)) - math.tan(math.radians(lat)) * math.tan(dec)))
    off = dt.datetime(date.year, date.month, date.day, 12, tzinfo=ZoneInfo('America/Toronto')).utcoffset().total_seconds() / 60
    rise = (720 - 4 * (lon + ha) - eqt + off) / 60; sset = (720 - 4 * (lon - ha) - eqt + off) / 60
    return rise, sset, sset - rise

# ---------------------------------------------------------------- calendar
def easter(y):
    a, b, c = y % 19, y // 100, y % 100; d, e = b // 4, b % 4; f = (b + 8) // 25; g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30; i, k = c // 4, c % 4; l = (32 + 2 * e + 2 * i - h - k) % 7; m = (a + 11 * h + 22 * l) // 451
    return dt.date(y, (h + l - 7 * m + 114) // 31, (h + l - 7 * m + 114) % 31 + 1)

def holidays(y):
    """Québec public holidays (statutory and the usual days off)."""
    e = easter(y); may25 = dt.date(y, 5, 25)
    patriotes = may25 - dt.timedelta(days=(may25.weekday() or 7))             # the Monday before May 25
    labour = dt.date(y, 9, 1) + dt.timedelta(days=(7 - dt.date(y, 9, 1).weekday()) % 7)
    thanks = dt.date(y, 10, 1) + dt.timedelta(days=(7 - dt.date(y, 10, 1).weekday()) % 7 + 7)
    return {dt.date(y, 1, 1), dt.date(y, 1, 2), e - dt.timedelta(2), e + dt.timedelta(1), patriotes, dt.date(y, 6, 24), dt.date(y, 7, 1),
            labour, thanks, dt.date(y, 12, 25), dt.date(y, 12, 26)}

def calendar_frame(idx):
    c = pd.DataFrame(index=idx)
    hol = set().union(*(holidays(y) for y in range(idx.min().year, idx.max().year + 1)))
    c['dow'] = idx.dayofweek
    c['holiday'] = [int(d.date() in hol) for d in idx]
    c['xmas'] = [int((d.month == 12 and d.day >= 24) or (d.month == 1 and d.day <= 2)) for d in idx]
    c['daytype'] = np.where((c.dow >= 5) | (c.holiday == 1), np.where(c.dow == 5, 'sat', 'sunhol'), 'weekday')
    c.loc[(c.holiday == 1), 'daytype'] = 'sunhol'
    st = [sun_times(d.date()) for d in idx]
    c['sunrise'] = [s[0] for s in st]; c['sunset'] = [s[1] for s in st]; c['daylen'] = [s[2] for s in st]
    c['doy'] = idx.dayofyear
    return c

# ---------------------------------------------------------------- weather
def wind_chill(t, v):
    """Environment Canada wind chill index; equals the air temperature above 10 °C or when the wind is under 5 km/h."""
    t = np.asarray(t, float); v = np.asarray(v, float)
    w = 13.12 + 0.6215 * t - 11.37 * np.power(np.maximum(v, 0.1), 0.16) + 0.3965 * t * np.power(np.maximum(v, 0.1), 0.16)
    return np.where((t <= 10) & (v >= 5), np.minimum(w, t), t)

WET_WORDS = ('Rain', 'Drizzle', 'Snow', 'Thunderstorm', 'Ice Pellets', 'Freezing', 'Hail')
def eccc_hourly():
    fs = sorted(glob.glob(os.path.join(ROOT, 'raw', 'eccc', 'en_climate_hourly_*_P1H.csv')))
    h = pd.concat([pd.read_csv(f, encoding='utf-8-sig') for f in fs])
    lst = pd.to_datetime(h['Date/Time (LST)'])
    # the file is in local standard time all year; put it on the local clock (daylight time in summer)
    t = (lst + pd.Timedelta(hours=5)).dt.tz_localize('UTC').dt.tz_convert('America/Toronto').dt.tz_localize(None)
    o = pd.DataFrame({'t': t.values, 'temp': h['Temp (°C)'].values, 'wind': h['Wind Spd (km/h)'].values, 'rh': h['Rel Hum (%)'].values,
                      'vis': h['Visibility (km)'].values, 'weather': h['Weather'].fillna('').values})
    o = o.dropna(subset=['temp']).drop_duplicates('t').set_index('t').sort_index()
    o['wind'] = o.wind.fillna(0); o['chill'] = wind_chill(o.temp, o.wind)
    w = o.weather.where(o.weather != 'NA', '')
    o['obs'] = (w != '').astype(int)
    o['rain_h'] = w.str.contains('Rain|Drizzle|Thunderstorm', regex=True).astype(int)
    o['snow_h'] = w.str.contains('Snow|Ice Pellets', regex=True).astype(int)
    return o

def eccc_daily():
    fs = sorted(glob.glob(os.path.join(ROOT, 'raw', 'eccc', 'en_climate_daily_*_P1D.csv')))
    d = pd.concat([pd.read_csv(f, encoding='utf-8-sig') for f in fs])
    d['date'] = pd.to_datetime(d['Date/Time']); d = d.set_index('date').sort_index()
    o = d.rename(columns={'Max Temp (°C)': 'tmax', 'Min Temp (°C)': 'tmin', 'Mean Temp (°C)': 'tmean', 'Total Rain (mm)': 'rain',
                          'Total Snow (cm)': 'snow', 'Total Precip (mm)': 'precip', 'Snow on Grnd (cm)': 'sog', 'Spd of Max Gust (km/h)': 'gust'})
    o = o[['tmax', 'tmin', 'tmean', 'rain', 'snow', 'precip', 'sog', 'gust']].apply(pd.to_numeric, errors='coerce')
    o = o[o.tmean.notna()]
    o['sog'] = o.sog.fillna(0)
    return o

def weather_daily():
    """Daily frame: ECCC daily values plus daytime (08:00–16:00 local clock) means from the hourly file."""
    d = eccc_daily(); h = eccc_hourly()
    hw = h[(h.index.hour >= WIN[0]) & (h.index.hour < WIN[1])]
    g = hw.groupby(hw.index.normalize()).agg(t_day=('temp', 'mean'), wind_day=('wind', 'mean'), chill_day=('chill', 'mean'),
                                             rain_hours=('rain_h', 'sum'), snow_hours=('snow_h', 'sum'), n_h=('temp', 'size'))
    g = g[g.n_h >= 6].drop(columns='n_h')
    w = d.join(g, how='inner')
    w['wet_day'] = ((w.rain_hours + w.snow_hours) > 0).astype(int)
    return w

def loading_flags(idx):
    l = pd.read_csv(LOADING, parse_dates=['day'])
    s = l[l.NomSecteur == 'CDN-301'].groupby('day').loads.sum(); e = l[l.NomSecteur == 'CDN-111'].groupby('day').loads.sum(); b = l[l.ArrondissementCode == 'CDN'].groupby('day').loads.sum()
    return pd.DataFrame({'loads_301': s.reindex(idx).fillna(0).values, 'loads_111': e.reindex(idx).fillna(0).values, 'loads_cdn': b.reindex(idx).fillna(0).values}, index=idx)

# ---------------------------------------------------------------- counts
def telraam_hourly(seg):
    fs = sorted(glob.glob(os.path.join(TELRAAM_API, f'{seg}_20*.csv')))
    if not fs: raise SystemExit(f'no Telraam API files for {seg} in {TELRAAM_API} (run Terrebonne-telraam/scripts/fetch_telraam.py)')
    h = pd.concat([pd.read_csv(f, parse_dates=['date']) for f in fs]).drop_duplicates('date').set_index('date').sort_index()
    return h[['uptime', 'bike', 'car', 'pedestrian', 'heavy', 'night']].fillna(0)

def telraam_daily(seg):
    """Daily frame: all-daylight total (the dashboard figure) and the fixed 08:00–16:00 window."""
    h = telraam_hourly(seg); h = h[h.uptime > 0]; day = h.index.normalize()
    a = h.groupby(day).agg(hours=('uptime', 'size'), uptime=('uptime', 'sum'), bike_all=('bike', 'sum'), car_all=('car', 'sum'))
    w = h[(h.index.hour >= WIN[0]) & (h.index.hour < WIN[1]) & (h.uptime >= WIN_UPTIME)]
    b = w.groupby(w.index.normalize()).agg(win_hours=('uptime', 'size'), bike=('bike', 'sum'), car=('car', 'sum'), ped=('pedestrian', 'sum'))
    o = a.join(b, how='left')
    o['valid_day'] = ((o.hours >= MIN_HOURS) & (o.uptime >= MIN_UPTIME)).astype(int)
    o['valid'] = ((o.valid_day == 1) & (o.win_hours == WIN[1] - WIN[0])).astype(int)
    o.index.name = 'date'
    return o

def loop_hourly():
    import openpyxl
    ws = openpyxl.load_workbook(LOOP_HOURLY, read_only=True).worksheets[0]
    rows = list(ws.iter_rows(min_row=4, values_only=True))
    d = pd.DataFrame([r[:5] for r in rows], columns=['t', 'bike', 'eb', 'wb', 'motor']).dropna(subset=['t'])
    d['t'] = pd.to_datetime(d['t']); return d.set_index('t').sort_index().astype(float)

def loop_daily():
    """Daily frame. bike = both directions, 2026-581 table (released Oct 9, 2026), to Aug 31, 2026; eb/wb and the 08–16
    window from the hourly workbook (2026-300, released June 4, 2026), full days July 27, 2025 – May 10, 2026."""
    k = pd.read_csv(LOOP_DAILY, parse_dates=['date']).set_index('date')[['bike', 'motor']].astype(float)
    h = loop_hourly(); day = h.index.normalize()
    n = h.groupby(day).size(); full = n[n == 24].index
    g = h.groupby(day).agg(bike_h=('bike', 'sum'), eb=('eb', 'sum'), wb=('wb', 'sum'))
    w = h[(h.index.hour >= WIN[0]) & (h.index.hour < WIN[1])]
    g['eb_win'] = w.groupby(w.index.normalize()).eb.sum(); g['bike_win'] = w.groupby(w.index.normalize()).bike.sum()
    o = k.join(g.loc[g.index.isin(full)], how='left')
    excl = o.index.strftime('%Y-%m-%d').isin(LOOP_EXCLUDE) | (o.bike <= 0)
    o['valid'] = (~excl).astype(int)
    o['valid_eb'] = ((o.valid == 1) & o.eb.notna()).astype(int)
    o['wb_degraded'] = (o.index >= WB_DEGRADED_FROM).astype(int)
    return o

GIR_INSTANCE, GIR_MIN_HOURS = 'det-00118-01', 22
def girouard_daily():
    """City detector at Girouard, the Terrebonne westbound channel: daily total from the hourly rows; a day is valid when
    at least GIR_MIN_HOURS of its 24 hourly rows are present and the total is above zero."""
    fs = sorted(glob.glob(os.path.join(CITY_DIR, 'cyclistes_202[56]_2026-10-16.csv')))
    d = pd.concat([pd.read_csv(f) for f in fs]); d = d[(d.instance == GIR_INSTANCE) & (d.agg_code == 'h')].copy()
    d['t'] = pd.to_datetime(d.periode, format='mixed'); d = d.drop_duplicates('t').set_index('t').sort_index()
    o = d.groupby(d.index.normalize()).volume.agg(hours='size', bike='sum')
    w = d[(d.index.hour >= WIN[0]) & (d.index.hour < WIN[1])]; o['bike_win'] = w.groupby(w.index.normalize()).volume.sum()
    o['valid'] = ((o.hours >= GIR_MIN_HOURS) & (o.bike > 0)).astype(int); o.index.name = 'date'
    return o

def design_frame(counts, extra_cols=()):
    """Join a daily count frame with weather, calendar and snow-loading columns; adds lagged snowfall."""
    w = weather_daily(); idx = w.index
    f = w.join(calendar_frame(idx)).join(loading_flags(idx))
    for k in range(1, 8): f[f'snow_l{k}'] = f.snow.shift(k)
    f['snow3'] = f.snow.shift(1).rolling(3).sum(); f['rain_l1'] = f.rain.shift(1)
    f['loading'] = (f.loads_301 > 0).astype(int); f['loading_111'] = (f.loads_111 > 0).astype(int); f['loading_cdn'] = (f.loads_cdn > 0).astype(int)
    f['winter'] = [int((d.month, d.day) >= (11, 16) or d.month <= 3) for d in f.index]
    return counts.join(f, how='inner')

def savefig(fig, folder, name):
    os.makedirs(folder, exist_ok=True)
    for ext in ('png', 'svg'): fig.savefig(os.path.join(folder, f'{name}.{ext}'), dpi=200 if ext == 'png' else None, bbox_inches='tight')

def style_axes(ax):
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'): ax.spines[s].set_color(AXIS)
    ax.tick_params(colors=MUTED, labelsize=8); ax.grid(True, color=GRID, lw=0.6); ax.set_axisbelow(True)

# ---------------------------------------------------------------- figures: shared pieces
def fig_setup():
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'Helvetica Neue', 'font.size': 9, 'axes.titlesize': 9.5, 'axes.titleweight': 'bold', 'axes.titlecolor': INK,
                         'axes.labelcolor': MUTED, 'axes.labelsize': 8.5, 'text.color': INK, 'svg.fonttype': 'none', 'figure.facecolor': 'white'})
    return plt

def tr(lang, en, fr): return en if lang == 'en' else fr
def label(series, lang): return SERIES[series][0 if lang == 'en' else 1]
def num(v, lang, dec=0):
    s = f'{v:,.{dec}f}'
    return s if lang == 'en' else s.replace(',', ' ').replace('.', ',')
def shade_winters(ax, lo, hi):
    """Light band over each November 16 – March 31 (the City's winter period for bike lanes)."""
    for y in range(lo.year - 1, hi.year + 1):
        a, b = pd.Timestamp(y, 11, 16), pd.Timestamp(y + 1, 3, 31)
        if b >= lo and a <= hi: ax.axvspan(max(a, lo), min(b, hi), color='#eef1f4', lw=0, zorder=0)
def read_daily(series):
    d = pd.read_csv(os.path.join(DERIVED, f'daily_{series}.csv'), parse_dates=['date']).set_index('date')
    if series == 'loop': d = d[d.valid_eb == 1].copy(); d['y'] = d.eb
    else: d = d[d.valid == 1].copy(); d['y'] = d.bike
    return d
SERIES_NOTE = {
    'en': {'west': 'bicycles, 08:00–16:00', 'east': 'bicycles, 08:00–16:00', 'loop': 'bicycles eastbound, 24 h', 'gir': 'bicycles westbound, 24 h', 'bixi': 'trips starting or ending', 'city': 'bicycles, 12 counters, 24 h'},
    'fr': {'west': 'vélos, 8 h–16 h', 'east': 'vélos, 8 h–16 h', 'loop': "vélos vers l'est, 24 h", 'gir': "vélos vers l'ouest, 24 h", 'bixi': 'trajets au départ ou à l’arrivée', 'city': 'vélos, 12 compteurs, 24 h'}}
SHORT = {'en': {'west': 'King Edward', 'east': 'Draper', 'loop': 'Kensington loop', 'gir': 'Girouard detector', 'bixi': 'BIXI station', 'city': 'City counters'},
         'fr': {'west': 'King Edward', 'east': 'Draper', 'loop': 'Boucle Kensington', 'gir': 'Détecteur Girouard', 'bixi': 'Station BIXI', 'city': 'Compteurs de la Ville'}}
