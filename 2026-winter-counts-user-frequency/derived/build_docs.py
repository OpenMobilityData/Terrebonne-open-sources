#!/usr/bin/env python3
"""Note (A4, pdflatex) and slide deck (beamer 16:9), English, from summary.json and the figures written by winter_counts_analysis.py.
Usage: python3 build_docs.py  (writes winter_counts_user_frequency_note_en.pdf and winter_counts_user_frequency_deck_en.pdf)"""
import json, os, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); S = json.load(open(os.path.join(HERE, 'summary.json')))
STAMP = datetime.datetime.now().strftime('%Y-%m-%d'); URL = 'https://openmobilitydata.github.io/Terrebonne-open-sources/2026-winter-counts-user-frequency/'
esc = lambda s: str(s).replace('&', '\\&').replace('%', '\\%').replace("'", "\\textquoteright{}").replace('–', '--').replace('≥', '$\\geq$').replace('≤', '$\\leq$').replace('°', '$^\\circ$')
f0 = lambda x: f'{x:,.0f}'; f1 = lambda x: f'{x:,.1f}'; pc = lambda x: f'{100 * x:.0f}\\,\\%'
co, w2, bf, bd, cr, sv, si, sc, nb, wx, g, yo, sn = S['core'], S['w2'], S['band_fit'], S['bounds'], S['corridor'], S['survey'], S['survey_implied'], S['survey_coverage'], S['nb_regression'], S['winter_ratio_by_weather'], S['girouard_vs_kensington_wb'], S['year_over_year'], S['snapshots']
R = {(r['sensor'], r['start']): r for r in S['ratios']}
ke_aut, ke_win, dr_aut, dr_win = R[('King Edward', '2025-09-01')], R[('King Edward', '2025-12-01')], R[('Draper', '2025-09-01')], R[('Draper', '2025-12-01')]
cov = S['coverage']; dm = S['direction_mapping']; j29 = sn['2025-01-29']; s19 = sn['2024-09-19']
ci = lambda c: f"{c[0]:.0f}--{c[1]:.0f}" if c and c[0] is not None else '--'
TN = {'base': 'base', 'one_way': 'more one-way trips', 'weather_sensitive': 'tail more weather-sensitive', 'survey_literal': 'survey categories literal'}
band_rows = '\n'.join(f"{TN[k]} & {v['N']['daily']:.0f} ({ci(v['ci']['daily'])}) & {v['N']['regular']:.0f} ({ci(v['ci']['regular'])}) & \\textbf{{{v['N_frequent']:.0f}}} ({ci(v['ci']['frequent'])}) & {v['N']['occas']:.0f} ({ci(v['ci']['occas'])}) & {pc(v['share_by_band']['daily'] + v['share_by_band']['regular'])} & {v['fitted_total']:,} \\\\" for k, v in bf.items())
tmpl_rows = '\n'.join(f"\\item \\textbf{{{TN[k]}}}: {esc(v)}" for k, v in S['templates'].items())
tail_rows = '\n'.join(f"{t['rides_per_winter']} & {t['passages_per_person']} & {t['people']:,} \\\\" for t in S['tail_table'])
cov_rows = '\n'.join(f"{esc(c['sensor'])} & {c['winter']} & {c['valid_days']} of {c['days']} & {c['first'] or '--'} & {c['last'] or '--'} & {c['passages']:,} \\\\" for c in cov if c['valid_days'])
nb_rows = '\n'.join(f"{esc(t['term'].replace('_', ' '))} & {t['coef']} & {t['se']} & {esc(t['effect'])} \\\\" for t in nb['terms'])
wx_rows = '\n'.join(f"{k.split('|')[0]} & {k.split('|')[1].replace('_', ' ')} & {v['days']} & {v['matched_hours']} & {v['telraam']:,} & {v['kensington']:,} & {v['ratio']} \\\\" for k, v in wx.items())
gir_rows = '\n'.join(f"{x['month']} & {x['days']} & {x['girouard_wb']:,} & {x['ken_wb']:,} & {x['ratio']} \\\\" for x in g)
bnd = lambda k: bd[k]
sv_rows = ''
import csv
for r in csv.DictReader(open(os.path.join(HERE, 'survey_context.csv'))):
    if r['passages_per_riding_day'] in ('1.0', '1.5', '2.0'): sv_rows += f"{esc(r['band'])} & {r['riding_days_low']}--{r['riding_days_high']} (central {r['riding_days_central']}) & {r['passages_per_riding_day']} & {int(r['passages_low']):,} & {int(r['passages_central']):,} & {int(r['passages_high']):,} \\\\\n"
base = bf['base']; freq_lo = min(v['ci']['frequent'][0] for v in bf.values()); freq_hi = max(v['ci']['frequent'][1] for v in bf.values()); occ_lo = min(v['ci']['occas'][0] for v in bf.values()); occ_hi = max(v['ci']['occas'][1] for v in bf.values())
fig = lambda name, w=1.0, cap='': f"\\begin{{figure}}[htbp]\\centering\\includegraphics[width={w}\\textwidth]{{figures/{name}_en.png}}" + (f"\\caption{{{cap}}}" if cap else '') + f"\\label{{fig:{name}}}\\end{{figure}}"

ABSTRACT = f"""The borough\\textquoteright{{}}s winter figures for rue de Terrebonne are passage counts at one point, Kensington, and the public debate has read them as numbers of people. This note asks what the available counts can and cannot say about the number of individuals who cycle the street in winter and how often, and uses the answer to place the APC-NDG survey of October--November 2026 (87 respondents cycled on Terrebonne last winter, 36 at least weekly) in context. Four sensors overlap in the winter of 2025--26: the borough\\textquoteright{{}}s loop at Kensington, two Telraam sensors at King Edward and Draper, and the City\\textquoteright{{}}s detector at Girouard (westbound only); two Miovision one-day counts of 2024 and 2025 give snapshots. From December~1, 2025 to February~28, 2026 the loop recorded {co['passages']:,} passages ({f1(co['weekday']['mean'])} per weekday, {f1(co['weekend']['mean'])} per weekend day); {pc(co['pairs']['share_of_weekday_passages'])} of weekday passages are in matched morning--evening round trips, about {co['pairs']['mean']:.0f} per weekday; {pc(co['dark_share'])} of passages are in darkness. Winter traffic concentrates toward the east end: on dry days Draper carries {cr['draper_over_kensington']:.2f} and King Edward {cr['king_edward_over_kensington']:.2f} times the Kensington count, and the City\\textquoteright{{}}s westbound count at Girouard is {cr['girouard_wb_over_kensington_wb']:.2f} times the loop\\textquoteright{{}}s. The Telraam-to-loop ratio rises by 50--60\\,\\% on days with snowfall, a discrepancy whose cause (over-detection, or cyclists leaving the snowed-in lane for the roadway where the loop cannot see them) the data do not settle. A model-free bound puts at least {bnd('king_edward')['people_ge_m2']} distinct cyclists on the street at King Edward on {bnd('king_edward')['date']} and at least {bnd('kensington')['people_ge_m2']} at Kensington on {bnd('kensington')['date']}. A negative-binomial mixture of three frequency bands fitted to the daily counts and the matched pairs shows what a single counter identifies: the passages produced by frequent riders and their round trips, but not the number of people behind them without an assumption on how often each rides; across four template variants the frequent core at Kensington lies between {freq_lo:.0f} and {freq_hi:.0f} people and the occasional tail between {occ_lo:.0f} and {occ_hi:.0f}. On any reading, the 87 individuals found by a voluntary survey are a floor under the winter riding population, not a measure of it, and the passages they report are consistent with the count."""

