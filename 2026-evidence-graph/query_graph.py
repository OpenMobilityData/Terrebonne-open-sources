#!/usr/bin/env python3
"""Run a saved query (queries/<name>.sql) against the SQLite copy of the evidence graph.

Usage:
  python3 query_graph.py                          list the saved queries
  python3 query_graph.py <name> [value | key=value ...] [--csv] [--full]
  python3 query_graph.py --sql "SELECT …"         an ad hoc query
Examples:
  python3 query_graph.py assertion x_done_deal
  python3 query_graph.py statements_by_agent agent=Teodoresco
  python3 query_graph.py sitting e_oct6
  python3 query_graph.py question 3.2
A query's parameters are its :names; one left out is NULL (the query then shows everything). A single bare value goes
to a query's only parameter. The copy (evidence_graph.sqlite) is rebuilt first when the CSVs are newer; it is never
the source of truth. --csv writes CSV to stdout; otherwise a table with cells cut at 60 characters (--full: uncut).
"""
import csv, os, re, sqlite3, sys
from graph_lib import HERE, SQLITE, NODES, EDGES, QUESTIONS, load, write_sqlite

QDIR = os.path.join(HERE, 'queries')


def fresh_db():
    srcs = [p for p in (NODES, EDGES, QUESTIONS, os.path.join(HERE, 'graph_lib.py')) if os.path.exists(p)]
    if not os.path.exists(SQLITE) or os.path.getmtime(SQLITE) < max(os.path.getmtime(p) for p in srcs):
        write_sqlite(*load())
    return sqlite3.connect(f'file:{SQLITE}?mode=ro', uri=True)


def saved():
    out = {}
    for f in sorted(os.listdir(QDIR)):
        if f.endswith('.sql'):
            text = open(os.path.join(QDIR, f), encoding='utf-8').read()
            first = text.splitlines()[0] if text else ''
            out[f[:-4]] = (text, first[2:].strip() if first.startswith('--') else '')
    return out


def table(cols, rows, full):
    cut = (lambda s: s) if full else (lambda s: s if len(s) <= 60 else s[:59] + '…')
    cells = [[cut('' if v is None else str(v)).replace('\n', ' ') for v in r] for r in rows]
    w = [max([len(c)] + [len(r[i]) for r in cells]) for i, c in enumerate(cols)]
    print('  '.join(c.ljust(w[i]) for i, c in enumerate(cols)))
    print('  '.join('-' * w[i] for i in range(len(cols))))
    for r in cells:
        print('  '.join(v.ljust(w[i]) for i, v in enumerate(r)).rstrip())
    print(f'({len(rows)} row{"" if len(rows) == 1 else "s"})')


def main(argv):
    flags = {a for a in argv if a in ('--csv', '--full')}
    args = [a for a in argv if a not in flags]
    q = saved()
    if not args:
        print('Saved queries (queries/*.sql):')
        for k, (text, doc) in q.items():
            params = sorted(set(re.findall(r':([a-z_]+)', text)))
            print(f'  {k:<22} {doc}' + (f'  [params: {", ".join(params)}]' if params else ''))
        return 0
    if args[0] == '--sql':
        sql, rest = args[1], args[2:]
    elif args[0] in q:
        sql, rest = q[args[0]][0], args[1:]
    else:
        print(f'unknown query « {args[0]} »; saved: {", ".join(q)}', file=sys.stderr); return 2
    names = list(dict.fromkeys(re.findall(r':([a-z_]+)', sql)))
    params = {n: None for n in names}
    for a in rest:
        if '=' in a:
            k, v = a.split('=', 1)
            if k not in params: print(f'unknown parameter « {k} »; this query takes: {", ".join(names) or "none"}', file=sys.stderr); return 2
            params[k] = v or None
        elif len(names) == 1:
            params[names[0]] = a
        else:
            print(f'give parameters as key=value; this query takes: {", ".join(names) or "none"}', file=sys.stderr); return 2
    db = fresh_db()
    cur = db.execute(sql, params)
    cols = [d[0] for d in cur.description]; rows = cur.fetchall()
    if '--csv' in flags:
        w = csv.writer(sys.stdout, lineterminator='\n'); w.writerow(cols); w.writerows(rows)
    else:
        table(cols, rows, '--full' in flags)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
