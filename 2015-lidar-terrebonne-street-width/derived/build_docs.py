#!/usr/bin/env python3
"""Note (A4, pdflatex) and slide deck (beamer 16:9) in English from summary.json, street_width_by_block.csv, cross_street_summary.json, cross_street_blocks.csv and the figures.
Usage: python3 build_docs.py  (writes terrebonne_street_width_note_en.pdf and terrebonne_street_width_deck_en.pdf)"""
import csv, json, os, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__)); S = json.load(open(os.path.join(HERE, 'summary.json')))
B = list(csv.DictReader(open(os.path.join(HERE, 'street_width_by_block.csv'), encoding='utf-8')))
STAMP = datetime.datetime.now().strftime('%Y-%m-%d'); C = S['curb']; R = S['right_of_way']
meds = [float(b['curb_median']) for b in B if b['curb_median']]
esc = lambda s: s.replace('&', '\\&').replace('%', '\\%').replace("'", "\\textquoteright{}").replace('–', '--')

# ---------- the cross streets (cross_street_widths.py)
X = json.load(open(os.path.join(HERE, 'cross_street_summary.json'))); XB = list(csv.DictReader(open(os.path.join(HERE, 'cross_street_blocks.csv'), encoding='utf-8')))
ART = set(X['params']['arterial']); fl = lambda x: None if x in ('', None) else float(x)
XL = [b for b in XB if b['street'] not in ART]; loc = [b for b in XL if int(b['stations_with_both_curbs']) >= 10]
BM = X['block_modes_local']; lo, hi = round(BM['p10'], 1), round(BM['p90'], 1)          # the typical band of the local blocks' most frequent readings
in_band = [b for b in loc if 8.9 <= fl(b['curb_mode']) <= 9.6]
exc = [b for b in loc if not (8.9 <= fl(b['curb_mode']) <= 9.6)]
def side(b): return 'north' if b['side'] == 'N' else 'south'
exc_txt = '; '.join(f"{b['street']} {side(b)} {fl(b['curb_mode']):.1f} m" + (f" ({b['stations_with_both_curbs']} of {b['stations']} stations kept, {int(round(100 * fl(b['core_share'])))}\\,\\% of them within 0.5 m of that reading: low confidence)" if fl(b['core_share']) < 0.5 else (f" (a {fl(b['block_length_m']):.0f} m stub, {b['stations_with_both_curbs']} stations)" if int(b['stations']) < 30 else '')) for b in exc)
lowc = [b for b in loc if fl(b['core_share']) < 0.5]
blvd = {}
for b in XB:
    if b['street'] in ART and int(b['stations_with_both_curbs']) >= 10: blvd.setdefault(b['street'], []).append(fl(b['curb_mode']))