NOTE = r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage[a4paper,margin=2.2cm]{geometry}\usepackage{graphicx,booktabs,longtable,amsmath,caption}\usepackage[hidelinks]{hyperref}
\captionsetup{font=small,labelfont=bf}\setlength{\parindent}{0pt}\setlength{\parskip}{0.6em}
\begin{document}
{\LARGE\textbf{How many people cycle rue de Terrebonne in winter, and how often?}}\\[3pt]
{\large Bicycle counts on four sensors, a frequency distribution, and the APC-NDG survey in context}\\[4pt]
{\small Terrebonne-open-sources, ''' + STAMP + r'''. Author: a resident of Côte-des-Neiges--Notre-Dame-de-Grâce (see the repository\textquoteright{}s « About the author »). Data: borough loop counter (access requests 2026-300 and 2026-581), the author\textquoteright{}s Telraam sensors (counts: Telraam), City open data (CC-BY 4.0), ECCC. Code, tables and figures: \url{''' + URL + r'''}.}

\section*{Abstract}
''' + ABSTRACT + r'''

\tableofcontents

\section{Question}
Two units run through the discussion of the winter layout adopted by the borough council on November 2, 2026 (file 1266880005). The counters count \emph{passages}: one bicycle crossing one point in one direction. The survey counts \emph{people}. Exposure to risk and the use made of the lane accrue per passage; representation and the reach of a measure are counted in persons. Neither unit converts into the other without an assumption about how often each person rides and how many times a trip crosses the counting point. This note states those assumptions explicitly and asks three questions: what the structure of the counts (hour of day, day of week, weather, several points along the street) says about the mix of frequent and occasional riders; what bounds and estimates on the number of individuals follow, and with what uncertainty; and how the survey\textquoteright{}s figures, 87 respondents who cycled on Terrebonne last winter and 36 at least weekly, sit against them. The survey figures used are those of the public filing of November 2, 2026; its finer frequency categories are not used here.

\section{Data}
\subsection{Sensors}
\begin{itemize}
\item \textbf{Kensington loop} (borough, Eco-Counter ZELT EVO, 45.47022~N, 73.63204~W): hourly counts by direction (eastbound \emph{IN\_est}, westbound \emph{OUT\_ouest}) from July 26, 2025 to May 11, 2026 (request 2026-300), daily totals to August 31, 2026 (request 2026-581). The westbound channel is degraded from about March 1, 2026 (the borough engineering division\textquoteright{}s reply of October 15, 2026, and the supplier\textquoteright{}s of October 21): the analyses below use December~1, 2025 to February~28, 2026 as the \emph{core} period, and December~1 to March~31 (the proposed conversion window) only for totals, which are then lower bounds.
\item \textbf{King Edward} (Telraam S2, segment 13374, west of Cavendish) and \textbf{Draper} (segment 13690, east of Kensington), installed by the author in August and September 2024: hourly counts of bicycles in two directions (A$>$B, B$>$A) with an uptime per hour; a camera sensor that counts in daylight only. Draper stopped on January 24, 2026; King Edward ran to May 4, 2026. The counts are Telraam\textquoteright{}s under its terms of use; only aggregates are published here.
\item \textbf{Girouard} (City detector det-00118, open data « Compteurs cyclistes permanents »): daily and hourly volumes from October 23, 2025; instance 01 is Terrebonne westbound (the only Terrebonne direction reported), instances 02--03 are Girouard itself.
\item \textbf{Miovision one-day counts} (request 2026-581, by approach in request 2026-634): September 19, 2024 and January 29, 2025 at Grand and at Cavendish, six peak hours and twelve hours.
\item \textbf{Weather}: ECCC daily, Montréal-Trudeau (7025251): snowfall, mean and minimum temperature, snow on the ground. \textbf{Daylight}: sunrise and sunset computed (NOAA algorithm) for the site.
\end{itemize}
\subsection{Coverage}
Winter 1 (December 1, 2024 to March 31, 2025) has the two Telraam sensors only; winter 2 (December 1, 2025 to March 31, 2026) has all four points, Draper to January 23. A Telraam day is valid with at least 8 reported hours and 6~h of uptime (the convention of the Terrebonne-telraam repository).
{\small\begin{longtable}{@{}llllll@{}}\toprule Sensor & winter & valid days & first & last & passages\\ \midrule
''' + cov_rows + r'''
\bottomrule\end{longtable}}
''' + fig('coverage_and_series', 1.0, 'Days with data on each sensor (top) and daily passages (bottom, log scale). Telraam: daylight hours; Girouard: westbound only.') + r'''

