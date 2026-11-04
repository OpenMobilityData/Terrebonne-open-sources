#!/usr/bin/env python3
"""Two petitions on the Terrebonne bike lane, what is on record (public version, Nov 4, 2026): page 1, the comparison table;
page 2, the two petitions by signers per 1,000 residents on one shared set of cells. Inputs: the public 2025-081 derived tables
(Terrebonne-access-requests) and the 2026 petition's aggregate counts (petition_counts_interim.json/.txt and the by-distance table,
written by the private pipeline from the signer list, which is not public; only aggregates are read here) and the shared-cell map
PNG (scripts/petition_2026_map_merged.py in the private repository, copied beside this script as map_script_copy.py; it needs the
DMTI CanMap polygon cache and the signer list). Run: python3 build.py
"""
import csv, json, os, re, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); PRV = os.path.expanduser('~/GitHub/Terrebonne-private')
D = os.path.expanduser('~/Terrebonne-data/petition-2026'); R = os.path.expanduser('~/GitHub/Terrebonne-access-requests/2025-081/derived')
pet = json.load(open(os.path.join(D, 'petition_counts_interim.json'))); txt = open(os.path.join(D, 'petition_counts_interim.txt'), encoding='utf-8').read()
g = lambda l: int(re.search(re.escape(l) + r':\s*(\d+)', txt).group(1))
rest26, out26 = g('outside CDN-NDG, in the City'), g('outside the City'); np26 = pet['unique_signers'] - pet['in_cdn_ndg'] - rest26 - out26
rd = lambda p: {r[list(r)[0]]: r for r in csv.DictReader(open(p, encoding='utf-8'))}
d24 = rd(os.path.join(R, 'petition_signatures_by_district.csv')); s24 = rd(os.path.join(R, 'petition_signatures_by_distance.csv')); f24 = rd(os.path.join(R, 'petition_filter_levels.csv'))
s26 = rd(os.path.join(PRV, 'figs', 'petition-2026', 'petition_2026_by_distance_interim.csv'))
MAP = os.path.join(HERE, 'figures', 'maps', 'petition_compare_2024_2026_percapita_2026-11-02.png')
import shutil; shutil.copy(os.path.join(PRV, 'figs', 'petition-2026', 'petition_compare_2024_2026_percapita_interim.png'), MAP)
shutil.copy(os.path.expanduser('~/Terrebonne-data/petition-2026/petition_2024_2026_shared_cells_interim.csv'), os.path.join(HERE, 'petitions_shared_cells_2026-11-02.csv'))
shutil.copy(os.path.join(PRV, 'scripts', 'petition_2026_map_merged.py'), os.path.join(HERE, 'map_script_copy.py'))
def band(tab, keys): return sum(int(tab[k]['entries']) for k in keys)
geo24 = int(s24['geocoded total']['entries']); geo26 = int(s26['geocoded total']['entries'])
B = ['within 100 m of the lane', '100 to 250 m', '250 to 500 m', '500 m to 1 km', '1 to 2 km', 'beyond 2 km']
def cum(tab, n): return band(tab, B[:n])
def pc(n, d): return f'{100 * n / d:.0f}\\,\\%'
stamp = re.search(r'_(\d{4}-\d{2}-\d{2}-\d{2}-\d{2})\.csv$', pet['export']).group(1)
import datetime as _dt, zoneinfo as _zi
_utc = _dt.datetime.strptime(stamp, '%Y-%m-%d-%H-%M').replace(tzinfo=_dt.timezone.utc).astimezone(_zi.ZoneInfo('America/Toronto'))
local_stamp = _utc.strftime('%B %-d, %Y, %-H:%M') + ' (Montréal time)'
esc = lambda s: s.replace('&', '\\&').replace('%', '\\%').replace('–', '--')
def row(label, a, b, bold=False):
    f = (lambda x: '\\textbf{%s}' % x) if bold else (lambda x: x)
    return f'{f(esc(label))} & {f(a)} & {f(b)} \\\\'
