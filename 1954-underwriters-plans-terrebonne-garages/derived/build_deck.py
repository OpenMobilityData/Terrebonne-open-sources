#!/usr/bin/env python3
"""Slide deck (beamer, 16:9) in English and French from summary.json, on_street_cars_by_block.csv
and the figures; each slide carries its own title, figure, one-line reading and source line so it
can stand alone as an image. Usage: python3 build_deck.py  (writes terrebonne_garages_deck_{en,fr}.pdf)"""
import csv, json, os, subprocess, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
S = json.load(open(os.path.join(HERE, 'summary.json'))); PD = S['present_day']; R = S['roll']
CARS = list(csv.DictReader(open(os.path.join(HERE, 'on_street_cars_by_block.csv'), encoding='utf-8')))
OC = {k: sum(int(r[k]) for r in CARS) for k in ('optical_N', 'optical_S', 'lidar_N', 'lidar_S', 'lidar_lots_N', 'lidar_lots_S', 'lidar_cross_street_within_block')}
OC['opt'] = OC['optical_N'] + OC['optical_S']; OC['lid'] = OC['lidar_N'] + OC['lidar_S']; OC['lots'] = OC['lidar_lots_N'] + OC['lidar_lots_S']
STAMP = datetime.datetime.now().strftime('%Y-%m-%d')
N, Y, P = S['buildings_terrebonne'], S['with_garage'], S['pct']
T = {'en': dict(
    title=r"Off-street parking on rue de Terrebonne", sub=r"What the 1954--55 fire-insurance plans, today's aerial imagery and the City's LiDAR show, building by building",
    author=r"Terrebonne-open-sources (a resident of Côte-des-Neiges--Notre-Dame-de-Grâce) \quad " + STAMP,
    src_plans=r"Source: Underwriters' Survey Bureau, Insurance plan of the city of Montreal, vol.~7, 1954--55 (BAnQ, notice 0000174390). Reading: the author, one row per building.",
    src_city=r"Base: Ville de Montréal open data, CC-BY 4.0 (géobase, assessment roll). Reading: the author.",
    src_img=r"Imagery: Gouvernement du Québec (Imagerie\_GQ, fetched Oct.~25, 2026). LiDAR: Ville de Montréal 2015, CC-BY 4.0.",
    s1t=f"{P:.0f}\\,\\% of the buildings on Terrebonne were built with a garage",
    s1b=[f"{N} residential buildings with a Terrebonne address, west end of the lane to Girouard, on the sixteen 1954--55 sheets available", f"{Y} were built with a garage (north side {S['side_N']['with_garage']} of {S['side_N']['buildings']}, south side {S['side_S']['with_garage']} of {S['side_S']['buildings']})", f"By dwellings (City roll): {R['dwellings_in_buildings_with_garage']} of {R['dwellings']}, {R['pct_dwellings']:.0f}\\,\\%", "The plans mark garages, not driveways: a lower bound for ``garage or driveway as built''"],
    s2t=f"Today, {PD['pct_either']:.0f}\\,\\% have a garage as built or a visible driveway",
    s2b=[f"{PD['checked']} buildings checked on the Québec government's aerial imagery (leaf-off, 8\\,cm per pixel, after June 2024)", f"{PD['driveway_or_apron_today']} show a driveway, paved apron or parking pad today ({PD['pct_driveway_today']:.0f}\\,\\%)", f"Garage as built \\emph{{or}} driveway today: {PD['garage_1954_or_driveway_today']} of {PD['checked']} ({PD['pct_either']:.0f}\\,\\%); by dwellings {PD['pct_dwellings_either']:.0f}\\,\\%", f"Of the 1954 garages, {PD['garage_1954_with_apron_today']} keep a visible apron, {PD['garage_1954_without_apron_today']} do not; {PD['no_garage_1954_with_driveway_today']} houses without a garage in 1954 have a driveway today", "What a garage holds inside cannot be seen from above"],
    s3t="Where the garages and driveways are, along the whole street", s3r="Dashed red: the side where the lane would become parking each winter under the proposal, as the councillor described it.",
    s4t="The 1954--55 plans, georeferenced: every garage is written ``Auto''", s4r="The frontage strips of the sheets, straightened along the street; one marker per building (the blank: sheet 787-8, missing from the series).",
    s5t="On today's parcels: garage as built and driveway today",
    s6t="Three sources, one frame", s6r="Aerial imagery (optical), the City's 2015 LiDAR as height above ground, and the 1954--55 sheets, all georeferenced into the same street frame.",
    s7t="One block in the three sources: Hingston to Hampton", s7r="Aprons and parked cars (optical); the same cars and the garages as 0.5--3.5\\,m objects (LiDAR, red squares = automatic car detections); the ``Autos Bast'' of 1954.",
    s8t="Cars parked on the street: two acquisitions, two moments",
    s8b=[f"Daytime, spring, after June 2024 (aerial imagery): {OC['opt']} cars on Terrebonne (north {OC['optical_N']}, south {OC['optical_S']})", f"Night, 2015, before the lane (City LiDAR, 00:00--04:00): {OC['lid']} cars on Terrebonne (north {OC['lidar_N']}, south {OC['lidar_S']}), {OC['lots']} on private lots within 45\\,m, {OC['lidar_cross_street_within_block']} on the cross streets", "Ten years and a redesign apart: each describes its moment, not a before-and-after"],
    s9t="Caveats", s9b=["Garages as built, not driveways: the 1954--55 share is a lower bound", "As built, as visible: neither reading sees inside a garage (workshop, storage, living space); a 1930 garage may be too small for today's vehicles", "Buildings, not households: a duplex pair has two to four flats and one or two garages", "One sheet missing in 1954--55 (south side, Hampton to Melrose); readings graded medium or unclear are flagged row by row", "Everything is in the table: one row per building, checkable by address"],
    s10t="Where to find it", s10b=[r"Web page, note, maps, tables: \url{https://openmobilitydata.github.io/Terrebonne-open-sources/1954-underwriters-plans-terrebonne-garages/}", r"The sheets themselves: BAnQ numérique, \url{https://collections.banq.qc.ca/ark:/52327/2244199}", r"Repository: \url{https://github.com/OpenMobilityData/Terrebonne-open-sources}"]),
 'fr': dict(
    title=r"Le stationnement hors rue sur la rue de Terrebonne", sub=r"Ce que montrent les plans d'assurance-incendie de 1954--1955, l'imagerie aérienne d'aujourd'hui et le LiDAR de la Ville, bâtiment par bâtiment",
    author=r"Terrebonne-open-sources (un résident de Côte-des-Neiges--Notre-Dame-de-Grâce) \quad " + STAMP,
    src_plans=r"Source\,: Underwriters' Survey Bureau, Insurance plan of the city of Montreal, vol.~7, 1954--1955 (BAnQ, notice 0000174390). Lecture\,: l'auteur, une ligne par bâtiment.",
    src_city=r"Fond\,: données ouvertes de la Ville de Montréal, CC-BY 4.0 (géobase, rôle d'évaluation). Lecture\,: l'auteur.",
    src_img=r"Imagerie\,: Gouvernement du Québec (Imagerie\_GQ, consultée le 25 oct. 2026). LiDAR\,: Ville de Montréal 2015, CC-BY 4.0.",
    s1t=f"{P:.0f}\\,\\% des bâtiments de la rue de Terrebonne ont été construits avec un garage",
    s1b=[f"{N} bâtiments résidentiels adressés sur Terrebonne, de l'extrémité ouest de la piste à Girouard, sur les seize feuillets disponibles de 1954--1955", f"{Y} construits avec un garage (côté nord {S['side_N']['with_garage']} sur {S['side_N']['buildings']}, côté sud {S['side_S']['with_garage']} sur {S['side_S']['buildings']})", f"Par logements (rôle de la Ville)\\,: {R['dwellings_in_buildings_with_garage']} sur {R['dwellings']}, {R['pct_dwellings']:.0f}\\,\\%", "Les plans marquent les garages, pas les entrées\\,: une borne inférieure pour «\\,garage ou entrée d'origine\\,»"],
    s2t=f"Aujourd'hui, {PD['pct_either']:.0f}\\,\\% ont un garage d'origine ou une entrée visible",
    s2b=[f"{PD['checked']} bâtiments vérifiés sur l'imagerie aérienne du Gouvernement du Québec (sans feuilles, 8\\,cm par pixel, après juin 2024)", f"{PD['driveway_or_apron_today']} montrent une entrée, une aire pavée ou une aire de stationnement ({PD['pct_driveway_today']:.0f}\\,\\%)", f"Garage d'origine \\emph{{ou}} entrée aujourd'hui\\,: {PD['garage_1954_or_driveway_today']} sur {PD['checked']} ({PD['pct_either']:.0f}\\,\\%); par logements {PD['pct_dwellings_either']:.0f}\\,\\%", f"Des garages de 1954, {PD['garage_1954_with_apron_today']} gardent une aire visible, {PD['garage_1954_without_apron_today']} non; {PD['no_garage_1954_with_driveway_today']} maisons sans garage en 1954 ont une entrée aujourd'hui", "Ce qu'un garage contient ne se voit pas du ciel"],
    s3t="Où sont les garages et les entrées, le long de toute la rue", s3r="Tirets rouges\\,: le côté où la piste deviendrait du stationnement chaque hiver selon la proposition, telle que décrite par le conseiller.",
    s4t="Les plans de 1954--1955, géoréférencés\\,: chaque garage porte le mot «\\,Auto\\,»", s4r="Les bandes de façade des feuillets, redressées le long de la rue; un repère par bâtiment (le blanc\\,: le feuillet 787-8, manquant).",
    s5t="Sur le cadastre d'aujourd'hui\\,: garage d'origine et entrée aujourd'hui",
    s6t="Trois sources, un même repère", s6r="Imagerie aérienne (optique), LiDAR 2015 de la Ville en hauteur au-dessus du sol, et feuillets de 1954--1955, tous géoréférencés dans le repère de la rue.",
    s7t="Un îlot dans les trois sources\\,: Hingston à Hampton", s7r="Aires pavées et voitures (optique); les mêmes voitures et les garages comme objets de 0,5--3,5\\,m (LiDAR, carrés rouges = détections automatiques); les «\\,Autos Bast\\,» de 1954.",
    s8t="Voitures stationnées dans la rue\\,: deux acquisitions, deux moments",
    s8b=[f"De jour, au printemps, après juin 2024 (imagerie)\\,: {OC['opt']} voitures sur Terrebonne (nord {OC['optical_N']}, sud {OC['optical_S']})", f"De nuit, en 2015, avant la piste (LiDAR, 0\\,h--4\\,h)\\,: {OC['lid']} voitures sur Terrebonne (nord {OC['lidar_N']}, sud {OC['lidar_S']}), {OC['lots']} sur les lots privés à moins de 45\\,m, {OC['lidar_cross_street_within_block']} sur les rues transversales", "Dix ans et un réaménagement d'écart\\,: chaque compte décrit son moment, pas un avant-après"],
    s9t="Réserves", s9b=["Garages d'origine, pas entrées\\,: la part de 1954--1955 est une borne inférieure", "D'origine, visible\\,: aucune lecture ne voit l'intérieur d'un garage (atelier, rangement, pièce habitable); un garage de 1930 peut être trop petit pour les véhicules d'aujourd'hui", "Bâtiments, pas ménages\\,: un duplex jumelé compte deux à quatre logements et un ou deux garages", "Un feuillet manquant en 1954--1955 (côté sud, Hampton à Melrose); les lectures de confiance moyenne ou incertaines sont signalées ligne par ligne", "Tout est dans le tableau\\,: une ligne par bâtiment, vérifiable par adresse"],
    s10t="Où trouver le tout", s10b=[r"Page web, note, cartes, tableaux\,: \url{https://openmobilitydata.github.io/Terrebonne-open-sources/1954-underwriters-plans-terrebonne-garages/}", r"Les feuillets eux-mêmes\,: BAnQ numérique, \url{https://collections.banq.qc.ca/ark:/52327/2244199}", r"Dépôt\,: \url{https://github.com/OpenMobilityData/Terrebonne-open-sources}"])}
