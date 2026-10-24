#!/usr/bin/env python3
"""Shared helpers for the evidence graph: load the CSVs, validate the structure, write the SQLite query copy.

nodes.csv, edges.csv and questions.csv are the source of truth. evidence_graph.sqlite is a generated copy for queries
(git-ignored, rewritten at every render and by query_graph.py when the CSVs are newer); never edit it.
"""
import csv, os, re, sqlite3
HERE = os.path.dirname(os.path.abspath(__file__))
NODES, EDGES, QUESTIONS = (os.path.join(HERE, f) for f in ('nodes.csv', 'edges.csv', 'questions.csv'))
SQLITE = os.path.join(HERE, 'evidence_graph.sqlite')
NODE_TYPES = ('agent', 'document', 'data', 'numerical assertion', 'assertion', 'statement', 'event')
# the closed list of relations (README, « What it is »)
RELATIONS = ('attributed_to', 'contained_in', 'released_in', 'withheld_in', 'redacted_in', 'summarized_in', 'precedes', 'implements',
             'computed_from', 'states', 'matches', 'refers_to', 'echoes', 'sets_aside', 'made_at', 'supports', 'undercuts', 'bears_on',
             'same_day', 'does_not_include', 'unsupported_by', 'differs_from', 'same_data_other_denominator')
NOTE_REQUIRED = ('differs_from', 'unsupported_by', 'does_not_include', 'same_data_other_denominator')


def read_csv(path):
    with open(path, encoding='utf-8', newline='') as f:
        r = csv.DictReader(f)
        return r.fieldnames, list(r)


def load():
    _, nodes = read_csv(NODES)
    _, edges = read_csv(EDGES)
    questions = read_csv(QUESTIONS)[1] if os.path.exists(QUESTIONS) else []
    return nodes, edges, questions


def time_secs(node):
    """Seconds into the recording: the `time` column (H:MM:SS or M:SS), else the &t=…s of a YouTube link, else None."""
    t = (node.get('time') or '').strip()
    m = re.fullmatch(r'(?:(\d+):)?(\d{1,2}):(\d\d)', t)
    if m:
        return int(m.group(1) or 0) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    m = re.search(r'youtube\.com/watch\?v=[\w-]+&t=(\d+)s', node.get('url') or '')
    return int(m.group(1)) if m else None