\section{Methods}
\subsection{Matching the sensors}
Telraam and loop are compared on the same clock hours of the same days, 8--16~h, with Telraam uptime of at least 0.7 in the hour; the ratio of summed passages is computed by month, by hour of day over a season, and separately for days with and without snowfall (ECCC $\geq 2.5$~cm). A ratio that is flat across the hours of the day indicates a real difference in traffic between the two points; a ratio that falls at dawn and dusk indicates the camera\textquoteright{}s detection loss. The Telraam directions were mapped to eastbound and westbound by correlating hourly A$>$B and B$>$A with the loop\textquoteright{}s two channels over September--October 2025. Girouard westbound is compared with the loop\textquoteright{}s westbound channel on common days with at least 20 reported hours.
\subsection{The structure of the winter at Kensington}
For every day of the core period: passages by direction and hour; the number of \emph{matched round trips}, defined as $\min(\text{EB}_{6\text{--}10\text{h}}, \text{WB}_{15\text{--}20\text{h}}) + \min(\text{WB}_{6\text{--}10\text{h}}, \text{EB}_{15\text{--}20\text{h}})$, a lower bound on the number of people who crossed the point outbound in the morning and back in the evening; the share of passages before sunrise or after sunset; the day type (weekday, weekend, holiday period December 22 to January 4) and the weather class (\emph{harsh} = snowfall $\geq 2.5$~cm or mean temperature $\leq -10\,^\circ$C). A negative-binomial regression of the daily total on these variables gives the size of each effect with a standard error.
\subsection{Model-free bounds on distinct users}
If no person crosses a point more than $m$ times in a day, the number of distinct people who rode on a given day is at least the day\textquoteright{}s count divided by $m$; the largest day of the winter at each point therefore gives a lower bound on the number of individuals who cycled the street that winter, with no other assumption. Both $m = 2$ (every passage half of a round trip) and $m = 4$ are reported.
\subsection{A frequency-band model}
Let $Y_d$ be the passages on day $d$ and $P_d$ the matched round trips on weekday $d$. Three bands of riders are defined by \emph{templates}: for band $b$, the probability $p_b(d)$ of riding on a day of a given type and weather, the passages per riding day $c_b$ (2 for a round trip through the point, less when trips are one-way), and the share $\pi_b$ of riding days that produce a matched pair. With $N_b$ people in band $b$,
\[ Y_d \sim \mathrm{NB}\Big(\mu_d = \sum_b N_b\, p_b(d)\, c_b,\ r_Y\Big), \qquad P_d \sim \mathrm{NB}\Big(\sum_b N_b\, p_b(d)\, \pi_b,\ r_P\Big), \]
and $N_b$ and the dispersions are estimated by maximum likelihood on the core period. Each $N_b$, and the sum $N_\text{daily} + N_\text{regular}$ (\emph{frequent}), receives a 95\,\% profile-likelihood interval. Because the templates, not the data, define what \emph{frequent} and \emph{occasional} mean, the fit is repeated with four template sets:
\begin{itemize}
''' + tmpl_rows + r'''
\end{itemize}
The model is deliberately simple. Its purpose is to show which quantities a single counter determines and which it does not.
\subsection{From one point to the street, and the survey}
Passages at King Edward, Draper and Girouard relative to Kensington, on dry days, bound the number of trips that cross at least one point: between the largest point and the sum of the points, in units of the Kensington count. For the survey, the passages its respondents would have produced at one point are computed under stated ranges of riding days per winter and passages per riding day, and compared with the count; the modelled bands give the share of each kind of rider the survey reached.

\section{Results}
\subsection{The winter at Kensington}
From December~1, 2025 to February~28, 2026 (''' + f"{co['days']}" + r''' days) the loop counted ''' + f"{co['passages']:,}" + r''' passages (''' + f"{co['eb']:,}" + r''' eastbound, ''' + f"{co['wb']:,}" + r''' westbound). Weekdays average ''' + f1(co['weekday']['mean']) + r''' passages (median ''' + f0(co['weekday']['median']) + r''', 10th--90th percentiles ''' + f0(co['weekday']['p10']) + r'''--''' + f0(co['weekday']['p90']) + r''', range ''' + f0(co['weekday']['min']) + r'''--''' + f0(co['weekday']['max']) + r'''); weekend days ''' + f1(co['weekend']['mean']) + r''' (median ''' + f0(co['weekend']['median']) + r'''). Mild weekdays average ''' + f1(co['weekday_by_weather']['mild']['mean']) + r''' (n = ''' + f"{co['weekday_by_weather']['mild']['n']}" + r'''), harsh weekdays ''' + f1(co['weekday_by_weather']['harsh']['mean']) + r''' (n = ''' + f"{co['weekday_by_weather']['harsh']['n']}" + r''', minimum ''' + f0(co['weekday_by_weather']['harsh']['min']) + r'''), holiday weekdays ''' + f1(co['weekday_by_weather']['holiday']['mean']) + r'''. Matched round trips average ''' + f1(co['pairs']['mean']) + r''' per weekday (10th--90th percentiles ''' + f0(co['pairs']['p10']) + r'''--''' + f0(co['pairs']['p90']) + r''') and account for ''' + pc(co['pairs']['share_of_weekday_passages']) + r''' of weekday passages; ''' + pc(co['dark_share']) + r''' of all passages occur before sunrise or after sunset. Over the whole window December~1 to March~31 the loop counted ''' + f"{w2['passages']:,}" + r''' passages, with no day below ''' + f0(w2['min_day']) + r''' and ''' + f"{w2['days_ge_40']}" + r''' days of 40 or more; the largest day, ''' + f"{w2['max_day_date']}" + r''', had ''' + f0(w2['max_day']) + r''' (westbound channel degraded in March: a lower bound).
''' + fig('kensington_hourly_profile', 1.0, 'Mean passages per hour by direction, weekdays and weekend days, December 1, 2025 to February 28, 2026; shaded = before sunrise and after sunset on January 15.') + r'''
''' + fig('kensington_weather_pairs', 1.0, 'Left: daily passages against mean temperature. Right: matched morning--evening round trips per weekday and the passages outside them.') + r'''

The negative-binomial regression (Table~\ref{tab:nb}; n = ''' + f"{nb['n']}" + r''' days, dispersion $r$ = ''' + f"{nb['dispersion_r']}" + r''') puts the weekend at ''' + esc([t for t in nb['terms'] if t['term'] == 'weekend'][0]['effect']) + r''' and the holiday period at ''' + esc([t for t in nb['terms'] if t['term'] == 'holiday'][0]['effect']) + r''' relative to an ordinary weekday; each degree of mean temperature adds ''' + esc([t for t in nb['terms'] if t['term'] == 'tmean_c'][0]['effect'].split(' per')[0]) + r''', each centimetre of snow on the ground removes ''' + esc([t for t in nb['terms'] if t['term'] == 'snow_on_ground_cm'][0]['effect'].split(' per')[0].replace('-', '')) + r'''; the day\textquoteright{}s own snowfall has no separate effect once snow on the ground and temperature are in; daylight hours and the time trend are confounded over a ninety-day window and should be read together. The lag-1 autocorrelation of the weekday residuals is ''' + f"{nb['lag1_autocorr_weekday_residuals']}" + r''': day-to-day persistence beyond the weather is weak.
\begin{table}[htbp]\centering\small\caption{Negative-binomial regression of daily passages at Kensington, core period. Coefficients per unit of the raw variable; standard errors approximate (BFGS inverse Hessian).}\label{tab:nb}
\begin{tabular}{@{}lrrl@{}}\toprule term & coefficient & s.e. & effect\\ \midrule
''' + nb_rows + r'''
\bottomrule\end{tabular}\end{table}

