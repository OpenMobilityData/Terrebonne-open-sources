#!/usr/bin/env python3
"""Add to the evidence graph from the command line: a statement with its three standard relations, any other node, or one edge.
Writes nodes.csv / edges.csv (the source of truth) only when every check passes, then runs the validator.

  python3 graph_add.py statement --id s_x --short "Oct 6 (2:49:33): « … »" --label "Oct 6, the councillor, 2:49:33: « … »" \\
      --date 2026-10-06 --source "2026-10-06_08.md, 2:49:33" --url "https://www.youtube.com/watch?v=0k_KZf9uxTk&t=10173s" \\
      --speaker a_teodoresco --event e_oct6 --transcript d_transcript_oct6 [--time 2:49:33] [--lang fr] [--aliases "…"] \\
      [--edge RELATION:TARGET[:NOTE]] …
  python3 graph_add.py node --id d_x --type document --short … --label … --date … --source … [--url …] [--edge …] [--in RELATION:SOURCE[:NOTE]]
  python3 graph_add.py edge FROM TO RELATION [--note "…"] [--url "…"]
  add --dry-run to any command to see the rows without writing them; --allow-orphan (node, statement) accepts a new
  node with no relation yet, for a new agent whose first statement is added in the next command.

A statement gets attributed_to (speaker), made_at (event) and contained_in (transcript document) in the same command;
--time defaults to the &t=…s of a YouTube --url. Refused: an id already in nodes.csv, an unknown target or relation, an
edge already present (same from, to and relation), a difference relation (differs_from, unsupported_by, does_not_include,
same_data_other_denominator) without a note, and a statement or node whose additions would leave a validation problem
that was not there before. After writing, render_graph.py redraws the page (and the SQLite copy): run it before committing.
"""
import argparse, csv, re, sys
from graph_lib import NODES, EDGES, NODE_TYPES, RELATIONS, NOTE_REQUIRED, read_csv, load, validate, write_report


def fmt_time(s):
    h, r = divmod(s, 3600); m, sec = divmod(r, 60)
    return f'{h}:{m:02d}:{sec:02d}' if h else f'{m:02d}:{sec:02d}'


