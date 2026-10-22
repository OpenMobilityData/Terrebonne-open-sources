#!/usr/bin/env python3
"""Render the Terrebonne evidence graph (nodes.csv, edges.csv) with Graphviz and as a browsable Cytoscape.js page.

Node types: agent, document, data, numerical assertion (a number put forward or derived, with the operation that produces it from the data), assertion, statement (a dated public statement), event.
Relations are factual verbs only (computed_from, states, matches, refers_to, withheld_in, differs_from, ...); none carries a judgment.
Outputs: evidence_graph.svg/.png (dot, left-to-right by type), evidence_graph.html (Cytoscape.js, click a node for its source).
Usage: python3 render_graph.py   (needs Graphviz `dot`)
"""
import csv, os, subprocess, json, html
HERE = os.path.dirname(os.path.abspath(__file__))
nodes = list(csv.DictReader(open(os.path.join(HERE, 'nodes.csv'), encoding='utf-8')))
edges = list(csv.DictReader(open(os.path.join(HERE, 'edges.csv'), encoding='utf-8')))
ids = {n['id'] for n in nodes}
bad = [(e['from'], e['to']) for e in edges if e['from'] not in ids or e['to'] not in ids]
assert not bad, f'edges to unknown nodes: {bad}'

# ---- structural checks (printed at every build; the report is also written to validation_report.txt)
def validate(nodes, edges):
    qp0 = os.path.join(HERE, 'questions.csv'); q_nodes = set()
    if os.path.exists(qp0):
        for q in csv.DictReader(open(qp0, encoding='utf-8')): q_nodes |= {x.strip() for x in q['nodes'].split(';') if x.strip()}
    out_rel = {}; in_rel = {}; deg = {n['id']: 0 for n in nodes}
    for e in edges:
        out_rel.setdefault(e['from'], set()).add(e['relation']); in_rel.setdefault(e['to'], set()).add(e['relation'])
        deg[e['from']] += 1; deg[e['to']] += 1
    problems = []
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
    nolink = [n['id'] for n in nodes if n['type'] in ('statement', 'document', 'data') and not n.get('url')]
    if nolink: print(f'note: {len(nolink)} statement/document/data node(s) without a link to their source: ' + ', '.join(nolink))
    for e in edges:
        if e['relation'] in ('differs_from', 'unsupported_by', 'does_not_include', 'same_data_other_denominator') and not e.get('note'):
            problems.append(f"difference without note: {e['from']} -> {e['to']}")
    qp = os.path.join(HERE, 'questions.csv')
    if os.path.exists(qp):
        for q in csv.DictReader(open(qp, encoding='utf-8')):
            for nid in [x.strip() for x in q['nodes'].split(';') if x.strip()]:
                if nid not in ids: problems.append(f"question {q['question']} cites unknown node: {nid}")
            if not q['nodes'].strip(): problems.append(f"question {q['question']} has no nodes")
    return problems
problems = validate(nodes, edges)
open(os.path.join(HERE, 'validation_report.txt'), 'w', encoding='utf-8').write(f"{len(nodes)} nodes, {len(edges)} edges; {len(problems)} problem(s)\n" + '\n'.join(problems) + '\n')
print(f"validation: {len(problems)} problem(s)" + (': ' + '; '.join(problems[:12]) + (' …' if len(problems) > 12 else '') if problems else ''))
STYLE = {'agent': ('#e9ebee', 'ellipse'), 'document': ('#fff3e8', 'note'), 'data': ('#e8f1fb', 'box'),
         'numerical assertion': ('#e6f6ef', 'box'), 'assertion': ('#fff8e1', 'octagon'), 'statement': ('#fdf1f1', 'box'), 'event': ('#f3eefc', 'hexagon')}
EDGE = {'differs_from': ('#e34948', 'dashed'), 'same_data_other_denominator': ('#e34948', 'dashed'), 'unsupported_by': ('#e34948', 'dotted'),
        'does_not_include': ('#e34948', 'dotted'), 'withheld_in': ('#7a7a7a', 'dashed'), 'redacted_in': ('#7a7a7a', 'dashed'),
        'computed_from': ('#2a78d6', 'solid'), 'states': ('#2a78d6', 'solid'), 'matches': ('#1baf7a', 'solid'), 'attributed_to': ('#b0b4b9', 'solid'),
        'supports': ('#1baf7a', 'solid'), 'undercuts': ('#e34948', 'solid'), 'bears_on': ('#eda100', 'dotted')}