N = lambda n: f'{n:,}'
dist24 = d24; by26 = pet['by_district']
rows = [
 r'\textbf{What is compared} & \textbf{2024 petition against the bike lane} & \textbf{2026 petition for the year-round lane} \\ \midrule',
 row('Object', 'against the reconfiguration of Terrebonne and the bike lanes (organizers\' letters, Feb. 2, 2024)', '« Gardons la piste Terrebonne toute l\'année pour la sécurité de nos enfants » (APC-NDG)'),
 row('Filed', 'tabled for the sitting of Feb. 5, 2024, the day council approved the project (CA24 170018, 3--2)', 'launched Oct. 21, 2026; handed over at the sitting of Nov. 2, 2026'),
 row('Source of the figures', 'the scan released by the borough on March 6, 2025 under access request 2025-081 (names, signatures, addresses blacked out; postal codes legible)', f'Action Network export of {local_stamp} and the paper sheets, transcribed'),
 r'\midrule',
 row('Days run, first signature to hand-over', '24: first online signature Jan. 12, 2024, tabled Feb. 5 (the paper sheets\' start date is not on record)', f"{pet['days_since_launch']}: launched Oct. 21, 2026, handed over Nov. 2"),
 row('Claimed by the organizers', '1,138 (796 on paper + 342 online) in the letter of Feb. 2; « 1,258 » in a supplement e-mailed Feb. 5', f"{N(pet['unique_signers'])} ({N(pet['online'])} online + {N(pet['paper'])} on paper)"),
 row('Lines on file', f"{N(int(f24['1 total lines (counter stamps)']['both']))} ({N(int(f24['1 total lines (counter stamps)']['handwritten']))} handwritten + {N(int(f24['1 total lines (counter stamps)']['online']))} online printout)", f"{N(pet['unique_signers'])} signers, the figure of the letter filed with the clerk (from {N(pet['submissions'])} rows before repeats were removed: {N(pet['submissions'] - pet['paper'])} online submissions and {N(pet['paper'] + 37)} paper rows)"),
 row('Counted once?', 'not checkable: names and addresses are blacked out; every line counted', f"yes: same e-mail and name = one signer ({pet['repeats']} online repeats; 37 paper rows that were re-sends removed)"),
 row('Located on the map (postal code, or street address)', f"{N(int(f24['4 well-formed full code']['both']))} full postal codes ({N(int(f24['4 well-formed full code']['handwritten']))} + {N(int(f24['4 well-formed full code']['online']))}); {N(geo24)} located", f"{N(pet['unique_signers'] - np26)} located ({N(geo26)} by postal code, {N(pet['paper_pc_inferred'])} by street address); {N(np26)} could not be located"),
 r'\midrule',
 row('Live in CDN--NDG', f"{N(int(d24['CDN-NDG (all districts)']['entries']))} ({pc(int(d24['CDN-NDG (all districts)']['entries']), geo24)} of those located)", f"{N(pet['in_cdn_ndg'])} ({pc(pet['in_cdn_ndg'], pet['unique_signers'] - np26)} of those located)", True),
 row('\\quad Notre-Dame-de-Grâce district', N(int(d24['CDN-NDG: Notre-Dame-de-Grâce']['entries'])), N(by26['Notre-Dame-de-Grâce'])),
 row('\\quad Loyola district', N(int(d24['CDN-NDG: Loyola']['entries'])), N(by26['Loyola'])),
 row('\\quad Snowdon, Côte-des-Neiges, Darlington', f"{int(d24['CDN-NDG: Snowdon']['entries'])}, {int(d24['CDN-NDG: Côte-des-Neiges']['entries'])}, {int(d24['CDN-NDG: Darlington']['entries'])}", f"{by26['Snowdon']}, {by26['Côte-des-Neiges']}, {by26['Darlington']}"),
 row('Other Montréal boroughs', N(int(d24['other Montreal borough']['entries'])), N(rest26)),
 row('Outside the City of Montréal', N(int(d24['outside the City of Montreal']['entries'])), N(out26)),
 row('Could not be located', N(int(d24['not geocoded (code not found or misread)']['entries'])), N(np26)),
 r'\midrule',
 row('Within 100 m of the lane (postal-code point)', f"{N(cum(s24, 1))} ({pc(cum(s24, 1), geo24)})", f"{N(cum(s26, 1))} ({pc(cum(s26, 1), geo26)})"),
 row('Within 250 m', f"{N(cum(s24, 2))} ({pc(cum(s24, 2), geo24)})", f"{N(cum(s26, 2))} ({pc(cum(s26, 2), geo26)})"),
 row('Within 500 m', f"{N(cum(s24, 3))} ({pc(cum(s24, 3), geo24)})", f"{N(cum(s26, 3))} ({pc(cum(s26, 3), geo26)})"),
 row('Within 1 km', f"{N(cum(s24, 4))} ({pc(cum(s24, 4), geo24)})", f"{N(cum(s26, 4))} ({pc(cum(s26, 4), geo26)})"),
 row('Beyond 2 km', f"{N(band(s24, B[5:]))} ({pc(band(s24, B[5:]), geo24)})", f"{N(band(s26, B[5:]))} ({pc(band(s26, B[5:]), geo26)})"),
 row('On Terrebonne or within one block (Somerled--Monkland)', f"{N(int(f24['6 full code in the Terrebonne corridor']['both']))}", f"{N(pet['within_block'])} ({pet['within_block_on_terrebonne']} on Terrebonne)", True),
]
L = [r'\documentclass[10pt,letterpaper]{article}', r'\usepackage[T1]{fontenc}\usepackage[utf8]{inputenc}\usepackage[scaled=0.95]{helvet}\renewcommand{\familydefault}{\sfdefault}',
     r'\usepackage[letterpaper,top=0.6in,bottom=0.6in,left=0.7in,right=0.7in]{geometry}\usepackage{booktabs,array,graphicx,pdflscape}\pagestyle{empty}\setlength{\parindent}{0pt}\renewcommand{\arraystretch}{1.15}',
     r'\begin{document}', r'{\large\textbf{Two petitions on the Terrebonne bike lane: what is on record (as of November 2, 2026)}}\\[2pt]',
     r'The 2024 column is the petition against the 2024 project as the borough released it under access request 2025-081; the 2026 column is the petition « Gardons la piste Terrebonne toute l\textquoteright année » of the Association des piétons et cyclistes de NDG as handed over to the borough council on November 2, 2026, counted from its export and paper sheets. Figures by place come from the postal code\textquoteright s point and the City\textquoteright s 2025 district polygons in both cases. Page 2: the two petitions by signers per 1,000 residents on one set of cells.\\[6pt]',
     r'\small\begin{tabular}{@{}p{2.05in}p{2.35in}p{2.35in}@{}}\toprule', *rows, r'\bottomrule\end{tabular}\\[8pt]',
     r'\footnotesize\textbf{Reading the table.} The 2024 petition\textquoteright s located entries lie mostly beside the lane: 44\,\% within 100 m. The 2026 petition\textquoteright s signers are more numerous and more spread: three quarters live in the borough, 41\,\% within 500 m of the lane, a further quarter elsewhere in Montréal. The 2024 figures count lines as tabled, since the released scan does not allow repeats to be found; the 2026 figures count each person once. ' +
     r'The borough\textquoteright s release of March 6, 2025 is the material it held on file in opposition to the 2024 project; its organizers\textquoteright{} letter of February 2, 2024 counted 1,138 and a supplement of February 5 « 1,258 ». Sources: openmobilitydata.github.io/Terrebonne-access-requests/2025-081/ (the 2024 petition as released, with its derived tables); the 2026 petition\textquoteright s cover letter and signer list as filed with the clerk (the list is not public; the counts are the letter\textquoteright s). Built by openmobilitydata.github.io/Terrebonne-open-sources/2026-11-02-petitions-comparison/derived/build.py.',
     r'\newpage\begin{landscape}\noindent\includegraphics[width=\linewidth]{' + MAP + r'}\\[4pt]\footnotesize\textbf{The two petitions by signers per 1,000 residents, same cells.} Six-character postal codes merged into one set of cells until every cell holds at least 5 signers of each petition and at least 300 residents (Census 2021 dissemination-area populations apportioned to the postal-code polygons by area, an estimate); the fill is signers per 1,000 residents on the same scale in both panels, the label the count; cells too narrow to hold a label are unlabelled. The 2024 panel counts the 921 lines whose postal code falls in a borough polygon (orphan codes attached to the nearest polygon), the 2026 panel 1,047 signers. The cell table with both counts and rates: petitions\_shared\_cells\_2026-11-02.csv. Postal-code boundaries: DMTI Spatial Inc., CanMap Postal Code Suite v2024.3; districts and lane: Ville de Montréal (CC-BY); population: Statistics Canada, Census 2021 (Open Licence).\end{landscape}',
r'\end{document}']
tex = os.path.join(HERE, 'petitions_comparison_2026-11-02.tex'); open(tex, 'w', encoding='utf-8').write('\n'.join(L))
subprocess.run(['pdflatex', '-interaction=batchmode', '-output-directory', os.path.dirname(tex), tex], capture_output=True)
for e in ('.aux', '.log'):
    try: os.remove(tex[:-4] + e)
    except OSError: pass
pdf = tex[:-4] + '.pdf'; print(pdf, subprocess.run(['pdfinfo', pdf], capture_output=True, text=True).stdout.split('Pages:')[1].split()[0], 'page(s)')
