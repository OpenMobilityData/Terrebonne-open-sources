#!/usr/bin/env python3
"""Note (A4) and deck (beamer 16:9), English, plus the lay abstracts (short in the note, both as .txt), from summary.json and the
figures of queue_analysis.py. Every number in the text comes from summary.json."""
import json, os, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); S = json.load(open(os.path.join(HERE, 'summary.json'), encoding='utf-8'))
STAMP = datetime.datetime.now().strftime('%Y-%m-%d')
URL = 'https://github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/2026-shared-lane-queue'
esc = lambda s: str(s).replace('&', '\\&').replace('%', '\\%').replace("'", "\\textquoteright{}").replace('–', '--')
F, G, GE, SC, D = S['flows'], S['grand'], S['geometry'], S['scenarios'], S['drivers']
am, pm = F['am_peak'], F['pm_peak']; c, lo, hi = SC['central'], SC['low'], SC['high']
L = f"{GE['cavendish_to_girouard_km']:g}"; Lkm = f"{GE['cavendish_to_girouard_km']:.1f}"
bd = lambda sc, x: sc['by_distance'][x]
pc = lambda v: f'{100 * v:.0f}\\,\\%'
rows = '\n'.join(f"{k} & {SC[k]['q']} & {SC[k]['vb']} & {SC[k]['vc']} & {pc(SC[k]['s'])} & {SC[k]['caught_per_km']:.1f} & "
                 + ' & '.join(f"{bd(SC[k], x)['expected_queue']:.1f}" for x in ('0.5', '1', L)) + ' \\\\' for k in ('low', 'central', 'high'))
mc_rows = '\n'.join(f"{k} & {x if x != L else Lkm} & {bd(SC[k], x)['mean']:.1f} & {bd(SC[k], x)['median']} & {bd(SC[k], x)['p10']}--{bd(SC[k], x)['p90']} & {pc(bd(SC[k], x)['share_zero'])} & {bd(SC[k], x)['time_avg']:.1f} \\\\"
                    for k in ('low', 'central', 'high') for x in ('0.5', '1', L))
fig = lambda name, w=1.0, cap='': f"\\begin{{figure}}[htbp]\\centering\\includegraphics[width={w}\\textwidth]{{figures/{name}_en.png}}" + (f"\\caption{{{cap}}}" if cap else '') + "\\end{figure}"
c1, cL, h1, hL, l1 = bd(c, '1'), bd(c, L), bd(hi, '1'), bd(hi, L), bd(lo, '1')

ABSTRACT = f"""In the winter layout put to the borough council on November 2, 2026 (file 1266880005), cyclists riding in the direction of motor traffic would share the traffic lane with cars; in the layout drawn by the borough\\textquoteright{{}}s consultant in 2023, that lane is 3.5\\,m wide between two rows of parked cars. A driver may pass a cyclist only with the clearance of art.~341 of the Highway Safety Code, which such a lane does not leave, so a driver who catches up stays behind. This note estimates how many cars build up behind one cyclist at the winter morning peak. The borough\\textquoteright{{}}s loop counter at Kensington recorded, on the {F['weekdays']} winter weekdays of 2025--26, a mean of {am['motor_mean']:.0f} motor vehicles in the busiest morning hour ({am['motor_p90']} on a busy day, 90th percentile) and {am['bikes_eb_mean']:.1f} eastbound bicycles; the Miovision count at Grand on January 29, 2025 gives {G['am_flow_per_hour']:.0f} eastbound cars an hour between 07:00 and 09:00, of which {pc(G['07-09']['turn_share'])} turned off. Cars catch up with a slower cyclist at a rate set by the flow and the two speeds, and leave the queue when they turn off at a cross street. With a cyclist at 15\\,km/h and cars at 25\\,km/h (stops included) and 7\\,\\% of queued cars turning off at each of the {GE['intersections']} cross streets between Cavendish and Girouard, a cyclist is caught by {c['caught_per_km']:.1f} cars per kilometre and has {c1['expected_queue']:.1f} cars behind after 1\\,km and {cL['expected_queue']:.1f} after the {Lkm}\\,km to Girouard (simulation: median {cL['median']}, 10th--90th percentiles {cL['p10']}--{cL['p90']}). Across the range of assumptions the queue after 1\\,km runs from {l1['expected_queue']:.1f} to {h1['expected_queue']:.1f} cars, and to {hL['expected_queue']:.1f} over the whole stretch on a busy morning with a slow cyclist. Seen from the drivers\\textquoteright{{}} side, about {D['cars_caught_per_peak_hour']:.0f} of the {c['q']} cars of the peak hour ({pc(D['share_of_peak_hour_cars'])}) would follow a cyclist, each losing at most {D['max_delay_min_1km']:.1f}\\,min per kilometre. The speeds are assumptions, not measurements, and the turn-off share comes from one intersection; the result is a range, not a measurement."""

