#!/usr/bin/env python3
"""The note (A4, pdflatex) and the slide deck (beamer 16:9), English, from derived/numbers.json and derived/tables/. Every figure in the text is
read from the tables at build time.
Usage: ~/.venvs/omd/bin/python scripts/build_docs.py [--final]   (without --final the note carries a DRAFT mark)
Writes docs/corridor_vehicles_curb_note_en.{tex,pdf}, docs/corridor_vehicles_curb_deck_en.{tex,pdf},
docs/deck_figures_en/NN-<figure>.png (each figure of the deck, named by its slide number) and derived/lay_abstract_en.txt."""
import datetime
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DOCS, T = ROOT / "docs", ROOT / "derived" / "tables"
FINAL = "--final" in sys.argv
NOW = datetime.datetime.now()
STAMP, TODAY = NOW.strftime("%Y-%m-%d-%H-%M-%S"), NOW.strftime("%B %-d, %Y")
URL = "https://github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/2026-terrebonne-corridor-vehicles-and-curb"
N = json.load(open(ROOT / "derived" / "numbers.json"))
tab = lambda n, **k: pd.read_csv(T / (n + ".csv"), **k)
C, R, A = N["sets"]["corridor"], N["sets"]["rest"], N["sets"]["all"]
FA, FB = N["fsa"]["H4A"], N["fsa"]["H4B"]
SP = tab("model_specifications"); CO = tab("model_coefficients"); DS = tab("downscaling_summary"); LS = tab("lidar_check_by_sector")
DA = tab("da_corridor", dtype={"dauid": str}); DA = DA[DA.set == "corridor"].sort_values(["west_to_east", "frontage"])
LO = tab("lofo_errors", index_col=0); HC = tab("fsa_households_check", index_col=0)
fleet = ", ".join(LO.index[LO["registered_over_1.5_times_predicted"]])
big = HC[(HC.households >= 1000) & ~HC.index.str.startswith("H7")]
n_ = lambda v, d=0: f"{v:,.{d}f}".replace(",", "{,}")
ds = lambda s, m: DS[(DS.set == s) & (DS.method == m)].iloc[0]
dm, dh = ds("all groups", "model"), ds("all groups", "in proportion to households")
cm, ch = ds("groups without an FSA of the fleet list", "model"), ds("groups without an FSA of the fleet list", "in proportion to households")
pm, ph = ds("H4A and H4B as one group", "model"), ds("H4A and H4B as one group", "in proportion to households")
chosen = SP[SP.chosen].iloc[0]
sg = lambda v, d=1: ("$-$" if v < 0 else "+") + f"{abs(v):.{d}f}"
whole = LS[LS.sector == "whole lane"].iloc[0]
tc = N["terrebonne_curb"]
pct_ban = 100 * C["forbidden_at_all_times_km"] / (C["forbidden_at_all_times_km"] + C["legal_curb_km"])
over = int((DA["automobiles_per_place_5.5m"] > 1).sum())
fig = lambda typ, name, cap, w=1.0: (f"\\begin{{figure}}[H]\\centering\\includegraphics[width={w}\\textwidth]{{../derived/figures/{typ}/{name}_en.png}}"
                                     f"\\caption{{{cap}}}\\end{{figure}}")
DRAFT = "" if FINAL else (r"\begin{center}\colorbox{red!15}{\parbox{0.96\textwidth}{\centering\textbf{\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, "
                          + TODAY + r". Not yet checked line by line; figures may change.}}}}\end{center}")

LAY_WORDS = 300
LAY = f"""How many cars belong to the households along the Terrebonne bike lane, and how much curb is there to park them? Québec's vehicle registry, as released, places each vehicle only in a postal district of about 10,000 households (H4A or H4B), not on a street. This note goes one step finer, and says which parts are measured and which are estimated.

Measured: the curb. Using the City's inventory of parking signs, every side of every block was read for stretches where parking is forbidden at all times. The {C['dissemination_areas']} census areas that touch the lane, reaching about one block to each side, hold {C['legal_curb_km']:.0f} km of legal curb. That is an upper limit: driveways, hydrants and bus stops are not removed.

Estimated: the cars. Census facts about each small area (renters, commuters who drive, household size, income) were used to share out each district's registered automobiles. For the corridor's {n_(C['households']).replace('{,}', ',')} households the estimate is about {round(C['automobiles_modelled'], -2):,} automobiles, between {round(C['low_90'], -2):,} and {round(C['high_90'], -2):,}: {C['per_household']:.2f} per household. For a single small area the estimate is uncertain by about a quarter either way.

The method was tested where the answer is known. Sharing a group of districts' total among its members, it was off by {dm['median_abs_pct']:.0f} per cent at the median, against {dh['median_abs_pct']:.0f} per cent for a simple split by number of households.

At 5.5 m per car, the corridor's legal curb would hold about {round(C['places_5.5m'], -2):,} cars, more than the estimated number registered there. This is not a measure of parking difficulty: it ignores garages and driveways, which about 70 per cent of dwellings on Terrebonne have, as well as visitors, time limits and where on the block a space is. A count of cars seen on a 2015 night agrees with the estimate only in order of magnitude.

The note makes no recommendation."""
n_lay = len(LAY.split()); assert n_lay <= LAY_WORDS, f"lay summary has {n_lay} words, limit {LAY_WORDS}"
(ROOT / "derived" / "lay_abstract_en.txt").write_text("Lay summary\n\n" + LAY + "\n", encoding="utf-8")
print("lay summary:", n_lay, "words")
LAY_TEX = "\n\n".join(q.replace("%", "\\%").replace("'", "\\textquoteright{}") for q in LAY.split("\n\n"))