\subsection{The other points}
On matched daylight hours King Edward counts ''' + f"{ke_aut['ratio']:.2f}" + r''' times the loop in September--October 2025 and ''' + f"{ke_win['ratio']:.2f}" + r''' times in the winter core; Draper ''' + f"{dr_aut['ratio']:.2f}" + r''' in autumn and ''' + f"{dr_win['ratio']:.2f}" + r''' in winter. The ratio by hour of day (Figure~\ref{fig:cross_sensor_ratios}) is roughly flat for King Edward in both seasons and falls only at the edges of daylight, as expected of a camera; Draper\textquoteright{}s winter ratio is above one through the day. The Telraam direction split is not recoverable from the data: the correlations of A$>$B with the loop\textquoteright{}s two channels differ by less than 0.1 at both sensors (King Edward ''' + f"{dm['King Edward']['r_ab_eb']}/{dm['King Edward']['r_ab_wb']}" + r''', Draper ''' + f"{dm['Draper']['r_ab_eb']}/{dm['Draper']['r_ab_wb']}" + r'''), so only totals are used. The City\textquoteright{}s westbound count at Girouard is ''' + f"{g[0]['ratio']:.2f}" + r''' times the loop\textquoteright{}s westbound channel in November and ''' + f"{g[1]['ratio']:.2f}" + r''', ''' + f"{g[2]['ratio']:.2f}" + r''' and ''' + f"{g[3]['ratio']:.2f}" + r''' times in December, January and February (Table~\ref{tab:gir}): within one pair of instruments, the east end gains relative to Kensington when winter comes.

\textbf{Snow days.} Table~\ref{tab:wx} splits the winter ratios by weather. On days without snowfall King Edward is at ''' + f"{wx['King Edward|no_snow']['ratio']:.2f}" + r''' and Draper at ''' + f"{wx['Draper|no_snow']['ratio']:.2f}" + r''' of the loop; on days with 2.5~cm or more they rise to ''' + f"{wx['King Edward|snow_ge_2.5cm']['ratio']:.2f}" + r''' and ''' + f"{wx['Draper|snow_ge_2.5cm']['ratio']:.2f}" + r'''. The two instruments diverge on snow days by 50--60\,\%, in the same direction at both Telraam sites. Two explanations fit: the camera over-detects on snow days (snow-clearing equipment, pedestrians on the roadway), or cyclists leave the snowed-in lane for the roadway, where an inductive loop placed in the lane cannot see them, so that the loop under-counts. The data do not separate them; the dry-day ratios are used below, and the loop\textquoteright{}s snow-day counts should be read as possibly low.
\begin{table}[htbp]\centering\small\caption{Telraam against the loop on matched hours (8--16~h, uptime $\geq 0.7$), winter core (Draper to January 23), by weather.}\label{tab:wx}
\begin{tabular}{@{}llrrrrr@{}}\toprule sensor & days & n days & matched hours & Telraam & Kensington & ratio\\ \midrule
''' + wx_rows + r'''
\bottomrule\end{tabular}\end{table}
\begin{table}[htbp]\centering\small\caption{Girouard westbound (City det-00118-01) against the loop\textquoteright{}s westbound channel, common days with $\geq 20$ reported hours.}\label{tab:gir}
\begin{tabular}{@{}lrrrr@{}}\toprule month & days & Girouard WB & Kensington WB & ratio\\ \midrule
''' + gir_rows + r'''
\bottomrule\end{tabular}\end{table}
''' + fig('cross_sensor_ratios', 1.0, 'Left: ratio of passages to the Kensington loop by month (Telraam on matched daylight hours; Girouard westbound on common days). Right: the same ratio by hour of day, autumn and winter.') + r'''

\textbf{Two snapshots.} On September 19, 2024 the Miovision camera at Grand counted ''' + f"{s19['grand_axis_12h']}" + r''' bicycles on the Terrebonne axis over twelve hours and the one at Cavendish ''' + f"{s19['cav_axis_12h']}" + r'''; the Telraam at King Edward counted ''' + f"{s19['king_edward_12h']['ab'] + s19['king_edward_12h']['ba']}" + r''' over the same hours (Draper not yet installed). On January 29, 2025, a day with ''' + f"{j29['weather']['snow']}" + r'''~cm of snow and a mean temperature of ''' + f"{j29['weather']['tmean']}" + r'''$\,^\circ$C, Grand counted ''' + f"{j29['grand_axis_12h']}" + r''' on the axis over twelve hours (''' + f"{j29['grand_eb_6h']}" + r''' on the eastbound approach and ''' + f"{j29['grand_wb_6h']}" + r''' on the westbound approach in the six peak hours: the « 8 » of the borough\textquoteright{}s deck), Cavendish ''' + f"{j29['cav_axis_12h']}" + r''', King Edward ''' + f"{j29['king_edward_12h']['ab'] + j29['king_edward_12h']['ba']}" + r''' and Draper ''' + f"{j29['draper_12h']['ab'] + j29['draper_12h']['ba']}" + r''' (''' + f"{j29['draper_12h']['hours']}" + r''' of 12 hours reported). The Draper figure is a snow-day Telraam count and carries the discrepancy just described; the other three are consistent with one another and with the winter gradient. On that day the eight eastbound passages at Grand had no westbound counterpart in the count window, so they cannot be read as four people going out and coming back through that point in those hours.
''' + fig('snapshot_days', 1.0, 'The two Miovision days with the Telraam sensors on the same hours (7--19~h).') + r'''

