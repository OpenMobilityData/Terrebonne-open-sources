#!/usr/bin/env python3
"""Note (A4, pdflatex) and slide deck (beamer 16:9), English, from derived/numbers.json, derived/tables/ and the
figures. Every figure in the text is read from the tables at build time.
Usage: python3 scripts/build_docs.py [--final]   (without --final both documents carry a DRAFT mark)
Writes docs/weather_bike_traffic_note_en.{tex,pdf}, docs/weather_bike_traffic_deck_en.{tex,pdf} and docs/deck_figures_en/NN-<figure>.png
(each figure of the deck, named by the number of the slide that shows it)."""
import os, sys, json, subprocess, datetime
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, '..')); DOCS = os.path.join(ROOT, 'docs'); T = os.path.join(ROOT, 'derived', 'tables')
FINAL = '--final' in sys.argv; STAMP = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'); TODAY = datetime.datetime.now().strftime('%B %-d, %Y')
URL = 'https://github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/2026-weather-and-bike-traffic'
N = json.load(open(os.path.join(ROOT, 'derived', 'numbers.json'))); H = N['hourly']
tab = lambda n: pd.read_csv(os.path.join(T, n + '.csv'))
EFF, BLK, CV, LAG, YR, CUR, COV = tab('effects_main'), tab('deviance_blocks').set_index('series'), tab('cross_validation').set_index('series'), tab('snow_lags_winter'), tab('year_terms'), tab('temperature_curve'), tab('coverage_by_month')
SER = ['west', 'loop', 'east', 'gir', 'bixi', 'city']; TER = ['west', 'loop', 'east', 'gir']   # the Terrebonne counters from west to east
INSTR = {'west': 'camera sensor, 08:00--16:00', 'east': 'camera sensor, 08:00--16:00', 'loop': 'loop, 24 h', 'gir': 'detector, 24 h', 'bixi': 'bike-share dock'}
def LEv(term, series):
    r = LE[(LE.term == term) & (LE.series == series)]
    return float(r.pct.iloc[0]) if len(r) else float('nan')
def loc_row(r):
    key = 'temperature above 20 °C (per degree)' if 'above 20' in r.term else r.term
    lab = ('temperature above 20 °C (per degree)' if 'above 20' in r.term else r.term).replace(' °C', '\\,$^\\circ$C')
    cells = ' & '.join(('--' if LEv(key, x) != LEv(key, x) else sg(LEv(key, x), 1 if 'temperature' in key else 0)) for x in ('west', 'loop', 'east', 'gir'))
    p = '$<$0.001' if r.p < 0.001 else f'{r.p:.3f}'
    return f"{lab} & {cells} & {r.chi2:.1f} & {int(r.df)} & {p} \\\\"
NAME = {'west': 'King Edward', 'east': 'Draper', 'loop': 'Kensington loop', 'gir': 'Girouard detector', 'bixi': 'BIXI station', 'city': 'City counters'}
D = lambda s: datetime.date.fromisoformat(s).strftime('%B %-d, %Y')
def sg(v, d=0):
    s = f'{abs(v):.{d}f}'; z = float(s) == 0
    return ('' if z else '$-$' if v < 0 else '+') + s
def p_(v, d=0): return sg(v, d) + '\\,\\%'
def rng(lo, hi, d=0): return f'{sg(lo, d)} to {sg(hi, d)}'
def eff(series, term, model='main'):
    r = EFF[(EFF.series == series) & (EFF.term == term) & (EFF.model == model)]
    return None if r.empty else r.iloc[0]
def cell(series, term, model='main'):
    r = eff(series, term, model)
    return '--' if r is None else f'{sg(r.pct)} ({rng(r.lo, r.hi)})'
def span(term, ss=TER, model='main'):
    """Range of reductions across series, as magnitudes: '14 to 22\\,\\%' (to be followed by 'fewer')."""
    v = sorted(-eff(s, term, model).pct for s in ss if eff(s, term, model) is not None)
    assert v[0] > 0, term
    return f'{v[0]:.0f} to {v[-1]:.0f}\\,\\%'
def curve(s, t):
    r = CUR[(CUR.series == s) & (CUR.temp == t)]
    return None if r.empty else float(r.index_20C_100.iloc[0])
def cspan(t, ss=TER):
    v = [curve(s, t) for s in ss]; return f'{min(v):.0f} to {max(v):.0f}'
fig = lambda typ, name, cap, w=1.0, pos='htbp': f"\\begin{{figure}}[{pos}]\\centering\\includegraphics[width={w}\\textwidth]{{../derived/figures/{typ}/{name}_en.png}}\\caption{{{cap}}}\\label{{fig:{name}}}\\end{{figure}}"
DRAFT = '' if FINAL else r'\begin{center}\colorbox{red!15}{\parbox{0.96\textwidth}{\centering\textbf{\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, ' + TODAY + r'. Not yet checked line by line; figures may change.}}}}\end{center}'

# ---------------------------------------------------------------- rows
ser_rows = '\n'.join(f"{NAME[s]} & {what} & {D(N[s]['first'])} to {D(N[s]['last'])} & {N[s]['n_days']} & {N[s]['mean_count']:,.0f} \\\\" for s, what in [
    ('west', 'Bicycles, both directions, 08:00--16:00 (Telraam S2 camera sensor, west of Cavendish)'),
    ('loop', 'Bicycles eastbound, 24 h (the borough\\textquoteright{}s Eco-Counter loop)'), ('east', 'Bicycles, both directions, 08:00--16:00 (Telraam S2 camera sensor, east of Cavendish)'), ('gir', 'Bicycles westbound, 24 h (the City\\textquoteright{}s pole-mounted detector at Girouard)'), ('bixi', 'Trips starting or ending at the station « Grand Boulevard / de Terrebonne », April 15 to November 15'),
    ('city', 'Bicycles, 24 h, sum of twelve City loop counters elsewhere in Montréal')])
slope_rows = '\n'.join(f"{NAME[s]} & {N[s]['bp']:.1f} ({N[s]['bp_lo']:.0f} to {N[s]['bp_hi']:.0f}) & {sg(N[s]['slope_cold_pct'], 1)} ({rng(N[s]['slope_cold_lo'], N[s]['slope_cold_hi'], 1)}) & {sg(N[s]['slope_warm_pct'], 1)} ({rng(N[s]['slope_warm_lo'], N[s]['slope_warm_hi'], 1)}) & {sg(N[s]['within_cold_pct'], 1)} ({rng(N[s]['within_cold_lo'], N[s]['within_cold_hi'], 1)}) \\\\" for s in SER)
cold_rows = '\n'.join(f"{NAME[s]} & {N[s]['days_below_0']} & {sg(N[s]['slope_below0_pct'], 1)} ({rng(N[s]['slope_below0_lo'], N[s]['slope_below0_hi'], 1)}) & {sg(N[s]['slope_0_to_bp_pct'], 1)} ({rng(N[s]['slope_0_to_bp_lo'], N[s]['slope_0_to_bp_hi'], 1)}) & {N[s]['cold0_p']:.2f} \\\\" for s in ['west', 'loop', 'east', 'gir', 'city'])
curve_rows = '\n'.join(f"{t:+d} & " + ' & '.join('--' if curve(s, t) is None else f'{curve(s, t):.0f}' for s in SER) + ' \\\\' for t in (-15, -10, -5, 0, 5, 10, 15, 20, 25)).replace('+', '').replace('-', '$-$')
TERMS = [('rain_under2', 'Rain, under 2 mm'), ('rain_2to10', 'Rain, 2 to 10 mm'), ('rain_over10', 'Rain, over 10 mm'), ('snow_under2', 'Snowfall, under 2 cm'), ('snow_2to10', 'Snowfall, 2 cm or more'),
         ('snow_on_ground', 'Snow on the ground, 1 cm or more'), ('wind_per_10kmh', 'Wind, per 10 km/h'), ('snow_yesterday_per_cm', 'Snowfall the day before, per cm'), ('saturday', 'Saturday'), ('sunday_holiday', 'Sunday or holiday'), ('christmas_period', 'December 24 to January 2')]