spec_rows = "\n".join(f"{r.specification}{' (used)' if r.chosen else ''} & {r.median_abs_pct:.1f} & {r.p75_abs_pct:.1f} & {r.p90_abs_pct:.1f} & {sg(r.H4A_pct)} & {sg(r.H4B_pct)} \\\\" for r in SP.itertuples())
coef_rows = "\n".join(f"{r.variable} & {sg(r.coefficient, 3)} & {r.standard_error:.3f} \\\\" for r in CO.itertuples())
da_rows = "\n".join(f"{r.frontage.replace('–', '--')} & {r.main_fsa} & {r.households:.0f} & {r.automobiles_modelled:.0f} & {r.low_90:.0f}--{r.high_90:.0f} & {r.per_household:.2f} & {r.legal_m / 1000:.2f} & {r.legal_m / 5.5:.0f} \\\\" for r in DA.itertuples())
set_rows = "\n".join(f"{lab} & {s['dissemination_areas']} & {n_(s['households'])} & {n_(s['automobiles_modelled'])} & {n_(s['low_90'])}--{n_(s['high_90'])} & {s['per_household']:.2f} & {s['legal_curb_km']:.1f} & {n_(s['places_6.0m'])}--{n_(s['places_5.0m'])} & {s['automobiles_per_place_5.5m']:.2f} \\\\"
                     for lab, s in (("Corridor", C), ("Other areas of H4A, H4B", R), ("All", A)))
lidar_rows = "\n".join(f"{r.sector.capitalize()} & {r.dwellings_addressed_on_terrebonne} & {r.cars_at_curbs_2015_night} & {r.cars_on_lots_2015_night} & {r.cars_seen_per_dwelling:.2f} & {r.modelled_automobiles_per_household:.2f} \\\\" for r in LS.itertuples())

NOTE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}
\usepackage[a4paper,margin=2.2cm]{geometry}\usepackage{graphicx,booktabs,longtable,amsmath,caption,xcolor,enumitem,array,float}\usepackage[hidelinks]{hyperref}
\captionsetup{font=small,labelfont=bf}\setlength{\parskip}{0.55em}\setlength{\parindent}{0pt}\setlist{itemsep=0.25em,topsep=0.3em}\widowpenalty=10000\clubpenalty=10000\raggedbottom
\newcommand{\docversion}{""" + STAMP + r"""}
\begin{document}
{\LARGE\bfseries Automobiles and curb along rue de Terrebonne\par}\vspace{0.3em}
{\large Registered vehicles known by postal district, modelled below it; legal curb measured block face by block face\par}\vspace{0.6em}
Rick Hoge, PhD \hfill """ + TODAY + r""" \hfill version \docversion
""" + DRAFT + r"""
\section*{Lay summary}
""" + LAY_TEX + r"""

""" + fig("overview-map", "overview_map", "Overview. Modelled automobiles and light trucks per household by dissemination area, 2024. The registered totals are known for the two FSAs only; the split among areas is a model.") + r"""

\tableofcontents
\newpage
\section{Question}
The vehicle files the SAAQ released under the access Act for 2023 and 2024 (file 03.06.34729) locate each vehicle to its forward sortation area (FSA, the first three characters of the postal code), and no finer. The protected bike lane on rue de Terrebonne lies in two FSAs: H4B west of avenue Royal, H4A east of it. On December 31, 2024 they held """ + n_(FB["automobiles_inferred"]) + r""" and """ + n_(FA["automobiles_inferred"]) + r""" automobiles and light trucks (type inferred from make, model and model year, as in the note of the repository \emph{Quebec-vehicle-registrations}), that is """ + f"{FB['per_household']:.2f}" + r""" and """ + f"{FA['per_household']:.2f}" + r""" per household of the 2021 Census.

An FSA holds ten to twelve thousand households; the lane's surroundings are a fraction of each. This note asks what can be said at a finer grain, about the dissemination areas that front the lane: how many automobiles are registered there, and how much legal curb they hold. The two halves of the answer are of different kinds, and the note keeps them apart throughout:
\begin{itemize}
\item \textbf{Curb is measured}, block face by block face, from the City\textquoteright{}s géobase and its inventory of parking signs.
\item \textbf{Automobiles below the FSA are modelled}, from 2021 Census variables, and scaled so that the areas of each FSA sum to its registered total. Within an FSA the split is an estimate with an interval, never a count.
\end{itemize}
The 2015 LiDAR and the aerial imagery read for the 1954--55 plans work serve as a check, not as an input. The note makes no recommendation.