\subsection{Bounds on distinct users}
The largest day at each point gives a floor under the number of individuals who cycled the street in the winter of 2025--26 (Table~\ref{tab:bounds}). At King Edward, ''' + f"{bnd('king_edward')['date']}" + r''' (a ''' + f"{bnd('king_edward')['weekday']}" + r''', no snowfall) had ''' + f"{bnd('king_edward')['max_day']}" + r''' passages in daylight: at least ''' + f"{bnd('king_edward')['people_ge_m2']}" + r''' people if no one passed more than twice, ''' + f"{bnd('king_edward')['people_ge_m4']}" + r''' if no one passed more than four times, on a sensor that counts about 0.6 of the loop on comparable days. At Kensington the largest day of the window, ''' + f"{bnd('kensington')['date']}" + r''', gives at least ''' + f"{bnd('kensington')['people_ge_m2']}" + r''' with the westbound channel degraded; within the core period, ''' + f"{bnd('kensington_core')['date']}" + r''' gives at least ''' + f"{bnd('kensington_core')['people_ge_m2']}" + r'''. Draper\textquoteright{}s largest day (''' + f"{bnd('draper')['date']}" + r''', ''' + f"{bnd('draper')['max_day']}" + r''') fell on a day with ''' + f"{bnd('draper')['snow_cm']}" + r'''~cm of snow and is not used.
\begin{table}[htbp]\centering\small\caption{Largest day of the winter window at each point and the implied floor on distinct cyclists.}\label{tab:bounds}
\begin{tabular}{@{}llrrrl@{}}\toprule point & date & passages & people, $m=2$ & people, $m=4$ & note\\ \midrule
Kensington loop & ''' + f"{bnd('kensington')['date']} & {bnd('kensington')['max_day']:.0f} & {bnd('kensington')['people_ge_m2']} & {bnd('kensington')['people_ge_m4']}" + r''' & westbound channel degraded\\
Kensington loop, core & ''' + f"{bnd('kensington_core')['date']} & {bnd('kensington_core')['max_day']:.0f} & {bnd('kensington_core')['people_ge_m2']} & {bnd('kensington_core')['people_ge_m4']}" + r''' & both channels sound\\
King Edward (Telraam) & ''' + f"{bnd('king_edward')['date']} & {bnd('king_edward')['max_day']:.0f} & {bnd('king_edward')['people_ge_m2']} & {bnd('king_edward')['people_ge_m4']}" + r''' & daylight; no snowfall\\
Draper (Telraam) & ''' + f"{bnd('draper')['date']} & {bnd('draper')['max_day']:.0f} & -- & --" + r''' & snow day, not used\\
Girouard WB (City) & ''' + f"{bnd('girouard_wb')['date']} & {bnd('girouard_wb')['max_day']:.0f} & {bnd('girouard_wb')['people_ge_m2']} & {bnd('girouard_wb')['people_ge_m4']}" + r''' & one direction\\
\bottomrule\end{tabular}\end{table}

\subsection{The frequency bands}
Table~\ref{tab:bands} gives the fitted number of people in each band at Kensington for the four template sets, with the profile-likelihood intervals, the share of passages produced by the frequent bands and the fitted total against the observed ''' + f"{base['observed_total']:,}" + r'''. Figure~\ref{fig:band_fit} shows the fit by day type and the profile curves for the base templates.
\begin{table}[htbp]\centering\small\caption{Frequency-band model at Kensington, December 1, 2025 to February 28, 2026: people per band (95\,\% profile interval), by template set.}\label{tab:bands}
\begin{tabular}{@{}lllllrr@{}}\toprule templates & most weekdays & 1--3 days a week & frequent (both) & a few times a month & share of passages, frequent & fitted total\\ \midrule
''' + band_rows + r'''
\bottomrule\end{tabular}\end{table}
''' + fig('band_fit', 1.0, 'Left: observed and fitted mean passages by day type (base templates). Right: profile log-likelihood for each band and for the frequent core; the 95\\,\\% interval is the range above the dashed line.') + r'''

Three things are stable across the template sets. First, the frequent core is small in number and large in passages: between ''' + f"{freq_lo:.0f}" + r''' and ''' + f"{freq_hi:.0f}" + r''' people produce ''' + f"{min(100 * (v['share_by_band']['daily'] + v['share_by_band']['regular']) for v in bf.values()):.0f}" + r'''--''' + f"{max(100 * (v['share_by_band']['daily'] + v['share_by_band']['regular']) for v in bf.values()):.0f}" + r'''\,\% of the winter passages at this point. Second, the split of that core between daily and one-to-three-days-a-week riders is not identified by the counts: the two bands trade against each other along a ridge of the likelihood, and the fitted split moves from all-daily to all-regular with changes in the templates that the data cannot reject. Third, the occasional tail is large in people and uncertain: ''' + f"{occ_lo:.0f}" + r''' to ''' + f"{occ_hi:.0f}" + r''' across the fits, because a given volume of tail passages can come from fewer people riding more often or more people riding less. Table~\ref{tab:tail} makes that dependence explicit for the base fit.
\begin{table}[htbp]\centering\small\caption{The occasional tail of the base fit (''' + f"{base['passages_by_band']['occas']:,}" + r''' passages) as a number of people, for a range of rides per winter per person (1.5 passages per ride).}\label{tab:tail}
\begin{tabular}{@{}rrr@{}}\toprule rides per winter & passages per person & people\\ \midrule
''' + tail_rows + r'''
\bottomrule\end{tabular}\end{table}

\subsection{From Kensington to the street}
On dry days King Edward carries ''' + f"{cr['king_edward_over_kensington']:.2f}" + r''', Draper ''' + f"{cr['draper_over_kensington']:.2f}" + r''' and Girouard westbound ''' + f"{cr['girouard_wb_over_kensington_wb']:.2f}" + r''' times the corresponding Kensington count. Trips that cross at least one of the four points number between ''' + f"{cr['trips_crossing_any_point_lower']:.2f}" + r''' and ''' + f"{cr['trips_crossing_any_point_upper']:.2f}" + r''' times the Kensington count, the lower figure if every trip crosses every point, the upper if no trip crosses two. The truth is between: trips from the west end to Villa-Maria cross all four, trips within Monkland Village cross one. Any figure for people on the street as a whole is the Kensington figure scaled by a factor in that range, and the uncertainty of the factor is of the same order as the uncertainty of the band model.

Year over year, on common valid calendar dates, King Edward counted ''' + f"{yo['King Edward']['ratio_w2_w1']:.2f}" + r''' and Draper ''' + f"{yo['Draper']['ratio_w2_w1']:.2f}" + r''' times in the winter of 2025--26 what they counted in 2024--25 (''' + f"{yo['King Edward']['common_days']}" + r''' and ''' + f"{yo['Draper']['common_days']}" + r''' days): the winter studied here was not the busier of the two.

