#!/usr/bin/env python3
"""The note (A4, pdflatex) and the slide deck (beamer 16:9), English, from derived/numbers.json and derived/tables/. Every figure in the text is
read from the tables at build time.
Usage: ~/.venvs/omd/bin/python scripts/build_docs.py [--final]   (without --final the note carries a DRAFT mark; with it, « Preliminary results, not peer reviewed »)
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
over = int((DA.automobiles_modelled > DA.legal_m / 5.5).sum())
OF = json.load(open(ROOT / "derived" / "offstreet.json")); OM, OS, OW, OK = OF["measured"], OF["corridor"], OF["measured"]["whole_lane"], OF["check"]
_m = pd.read_csv(ROOT / "derived" / "tables" / "offstreet_measured_by_da.csv", dtype={"dauid": str}).sort_values(["west_to_east", "frontage"]).reset_index(drop=True)
_m["no"] = range(1, len(_m) + 1); _c = _m.legal_m / 5.5
_rA = _m.automobiles_modelled / (_c + _m.private_independent); _rB = _m.automobiles_modelled / _c; _ls = (_m.dwellings_in_large_buildings / _m.households).clip(upper=1)
_n = lambda r: (int((r < 0.8).sum()), int(((r >= 0.8) & (r <= 1.0)).sum()), int((r > 1.0).sum()))
STAT = {k: "{} green, {} yellow, {} red".format(*_n(r)) for k, r in (("A", _rA), ("B", _rB))}
STAT["red_A"] = "; ".join(f"area {int(n)}, {100 * l:.0f}\\,\\%" for n, l in zip(_m.no[_rA > 1.0], _ls[_rA > 1.0]))
# ---------------- snow-loading nights (scripts/snow_loading.py)
SL = json.load(open(ROOT / "derived" / "snow_loading.json")); SA = tab("snow_loading_areas", dtype={"dauid": str}).sort_values("no")
_w = [x[:5].replace("-", "--") + x[-2:] for x in SL["winters"]]
_ops = lambda sec: ", ".join(str(SL["operations_per_winter"][s].get(sec, 0)) for s in SL["winters"][1:])
_lst = lambda d: ", ".join(str(v) for v in d.values()).rsplit(", ", 1)
_and = lambda d: " and ".join(_lst(d))
SQ = {q: SL["area_scale"][f"q{q}"] for q in (25, 50, 100)}
_q50w = SA[(SA.share_q50_with_private > 1) & (SA.share_ordinary_with_private <= 1)]
_already = SA[SA.share_ordinary_with_private > 1]
SNOW_NIGHTS = f"{_q50w.nights_per_winter_q50_with_private.mean():.1f}"
SLD, SLN = SL["district_scale"]["Loyola"], SL["district_scale"]["Notre-Dame-de-Grâce"]
SENS = SL["district_sensitivity_operation_min"]
_ops301 = " and ".join(", ".join(str(SL["operations_per_winter"][s]["CDN-301"]) for s in SL["winters"]).rsplit(", ", 1))
_maxban = 100 * max(max(SLD["max_share_of_curb_under_ban"].values()), max(SLN["max_share_of_curb_under_ban"].values()))
_lot = next(v[0] for v in SL["free_lot"].values() if v)
_lotw = [k[:5].replace("-", "--") + k[-2:] for k, v in SL["free_lot"].items() if v]
fig = lambda typ, name, cap, w=1.0: (f"\\begin{{figure}}[H]\\centering\\includegraphics[width={w}\\textwidth]{{../derived/figures/{typ}/{name}_en.png}}"
                                     f"\\caption{{{cap}}}\\end{{figure}}")
PRELIM = (r"\begin{center}\colorbox{black!6}{\parbox{0.96\textwidth}{\centering\textbf{Preliminary results, not peer reviewed} (version " + TODAY + r").}}\end{center}")   # owner, Nov 12, 2026: a stable document carries this instead of the draft mark
DRAFT = PRELIM if FINAL else (r"\begin{center}\colorbox{red!15}{\parbox{0.96\textwidth}{\centering\textbf{\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, "
                          + TODAY + r". Not yet checked line by line; figures may change.}}}}\end{center}")

LAY_WORDS = 300
LAY = f"""How many cars belong to the households along the Terrebonne bike lane, and how much curb is there to park them? Québec's vehicle registry, as released, places each vehicle only in a postal district of about 10,000 households (H4A or H4B), not on a street. This note looks closer, and says which parts are measured and which estimated.