def wrap(s, w=34):
    s = s.replace('\\', '/').replace('"', '\\"')
    out, line = [], ''
    for word in s.split():
        if len(line) + len(word) + 1 > w: out.append(line); line = word
        else: line = (line + ' ' + word).strip()
    out.append(line); return '\\n'.join(out)
dot = ['digraph G {', 'rankdir=LR; newrank=true; splines=spline; nodesep=0.25; ranksep=0.9; fontname="Helvetica"; node [fontname="Helvetica", fontsize=9, style="filled,rounded", penwidth=0.6, color="#9aa0a6"]; edge [fontname="Helvetica", fontsize=7.5, color="#9aa0a6", arrowsize=0.6];']
order = ['agent', 'document', 'data', 'numerical assertion', 'assertion', 'statement', 'event']
for t in order:
    fill, shape = STYLE[t]
    dot.append(f'subgraph cluster_{t.replace(" ", "_")} {{ label="{t if t == "data" else t + "s"}"; fontsize=11; color="#d9dcd8"; style="rounded";')
    for n in nodes:
        if n['type'] == t:
            lab = wrap(n['label']) + (f'\\n[{n["date"]}]' if n['date'] else '')
            href = f', URL="{n["url"]}", target="_blank"' if n.get('url') else ''
            dot.append(f'  {n["id"]} [label="{lab}", fillcolor="{fill}", shape={shape}{href}];')
    dot.append('}')
for e in edges:
    col, sty = EDGE.get(e['relation'], ('#9aa0a6', 'solid'))
    tip = e.get('note', '').replace('"', '\\"')
    extra = ', constraint=false' if e['relation'] in ('made_at', 'attributed_to', 'same_day') else ''
    dot.append(f'{e["from"]} -> {e["to"]} [label="{e["relation"].replace("_", " ")}", color="{col}", fontcolor="{col}", style={sty}{extra}' + (f', tooltip="{tip}"' if tip else '') + '];')
dot.append('}')
open(os.path.join(HERE, 'evidence_graph.dot'), 'w', encoding='utf-8').write('\n'.join(dot))
# Cytoscape.js page (data embedded; cdnjs, pinned version). Short titles on the nodes, full text in the side panel.
COL = {'agent': '#9aa0a6', 'document': '#eb6834', 'data': '#2a78d6', 'numerical assertion': '#1baf7a', 'assertion': '#eda100', 'statement': '#e34948', 'event': '#6250d6'}
ORDER = ['agent', 'document', 'data', 'numerical assertion', 'assertion', 'statement', 'event']
els = [{'data': {'id': n['id'], 'short': n['short'], 'label': n['label'], 'type': n['type'], 'date': n['date'], 'source': n['source'], 'aliases': n.get('aliases', ''), 'url': n.get('url', '')}} for n in nodes] + \
      [{'data': {'id': f'e{i}', 'source': e['from'], 'target': e['to'], 'rel': e['relation'].replace('_', ' '), 'note': e.get('note', ''), 'url': e.get('url', '') or ''}} for i, e in enumerate(edges)]