\subsection{The survey in context}
The survey\textquoteright{}s public filing reports 87 respondents who cycled on Terrebonne in the winter of 2025--26, 36 of them at least weekly, among 161 respondents kept. Table~\ref{tab:sv} gives the passages they would have produced at one point if every trip crossed it, for stated ranges of riding days and passages per riding day; Figure~\ref{fig:survey_vs_count} compares them with the count.
\begin{table}[htbp]\centering\small\caption{Passages implied by the survey\textquoteright{}s 87 winter cyclists at one point, December 1 to March 31 (17.3 weeks), under stated assumptions.}\label{tab:sv}
\begin{tabular}{@{}llrrrr@{}}\toprule band & riding days per winter & passages per riding day & low & central & high\\ \midrule
''' + sv_rows + r'''
\bottomrule\end{tabular}\end{table}
''' + fig('survey_vs_count', 0.85) + r'''

Under central assumptions the 87 account for ''' + f"{si['passages_central']:,}" + r''' passages, ''' + pc(si['ratio_central']) + r''' of the ''' + f"{si['counted_w2']:,}" + r''' counted at Kensington over the window (range ''' + pc(si['ratio_low']) + r'''--''' + pc(si['ratio_high']) + r'''). The count does not contradict the survey; the survey cannot account for the whole count except under the most generous assumptions, and not at all for the trips that never cross Kensington. Against the modelled bands, the survey\textquoteright{}s 36 weekly riders compare with a frequent core of ''' + f"{freq_lo:.0f}" + r'''--''' + f"{freq_hi:.0f}" + r''' people at Kensington alone, and its 51 less-than-weekly riders with an occasional tail of ''' + f"{occ_lo:.0f}" + r'''--''' + f"{occ_hi:.0f}" + r''' at that point, both to be multiplied by the corridor factor for the street. On the frequent side the survey plausibly reached a large share of the population; on the occasional side a small one. That asymmetry is the expected signature of a voluntary survey of users, and it is the right way to state the survey\textquoteright{}s limits: it over-represents frequent riders among people and under-represents the tail, while the passages, the quantity the counters measure, are dominated by the frequent riders in any case.

\section{Discussion}
\textbf{Trips and people.} The quantity at stake in the winter layout is the number of trips that lose a protected lane: ''' + f"{w2['passages']:,}" + r''' passages at one point over the proposed window, more over the street. The number of people behind them is a different quantity, needed for a different purpose, and it cannot be read off a counter without an assumption about frequency: the same ''' + f"{co['passages']:,}" + r''' core-period passages are consistent with a few dozen frequent riders and a tail of some tens of people, or with a tail of several hundred, depending on how often an occasional rider rides. A division of passages by two, the conversion used in the borough\textquoteright{}s presentation of January 29, 2025 (« 8 passages \ldots{} 4 cyclists »), is one such assumption; applied to that day\textquoteright{}s count it supposes a return leg that the count window does not contain.

\textbf{What one counter identifies.} The matched round trips and the weekday pattern pin down the passages produced by frequent riders and a floor under their number (about ''' + f"{co['pairs']['mean']:.0f}" + r''' round-trip commuters on an ordinary weekday at Kensington). They do not separate daily from near-daily riders, and they say little about the tail beyond its volume. The model-free bounds are the most defensible statements about people: at least ''' + f"{bnd('king_edward')['people_ge_m2']}" + r''' distinct cyclists at King Edward on one March day, at least ''' + f"{bnd('kensington_core')['people_ge_m2']}" + r''' at Kensington on one December day, before any assumption on frequency.

\textbf{The street is not uniform.} The east end holds its traffic in winter better than the middle, on two independent pairs of instruments (Draper against the loop; Girouard against the loop\textquoteright{}s westbound channel) and in the November-to-winter change of the same ratio. Kensington is therefore not the busiest point of the lane in winter, and a count there is a lower bound on the use of the street.

\textbf{Snow days.} The 50--60\,\% divergence between the Telraam sensors and the loop on snow days is the one finding that bears directly on the borough\textquoteright{}s own record: if the loop under-counts when the lane is snowed in, the winter figures from Kensington are low precisely on the days the measure is about. The alternative, over-detection by the camera, is as plausible on the present evidence. A side-by-side check on a snow day (a few hours of video at the loop) would settle it.

\textbf{Limitations.} Templates are assumptions, stated so that they can be argued; the sensitivity analysis spans the readings the author considers reasonable, not all readings. The loop\textquoteright{}s westbound channel limits the core period to ninety days. The Telraam counts are daylight-only, carry an unknown detection rate, and belong to Telraam. Girouard reports one direction. The survey figures are self-reported from memory and come from a voluntary sample; the comparison uses its public figures only. The Miovision days are two days. No sensor identifies individuals; a passage-weighted frequency distribution, obtained by asking passing cyclists at the counting point how often they ride there, would convert passages into people without a model, and is the measurement this note cannot replace.