blvd_txt = ', '.join(f"{k} {min(v):.1f}" + (f"--{max(v):.1f}" if max(v) - min(v) >= 0.15 else '') + ' m' for k, v in blvd.items())
max_tt = max(max(int(b['no_parking_any_time_poles_L']), int(b['no_parking_any_time_poles_R'])) for b in XL)
no_sign_blocks = [b for b in XL if int(b['sign_poles_L']) == 0 or int(b['sign_poles_R']) == 0]
TS = X['terrebonne_stations']; W = X['winter_shared_without_contraflow']; T = X['terrebonne']
sh_lo, sh_hi = round(lo - 4.8, 1), round(hi - 4.8, 1); d_lo, d_hi = round(sh_lo - 3.5, 1), round(sh_hi - 3.5, 1); t_lo, t_hi = round(T - hi, 1), round(T - lo, 1)
best_lo, best_hi = round(sh_lo - 1.75, 1), round(sh_hi - 1.75, 1); door_lo, door_hi = round(sh_lo - 2.25, 1), round(sh_hi - 2.25, 1)   # the car's room: cyclist 0.75 m + 1 m clearance; + 0.5 m from the doors
XBX = json.load(open(os.path.join(HERE, 'cross_street_boxes_kensington.json'))); n_better = sum(1 for b in loc if fl(b['curb_mode']) - 4.8 > 3.5)
ARG = "Due to the width of the roads and the allocation of 2.5 metres to the bike lane and buffer zone, the shared lane along Terrebonne will be around a metre narrower than the lanes shared by drivers and cyclists on the smaller side streets intersecting with Terrebonne."
NOTE_PIC = (r"""\textbf{The comparison in one picture.} Figure~\ref{fig:boxes} draws the three widths to scale on the aerial imagery of Terrebonne and Kensington: Terrebonne from curb to curb (the block medians, """ + f"{XBX['drawn']['terrebonne_west']:.1f} and {XBX['drawn']['terrebonne_east']:.1f} m), the {XBX['residual']:.1f} m that remain beside the contraflow lane and its buffer ({XBX['contraflow_plus_buffer']:.1f} m), where the December layout puts parking, the shared lane and parking, and Kensington from curb to curb ({XBX['drawn']['cross'][0]:.1f} m, both blocks). The two Terrebonne boxes are repeated on Kensington: the 11 m box overshoots its curbs, the {XBX['residual']:.1f} m box leaves room to spare." + r"""
\begin{figure}[h]\centering\includegraphics[height=0.6\textheight]{figures/cross_street_boxes_en.png}\caption{Rue de Terrebonne and avenue Kensington, the three widths to scale (aerial imagery: Gouvernement du Québec, Imagerie\_GQ, before the 2024 lane; curbs and widths: City LiDAR 2015).}\label{fig:boxes}\end{figure}

\textbf{What the cross streets show.} In one sentence: """ + esc(ARG) + r""" The author, who cycles the side streets, finds them already tight for a car to pass, even in summer; Terrebonne\textquoteright{}s shared lane for winter will be narrower still. Riding on the side streets is accepted practice: they are short blocks, used by drivers and cyclists to reach an address and, by cyclists, to move between the longer streets that carry bike lanes, so a driver held behind a cyclist is held for a block; Terrebonne is 2.4 km, and a driver held there is held for the length of the street. The arithmetic agrees with the experience. In the best case for a passing driver, the cyclist against the parked cars and one metre of clearance, a shared lane of """ + f"{sh_lo:.1f} to {sh_hi:.1f} m leaves {best_lo:.1f} to {best_hi:.1f} m for the car; with the cyclist 0.5 m from the doors, {door_lo:.1f} to {door_hi:.1f} m. The winter layout" + r"""\textquoteright{}s 3.5 m leaves 1.75 m and 1.25 m. The lane the winter layout draws for Terrebonne is therefore tighter than the shared lane of """ + f"{n_better} of the {len(loc)} local cross-street blocks measured, and it is meant for the length of the street, in winter, where the cross streets serve a block or two." + r"""

""")
DECK_PIC = (r"""\begin{frame}{The comparison in one picture: Terrebonne and Kensington}\centering\includegraphics[height=0.9\textheight]{figures/cross_street_boxes_en.png}\end{frame}
""")
DECK_ARG = (r"""\item """ + esc(ARG) + r"""
\item The side streets are already tight for a car to pass, even in summer (the author\textquoteright{}s experience of them); the winter shared lane will be narrower still. They are short, so a driver held behind a cyclist is held for a block; Terrebonne is 2.4 km.
\item A pass on a cross street leaves the car """ + f"{best_lo:.1f}--{best_hi:.1f} m in the best case ({door_lo:.1f}--{door_hi:.1f} m with 0.5 m from the doors); the winter layout" + r"""\textquoteright{}s 3.5 m leaves 1.75 m (1.25 m). Tighter than """ + f"{n_better} of the {len(loc)} blocks measured." + r"""
""")
def xcell(b):
    if b is None: return '--'
    if b['curb_mode'] in ('', None) or int(b['stations_with_both_curbs']) < 10: return f"-- ({b['stations_with_both_curbs']})"
    return f"{fl(b['curb_mode']):.1f} / {fl(b['curb_median']):.1f} ({b['stations_with_both_curbs']})" + ('*' if fl(b['core_share']) < 0.5 else '')
