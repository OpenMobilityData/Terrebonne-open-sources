#!/usr/bin/env python3
"""Meeting counts from documents.csv: how many meetings of each body, school year by school year, have posted minutes,
and how many of those minutes (or the meeting's agenda) mention Terrebonne or a bike lane.

A « mention » is any match of Terrebonne in the text other than the school's own letterhead address
(« 6440 rue Terrebonne », « 5870 de Terrebonne »), or of bike lane / bike path / piste cyclable
(columns terrebonne_mentions − address_only_mentions, and bike_lane_mentions, of documents.csv).
A meeting is a (body, meeting date) pair with at least one row other than an index page or an annual report;
« minutes_not_posted » rows are meetings shown by a calendar, an agenda, an annual report or a later document.

Writes meetings.csv (one row per meeting) and meeting_counts.csv (one row per body and school year), and prints
the counts as a Markdown table for the README. Run from the folder: python3 derived/build.py
"""
import collections, csv, os

D = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(os.path.join(D, 'documents.csv'), encoding='utf-8')))
MINUTES = ('minutes', 'special_minutes', 'aga_minutes')
AGENDA = ('agenda', 'special_agenda', 'aga_agenda')


def mention(x):
    n = lambda c: int(x[c] or 0)
    return n('terrebonne_mentions') - n('address_only_mentions') > 0 or n('bike_lane_mentions') > 0


M = {}
for x in rows:
    if x['doc_type'] in ('index_page', 'annual_report') or not x['meeting_date']:
        continue
    m = M.setdefault((x['body'], x['meeting_date']), {'body': x['body'], 'school_year': x['school_year'], 'meeting_date': x['meeting_date'],
                                                      'minutes_posted': 0, 'agenda_posted': 0, 'mention_in_minutes': 0, 'mention_in_agenda': 0})
    if x['doc_type'] in MINUTES:
        m['minutes_posted'] = 1; m['mention_in_minutes'] |= mention(x)
    if x['doc_type'] in AGENDA:
        m['agenda_posted'] = 1; m['mention_in_agenda'] |= mention(x)
meetings = sorted(M.values(), key=lambda m: (m['body'], m['meeting_date']))
with open(os.path.join(D, 'meetings.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(meetings[0])); w.writeheader(); w.writerows(meetings)

C = collections.OrderedDict()
for m in meetings:
    c = C.setdefault((m['body'], m['school_year']), collections.Counter())
    c['meetings'] += 1
    c['minutes_posted'] += m['minutes_posted']
    c['minutes_with_mention'] += m['mention_in_minutes']
    c['minutes_without_mention'] += m['minutes_posted'] and not m['mention_in_minutes']
    c['no_minutes_agenda_with_mention'] += (not m['minutes_posted']) and m['mention_in_agenda']
    c['meetings_with_mention'] += m['mention_in_minutes'] or m['mention_in_agenda']
FIELDS = ['meetings', 'minutes_posted', 'minutes_with_mention', 'minutes_without_mention', 'no_minutes_agenda_with_mention', 'meetings_with_mention']
with open(os.path.join(D, 'meeting_counts.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['body', 'school_year'] + FIELDS)
    for (b, y), c in C.items(): w.writerow([b, y] + [c[k] for k in FIELDS])

print('| Body | School year | Meetings | Minutes posted | Minutes with a mention | Minutes without | No minutes, agenda with a mention | Meetings with a mention |')
print('|---|---|---:|---:|---:|---:|---:|---:|')
tot = collections.defaultdict(collections.Counter)
for (b, y), c in C.items():
    print(f'| {b} | {y} | ' + ' | '.join(str(c[k]) for k in FIELDS) + ' |'); tot[b].update(c)
for b, c in tot.items():
    print(f'| **{b}** | **all** | ' + ' | '.join(f'**{c[k]}**' for k in FIELDS) + ' |')