Measured: the curb. Using the City's inventory of parking signs, every side of every block was read for stretches where parking is always forbidden. The {C['dissemination_areas']} census areas that touch the lane, reaching about one block to each side, hold {C['legal_curb_km']:.0f} km of legal curb. That is an upper limit: driveways and hydrants are not removed.

Estimated: the cars. Census facts about each small area (renters, commuters who drive, household size, income) were used to share out each district's registered automobiles. For the corridor's {n_(C['households']).replace('{,}', ',')} households the estimate is about {round(C['automobiles_modelled'], -2):,} automobiles, between {round(C['low_90'], -2):,} and {round(C['high_90'], -2):,}: {C['per_household']:.2f} per household. For a single small area the estimate is uncertain by about a quarter either way.

Tested where the answer is known (sharing a group of districts' total among its members), the method was off by {dm['median_abs_pct']:.0f} per cent at the median, against {dh['median_abs_pct']:.0f} per cent for a split by number of households.

At 5.5 m per car, the corridor's legal curb would hold about {round(C['places_5.5m'], -2):,} cars: more than the estimated number registered there, even if all were kept on the street. Every lot was examined on aerial photos and a random sample of {OK['small_judged'] + OK['small_cannot_tell'] + OK['large_sampled']} checked from the street: {OK['small_yes']} of {OK['small_judged']} small buildings have a driveway, pad or garage. That makes about {round(OS['private_independent'], -2):,} private places, garage interiors and apartment buildings not counted. Neither figure measures parking difficulty: visitors, time limits and distance to one's door are left out.

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
A block face is one side of one géobase segment (autoroutes, bridges, tunnels and back lanes left out). A segment runs from the centre of one intersection to the centre of the next. A face\textquoteright{}s legal curb is its length, less 10\,m at each end, less the stretches where a sign forbids stopping or parking at all times («\,\textbackslash A EN TOUT TEMPS\,», «\,\textbackslash P EN TOUT TEMPS\,»). The stretch a sign governs runs from its pole to the next pole in the direction of its arrow; a sign without an arrow governs the stretches on both sides of its pole. Where the usual reading of the arrows leaves a stretch claimed both by an all-time prohibition and by another parking rule (hours, days, a time limit: a rule that implies parking exists there), the other reading is taken for that face if it leaves fewer such stretches; a stretch still claimed both ways counts for half.

The 10\,m at each end is the half roadway of the cross street (5\,m, an assumption: the local cross streets measure 9.0 to 9.4\,m from curb to curb on the 2015 LiDAR, rue de Terrebonne 11.0\,m) plus the 5\,m next to an intersection where the Highway Safety Code forbids stopping, signed or not (art.~386, par.~4).

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
The corridor holds """ + f"{C['curb_km']:.1f}" + r"""\,km of curb; net of 10\,m at each end of each face, """ + f"{pct_ban:.0f}" + r"""\,\% is forbidden at all times, leaving """ + f"{C['legal_curb_km']:.1f}" + r"""\,km of legal curb: """ + n_(C["places_6.0m"]) + r""" to """ + n_(C["places_5.0m"]) + r""" places at 6 to 5\,m, an upper bound. That is """ + f"{C['legal_curb_m_per_household']:.1f}" + r"""\,m of legal curb per household (""" + f"{R['legal_curb_m_per_household']:.1f}" + r"""\,m in the other areas of the two FSAs).

""" + fig("curb-map", "curb_map", "Block faces of the corridor. A face is drawn orange when all-time prohibitions cover half of it or more.", 0.92) + r"""

\subsection{Automobiles beside curb: if every vehicle were kept on the street}
At 5.5\,m per place the corridor has """ + f"{C['automobiles_per_place_5.5m']:.2f}" + r""" modelled automobile per place of legal curb (""" + f"{C['automobiles_per_place_low_90']:.2f} to {C['automobiles_per_place_high_90']:.2f}" + r"""); in """ + str(over) + r""" of the """ + str(len(DA)) + r""" areas the estimate exceeds the area\textquoteright{}s own places (Figure~\ref{fig:both}).

This comparison is the limiting case in which every registered vehicle is kept at the curb and no private place is used. Private parking is taken up in the next section.

\textbf{The ratio is not a measure of parking pressure, in either direction.} The curb figure is an upper bound (no driveway, hydrant or bus stop deducted, no hourly or permit rule). The automobile figure is every vehicle registered, wherever it is kept. Visitors, institutions and vehicles from elsewhere use the same curb; a place at the far end of an area is not a place at one\textquoteright{}s door. The measurements of occupancy that exist are those of the borough\textquoteright{}s 2023 study: on Thursday, September 29, 2022, at 18:30--19:30, 247 cars on rue de Terrebonne\textquoteright{}s places (50\,\%) and 311 on the cross-street stubs (51\,\%) (EXP, Tables 3-2 and 3-3, as transcribed in \emph{2026-parking-supply-demand-survey-context}).

\begin{figure}[H]\centering\includegraphics[width=\textwidth]{../derived/figures/curb-and-automobiles/curb_and_automobiles_en.png}\caption{Modelled automobiles and the places the legal curb would hold, by area.}\label{fig:both}\end{figure}

\subsection{Private parking}
\textbf{Measured, on rue de Terrebonne.} Every lot addressed on the street along the lane (""" + str(OM["lots"]) + r""") was judged by the author from street-level imagery on November 12, 2026 (folder \emph{1954-underwriters-plans-terrebonne-garages}, \texttt{derived/street\_check/}): """ + str(OM["with_access"]) + r""" of the """ + str(OM["lots_judged"]) + r""" lots judged have car access today, at least one private place usable (""" + f"{100 * OM['share']:.0f}" + r"""\,\%; 95\,\% interval """ + f"{100 * OM['share_low']:.0f} to {100 * OM['share_high']:.0f}" + r"""). Its buildings of five dwellings or fewer hold """ + str(OW["private_places_independent"]) + r""" independent private places (""" + str(OW["private_places_total"]) + r""" counting cars in tandem) for """ + str(OW["dwellings_small_judged"]) + r""" dwellings, whose modelled automobiles number """ + f"{OW['modelled_automobiles_small_judged']:.0f}" + r"""; the street\textquoteright{}s one parking band holds """ + str(OW["curb_places_on_terrebonne_today_5.5m"]) + r""" places at 5.5\,m. On """ + str(OW["converted_none_left"] + OW["converted_some_left"]) + r""" lots the parking has been turned to another use, wholly (""" + str(OW["converted_none_left"]) + r""") or in part (""" + str(OW["converted_some_left"]) + r"""), where the 1954--55 plans take precedence when they show a garage. The """ + str(OW["large_lots"]) + r""" larger buildings (""" + str(OW["dwellings_large"]) + r""" dwellings) are given no places; """ + str(OW["large_with_underground_garage"]) + r""" of them have an underground garage. Garage interiors are not counted. The check replaced a reading of October 25, 2026 from the 1954--55 plans and the aerial imagery (a garage as built or a driveway at 89 of 123 buildings, one place counted for each), which missed driveways.

""" + fig("off-street-terrebonne", "off_street_terrebonne", "Rue de Terrebonne: modelled automobiles of the dwellings in its buildings of five dwellings or fewer, their private places counted lot by lot from street level (independent places), and the places of the street\\textquoteright{}s parking band today, by sector of the 2023 study.", 0.92) + r"""

\textbf{Measured, for the corridor.} Every lot of the corridor that holds a dwelling (""" + n_(OS["small_buildings"] + OS["large_buildings"]) + r""" lots) was read on enlarged crops of the same aerial imagery, by independent readers working from a written protocol (folder \texttt{derived/readings/}): can a car be driven off the street and left standing clear of the sidewalk, on the lot\textquoteright{}s own driveway, a driveway shared with the neighbour, a front pad, a rear pad or a parking lot? A first reading failed its checks and was discarded; the protocol and the images were corrected and every lot was read again. Two independent readings of the same lot then agreed on 95\,\% of the lots where both gave a yes or a no.

Agreement between readers is not accuracy. Before the second reading, """ + str(OK["small_judged"] + OK["small_cannot_tell"] + OK["large_sampled"]) + r""" lots were drawn at random (100 buildings of five dwellings or fewer, 12 larger), and the author judged each one from street-level imagery, without seeing any reader\textquoteright{}s answer. Of the """ + str(OK["small_judged"]) + r""" small buildings judged yes or no, """ + str(OK["small_yes"]) + r""" have car access (""" + f"{100 * OK['small_share']:.0f}" + r"""\,\%; 95\,\% interval """ + f"{100 * OK['small_share_low']:.0f} to {100 * OK['small_share_high']:.0f}" + r"""). The readers from above missed part of them:
\begin{table}[H]\centering\small
\caption{The author\textquoteright{}s check against the readers\textquoteright{} answers, buildings of five dwellings or fewer. Places: as counted by the author; independent = a car can leave without another being moved; garage interiors not counted.}
\begin{tabular}{@{}lrrrr@{}}\toprule
Reader\textquoteright{}s answer & lots checked & with car access & independent places & total places \\\midrule
""" + "\n".join(f"{lab} & {OK['by_reader_answer'][k]['lots']} & {OK['by_reader_answer'][k]['owner_yes']} & {OK['by_reader_answer'][k]['independent']} & {OK['by_reader_answer'][k]['total']} \\\\" for k, lab in (("yes", "Yes"), ("unclear", "Unclear"), ("no", "No"))) + r"""
\bottomrule\end{tabular}\end{table}
The estimate therefore rests on the check, and uses the readings only to sharpen it: to the lots of each reader answer (""" + n_(OS["read_yes"]) + r""" yes, """ + n_(OS["read_unclear"]) + r""" unclear, """ + n_(OS["read_no"]) + r""" no) it applies the share with access and the mean number of places the author found for the checked lots of that answer. Intervals come from resampling the checked lots (2{,}000 draws, 90\,\%).

For the corridor\textquoteright{}s """ + n_(OS["small_buildings"]) + r""" buildings of five dwellings or fewer: """ + n_(OS["with_access"]) + r""" have car access (""" + n_(OS["with_access_low"]) + r""" to """ + n_(OS["with_access_high"]) + r"""; """ + f"{100 * OS['share_with_access']:.0f}" + r"""\,\%), with """ + n_(OS["private_independent"]) + r""" independent places (""" + n_(OS["private_independent_low"]) + r""" to """ + n_(OS["private_independent_high"]) + r""") and """ + n_(OS["private_total"]) + r""" places in all when cars standing one behind another are counted (""" + n_(OS["private_total_low"]) + r""" to """ + n_(OS["private_total_high"]) + r"""). Garage interiors are in neither figure. Curb and independent private places together number """ + n_(OS["curb_plus_private"]) + r""" at 5.5\,m, against """ + n_(OS["automobiles_modelled"]) + r""" modelled automobiles: """ + f"{OS['per_place_with_private']:.2f}" + r""" automobile per place, against """ + f"{OS['per_place_curb_only']:.2f}" + r""" with the curb alone; the estimate exceeds the area\textquoteright{}s places in """ + str(OS["areas_over_with_private"]) + r""" of the """ + str(len(DA)) + r""" areas, against """ + str(OS["areas_over_curb_only"]) + r""".

\textbf{Buildings of six dwellings or more} (""" + str(OS["large_buildings"]) + r""" buildings, """ + n_(OS["dwellings_in_large_buildings"]) + r""" dwellings) are given no private place here. Of the """ + str(OK["large_sampled"]) + r""" in the check, """ + str(OK["large_underground_garage"]) + r""" have an underground garage whose places cannot be seen from the street or from above, """ + str(OK["large_no"]) + r""" have no parking, and for """ + str(OK["large_cannot_tell"]) + r""" it could not be told. Their modelled automobiles are in the comparison; their garages are not.

\textbf{Limits.} The check is one person\textquoteright{}s judgment from street-level imagery, on """ + str(OK["small_judged"]) + r""" small buildings. The aerial imagery predates the 2024 lane; the street-level imagery is more recent. The first reading of rue de Terrebonne, of October 25, was made from the air alone and found a garage or driveway at 72\,\% of the buildings; checked from the street, the same street gives """ + f"{100 * OM['share']:.0f}" + r"""\,\% with car access, close to the """ + f"{100 * OK['small_share']:.0f}" + r"""\,\% found for the corridor\textquoteright{}s sample from the street.

""" + fig("off-street-corridor", "off_street_corridor", "The corridor\\textquoteright{}s areas with the measured private places of small buildings added (independent places only).") + r"""

\subsection{The corridor on one map}
Figure~\ref{fig:corridor-parking-map} puts every source on one map: each area shaded by its modelled automobiles, the legal curb of every block face, and, on rue de Terrebonne, each lot\textquoteright{}s private places as counted from the street. Elsewhere in the corridor no private place is drawn lot by lot, since per lot those are readings from above; the table below the map gives each area\textquoteright{}s calibrated total with its interval. Figure~\ref{fig:status-map} colours each area by its modelled automobiles as a share of its places, with the thresholds of the charts (green under 80\,\%, yellow 80 to 100\,\%, red over 100\,\%): with private places, """ + STAT["A"] + r"""; with the curb alone, """ + STAT["B"] + r""". With private places, the areas over 100\,\% are areas where almost every household lives in a building of six dwellings or more, whose garages are not counted (share of households in such buildings: """ + STAT["red_A"] + r"""): the share there reflects places the count leaves out. A share compares registered vehicles with capacity; it does not measure how full the street is.

""" + fig("corridor-parking-map", "corridor_parking_map", "The corridor\\textquoteright{}s parking on one map: areas shaded by modelled automobiles (SAAQ 2024), legal curb by block face (measured), and rue de Terrebonne\\textquoteright{}s lots by their private places (counted from street level, November 12, 2026); per area, modelled automobiles, curb places and private places with their intervals.\\label{fig:corridor-parking-map}", 1.0) + r"""

""" + fig("status-map", "status_map", "Modelled automobiles as a share of places, by area. A: curb and private places; B: curb alone. Hatched in A: areas where most households live in buildings of six dwellings or more, whose garages are not counted.\\label{fig:status-map}", 1.0) + r"""

\subsection{Snow-loading nights}\label{sec:snow}
On a snow-loading night parking is banned on the streets being cleared. The City publishes the truckloads hauled per snow-removal sector and per day, and each season\textquoteright{}s sector outlines; it does not publish which street, or which side, was under a ban on which night. Info-Neige (Planif-Neige) is offered as a live service with a token, with no history on the open-data portal (checked November 12, 2026). That part is therefore replaced by assumptions, stated here and given a range. The figures below compare capacity on a loading night; none is an observation of a loading night.

\textbf{Operations.} The corridor\textquoteright{}s legal curb lies in three sectors in 2025--26: CDN-301 (""" + f"{SL['sector_curb_km_2025_26']['CDN-301']:.1f}" + r"""\,km), CDN-111 (""" + f"{SL['sector_curb_km_2025_26']['CDN-111']:.1f}" + r"""\,km) and CDN-112 (""" + f"{SL['sector_curb_km_2025_26']['CDN-112']:.1f}" + r"""\,km); in """ + _w[0] + r""" it lay in the sectors of that season (CDN-301, CDN-105, CDN-106). A loading operation is taken to be a run of loading days in a sector, one-day gaps allowed, of at least """ + str(SL["operation_min_truckloads"]) + r""" truckloads, between December 1 and March 31; """ + str(SL["spot_runs_left_out"]) + r""" smaller runs in the borough\textquoteright{}s sectors are treated as spot removals and left out. CDN-301 had """ + _ops301 + r""" operations in the five winters """ + _w[0] + r""" to """ + _w[-1] + r""". Each block face is assumed to be under a ban for one night per operation, during the night hours, when registered automobiles are at home.

\textbf{Two scales.} \emph{Area}: displaced cars stay in their own area. On the area\textquoteright{}s loading nights a share of its curb is under a ban: 25\,\% (its streets spread over four nights, a side at a time), 50\,\% (a side a night, two nights: the central case) or 100\,\% (both sides the same night). \emph{District}: displaced cars can park anywhere in the district\textquoteright{}s part of the corridor; on each night the share of its curb under a ban is that night\textquoteright{}s truckloads in the sector over the operation\textquoteright{}s total, as if loading proceeded evenly over the sector. That share never exceeds """ + f"{_maxban:.0f}" + r"""\,\%.

\textbf{Free lots.} The City\textquoteright{}s list of lots open during loading holds one lot within 1.5\,km of the corridor: the Doug-Harvey arena lot (4985 West Hill), """ + str(_lot["places"]) + r""" places, """ + _lot["hours"].replace(" à ", "--") + r""", listed for """ + ", ".join(_lotw) + r""" and not for the last two winters. Its places are added in the winters it was listed, to each area within 500\,m and to the Loyola district.

\textbf{Area scale.} In the central case, on its loading night, """ + str(SQ[50]["with_private"]["areas_over_100_on_loading_night"]) + r""" of the """ + str(len(SA)) + r""" areas have more modelled automobiles than places, private places included; """ + str(len(_already)) + r""" of them (areas """ + " and ".join(str(n) for n in _already.no) + r""", mostly of large buildings whose garages are not counted) are above 100\,\% on an ordinary night already. The other """ + str(len(_q50w)) + r""" (areas """ + ", ".join(str(n) for n in _q50w.no) + r""") are pushed above 100\,\% on """ + SNOW_NIGHTS + r""" nights a winter on average (two nights an operation, five winters). With the curb alone, """ + str(SQ[50]["curb_only"]["areas_over_100_on_loading_night"]) + r""" areas are above 100\,\% on their loading night, """ + str(SQ[50]["curb_only"]["of_which_over_100_on_ordinary_nights"]) + r""" of them already on an ordinary night. If the ban takes 25\,\% of the curb a night, """ + str(SQ[25]["with_private"]["areas_over_100_on_loading_night"]) + r""" areas are above 100\,\% with private places (""" + str(SQ[25]["with_private"]["areas_pushed_over_100_by_loading"]) + r""" pushed over by loading); if it takes 100\,\%, all """ + str(SQ[100]["with_private"]["areas_over_100_on_loading_night"]) + r""" are (Figure~\ref{fig:snow-areas}).

\textbf{District scale.} The Loyola part of the corridor stays below 100\,\% on every night of the five winters, with the curb alone (at most """ + f"{100 * max(SLD['max_share_curb_only'].values()):.0f}" + r"""\,\%) as with private places. The Notre-Dame-de-Grâce part stays below 100\,\% with private places (at most """ + f"{100 * max(SLN['max_share_with_private'].values()):.0f}" + r"""\,\%); with the curb alone it is above 100\,\% on """ + _and(SLN["nights_over_100_curb_only"]) + r""" nights in the five winters, of """ + _and(SLN["loading_nights"]) + r""" nights with loading in its sectors. At the upper end of the automobile interval, with private places, it is above 100\,\% on """ + _and(SLN["nights_over_100_with_private_high"]) + r""" nights. With a threshold of 50 or 200 truckloads for an operation, the NDG count with the curb alone over the five winters is """ + str(SENS["50"]["Notre-Dame-de-Grâce"]["nights_over_100_curb_only_total"]) + r""" or """ + str(SENS["200"]["Notre-Dame-de-Grâce"]["nights_over_100_curb_only_total"]) + r""", against """ + str(SENS["100"]["Notre-Dame-de-Grâce"]["nights_over_100_curb_only_total"]) + r""" (Figure~\ref{fig:snow-districts}).

\textbf{What these figures cannot show.} Which streets were under a ban on which night, and for which hours; whether loading proceeds evenly over a sector; where displaced cars actually went. \textbf{Snow left on the street is not counted:} only the bans for loading are; between a snowfall and its loading, snowbanks and windrows narrow the usable curb, keep cars away from it and lengthen the gaps between them, so the curb holds fewer cars than its length suggests on those nights too. No record of the usable curb with snow on the ground exists, so the places on such nights are overstated. A long run of loading days may hold two operations (February 2025: 22 days counted as one), which would add nights. Visitors, institutions and vehicles from elsewhere are not in the automobile figure; vehicles kept in garages are not in the places. As everywhere in this note, a share of places compares capacity, not occupancy; registered automobiles stand in for overnight demand.

\begin{figure}[H]\centering\includegraphics[width=\textwidth]{../derived/figures/snow-loading-areas/snow_loading_areas_en.png}\caption{Snow-loading nights, area by area: the share of places on an ordinary night and on the area\textquoteright{}s loading night, under the three assumptions.}\label{fig:snow-areas}\end{figure}

\begin{figure}[H]\centering\includegraphics[width=\textwidth]{../derived/figures/snow-loading-districts/snow_loading_districts_en.png}\caption{Snow-loading nights, district by district, five winters, night by night.}\label{fig:snow-districts}\end{figure}

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
\item \textbf{Measured, with a measured error:} private places of the corridor\textquoteright{}s small buildings, from a reading of every lot calibrated on a random sample checked from the street.
\item \textbf{Not counted:} garage interiors; the parking of buildings of six dwellings or more, several of which have underground garages.
\item \textbf{Modelled:} the automobiles of every area smaller than an FSA. The model shares a known total better than households alone at the one level where this can be tested; below the FSA nothing can test it, and the 2015 check does not confirm its area-by-area differences.
\item \textbf{Not measured by anyone:} where registered vehicles are kept; occupancy of the curb since the lane was built; which streets are under a snow-loading ban on which night (not published).
\item The curb reading rests on the sign inventory as published on October 23, 2026 and on rules for arrows that were checked on rue de Terrebonne only.
\end{itemize}

\section{Reproducibility}
Scripts, tables and figures: \url{""" + URL + r"""}. Order: \texttt{build\_dataset.py}, \texttt{curb\_supply.py}, \texttt{demand\_model.py}, \texttt{corridor.py}, \texttt{offstreet\_strips.py}, \texttt{offstreet\_crops.py}, \texttt{offstreet\_readings\_v2.py}, \texttt{offstreet.py}, \texttt{snow\_loading.py}, the figure scripts under \texttt{derived/figures/}, \texttt{build\_docs.py}. The census, roll, sign and postal-code files are read from outside the repository (sources and dates in the folder\textquoteright{}s README); the tables by dissemination area and by block face are in \texttt{derived/tables/}.

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
DMARK = (r"\setbeamertemplate{footline}{\hfill{\tiny\textcolor{black!60}{Preliminary results, not peer reviewed, " + TODAY + r"}\quad\insertframenumber}\hspace{1em}\vspace{0.4em}}") if FINAL else r"\setbeamertemplate{footline}{\hfill{\tiny\textcolor{red!70!black}{DRAFT for the author\textquoteright{}s review, " + TODAY + r"}\quad\insertframenumber}\hspace{1em}\vspace{0.4em}}"
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
\item Less 10\,m at each end (cross street\textquoteright{}s half roadway, and the 5\,m of the Highway Safety Code), less stretches forbidden at all times
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
\item This comparison is the limiting case where \textbf{every registered vehicle is kept at the curb}. Private parking: next slides.
\item Visitors, institutions and vehicles from elsewhere use the same curb; a place at the far end of an area is not a place at one\textquoteright{}s door.
\item The occupancy measurements that exist are EXP\textquoteright{}s: Thursday, September 29, 2022, 18:30--19:30: 247 cars on Terrebonne\textquoteright{}s places (50\,\%), 311 on the cross-street stubs (51\,\%).
\end{itemize}""") + ffig("Private parking, measured on rue de Terrebonne", "off-street-terrebonne", "off_street_terrebonne", f"{OM['with_access']} of the {OM['lots_judged']} lots judged from street level (Nov.~12, 2026) have car access today ({100 * OM['share']:.0f}\\,\\%). Private places counted lot by lot; the {OW['large_lots']} larger buildings get none.", 0.6) + fr("Private parking in the corridor: every lot read, then checked", r"""\begin{itemize}
\item Every lot holding a dwelling (""" + n_(OS["small_buildings"] + OS["large_buildings"]) + r""") was read on enlarged aerial crops by independent readers under a written protocol. A first reading failed its checks and was redone.
\item A random sample of """ + str(OK["small_judged"] + OK["small_cannot_tell"] + OK["large_sampled"]) + r""" lots, drawn beforehand, was judged by the author from street-level imagery without seeing the readers\textquoteright{} answers.
\item Small buildings in the check: \textbf{""" + str(OK["small_yes"]) + r""" of """ + str(OK["small_judged"]) + r""" have car access} (""" + f"{100 * OK['small_share']:.0f}" + r"""\,\%). Where the readers said yes, the check confirmed """ + f"{OK['by_reader_answer']['yes']['owner_yes']} of {OK['by_reader_answer']['yes']['lots']}" + r"""; where they said no, only """ + f"{OK['by_reader_answer']['no']['lots'] - OK['by_reader_answer']['no']['owner_yes']} of {OK['by_reader_answer']['no']['lots']}" + r""": a view from above misses driveways.
\item Estimate for the """ + n_(OS["small_buildings"]) + r""" small buildings, calibrated on the check: \textbf{""" + n_(OS["private_independent"]) + r""" private places} a car can leave without another being moved (""" + n_(OS["private_independent_low"]) + r""" to """ + n_(OS["private_independent_high"]) + r"""); """ + n_(OS["private_total"]) + r""" with cars one behind another. Garage interiors not counted.
\item The """ + str(OS["large_buildings"]) + r""" buildings of six dwellings or more are given none: """ + str(OK["large_underground_garage"]) + r""" of the """ + str(OK["large_sampled"]) + r""" checked have an underground garage that cannot be counted.
\end{itemize}""") + ffig("With private parking added, area by area", "off-street-corridor", "off_street_corridor", f"{OS['per_place_with_private']:.2f} modelled automobile per place with private places, against {OS['per_place_curb_only']:.2f} with the curb alone.", 0.7) + ffig("All the sources on one map", "corridor-parking-map", "corridor_parking_map", "Off Terrebonne, private places are shown per area only (calibrated totals), never lot by lot.", 0.8) + ffig("Automobiles as a share of places, by area", "status-map", "status_map", f"Reds in A: large buildings, garages not counted. A share does not measure how full the street is.", 0.76) + fr("Snow-loading nights: what the data allow", r"""\begin{itemize}
\item The City publishes \textbf{truckloads per sector per day} and the sector outlines; \textbf{not} which street or side was under a ban on which night (Info-Neige is live only, no history).
\item Operation: a run of loading days in a sector with $\geq$ """ + str(SL["operation_min_truckloads"]) + r""" truckloads, Dec.~1 to Mar.~31. CDN-301: """ + _ops301 + r""" operations in """ + _w[0] + r""" to """ + _w[-1] + r""".
\item Assumed: each block face under a ban one night per operation, at night. On the area\textquoteright{}s loading night \textbf{25, 50 (central) or 100\,\%} of its curb under a ban.
\item Two scales: cars stay in their \textbf{area}; or move anywhere in the \textbf{district}\textquoteright{}s part of the corridor (night\textquoteright{}s share of the curb = night\textquoteright{}s truckloads over the operation\textquoteright{}s, at most """ + f"{_maxban:.0f}" + r"""\,\%).
\item Not counted: \textbf{uncleared snow}. Between a snowfall and its loading, snowbanks narrow the usable curb; no record of it exists, so places on those nights are overstated.
\item One free lot within 1.5\,km: Doug-Harvey arena, """ + str(_lot["places"]) + r""" places, listed """ + _lotw[0] + r""" to """ + _lotw[-1] + r""" only; added in those winters.
\end{itemize}""") + ffig("Snow-loading nights, area by area", "snow-loading-areas", "snow_loading_areas", f"Central case (50\\,\\%), private places included: {SQ[50]['with_private']['areas_over_100_on_loading_night']} of {len(SA)} areas above 100\\,\\% on their loading night, {len(_already)} of them already on an ordinary night; the other {len(_q50w)} on {SNOW_NIGHTS} nights a winter. Assumptions, not observations.", 0.66) + ffig("Snow-loading nights, district by district", "snow-loading-districts", "snow_loading_districts", f"Loyola: below 100\\,\\% every night. NDG: below 100\\,\\% with private places; curb alone above it on {_and(SLN['nights_over_100_curb_only'])} nights ({_w[0]} to {_w[-1]}). Capacity, not occupancy.", 0.64) +  ffig("A check from another source: the 2015 LiDAR night", "lidar-check", "lidar_check", f"{int(whole.cars_at_curbs_2015_night + whole.cars_on_lots_2015_night)} cars seen for {int(whole.dwellings_addressed_on_terrebonne)} dwellings addressed on Terrebonne. Agreement in order of magnitude; area by area, no relation (rank correlation {N['lidar']['rho_rate']:.2f}, {N['lidar']['areas']} areas).", 0.6) + ffig("Cross-check: the garages of 1954--55 and car access today", "social-maps", "then_and_now", "Hingston to Hampton: « Autos Bast » (basement garages) in 1954--55, car access today. A cross-check only.", 0.68) + fr("Cross-check: the 2015 LiDAR night, Grand to Melrose", "\\begin{center}\\includegraphics[height=0.68\\textheight]{../../1954-underwriters-plans-terrebonne-garages/derived/figures/terrebonne_parked_cars_lidar_hero_en.png}\\end{center}\n{\\footnotesize Parked cars in red, at the curbs and in the driveways (2015, at night, trees removed). A cross-check only.}") + fr("What is shown and what is not", r"""\begin{itemize}
\item \textbf{Measured:} the registered automobiles of H4A and H4B (type inferred); the legal curb of each block face, as an upper bound; garages and driveways on rue de Terrebonne.
\item \textbf{Measured, with a measured error:} private places of small buildings (every lot read, a random sample checked from the street).
\item \textbf{Not counted:} garage interiors; the garages of larger buildings.
\item \textbf{Modelled:} the automobiles of every area smaller than an FSA. The model shares a known total better than households alone where that can be tested; below the FSA nothing can test it, and the 2015 check does not confirm its area-by-area differences.
\item \textbf{Not measured by anyone:} where registered vehicles are kept; occupancy of the curb since the lane was built; which streets are under a snow-loading ban on which night (not published).
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
print("OK build_docs", STAMP, "preliminary" if FINAL else "draft")