def validate(nodes, edges, questions):
    """Structural checks; returns the list of problems (empty = clean)."""
    ids = {n['id'] for n in nodes}
    q_nodes = set()
    for q in questions:
        q_nodes |= {x.strip() for x in q['nodes'].split(';') if x.strip()}
    out_rel, in_rel, deg = {}, {}, {n['id']: 0 for n in nodes}
    problems = []
    for e in edges:
        if e['from'] not in ids or e['to'] not in ids:
            problems.append(f"edge to unknown node: {e['from']} -> {e['to']}"); continue
        out_rel.setdefault(e['from'], set()).add(e['relation']); in_rel.setdefault(e['to'], set()).add(e['relation'])
        deg[e['from']] += 1; deg[e['to']] += 1
    for n in nodes:
        o = out_rel.get(n['id'], set()); i = in_rel.get(n['id'], set()); t = n['type']
        if deg[n['id']] == 0: problems.append(f"orphan: {n['id']}")
        if t == 'statement':
            if 'made_at' not in o: problems.append(f"statement without made_at: {n['id']}")
            if 'attributed_to' not in o: problems.append(f"statement without attributed_to: {n['id']}")
            if not n['source']: problems.append(f"statement without source: {n['id']}")
        if t == 'numerical assertion' and 'computed_from' not in o: problems.append(f"numerical assertion without computed_from: {n['id']}")
        if t == 'assertion':
            if not (i & {'states', 'supports', 'undercuts', 'bears_on'}): problems.append(f"assertion without evidence: {n['id']}")
            if n['id'] not in q_nodes: problems.append(f"assertion not attached to a question: {n['id']}")
        if t == 'document' and n['source'].startswith('2026-581') and not (o & {'released_in', 'withheld_in', 'redacted_in', 'contained_in'}) and n['id'] != 'd_release':
            problems.append(f"document without release status: {n['id']}")
        if t == 'data' and not n['source']: problems.append(f"data without source: {n['id']}")
        if t in ('statement', 'document', 'data', 'event') and not n['date']: problems.append(f"undated {t}: {n['id']}")
        if t not in NODE_TYPES: problems.append(f"unknown node type « {t} »: {n['id']}")
        if (n.get('time') or '').strip() and time_secs({'time': n['time']}) is None: problems.append(f"time not H:MM:SS: {n['id']}")
    seen_ids = set()
    for n in nodes:
        if n['id'] in seen_ids: problems.append(f"duplicate node id: {n['id']}")
        seen_ids.add(n['id'])
    seen = set()
    for e in edges:
        k = (e['from'], e['to'], e['relation'])
        if k in seen: problems.append(f"duplicate edge: {e['from']} -{e['relation']}-> {e['to']}")
        seen.add(k)
        if e['relation'] not in RELATIONS: problems.append(f"unknown relation « {e['relation']} »: {e['from']} -> {e['to']}")
        if e['relation'] in NOTE_REQUIRED and not e.get('note'):
            problems.append(f"difference without note: {e['from']} -> {e['to']}")
    for q in questions:
        for nid in [x.strip() for x in q['nodes'].split(';') if x.strip()]:
            if nid not in ids: problems.append(f"question {q['question']} cites unknown node: {nid}")
        if not q['nodes'].strip(): problems.append(f"question {q['question']} has no nodes")
    return problems


def write_report(nodes, edges, problems):
    with open(os.path.join(HERE, 'validation_report.txt'), 'w', encoding='utf-8') as f:
        f.write(f"{len(nodes)} nodes, {len(edges)} edges; {len(problems)} problem(s)\n" + '\n'.join(problems) + '\n')


def write_sqlite(nodes, edges, questions, path=SQLITE):
    """Write the query copy: tables nodes (CSV columns + time_s), edges (+ row = line order in edges.csv), questions, question_nodes."""
    tmp = path + '.tmp'
    if os.path.exists(tmp): os.remove(tmp)
    db = sqlite3.connect(tmp)
    cols = list(nodes[0].keys()) if nodes else ['id']
    db.execute('CREATE TABLE nodes (' + ', '.join(f'"{c}" TEXT' + (' PRIMARY KEY' if c == 'id' else '') for c in cols) + ', time_s INTEGER)')
    db.executemany(f'INSERT INTO nodes VALUES ({", ".join("?" * (len(cols) + 1))})', [[n.get(c, '') for c in cols] + [time_secs(n)] for n in nodes])
    db.execute('CREATE TABLE edges (row INTEGER PRIMARY KEY, "from" TEXT, "to" TEXT, relation TEXT, note TEXT, url TEXT)')
    db.executemany('INSERT INTO edges VALUES (?,?,?,?,?,?)', [(i + 1, e['from'], e['to'], e['relation'], e.get('note', ''), e.get('url', '') or '') for i, e in enumerate(edges)])
    db.execute('CREATE TABLE questions (question TEXT PRIMARY KEY, title TEXT)')
    db.execute('CREATE TABLE question_nodes (question TEXT, node TEXT, pos INTEGER)')
    for q in questions:
        db.execute('INSERT INTO questions VALUES (?,?)', (q['question'], q['title']))
        db.executemany('INSERT INTO question_nodes VALUES (?,?,?)', [(q['question'], x.strip(), k) for k, x in enumerate(q['nodes'].split(';')) if x.strip()])
    db.execute('CREATE INDEX edges_from ON edges ("from")'); db.execute('CREATE INDEX edges_to ON edges ("to")')
    db.commit(); db.close()
    os.replace(tmp, path)
    return path
