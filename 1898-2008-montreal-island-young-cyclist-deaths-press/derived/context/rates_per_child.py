#!/usr/bin/env python3
"""The press record set against the number of children: deaths of cyclists under 15 on the island of Montréal per
decade (events.csv, one folder up; with the inferred rows and as printed) over the island's population aged 5 to 14 at
the censuses of that decade (children_island_by_census.csv).

Every death in the record's under-15 group is of a child aged 5 to 14, so 5 to 14 is the denominator.
Children of a decade = the mean of the island figures of the censuses that fall in it or bound it:
  1930s: 1931 and 1941      1940s: 1941 and 1951      1950s: 1951, 1956 and 1961      1960s: 1961, 1966, 1971
  1970s: 1971, 1976, 1981   1980s: 1981 and 1991      1990s: 1991 (no 1996 or 2001 by age)   2000s: 2006 (secondary)
1966 and 1971 are not printed for the island alone: island = « Île-de-Montréal et Île-Jésus » less the City of Laval
(a subtraction made here, flagged in the table). No island figure by age was found for 1921, so the 1920s have no rate.

A RATE HERE IS NOT A RISK: the numerator is what the digitized papers reported (later decades are a floor), and
nothing measures how much children cycled. The table shows what the count looks like per child, nothing more.

  python3 rates_per_child.py  ->  rates_per_child.md, rates_per_child.csv
"""
import csv, os, collections
H = os.path.dirname(os.path.abspath(__file__))
C = list(csv.DictReader(open(os.path.join(H, 'children_island_by_census.csv'), encoding='utf-8')))
def pop(year, cls, geo_has=''):
    r = [x for x in C if x['census_year'] == str(year) and x['geography_class'] == cls and x['age_group'].startswith('5-14') and geo_has.lower() in x['geography_as_printed'].lower()]
    assert len(r) == 1, (year, cls, geo_has, len(r)); return int(r[0]['population'])
isl = {y: pop(y, 'island') for y in (1931, 1941, 1951, 1956, 1961, 1976, 1981, 1991, 2006)}
for y in (1966, 1971): isl[y] = pop(y, 'island with Île-Jésus') - pop(y, 'other', 'laval')
USE = {'1930s': (1931, 1941), '1940s': (1941, 1951), '1950s': (1951, 1956, 1961), '1960s': (1961, 1966, 1971), '1970s': (1971, 1976, 1981),
       '1980s': (1981, 1991), '1990s': (1991,), '2000s': (2006,)}
ev = list(csv.DictReader(open(os.path.join(H, '..', 'events.csv'), encoding='utf-8')))
u = [e for e in ev if e['age_group'] in ('under 10', '10 to 14') and e['on_island_inferred'] == 'yes' and not e['listed_apart']]
n_all = collections.Counter(e['event_date'][:3] + '0s' for e in u); n_pr = collections.Counter(e['event_date'][:3] + '0s' for e in u if e['on_island'] == 'yes')
rows = []
for d in ('1910s', '1920s') + tuple(USE):
    if d in USE:
        ch = sum(isl[y] for y in USE[d]) / len(USE[d])
        rows.append([d, n_pr[d], n_all[d], f'{ch:,.0f}', ', '.join(str(y) + ('*' if y in (1966, 1971) else '') for y in USE[d]), f'{n_pr[d] / 10 / ch * 1e5:.2f}', f'{n_all[d] / 10 / ch * 1e5:.2f}'])
    else: rows.append([d, n_pr[d], n_all[d], 'not found', '', '', ''])
hdr = ['decade', 'deaths under 15, place as printed', 'with the inferred rows', 'children aged 5 to 14 on the island (mean of the censuses used)', 'censuses used', 'deaths per 100,000 children a year, as printed', 'with the inferred rows']
with open(os.path.join(H, 'rates_per_child.csv'), 'w', newline='', encoding='utf-8') as f: csv.writer(f).writerows([hdr] + rows)
L = ['# The press record per child (built by rates_per_child.py)', '',
     'Deaths of cyclists under 15 on the island of Montréal reported by the digitized papers, per decade, over the island\'s children aged 5 to 14. **Not a risk:** the numerator is a press record (the later decades are a floor) and nothing measures how much children cycled.', '',
     '| ' + ' | '.join(hdr) + ' |', '|---|' + '---:|' * 3 + '---|' + '---:|' * 2]
L += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
L += ['', '\\* island = « Île-de-Montréal et Île-Jésus » less the City of Laval (a subtraction; the census prints the two islands together in 1966 and 1971).', '',
      'Island, children aged 5 to 14 at each census: ' + '; '.join(f"{y}: {isl[y]:,}" + ('*' if y in (1966, 1971) else '') for y in sorted(isl)) + '. The 2006 figure is from a secondary source (the City\'s statistical yearbook).', '']
open(os.path.join(H, 'rates_per_child.md'), 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(L[4:]))