eff_rows = '\n'.join(f"{lab} & " + ' & '.join(cell(s, t) for s in SER) + ' \\\\' for t, lab in TERMS)
days_rows = '\n'.join(f"{lab} & " + ' & '.join('--' if eff(s, t) is None else f'{int(eff(s, t).days)}' for s in SER) + ' \\\\' for t, lab in TERMS[:6])
blk_rows = '\n'.join(f"{NAME[s]} & {100 * BLK.loc[s, 'calendar_season_alone']:.0f} & {100 * BLK.loc[s, 'weather_alone']:.0f} & {100 * BLK.loc[s, 'both']:.0f} & {100 * BLK.loc[s, 'shared']:.0f} & {100 * BLK.loc[s, 'unique_weather']:.0f} & {100 * BLK.loc[s, 'unique_calendar_season']:.0f} \\\\" for s in SER)
aic_rows = '\n'.join(f"{NAME[s]} & {N[s]['aic_linear']:.1f} & {N[s]['aic_temp']:.1f} & {N[s]['aic_spline']:.1f} & {N[s]['aic_temp_nowind']:.1f} & {N[s]['aic_chill']:.1f} & {N[s]['corr_temp_chill']:.3f} \\\\" for s in SER)
cv_rows = '\n'.join(f"{NAME[s]} & {int(CV.loc[s, 'days_predicted'])} & {CV.loc[s, 'median_abs_pct_error_in']:.0f} & {CV.loc[s, 'median_abs_pct_error_out']:.0f} & {CV.loc[s, 'r2_log_in']:.2f} & {CV.loc[s, 'r2_log_out']:.2f} \\\\" for s in SER)
lag_rows = '\n'.join(f"{k} & " + ' & '.join((lambda r: f'{sg(r.pct_per_5cm)} ({rng(r.lo, r.hi)})')(LAG[(LAG.series == s) & (LAG.lag_days == k)].iloc[0]) for s in TER) + ' \\\\' for k in range(8))
load_rows = '\n'.join(f"{NAME[s]} & {N[s]['loading_sector']} & {N[s]['winter_days']:.0f} & {N[s]['winter_loading_days']:.0f} & {cell(s, 'loading_day', 'winter_lags')} & {cell(s, 'temp_per_degree', 'winter_lags')} \\\\" for s in TER)
yr = lambda s, y: YR[(YR.series == s) & (YR.year == y)].iloc[0]
yr_rows = '\n'.join(f"{NAME[r.series]} & {r.year.replace('-', '--')} against {r.reference.replace('-', '--')} & {int(r.days)} & {sg(r.pct)} ({rng(r.lo, r.hi)}) \\\\" for r in YR.itertuples() if not (r.series == 'city' and r.year == '2026-27'))
cov_rows = '\n'.join(f"{r.month} & {r.west} & {r.loop} & {r.east} & {r.gir} & {r.bixi} & {r.city} \\\\" for r in COV.itertuples())
he = lambda k: f"{-H[k]['pct']:.0f}\\,\\% ({-H[k]['hi']:.0f} to {-H[k]['lo']:.0f})"
wspan = f"{100 * H['window_share_min']:.0f} to {100 * H['window_share_max']:.0f}"
west, east, loop = N['west'], N['east'], N['loop']
cold_span = f"{min(N[s]['slope_cold_pct'] for s in TER):.0f} to {max(N[s]['slope_cold_pct'] for s in TER):.0f}"
w27 = yr('west', '2026-27'); w26 = yr('west', '2025-26'); e26 = yr('east', '2025-26'); c26 = yr('city', '2025-26')
dchill = {s: N[s]['aic_temp'] - N[s]['aic_chill'] for s in SER}
b26 = yr('bixi', '2025-26')
LCT = tab('location_context'); LC = {r.series: r for r in LCT.itertuples()}; DK = tab('location_draper_over_king_edward'); LT = tab('location_tests'); LE = tab('location_effects')
YS = tab('year_comparison_steps'); YS = YS[YS.common_dates >= 30]; YW = tab('year_comparison_weather')
ys = lambda s_, y: YS[(YS.series == s_) & (YS.year == y)].iloc[0]; yw = lambda s_, y: YW[(YW.series == s_) & (YW.year == y)].iloc[0]
st = lambda r, k: f"{sg(r[k + '_pct'])} ({rng(r[k + '_lo'], r[k + '_hi'])})"
ystep_rows = '\n'.join(f"{NAME[r.series]} & {r.year.replace('-', '--')} against {r.reference.replace('-', '--')} & {int(r.common_dates)} & {st(r, 'step1')} & {st(r, 'step2')} & {st(r, 'step3')} \\\\" for _, r in YS.iterrows())
yweather_rows = '\n'.join(f"{NAME[r.series]}, {r.year.replace('-', '--')} against {r.reference.replace('-', '--')} & {r.daytime_temp_mean_ref:.1f} / {r.daytime_temp_mean_year:.1f} & {r.days_below_minus10_ref:.0f} / {r.days_below_minus10_year:.0f} & {r.snowfall_cm_ref:.0f} / {r.snowfall_cm_year:.0f} & {r.snow_on_ground_days_ref:.0f} / {r.snow_on_ground_days_year:.0f} & {r.rain_mm_ref:.0f} / {r.rain_mm_year:.0f} \\\\" for _, r in YW.iterrows())
s1w, s1e, s1w3, wxw = ys('west', '2025-26'), ys('east', '2025-26'), ys('west', '2026-27'), yw('west', '2025-26')
yv = lambda r: f"{sg(r.pct)}\\,\\% ({rng(r.lo, r.hi)})"

SUMMARY_ITEMS = f"""\\item \\textbf{{Temperature.}} On the four Terrebonne count series, each additional degree of daytime temperature goes with {cold_span}\\,\\% more bicycles, up to roughly 20\\,$^\\circ$C; above that the count stops rising. Holding rain, snow, wind, day of the week and time of year fixed, a day at 0\\,$^\\circ$C has {cspan(0)}\\,\\% of the count of the same day at 20\\,$^\\circ$C, and a day at $-$10\\,$^\\circ$C has {cspan(-10)}\\,\\%. The count falls steadily with the cold; it does not fall to zero.
\\item \\textbf{{No threshold in the cold.}} In percentage terms the slope below 0\\,$^\\circ$C is not distinguishable from the slope between 0\\,$^\\circ$C and 20\\,$^\\circ$C on any Terrebonne series. The change of slope that the earlier analyses placed near $-$1 or $-$5\\,$^\\circ$C belongs to a straight-line model of the counts themselves; the only change of slope the data support is the levelling-off in warm weather, and its position is poorly determined (intervals of ten degrees or more).
\\item \\textbf{{Wind chill.}} Replacing air temperature and wind by the wind-chill index fits about as well (the two are correlated at {west['corr_temp_chill']:.3f}); the data cannot separate them.
\\item \\textbf{{Rain and snow.}} At a given temperature and time of year, a day with 2 to 10\\,mm of rain has {span('rain_2to10')} fewer bicycles on the Terrebonne series, a day with more than 10\\,mm {span('rain_over10')} fewer, and a day with at least 1\\,cm of snow on the ground {span('snow_on_ground', ['west', 'east', 'loop'])} fewer at King Edward, Draper and Kensington, where it is the largest single weather effect after temperature; at the Girouard detector snow on the ground shows no measurable effect ({cell('gir', 'snow_on_ground')}\\,\\%).
\\item \\textbf{{Season or weather?}} The two cannot be fully separated: {100 * min(BLK.loc[x, 'shared'] for x in TER):.0f} to {100 * max(BLK.loc[x, 'shared'] for x in TER):.0f}\\,\\% of the day-to-day variation on the Terrebonne series can be attributed to either. Weather effects estimated only from the variation inside each calendar month are nonetheless close to those estimated over the whole record.
\\item \\textbf{{Darkness.}} On the loop counter, the same clock hour in the evening carries {he('dark_eve')} fewer bicycles when the sun has set than when it is up, at the same temperature and in the same month.
\\item \\textbf{{Snow loading.}} On the days the City loaded snow in the sector that contains each counter, the counts are not distinguishable from other winter days once temperature and snow are accounted for; the intervals are wide ({min(N[x]['winter_loading_days'] for x in TER):.0f} to {max(N[x]['winter_loading_days'] for x in TER):.0f} loading days per series).
\\item \\textbf{{By location.}} The counters stand at different points of the street, from King Edward at the west end ({LC['west'].km_to_downtown_reference:.1f}\\,km from downtown) to Girouard at the east end ({LC['gir'].km_to_downtown_reference:.1f}\\,km), and each is analysed as its own location; a difference between two of them is a difference between places, and between instruments, not a discrepancy. The response to temperature is similar along the street (from {N['west']['slope_cold_pct']:.1f}\\,\\% per degree at King Edward to {N['gir']['slope_cold_pct']:.1f}\\,\\% at Girouard); the effects of light rain, heavy rain, snow on the ground and the weekend do differ by location (tests in Section~\\ref{{sec:location}}). On the days both camera sensors were valid, Draper counted {DK.iloc[0].draper_over_king_edward:.2f} times what King Edward counted ({DK.iloc[0].lo:.2f} to {DK.iloc[0].hi:.2f}), the one comparison between two locations made with the same instrument.
\\item \\textbf{{Year to year.}} The weather of each year is part of the comparison: the model that estimates the difference between years also contains temperature, rain, snowfall, snow on the ground and wind, so a colder or snowier year is not mistaken for a decline. On that basis King Edward counted {yv(w26)} in its second counting year (from August~15, 2025) compared with its first, and {yv(w27)} from August~15 to November~8, 2026 compared with its first year. (compared plainly on the same dates, without the weather, {st(s1w, 'step1')}\\,\\% and {st(s1w3, 'step1')}\\,\\%; its second year was colder and much snowier than its first). Draper counted {yv(e26)} after its first year, the BIXI station {yv(b26)}, and the City\\textquoteright{{}}s counters elsewhere {yv(c26)}. The year-to-year figures are specific to each location and are not expected to be the same along the street. Downtime is accounted for in these figures: only days with a complete, valid count enter, and each is compared with days of the same time of year, day type and weather, so a gap in one year is not counted as a decline. The comparisons remain limited for other reasons: two to three years of data, a camera sensor whose field of view can change when it is remounted, and a third year that so far holds a single autumn. A year term absorbs every difference between the years other than the weather."""