\section{Data}
\begin{itemize}
\item \textbf{Vehicles.} SAAQ, files released under the access Act for December 31, 2023 and 2024, by FSA; the table \texttt{type\_by\_fsa.csv} of \emph{Quebec-vehicle-registrations} (type inferred; all automobiles and light trucks, whether registered to a person or to a business: the release carries no class).
\item \textbf{Census.} Statistics Canada, 2021 Census profile by FSA (98-401-X2021013) and by dissemination area (98-401-X2021006), and the dissemination-area boundaries. Counts are randomly rounded to 5 by Statistics Canada; tenure, commuting and income come from the 25\,\% sample.
\item \textbf{Curb.} City of Montréal, géobase (street segments, October 14, 2026) and \emph{Signalisation -- stationnement} (sign inventory, October 23, 2026), both CC BY 4.0.
\item \textbf{Dwellings.} City of Montréal, \emph{Unités d\textquoteright{}évaluation foncière} (assessment roll, CC BY 4.0), used to share a dissemination area that straddles two FSAs and to count the dwellings addressed on rue de Terrebonne; FSA polygons from DMTI Spatial, CanMap Postal Code Suite v2024.3 (under licence, not redistributed).
\item \textbf{Checks.} The cars counted by eye on the City\textquoteright{}s 2015 night LiDAR and the garage and driveway readings, from the folder \emph{1954-underwriters-plans-terrebonne-garages}; the parking counts of the borough\textquoteright{}s 2023 study (EXP), as transcribed in \emph{2026-parking-supply-demand-survey-context}.
\end{itemize}

\section{Method}
\subsection{Dissemination areas and FSAs}
Dissemination areas do not nest in FSAs. Each area is shared among FSAs in proportion to the dwellings of the assessment roll found in each FSA polygon. Rebuilt this way from dissemination areas, the households of the island\textquoteright{}s """ + str(len(big)) + r""" FSAs of 1{,}000 households or more differ from Statistics Canada\textquoteright{}s own FSA profile by """ + f"{big.households_pct_difference.abs().median():.1f}" + r"""\,\% at the median (H4A """ + sg(FA["households_from_da_pct"]) + r"""\,\%, H4B """ + sg(FB["households_from_da_pct"]) + r"""\,\%). """ + str(A["dissemination_areas"]) + r""" areas have a part in H4A or H4B.

\subsection{The corridor}
The corridor is the set of """ + str(C["dissemination_areas"]) + r""" dissemination areas that hold a block face of rue de Terrebonne along the lane, from its west end to Girouard. They reach about one block to each side (Somerled is about 260\,m north of the lane, Monkland about 285\,m south); """ + str(int((DA.share_within_300m >= 0.9).sum())) + r""" of them have nine-tenths or more of their surface within 300\,m of the lane (the others are the larger areas toward the west end, the smallest share being """ + f"{100 * DA.share_within_300m.min():.0f}" + r"""\,\%), and no area outside the set has half its surface within that distance.

\subsection{Legal curb}
A block face is one side of one géobase segment (autoroutes, bridges, tunnels and back lanes left out). Its legal curb is its length, less 5\,m at each end (an assumption for intersections), less the stretches where a sign forbids stopping or parking at all times («\,\textbackslash A EN TOUT TEMPS\,», «\,\textbackslash P EN TOUT TEMPS\,»). The stretch a sign governs runs from its pole to the next pole in the direction of its arrow; a sign without an arrow governs the stretches on both sides of its pole. Where the usual reading of the arrows leaves a stretch claimed both by an all-time prohibition and by another parking rule (hours, days, a time limit: a rule that implies parking exists there), the other reading is taken for that face if it leaves fewer such stretches; a stretch still claimed both ways counts for half.

The result is an \textbf{upper bound} on legal curb: driveways, hydrants, bus stops, hourly rules, permit zones and seasonal rules are not deducted. Places are legal curb divided by 5, 5.5 and 6\,m.

\textbf{Check on rue de Terrebonne}, where the layout is known: the reading finds parking on the south side west of Cavendish and on the north side east of it, one band, as built in 2024: """ + n_(N["terrebonne_legal_m"]) + r"""\,m of legal curb, """ + str(N["terrebonne_places_5.5m"]) + r""" places at 5.5\,m. The borough\textquoteright{}s 2023 study counted 478 places on the two sides before the lane (report p.~40): 230 westbound and 248 eastbound.