def parse_link(spec, flag):
    parts = spec.split(':', 2)
    if len(parts) < 2: sys.exit(f'{flag} expects RELATION:ID[:NOTE], got « {spec} »')
    return parts[0], parts[1], parts[2] if len(parts) == 3 else ''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('statement', 'node'):
        p = sub.add_parser(name)
        p.add_argument('--id', required=True); p.add_argument('--short', required=True); p.add_argument('--label', required=True)
        p.add_argument('--date', default=''); p.add_argument('--source', default=''); p.add_argument('--url', default='')
        p.add_argument('--aliases', default=''); p.add_argument('--time', default=''); p.add_argument('--lang', default='')
        p.add_argument('--edge', action='append', default=[], metavar='RELATION:TARGET[:NOTE]', help='an outgoing edge (repeatable)')
        p.add_argument('--in', dest='inc', action='append', default=[], metavar='RELATION:SOURCE[:NOTE]', help='an incoming edge (repeatable)')
        p.add_argument('--dry-run', action='store_true')
        p.add_argument('--allow-orphan', action='store_true', help='accept the new node as an orphan for now (e.g. a new agent whose statement is added next)')
        if name == 'statement':
            p.add_argument('--speaker', required=True, help='agent id (attributed_to)')
            p.add_argument('--event', required=True, help='event id: the sitting, interview or meeting (made_at)')
            p.add_argument('--transcript', required=True, help='document id of the transcript (contained_in)')
        else:
            p.add_argument('--type', required=True, choices=NODE_TYPES)
    p = sub.add_parser('edge')
    p.add_argument('src'); p.add_argument('dst'); p.add_argument('relation')
    p.add_argument('--note', default=''); p.add_argument('--url', default=''); p.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    nfields, _ = read_csv(NODES); efields, _ = read_csv(EDGES)
    nodes, edges, questions = load()
    ids = {n['id']: n for n in nodes}
    before = set(validate(nodes, edges, questions))
    errors, new_nodes, new_edges = [], [], []

    if a.cmd in ('statement', 'node'):
        if a.id in ids: errors.append(f'id already in nodes.csv: {a.id} ({ids[a.id]["type"]}: {ids[a.id]["short"]})')
        if not re.fullmatch(r'[a-z][a-z0-9_]*', a.id): errors.append(f'id must be lower-case letters, digits and underscores: {a.id}')
        if a.date and not re.fullmatch(r'\d{4}(-\d\d){0,2}', a.date): errors.append(f'date must be YYYY, YYYY-MM or YYYY-MM-DD: {a.date}')
        t = a.time
        if not t:
            m = re.search(r'youtube\.com/watch\?v=[\w-]+&t=(\d+)s', a.url)
            if m: t = fmt_time(int(m.group(1)))
        if t and not re.fullmatch(r'(?:\d+:)?\d{1,2}:\d\d', t): errors.append(f'time must be H:MM:SS or MM:SS: {t}')
        row = {k: '' for k in nfields}
        row.update(id=a.id, type='statement' if a.cmd == 'statement' else a.type, short=a.short, label=a.label, date=a.date,
                   source=a.source, aliases=a.aliases, url=a.url)
        if 'time' in row: row['time'] = t
        if 'lang' in row: row['lang'] = a.lang
        new_nodes.append(row)
        links = []
        if a.cmd == 'statement':
            for rel, dst, want in (('attributed_to', a.speaker, 'agent'), ('made_at', a.event, 'event'), ('contained_in', a.transcript, 'document')):
                if dst in ids and ids[dst]['type'] != want:
                    errors.append(f'{rel} target {dst} is of type « {ids[dst]["type"]} », expected « {want} »')
                links.append((a.id, dst, rel, ''))
        links += [(a.id, d, r, nt) for r, d, nt in (parse_link(s, '--edge') for s in a.edge)]
        links += [(s_, a.id, r, nt) for r, s_, nt in (parse_link(s, '--in') for s in a.inc)]
        known = set(ids) | {a.id}
        for s_, d, r, nt in links:
            new_edges.append({'from': s_, 'to': d, 'relation': r, 'note': nt, 'url': ''})
    else:
        known = set(ids)
        new_edges.append({'from': a.src, 'to': a.dst, 'relation': a.relation, 'note': a.note, 'url': a.url})

    have = {(e['from'], e['to'], e['relation']) for e in edges}
    for e in new_edges:
        for end in ('from', 'to'):
            if e[end] not in known: errors.append(f'unknown node id: {e[end]}')
        if e['relation'] not in RELATIONS: errors.append(f'unknown relation « {e["relation"]} »; the closed list: {", ".join(RELATIONS)}')
        if e['relation'] in NOTE_REQUIRED and not e['note']: errors.append(f'{e["relation"]} needs a note stating the point of difference: {e["from"]} -> {e["to"]}')
        k = (e['from'], e['to'], e['relation'])
        if k in have: errors.append(f'edge already present: {e["from"]} -{e["relation"]}-> {e["to"]}')
        have.add(k)
        if e['from'] == e['to']: errors.append(f'edge from a node to itself: {e["from"]}')
    if not errors:
        after = validate(nodes + new_nodes, edges + new_edges, questions)
        added = [p for p in after if p not in before]
        if getattr(a, 'allow_orphan', False):
            added = [p for p in added if p != f'orphan: {a.id}']
        if added: errors += [f'would add a validation problem: {p}' for p in added]
    if errors:
        print('refused, nothing written:\n  ' + '\n  '.join(dict.fromkeys(errors)), file=sys.stderr); return 1

    w = csv.DictWriter(sys.stdout, fieldnames=nfields, lineterminator='\n')
    for r in new_nodes: print('node: ', end=''); w.writerow(r)
    w = csv.DictWriter(sys.stdout, fieldnames=efields, lineterminator='\n')
    for e in new_edges: print('edge: ', end=''); w.writerow({k: e.get(k, '') for k in efields})
    if a.dry_run:
        print('dry run: nothing written'); return 0
    # append with the files' own line ending (\r\n, as csv writes it), after making sure each file ends with one
    for path, fields, rows in ((NODES, nfields, new_nodes), (EDGES, efields, [{k: e.get(k, '') for k in efields} for e in new_edges])):
        if not rows: continue
        raw = open(path, 'rb').read()
        if raw and not raw.endswith(b'\n'):
            open(path, 'ab').write(b'\r\n')
        with open(path, 'a', encoding='utf-8', newline='') as f:
            csv.DictWriter(f, fieldnames=fields).writerows(rows)
    nodes, edges, questions = load()
    problems = validate(nodes, edges, questions); write_report(nodes, edges, problems)
    print(f'written; validation: {len(nodes)} nodes, {len(edges)} edges, {len(problems)} problem(s)' + (': ' + '; '.join(problems) if problems else ''))
    print('next: python3 render_graph.py (page, drawings and the SQLite copy)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