def xsigns(b): return '--' if b is None else f"{b['sign_poles_L']}+{b['sign_poles_R']} ({int(b['no_parking_any_time_poles_L']) + int(b['no_parking_any_time_poles_R'])})"
streets = []
for b in sorted(XB, key=lambda b: int(b['order'])):
    if b['street'] not in [s_[0] for s_ in streets]: streets.append((b['street'], {}))
    dict(streets)[b['street']][b['side']] = b
xrows = '\n'.join(f"{esc(st)} & {'one-way' if all(int(x['one_way']) for x in d.values()) else 'two-way'} & {xcell(d.get('N'))} & {xsigns(d.get('N'))} & {xcell(d.get('S'))} & {xsigns(d.get('S'))} \\\\" for st, d in streets)
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

\section*{EXP\textquoteright{}s three sections against the measured roadway}
\begin{center}\includegraphics[width=0.75\textwidth]{../raw/exp2023_fig3-1_configuration_2023.png}\\ {\small 2023 (EXP Fig.~3-1, report p.~25): 2.2 + 3.3 + 3.3 + 2.2 = 11.0 m curb to curb.}\end{center}
\begin{center}\includegraphics[width=0.75\textwidth]{../raw/exp2023_fig6-7_amenagement_B.png}\\ {\small Today, Aménagement B (Fig.~6-7, p.~72): 1.8 + 0.5 + 3.5 + 2.5 + 0.5 + 2.0 = 10.8 m.}\end{center}
\begin{center}\includegraphics[width=0.75\textwidth]{../raw/exp2023_fig6-6_amenagement_A.png}\\ {\small Winter, assumed to be Aménagement A (Fig.~6-6, p.~72): 2.4 + 3.5 + 2.4 + 0.5 + 2.0 = 10.8 m; applied to B\textquoteright{}s bands, 2.3 + 3.5 + 2.5 + 0.5 + 2.0 = 10.8 m.}\end{center}
Every section EXP drew fits the measured 11.0 m with 0 to 0.2 m to spare; none has room for a wider shared lane without narrowing the parking bands, the buffer or the contraflow lane. The figures are reproduced from the borough\textquoteright{}s published study (Terrebonne-open-sources, 2023-exp-mobility-study).

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