\subsection{Automobiles below the FSA}
\begin{enumerate}
\item Across the """ + str(N["model"]["fsas"]) + r""" FSAs beginning with H that hold 1{,}000 households or more, the logarithm of automobiles per household is regressed on four census variables: the share of renter households, the share of commuters who drive, persons per household, and the logarithm of the median household income. The regression is robust (Huber weights), because a few FSAs hold fleets registered to businesses (""" + fleet + r""": registered counts more than 1.5 times what their census variables predict).
\item The rate of each dissemination area is predicted from its own census variables.
\item The predictions are scaled so that the parts of the areas lying in each FSA sum to that FSA\textquoteright{}s registered total. The scale factors of H4A and H4B are """ + f"{FA['scale_factor']:.2f} and {FB['scale_factor']:.2f}" + r""".
\end{enumerate}
Specifications were compared by leaving each FSA out in turn (Table~\ref{tab:spec}); the one used has the smallest error at the 90th percentile and close to the smallest at the median. Dwelling type adds nothing once tenure, commuting and household size are in.

\textbf{Intervals} come from 2{,}000 draws, each combining: the FSAs resampled and the model refitted; the sampling error of the 25\,\% sample variables in each dissemination area; an unexplained factor for each area, whose spread is the one measured by the downscaling test below; and the scaling to the FSA totals. Dissemination areas are about twenty times smaller than FSAs, and their true unexplained spread may be larger than the one measured among FSAs: the tables also carry intervals with that spread doubled, which are wider by a few points only, because the sampling error of the census variables dominates. The intervals do not cover what the model cannot see: the vehicles are those of December 31, 2024 and the census is of May 2021; the type is inferred; vehicles registered to businesses are in the totals.

\section{Results}
\subsection{Does the model work where the answer is known?}
Two tests, both at the level of FSAs, the only level at which registered counts exist.

\emph{Each FSA left out in turn.} The model fitted on the other FSAs predicts the left-out FSA\textquoteright{}s rate within """ + f"{chosen.median_abs_pct:.1f}" + r"""\,\% at the median (""" + f"{chosen.p90_abs_pct:.0f}" + r"""\,\% at the 90th percentile, the business FSAs included). H4A is under-predicted by """ + f"{abs(chosen.H4A_pct):.0f}" + r"""\,\%, H4B by """ + f"{abs(chosen.H4B_pct):.1f}" + r"""\,\%.

\emph{Downscaling, one level up.} Neighbouring FSAs were grouped by threes (""" + str(int(dm["groups"])) + r""" groups, """ + str(int(dm["fsas"])) + r""" FSAs); for each group the model was fitted without its members, and the group\textquoteright{}s registered total was shared among them by the model. This is the operation the note performs below the FSA, done where it can be checked. The share of each FSA is off by """ + f"{dm['median_abs_pct']:.1f}" + r"""\,\% at the median (""" + f"{dm['p90_abs_pct']:.0f}" + r"""\,\% at the 90th percentile); sharing in proportion to households is off by """ + f"{dh['median_abs_pct']:.1f}" + r"""\,\% (""" + f"{dh['p90_abs_pct']:.0f}" + r"""\,\%). Without the groups that hold a business FSA: """ + f"{cm['median_abs_pct']:.1f}" + r"""\,\% against """ + f"{ch['median_abs_pct']:.1f}" + r"""\,\%. For H4A and H4B taken as one group, the model\textquoteright{}s shares are off by """ + sg(pm["H4A_pct"]) + r"""\,\% and """ + sg(pm["H4B_pct"]) + r"""\,\%, the household split by """ + sg(ph["H4A_pct"]) + r"""\,\% and """ + sg(ph["H4B_pct"]) + r"""\,\%: for this pair the model gains little.

""" + fig("model-tests", "model_tests", "The two tests. Left: each FSA\\textquoteright{}s rate predicted without it (hollow: FSAs with fleets). Right: error of each FSA\\textquoteright{}s share of its group\\textquoteright{}s total; errors above 80\\,\\% drawn at 80.") + r"""

The tests say the model shares a total among FSAs better than households alone do. They cannot say how well it shares an FSA among its dissemination areas: no registered count exists at that level.

\subsection{The corridor}
\begin{table}[H]\centering\small
\caption{Modelled automobiles and measured legal curb. Interval: 90\,\%. Places: legal curb at 6\,m to 5\,m per vehicle (upper bound). Last column: modelled automobiles per place at 5.5\,m.}\label{tab:sets}
\footnotesize\setlength{\tabcolsep}{4pt}\begin{tabular}{@{}p{3.3cm}rrrrrrrr@{}}\toprule
 & areas & hh. & autos & interval & per hh. & curb km & places & per place \\\midrule
""" + set_rows + r"""
\bottomrule\end{tabular}\end{table}
The corridor\textquoteright{}s """ + n_(C["households"]) + r""" households are estimated to have """ + n_(C["automobiles_modelled"]) + r""" automobiles and light trucks registered (""" + n_(C["low_90"]) + r""" to """ + n_(C["high_90"]) + r"""), """ + f"{C['per_household']:.2f}" + r""" per household (""" + f"{C['per_household_low_90']:.2f} to {C['per_household_high_90']:.2f}" + r"""); the other areas of the two FSAs, """ + f"{R['per_household']:.2f}" + r""". The two alternative specifications give """ + n_(C["alt_3_variables"]) + r""" and """ + n_(C["alt_6_variables"]) + r""" for the corridor. Area by area the estimates run from """ + f"{DA.per_household.min():.2f} to {DA.per_household.max():.2f}" + r""" per household, and the 90\,\% interval of a single area is about """ + f"{100 * ((DA.high_90 - DA.low_90) / 2 / DA.automobiles_modelled).median():.0f}" + r"""\,\% of its estimate either way (Figure~\ref{fig:areas}, Table~\ref{tab:da}). The differences between neighbouring areas are mostly within those intervals.