ABSTRACT = f"""This note measures how the number of bicycles counted on rue de Terrebonne varies with the weather, with daylight and with snow, using every count series available for the street: two citizen-operated Telraam camera sensors (King Edward, {west['n_days']} valid days from {D(west['first'])}; Draper, {east['n_days']} days), the borough\\textquoteright{{}}s loop counter at Kensington ({loop['n_days']} days, eastbound, hourly release of June~4, 2026), the City\\textquoteright{{}}s detector at Girouard ({N['gir']['n_days']} days, westbound), trips at the BIXI station on the street, and, as a reference, twelve City counters elsewhere in Montréal. Weather is Environment and Climate Change Canada\\textquoteright{{}}s record at Montréal-Trudeau. Each series is modelled separately by negative binomial regression, so that every effect is a percentage and no levels are compared between series; the Telraam sensors, which count only in daylight, are analysed in a fixed window (08:00--16:00) that is daylight all year. The analysis accounts for sensor downtime: only days with a complete, valid count are used, no gap is filled in, and every comparison is between days of the same time of year, day type and weather, so that a period without data removes days from a comparison without being read as a drop in cycling. From one year to the next, with each year\\textquoteright{{}}s weather taken into account in the model (a colder or snowier year is compared with what that weather predicts), the result depends on the location (King Edward, at the west end, {yv(w27)} in the autumn of 2026 against its first year; Draper, further east, {yv(e26)} after its first year), and two to three years of data do not establish a trend at either. Location is a parameter of every model: each counter is analysed as its own point on the street. The note states what was measured, with intervals, and what the data cannot show. It makes no recommendation."""

LAY_WORDS = 300
r0 = lambda term: span(term).replace('\\,\\%', '')
LAY = f"""How much does weather change cycling on rue de Terrebonne? This note uses every count available: citizen-operated camera sensors at King Edward and Draper, the borough's counter at Kensington, the City's detector at Girouard, and trips at the BIXI station at Grand Boulevard. Weather is from Trudeau airport; counts run August 2024 to November 2026.

Temperature matters most. Each degree warmer brings {cold_span} per cent more bicycles, up to about 20 °C, then levels off. A day at 0 °C sees {cspan(0)} per cent of the bicycles of the same day at 20 °C; a day at −10 °C, {cspan(-10)} per cent. There is no temperature below which cycling stops.

A day with 2 to 10 mm of rain has {r0('rain_2to10')} per cent fewer bicycles than a dry day at the same temperature; snow on the ground goes with {span('snow_on_ground', ['west', 'east', 'loop']).replace(chr(92) + ',' + chr(92) + '%', '')} per cent fewer at three of the four counters. At the same evening hour and temperature, the borough's counter records {-H['dark_eve']['pct']:.0f} per cent fewer bicycles after sunset.

Cold, snow and short days arrive together, so much of the winter drop could be either weather or season. Snow-loading days look like other winter days, but are too few to be sure. Year to year, with each year's weather accounted for, the result depends on the location: the west-end camera (King Edward) counted {w27.pct:.0f} per cent more in autumn 2026 than in its first year, the camera further east (Draper) {-e26.pct:.0f} per cent fewer. The analysis accounts for sensor downtime (only complete days, compared like with like), but two to three years of counts cannot show whether cycling on the street is rising or falling.

Counters differ in place and type; only percentage changes are compared. The note makes no recommendation."""
n_lay = len(LAY.split()); assert n_lay <= LAY_WORDS, f'lay summary has {n_lay} words, limit {LAY_WORDS}'
open(os.path.join(ROOT, 'derived', 'lay_abstract_en.txt'), 'w', encoding='utf-8').write('Lay summary\n\n' + LAY + '\n')
print('lay summary:', n_lay, 'words')
LAY_TEX = '\n\n'.join(q.replace('%', '\\%').replace("'", '\\textquoteright{}').replace('°C', '$^\\circ$C').replace('−', '$-$') for q in LAY.split('\n\n'))

NOTE = r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage[a4paper,margin=2.2cm]{geometry}\usepackage{graphicx,booktabs,longtable,amsmath,caption,xcolor,enumitem,array,float}\usepackage[hidelinks]{hyperref}
\captionsetup{font=small,labelfont=bf}\setlength{\parskip}{0.55em}\setlength{\parindent}{0pt}\setlist{itemsep=0.25em,topsep=0.3em}\widowpenalty=10000\clubpenalty=10000\raggedbottom
\newcommand{\docversion}{''' + STAMP + r'''}
\begin{document}
{\raggedright\LARGE\bfseries Weather, daylight, snow and bicycle traffic on rue de Terrebonne\par}\vspace{0.3em}
{\large Six count series, August 2024 to November 2026\par}\vspace{0.6em}
{\small Terrebonne-open-sources, version \docversion. Author: Rick Hoge, PhD (see the repository\textquoteright{}s « About the author »). Scripts, tables and figures: \url{''' + URL + r'''}.\par}
''' + DRAFT + r'''
\subsection*{Lay summary}
''' + LAY_TEX + r'''
\subsection*{Abstract}
''' + ABSTRACT + r'''
\subsection*{What the analysis finds}
\begin{enumerate}
''' + SUMMARY_ITEMS + r'''
\end{enumerate}
''' + fig('overview', 'overview', 'Daytime temperature and the daily count of each series. Each panel has its own scale; the series are not compared in level.', 0.97, 'p') + r'''
\tableofcontents\clearpage

\section{Questions}
\begin{enumerate}
\item How does the daily count of bicycles vary with temperature, and is there a temperature at which the response changes?
\item Does wind chill describe the response better than air temperature?
\item What do rain, snowfall, snow on the ground and wind each add at a given temperature?
\item How much of the seasonal swing can be attributed to weather, and how much to day length and the calendar?
\item Does a snowfall depress the counts on the following days, and do the days on which the City loads snow differ from other winter days?
\item How do the responses differ from one location on the street to another?
\item After weather is accounted for, does the count differ from one year to the next?
\end{enumerate}

\section{Data}
\subsection{The count series}
\begin{center}\small\begin{tabular}{@{}p{2.4cm}p{6.1cm}p{4.0cm}rr@{}}\toprule
Series & What is counted & Days used in the models & Days & Mean a day\\\midrule
''' + ser_rows + r'''
\bottomrule\end{tabular}\end{center}
The means are given to describe each series, not to compare them: a camera sensor counting eight daytime hours in both directions, one direction of a loop counting 24 hours, and trips at a bike-share dock are different quantities.

\textbf{Telraam sensors (King Edward, Draper).} Installed by Terrebonne residents in August and September 2024; the author was tasked with the statistical analysis of their data. Hourly counts from the Telraam API (pull of November~9, 2026). A Telraam sensor counts only in daylight. Its daily total therefore covers about nine hours in December and sixteen in June, and would rise and fall with the length of the day even if nobody changed their habits (Figure~\ref{fig:daylight}, left). To remove that artefact every analysis here uses the count in a \emph{fixed clock window, 08:00 to 16:00}, which is daylight on every day of the year at Montréal\textquoteright{}s latitude (the latest sunrise is about 07:35 and the earliest sunset about 16:10). The price is that the evening peak is left out. A day is valid when the sensor reported at least 8 hours with at least 6 hours of summed uptime, and all eight window hours with an uptime of at least 0.5. Invalid days are left out and nothing is interpolated. King Edward has no valid day in February 2026; Draper has none from February to April 2026 (Appendix~\ref{app:coverage}). Whether the API\textquoteright{}s hourly counts are already scaled for uptime could not be confirmed from Telraam\textquoteright{}s documentation; they are used as delivered.

\textbf{Kensington loop.} The borough\textquoteright{}s Eco-Counter (inductive loops, 24 hours, by direction). The hourly workbook released on June~4, 2026 under access request 2026-300 runs from July~26, 2025 to May~11, 2026. The westbound channel under-counts from about March~1, 2026, so the models use the eastbound channel alone. The daily table released on October~9, 2026 under request 2026-581 serves to identify the days set aside (May~29--31, 2026, zeros; June~7--9, 2026). One site, less than one full year, one direction.