LAY = f"""Lay summary

In the winter layout the borough proposes for rue de Terrebonne, cyclists going the same way as the cars would ride in the traffic lane, between two rows of parked cars. That lane is too narrow for a car to pass a cyclist with the one metre the Highway Safety Code requires, so a driver who catches up has to stay behind. This note estimates how many cars would line up behind one cyclist at the winter morning rush.

The borough's own counter at Kensington shows about {am['motor_mean']:.0f} cars an hour at the busiest morning hour in winter, and up to about {am['motor_p90']} on a busy day. If a cyclist rides at 15 km/h and cars would otherwise average 25 km/h, a few cars catch up every kilometre, and a few of them turn off at the cross streets. The result: a cyclist typically has two or three cars behind by the time they reach Girouard, from about one on a quiet morning to about eight on a busy morning with a slow cyclist on snow.

Most drivers never meet a cyclist: about {D['cars_caught_per_peak_hour']:.0f} of the {c['q']} cars of the peak hour would end up behind one, each losing at most about a minute and a half per kilometre. The speeds are assumptions, not measurements, so the figures are a range rather than a count.
"""
LAY_SHORT = f"""Lay summary

In the borough's winter layout, cyclists going the same way as the cars would ride in a traffic lane too narrow for a car to pass them with the one metre the law requires, so drivers who catch up stay behind. Using the borough's counter (about {am['motor_mean']:.0f} cars an hour at the winter morning rush) and assumed speeds of 15 km/h for the cyclist and 25 km/h for cars, a cyclist typically has two or three cars behind by Girouard: about one on a quiet morning, about eight on a busy one with a slow cyclist on snow. About {D['cars_caught_per_peak_hour']:.0f} of the {c['q']} peak-hour cars would follow a cyclist, each losing at most about a minute and a half per kilometre.
"""
open(os.path.join(HERE, 'lay_abstract_en_long.txt'), 'w', encoding='utf-8').write(LAY.strip() + '\n')
open(os.path.join(HERE, 'lay_abstract_en_short.txt'), 'w', encoding='utf-8').write(LAY_SHORT.strip() + '\n')
wc = lambda t: len(t.split()); lim = wc(' '.join(LAY.strip().split('\n\n')[1:3])); short_wc = wc(' '.join(LAY_SHORT.strip().split('\n\n')[1:]))
assert short_wc <= lim, f'short lay summary {short_wc} words exceeds {lim}'; print(f'lay summary: long {wc(LAY)} words, short {short_wc} (limit {lim})')
LAY_TEX = '\\section*{Lay summary}\n' + '\n\n'.join(esc(p) for p in LAY_SHORT.strip().split('\n\n')[1:]) + '\n'