\section{Reproducibility}
\texttt{winter\_counts\_analysis.py} reads the sources in place and writes \texttt{summary.json} (every number quoted here), \texttt{coverage.csv}, \texttt{cross\_sensor\_ratios.csv}, \texttt{kensington\_winter\_days.csv} (one row per day of the winter window with every variable used), \texttt{band\_fit.csv}, \texttt{survey\_context.csv} and the figures; \texttt{build\_docs.py} writes this note and the deck. The two extracts in \texttt{raw/} are the City\textquoteright{}s det-00118 rows (CC-BY 4.0) and ECCC\textquoteright{}s 2024 daily file. The Telraam exports are read from a private copy; the Terrebonne-telraam repository\textquoteright{}s README states the terms. Generated ''' + esc(S['generated']) + r'''.
\end{document}
'''

DECK = r'''\documentclass[aspectratio=169,10pt]{beamer}\usetheme{default}\usecolortheme{seahorse}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{helvet}\usepackage{booktabs,amsmath}
\title{How many people cycle rue de Terrebonne in winter, and how often?}\subtitle{Bicycle counts on four sensors, a frequency distribution, and the APC-NDG survey in context}\author{Terrebonne-open-sources (a resident of Côte-des-Neiges--Notre-Dame-de-Grâce)}\date{''' + STAMP + r'''}
\begin{document}
\begin{frame}\titlepage\end{frame}
\begin{frame}{Two units}\begin{itemize}
\item Counters count \textbf{passages}: one bicycle, one point, one direction. The survey counts \textbf{people}.
\item Exposure and use accrue per passage; representation is counted in persons. Neither converts into the other without an assumption on how often each person rides and whether a trip crosses the point twice.
\item Questions: what does the structure of the counts say about frequent and occasional riders? What bounds on individuals follow? How do the survey\textquoteright{}s 87 winter cyclists (36 at least weekly) sit against the counts?
\end{itemize}\end{frame}
\begin{frame}{Four sensors, two winters}\centering\includegraphics[width=0.9\textwidth]{figures/coverage_and_series_en.png}\end{frame}
\begin{frame}{Data and caveats}\begin{itemize}
\item \textbf{Kensington loop} (borough): hourly by direction, Jul 2025--May 2026; westbound channel degraded from March 2026 $\Rightarrow$ core period Dec 1, 2025 -- Feb 28, 2026.
\item \textbf{King Edward} and \textbf{Draper} (Telraam S2, the author\textquoteright{}s): hourly, daylight only, uptime per hour; Draper stopped Jan 24, 2026; counts belong to Telraam, aggregates only.
\item \textbf{Girouard} (City det-00118): westbound only, from Oct 23, 2025 (open data).
\item \textbf{Miovision} one-day counts: Sept 19, 2024 and Jan 29, 2025 (requests 2026-581, 2026-634).
\item ECCC daily weather; computed sunrise and sunset.
\end{itemize}\end{frame}
\begin{frame}{The winter at Kensington, Dec 1 -- Feb 28}\begin{columns}\column{0.55\textwidth}\includegraphics[width=\textwidth]{figures/kensington_hourly_profile_en.png}\column{0.45\textwidth}\small\begin{itemize}
\item ''' + f"{co['passages']:,}" + r''' passages in ''' + f"{co['days']}" + r''' days; weekdays ''' + f1(co['weekday']['mean']) + r''' (p10--p90 ''' + f0(co['weekday']['p10']) + r'''--''' + f0(co['weekday']['p90']) + r'''), weekend ''' + f1(co['weekend']['mean']) + r'''.
\item Mild weekdays ''' + f1(co['weekday_by_weather']['mild']['mean']) + r''', harsh ''' + f1(co['weekday_by_weather']['harsh']['mean']) + r''', holiday ''' + f1(co['weekday_by_weather']['holiday']['mean']) + r'''.
\item Matched AM/PM round trips: ''' + f1(co['pairs']['mean']) + r''' per weekday, ''' + pc(co['pairs']['share_of_weekday_passages']) + r''' of weekday passages.
\item ''' + pc(co['dark_share']) + r''' of passages in darkness.
\item Dec 1 -- Mar 31: ''' + f"{w2['passages']:,}" + r''' passages, no day below ''' + f0(w2['min_day']) + r''', ''' + f"{w2['days_ge_40']}" + r''' days $\geq 40$ (lower bound).
\end{itemize}\end{columns}\end{frame}
\begin{frame}{Weather and round trips}\centering\includegraphics[width=0.95\textwidth]{figures/kensington_weather_pairs_en.png}\\{\scriptsize NB regression: weekend ''' + esc([t for t in nb['terms'] if t['term'] == 'weekend'][0]['effect']) + r''', holiday period ''' + esc([t for t in nb['terms'] if t['term'] == 'holiday'][0]['effect']) + r''', ''' + esc([t for t in nb['terms'] if t['term'] == 'tmean_c'][0]['effect']) + r''' of mean temperature, ''' + esc([t for t in nb['terms'] if t['term'] == 'snow_on_ground_cm'][0]['effect']) + r''' of snow on the ground; residual lag-1 autocorrelation ''' + f"{nb['lag1_autocorr_weekday_residuals']}" + r'''.}\end{frame}
\begin{frame}{The other points: the east end holds up in winter}\centering\includegraphics[width=0.95\textwidth]{figures/cross_sensor_ratios_en.png}\\{\scriptsize Dry days, winter core: King Edward ''' + f"{cr['king_edward_over_kensington']:.2f}" + r''', Draper ''' + f"{cr['draper_over_kensington']:.2f}" + r''' of the loop; Girouard WB ''' + f"{cr['girouard_wb_over_kensington_wb']:.2f}" + r''' of the loop\textquoteright{}s WB (''' + f"{g[0]['ratio']:.2f}" + r''' in November).}\end{frame}
\begin{frame}{Snow days: the instruments diverge}\centering\small\begin{tabular}{@{}llrrrrr@{}}\toprule sensor & days & n & matched h & Telraam & Kensington & ratio\\ \midrule
''' + wx_rows + r'''
\bottomrule\end{tabular}\\[6pt]\footnotesize On days with $\geq 2.5$ cm of snow both Telraam sensors count 50--60\,\% more relative to the loop. Either the camera over-detects on snow days, or cyclists leave the snowed-in lane for the roadway where the loop cannot see them. The data do not settle it; dry-day ratios are used, and the loop\textquoteright{}s snow-day counts may be low.\end{frame}
\begin{frame}{Two snapshot days}\centering\includegraphics[width=0.95\textwidth]{figures/snapshot_days_en.png}\\{\scriptsize Jan 29, 2025: ''' + f"{j29['weather']['snow']}" + r''' cm of snow, mean ''' + f"{j29['weather']['tmean']}" + r''' $^\circ$C. Grand: ''' + f"{j29['grand_eb_6h']}" + r''' eastbound, ''' + f"{j29['grand_wb_6h']}" + r''' westbound in six peak hours (the « 8 »): no return leg in the window. Draper is a snow-day Telraam count.}\end{frame}
\begin{frame}{Floors under the number of individuals (no model)}\centering\small\begin{tabular}{@{}llrrrl@{}}\toprule point & date & passages & people, $m=2$ & people, $m=4$ & note\\ \midrule
Kensington loop & ''' + f"{bnd('kensington')['date']} & {bnd('kensington')['max_day']:.0f} & {bnd('kensington')['people_ge_m2']} & {bnd('kensington')['people_ge_m4']}" + r''' & WB channel degraded\\
Kensington, core & ''' + f"{bnd('kensington_core')['date']} & {bnd('kensington_core')['max_day']:.0f} & {bnd('kensington_core')['people_ge_m2']} & {bnd('kensington_core')['people_ge_m4']}" + r''' & both channels sound\\
King Edward (Telraam) & ''' + f"{bnd('king_edward')['date']} & {bnd('king_edward')['max_day']:.0f} & {bnd('king_edward')['people_ge_m2']} & {bnd('king_edward')['people_ge_m4']}" + r''' & daylight, no snow\\
Girouard WB (City) & ''' + f"{bnd('girouard_wb')['date']} & {bnd('girouard_wb')['max_day']:.0f} & {bnd('girouard_wb')['people_ge_m2']} & {bnd('girouard_wb')['people_ge_m4']}" + r''' & one direction\\
\bottomrule\end{tabular}\\[6pt]\footnotesize If no one crosses a point more than $m$ times in a day, the largest day divided by $m$ is a floor under the distinct cyclists of the winter.\end{frame}
\begin{frame}{A frequency-band model}\small
\[ Y_d \sim \mathrm{NB}\Big(\sum_b N_b\, p_b(d)\, c_b\Big), \qquad P_d \sim \mathrm{NB}\Big(\sum_b N_b\, p_b(d)\, \pi_b\Big) \]
\begin{itemize}
\item Three bands (most weekdays / 1--3 days a week / a few times a month), each a template: probability of riding by day type and weather, passages per riding day, share of riding days giving a matched pair.
\item Fitted by maximum likelihood on the core period (daily totals and matched pairs); 95\,\% profile intervals; four template sets.
\item Purpose: to show which quantities one counter determines and which it does not.
\end{itemize}\end{frame}
\begin{frame}{What the counts pin down, and what they do not}\centering\includegraphics[width=0.95\textwidth]{figures/band_fit_en.png}\end{frame}
\begin{frame}{People per band, by template set (Kensington, core period)}\centering\scriptsize\begin{tabular}{@{}lllllrr@{}}\toprule templates & most weekdays & 1--3 days/week & frequent (both) & a few times a month & passages, frequent & fitted total\\ \midrule
''' + band_rows + r'''
\bottomrule\end{tabular}\\[6pt]\footnotesize Stable: the frequent core is small in number (''' + f"{freq_lo:.0f}" + r'''--''' + f"{freq_hi:.0f}" + r''') and makes most of the passages. Not identified: the split daily / near-daily, and the size of the tail (''' + f"{occ_lo:.0f}" + r'''--''' + f"{occ_hi:.0f}" + r''') without an assumption on how often an occasional rider rides.\end{frame}
\begin{frame}{From Kensington to the street}\begin{itemize}
\item Dry-day ratios to Kensington: King Edward ''' + f"{cr['king_edward_over_kensington']:.2f}" + r''', Draper ''' + f"{cr['draper_over_kensington']:.2f}" + r''', Girouard WB ''' + f"{cr['girouard_wb_over_kensington_wb']:.2f}" + r'''.
\item Trips crossing at least one point: between ''' + f"{cr['trips_crossing_any_point_lower']:.2f}" + r''' (every trip crosses every point) and ''' + f"{cr['trips_crossing_any_point_upper']:.2f}" + r''' (no trip crosses two) times the Kensington count.
\item Kensington is not the busiest point of the lane in winter; a count there is a lower bound on the street.
\item Year over year on common dates: King Edward ''' + f"{yo['King Edward']['ratio_w2_w1']:.2f}" + r''', Draper ''' + f"{yo['Draper']['ratio_w2_w1']:.2f}" + r''' of the 2024--25 winter.
\end{itemize}\end{frame}
\begin{frame}{The survey in context}\begin{columns}\column{0.5\textwidth}\includegraphics[width=\textwidth]{figures/survey_vs_count_en.png}\column{0.5\textwidth}\small\begin{itemize}
\item 87 respondents cycled on Terrebonne last winter, 36 at least weekly (public filing, Nov 2, 2026).
\item Their passages at one point, if every trip crossed it: ''' + f"{si['passages_central']:,}" + r''' central (''' + f"{si['passages_low']:,}" + r'''--''' + f"{si['passages_high']:,}" + r''') against ''' + f"{si['counted_w2']:,}" + r''' counted: ''' + pc(si['ratio_central']) + r'''.
\item 36 weekly riders against a frequent core of ''' + f"{freq_lo:.0f}" + r'''--''' + f"{freq_hi:.0f}" + r''' at Kensington alone; 51 occasional against a tail of ''' + f"{occ_lo:.0f}" + r'''--''' + f"{occ_hi:.0f}" + r'''; both $\times$ the corridor factor for the street.
\item The survey reached a large share of frequent riders and a small share of the tail: the signature of a voluntary survey of users. The count does not contradict it; the 87 are a floor, not a measure.
\end{itemize}\end{columns}\end{frame}
\begin{frame}{What this settles and what it does not}\begin{itemize}
\item Trips at stake: ''' + f"{w2['passages']:,}" + r''' passages at one point over the proposed window, more over the street.
\item People: at least ''' + f"{bnd('king_edward')['people_ge_m2']}" + r''' at King Edward on one March day and ''' + f"{bnd('kensington_core')['people_ge_m2']}" + r''' at Kensington on one December day, before any assumption; beyond that, the head count depends on the frequency assumed, and a division of passages by two is one such assumption.
\item About ''' + f"{co['pairs']['mean']:.0f}" + r''' round-trip commuters cross Kensington on an ordinary winter weekday; frequent riders make most passages; the tail is large in people and poorly measured.
\item Open: the snow-day divergence between the camera sensors and the loop; a passage-weighted frequency distribution (asking passing cyclists at the counting point) would turn passages into people without a model.
\item Code, data tables and every figure: \url{''' + URL + r'''}
\end{itemize}\end{frame}
\end{document}
'''
for name, src in (('winter_counts_user_frequency_note_en', NOTE), ('winter_counts_user_frequency_deck_en', DECK)):
    open(os.path.join(HERE, name + '.tex'), 'w', encoding='utf-8').write(src)
    for _ in range(3): r = subprocess.run(['pdflatex', '-interaction=batchmode', name + '.tex'], cwd=HERE, capture_output=True, text=True)
    log = open(os.path.join(HERE, name + '.log'), encoding='latin-1').read(); errs = [l for l in log.splitlines() if l.startswith('!')]
    for e in ('.aux', '.log', '.nav', '.out', '.snm', '.toc'):
        try: os.remove(os.path.join(HERE, name + e))
        except OSError: pass
    pi = subprocess.run(['pdfinfo', os.path.join(HERE, name + '.pdf')], capture_output=True, text=True).stdout
    print(name, (pi.split('Pages:')[1].split()[0] if 'Pages:' in pi else '?'), 'pages', ('ERRORS: ' + '; '.join(errs[:5])) if errs else 'ok')
