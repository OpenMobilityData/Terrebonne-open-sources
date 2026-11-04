#!/usr/bin/env python3
"""Note (A4, pdflatex) and slide deck (beamer 16:9) in English from summary.json, street_width_by_block.csv and the figures.
Usage: python3 build_docs.py  (writes terrebonne_street_width_note_en.pdf and terrebonne_street_width_deck_en.pdf)"""
import csv, json, os, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); S = json.load(open(os.path.join(HERE, 'summary.json')))
B = list(csv.DictReader(open(os.path.join(HERE, 'street_width_by_block.csv'), encoding='utf-8')))
STAMP = datetime.datetime.now().strftime('%Y-%m-%d'); C = S['curb']; R = S['right_of_way']
meds = [float(b['curb_median']) for b in B if b['curb_median']]
esc = lambda s: s.replace('&', '\\&').replace('%', '\\%').replace("'", "\\textquoteright{}").replace('–', '--')
rows = '\n'.join(f"{esc(b['block'])} & {b['stations_with_both_curbs']}/{b['stations']} & {b['curb_median']} & {b['curb_p10']}--{b['curb_p90']} & {b['row_median']} & {b['sidewalk_N_median']} & {b['sidewalk_S_median']} \\\\" for b in B)
URL = 'https://openmobilitydata.github.io/Terrebonne-open-sources/2015-lidar-terrebonne-street-width/'
note = r'''\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage[a4paper,margin=2.2cm]{geometry}\usepackage{graphicx,booktabs,longtable,hyperref}\usepackage[hidelinks]{hyperref}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.6em}
\begin{document}
{\LARGE\textbf{How wide is rue de Terrebonne? The roadway along the lane, from the City\textquoteright{}s 2015 LiDAR}}\\[4pt]
{\small Terrebonne-open-sources, ''' + STAMP + r'''. Data: Ville de Montréal, LiDAR aérien 2015 and unités d\textquoteright{}évaluation foncière (open data, CC-BY 4.0). Method and code: \url{''' + URL + r'''}.}

\section*{Question}
The winter layout proposed for rue de Terrebonne (borough file 1266880005, adopted November 2, 2026) keeps the contraflow protected lane and turns the lane running with traffic into parking for the winter, so that cyclists going with traffic share the traffic lane. The cross-section drawn for that type of layout in the borough\textquoteright{}s 2023 study (EXP, Figure 6-6, p.~72) is, from the south property line: sidewalk 1.8 m, contraflow lane 2.0 m, buffer 0.5 m, parking 2.4 m, shared lane 3.5 m, parking 2.4 m, sidewalk 1.8 m, that is 10.8 m from curb to curb in a 14.4 m section. Whether the street is in fact 10.8 m wide, everywhere along the 2.4 km, decides how much room any winter layout has. This note measures it.

\section*{Data and method}
The City\textquoteright{}s 2015 airborne LiDAR (six 1 km tiles, NAD83(CSRS)/MTM 8; classes ground, high vegetation, building) was rasterized once for the earlier parking work: the mean elevation of ground-class returns on a 0.25 m grid along the corridor. On that surface a cross-section is sampled every 2 m along the lane\textquoteright{}s axis (the City géobase, from the lane\textquoteright{}s west end to Girouard; ''' + f"{S['stations']}" + r''' stations), from 16 m south to 16 m north of the axis, every 0.1 m. On each side, scanning outward from the axis, the curb is the first place between 3 and 8 m from the axis where the ground rises by at least 7 cm over 0.5 m; its position is the point of steepest rise in that window. A Montréal curb face is 10 to 15 cm high; a driveway ramp at about 1:12 rises 4 cm over 0.5 m and does not pass, though a steeper apron sometimes does. The LiDAR was flown on two weeknights with cars parked at the curbs, and under a car or a dense tree there are no ground returns; a station is kept only when both curbs are found and the width lies between 9 and 13 m (''' + f"{S['kept']}" + r''' stations). The right-of-way is measured on the same line as the distance between the first parcel outline on each side (the City\textquoteright{}s assessment units); the sidewalk zone is the parcel line to the curb.

\section*{Results}
\begin{itemize}
\item Curb to curb: median ''' + f"{C['median']}" + r''' m over the ''' + f"{C['n']}" + r''' stations kept; 10\,\% of stations read under ''' + f"{C['p10']}" + r''' m and 10\,\% over ''' + f"{C['p90']}" + r''' m (the high tail is aprons taken for curbs). The block medians run from ''' + f"{min(meds)}" + r''' to ''' + f"{max(meds)}" + r''' m: the roadway is the same width along the whole lane, within a few decimetres.
\item Right-of-way: ''' + f"{R['median']}" + r''' m at every block but the Belmore stub and three lots (the 66-foot standard, 20.12 m); sidewalk zones about ''' + f"{S['sidewalk_N']['median']}" + r''' m on the north side and ''' + f"{S['sidewalk_S']['median']}" + r''' m on the south side (parcel line to curb, including the grass strip).
\item EXP\textquoteright{}s own statement of the existing section (report p.~50, PDF p.~61): « L\textquoteright{}emprise fonctionnelle actuelle de la rue de Terrebonne est d\textquoteright{}environ 14,6 m, soit une chaussée d\textquoteright{}environ 11 m et deux trottoirs d\textquoteright{}environ 1,8 m. » The LiDAR\textquoteright{}s 11.0 m is EXP\textquoteright{}s « environ 11 m »; EXP\textquoteright{}s 14.6 m is roadway plus paved sidewalks, not the 20.1 m right-of-way, the difference being the grass strips.
\item Against the 2023 drawing: 10.8 m of lanes and parking in an 11.0 m roadway. The winter layout fits with about 0.2 m to spare across the street. A shared lane wider than 3.5 m would have to come from the parking bands (2.4 m), the buffer (0.5 m) or the contraflow lane (2.0 m).
\item Before 2024 the street was two-way with parking on both sides; two 3.3 m lanes (EXP 2023) and two parking bands of 2.2 m make the same 11.0 m.
\end{itemize}

\begin{center}\includegraphics[width=\textwidth]{figures/street_width_profile_en.png}\end{center}
\begin{center}\includegraphics[width=\textwidth]{figures/street_width_sections_en.png}\end{center}
\begin{center}\includegraphics[width=\textwidth]{figures/street_width_overhead_en.png}\end{center}
\begin{center}\includegraphics[width=\textwidth]{figures/street_width_west_end_en.png}\end{center}

\section*{The west end}
The public street ends where the lane ends, at the Loyola campus boundary (the City géobase\textquoteright{}s last segment, 1320365, ends there; beyond it the roadway is the campus\textquoteright{}s). The last public block, west end to Belmore, reads 11.0 m curb to curb (19 of 30 stations kept), a 20.09 m right-of-way and sidewalk zones of 4.4 m north and 4.7 m south: the same section as the rest of the street. It is two-way with no parking on either side; the 2015 surface and the pre-2024 imagery cannot measure the 2024 bike lanes, but an 11.0 m roadway holds, for example, two 2.0 m lanes with 0.5 m buffers and two 3.0 m travel lanes (arithmetic, not the marking plan).

\section*{By block}
{\small\begin{longtable}{@{}lrrrrrr@{}}\toprule Block (west to east) & kept/stations & curb--curb median (m) & p10--p90 & right-of-way (m) & sidewalk N (m) & sidewalk S (m)\\ \midrule
''' + rows + r'''
\bottomrule\end{longtable}}

\section*{Caveats}
\begin{itemize}
\item The curb is read from a 0.25 m elevation grid: a single reading is good to about 0.2 m; the block medians are the figures to use.
\item 2015 surface, 2024 layout: the curbs have not moved; the lane markings of 2024 are not in the LiDAR.
\item Stations hidden by parked cars or trees are left out, not interpolated; blocks with few kept stations (Hingston--Hampton, Hampton--Royal) carry more uncertainty.
\item The right-of-way is the City\textquoteright{}s parcel geometry, not a survey.
\end{itemize}
\end{document}
'''
deck = r'''\documentclass[aspectratio=169,11pt]{beamer}\usetheme{default}\usecolortheme{seahorse}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{helvet}\usepackage{booktabs}
\title{How wide is rue de Terrebonne?}\subtitle{The roadway along the lane, measured on the City\textquoteright{}s 2015 LiDAR}\author{Terrebonne-open-sources (a resident of Côte-des-Neiges--Notre-Dame-de-Grâce)}\date{''' + STAMP + r'''}
\begin{document}
\begin{frame}\titlepage\end{frame}
\begin{frame}{The question}\begin{itemize}
\item The winter layout adopted on November 2, 2026 (file 1266880005) turns the lane running with traffic into parking and has cyclists share the traffic lane.
\item The borough\textquoteright{}s 2023 study drew that type of section (EXP, Fig.~6-6): parking 2.4 + shared lane 3.5 + parking 2.4 + buffer 0.5 + contraflow lane 2.0 = \textbf{10.8 m} curb to curb.
\item Is the street 10.8 m wide, everywhere along its 2.4 km? That decides how much room any winter layout has.
\end{itemize}\vfill\scriptsize Source: EXP 2023, p.~72; borough file 1266880005, pp.~207--212 of the Nov.~2 bundle.\end{frame}
\begin{frame}{Data and method}\begin{itemize}
\item Ville de Montréal, LiDAR aérien 2015 (open data, CC-BY 4.0): ground returns averaged on a 0.25 m grid along the corridor.
\item A cross-section every 2 m along the lane\textquoteright{}s axis (''' + f"{S['stations']}" + r''' stations), 16 m each side, every 0.1 m.
\item Curb = the first rise of 7 cm over 0.5 m outward from the axis, 3--8 m out (a curb face is 10--15 cm; a 1:12 driveway ramp rises 4 cm and does not pass).
\item Night flight, cars at the curbs: no ground under a car. Stations with both curbs found and a width of 9--13 m are kept: ''' + f"{S['kept']}" + r'''.
\item Right-of-way: parcel line to parcel line on the same section (City assessment units).
\end{itemize}\end{frame}
\begin{frame}{The roadway is 11.0 m wide, along the whole street}\centering\includegraphics[width=\textwidth]{figures/street_width_profile_en.png}\end{frame}
\begin{frame}{What a cross-section looks like}\centering\includegraphics[width=\textwidth]{figures/street_width_sections_en.png}\end{frame}
\begin{frame}{Review: every curb detection on the LiDAR surface}\centering\includegraphics[height=0.86\textheight]{figures/street_width_overhead_en.png}\\{\tiny Hillshade of the ground surface in the street frame; red = north curb, blue = south curb; grey ticks on the axis = stations dropped (a parked car or a tree hid a curb, or the width fell outside 9--13 m).}\end{frame}
\begin{frame}{The west end, where the public street meets the Loyola campus}\centering\includegraphics[width=\textwidth]{figures/street_width_west_end_en.png}\\{\small The last public block (west end to Belmore) reads 11.0 m curb to curb (19 of 30 stations), a 20.09 m right-of-way and 4.4--4.7 m sidewalk zones: the same section as the rest of the street. Beyond the lane\textquoteright{}s end the roadway is the campus\textquoteright{}s, not the City\textquoteright{}s (géobase). The 2015 surface and the pre-2024 imagery cannot measure the 2024 bike lanes themselves; a two-way block with no parking fits 11.0 m as, for example, 2.0 + 0.5 + 3.0 + 3.0 + 0.5 + 2.0 (arithmetic, not the plan).}\end{frame}
\begin{frame}{The figures}\begin{itemize}
\item Curb to curb: median \textbf{''' + f"{C['median']}" + r''' m} (p10 ''' + f"{C['p10']}" + r''', p90 ''' + f"{C['p90']}" + r'''); block medians ''' + f"{min(meds)}" + r'''--''' + f"{max(meds)}" + r''' m.
\item Right-of-way ''' + f"{R['median']}" + r''' m everywhere but the Belmore stub and three lots: the 66-foot standard.
\item Sidewalk zones, parcel line to curb: ''' + f"{S['sidewalk_N']['median']}" + r''' m north, ''' + f"{S['sidewalk_S']['median']}" + r''' m south.
\item EXP 2023 itself (p.~50): « une chaussée d\textquoteright{}environ 11 m et deux trottoirs d\textquoteright{}environ 1,8 m », 14.6 m in all: the LiDAR reconciles with the study\textquoteright{}s own measure.
\item Before 2024: two 3.3 m lanes and two 2.2 m parking bands = 11.0 m. Winter layout: 10.8 m of the 11.0 m.
\end{itemize}\end{frame}
\begin{frame}{What it means for the shared lane}\begin{itemize}
\item The 2023 drawing uses 10.8 of the 11.0 m: \textbf{about 0.2 m spare across the whole street}.
\item A shared lane wider than 3.5 m can only come from the parking bands (2.4 m), the buffer (0.5 m) or the contraflow lane (2.0 m).
\item With a cyclist 0.75 m wide at 0.5 m from the parked cars and the Code\textquoteright{}s 1 m clearance, 1.75 m of the shared lane is left for a car 1.8--2.0 m wide before mirrors (EXP Fig.~6-6; the owner\textquoteright{}s sketches). The width measured here does not change that arithmetic; it confirms the drawing\textquoteright{}s premise.
\item In winter, windrows push the parked cars toward the lane line: the measured 11.0 m is the summer maximum.
\end{itemize}\end{frame}
\begin{frame}{Caveats and where to find it}\begin{itemize}
\item One reading is good to about 0.2 m (0.25 m grid); use the block medians. Blocks with few kept stations carry more uncertainty.
\item 2015 surface, 2024 markings: the curbs have not moved; the markings are not in the LiDAR.
\item Every station, every block and the code: \url{''' + URL + r'''}
\end{itemize}\end{frame}
\end{document}
'''
for name, src in (('terrebonne_street_width_note_en', note), ('terrebonne_street_width_deck_en', deck)):
    open(os.path.join(HERE, name + '.tex'), 'w', encoding='utf-8').write(src)
    for _ in range(2): subprocess.run(['pdflatex', '-interaction=batchmode', name + '.tex'], cwd=HERE, capture_output=True)
    for e in ('.aux', '.log', '.nav', '.out', '.snm', '.toc'):
        try: os.remove(os.path.join(HERE, name + e))
        except OSError: pass
    print(name, subprocess.run(['pdfinfo', os.path.join(HERE, name + '.pdf')], capture_output=True, text=True).stdout.split('Pages:')[1].split()[0], 'pages')