\textbf{Girouard detector.} The City\textquoteright{}s pole-mounted detector at the corner of Girouard (open data « Compteurs cyclistes permanents », instance det-00118-01; files downloaded October~16, 2026) counts bicycles on Terrebonne in one direction, westbound, 24 hours a day, from October~23, 2025. It is the City\textquoteright{}s only counter on the street, at its east end, and it covers the summer of 2026, which the loop\textquoteright{}s hourly release does not. A day is used when at least 22 of its 24 hourly rows are present. One direction, a little under one year, a camera-type detector rather than a loop.

\textbf{BIXI station.} The station « Grand Boulevard / de Terrebonne » stands 6\,m from the lane. BIXI Montréal\textquoteright{}s open trip files give each trip\textquoteright{}s start and end station and time; the series is the number of trips starting or ending there each day. A trip is not a bicycle passing a point, and a day without a trip is absent from the files rather than recorded as zero, so the models use the regular season only (April~15 to November~15). The station recorded trips in the winter of 2025--26 (3 to 6 a day on the days with trips) and none in the winter of 2024--25.

\textbf{City counters.} Twelve of the City\textquoteright{}s permanent loop counters elsewhere in Montréal, none on Terrebonne, kept because they report on at least 97\,\% of days from January~1, 2025 to November~6, 2026; the series is their sum on the days when all twelve report. It is a reference for how bicycle traffic elsewhere in Montréal responds to the same weather.

\subsection{Weather, daylight, snow}
Environment and Climate Change Canada, station Montréal-Trudeau (climate ID 7025251), about 9\,km from the street. From the daily file: rain (mm), snowfall (cm), snow on the ground (cm). From the hourly file: temperature and wind, averaged over 08:00--16:00 local time (« daytime »), and the wind-chill index computed from them by Environment Canada\textquoteright{}s formula. The hourly file carries no precipitation amount, so rain and snowfall are 24-hour totals: rain that fell at night counts as a rainy day. Sunrise and sunset are computed for the street\textquoteright{}s position (NOAA solar equations). Snow loading is the City\textquoteright{}s record of loads by day and by snow-removal sector (open data, snow-removal transactions): sector CDN-301 contains the lane from its west end to Royal (King Edward and Kensington), sector CDN-111 from Draper to Girouard (the Draper sensor and the Girouard detector). Each counter is matched with its own sector.

\section{Method}
\textbf{One model per series, on a percentage scale.} Daily counts are modelled by negative binomial regression with a log link. Counts are non-negative, their spread grows with their level, and a weather effect is plausibly proportional (rain removes a share of the riders, not a fixed number); a straight-line model of the counts themselves, as in the earlier analyses, forces a rainy day to remove as many bicycles in January as in June. On the log scale every coefficient is a percentage change, which is also what allows the series to be set side by side without comparing their levels.

\textbf{Terms.} Day type (weekday, Saturday, Sunday or public holiday); December~24 to January~2; the counting year (from August~15); two annual harmonics for the time of year; daytime temperature; rain of the day in classes (none, under 2\,mm, 2 to 10\,mm, over 10\,mm); snowfall of the day in classes (none, under 2\,cm, 2\,cm or more); snow on the ground (1\,cm or more); daytime wind; snowfall of the day before. A class with fewer than five days is merged with its neighbour.

\textbf{Temperature.} Two forms are fitted: a natural cubic spline (five degrees of freedom), which lets the data draw the curve, and a line with one change of slope at a temperature that is itself estimated, by profiling the deviance over a grid from $-$8 to 26\,$^\circ$C. The second is the form of the earlier analyses, here on the percentage scale and with the two segments joined.

\textbf{Uncertainty.} Consecutive days resemble each other, so standard errors that assume independent days are too small. The intervals reported are robust to heteroskedasticity and autocorrelation (Newey--West, seven lags); the interval for the change of slope comes from a moving-block bootstrap (blocks of 14 consecutive days, 300 replicates). The dispersion parameter is set so that the Pearson statistic equals its degrees of freedom.

\textbf{Season against weather.} Temperature, day length and the calendar move together over the year. Three devices are used: the deviance accounted for by calendar-and-season terms alone, by weather terms alone and by both; a model in which the season terms are replaced by one constant per calendar month, so that weather effects are estimated only from days of the same month; and, for the loop, an hourly model in which the same clock hour is sometimes light and sometimes dark.

\textbf{Location.} The counters stand at different points of a street that runs from a more residential west end towards downtown, and they are not the same instruments. Location is therefore a parameter of every model: each counter has its own level and its own response to every condition, which is what fitting one model per counter means. A further model (Section~\ref{sec:location}) puts the four counters on the street together, with a location term and its interaction with every other term, to test whether each effect is the same at every location. A difference between two counters is read as a difference between places and instruments, never as one counter contradicting another.

\textbf{Downtime and gaps.} The camera sensors have periods of downtime, some of them weeks long (Appendix~\ref{app:coverage}). The analysis accounts for them in three ways. A day enters only if its count is complete and valid (Section~2.1); a partial day is never used as if it were a low count. No missing day or hour is filled in or interpolated. And no total or average is taken across a gap: every estimate comes from a model in which a day is compared with days of the same time of year, day type and weather, so a period without data shortens the record without shifting the estimates. The same holds for the loop\textquoteright{}s excluded days and the Girouard detector\textquoteright{}s incomplete days.

\textbf{What the models cannot show.} They describe association in the record, not what any person would do. They cannot separate temperature from other things that change with the season (school terms, holidays abroad, habits). Weather is measured at the airport. The loop\textquoteright{}s record covers one winter.

\section{Temperature}
''' + fig('temperature-scatter', 'temperature_scatter', 'Daily count against daytime temperature, days marked by precipitation. Black line: median of the days without precipitation, by 2.5-degree band.', 0.95) + r'''
Figure~\ref{fig:temperature_scatter} shows the raw relation. Figure~\ref{fig:temperature_curve} shows the fitted response with everything else held fixed, each series relative to its own level at 20\,$^\circ$C.
''' + fig('temperature-curve', 'temperature_curve', 'Fitted response to temperature (spline model), relative to 20\\,$^\\circ$C.', 0.85) + r'''
\begin{center}\small\begin{tabular}{@{}rrrrrrr@{}}\toprule
Daytime temperature ($^\circ$C) & King Edward & Kensington loop & Draper & Girouard detector & BIXI station & City counters\\\midrule
''' + curve_rows + r'''
\bottomrule\multicolumn{7}{@{}l}{\footnotesize Count relative to the same day at 20\,$^\circ$C (= 100), spline model. BIXI: regular season only.}\end{tabular}\end{center}

\textbf{Slopes.} With temperature as a line with one change of slope:
\begin{center}\small\begin{tabular}{@{}lp{2.9cm}p{3.2cm}p{3.2cm}p{3.2cm}@{}}\toprule
Series & Change of slope, $^\circ$C (bootstrap 95\,\%) & Below it: \% per degree & Above it: \% per degree & Below it, within calendar months\\\midrule
''' + slope_rows + r'''
\bottomrule\end{tabular}\end{center}
On the four Terrebonne series each degree below the change of slope goes with ''' + cold_span + r'''\,\% more bicycles, and the estimate is the same when only days of the same calendar month are compared (last column). The BIXI station and the City counters show smaller slopes (''' + f"{N['bixi']['slope_cold_pct']:.1f} and {N['city']['slope_cold_pct']:.1f}" + r'''\,\%). Above the change of slope the count is flat or falls slightly.

\textbf{Where the slope changes.} The lowest deviance is at ''' + ', '.join(f"{N[s]['bp']:g}" for s in TER) + r'''\,$^\circ$C for King Edward, the Kensington loop, Draper and the Girouard detector, but the bootstrap intervals are wide (Appendix~\ref{app:bp}): the response bends gradually, as the spline shows, rather than at a point. The spline and the two-segment line fit about equally well (Appendix~\ref{app:aic}); a single straight line on the log scale fits worse on every series.

\textbf{Is there a second change in the cold?} Adding a change of slope at 0\,$^\circ$C to the model:
\begin{center}\small\begin{tabular}{@{}lrp{3.6cm}p{3.6cm}r@{}}\toprule
Series & Days below 0\,$^\circ$C & Below 0\,$^\circ$C: \% per degree & 0\,$^\circ$C to the change of slope: \% per degree & $p$ (difference)\\\midrule
''' + cold_rows + r'''
\bottomrule\end{tabular}\end{center}
On the Terrebonne series the two slopes are not distinguishable. The earlier analyses, which fitted two straight lines to the counts themselves, placed a change of slope at $-$1\,$^\circ$C (air temperature) or $-$5\,$^\circ$C (feels-like temperature): a count that falls by a constant percentage per degree traces a curve that flattens towards zero, and two straight lines fitted to that curve meet near where it flattens. The City counters do show a flatter slope below 0\,$^\circ$C.