\begin{figure}[H]\centering\includegraphics[width=\textwidth]{../derived/figures/area-estimates/area_estimates_en.png}\caption{Modelled automobiles per household, the corridor\textquoteright{}s areas from west to east.}\label{fig:areas}\end{figure}

\subsection{Legal curb}
The corridor holds """ + f"{C['curb_km']:.1f}" + r"""\,km of curb; net of 5\,m at each end of each face, """ + f"{pct_ban:.0f}" + r"""\,\% is forbidden at all times, leaving """ + f"{C['legal_curb_km']:.1f}" + r"""\,km of legal curb: """ + n_(C["places_6.0m"]) + r""" to """ + n_(C["places_5.0m"]) + r""" places at 6 to 5\,m, an upper bound. That is """ + f"{C['legal_curb_m_per_household']:.1f}" + r"""\,m of legal curb per household (""" + f"{R['legal_curb_m_per_household']:.1f}" + r"""\,m in the other areas of the two FSAs).

""" + fig("curb-map", "curb_map", "Block faces of the corridor. A face is drawn orange when all-time prohibitions cover half of it or more.", 0.92) + r"""

\subsection{Automobiles beside curb}
At 5.5\,m per place the corridor has """ + f"{C['automobiles_per_place_5.5m']:.2f}" + r""" modelled automobile per place of legal curb (""" + f"{C['automobiles_per_place_low_90']:.2f} to {C['automobiles_per_place_high_90']:.2f}" + r"""); in """ + str(over) + r""" of the """ + str(len(DA)) + r""" areas the estimate exceeds the area\textquoteright{}s own places (Figure~\ref{fig:both}).

\textbf{This ratio is not a measure of parking pressure, in either direction.} The curb figure is an upper bound (no driveway, hydrant or bus stop deducted, no hourly or permit rule). The automobile figure is every vehicle registered, wherever it is kept: off-street parking is in neither term, and on rue de Terrebonne itself 70\,\% of dwellings are in a building with a garage as built or a driveway today (188 of 268; \emph{1954-underwriters-plans-terrebonne-garages}). Visitors, institutions and vehicles from elsewhere use the same curb; a place at the far end of an area is not a place at one\textquoteright{}s door. The measurements of occupancy that exist are those of the borough\textquoteright{}s 2023 study: on Thursday, September 29, 2022, at 18:30--19:30, 247 cars on rue de Terrebonne\textquoteright{}s places (50\,\%) and 311 on the cross-street stubs (51\,\%) (EXP, Tables 3-2 and 3-3, as transcribed in \emph{2026-parking-supply-demand-survey-context}).

\begin{figure}[H]\centering\includegraphics[width=\textwidth]{../derived/figures/curb-and-automobiles/curb_and_automobiles_en.png}\caption{Modelled automobiles and the places the legal curb would hold, by area.}\label{fig:both}\end{figure}

\subsection{A check from the 2015 LiDAR night}
The City\textquoteright{}s 2015 LiDAR was flown at night. Counted by eye along rue de Terrebonne: """ + str(int(whole.cars_at_curbs_2015_night)) + r""" cars at the curbs and """ + str(int(whole.cars_on_lots_2015_night)) + r""" on the lots along the street, """ + str(int(whole.cars_at_curbs_2015_night + whole.cars_on_lots_2015_night)) + r""" for the """ + str(int(whole.dwellings_addressed_on_terrebonne)) + r""" dwellings addressed on the street: """ + f"{whole.cars_seen_per_dwelling:.2f}" + r""" per dwelling. The model gives """ + f"{whole.modelled_automobiles_per_household:.2f}" + r""" per household for the areas that hold those dwellings.
\begin{table}[H]\centering\small
\caption{Cars seen on the 2015 LiDAR night along rue de Terrebonne, and the model, by sector of the 2023 study.}
\begin{tabular}{@{}lrrrrr@{}}\toprule
Sector & dwellings & at curbs & on lots & seen per dwelling & modelled per household \\\midrule
""" + lidar_rows + r"""
\bottomrule\end{tabular}\end{table}
The two quantities are not the same: the LiDAR sees visitors\textquoteright{} cars and the lots of churches, schools and corner buildings addressed on the cross streets, and does not see cars inside garages or away for the night; nine years separate the two. They agree in order of magnitude. They do not agree in detail: across the """ + str(N["lidar"]["areas"]) + r""" areas with ten dwellings or more on Terrebonne, the rank correlation between cars seen per dwelling and the modelled rate is """ + f"{N['lidar']['rho_rate']:.2f}" + r""" ($p$ = """ + f"{N['lidar']['p_rate']:.2f}" + r"""), not distinguishable from none. The check therefore supports the level of the estimate, not the split between areas.

