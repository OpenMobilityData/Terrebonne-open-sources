#!/usr/bin/env python3
"""How large a lane-related change would have to be to stand apart from the
year-to-year variation of the parish's figures: a detection threshold.

Noise: the standard deviation of the year-to-year percent changes observed before
the lane (2015–2023, eight changes), for the parish alone (design A) and for the
parish's change minus the median change of the twelve peer parishes (design B,
peer_comparison_long.csv). Two noise sets: all eight changes, and the five that
exclude the three COVID transitions (2019->20, 2020->21, 2021->22).
Threshold: two standard deviations (a change beyond it would be unusual at about
the 5 % level if changes were normal and independent; eight observations make
this a rough gauge, not a test). The lane covered seven of the twelve months of
2024, so a full-year lane effect shows in the 2024 return at 7/12 of its size:
the full-year effect detectable in 2024 is the threshold x 12/7. One full year
(the 2025 return) is detectable at the threshold itself; the mean of two full
years at the threshold / sqrt(2).
Outputs: detection_threshold.csv, detection_threshold_{en,fr}.tex (table), and the
sentence used in the abstract, detection_sentence_{en,fr}.tex.
"""
import csv, os, statistics as st, math
HERE = os.path.dirname(os.path.abspath(__file__))
long = list(csv.DictReader(open(os.path.join(HERE, 'peer_comparison_long.csv'), encoding='utf-8')))
SUB = '130341852RR0001'
peers = sorted({r['bn'] for r in long} - {SUB})
def v(bn, y, k): return float(next(r[k] for r in long if r['bn'] == bn and int(r['fiscal_year']) == y) or 0)
def pct(a, b): return 100 * (b / a - 1)
COVID = {2020, 2021, 2022}   # the year each transition lands on
YEARS = list(range(2015, 2024))
rows = []
for metric, key in (('gifts', 'gifts_4500_plus_4530'), ('revenue', 'line_4700')):
    own = {y + 1: pct(v(SUB, y, key), v(SUB, y + 1, key)) for y in YEARS[:-1]}
    dd = {y + 1: own[y + 1] - st.median(pct(v(b, y, key), v(b, y + 1, key)) for b in peers if v(b, y, key) > 0) for y in YEARS[:-1]}
    obs = {'A': pct(v(SUB, 2023, key), v(SUB, 2024, key)),
           'B': pct(v(SUB, 2023, key), v(SUB, 2024, key)) - st.median(pct(v(b, 2023, key), v(b, 2024, key)) for b in peers)}
    for design, series in (('A', own), ('B', dd)):
        for noise, keep in (('all', lambda y: True), ('excl_covid', lambda y: y not in COVID)):
            xs = [c for y, c in series.items() if keep(y)]
            sd = st.stdev(xs); thr = 2 * sd
            rows.append(dict(metric=metric, design=design, noise=noise, n=len(xs), sd=round(sd, 1), threshold_2sd=round(thr, 1),
                             full_year_effect_detectable_in_2024=round(thr * 12 / 7, 1), detectable_with_one_full_year=round(thr, 1),
                             detectable_with_two_full_years=round(thr / math.sqrt(2), 1), observed_2024=round(obs[design], 1)))