\section{Wind chill}
The wind-chill index and the daytime temperature are almost the same variable over a year (correlation ''' + f"{west['corr_temp_chill']:.3f}" + r'''). A model with the wind-chill index in place of temperature and wind has an AIC that differs by ''' + f"{sg(-max(dchill[s] for s in TER), 1)} to {sg(-min(dchill[s] for s in TER), 1)}" + r''' on the Terrebonne series (negative values favour wind chill; Appendix~\ref{app:aic}): small differences, three of four in its favour, not enough to say that riders respond to wind chill rather than to temperature. Wind as a separate term goes with ''' + cell('west', 'wind_per_10kmh') + r'''\,\% per 10\,km/h at King Edward and is not distinguishable from zero on the other three Terrebonne series.

\section{Rain, snow and wind}
''' + fig('effects', 'effects', 'Change in the daily count associated with each condition, temperature and time of year held fixed.', 0.92) + r'''
\begin{center}\scriptsize\setlength{\tabcolsep}{3pt}\begin{tabular}{@{}lllllll@{}}\toprule
Condition & King Edward & Kensington loop & Draper & Girouard detector & BIXI station & City counters\\\midrule
''' + eff_rows + r'''
\bottomrule\multicolumn{7}{@{}p{16cm}}{\scriptsize Percentage change in the daily count (95\,\% interval), compared with a day without the condition (for the day types, with a weekday). --: fewer than five such days, or not applicable.}\end{tabular}\end{center}
Number of days behind each estimate:
\begin{center}\footnotesize\begin{tabular}{@{}p{4.6cm}rrrrrr@{}}\toprule
Condition & King Edward & Kensington loop & Draper & Girouard detector & BIXI station & City counters\\\midrule
''' + days_rows + r'''
\bottomrule\end{tabular}\end{center}
Light rain (under 2\,mm in 24 hours) is not distinguishable from none on the camera sensors, which count 08:00--16:00; the two 24-hour counters on the street, the loop and the Girouard detector, show a reduction. Snow on the ground goes with a third to a half fewer bicycles at King Edward, Draper and Kensington and with no measurable change at the Girouard detector (''' + cell('gir', 'snow_on_ground') + r'''\,\%, 88 such days); the record does not say why the east end differs. The effects are multiplicative: on a January day that would see 20 bicycles in the window, 2 to 10\,mm of rain removes about four; on a June day that would see 300, about sixty. Snow on the ground carries the persistence of a snowfall: once it is in the model, the snowfall of the day before adds little.

\section{Day length, season and darkness}
''' + fig('season-weather', 'season_weather', 'Share of the deviance of daily counts accounted for by the two sets of terms.', 0.85) + r'''
\begin{center}\footnotesize\begin{tabular}{@{}lrrrrrr@{}}\toprule
 & \multicolumn{3}{c}{Deviance accounted for (\%)} & \multicolumn{3}{c}{of which (\%)}\\\cmidrule(lr){2-4}\cmidrule(l){5-7}
Series & Calendar and season alone & Weather alone & Both & Either & Weather only & Calendar and season only\\\midrule
''' + blk_rows + r'''
\bottomrule\end{tabular}\end{center}
Most of what the models account for can be credited to either set of terms: the time of year predicts the weather, and the weather predicts the time of year. The record cannot say how much of the winter low is cold and snow and how much is the season as such. What it does say is that weather matters \emph{within} the season: the weather-only share is ''' + f"{100 * min(BLK.loc[s, 'unique_weather'] for s in TER):.0f} to {100 * max(BLK.loc[s, 'unique_weather'] for s in TER):.0f}" + r'''\,\% on the Terrebonne series, and the temperature slope is unchanged when estimated inside calendar months.

''' + fig('daylight', 'daylight', 'Left: the share of a Telraam sensor\\textquoteright{}s daylight total that falls in the fixed window. Right: the share of the loop\\textquoteright{}s 24-hour total in the same window.', 0.95) + r'''
\textbf{What a daylight-only sensor sees.} In June the 08:00--16:00 window holds a little over half of a Telraam sensor\textquoteright{}s daily total; in December it holds more than 80\,\%, because there is little daylight outside it. A year-round comparison of Telraam daily totals therefore mixes a change in riding with a change in counting hours. On the loop, which counts day and night, the same window holds ''' + wspan + r'''\,\% of the 24-hour total in every month of the hourly record, so the fixed window is a stable part of the day.

\textbf{Darkness at the same clock hour.} The loop\textquoteright{}s hourly record (''' + f"{H['n_hours']:,} hours between 06:00 and 22:00 on {H['n_days']} days, {H['dark_evening_hours']:,} of them after sunset and {H['dark_morning_hours']} before sunrise" + r''') allows a direct comparison: the same hour of the same type of day, in the same month and at the same temperature, when the sun is up and when it is down. An evening hour after sunset carries ''' + he('dark_eve') + r''' fewer bicycles, a morning hour before sunrise ''' + he('dark_morn') + r'''. In the same model an hour with rain observed carries ''' + he('rain_h') + r''' and an hour with snow observed ''' + he('snow_h') + r'''. This is one site and one direction; with month constants in the model, the comparison rests mostly on the weeks around the clock changes and the equinoxes.

\section{Snowfall, the days after, and snow loading}
''' + fig('snow-lags', 'snow_lags', 'Winter days: change in the count per 5\\,cm of snowfall on the day and on each of the seven days before.', 0.95) + r'''
On winter days (November~16 to March~31), with temperature, rain, wind, day type and snow on the ground in the model:
\begin{center}\footnotesize\scriptsize\begin{tabular}{@{}rllll@{}}\toprule
Days after the snowfall & King Edward & Kensington loop & Draper & Girouard detector\\\midrule
''' + lag_rows + r'''
\bottomrule\multicolumn{5}{@{}l}{\footnotesize Percentage change per 5\,cm of snow (95\,\% interval).}\end{tabular}\end{center}
The day of a snowfall shows the clearest reduction (''' + f"{min(-LAG[(LAG.lag_days == 0)].pct_per_5cm):.0f} to {max(-LAG[(LAG.lag_days == 0)].pct_per_5cm):.0f}" + r'''\,\% per 5\,cm; the interval excludes zero at ''' + ' and '.join(NAME[s] if s != 'gir' else 'the Girouard detector' for s in TER if LAG[(LAG.series == s) & (LAG.lag_days == 0)].hi.iloc[0] < 0) + r'''). On the following days the estimates scatter around zero and a few negative values, with wide intervals and no pattern common to the four series; winter counts are small (a few dozen a day), each series has ''' + f"{min(N[s]['winter_days'] for s in TER):.0f} to {max(N[s]['winter_days'] for s in TER):.0f}" + r''' winter days, and snow on the ground already carries part of the after-effect. An average over snowfall episodes was also computed (\texttt{snow\_episodes\_summary.csv}); with fewer than ten episodes of 10\,cm or more per series it is too noisy to read.

\textbf{Snow-loading days.}
\begin{center}\small\begin{tabular}{@{}llrrp{3.4cm}p{3.4cm}@{}}\toprule
Series & Sector & Winter days & of which loading days & Loading day: change (\%) & Temperature: \% per degree (winter only)\\\midrule
''' + load_rows + r'''
\bottomrule\end{tabular}\end{center}
On the days the City loaded snow in the sector that contains the counter, the counts are not distinguishable from those of other winter days with the same temperature and snow. The intervals are wide enough to contain a reduction of a quarter or more as well as no change; the record does not settle the question. In winter alone, each degree goes with ''' + f"{min(eff(s, 'temp_per_degree', 'winter_lags').pct for s in TER):.0f} to {max(eff(s, 'temp_per_degree', 'winter_lags').pct for s in TER):.0f}" + r'''\,\% more bicycles on the four series.

\section{Location: what differs along the street}\label{sec:location}
The counters do not measure the same thing at the same place, and none of the differences between them is a discrepancy. The street runs from a more residential west end towards downtown; a counter further east can be expected to see more through traffic and more commuters, and the resident population around the counters also differs:
\begin{center}\footnotesize\resizebox{\textwidth}{!}{\begin{tabular}{@{}lrrrrll@{}}\toprule
Counter (west to east) & From the west end (km) & To downtown (km) & Residents within 500\,m & Residents per km$^2$ & Motor traffic & Instrument\\\midrule
''' + '\n'.join(f"{NAME.get(r.series, r.location)} & {r.km_from_lane_west_end:.2f} & {r.km_to_downtown_reference:.1f} & {r.residents_within_500m_2021:,} & {r.residents_per_km2_within_500m:,} & one-way {r.motor_traffic_one_way} & {INSTR[r.series]} \\\\" for r in LCT.itertuples()) + r'''
\bottomrule\multicolumn{7}{@{}p{16cm}}{\footnotesize Distances in a straight line, the first from the west end of the lane; downtown reference point: avenue McGill College at rue Sainte-Catherine Ouest. Residents: 2021 Census, dissemination areas, weighted by the share of each area within 500\,m of the counter (Statistics Canada).}\end{tabular}}\end{center}
\textbf{What location can and cannot be adjusted for.} Each counter is its own location in every model of this note, with its own level and its own responses. An adjustment for « centrality » as such, a coefficient for distance to downtown or for population density, cannot be estimated from this record: there are four counters on the street, of three different kinds (two camera sensors read over eight daytime hours in both directions, one loop and one detector counting 24 hours in one direction each), so position and instrument cannot be told apart, and four points do not determine a gradient. The table above gives the context in which each counter\textquoteright{}s figures are to be read.