# swimlane positions: one column per type, nodes ordered by date (undated last)
# swimlanes: one column per type, except statements, which get one column per event they were made at (events in date order)
made_at = {e['from']: e['to'] for e in edges if e['relation'] == 'made_at'}
ev_date = {n['id']: (n['date'] or '9999') for n in nodes if n['type'] == 'event'}
by_date = lambda n: (n['date'] or '9999')
lanes = []   # list of (title, [ids])
for t in ORDER:
    if t != 'statement':
        lanes.append((t, [n['id'] for n in sorted((n for n in nodes if n['type'] == t), key=by_date)]))
    else:
        # one column per sitting or interview; the Oct 6 sitting is split by exchange (address, then one column per
        # questioner, in webcast order), each column ordered by the first time stamp in the node's source
        import re as _re
        OCT6 = {'01': 'address', '07': 'Trudeau', '02': 'Joutel', '03': 'Garate', '04': 'Lund', '05': 'Hoge', '06': 'Jazz'}
        OCT6_ORDER = ['01', '07', '02', '03', '04', '05', '06']
        def tsecs(src):
            m = _re.search(r'(\d+):(\d\d)(?::(\d\d))?', src or '')
            if not m: return 10**9
            h, mi, se = m.group(1), m.group(2), m.group(3)
            return (int(h) * 3600 + int(mi) * 60 + int(se)) if se else (int(h) * 60 + int(mi))
        groups = {}
        for n in sorted((n for n in nodes if n['type'] == 'statement'), key=by_date):
            ev = made_at.get(n['id'], 'other')
            m = _re.search(r'2026-10-06_(0\d)\.md', n.get('source', '')) if ev == 'e_oct6' else None
            groups.setdefault((ev, m.group(1) if m else ''), []).append(n)
        def lane_key(k):
            ev, part = k
            return (ev_date.get(ev, '9999'), ev, OCT6_ORDER.index(part) if part in OCT6_ORDER else 99)
        for k in sorted(groups, key=lane_key):
            ev, part = k
            col = groups[k]
            if ev == 'e_oct6':
                col = sorted(col, key=lambda n: tsecs(n.get('source', '')))
            lanes.append((f'statements: {ev}' + (f' ({OCT6[part]})' if part in OCT6 else ''), [n['id'] for n in col]))
pos = {}
# row spacing follows each label's wrapped height (font 10, wrap at 130 px: about 26 characters a line), so labels
# never overlap inside a column; each column is centred on the same horizontal midline (the tallest column sets
# the height), so the edges fan out from the middle instead of bunching along the top edge
import math as _m
short_of = {n['id']: n['short'] for n in nodes}
def row_h(nid):
    words = short_of[nid].split(); lines, cur = 1, 0
    for w in words:
        if cur and cur + 1 + len(w) > 26: lines += 1; cur = len(w)
        else: cur += (1 if cur else 0) + len(w)
    return 16 + 3 + lines * 12 + 14
col_h = {ci: sum(row_h(nid) for nid in col) for ci, (_, col) in enumerate(lanes)}
tallest = max(col_h.values())
for ci, (title, col) in enumerate(lanes):
    y = 60 + (tallest - col_h[ci]) / 2
    for nid in col:
        h = row_h(nid)
        pos[nid] = {'x': 80 + ci * 280, 'y': round(y + 8)}
        y += h
import collections as _c
REL_STYLE = {'supports': ('#1baf7a', 'solid'), 'undercuts': ('#e34948', 'solid'), 'bears on': ('#eda100', 'dotted'),
             'differs from': ('#e34948', 'dashed'), 'same data other denominator': ('#e34948', 'dashed'), 'unsupported by': ('#e34948', 'dashed'), 'does not include': ('#e34948', 'dashed'),
             'withheld in': ('#b0b4b9', 'dashed'), 'redacted in': ('#b0b4b9', 'dashed')}
