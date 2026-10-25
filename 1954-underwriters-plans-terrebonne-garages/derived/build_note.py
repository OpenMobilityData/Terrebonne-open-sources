#!/usr/bin/env python3
"""Fill the note (LaTeX -> PDF) and the web page (../index.html) from summary.json and
buildings_geo.csv. Run after summary.py and maps.py. Usage: python3 build_note.py"""
import csv, json, os, subprocess, datetime, html
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
S = json.load(open(os.path.join(HERE, 'summary.json')))
rows = list(csv.DictReader(open(os.path.join(HERE, 'buildings_geo.csv'), encoding='utf-8')))
STAMP = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
P = 'https://openmobilitydata.github.io/Terrebonne-open-sources/1954-underwriters-plans-terrebonne-garages/'
def pc(x): return f"{x:.0f}\\,\\%" if x is not None else '--'
def pch(x): return f"{x:.0f} %" if x is not None else '–'
N, Y, PCT = S['buildings_terrebonne'], S['with_garage'], S['pct']
by_tex = '\n'.join(f"{b['side']} & {b['sheet']} & {b['extent'].replace('&', r'\&')} & {b['buildings']} & {b['with_garage']} & {pc(b['pct'])} \\\\" for b in S['by_sheet'])
by_html = '\n'.join(f"<tr><td>{b['side']}</td><td>{b['sheet']}</td><td>{html.escape(b['extent'])}</td><td>{b['buildings']}</td><td>{b['with_garage']}</td><td>{pch(b['pct'])}</td></tr>" for b in S['by_sheet'])
PD = S.get('present_day'); dec = ', '.join(f"{k} {v}" for k, v in S['construction_years']['by_decade'].items())
ga = S['garage_access']; gk = S['garage_kind']; R = S['roll']; C = S['corner_cross_street']
tex = r"""\documentclass[11pt]{article}
\usepackage[margin=2.3cm]{geometry}\usepackage{graphicx}\usepackage{booktabs}\usepackage{longtable}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{lmodern}\usepackage{microtype}
\usepackage[hidelinks]{hyperref}\usepackage{caption}\captionsetup{font=small}
\title{Off-street parking on rue de Terrebonne as built:\\ a reading of the 1954--55 fire-insurance plans}
\author{Terrebonne-open-sources (a resident of Côte-des-Neiges--Notre-Dame-de-Grâce)}
\date{October 25, 2026 \quad\small v""" + STAMP + r"""}
\begin{document}\maketitle
\section*{Summary}
Of the \textbf{""" + f"{N}" + r"""} residential buildings with a rue de Terrebonne address between the west end of the protected lane (Belmore) and avenue Girouard on the sixteen sheets available, \textbf{""" + f"{Y}" + r"""} were built with a garage, that is \textbf{""" + pc(PCT) + r"""} (north side """ + f"{S['side_N']['with_garage']} of {S['side_N']['buildings']}, " + pc(S['side_N']['pct']) + r"""; south side """ + f"{S['side_S']['with_garage']} of {S['side_S']['buildings']}, " + pc(S['side_S']['pct']) + r"""). Counting only the readings made with high confidence gives """ + pc(S['high_confidence']['pct']) + r""". Weighted by the dwellings the City's assessment roll lists in the same buildings, """ + pc(R['pct_dwellings']) + r""" of the """ + f"{R['dwellings']}" + r""" dwellings are in a building that was built with a garage.

The plans show garages as built, not driveways: a driveway without a garage leaves no mark, so the share of properties with a driveway or a garage as built is at least this figure. They show the stock of 1954--55, not of today; the City's roll dates """ + f"{S['construction_years']['n'] - S['construction_years']['after_1955']} of the {S['construction_years']['n']}" + r""" matched buildings to 1955 or earlier (median """ + f"{S['construction_years']['median']}" + r"""), so the frontage drawn is essentially the one standing today, but the use of each garage and driveway since then is not recorded here.

\section{Source}
The Underwriters' Survey Bureau, Limited, \emph{Insurance plan of the city of Montreal}, volume 7, sheets 739-2 to 739-5, 775, 784-1, 784-2, 785-1, 787-5 to 787-7, 789-12 to 789-16 and 798-3, dated November 1954 to December 1955 on the sheets (``Montreal, vol.~7, November 1954''; sheet 775 ``April 1955''; sheet 739-4 ``December 1955''). Each sheet carries the notice ``This plan is the property of the Underwriters' Survey Bureau, Limited, (unauthorized reproduction prohibited) \ldots'' and ``Copyright registered at Ottawa by the Underwriters' Survey Bureau, Limited, Toronto and Montreal''. The plans draw every building with its construction, storeys and civic number, and write \emph{Auto} or \emph{Autos} on every garage: in the basement (\emph{Auto Bt}, \emph{Autos Bast}), attached, or detached in the yard. Sheet 787-8 (south side, Hampton to Melrose: the Royal and Draper blocks) is missing from the copy available and from every other copy found; those two block faces are not counted (the north side opposite them has """ + f"{[b for b in S['by_sheet'] if b['sheet']=='787-6'][0]['with_garage'] + [b for b in S['by_sheet'] if b['sheet']=='787-6'][1]['with_garage'] + [b for b in S['by_sheet'] if b['sheet']=='787-6'][2]['with_garage']} garages on {sum(b['buildings'] for b in S['by_sheet'] if b['sheet']=='787-6')} buildings" + r""").

\section{Method}
\begin{enumerate}
\item \textbf{Reading.} Every building on the Terrebonne block faces, both sides, was read from the scans at two to four times magnification and recorded in \texttt{buildings\_1954.csv} (one row per building: sheet, side, block, cross streets, civic numbers, building type, the street it is addressed on, corner lot, garage yes/no, kind of garage, the presumed access, a confidence grade and notes). The unit is the building with a Terrebonne civic number: a semi-detached pair is two buildings, a duplex pair is one building of two to four flats, an apartment building counts once. Corner buildings addressed on the cross street (""" + f"{C['buildings']}" + r""", of which """ + f"{C['with_garage']}" + r""" with a garage) are listed with the cross street as their frontage and left out of the share; so are the two churches, the presbytery and the two frontages vacant in 1954--55.
\item \textbf{Georeferencing.} Each sheet was fitted to the City's géobase (CC-BY~4.0) by a similarity transform on the pixel positions of its Terrebonne intersections (\texttt{controls.csv}, \texttt{georef.py}); residuals are 0--4\,m (one of 7\,m). The fit was checked by drawing the City's assessment-roll parcels over each sheet.
\item \textbf{Positions and dwellings.} Each row was joined to the City's \emph{unités d'évaluation foncière} (CC-BY~4.0) by civic number and street, or, for corner buildings renumbered on the cross street since 1954, by position (\texttt{buildings.py}; """ + f"{sum(r['match'].startswith('roll') for r in rows)} of {len(rows)}" + r""" rows matched, the rest placed schematically along their block face). The roll gives the dwelling count and the year of construction of each matched building.
\item \textbf{Maps.} Both maps use a frame straightened along the street (distance along Terrebonne, offset across; north side above). The first draws the markers on the georeferenced sheets, the second on a base made only of the City's open data (\texttt{maps.py}).
\end{enumerate}

\section{Results}
\begin{table}[h]\centering\small
\begin{tabular}{lrrr}\toprule
 & Buildings addressed on Terrebonne & With a garage as built & Share\\\midrule
North side & """ + f"{S['side_N']['buildings']} & {S['side_N']['with_garage']} & " + pc(S['side_N']['pct']) + r"""\\
South side (sheet 787-8 missing) & """ + f"{S['side_S']['buildings']} & {S['side_S']['with_garage']} & " + pc(S['side_S']['pct']) + r"""\\
\textbf{Both sides} & \textbf{""" + f"{N}" + r"""} & \textbf{""" + f"{Y}" + r"""} & \textbf{""" + pc(PCT) + r"""}\\
High-confidence readings only & """ + f"{S['high_confidence']['buildings']} & {S['high_confidence']['with_garage']} & " + pc(S['high_confidence']['pct']) + r"""\\
Dwellings (City roll, """ + f"{R['buildings_matched']}" + r""" buildings) & """ + f"{R['dwellings']} & {R['dwellings_in_buildings_with_garage']} & " + pc(R['pct_dwellings']) + r"""\\\bottomrule
\end{tabular}\caption{Garages as built on the Terrebonne frontage, 1954--55 plans.}\end{table}

Of the """ + f"{Y}" + r""" garages, """ + f"{gk.get('basement', 0)}" + r""" are basement garages, """ + f"{gk.get('detached', 0)}" + r""" are detached in the yard and """ + f"{gk.get('attached or in an annex', 0)}" + r""" attached or in an annex. The door opens on Terrebonne for """ + f"{ga.get('Terrebonne', 0)}" + r""", on either street for """ + f"{ga.get('either street (corner)', 0)}" + r""" corner lots, and on a rear lane for """ + f"{ga.get('lane', 0)}" + r""". Building types on the frontage (from the plans): """ + ', '.join(f"{k} {v}" for k, v in S['types'].items()) + r""". Years of construction from the roll, by decade: """ + dec + r""".

\begin{longtable}{llp{5.2cm}rrr}
\caption{By block face (residential buildings addressed on Terrebonne).}\\\toprule
Side & Sheet & Block face & Buildings & Garage & Share\\\midrule\endfirsthead
\toprule Side & Sheet & Block face & Buildings & Garage & Share\\\midrule\endhead
""" + by_tex + r"""
\\\bottomrule\end{longtable}

\begin{figure}[p]\centering\includegraphics[width=\textwidth]{figures/terrebonne_garages_1954_map_city_en.pdf}
\caption{On a base drawn from the City's open data (géobase, assessment-roll parcels; CC-BY 4.0).}\end{figure}
\begin{figure}[p]\centering\includegraphics[width=\textwidth]{figures/terrebonne_garages_1954_map_underwriters_en.png}
\caption{On the 1954--55 sheets, georeferenced and straightened along the street.}\end{figure}

\section{The frontages today}
A check of each building's frontage on the Gouvernement du Qu\'ebec's continuous aerial imagery (service \emph{Imagerie\_GQ}, fetched October 25, 2026; leaf-off spring imagery, about 8~cm per pixel; the City's parcels overlaid) recorded, for """ + f"{PD['checked']}" + r""" of the """ + f"{N}" + r""" buildings, whether a driveway, paved apron or parking pad is visible on the lot today, whether a vehicle was parked on it at the moment of the photograph, and from which street it is reached (\texttt{buildings\_geo.csv}, columns \texttt{driveway\_today}, \texttt{vehicle\_or\_pad\_on\_lot}, \texttt{access\_today}). What a garage holds inside cannot be seen from above, so the check measures the visible access, not the use.

\begin{table}[h]\centering\small
\begin{tabular}{lrr}\toprule
 & Buildings & Share\\\midrule
Checked & """ + f"{PD['checked']}" + r""" & \\
Driveway, apron or parking pad visible today & """ + f"{PD['driveway_or_apron_today']} & " + pc(PD['pct_driveway_today']) + r"""\\
Garage as built (1954--55) \emph{or} driveway today & """ + f"{PD['garage_1954_or_driveway_today']} & " + pc(PD['pct_either']) + r"""\\
\quad north side & """ + f"{PD['by_side']['N']['either']} of {PD['by_side']['N']['checked']} & " + pc(100 * PD['by_side']['N']['either'] / PD['by_side']['N']['checked']) + r"""\\
\quad south side & """ + f"{PD['by_side']['S']['either']} of {PD['by_side']['S']['checked']} & " + pc(100 * PD['by_side']['S']['either'] / PD['by_side']['S']['checked']) + r"""\\
\quad by dwellings (City roll) & """ + f"{PD['dwellings_either']} of {PD['dwellings_checked']} & " + pc(PD['pct_dwellings_either']) + r"""\\
Garage of 1954--55 with its apron still visible & """ + f"{PD['garage_1954_with_apron_today']}" + r""" & \\
Garage of 1954--55 with no apron visible today & """ + f"{PD['garage_1954_without_apron_today']}" + r""" & \\
No garage in 1954--55, a driveway or pad today & """ + f"{PD['no_garage_1954_with_driveway_today']}" + r""" & \\
A vehicle parked on the lot when photographed & """ + f"{PD['vehicle_on_lot_at_capture']}" + r""" & \\\bottomrule
\end{tabular}\caption{The frontages today (aerial imagery read October 25, 2026).}\end{table}

\begin{figure}[p]\centering\includegraphics[width=\textwidth]{figures/terrebonne_garages_1954_map_today_en.pdf}
\caption{Garage as built and driveway today, building by building.}\end{figure}

\section{Caveats}
\begin{itemize}
\item \textbf{Garages, not driveways.} The plans mark structures. A driveway or parking pad without a garage leaves no mark, so the as-built share with a driveway or garage is a lower bound.
\item \textbf{As built, not as used.} The 1954--55 share counts structures; the present-day check sees aprons, driveways and parked vehicles from above but not what a garage holds inside (a workshop, storage, living space), so neither figure is the share of households that park off-street today. A garage built in 1930 or 1950 may also be too small for a large vehicle of today. Ten garages of 1954--55 show no apron today and one reading is unclear.
\item \textbf{Buildings, not households.} The share by building and the share by dwelling happen to agree (""" + pc(PCT) + r""" and """ + pc(R['pct_dwellings']) + r"""), but a duplex pair has two to four flats and one or two garages, and three of the four apartment buildings have a basement garage of unrecorded capacity.
\item \textbf{One sheet missing} (787-8) and """ + f"{sum(r['confidence']=='medium' for r in rows if r['addressed_on']=='Terrebonne')}" + r""" readings graded medium (noted row by row).
\item \textbf{Corner lots.} Which street a corner building is addressed on changed in places between 1954 and the present roll; the table keeps the 1954 numbering and the join records the present unit.
\end{itemize}
\end{document}
"""
open(os.path.join(HERE, 'terrebonne_garages_1954_note_en.tex'), 'w').write(tex)
for _ in range(2): subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', 'terrebonne_garages_1954_note_en.tex'], cwd=HERE, stdout=subprocess.DEVNULL)
for ext in ('.aux', '.log', '.out'):
    try: os.remove(os.path.join(HERE, 'terrebonne_garages_1954_note_en' + ext))
    except FileNotFoundError: pass