NOTE_X = r"""\section*{The cross streets}
\textbf{Question.} Most of the streets that cross rue de Terrebonne between the lane\textquoteright{}s west end and Girouard are one-way local streets with parking on both sides and a single lane shared by cars and bicycles: the arrangement the winter layout gives the direction riding with traffic, without the contraflow lane (2.0 m) and its buffer (0.5 m). The winter section leaves 8.3 m for parking, shared lane and parking (2.4 + 3.5 + 2.4). How wide are the cross streets, and do they share a typical width?

\textbf{Method.} The same ground raster and the same curb detector, applied to the first block of each cross street on each side of Terrebonne (the géobase segments that meet the intersection), from 20 m past the intersection (clear of the curb returns) to 240 m or the block\textquoteright{}s end: a cross-section every 2 m, 14 m each side; the curb window runs 2.5 to 8 m from the axis (11 m for the three two-way boulevards, Cavendish, Grand and Girouard); a station is kept when both curbs are found and the width lies between 5 and 13 m (22 m for the boulevards). """ + f"{X['blocks']} blocks at {X['streets']} streets, {X['stations']:,} stations, {X['kept']:,} kept." + r""" A lowered curb at a driveway apron, or a curb hidden under a tree, makes the detector read the next rise further out, so a block\textquoteright{}s readings have a tight core and a tail toward wider values, never narrower: the figure reported per block is the most frequent reading (0.2 m bins), with the median and the 10th--90th percentiles beside it. The City\textquoteright{}s parking-sign inventory gives, for each side of each block, the number of sign poles within 12 m of the axis and the number carrying « \textbackslash{}A EN TOUT TEMPS » (no parking at any time).

\textbf{Results.}
\begin{itemize}
\item The local cross streets (""" + f"{len(XL)} blocks, all one-way; {len(loc)} with ten or more stations kept) read {lo:.1f} to {hi:.1f} m curb to curb: over all their stations the most frequent reading is {X['local']['mode']:.1f} m and the median {X['local']['median']:.1f} m; block by block, {len(in_band)} of {len(loc)} lie between 8.9 and 9.6 m. The others: {exc_txt}." + r"""
\item Every local block has parking signs on both sides""" + (f" but {len(no_sign_blocks)}" if no_sign_blocks else '') + f", with at most {max_tt} « \\textbackslash{{}}A EN TOUT TEMPS » poles per side (the corner clearances): parking on both sides, under the time restrictions the signs give, is the rule." + r"""
\item The three two-way boulevards are wider: """ + blvd_txt + r""".
\item Rue de Terrebonne itself: """ + f"{T:.1f} m (most frequent reading {TS['mode']:.2f} m, median {TS['median']:.1f} m), {t_lo:.1f} to {t_hi:.1f} m wider than its local cross streets." + r"""
\item The arithmetic. The winter section spends 2.5 m on the contraflow lane and its buffer and leaves 8.3 m for parking, shared lane and parking. A cross street of """ + f"{lo:.1f} to {hi:.1f} m with the same two 2.4 m parking bands leaves {sh_lo:.1f} to {sh_hi:.1f} m for its shared lane. The 3.5 m shared lane the winter layout draws on Terrebonne is {d_lo:.1f} to {d_hi:.1f} m narrower than the lane the cross streets give the same arrangement: the cross streets are not the equivalent of the winter layout; in the part that a cyclist riding with traffic uses, they are about a metre wider." + r"""
\end{itemize}

\begin{center}\includegraphics[width=\textwidth]{figures/cross_street_widths_en.png}\end{center}
\begin{center}\includegraphics[width=0.85\textwidth]{figures/cross_street_widths_hist_en.png}\end{center}
\begin{center}\includegraphics[width=\textwidth]{figures/cross_street_widths_review_en.png}\end{center}

\textbf{By street.} Most frequent reading / median, in metres, and the number of stations kept, for the first block north and south of Terrebonne; * = fewer than half the stations within 0.5 m of the most frequent reading; signs = parking-sign poles left + right of the block\textquoteright{}s axis, with the number of « \textbackslash{}A EN TOUT TEMPS » poles in brackets.
{\small\begin{longtable}{@{}llllll@{}}\toprule Street (west to east) & direction & north block & signs & south block & signs\\ \midrule
""" + xrows + r"""
\bottomrule\end{longtable}}

\textbf{Caveats, for this part.} The cross streets\textquoteright{} parking bands are not marked: cars park at the curb, and a parked car takes 2.0 to 2.2 m with its mirrors, so the 2.4 m band is the drawing\textquoteright{}s figure applied for comparison. Snow windrows narrow Terrebonne and its cross streets alike. Only the first block on each side is measured; a street may change further from Terrebonne. The sign counts are an indicator of the parking regime, not a reading of the regulations. 2015 surface, as above.
"""