rel_counts = _c.Counter(e['relation'].replace('_', ' ') for e in edges)
rel_legend = ''.join(f'<div class="rel" data-rel="{r}"><i class="line" style="border-top:2px {REL_STYLE.get(r, ("#b0b4b9", "solid"))[1]} {REL_STYLE.get(r, ("#b0b4b9", "solid"))[0]}"></i>{r} <i class="muted" style="font-style:normal">· {n}</i></div>' for r, n in sorted(rel_counts.items(), key=lambda x: (-x[1], x[0])))
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Terrebonne evidence graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/cytoscape-svg@0.4.0/cytoscape-svg.js"></script>
<style>:root{{--bg:#fcfcfb;--fg:#1f2428;--muted:#5f6b74;--line:#d9dcd8;--panel:#ffffff}}@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1a1a19;--fg:#ecece8;--muted:#a3a79f;--line:#34373a;--panel:#222322}}}}:root[data-theme="dark"]{{--bg:#1a1a19;--fg:#ecece8;--muted:#a3a79f;--line:#34373a;--panel:#222322}}
html,body{{margin:0;height:100%;background:var(--bg);color:var(--fg);font:14px/1.4 -apple-system,"Helvetica Neue",Arial,sans-serif}}#cy{{position:absolute;inset:0;right:360px}}
#side{{position:absolute;top:0;right:0;width:360px;height:100%;overflow:auto;border-left:1px solid var(--line);padding:14px 16px;box-sizing:border-box;background:var(--panel)}}h1{{font-size:16px;margin:0 0 6px}}.muted{{color:var(--muted);font-size:12px}}
.leg span{{display:inline-block;width:10px;height:10px;border-radius:5px;margin-right:4px}}.leg div{{margin:2px 0;font-size:12px}}#info{{margin-top:12px;font-size:13px}}#info b{{display:block;margin-bottom:4px}}#info ul{{padding-left:16px;margin:6px 0 0}}#info li{{margin:2px 0;font-size:12px}}
.rel{{cursor:pointer;font-size:12px;margin:2px 0}}.rel.on{{font-weight:600}}.rel i.line{{display:inline-block;width:18px;height:0;margin-right:6px;vertical-align:middle}}#rels{{margin-top:10px}}
.btns{{margin:10px 0}}button{{font:12px -apple-system,"Helvetica Neue",Arial,sans-serif;padding:4px 10px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);margin-right:6px;cursor:pointer}}button.on{{border-color:var(--fg)}}
@media (max-width:700px){{#cy{{right:0;bottom:42%}}#side{{top:58%;width:100%;height:42%;border-left:0;border-top:1px solid var(--line)}}}}</style></head><body>
<div id="cy"></div><div id="side"><h1>Terrebonne evidence graph</h1><p class="muted">Public statements, documents, data, numerical assertions and assertions, with factual relations only. Click a node for its full text, source and links; double-click a node to open its source itself (the page of the bundle, the moment in the webcast, the file); click a line to see the relation and open the source it rests on; the ↗ after each relation in a node's list opens the other end's source; drag to rearrange; scroll to zoom. Columns: agents, documents, data, numerical assertions, assertions (the propositions the evidence bears on: green = supports, red = undercuts, amber dotted = bears on), then the statements in one column per sitting or interview, then events; oldest at the top. In the force layout the labels are off; hover or click a node to read them, or turn them back on.</p>
<div class="btns"><button id="b_lanes" class="on">Columns by type</button><button id="b_force">Force layout</button><button id="b_fit">Fit</button><button id="b_reset">Reset view</button><button id="b_labels">Labels: on</button></div><div class="btns"><input id="q" type="search" placeholder="Find a node (words, phrases, aliases)…" style="width:100%;font:13px -apple-system,&quot;Helvetica Neue&quot;,Arial,sans-serif;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg)"><div id="hits" class="muted" style="font-size:12px;margin-top:4px"></div></div><div class="btns"><button id="b_copy">Copy image</button><button id="b_save">Save PNG</button><button id="b_svg">Save SVG</button> <span id="msg" class="muted"></span></div>
<div class="leg">{''.join(f'<div><span style="background:{c}"></span>{t}</div>' for t, c in COL.items())}</div><details id="relbox" class="leg"><summary class="muted" style="cursor:pointer;font-size:12px;margin-top:10px">Relations ({len(rel_counts)} kinds) — click one to show only its lines</summary><div id="rels"><div class="muted" style="margin:4px 0 6px">Click again, tap the background or Reset to clear; link with #rel=… <label style="display:block;margin-top:4px;cursor:pointer"><input type="checkbox" id="keepattr"> Keep the « attributed to » lines of the highlighted nodes</label></div>{rel_legend}</div></details><div id="info" class="muted">Nothing selected.</div></div>
<script>
const COL={json.dumps(COL)}; const POS={json.dumps(pos)};
const fg=getComputedStyle(document.documentElement).getPropertyValue('--fg').trim()||'#1f2428', bg=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()||'#fcfcfb';
const cy=cytoscape({{container:document.getElementById('cy'),elements:{json.dumps(els)},wheelSensitivity:0.2,
 style:[{{selector:'node',style:{{'label':'data(short)','font-size':10,'text-wrap':'wrap','text-max-width':130,'background-color':e=>COL[e.data('type')],'width':16,'height':16,'color':fg,'text-valign':'bottom','text-margin-y':3,'text-background-color':bg,'text-background-opacity':0.85,'text-background-padding':2,'text-background-shape':'roundrectangle'}}}},
        {{selector:'edge',style:{{'width':1,'line-color':'#b0b4b9','target-arrow-color':'#b0b4b9','target-arrow-shape':'triangle','arrow-scale':0.7,'curve-style':'bezier','label':'','font-size':8,'color':'#5f6b74','text-rotation':'autorotate','text-background-color':bg,'text-background-opacity':0.85,'text-background-padding':1}}}},
        {{selector:'edge[rel = "differs from"], edge[rel = "same data other denominator"], edge[rel = "unsupported by"], edge[rel = "does not include"]',style:{{'line-color':'#e34948','target-arrow-color':'#e34948','line-style':'dashed'}}}},
        {{selector:'edge[rel = "withheld in"], edge[rel = "redacted in"]',style:{{'line-style':'dashed'}}}},
        {{selector:'edge[rel = "supports"]',style:{{'line-color':'#1baf7a','target-arrow-color':'#1baf7a'}}}},{{selector:'edge[rel = "undercuts"]',style:{{'line-color':'#e34948','target-arrow-color':'#e34948'}}}},{{selector:'edge[rel = "bears on"]',style:{{'line-color':'#eda100','target-arrow-color':'#eda100','line-style':'dotted'}}}},
        {{selector:'.dim',style:{{'opacity':0.15}}}},{{selector:'.hl',style:{{'width':2,'label':'data(rel)','opacity':1}}}},{{selector:'edge.hlrel',style:{{'width':2.5,'opacity':1}}}},{{selector:'edge.hlattr',style:{{'width':1.5,'opacity':1}}}},{{selector:'node.hlrel',style:{{'width':20,'height':20,'opacity':1,'label':'data(short)'}}}},{{selector:'node.hl',style:{{'width':22,'height':22,'font-size':11,'opacity':1,'label':'data(short)'}}}},
        {{selector:'node.nolabel',style:{{'label':''}}}},{{selector:'node.found',style:{{'border-width':3,'border-color':'#eda100','label':'data(short)','z-index':8}}}},{{selector:'node.hover',style:{{'label':'data(short)','z-index':9}}}},
        {{selector:':selected',style:{{'border-width':3,'border-color':fg}}}}],
 layout:{{name:'preset',positions:n=>POS[n.id()],fit:true,padding:30}}}});
let curRel=null;
function clearRel(){{curRel=null;cy.elements().removeClass('hlrel');document.querySelectorAll('#rels .rel').forEach(d=>d.classList.remove('on'));}}
function focus(n){{cy.elements().removeClass('hl dim'); clearRel(); if(!n){{return;}} const nb=n.closedNeighborhood(); cy.elements().not(nb).addClass('dim'); nb.addClass('hl');}}
function focusRel(rel){{cy.elements().removeClass('hl dim hlrel'); cy.elements().unselect(); document.querySelectorAll('#rels .rel').forEach(d=>d.classList.toggle('on',d.dataset.rel===rel)); curRel=rel; if(!rel){{document.getElementById('info').innerHTML='Nothing selected.';return;}}
 const es=cy.edges().filter(e=>e.data('rel')===rel), ns=es.connectedNodes(); cy.elements().not(es).not(ns).addClass('dim'); es.addClass('hlrel'); ns.addClass('hlrel');
 let extra='';
 if(document.getElementById('keepattr').checked && rel!=='attributed to'){{const at=cy.edges().filter(e=>e.data('rel')==='attributed to' && (ns.contains(e.source())||ns.contains(e.target()))); const an=at.connectedNodes().not(ns); at.removeClass('dim').addClass('hlattr'); an.removeClass('dim').addClass('hlrel'); extra=' Plus '+at.length+' « attributed to » line'+(at.length===1?'':'s')+' to '+an.length+' agent'+(an.length===1?'':'s')+'.';}}
 document.getElementById('info').innerHTML='<b>'+rel+'</b>'+es.length+' relation'+(es.length===1?'':'s')+' shown, '+ns.length+' nodes.'+extra+' Other lines are dimmed; click a node for its text, Reset to clear.'; document.getElementById('relbox').open=true; if(history.replaceState)history.replaceState(null,'','#rel='+encodeURIComponent(rel)+(document.getElementById('keepattr').checked?'&attr=1':''));}}
document.getElementById('keepattr').onchange=()=>{{if(curRel)focusRel(curRel);}};
document.querySelectorAll('#rels .rel').forEach(d=>d.onclick=()=>focusRel(curRel===d.dataset.rel?null:d.dataset.rel));
if(location.hash.startsWith('#rel=')){{const h=location.hash.slice(5).split('&'); const r=decodeURIComponent(h[0]); if(h.includes('attr=1'))document.getElementById('keepattr').checked=true; if(cy.edges().some(e=>e.data('rel')===r)) setTimeout(()=>focusRel(r),50);}}
cy.on('tap','node',e=>{{const n=e.target,d=n.data(); focus(n);
 const links=n.connectedEdges().map(ed=>{{const other=ed.source().id()===n.id()?ed.target():ed.source(); const dir=ed.source().id()===n.id()?'→':'←'; const ou=ed.data('url')||other.data('url'); return '<li>'+dir+' '+ed.data('rel')+' <i>'+other.data('short').replace(/</g,'&lt;')+'</i>'+(ou?' <a href="'+ou.replace(/"/g,'&quot;')+'" target="_blank" rel="noopener" title="Open the source of this relation">↗</a>':'')+(ed.data('note')?'<br><span class="muted">'+ed.data('note').replace(/</g,'&lt;')+'</span>':'')+'</li>';}}).join('');
 document.getElementById('info').innerHTML='<b>'+d.label.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</b>'+(d.date?d.date+'<br>':'')+'Type: '+d.type+'<br>Source: '+(d.source||'—')+(d.aliases?'<br>Also said as: '+d.aliases.replace(/</g,'&lt;'):'')+(d.url?'<br><a href="'+d.url.replace(/"/g,'&quot;')+'" target="_blank" rel="noopener">Open source ↗</a> (or double-click the node)':'')+'<ul>'+links+'</ul>';}});
cy.on('tap',e=>{{if(e.target===cy){{focus(null);document.getElementById('info').innerHTML='Nothing selected.';if(history.replaceState)history.replaceState(null,'',location.pathname);}}}});
function openUrl(u,what){{if(!u){{say('No public link for this '+what+' (see its Source line).');return;}} const w=window.open(u,'_blank','noopener'); if(!w)say('The browser blocked the new tab: use the Open source link in the panel.');}}
cy.on('dbltap','node',e=>openUrl(e.target.data('url'),'node'));
cy.on('tap','edge',e=>{{const ed=e.target,s=ed.source(),t=ed.target(); cy.elements().removeClass('hl dim'); clearRel(); cy.elements().not(ed).not(s).not(t).addClass('dim'); ed.addClass('hl'); s.addClass('hl'); t.addClass('hl');
 const u=ed.data('url')||t.data('url')||s.data('url');
 document.getElementById('info').innerHTML='<b>'+s.data('short').replace(/</g,'&lt;')+'</b><br>→ <b>'+ed.data('rel')+'</b> →<br><b>'+t.data('short').replace(/</g,'&lt;')+'</b>'+(ed.data('note')?'<br><span class="muted">'+ed.data('note').replace(/</g,'&lt;')+'</span>':'')+(u?'<br><a href="'+u.replace(/"/g,'&quot;')+'" target="_blank" rel="noopener">Open the source of this relation ↗</a> (or double-click the line)':'<br><span class="muted">No public link on either end.</span>');}});
cy.on('dbltap','edge',e=>{{const ed=e.target; openUrl(ed.data('url')||ed.target().data('url')||ed.source().data('url'),'relation');}});
const bl=document.getElementById('b_lanes'),bf=document.getElementById('b_force');
bl.onclick=()=>{{setLabels(true);cy.layout({{name:'preset',positions:n=>POS[n.id()],fit:true,padding:30,animate:true}}).run();bl.classList.add('on');bf.classList.remove('on');}};
let labels=true; const bL=document.getElementById('b_labels');
function setLabels(on){{labels=on;cy.nodes().toggleClass('nolabel',!on);bL.textContent='Labels: '+(on?'on':'off');}}
bL.onclick=()=>setLabels(!labels);
cy.on('mouseover','node',e=>e.target.addClass('hover')); cy.on('mouseout','node',e=>e.target.removeClass('hover'));
bf.onclick=()=>{{setLabels(false);cy.layout({{name:'cose',animate:true,nodeRepulsion:()=>400000,idealEdgeLength:()=>220,edgeElasticity:()=>40,gravity:0.15,numIter:1500,padding:30,fit:true}}).run();bf.classList.add('on');bl.classList.remove('on');}};
document.getElementById('b_fit').onclick=()=>cy.fit(30);
const qbox=document.getElementById('q'),hits=document.getElementById('hits');
qbox.oninput=()=>{{const s=qbox.value.trim().toLowerCase();hits.innerHTML='';if(s.length<2){{cy.nodes().removeClass('found');return;}}
 const m=cy.nodes().filter(n=>((n.data('short')||'')+' '+(n.data('label')||'')+' '+(n.data('aliases')||'')).toLowerCase().includes(s));
 cy.nodes().removeClass('found');m.addClass('found');
 hits.innerHTML=m.length?m.slice(0,12).map(n=>'<div><a href="#" data-id="'+n.id()+'" style="color:inherit">'+n.data('short').replace(/</g,'&lt;')+'</a></div>').join('')+(m.length>12?'<div>… '+(m.length-12)+' more</div>':''):'No match.';
 hits.querySelectorAll('a').forEach(a=>a.onclick=ev=>{{ev.preventDefault();const n=cy.getElementById(a.dataset.id);n.select();cy.animate({{center:{{eles:n}},zoom:1.2}},{{duration:300}});n.emit('tap');}});}};
document.getElementById('b_reset').onclick=()=>{{setLabels(true);focus(null);cy.elements().unselect();document.getElementById('info').innerHTML='Nothing selected.';cy.layout({{name:'preset',positions:n=>POS[n.id()],fit:true,padding:30,animate:true}}).run();bl.classList.add('on');bf.classList.remove('on');}};
function shot(){{return cy.png({{full:false,scale:2,bg:bg}});}}
function say(m){{const s=document.getElementById('msg');s.textContent=m;setTimeout(()=>s.textContent='',3000);}}
document.getElementById('b_copy').onclick=async()=>{{try{{const blob=await (await fetch(shot())).blob();await navigator.clipboard.write([new ClipboardItem({{'image/png':blob}})]);say('Copied to the clipboard.');}}catch(e){{say('Clipboard not available here; use Save PNG.');}}}};
document.getElementById('b_svg').onclick=()=>{{try{{const s=cy.svg({{scale:1,full:false,bg:bg}});const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([s],{{type:'image/svg+xml'}}));a.download='terrebonne-evidence-graph-'+new Date().toISOString().slice(0,10)+'.svg';a.click();say('Saved.');}}catch(e){{say('SVG export not available (extension did not load).');}}}};
document.getElementById('b_save').onclick=()=>{{const a=document.createElement('a');a.href=shot();a.download='terrebonne-evidence-graph-'+new Date().toISOString().slice(0,10)+'.png';a.click();say('Saved.');}};
</script></body></html>'''
open(os.path.join(HERE, 'evidence_graph.html'), 'w', encoding='utf-8').write(page)
ok = True
for fmt in ('svg', 'png'):
    dotfile = os.path.join(HERE, 'evidence_graph.dot'); outp = os.path.join(HERE, f'evidence_graph.{fmt}'); dpi = '-Gdpi=110' if fmt == 'png' else '-Gdpi=72'
    attempts = (['dot', dpi], ['dot', dpi, '-Gsplines=polyline'], ['dot', dpi, '-Gclusterrank=none', '-Gsplines=line'],
                ['sfdp', dpi, '-Goverlap=prism', '-Gsplines=false'], ['sfdp', dpi, '-Goverlap=scale', '-Gsplines=line'])
    for cmd in attempts:
        r = subprocess.run(cmd + [f'-T{fmt}', dotfile, '-o', outp], capture_output=True)
        if r.returncode == 0 and os.path.getsize(outp) > 0:
            if cmd != attempts[0]: print(f'{fmt}: drawn with', ' '.join(cmd[0:1] + cmd[2:]))
            break
    else:
        ok = False; print('graphviz failed for', fmt, r.stderr.decode()[-200:])
print('nodes', len(nodes), 'edges', len(edges), '-> evidence_graph.html, .dot' + (', .svg, .png' if ok else ' (svg/png NOT updated)'))