NOTE = r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage[a4paper,margin=2.2cm]{geometry}\usepackage{graphicx,booktabs,amsmath,caption}\usepackage[hidelinks]{hyperref}
\captionsetup{font=small,labelfont=bf}\setlength{\parindent}{0pt}\setlength{\parskip}{0.6em}
\begin{document}
{\LARGE\textbf{How many cars queue behind a cyclist in a shared winter lane on rue de Terrebonne?}}\\[4pt]
{\small Terrebonne-open-sources, ''' + STAMP + r'''. Author: a resident of Côte-des-Neiges--Notre-Dame-de-Grâce (see the repository\textquoteright{}s « About the author »). Companion to the notes on street width, winter counts and parking. Data: the borough\textquoteright{}s loop counter (request 2026-300) and Miovision count (request 2026-634), the City géobase (CC-BY 4.0). Code, tables and figures: \url{''' + URL + r'''}.}

\section*{Abstract}
''' + ABSTRACT + r'''

''' + LAY_TEX + r'''
\tableofcontents

\section{Question}
The borough\textquoteright{}s offer to City council of November 2, 2026 (file 1266880005, p.~3) describes the winter measure: « retirer, durant la période hivernale, la bande cyclable située dans le même sens que la circulation véhiculaire afin de permettre son utilisation comme bande de stationnement. Les cyclistes circulant dans le même sens que la circulation seraient alors appelés à partager la voie de circulation avec les véhicules motorisés. » The only drawing of such a layout on the public record is the consultant\textquoteright{}s Aménagement~A (EXP, 2023, Figure~6-6, p.~72): a 3.5\,m lane between two 2.4\,m parking lanes. The street-width note in this repository measures the roadway at 11.0\,m curb to curb.

The question here is not whether a car fits beside a cyclist, which the street-width note addresses, but what happens when it does not: how many cars build up behind one cyclist, at the hour when most of them ride.

\section{The rules that apply}
Highway Safety Code (LégisQuébec, text current to October 15, 2026):
\begin{itemize}
\item art.~341: a driver may pass a cyclist in the same lane only with a reasonable distance, at least 1\,m where the limit is 50\,km/h or less (Terrebonne is posted at 30\,km/h); otherwise the driver stays behind.
\item art.~487: the cyclist rides as near the right edge as possible, taking into account the state of the roadway and the risk of dooring.
\item On a street designated as a vélorue by a municipality (arts.~496.1--496.8), a cyclist may ride on the full width of the lane (art.~496.8); art.~341 applies, but a driver is exempt from the distance where there is enough room to pass without danger (art.~496.3).
\end{itemize}
In a 3.5\,m lane between parked cars, a cyclist clear of the doors and a car of 1.8--2.0\,m leave no room for the 1\,m clearance; a cyclist who takes the lane leaves none at all. Under either status, the case modelled here is a driver who catches up and stays behind.

\section{Data}
\begin{itemize}
\item \textbf{Flows.} The borough\textquoteright{}s Eco-Counter loop at Terrebonne/Kensington, hourly, July 26, 2025 -- May 11, 2026 (request 2026-300). East of Cavendish Terrebonne is one-way eastbound, so the motor-vehicle count is the traffic of the lane cyclists would share. Winter weekdays, December 1 -- March 31 (''' + str(F['weekdays']) + r''' days). The time stamps mark the end of each hour (the period starts at 08:58 and the first record is 09:00).
\item \textbf{Turning off.} Miovision count at Terrebonne/Grand, January 29, 2025, light vehicles on the eastbound approach (request 2026-634, B2): between 07:00 and 09:00, ''' + f"{G['07-09']['through']} through, {G['07-09']['right']} right, {G['07-09']['left']} left ({pc(G['07-09']['turn_share'])} turning off); over 12 hours {pc(G['12h']['turn_share'])}" + r'''. Grand is a boulevard; the turn-off share at the one-way local cross streets is lower.
\item \textbf{Geometry.} The City géobase frame used by the street-width note: ''' + f"{GE['cavendish_to_girouard_km']:.2f}\\,km and {GE['intersections']} cross streets from Cavendish to Girouard ({GE['per_km']:.1f} per km)" + r'''.
\end{itemize}
''' + fig('hourly_flows', 1.0, f"Winter weekday flows at Kensington, by hour. Morning peak {am['hour']:02d}:00--{am['hour'] + 1:02d}:00: {am['motor_mean']:.0f} motor vehicles (busy day {am['motor_p90']}), {am['bikes_eb_mean']:.1f} eastbound bicycles; afternoon peak {pm['hour']:02d}:00--{pm['hour'] + 1:02d}:00: {pm['motor_mean']:.0f} (busy day {pm['motor_p90']}).") + r'''
As a check, the Miovision count at Grand gives ''' + f"{G['am_flow_per_hour']:.0f}" + r''' eastbound cars an hour between 07:00 and 09:00 on January 29, 2025, close to the counter\textquoteright{}s winter mean.