\textbf{The one like-for-like comparison of two locations.} The two camera sensors are the same instrument, read in the same window. On the days valid at both:
\begin{center}\small\resizebox{\textwidth}{!}{\begin{tabular}{@{}lrrrl@{}}\toprule
Days & Number & King Edward, mean a day & Draper, mean a day & Draper over King Edward (95\,\% interval)\\\midrule
''' + '\n'.join(f"{r.days.replace('–', '--')} & {r.n_days} & {r.king_edward_mean:.0f} & {r.draper_mean:.0f} & {r.draper_over_king_edward:.2f} ({r.lo:.2f} to {r.hi:.2f}) \\\\" for r in DK.itertuples()) + r'''
\bottomrule\end{tabular}}\end{center}
Draper, 1.4\,km further east, counts about a fifth more than King Edward in the same eight hours, and proportionately more in winter (the winter interval is wide). This is a difference between two places on the street.

\textbf{Do the effects differ by location?} A single model of the four counters on the street (''' + f"{int(LT.n_days.iloc[0]):,}" + r''' counter-days), with a location term and its interaction with every other term, and standard errors clustered by date because the counters share each day\textquoteright{}s weather, tests whether each effect is the same at the four locations:
\begin{center}\small\begin{tabular}{@{}lrrrrrrr@{}}\toprule
 & \multicolumn{4}{c}{Effect at each location (\%)} & \multicolumn{3}{c}{Same at all four?}\\\cmidrule(lr){2-5}\cmidrule(l){6-8}
Term & King Edward & Kensington & Draper & Girouard & $\chi^2$ & df & $p$\\\midrule
''' + '\n'.join(loc_row(r) for r in LT.itertuples()) + r'''
\bottomrule\multicolumn{8}{@{}p{15.5cm}}{\footnotesize Change of slope fixed at 20\,$^\circ$C in this model so that the slopes are comparable. A small $p$ means the effect differs by location.}\end{tabular}\end{center}
The response to temperature below 20\,$^\circ$C is close along the street, a little steeper at the west end than at the east end (''' + f"{LEv('temperature below 20 °C (per degree)', 'west'):.1f} against {LEv('temperature below 20 °C (per degree)', 'gir'):.1f}" + r'''\,\% per degree; the test is borderline). The effects that clearly differ are those of the weekend, of light and heavy rain, and of snow on the ground. The weekend and light-rain differences follow the instrument: the two 24-hour counters (the loop and the Girouard detector) show them and the two camera sensors, read 08:00--16:00, do not. Snow on the ground goes with a large reduction at King Edward, Kensington and Draper and with none at Girouard, at the east end. The record cannot say how much of any of this is the place and how much the instrument.

The BIXI station and the City\textquoteright{}s counters elsewhere respond less steeply to temperature than the counters on the street; they are different quantities again (trips at a dock; a sum of counters on other streets) and are shown for context.

\section{Year to year, after weather}
\textbf{Is the weather of each year allowed for?} Yes. The year term is estimated in the same model as temperature, rain, snowfall, snow on the ground and wind. A year that was colder, wetter or snowier is therefore compared with what the model expects for that weather, not with the raw count of a milder year. To make the part played by the weather visible, the comparison is shown here in three steps:
\begin{enumerate}
\item \emph{Plain comparison, no model:} the same calendar dates, valid in both years; the ratio of the two totals. It accounts for downtime (a date enters only if both years have it) but not for the weather.
\item \emph{Model with day type and time of year only,} no weather term.
\item \emph{The main model,} with the weather terms: the figure quoted in this note.
\end{enumerate}
\begin{center}\footnotesize\begin{tabular}{@{}llrlll@{}}\toprule
Series & Counting years & Dates in both & 1. Plain, same dates (\%) & 2. Season only (\%) & 3. With weather (\%)\\\midrule
''' + ystep_rows + r'''
\bottomrule\multicolumn{6}{@{}p{15.5cm}}{\footnotesize Counting years run from August 15. 95\,\% intervals: step 1, bootstrap over 14-day blocks of dates; steps 2 and 3, autocorrelation-robust. Comparisons with fewer than 30 dates in both years are not shown.}\end{tabular}\end{center}
How the weather differed, on the dates both years have (first year / later year):
\begin{center}\footnotesize\resizebox{\textwidth}{!}{\begin{tabular}{@{}lrrrrr@{}}\toprule
Comparison & Daytime temp. ($^\circ$C) & Days below $-$10\,$^\circ$C & Snowfall (cm) & Days, snow on ground & Rain (mm)\\\midrule
''' + yweather_rows + r'''
\bottomrule\end{tabular}}\end{center}
The weather matters to the answer. On the dates King Edward has in both of its first two years, the second year was colder (''' + f"{wxw.daytime_temp_mean_year:.1f} against {wxw.daytime_temp_mean_ref:.1f}" + r'''\,$^\circ$C by day) and much snowier (''' + f"{wxw.snowfall_cm_year:.0f} against {wxw.snowfall_cm_ref:.0f}\\,cm of snow, {wxw.snow_on_ground_days_year:.0f} against {wxw.snow_on_ground_days_ref:.0f}" + r''' days with snow on the ground). Compared plainly, the second year is ''' + st(s1w, 'step1') + r'''\,\%; with the time of year alone, ''' + st(s1w, 'step2') + r'''\,\%; once the weather is in the model, ''' + st(s1w, 'step3') + r'''\,\%: what looked like a lower second year is accounted for by a harder winter. At Draper the difference narrows with the weather but remains (''' + st(s1e, 'step2') + r''' to ''' + st(s1e, 'step3') + r'''\,\%). King Edward\textquoteright{}s autumn of 2026 is higher than its autumn of 2024 at every step (''' + st(s1w3, 'step1') + r'''\,\% plainly, ''' + st(s1w3, 'step3') + r'''\,\% with the weather); the two autumns were close in temperature (''' + f"{yw('west', '2026-27').daytime_temp_mean_year:.1f} against {yw('west', '2026-27').daytime_temp_mean_ref:.1f}" + r'''\,$^\circ$C by day) and the autumn of 2026 had more rain (''' + f"{yw('west', '2026-27').rain_mm_year:.0f} against {yw('west', '2026-27').rain_mm_ref:.0f}" + r'''\,mm).

The adjustment has its own limits: it assumes that riders respond to a given temperature or snowfall in the same way each year, the weather is measured at the airport, and the state of the lane itself (cleared or not) is not observed.

The year terms of the main model, for every series that has them:
\begin{center}\small\begin{tabular}{@{}llrp{4.2cm}@{}}\toprule
Series & Counting years (from August 15) & Days in the later year & Change (\%, 95\,\% interval)\\\midrule
''' + yr_rows + r'''
\bottomrule\end{tabular}\end{center}
These figures are to be read with care. \textbf{Downtime is accounted for:} only days with a complete, valid count enter the models, nothing is filled in, and the year term compares each day with days of the same time of year, day type and weather. A month missing in one year therefore is not read as a decline; it simply contributes no days, and the year term rests on the months that year does have (on the model\textquoteright{}s assumption that the seasonal pattern is the same from year to year). What a year term cannot exclude is anything else that differs between the years: a camera sensor\textquoteright{}s field of view can change when it is remounted, and the 2026--27 counting year so far holds only August~15 to early November. King Edward\textquoteright{}s 2026--27 figure compares that autumn with the autumn of 2024. Draper\textquoteright{}s and the BIXI station\textquoteright{}s later years are merged (too few days after August~15, 2026), and the City counters\textquoteright{} 2026--27 term is not shown (its first year holds no autumn to compare with). The loop and the Girouard detector each have about one year and no such term.

\section{How well the models predict}
Each calendar month in turn was left out, the model fitted on the rest, and the month predicted:
\begin{center}\small\begin{tabular}{@{}lrrrrr@{}}\toprule
 & & \multicolumn{2}{c}{Median absolute error (\%)} & \multicolumn{2}{c}{$R^2$ on the log scale}\\\cmidrule(lr){3-4}\cmidrule(l){5-6}
Series & Days predicted & Fitted & Month left out & Fitted & Month left out\\\midrule
''' + cv_rows + r'''
\bottomrule\end{tabular}\end{center}
The typical day is predicted to within about a fifth to a quarter of its count, and little accuracy is lost on a month the model has not seen. A fifth of a small winter count is a few bicycles.