""" + fig("lidar-check", "lidar_check", "Cars seen per dwelling on the 2015 night and the model\\textquoteright{}s rate, by sector.", 0.9) + r"""

\section{What the note shows and does not show}
\begin{itemize}
\item \textbf{Measured:} the registered automobiles of H4A and H4B (type inferred); the legal curb of each block face, as an upper bound; the dwellings and, on rue de Terrebonne, the garages and driveways.
\item \textbf{Modelled:} the automobiles of every area smaller than an FSA. The model shares a known total better than households alone at the one level where this can be tested; below the FSA nothing can test it, and the 2015 check does not confirm its area-by-area differences.
\item \textbf{Not measured by anyone:} off-street places beyond rue de Terrebonne; where registered vehicles are kept; occupancy of the curb since the lane was built.
\item The curb reading rests on the sign inventory as published on October 23, 2026 and on rules for arrows that were checked on rue de Terrebonne only.
\end{itemize}

\section{Reproducibility}
Scripts, tables and figures: \url{""" + URL + r"""}. Order: \texttt{build\_dataset.py}, \texttt{curb\_supply.py}, \texttt{demand\_model.py}, \texttt{corridor.py}, the figure scripts under \texttt{derived/figures/}, \texttt{build\_docs.py}. The census, roll, sign and postal-code files are read from outside the repository (sources and dates in the folder\textquoteright{}s README); the tables by dissemination area and by block face are in \texttt{derived/tables/}.