DECK_X = r"""\begin{frame}{The cross streets: the same arrangement, without the contraflow lane}\begin{itemize}
\item Most cross streets of Terrebonne are one-way local streets with parking on both sides and one lane shared by cars and bicycles: what the winter layout gives the direction riding with traffic, less the contraflow lane (2.0 m) and its buffer (0.5 m).
\item The winter section leaves \textbf{8.3 m} for parking, shared lane and parking (2.4 + 3.5 + 2.4). How wide are the cross streets?
\item Same LiDAR surface, same curb detector, the first block of each cross street on each side of Terrebonne: """ + f"{X['blocks']} blocks at {X['streets']} streets, {X['kept']:,} stations kept." + r"""
\item Driveway aprons and tree cover make the detector read wide, never narrow: per block, the most frequent reading is reported, with the median and the 10th--90th percentiles.
\end{itemize}\end{frame}
\begin{frame}{The local cross streets are """ + f"{lo:.1f} to {hi:.1f}" + r""" m wide; Terrebonne is 11.0 m}\centering\includegraphics[width=\textwidth]{figures/cross_street_widths_en.png}\end{frame}
\begin{frame}{Every station: the cross streets against Terrebonne}\centering\includegraphics[width=0.78\textwidth]{figures/cross_street_widths_hist_en.png}\\[4pt]\scriptsize\begin{tabular}{lrl}\toprule & curb to curb (m) & \\ \midrule
Local cross streets (one-way, parking both sides), """ + f"{len(loc)} blocks & {lo:.1f}--{hi:.1f} & most frequent readings per block; {len(in_band)} of {len(loc)} between 8.9 and 9.6 m" + r"""\\
Terrebonne, along the lane & """ + f"{T:.1f} & most frequent reading {TS['mode']:.2f}, median {TS['median']:.1f}" + r"""\\
Winter section, parking + shared lane + parking & 8.3 & 2.4 + 3.5 + 2.4 (EXP Fig.~6-6)\\
Two-way boulevards & """ + esc(blvd_txt) + r"""\\ \bottomrule\end{tabular}\end{frame}
\begin{frame}{Review: every curb detection on the cross streets}\centering\includegraphics[height=0.86\textheight]{figures/cross_street_widths_review_en.png}\\{\tiny Hillshade of the ground surface along the first block of every cross street, looking away from Terrebonne; red = left curb, blue = right curb; grey ticks = stations dropped. Every block\textquoteright{}s label gives its most frequent reading and the stations kept.}\end{frame}
\begin{frame}{What the cross streets say about the shared lane}\begin{itemize}
""" + DECK_ARG + r"""\item A local cross street is """ + f"{lo:.1f} to {hi:.1f} m curb to curb; with the drawing" + r"""\textquoteright{}s 2.4 m parking bands it leaves """ + f"\\textbf{{{sh_lo:.1f} to {sh_hi:.1f} m}} for the shared lane, against \\textbf{{3.5 m}} on Terrebonne." + r"""
\item Parking on both sides is the rule on every local block (sign inventory); their parking bands are unmarked; snow narrows both streets.
\end{itemize}\end{frame}
"""

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
\begin{frame}{The street in 2023: EXP\textquoteright{}s Figure 3-1}\centering\includegraphics[height=0.6\textheight]{../raw/exp2023_fig3-1_configuration_2023.png}\\{\small 1.8 sidewalk | 2.2 parking | 3.3 | 3.3 | 2.2 parking | 1.8 sidewalk: \textbf{11.0 m curb to curb}; Table 3-1: « Largeur de la chaussée: environ 11 m », « Emprise fonctionnelle: environ 14,6 m ». The LiDAR reads the same 11.0 m.}\\{\tiny Source: EXP, Étude de mobilité sur la rue de Terrebonne, Sept.~2023, report p.~25 (PDF p.~36).}\end{frame}
\begin{frame}{The street today: Aménagement B, built in 2024 (EXP Figure 6-7)}\centering\includegraphics[height=0.6\textheight]{../raw/exp2023_fig6-7_amenagement_B.png}\\{\small 1.8 sidewalk | 1.8 bike lane | 0.5 buffer | 3.5 traffic lane | 2.5 parking | 0.5 buffer | 2.0 bike lane | 1.8 sidewalk: \textbf{10.8 m curb to curb} in the 11.0 m roadway; one-way motor traffic, a protected lane each way.}\\{\tiny Source: EXP 2023, report p.~72 (PDF p.~83). The borough\textquoteright{}s 2024 file describes the built layout as one lane protected by bollards, the other by the remaining parking band.}\end{frame}
\begin{frame}{The winter layout, assumed to be Aménagement A (EXP Figure 6-6)}\centering\includegraphics[height=0.6\textheight]{../raw/exp2023_fig6-6_amenagement_A.png}\\{\small 1.8 | 2.4 parking | 3.5 « chaussée désignée » | 2.4 parking | 0.5 buffer | 2.0 contraflow lane | 1.8: \textbf{10.8 m curb to curb}. Assumption: the Nov.~2 file keeps the contraflow lane and turns the lane running with traffic into parking; applied to B\textquoteright{}s bands that gives 2.3 + 3.5 + 2.5 + 0.5 + 2.0 = 10.8 m, the same arithmetic. No marking plan has been released.}\\{\tiny Source: EXP 2023, report p.~72 (PDF p.~83); borough file 1266880005, Nov.~2, 2026.}\end{frame}
\begin{frame}{The three sections against the measured roadway}\centering\scriptsize\begin{tabular}{lrrl}\toprule Section & bands, curb to curb (m) & total & cyclists ride in\\ \midrule
2023 (Fig.~3-1) & 2.2 + 3.3 + 3.3 + 2.2 & 11.0 & two 3.3 m shared lanes, two-way\\
Today, B (Fig.~6-7) & 1.8 + 0.5 + 3.5 + 2.5 + 0.5 + 2.0 & 10.8 & protected lanes, 1.8 and 2.0 m\\
Winter, A (Fig.~6-6) & 2.4 + 3.5 + 2.4 + 0.5 + 2.0 & 10.8 & a 3.5 m lane shared with traffic; contraflow 2.0 m\\
C (Fig.~6-8), not built & 2.1 + 3.3 + 3.3 + 2.1 & 10.8 & two 3.3 m shared lanes\\
\midrule LiDAR 2015, this note & & \textbf{11.0} & block medians 10.8--11.35 m\\ \bottomrule\end{tabular}\\[8pt]{\small Every EXP section fits the measured roadway with 0 to 0.2 m to spare; none has room for a wider shared lane without narrowing the parking bands, the buffer or the contraflow lane. EXP\textquoteright{}s sidewalks are the paved 1.8 m; the LiDAR\textquoteright{}s zones (4.4 and 4.7 m) run to the parcel line.}\end{frame}
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
note = note.replace(r'\section*{By block}', NOTE_X + '\n' + r'\section*{By block}'); deck = deck.replace(r'\begin{frame}{The figures}', DECK_X + '\n' + r'\begin{frame}{The figures}')
note = note.replace(r'\textbf{Caveats, for this part.}', NOTE_PIC + r'\textbf{Caveats, for this part.}'); deck = deck.replace(r'\begin{frame}{What the cross streets say about the shared lane}\begin{itemize}', DECK_PIC + r'\begin{frame}{What the cross streets say about the shared lane}\begin{itemize}')
for name, src in (('terrebonne_street_width_note_en', note), ('terrebonne_street_width_deck_en', deck)):
    open(os.path.join(HERE, name + '.tex'), 'w', encoding='utf-8').write(src)
    for _ in range(2): subprocess.run(['pdflatex', '-interaction=batchmode', name + '.tex'], cwd=HERE, capture_output=True)
    for e in ('.aux', '.log', '.nav', '.out', '.snm', '.toc'):
        try: os.remove(os.path.join(HERE, name + e))
        except OSError: pass
    print(name, subprocess.run(['pdfinfo', os.path.join(HERE, name + '.pdf')], capture_output=True, text=True).stdout.split('Pages:')[1].split()[0], 'pages')