\section{Limits}
\begin{itemize}
\item \textbf{Daylight-only sensors.} The Telraam figures are 08:00--16:00 counts. They say nothing about evening and night riding, and their levels are never to be compared with the loop\textquoteright{}s.
\item \textbf{Gaps (accounted for, not filled).} Only complete, valid days are used and each is compared with like days, so downtime does not bias the estimates; it does reduce the days available. King Edward has no valid day in February 2026 and few in December 2025 and July 2026; Draper has none from February to April 2026. The winter of 2025--26 is therefore thinly covered by the camera sensors and carried mostly by the loop and the Girouard detector.
\item \textbf{The Girouard detector: one direction, one winter,} and a camera-type detector whose counting method the City\textquoteright{}s page does not detail.
\item \textbf{One loop site, one winter, one direction} in the models; the westbound channel is not used after the fault of March 2026, and for consistency not before.
\item \textbf{Weather at the airport,} 9\,km away; precipitation as 24-hour totals; the state of the lane itself (cleared or not, icy or not) is not observed. Snow on the ground at the airport stands in for it.
\item \textbf{Season and weather are confounded} and no model can fully separate them from this record.
\item \textbf{Association, not cause.} A percentage per degree describes days in the record; it does not predict what would happen under conditions the record does not contain.
\item \textbf{Uptime.} Telraam hours with an uptime under 0.5 are dropped; whether the remaining counts are already scaled for uptime is not documented.
\end{itemize}

\appendix
\section{Valid days by month}\label{app:coverage}
\begin{center}\footnotesize\begin{tabular}{@{}lrrrrrr@{}}\toprule
Month & King Edward & Kensington loop & Draper & Girouard detector & BIXI station & City counters\\\midrule
''' + cov_rows + r'''
\bottomrule\multicolumn{7}{@{}p{12cm}}{\footnotesize Loop: days valid in the daily table (both directions); the models use the eastbound channel, to May~10, 2026. BIXI: days with at least one trip.}\end{tabular}\end{center}

\section{Model comparison}\label{app:aic}
\begin{center}\small\begin{tabular}{@{}lrrrrrr@{}}\toprule
 & \multicolumn{3}{c}{AIC, temperature as} & \multicolumn{2}{c}{AIC, without the wind term} & \\\cmidrule(lr){2-4}\cmidrule(lr){5-6}
Series & one line & two segments & spline & temperature & wind chill & Correlation, temperature and wind chill\\\midrule
''' + aic_rows + r'''
\bottomrule\end{tabular}\end{center}
Lower is better; differences of less than about 2 are not meaningful. AIC values are comparable only within a row.

\section{Where the slope changes: deviance profile}\label{app:bp}
''' + fig('breakpoint', 'breakpoint', 'Deviance of the two-segment model as the change of slope is moved, each series relative to its own minimum.', 0.85, 'H') + r'''

\section{The earlier analyses and what was kept}\label{app:matlab}
Between September 2024 and May 2026 the author explored the Telraam counts in MATLAB. Those scripts were read before this work; none of their code is used here. In summary:
\begin{center}\footnotesize\begin{tabular}{@{}p{3.3cm}p{6.6cm}p{5.6cm}@{}}\toprule
Earlier analysis & What it did & Here\\\midrule
Regressions of February 2025 & Least-squares fits of daily counts on temperature or feels-like temperature, squared terms, precipitation; two straight lines with a change of slope found by search ($-$1 and $-$5\,$^\circ$C); King Edward only, 290 days & Count model on the percentage scale; change of slope estimated with an interval, segments joined; the cold change of slope tested and not found \\
Sunset adjustment & Counts up to 15:00 multiplied by a fixed ratio (1.65 on weekdays, 1.37 on weekends) to stand for the whole day & Replaced by the fixed 08:00--16:00 window, with no scaling \\
Filling of dark hours & Five ways to fill the hours after sunset from a reference daily profile & Not kept: no count is estimated for hours the sensor did not see \\
Daily weather regression of November 2025 & Least squares on before-15:00 counts with temperature, precipitation, wind, weekend and a linear trend; ten interaction tests; weather classes compared by $t$-tests & Kept as the main model, with a count distribution, season terms in place of the trend and autocorrelation-robust intervals \\
Weekly season-and-anomaly split & Share of variance from a seasonal baseline and from weather anomalies, weekly & Kept, daily, as the deviance shares and the within-month model \\
Lagged-snow regression and snow-event averages, winter 2024--25 & Ten lags of a snow proxy (precipitation on days below 0\,$^\circ$C); average response by snowfall class & Kept with measured snowfall and snow on the ground, two winters, four series, and the City\textquoteright{}s loading record \\
Winter retention, storm recovery, composite scores & Ratios of winter to summer counts by mode; one storm; ad hoc scores & Not kept \\
Weather source & A commercial city-level feed & Environment and Climate Change Canada, Montréal-Trudeau \\
\bottomrule\end{tabular}\end{center}