\appendix
\section{Tables}
\begin{table}[H]\centering\small
\caption{Specifications compared, each FSA left out in turn: absolute error of the predicted rate (\%), and the signed error for H4A and H4B.}\label{tab:spec}
\begin{tabular}{@{}p{7.4cm}rrrrr@{}}\toprule
Variables & median & 75th & 90th & H4A & H4B \\\midrule
""" + spec_rows + r"""
\bottomrule\end{tabular}\end{table}
\begin{table}[H]\centering\small
\caption{Coefficients of the model used (logarithm of automobiles per household; robust regression, """ + str(N["model"]["fsas"]) + r""" FSAs).}
\begin{tabular}{@{}lrr@{}}\toprule
Variable & coefficient & standard error \\\midrule
""" + coef_rows + r"""
\bottomrule\end{tabular}\end{table}
{\small
\begin{longtable}{@{}p{5.6cm}lrrrrrr@{}}
\caption{The corridor\textquoteright{}s dissemination areas, west to east. N, S: side of rue de Terrebonne and the cross streets the frontage runs between. Automobiles: modelled, with 90\,\% interval. Places: legal curb at 5.5\,m (upper bound).}\label{tab:da}\\\toprule
Frontage on Terrebonne & FSA & hh. & autos & interval & per hh. & curb km & places \\\midrule\endhead
""" + da_rows + r"""
\bottomrule\end{longtable}}
\end{document}
"""
# ---------------------------------------------------------------- the slide deck (beamer, 16:9)
fr = lambda title, body: "\\begin{frame}{" + title + "}\n" + body + "\n\\end{frame}\n"
ffig = lambda title, typ, name, text="", h=0.66: fr(title, f"\\begin{{center}}\\includegraphics[height={h}\\textheight]{{../derived/figures/{typ}/{name}_en.png}}\\end{{center}}" + (f"\n{{\\footnotesize {text}}}" if text else ""))
DMARK = "" if FINAL else r"\setbeamertemplate{footline}{\hfill{\tiny\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, " + TODAY + r"}\quad\insertframenumber}\hspace{1em}\vspace{0.4em}}"
half = 100 * ((DA.high_90 - DA.low_90) / 2 / DA.automobiles_modelled).median()
DECK = r"""\documentclass[aspectratio=169,10pt]{beamer}\usetheme{default}\usecolortheme{seahorse}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}[frame number]
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{helvet}\usepackage{booktabs,amsmath}
""" + DMARK + r"""
\title{Automobiles and curb along rue de Terrebonne}\subtitle{Registered vehicles known by postal district, modelled below it; legal curb measured block face by block face}\author{Rick Hoge, PhD}\institute{Terrebonne-open-sources}\date{""" + TODAY + r"""}
\begin{document}
\begin{frame}\titlepage\end{frame}
""" + ffig("Overview", "overview-map", "overview_map", "Registered totals are known for H4A and H4B only. The split among dissemination areas is a model.", 0.74) + fr("The question", r"""\begin{itemize}
\item The SAAQ files released under the access Act for 2023 and 2024 locate each vehicle to its \textbf{FSA} (first three characters of the postal code), and no finer.
\item The lane lies in two FSAs: \textbf{H4B} west of Royal (""" + n_(FB["automobiles_inferred"]) + r""" automobiles and light trucks, """ + f"{FB['per_household']:.2f}" + r""" per household) and \textbf{H4A} east of it (""" + n_(FA["automobiles_inferred"]) + r""", """ + f"{FA['per_household']:.2f}" + r"""). Type inferred; December 31, 2024.
\item An FSA holds ten to twelve thousand households. What can be said about the areas that front the lane: how many automobiles are registered there, and how much legal curb do they hold?
\item The note makes no recommendation.
\end{itemize}""") + fr("Two kinds of figures, kept apart", r"""\begin{columns}[T]
\begin{column}{0.47\textwidth}\textbf{Measured: the curb}
\begin{itemize}\small
\item City géobase and parking-sign inventory (October 2026)
\item Every side of every street segment
\item Less 5\,m at each end, less stretches forbidden at all times
\item An \textbf{upper bound}: driveways, hydrants, bus stops, hourly and permit rules not deducted
\end{itemize}\end{column}
\begin{column}{0.47\textwidth}\textbf{Modelled: the automobiles}
\begin{itemize}\small
\item Registered totals exist by FSA only
\item Shared among dissemination areas from 2021 Census variables
\item Scaled so each FSA\textquoteright{}s areas sum to its registered total
\item An \textbf{estimate with an interval}, never a count
\end{itemize}\end{column}\end{columns}
\vspace{1em}The 2015 LiDAR night count and the imagery are a \textbf{check}, not an input.""") + fr("The corridor", r"""\begin{itemize}
\item The """ + str(C["dissemination_areas"]) + r""" dissemination areas that hold a block face of rue de Terrebonne along the lane, west end to Girouard.
\item They reach about one block to each side (Somerled about 260\,m north, Monkland about 285\,m south).
\item """ + n_(C["households"]) + r""" households (2021 Census).
\item Dissemination areas do not nest in FSAs: each is shared among FSAs by the dwellings of the City\textquoteright{}s assessment roll in each FSA polygon. Households rebuilt this way: H4A """ + sg(FA["households_from_da_pct"]) + r"""\,\%, H4B """ + sg(FB["households_from_da_pct"]) + r"""\,\% against Statistics Canada\textquoteright{}s own FSA profile.
\end{itemize}""") + fr("Method: legal curb", r"""\begin{itemize}
\item A sign governs the stretch from its pole to the next pole in the direction of its arrow; a sign without an arrow, the stretches on both sides.
\item Where the usual reading of the arrows leaves a stretch claimed both by an all-time prohibition and by an hourly rule, the other reading is taken for that face if it leaves fewer such stretches.
\item \textbf{Check on rue de Terrebonne}, where the layout is known: the reading finds one parking band, south side west of Cavendish, north side east of it: """ + n_(N["terrebonne_legal_m"]) + r"""\,m, """ + str(N["terrebonne_places_5.5m"]) + r""" places at 5.5\,m.
\item The borough\textquoteright{}s 2023 study counted 478 places on the two sides before the lane (230 westbound, 248 eastbound).
\end{itemize}""") + ffig("Legal curb by block face", "curb-map", "curb_map", f"Corridor: {C['curb_km']:.1f} km of curb, {C['legal_curb_km']:.1f} km legal; {n_(C['places_6.0m'])} to {n_(C['places_5.0m'])} places at 6 to 5 m (upper bound).", 0.7) + fr("Method: automobiles below the FSA", r"""\begin{enumerate}
\item Across """ + str(N["model"]["fsas"]) + r""" FSAs (1{,}000 households or more), the logarithm of automobiles per household is regressed on: share of renters, share of commuters who drive, persons per household, median household income. Robust regression: a few FSAs hold business fleets (""" + fleet + r""").
\item Each dissemination area\textquoteright{}s rate is predicted from its own census variables.
\item Predictions are scaled so each FSA\textquoteright{}s areas sum to its registered total (factors """ + f"{FA['scale_factor']:.2f} for H4A, {FB['scale_factor']:.2f} for H4B" + r""").
\end{enumerate}
\textbf{Intervals}: 2{,}000 draws (FSAs resampled; sampling error of the 25\,\% sample variables; an unexplained factor per area; rescaling).