\section{Model}
A cyclist rides at average speed $v_b$; the cars behind would average $v_c > v_b$; both speeds include the stops. Cars pass the counter at $q$ vehicles an hour. Per kilometre the cyclist rides, the cars that catch up number
\[ \lambda = q\left(\frac{1}{v_b} - \frac{1}{v_c}\right). \]
With no passing they queue. A queued car leaves when it turns off at a cross street, with probability $s$ at each one; with $n$ cross streets per kilometre, $\mu = s\,n$, and the expected queue after $x$\,km is
\[ N(x) = \frac{\lambda}{\mu}\left(1 - e^{-\mu x}\right), \]
which tends to $\lambda/\mu$ on a long street and to $\lambda x$ when no one turns off. A Monte Carlo simulation of the same process (catch-ups as a Poisson process along the cyclist\textquoteright{}s path, each queued car turning off with probability $s$ at each of the actual cross streets after Cavendish; 20,000 runs) gives the spread around the expectation.

\begin{table}[htbp]\centering\small
\begin{tabular}{lrrrrrrrr}\toprule
case & $q$ (veh/h) & $v_b$ & $v_c$ & $s$ & caught /km & \multicolumn{3}{c}{expected queue after} \\
 & & (km/h) & (km/h) & & & 0.5\,km & 1\,km & ''' + Lkm + r'''\,km \\\midrule
''' + rows + r'''
\bottomrule\end{tabular}
\caption{The three cases. Central: the mean winter morning peak. High: a busy morning (90th percentile), a slow cyclist on snow, fast cars, few turning off. Low: light traffic, a fast cyclist, slow cars, many turning off.}\end{table}

\section{Results}
''' + fig('queue_by_distance', 1.0, 'Cars queued behind one cyclist riding east from Cavendish, by distance, in the three cases.') + r'''
In the central case a cyclist has ''' + f"{c1['expected_queue']:.1f} cars behind after 1\\,km and {cL['expected_queue']:.1f} at Girouard; in the simulation the queue at Girouard has median {cL['median']} and 10th--90th percentiles {cL['p10']}--{cL['p90']}, and the cyclist reaches Girouard with no car behind in {pc(cL['share_zero'])} of runs. Averaged over the ride, {cL['time_avg']:.1f} cars follow. On a busy morning with a slow cyclist the queue at Girouard is {hL['expected_queue']:.1f} (percentiles {hL['p10']}--{hL['p90']}); on a quiet morning with a fast cyclist, under one" + r'''.

\begin{table}[htbp]\centering\small
\begin{tabular}{lrrrrrr}\toprule
case & km & mean & median & 10th--90th & no car behind & mean over the ride \\\midrule
''' + mc_rows + r'''
\bottomrule\end{tabular}
\caption{Simulation, 20,000 runs per case and distance.}\end{table}