\section{Sources}
Environment and Climate Change Canada, historical climate data, MONTREAL INTL A (7025251), downloaded November~10, 2026. Telraam (citizen-operated sensors; the counts belong to Telraam). Arrondissement de Côte-des-Neiges--Notre-Dame-de-Grâce, loop counter at Terrebonne/Kensington, access requests 2026-300 (released June~4, 2026) and 2026-581 (released October~9, 2026). Ville de Montréal open data: permanent bicycle counters (files of November~7, 2026), snow-removal transactions; CC~BY~4.0. BIXI Montréal open data, trip history 2024--2026 (downloaded November~10, 2026; listed by the City\textquoteright{}s portal under CC~BY~4.0, attribution to BIXI Montréal). Details and licences: the folder\textquoteright{}s README.
\end{document}
'''

# ---------------------------------------------------------------- deck
def fr(title, body): return f'\\begin{{frame}}{{{title}}}\n{body}\n\\end{{frame}}\n'
def ffig(title, typ, name, note='', w=0.78): return fr(title, f'\\centering\\includegraphics[width={w}\\textwidth,height=0.76\\textheight,keepaspectratio]{{../derived/figures/{typ}/{name}_en.png}}' + (f'\\\\[0.2em]{{\\scriptsize {note}}}' if note else ''))
DMARK = '' if FINAL else r'\setbeamertemplate{footline}{\hfill{\tiny\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, ' + TODAY + r'}\quad\insertframenumber}\hspace{1em}\vspace{0.4em}}'
DECK = r'''\documentclass[aspectratio=169,10pt]{beamer}\usetheme{default}\usecolortheme{seahorse}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{helvet}\usepackage{booktabs,amsmath}
''' + DMARK + r'''
\title{Weather, daylight, snow and bicycle traffic on rue de Terrebonne}\subtitle{Six count series, August 2024 to November 2026: methods in brief and the main results}\author{Rick Hoge, PhD}\institute{Terrebonne-open-sources}\date{''' + TODAY + r'''}
\begin{document}
\begin{frame}\titlepage\end{frame}
''' + fr('The question and the sources', r'''\begin{itemize}
\item How does the number of bicycles counted on rue de Terrebonne vary with temperature, wind chill, rain, snow, daylight and snow loading?
\item Six series, each analysed on its own and never compared in level:
\begin{itemize}\footnotesize
\item \textbf{King Edward} and \textbf{Draper}: citizen-operated Telraam camera sensors, bicycles 08:00--16:00 (''' + f"{west['n_days']} and {east['n_days']}" + r''' valid days from August and September 2024)
\item \textbf{Kensington loop}: the borough\textquoteright{}s counter, eastbound, 24 h (''' + f"{loop['n_days']}" + r''' days, July 27, 2025 to May 10, 2026; hourly release of June 4, 2026)
\item \textbf{Girouard detector}: the City\textquoteright{}s detector at the east end, westbound, 24 h (''' + f"{N['gir']['n_days']}" + r''' days, October 24, 2025 to October 15, 2026)
\item \textbf{BIXI station} Grand Boulevard / de Terrebonne: trips starting or ending, regular season
\item \textbf{City counters}: twelve loop counters elsewhere in Montréal, as a reference
\end{itemize}
\item Weather: Environment and Climate Change Canada, Montréal-Trudeau (daily rain, snowfall, snow on the ground; hourly temperature and wind). Snow loading: the City\textquoteright{}s record for the sector that contains each counter (CDN-301, CDN-111).
\end{itemize}''') + ffig('The record', 'overview', 'overview', 'Each panel has its own scale.', 0.55) + fr('Method (1): what is counted', r'''\begin{itemize}
\item A Telraam sensor counts \textbf{only in daylight}: about 9 hours in December, 16 in June. Its daily total moves with the length of the day even if riding does not.
\item Every Telraam figure here is the count in a \textbf{fixed window, 08:00--16:00}, daylight all year. The evening peak is left out.
\item Valid day: at least 8 reported hours and 6 hours of uptime, and all eight window hours with uptime of 0.5 or more. Nothing is interpolated.
\item The loop: eastbound channel only (the westbound channel under-counts from about March 1, 2026).
\item BIXI: a day without a trip is absent from the file, not a zero; April 15 to November 15 only in the models.
\end{itemize}''') + fr('Method (2): the model', r'''\begin{itemize}
\item One \textbf{negative binomial regression per series}, log link: every effect is a percentage change, so series can be set side by side without comparing levels.
\item Terms: day type, holidays, counting year, time of year (two annual harmonics), daytime temperature, rain and snowfall in classes, snow on the ground, wind, snowfall of the day before.
\item Temperature: a spline, and a line with one change of slope whose position is estimated.
\item Intervals robust to autocorrelation (Newey--West); moving-block bootstrap for the change of slope.
\item Checks: effects re-estimated inside calendar months; each month left out and predicted; wind chill in place of temperature; an hourly model of the loop for darkness.
\end{itemize}''') + ffig('Temperature: the raw relation', 'temperature-scatter', 'temperature_scatter', 'Each panel has its own scale. Black line: median of the days without precipitation.', 0.62) + ffig('Temperature: the fitted response, relative to 20\\,$^\\circ$C', 'temperature-curve', 'temperature_curve', f"Terrebonne series: {cold_span}\\,\\% more bicycles per degree up to roughly 20\\,$^\\circ$C; at 0\\,$^\\circ$C, {cspan(0)}\\,\\% of the count at 20\\,$^\\circ$C; at $-$10\\,$^\\circ$C, {cspan(-10)}\\,\\%.", 0.66) + fr('Temperature: what the fits say', r'''\begin{itemize}
\item Below roughly 20\,$^\circ$C, each degree goes with ''' + cold_span + r'''\,\% more bicycles on the four Terrebonne series; the same inside calendar months.
\item Above that the count is flat or falls slightly. The position of the bend is poorly determined (intervals of ten degrees or more): the response bends gradually.
\item \textbf{No second change of slope in the cold}: below 0\,$^\circ$C the percentage slope is not distinguishable from the slope between 0 and 20\,$^\circ$C.
\item The $-$1 and $-$5\,$^\circ$C thresholds of the earlier analyses came from fitting straight lines to the counts themselves.
\item Wind chill in place of temperature and wind fits about as well (correlation ''' + f"{west['corr_temp_chill']:.3f}" + r'''); the data cannot separate them.
\end{itemize}''') + ffig('Rain, snow and wind at a given temperature and time of year', 'effects', 'effects', '', 0.66) + ffig('Season or weather?', 'season-weather', 'season_weather', 'Most of what the models account for can be credited to either: the record cannot fully separate season from weather. Weather effects estimated inside calendar months are the same.', 0.74) + ffig('Day length: what a daylight-only sensor sees', 'daylight', 'daylight', f"On the loop (hourly), the same evening hour carries {he('dark_eve')} fewer bicycles after sunset than before, at the same temperature and in the same month.", 0.84) + ffig('Snowfall and the days after (winter days)', 'snow-lags', 'snow_lags', 'The day of the snowfall shows the clearest reduction; no pattern common to the four series on the following days. Snow on the ground carries part of the after-effect.', 0.9) + fr('Snow-loading days', r'''\begin{center}\small\begin{tabular}{llrrl}\toprule
Series & Sector & Winter days & Loading days & Change on a loading day (\%)\\\midrule
''' + '\n'.join(f"{NAME[s]} & {N[s]['loading_sector']} & {N[s]['winter_days']:.0f} & {N[s]['winter_loading_days']:.0f} & {cell(s, 'loading_day', 'winter_lags')} \\\\" for s in TER) + r'''
\bottomrule\end{tabular}\end{center}
\begin{itemize}
\item With temperature, snowfall, snow on the ground, rain, wind and day type in the model, loading days are not distinguishable from other winter days.
\item The intervals are wide: they contain no change and a reduction of a quarter or more. The record does not settle the question.
\end{itemize}''') + fr('Location is a parameter: the counters stand at different points of the street', r'''\begin{center}\resizebox{0.92\textwidth}{!}{\begin{tabular}{lrrrl}\toprule
Counter (west to east) & To downtown (km) & Residents within 500\,m & Residents per km$^2$ & Instrument\\\midrule
''' + '\n'.join(f"{NAME.get(r.series, r.location)} & {r.km_to_downtown_reference:.1f} & {r.residents_within_500m_2021:,} & {r.residents_per_km2_within_500m:,} & {INSTR[r.series]} \\\\" for r in LCT.itertuples()) + r'''
\bottomrule\end{tabular}}\end{center}
\begin{itemize}
\item Each counter is analysed as its own location. A difference between two counters is a difference between places and instruments, not a discrepancy.
\item Like for like (the two camera sensors, same window, same days): Draper counts ''' + f"{DK.iloc[0].draper_over_king_edward:.2f} times King Edward ({DK.iloc[0].lo:.2f} to {DK.iloc[0].hi:.2f})" + r'''.
\item Tested in one model of the four counters: the response to temperature is close along the street; the effects of the weekend, rain and snow on the ground differ by location.
\item A coefficient for « centrality » cannot be estimated: four counters of three kinds.
\end{itemize}''') + fr('Year to year: is the weather allowed for?', r'''\begin{itemize}
\item Yes: the year term is estimated in the same model as temperature, rain, snowfall, snow on the ground and wind. Downtime is accounted for (only valid days; like compared with like).
\end{itemize}
\begin{center}\resizebox{0.98\textwidth}{!}{\begin{tabular}{llrlll}\toprule
Series & Years & Dates in both & 1. Plain, same dates (\%) & 2. Season only (\%) & 3. With weather (\%)\\\midrule
''' + ystep_rows + r'''
\bottomrule\end{tabular}}\end{center}
\begin{itemize}
\item King Edward\textquoteright{}s second year was colder and much snowier than its first (''' + f"{wxw.snowfall_cm_year:.0f} against {wxw.snowfall_cm_ref:.0f}" + r'''\,cm of snow on the common dates): the apparent drop disappears once the weather is in the model.
\item The result is specific to each location (King Edward at the west end, Draper further east); two to three years do not establish a trend at either.
\end{itemize}''') + fr('How well the models predict', r'''\begin{center}\small\begin{tabular}{lrrrrr}\toprule
 & & \multicolumn{2}{c}{Median absolute error (\%)} & \multicolumn{2}{c}{$R^2$ (log scale)}\\
Series & Days & Fitted & Month left out & Fitted & Month left out\\\midrule
''' + cv_rows + r'''
\bottomrule\end{tabular}\end{center}
Each calendar month in turn is left out and predicted from the rest.''') + fr('Limits', r'''\begin{itemize}
\item Telraam figures are 08:00--16:00 counts; never compared in level with the loop.
\item Sensor downtime is accounted for: only complete, valid days are used, compared with days of like season and weather; nothing is filled in. It reduces coverage: King Edward has no valid day in February 2026, Draper none from February to April 2026.
\item The loop and the Girouard detector: one winter and one direction each.
\item Weather at the airport (9 km); precipitation as 24-hour totals; the state of the lane is not observed.
\item Season and weather are confounded; the models describe association in the record, not cause.
\item Year-to-year terms absorb anything that differs between years besides the weather (gaps, sensor position); see the note.
\end{itemize}''') + fr('Where everything is', r'''\begin{itemize}
\item Note, tables, figures (English and French) and scripts: \url{''' + URL + r'''}
\item Sources: Environment and Climate Change Canada; Telraam (citizen-operated sensors); borough loop counter (access requests 2026-300, released June 4, 2026, and 2026-581, released October 9, 2026); City of Montréal open data (CC BY 4.0); BIXI Montréal open data.
\end{itemize}''') + r'''
\end{document}
'''

os.makedirs(DOCS, exist_ok=True)
# the deck's figures as PNG files named by slide number (07-effects.png = the figure of slide 7), rewritten at each build
import re, shutil, glob
FIGDIR = os.path.join(DOCS, 'deck_figures_en'); os.makedirs(FIGDIR, exist_ok=True)
for old in glob.glob(os.path.join(FIGDIR, '*.png')): os.remove(old)
for n, frame in enumerate(DECK.split('\\begin{frame}')[1:], 1):
    for m in re.finditer(r'\\includegraphics\[[^\]]*\]\{([^}]+)\}', frame):
        src = os.path.normpath(os.path.join(DOCS, m.group(1))); name = os.path.basename(src).replace('_en.png', '.png').replace('_', '-')
        shutil.copyfile(src, os.path.join(FIGDIR, f'{n:02d}-{name}')); print('slide figure', f'{n:02d}-{name}')
for name, tex, runs in (('weather_bike_traffic_note_en', NOTE, 3), ('weather_bike_traffic_deck_en', DECK, 2)):
    open(os.path.join(DOCS, name + '.tex'), 'w', encoding='utf-8').write(tex)
    for _ in range(runs):
        r = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', name + '.tex'], cwd=DOCS, capture_output=True, text=True)
        if r.returncode: print(r.stdout[-2500:]); raise SystemExit(f'pdflatex failed on {name}')
    for ext in ('aux', 'log', 'out', 'toc', 'nav', 'snm'):
        p = os.path.join(DOCS, f'{name}.{ext}')
        if os.path.exists(p): os.remove(p)
    print('built', name, 'version', STAMP)