Not covered by the intervals: census of 2021 against vehicles of 2024; inferred type; vehicles registered to businesses.""") + ffig("Does the model work where the answer is known?", "model-tests", "model_tests", f"Sharing a group of FSAs\\textquoteright{{}} total among its members: off by {dm['median_abs_pct']:.1f}\\,\\% at the median with the model, {dh['median_abs_pct']:.1f}\\,\\% in proportion to households. For H4A and H4B as a pair the model gains little. Below the FSA nothing can test the split.", 0.6) + fr("The corridor: modelled automobiles, measured curb", r"""\begin{center}\resizebox{0.98\textwidth}{!}{\begin{tabular}{lrrrrrrrr}\toprule
 & areas & households & automobiles & 90\,\% interval & per household & legal curb km & places (6 to 5\,m) & per place (5.5\,m) \\\midrule
""" + set_rows + r"""
\bottomrule\end{tabular}}\end{center}
\begin{itemize}
\item Corridor: """ + f"{C['per_household']:.2f}" + r""" automobile per household (""" + f"{C['per_household_low_90']:.2f} to {C['per_household_high_90']:.2f}" + r"""); the other areas of the two FSAs, """ + f"{R['per_household']:.2f}" + r""".
\item The two alternative specifications give """ + n_(C["alt_3_variables"]) + r""" and """ + n_(C["alt_6_variables"]) + r""" for the corridor.
\item Places are an upper bound; automobiles are every vehicle registered, wherever it is kept.
\end{itemize}""") + ffig("Area by area: the estimates and their intervals", "area-estimates", "area_estimates", f"A single area\\textquoteright{{}}s 90\\,\\% interval is about {half:.0f}\\,\\% of its estimate either way; most differences between neighbours are within it.", 0.7) + ffig("Modelled automobiles beside the places the legal curb would hold", "curb-and-automobiles", "curb_and_automobiles", "", 0.76) + fr("Why the ratio is not a measure of parking pressure", r"""\begin{itemize}
\item At 5.5\,m per place: """ + f"{C['automobiles_per_place_5.5m']:.2f}" + r""" modelled automobile per place of legal curb in the corridor (""" + f"{C['automobiles_per_place_low_90']:.2f} to {C['automobiles_per_place_high_90']:.2f}" + r"""); the estimate exceeds the area\textquoteright{}s own places in """ + str(over) + r""" of """ + str(len(DA)) + r""" areas.
\item The curb figure is an \textbf{upper bound}: no driveway, hydrant, bus stop, hourly or permit rule deducted.
\item \textbf{Off-street parking is in neither term.} On rue de Terrebonne, 70\,\% of dwellings are in a building with a garage as built or a driveway today (188 of 268).
\item Visitors, institutions and vehicles from elsewhere use the same curb; a place at the far end of an area is not a place at one\textquoteright{}s door.
\item The occupancy measurements that exist are EXP\textquoteright{}s: Thursday, September 29, 2022, 18:30--19:30: 247 cars on Terrebonne\textquoteright{}s places (50\,\%), 311 on the cross-street stubs (51\,\%).
\end{itemize}""") + ffig("A check from another source: the 2015 LiDAR night", "lidar-check", "lidar_check", f"{int(whole.cars_at_curbs_2015_night + whole.cars_on_lots_2015_night)} cars seen for {int(whole.dwellings_addressed_on_terrebonne)} dwellings addressed on Terrebonne. Agreement in order of magnitude; area by area, no relation (rank correlation {N['lidar']['rho_rate']:.2f}, {N['lidar']['areas']} areas).", 0.6) + fr("What is shown and what is not", r"""\begin{itemize}
\item \textbf{Measured:} the registered automobiles of H4A and H4B (type inferred); the legal curb of each block face, as an upper bound; garages and driveways on rue de Terrebonne.
\item \textbf{Modelled:} the automobiles of every area smaller than an FSA. The model shares a known total better than households alone where that can be tested; below the FSA nothing can test it, and the 2015 check does not confirm its area-by-area differences.
\item \textbf{Not measured by anyone:} off-street places beyond rue de Terrebonne; where registered vehicles are kept; occupancy of the curb since the lane was built.
\end{itemize}""") + fr("Where everything is", r"""\begin{itemize}
\item Note, tables by dissemination area and by block face, figures (English and French) and scripts: \url{""" + URL + r"""}
\item Sources: SAAQ (access request 03.06.34729; tables of Quebec-vehicle-registrations); Statistics Canada, 2021 Census; City of Montréal open data (géobase, parking-sign inventory, assessment roll, LiDAR 2015; CC BY 4.0); DMTI Spatial (FSA polygons, under licence).
\end{itemize}""") + r"""
\end{document}
"""
import glob, os, re, shutil
FIGDIR = DOCS / "deck_figures_en"; FIGDIR.mkdir(exist_ok=True)
for old in FIGDIR.glob("*.png"):
    old.unlink()
for n, frame in enumerate(DECK.split("\\begin{frame}")[1:], 1):
    for m in re.finditer(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", frame):
        src = (DOCS / m.group(1)).resolve()
        shutil.copyfile(src, FIGDIR / f"{n:02d}-{src.name.replace('_en.png', '.png').replace('_', '-')}")
dk = DOCS / "corridor_vehicles_curb_deck_en.tex"
dk.write_text(DECK, encoding="utf-8")
for _ in range(2):
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", dk.name], cwd=DOCS, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2500:]); sys.exit(1)
for ext in ("aux", "log", "out", "toc", "nav", "snm"):
    (DOCS / f"corridor_vehicles_curb_deck_en.{ext}").unlink(missing_ok=True)
print("OK deck")
DOCS.mkdir(exist_ok=True)
tex = DOCS / "corridor_vehicles_curb_note_en.tex"
tex.write_text(NOTE, encoding="utf-8")
for _ in range(3):
    r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name], cwd=DOCS, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout[-2500:]); sys.exit(1)
for ext in ("aux", "log", "out", "toc"):
    (DOCS / f"corridor_vehicles_curb_note_en.{ext}").unlink(missing_ok=True)
print("OK build_docs", STAMP, "final" if FINAL else "draft")