def items(lst): return '\n'.join(r'\item ' + x for x in lst)
def deck(lang):
    t = T[lang]; L = lang
    def panels(stem, title, reading, src):
        return r"""\begin{frame}{""" + title + r"""}
\begin{center}\includegraphics[width=\textwidth]{figures/panels/""" + stem + "_" + L + r"""_p1.pdf}\\[1pt]\includegraphics[width=\textwidth]{figures/panels/""" + stem + "_" + L + r"""_p2.pdf}\\[1pt]\includegraphics[width=\textwidth]{figures/panels/""" + stem + "_" + L + r"""_p3.pdf}\end{center}
\vfill{\scriptsize """ + reading + r""" \textbf{(1/2)}}\\{\tiny """ + src + r"""}\end{frame}
\begin{frame}{""" + title + r"""}
\begin{center}\includegraphics[width=\textwidth]{figures/panels/""" + stem + "_" + L + r"""_p4.pdf}\\[1pt]\includegraphics[width=\textwidth]{figures/panels/""" + stem + "_" + L + r"""_p5.pdf}\\[3pt]\includegraphics[width=0.95\textwidth]{figures/panels/""" + stem + "_" + L + r"""_legend.pdf}\end{center}
\vfill{\scriptsize """ + reading + r""" \textbf{(2/2)}}\\{\tiny """ + src + r"""}\end{frame}
"""
    tex = r"""\documentclass[aspectratio=169,11pt]{beamer}
\usetheme{default}\usecolortheme{seagull}\setbeamertemplate{navigation symbols}{}\setbeamertemplate{footline}{\hfill\scriptsize\insertframenumber/\inserttotalframenumber\hspace{2mm}\vspace{1mm}}
\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage{lmodern}\usepackage{url}\usepackage{graphicx}
\setbeamerfont{frametitle}{size=\large,series=\bfseries}\setbeamercolor{frametitle}{fg=black}\setbeamertemplate{frametitle}{\vspace{2mm}\insertframetitle\par\vspace{1mm}\hrule}
\setbeamertemplate{itemize items}[circle]
\title{""" + t['title'] + r"""}\subtitle{""" + t['sub'] + r"""}\author{""" + t['author'] + r"""}\date{}
\begin{document}
\begin{frame}\titlepage\vfill{\tiny """ + t['src_plans'] + ' ' + t['src_img'] + r"""}\end{frame}
\begin{frame}{""" + t['s1t'] + r"""}\begin{columns}[T]\column{0.6\textwidth}\begin{itemize}""" + items(t['s1b']) + r"""\end{itemize}\column{0.38\textwidth}\centering\includegraphics[height=0.68\textheight]{figures/method_detail_hingston_hampton_""" + L + r""".png}\end{columns}\vfill{\tiny """ + t['src_plans'] + r"""}\end{frame}
\begin{frame}{""" + t['s2t'] + r"""}\begin{itemize}""" + items(t['s2b']) + r"""\end{itemize}\vfill{\tiny """ + t['src_img'] + ' ' + t['src_city'] + r"""}\end{frame}
\begin{frame}{""" + t['s3t'] + r"""}\begin{center}\includegraphics[height=0.72\textheight]{figures/terrebonne_garages_distribution_""" + L + r""".pdf}\end{center}\vfill{\scriptsize """ + t['s3r'] + r"""}\\{\tiny """ + t['src_plans'] + ' ' + t['src_img'] + r"""}\end{frame}
""" + panels('today', t['s5t'], t['s3r'], t['src_city'] + ' ' + t['src_img']) + panels('underwriters', t['s4t'], t['s4r'], t['src_plans']) + r"""
\begin{frame}{""" + t['s6t'] + r"""}\begin{center}\includegraphics[height=0.74\textheight]{figures/method_overview_""" + L + r""".png}\end{center}\vfill{\scriptsize """ + t['s6r'] + r"""}\\{\tiny """ + t['src_img'] + ' ' + t['src_plans'] + r"""}\end{frame}
\begin{frame}{""" + t['s7t'] + r"""}\begin{columns}[T]\column{0.42\textwidth}\centering\includegraphics[height=0.74\textheight]{figures/method_detail_hingston_hampton_""" + L + r""".png}\column{0.56\textwidth}{\small """ + t['s7r'] + r"""}\end{columns}\vfill{\tiny """ + t['src_img'] + ' ' + t['src_plans'] + r"""}\end{frame}
\begin{frame}{""" + t['s8t'] + r"""}\begin{columns}[T]\column{0.45\textwidth}\begin{itemize}""" + items(t['s8b']) + r"""\end{itemize}\column{0.55\textwidth}\includegraphics[width=\textwidth]{figures/terrebonne_on_street_cars_""" + L + r""".pdf}\end{columns}\vfill{\tiny """ + t['src_img'] + r"""}\end{frame}
\begin{frame}{""" + t['s9t'] + r"""}\begin{itemize}""" + items(t['s9b']) + r"""\end{itemize}\end{frame}
\begin{frame}{""" + t['s10t'] + r"""}\begin{itemize}""" + items(t['s10b']) + r"""\end{itemize}\vfill{\tiny """ + t['src_plans'] + ' ' + t['src_city'] + ' ' + t['src_img'] + r"""}\end{frame}
\end{document}
"""
    name = f'terrebonne_garages_deck_{L}'
    open(os.path.join(HERE, name + '.tex'), 'w', encoding='utf-8').write(tex)
    for _ in range(2): subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error', name + '.tex'], cwd=HERE, stdout=subprocess.DEVNULL)
    for ext in ('.aux', '.log', '.nav', '.out', '.snm', '.toc'):
        try: os.remove(os.path.join(HERE, name + ext))
        except FileNotFoundError: pass
    print('deck', L, os.path.exists(os.path.join(HERE, name + '.pdf')))
if __name__ == '__main__':
    deck('en'); deck('fr')