\textbf{The drivers\textquoteright{} side.} About ''' + f"{D['cyclists_eb_peak_hour']:.1f}" + r''' eastbound cyclists pass Kensington in the morning peak hour. In the central case each is caught by ''' + f"{D['cars_caught_per_cyclist_1km']:.1f}" + r''' cars per kilometre, so about ''' + f"{D['cars_caught_per_peak_hour']:.0f} of the {c['q']} cars of that hour ({pc(D['share_of_peak_hour_cars'])}) end up behind a cyclist for part of their trip, each losing at most {D['max_delay_min_1km']:.1f}\\,min per kilometre followed" + r'''. The queue is a constant presence for the cyclist and an occasional one for drivers.

''' + fig('sensitivity_1km', 0.72, 'Expected queue after 1\\,km at the central flow and turn-off share, by the two speeds.') + r'''
The result depends most on the gap between the two speeds: at the central flow, the queue after 1\,km ranges from none, when the cars are no faster than the cyclist, to ''' + f"{S['sensitivity_1km']['max']:.1f}" + r''' cars with a 10\,km/h cyclist and 30\,km/h cars.

\section{What the estimate leaves out}
\begin{itemize}
\item \textbf{Speeds.} No speed was measured on Terrebonne for either mode. The cases bracket plausible averages with the all-way stops and signals of the street; winter conditions slow cyclists more than cars.
\item \textbf{Turning off.} One intersection (Grand, a boulevard) was measured; the local cross streets, mostly one-way, are assumed to take fewer cars.
\item \textbf{Passing.} The model assumes no pass. Where a driver judges there is room (art.~496.3 on a vélorue), some cars will pass, shortening the queue at the cost of closer passes.
\item \textbf{Several cyclists, snow, the west half.} Cyclists are treated one at a time; snowbanks along parked cars narrow the lane further; west of Cavendish the shared direction is westbound and there is no motor-vehicle count comparable to the Kensington loop, so the estimate covers the east half only.
\item \textbf{Uniform flow.} The counter\textquoteright{}s flow at Kensington is taken to hold along the whole stretch; in fact cars enter and leave at every cross street, so the flow is lower near Cavendish and may differ near Girouard.
\end{itemize}