with open(os.path.join(HERE, 'detection_threshold.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
def g(metric, design, noise): return next(r for r in rows if r['metric'] == metric and r['design'] == design and r['noise'] == noise)
L = {'en': dict(metric={'gifts': 'Gifts (4500 + 4530)', 'revenue': 'Total revenue (4700)'}, design={'A': 'parish alone', 'B': 'parish minus peers\' median'},
                noise={'all': 'all eight pre-lane changes', 'excl_covid': 'excluding the three COVID transitions'},
                h=['Measure', 'Design', 'Noise set', '$n$', 'SD of changes (\\%)', 'Threshold, 2 SD (\\%)', 'Full-year effect detectable in 2024 (\\%)', 'With one full year (\\%)', 'With two full years (\\%)', 'Observed 2024 (\\%)']),
     'fr': dict(metric={'gifts': 'Dons (4500 + 4530)', 'revenue': 'Total des revenus (4700)'}, design={'A': 'paroisse seule', 'B': 'paroisse moins la médiane des voisines'},
                noise={'all': 'les huit variations d\'avant la piste', 'excl_covid': 'sans les trois transitions COVID'},
                h=['Mesure', 'Plan', 'Bruit', '$n$', 'ET des variations (\\%)', 'Seuil, 2 ET (\\%)', 'Effet annuel détectable en 2024 (\\%)', 'Avec une année complète (\\%)', 'Avec deux années complètes (\\%)', 'Observé 2024 (\\%)'])}
def num(x, lang): 
    s = f'{x:.0f}' if abs(x) >= 10 else f'{x:.1f}'
    return s.replace('.', ',') if lang == 'fr' else s
for lang in ('en', 'fr'):
    t = L[lang]
    with open(os.path.join(HERE, f'detection_threshold_{lang}.tex'), 'w', encoding='utf-8') as f:
        f.write('\\begin{tabular}{@{}lllrrrrrrr@{}}\\toprule\n' + ' & '.join(t['h']) + ' \\\\\\midrule\n')
        for r in rows:
            f.write(' & '.join([t['metric'][r['metric']], t['design'][r['design']], t['noise'][r['noise']], str(r['n'])] + [num(r[k], lang) for k in ('sd', 'threshold_2sd', 'full_year_effect_detectable_in_2024', 'detectable_with_one_full_year', 'detectable_with_two_full_years')] + [('$-$' if r['observed_2024'] < 0 else '') + num(abs(r['observed_2024']), lang)]) + ' \\\\\n')
        f.write('\\bottomrule\\end{tabular}\n')
    gA, gAx, gB, gBx = g('gifts', 'A', 'all'), g('gifts', 'A', 'excl_covid'), g('gifts', 'B', 'all'), g('gifts', 'B', 'excl_covid')
    rA, rAx, rB, rBx = g('revenue', 'A', 'all'), g('revenue', 'A', 'excl_covid'), g('revenue', 'B', 'all'), g('revenue', 'B', 'excl_covid')
    if lang == 'en':
        sent = (f"Given the year-to-year variation observed from 2015 to 2023, this record cannot be expected to detect a lane-related change in the parish's gifts smaller than about {num(gAx['threshold_2sd'],lang)} to {num(gA['threshold_2sd'],lang)}~\\% of a year's gifts against the parish's own history, or about {num(gBx['threshold_2sd'],lang)} to {num(gB['threshold_2sd'],lang)} points against the median change of the twelve neighbouring parishes (two standard deviations of the pre-lane changes, the lower figure excluding the three COVID transitions; section~\\ref{{sec:threshold}}). Because the lane covered seven of the twelve months of 2024, a lane effect would have had to remove about {num(gBx['full_year_effect_detectable_in_2024'],lang)} to {num(gA['full_year_effect_detectable_in_2024'],lang)}~\\% of the parish's full-year gifts, and about {num(rAx['full_year_effect_detectable_in_2024'],lang)} to {num(rA['full_year_effect_detectable_in_2024'],lang)}~\\% of its total revenue, to stand apart in the 2024 return; the observed 2024 changes ({'$-$' if gA['observed_2024']<0 else ''}{num(abs(gA['observed_2024']),lang)}~\\% on gifts, {'$-$' if gB['observed_2024']<0 else ''}{num(abs(gB['observed_2024']),lang)} points against the peers) are well inside those thresholds. The 2025 return, a full year, would lower the threshold to about {num(gBx['detectable_with_one_full_year'],lang)} to {num(gA['detectable_with_one_full_year'],lang)}~\\% of gifts, and two full years to about {num(gBx['detectable_with_two_full_years'],lang)} to {num(gA['detectable_with_two_full_years'],lang)}~\\%.")
    else:
        sent = (f"Compte tenu de la variation d'une année à l'autre observée de 2015 à 2023, on ne peut attendre de ce dossier qu'il détecte un changement lié à la piste dans les dons de la paroisse inférieur à environ {num(gAx['threshold_2sd'],lang)} à {num(gA['threshold_2sd'],lang)}~\\% des dons d'une année contre l'histoire de la paroisse elle-même, ou à environ {num(gBx['threshold_2sd'],lang)} à {num(gB['threshold_2sd'],lang)} points contre la variation médiane des douze paroisses voisines (deux écarts-types des variations d'avant la piste, le chiffre le plus bas sans les trois transitions COVID~; section~\\ref{{sec:threshold}}). Comme la piste a couvert sept des douze mois de 2024, un effet de la piste aurait dû retrancher environ {num(gBx['full_year_effect_detectable_in_2024'],lang)} à {num(gA['full_year_effect_detectable_in_2024'],lang)}~\\% des dons annuels de la paroisse, et environ {num(rAx['full_year_effect_detectable_in_2024'],lang)} à {num(rA['full_year_effect_detectable_in_2024'],lang)}~\\% de ses revenus totaux, pour se détacher dans la déclaration de 2024~; les variations observées en 2024 ({'$-$' if gA['observed_2024']<0 else ''}{num(abs(gA['observed_2024']),lang)}~\\% sur les dons, {'$-$' if gB['observed_2024']<0 else ''}{num(abs(gB['observed_2024']),lang)} points contre les voisines) sont bien en deçà de ces seuils. La déclaration de 2025, une année complète, abaisserait le seuil à environ {num(gBx['detectable_with_one_full_year'],lang)} à {num(gA['detectable_with_one_full_year'],lang)}~\\% des dons, et deux années complètes à environ {num(gBx['detectable_with_two_full_years'],lang)} à {num(gA['detectable_with_two_full_years'],lang)}~\\%.")
    open(os.path.join(HERE, f'detection_sentence_{lang}.tex'), 'w', encoding='utf-8').write(sent + '\n')
    if lang == 'en': print(sent)
print('\n'.join(f"{r['metric']:8} {r['design']} {r['noise']:11} n={r['n']} SD {r['sd']:5} thr {r['threshold_2sd']:5} 2024full {r['full_year_effect_detectable_in_2024']:5} 1y {r['detectable_with_one_full_year']:5} 2y {r['detectable_with_two_full_years']:5} obs {r['observed_2024']}" for r in rows))