# ---- web page ----
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Terrebonne garages 1954</title>
<style>:root{{--bg:#fcfcfb;--ink:#0b0b0b;--muted:#52514e;--rule:#dedbd3;--accent:#2a78d6}}
@media (prefers-color-scheme:dark){{:root:not([data-theme=light]){{--bg:#1a1a19;--ink:#f0efec;--muted:#c3c2b7;--rule:#3a3936;--accent:#3987e5}}}}
:root[data-theme=dark]{{--bg:#1a1a19;--ink:#f0efec;--muted:#c3c2b7;--rule:#3a3936;--accent:#3987e5}}
body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 -apple-system,Helvetica,Arial,sans-serif}}
main{{max-width:900px;margin:0 auto;padding:24px 16px}}h1{{font-size:1.6rem;line-height:1.25}}h2{{font-size:1.15rem;margin-top:2rem}}
.big{{font-size:2.6rem;font-weight:700;color:var(--accent);line-height:1.1}}.muted{{color:var(--muted);font-size:.9rem}}
table{{border-collapse:collapse;width:100%;font-size:.92rem;margin:1rem 0}}th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--rule)}}th{{color:var(--muted);font-weight:600}}
td:nth-child(n+4),th:nth-child(n+4){{text-align:right}}img{{max-width:100%;height:auto;border:1px solid var(--rule)}}
details{{margin:1rem 0}}a{{color:var(--accent)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px;margin:1rem 0}}.tile{{border:1px solid var(--rule);border-radius:8px;padding:12px}}</style></head><body><main>
<h1>Off-street parking on rue de Terrebonne as built: the 1954–55 fire-insurance plans</h1>
<p class="muted">Terrebonne-open-sources · built {STAMP} · <a href="derived/terrebonne_garages_1954_note_en.pdf">note (PDF)</a> · <a href="derived/buildings_geo.csv">table (CSV)</a> · <a href="https://github.com/OpenMobilityData/Terrebonne-open-sources/tree/main/1954-underwriters-plans-terrebonne-garages">repository folder</a></p>
<div class="grid">
<div class="tile"><div class="big">{PCT:.0f} %</div><div>of the {N} residential buildings with a Terrebonne address were built with a garage ({Y} buildings)</div></div>
<div class="tile"><div class="big">{S['side_N']['pct']:.0f} % · {S['side_S']['pct']:.0f} %</div><div>north side ({S['side_N']['with_garage']} of {S['side_N']['buildings']}) · south side ({S['side_S']['with_garage']} of {S['side_S']['buildings']}; one sheet missing)</div></div>
<div class="tile"><div class="big">{PD['pct_either']:.0f} %</div><div>were built with a garage or show a driveway or parking pad on today's aerial imagery ({PD['garage_1954_or_driveway_today']} of {PD['checked']} checked)</div></div>
</div>
<p>The Underwriters' Survey Bureau's insurance plans of Montreal (volume 7, sheets dated November 1954 to December 1955) draw every building on rue de Terrebonne and write <em>Auto</em> on every garage. Reading the sixteen sheets available building by building, from the west end of the protected lane (Belmore) to avenue Girouard, gives the figures above. The plans record garages as built, not driveways, so a property with a driveway and no garage is not counted: the share with a driveway <em>or</em> a garage as built is at least {PCT:.0f} %. They record 1954–55, not today: the City's roll dates {S['construction_years']['n'] - S['construction_years']['after_1955']} of the {S['construction_years']['n']} matched buildings to 1955 or earlier (median {S['construction_years']['median']}), so the buildings are the ones standing today, but what each garage or driveway is used for now is not recorded here.</p>
<h2>The frontages today</h2>
<p>A second reading, on the Gouvernement du Québec's continuous aerial imagery (fetched October 25, 2026, leaf-off, about 8 cm per pixel, with the City's parcels overlaid), recorded for {PD['checked']} of the {N} buildings whether a driveway, paved apron or parking pad is visible on the lot today and from which street it is reached. <strong>{PD['driveway_or_apron_today']} buildings ({PD['pct_driveway_today']:.0f} %) show one</strong>; counting a building if it either was built with a garage or shows a driveway today gives <strong>{PD['garage_1954_or_driveway_today']} of {PD['checked']}, {PD['pct_either']:.0f} %</strong> (north {PD['by_side']['N']['either']} of {PD['by_side']['N']['checked']}, south {PD['by_side']['S']['either']} of {PD['by_side']['S']['checked']}; by dwellings {PD['pct_dwellings_either']:.0f} %). Of the garages of 1954–55, {PD['garage_1954_with_apron_today']} still have a visible apron and {PD['garage_1954_without_apron_today']} do not; {PD['no_garage_1954_with_driveway_today']} buildings with no garage in 1954–55 have a driveway or parking pad today. A vehicle was parked on the lot of {PD['vehicle_on_lot_at_capture']} buildings when the photograph was taken. What a garage holds inside cannot be seen from above.</p>
<p><a href="derived/figures/terrebonne_garages_1954_map_today_en.png"><img src="derived/figures/terrebonne_garages_1954_map_today_en.png" alt="Map of the Terrebonne frontage: garage as built and driveway today, one marker per building"></a></p>
<p class="muted">Garage as built (1954–55) and driveway or apron today (2026 imagery), building by building. <a href="derived/figures/terrebonne_garages_1954_map_today_en.pdf">PDF</a> · <a href="derived/figures/terrebonne_garages_1954_map_today_fr.png">français</a></p>
<h2>Where the frontage is</h2>
<p>Of the {Y} garages, {gk.get('basement',0)} are basement garages, {gk.get('detached',0)} detached in the yard and {gk.get('attached or in an annex',0)} attached or in an annex; the door opens on Terrebonne for {ga.get('Terrebonne',0)}, on either street for {ga.get('either street (corner)',0)} corner lots and on a rear lane for {ga.get('lane',0)}. A further {C['buildings']} corner buildings stand on the Terrebonne block faces but are addressed on the cross street, with their doors and driveways there ({C['with_garage']} of them have a garage); they are shown as squares and left out of the share. Two churches, the presbytery and two frontages vacant in 1954–55 are shown as diamonds.</p>
<h2>Maps</h2>
<p><a href="derived/figures/terrebonne_garages_1954_map_city_en.png"><img src="derived/figures/terrebonne_garages_1954_map_city_en.png" alt="Map of the Terrebonne frontage on the City's parcels, one marker per building, coloured by garage as built"></a></p>
<p class="muted">On a base drawn from the City's open data (géobase street centrelines and assessment-roll parcels, CC-BY 4.0), straightened along the street: north side above, south side below, west at left. <a href="derived/figures/terrebonne_garages_1954_map_city_en.pdf">PDF</a> · <a href="derived/figures/terrebonne_garages_1954_map_city_fr.png">français</a></p>
<p><a href="derived/figures/terrebonne_garages_1954_map_underwriters_en.png"><img src="derived/figures/terrebonne_garages_1954_map_underwriters_en.png" alt="The same markers on the 1954–55 fire-insurance sheets, georeferenced and straightened along the street"></a></p>
<p class="muted">The same markers on the 1954–55 sheets, georeferenced on the City's géobase and straightened along the street; the blank in the fourth panel is the missing sheet 787-8. <a href="derived/figures/terrebonne_garages_1954_map_underwriters_en.pdf">PDF</a> · <a href="derived/figures/terrebonne_garages_1954_map_underwriters_fr.png">français</a></p>
<h2>By block face</h2>
<details open><summary>Residential buildings addressed on Terrebonne, by sheet and block face</summary>
<table><thead><tr><th>Side</th><th>Sheet</th><th>Block face</th><th>Buildings</th><th>Garage</th><th>Share</th></tr></thead><tbody>{by_html}</tbody></table></details>
<h2>Caveats</h2>
<ul><li><strong>Garages, not driveways.</strong> A driveway or parking pad without a garage leaves no mark on the plans; the figure is a lower bound for "driveway or garage as built".</li>
<li><strong>As built, not as used.</strong> The 1954–55 figure counts structures; the present-day reading sees aprons, driveways and parked vehicles from above but not what a garage holds inside (a workshop, storage, living space). Neither is the share of households that park off-street today. A garage of 1930 or 1950 may also be too small for a large vehicle of today.</li>
<li><strong>Buildings, not households.</strong> A duplex pair has two to four flats and one or two garages; three of the four apartment buildings have a basement garage of unrecorded capacity. The share by dwelling ({R['pct_dwellings']:.0f} %) happens to match the share by building.</li>
<li><strong>One sheet missing</strong> (787-8, south side between Hampton and Melrose) and {sum(r['confidence']=='medium' for r in rows if r['addressed_on']=='Terrebonne')} readings graded medium, noted row by row in the table.</li></ul>
<h2>Method and files</h2>
<p>One row per building read on the scans (<a href="derived/buildings_1954.csv">buildings_1954.csv</a>); each sheet fitted to the City's géobase by its Terrebonne intersections (<a href="derived/controls.csv">controls.csv</a>, <code>georef.py</code>; residuals 0–4 m) and checked against the City's parcels; each row joined to the City's assessment roll by civic number and street, or by position for corner buildings renumbered since 1954 (<code>buildings.py</code> → <a href="derived/buildings_geo.csv">buildings_geo.csv</a>, with dwellings and year of construction); the present-day reading on the Québec government's aerial imagery rendered block by block with the parcels overlaid (<code>ortho_strips_qc.py</code>; the imagery is served, not redistributed), recorded in <a href="derived/present_day_check.csv">present_day_check.csv</a> and joined by <code>merge_present_day.py</code>; maps by <code>maps.py</code>; this page and the note by <code>build_note.py</code>. The scans themselves are not reproduced in the repository (see the folder's README on their status); the City data are CC-BY 4.0.</p>
<p class="muted">The author is a resident of Côte-des-Neiges–Notre-Dame-de-Grâce; counts and positions are the author's reading and may contain errors, which the row-by-row table is meant to let anyone find.</p>
</main></body></html>"""
open(os.path.join(ROOT, 'index.html'), 'w').write(page)
print('note and page built', STAMP)