\section{Reproduction}
\texttt{queue\_analysis.py} reads the two released workbooks from the sibling repository Terrebonne-access-requests (requests 2026-300 and 2026-634) and the street frame of the 1954 plans folder, and writes \texttt{summary.json}, the tables and the figures; \texttt{build\_docs.py} writes this note, the deck and the lay abstracts from \texttt{summary.json}.
\end{document}
'''

DECK = r'''\documentclass[aspectratio=169,10pt]{beamer}
\usetheme{default}\usefonttheme{professionalfonts}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}\usepackage{booktabs,amsmath}
\setbeamercolor{frametitle}{fg=black}\setbeamercolor{title}{fg=black}
\title{Cars queued behind a cyclist in a shared winter lane}\subtitle{Rue de Terrebonne, winter morning peak}\author{Terrebonne-open-sources (a resident of Côte-des-Neiges--Notre-Dame-de-Grâce)}\date{''' + STAMP + r'''}
\begin{document}
\frame{\titlepage}
\begin{frame}{The question}\begin{itemize}
\item Winter layout of November 2, 2026: cyclists going with traffic « appelés à partager la voie de circulation avec les véhicules motorisés » (file 1266880005, p.~3).
\item EXP 2023, Figure 6-6: a 3.5\,m lane between two parking lanes.
\item Passing a cyclist needs 1\,m of clearance (art.~341); that lane does not leave it. A driver who catches up stays behind.
\item How many cars build up behind one cyclist at the morning peak?
\end{itemize}\end{frame}
\begin{frame}{The traffic}\centering\includegraphics[width=0.95\textwidth]{figures/hourly_flows_en.png}\\\small Kensington loop, ''' + f"{F['weekdays']} winter weekdays: {am['motor_mean']:.0f} motor vehicles at {am['hour']:02d}:00--{am['hour'] + 1:02d}:00 (busy day {am['motor_p90']}), {am['bikes_eb_mean']:.1f} eastbound bicycles" + r'''\end{frame}
\begin{frame}{The model}\begin{itemize}
\item Cars catch up at $\lambda = q\,(1/v_b - 1/v_c)$ per km ridden; no passing, so they queue.
\item A queued car leaves when it turns off: share $s$ at each of ''' + f"{GE['intersections']} cross streets in {GE['cavendish_to_girouard_km']:.1f}\\,km" + r''' (Cavendish $\to$ Girouard).
\item Expected queue $N(x) = (\lambda/\mu)(1-e^{-\mu x})$, $\mu = s \times$ cross streets per km; simulation for the spread.
\item Turning off measured at Grand (Jan 29, 2025): ''' + pc(G['07-09']['turn_share']) + r''' at 07:00--09:00; local streets assumed lower (4--12\,\%).
\end{itemize}\end{frame}
\begin{frame}{Three cases}\centering\small
\begin{tabular}{lrrrrrrrr}\toprule
case & $q$ & $v_b$ & $v_c$ & $s$ & caught/km & 0.5\,km & 1\,km & ''' + Lkm + r'''\,km \\\midrule
''' + rows + r'''
\bottomrule\end{tabular}\\[6pt]speeds in km/h, stops included; queue = expected cars behind the cyclist\end{frame}
\begin{frame}{Cars queued behind one cyclist}\centering\includegraphics[width=0.9\textwidth]{figures/queue_by_distance_en.png}\end{frame}
\begin{frame}{The result}\begin{itemize}
\item Central case: ''' + f"{c1['expected_queue']:.1f} cars after 1\\,km, {cL['expected_queue']:.1f} at Girouard (simulation median {cL['median']}, 10th--90th {cL['p10']}--{cL['p90']})." + r'''
\item Busy morning, slow cyclist: ''' + f"{hL['expected_queue']:.1f} at Girouard; quiet morning, fast cyclist: under one." + r'''
\item Drivers\textquoteright{} side: about ''' + f"{D['cars_caught_per_peak_hour']:.0f} of {c['q']} peak-hour cars ({pc(D['share_of_peak_hour_cars'])}) follow a cyclist, each losing at most {D['max_delay_min_1km']:.1f}\\,min/km." + r'''
\end{itemize}\end{frame}
\begin{frame}{What drives it}\centering\includegraphics[width=0.62\textwidth]{figures/sensitivity_1km_en.png}\\\small the gap between the two speeds matters most\end{frame}
\begin{frame}{Limits}\begin{itemize}
\item Speeds assumed, not measured; turning off measured at one intersection.
\item No passing assumed; on a vélorue art.~496.3 lets a driver pass where judged safe (shorter queue, closer passes).
\item One cyclist at a time; snowbanks narrow the lane further; west of Cavendish not covered (no comparable count).
\item Code, data and tables: \url{''' + URL + r'''}
\end{itemize}\end{frame}
\end{document}
'''
for name, tex in (('shared_lane_queue_note_en', NOTE), ('shared_lane_queue_deck_en', DECK)):
    open(os.path.join(HERE, name + '.tex'), 'w', encoding='utf-8').write(tex)
    for _ in range(2): r = subprocess.run(['pdflatex', '-interaction=nonstopmode', name + '.tex'], cwd=HERE, capture_output=True, text=True)
    for ext in ('aux', 'log', 'out', 'toc', 'nav', 'snm'):
        try: os.remove(os.path.join(HERE, f'{name}.{ext}'))
        except FileNotFoundError: pass
    info = subprocess.run(['pdfinfo', os.path.join(HERE, name + '.pdf')], capture_output=True, text=True).stdout
    print(name, info.split('Pages:')[1].split()[0] if 'Pages:' in info else 'FAILED', 'pages')
