#!/usr/bin/env python3
"""Render the Terrebonne evidence graph (nodes.csv, edges.csv) with Graphviz and as a browsable Cytoscape.js page.

Node types: agent, document, data, figure (a number derived from data), statement (a dated public statement), event.
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
STYLE = {'agent': ('#e9ebee', 'ellipse'), 'document': ('#fff3e8', 'note'), 'data': ('#e8f1fb', 'box'),
         'figure': ('#e6f6ef', 'box'), 'statement': ('#fdf1f1', 'box'), 'event': ('#f3eefc', 'hexagon')}
EDGE = {'differs_from': ('#e34948', 'dashed'), 'same_data_other_denominator': ('#e34948', 'dashed'), 'unsupported_by': ('#e34948', 'dotted'),
        'does_not_include': ('#e34948', 'dotted'), 'withheld_in': ('#7a7a7a', 'dashed'), 'redacted_in': ('#7a7a7a', 'dashed'),
        'computed_from': ('#2a78d6', 'solid'), 'states': ('#2a78d6', 'solid'), 'matches': ('#1baf7a', 'solid'), 'attributed_to': ('#b0b4b9', 'solid')}
def wrap(s, w=34):
    s = s.replace('\\', '/').replace('"', '\\"')
    out, line = [], ''
    for word in s.split():
        if len(line) + len(word) + 1 > w: out.append(line); line = word
        else: line = (line + ' ' + word).strip()
    out.append(line); return '\\n'.join(out)
dot = ['digraph G {', 'rankdir=LR; splines=true; nodesep=0.25; ranksep=0.9; fontname="Helvetica"; node [fontname="Helvetica", fontsize=9, style="filled,rounded", penwidth=0.6, color="#9aa0a6"]; edge [fontname="Helvetica", fontsize=7.5, color="#9aa0a6", arrowsize=0.6];']
order = ['agent', 'document', 'data', 'figure', 'statement', 'event']
for t in order:
    fill, shape = STYLE[t]
    dot.append(f'subgraph cluster_{t} {{ label="{t if t == "data" else t + "s"}"; fontsize=11; color="#d9dcd8"; style="rounded";')
    for n in nodes:
        if n['type'] == t:
            lab = wrap(n['label']) + (f'\\n[{n["date"]}]' if n['date'] else '')
            dot.append(f'  {n["id"]} [label="{lab}", fillcolor="{fill}", shape={shape}];')
    dot.append('}')
for e in edges:
    col, sty = EDGE.get(e['relation'], ('#9aa0a6', 'solid'))
    tip = e.get('note', '').replace('"', '\\"')
    dot.append(f'{e["from"]} -> {e["to"]} [label="{e["relation"].replace("_", " ")}", color="{col}", fontcolor="{col}", style={sty}' + (f', tooltip="{tip}"' if tip else '') + '];')
dot.append('}')
open(os.path.join(HERE, 'evidence_graph.dot'), 'w', encoding='utf-8').write('\n'.join(dot))
for fmt in ('svg', 'png'):
    subprocess.run(['dot', f'-T{fmt}', '-Gdpi=110' if fmt == 'png' else '-Gdpi=72', os.path.join(HERE, 'evidence_graph.dot'), '-o', os.path.join(HERE, f'evidence_graph.{fmt}')], check=True)
# Cytoscape.js page (data embedded; cdnjs, pinned version). Short titles on the nodes, full text in the side panel.
COL = {'agent': '#9aa0a6', 'document': '#eb6834', 'data': '#2a78d6', 'figure': '#1baf7a', 'statement': '#e34948', 'event': '#6250d6'}
ORDER = ['agent', 'document', 'data', 'figure', 'statement', 'event']
els = [{'data': {'id': n['id'], 'short': n['short'], 'label': n['label'], 'type': n['type'], 'date': n['date'], 'source': n['source']}} for n in nodes] + \
      [{'data': {'id': f'e{i}', 'source': e['from'], 'target': e['to'], 'rel': e['relation'].replace('_', ' '), 'note': e.get('note', '')}} for i, e in enumerate(edges)]
# swimlane positions: one column per type, nodes ordered by date (undated last)
lanes = {}
for n in sorted(nodes, key=lambda n: (n['date'] or '9999')):
    lanes.setdefault(n['type'], []).append(n['id'])
pos = {}
for ci, t in enumerate(ORDER):
    col = lanes.get(t, [])
    for ri, nid in enumerate(col):
        pos[nid] = {'x': 80 + ci * 260, 'y': 60 + ri * (900 / max(1, len(col) - 1) if len(col) > 1 else 0)}
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Terrebonne evidence graph</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.30.2/cytoscape.min.js"></script>
<style>:root{{--bg:#fcfcfb;--fg:#1f2428;--muted:#5f6b74;--line:#d9dcd8;--panel:#ffffff}}@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#1a1a19;--fg:#ecece8;--muted:#a3a79f;--line:#34373a;--panel:#222322}}}}:root[data-theme="dark"]{{--bg:#1a1a19;--fg:#ecece8;--muted:#a3a79f;--line:#34373a;--panel:#222322}}
html,body{{margin:0;height:100%;background:var(--bg);color:var(--fg);font:14px/1.4 -apple-system,"Helvetica Neue",Arial,sans-serif}}#cy{{position:absolute;inset:0;right:360px}}
#side{{position:absolute;top:0;right:0;width:360px;height:100%;overflow:auto;border-left:1px solid var(--line);padding:14px 16px;box-sizing:border-box;background:var(--panel)}}h1{{font-size:16px;margin:0 0 6px}}.muted{{color:var(--muted);font-size:12px}}
.leg span{{display:inline-block;width:10px;height:10px;border-radius:5px;margin-right:4px}}.leg div{{margin:2px 0;font-size:12px}}#info{{margin-top:12px;font-size:13px}}#info b{{display:block;margin-bottom:4px}}#info ul{{padding-left:16px;margin:6px 0 0}}#info li{{margin:2px 0;font-size:12px}}
.btns{{margin:10px 0}}button{{font:12px -apple-system,"Helvetica Neue",Arial,sans-serif;padding:4px 10px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);margin-right:6px;cursor:pointer}}button.on{{border-color:var(--fg)}}
@media (max-width:700px){{#cy{{right:0;bottom:42%}}#side{{top:58%;width:100%;height:42%;border-left:0;border-top:1px solid var(--line)}}}}</style></head><body>
<div id="cy"></div><div id="side"><h1>Terrebonne evidence graph</h1><p class="muted">Public statements, documents, data and derived figures, with factual relations only. Click a node for its full text, source and links; drag to rearrange; scroll to zoom. Columns: agents, documents, data, figures, statements, event; newest at the bottom.</p>
<div class="btns"><button id="b_lanes" class="on">Columns by type</button><button id="b_force">Force layout</button><button id="b_fit">Fit</button></div><div class="btns"><button id="b_copy">Copy image</button><button id="b_save">Save PNG</button> <span id="msg" class="muted"></span></div>
<div class="leg">{''.join(f'<div><span style="background:{c}"></span>{t}</div>' for t, c in COL.items())}</div><div id="info" class="muted">Nothing selected.</div></div>
<script>
const COL={json.dumps(COL)}; const POS={json.dumps(pos)};
const fg=getComputedStyle(document.documentElement).getPropertyValue('--fg').trim()||'#1f2428', bg=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim()||'#fcfcfb';
const cy=cytoscape({{container:document.getElementById('cy'),elements:{json.dumps(els)},wheelSensitivity:0.2,
 style:[{{selector:'node',style:{{'label':'data(short)','font-size':10,'text-wrap':'wrap','text-max-width':130,'background-color':e=>COL[e.data('type')],'width':16,'height':16,'color':fg,'text-valign':'bottom','text-margin-y':3,'text-background-color':bg,'text-background-opacity':0.85,'text-background-padding':2,'text-background-shape':'roundrectangle'}}}},
        {{selector:'edge',style:{{'width':1,'line-color':'#b0b4b9','target-arrow-color':'#b0b4b9','target-arrow-shape':'triangle','arrow-scale':0.7,'curve-style':'bezier','label':'','font-size':8,'color':'#5f6b74','text-rotation':'autorotate','text-background-color':bg,'text-background-opacity':0.85,'text-background-padding':1}}}},
        {{selector:'edge[rel = "differs from"], edge[rel = "same data other denominator"], edge[rel = "unsupported by"], edge[rel = "does not include"]',style:{{'line-color':'#e34948','target-arrow-color':'#e34948','line-style':'dashed'}}}},
        {{selector:'edge[rel = "withheld in"], edge[rel = "redacted in"]',style:{{'line-style':'dashed'}}}},
        {{selector:'.dim',style:{{'opacity':0.15}}}},{{selector:'.hl',style:{{'width':2,'label':'data(rel)','opacity':1}}}},{{selector:'node.hl',style:{{'width':22,'height':22,'font-size':11,'opacity':1}}}},
        {{selector:':selected',style:{{'border-width':3,'border-color':fg}}}}],
 layout:{{name:'preset',positions:n=>POS[n.id()],fit:true,padding:30}}}});
function focus(n){{cy.elements().removeClass('hl dim'); if(!n){{return;}} const nb=n.closedNeighborhood(); cy.elements().not(nb).addClass('dim'); nb.addClass('hl');}}
cy.on('tap','node',e=>{{const n=e.target,d=n.data(); focus(n);
 const links=n.connectedEdges().map(ed=>{{const other=ed.source().id()===n.id()?ed.target():ed.source(); const dir=ed.source().id()===n.id()?'→':'←'; return '<li>'+dir+' '+ed.data('rel')+' <i>'+other.data('short').replace(/</g,'&lt;')+'</i>'+(ed.data('note')?'<br><span class="muted">'+ed.data('note').replace(/</g,'&lt;')+'</span>':'')+'</li>';}}).join('');
 document.getElementById('info').innerHTML='<b>'+d.label.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</b>'+(d.date?d.date+'<br>':'')+'Type: '+d.type+'<br>Source: '+(d.source||'—')+'<ul>'+links+'</ul>';}});
cy.on('tap',e=>{{if(e.target===cy){{focus(null);document.getElementById('info').innerHTML='Nothing selected.';}}}});
const bl=document.getElementById('b_lanes'),bf=document.getElementById('b_force');
bl.onclick=()=>{{cy.layout({{name:'preset',positions:n=>POS[n.id()],fit:true,padding:30,animate:true}}).run();bl.classList.add('on');bf.classList.remove('on');}};
bf.onclick=()=>{{cy.layout({{name:'cose',animate:true,nodeRepulsion:()=>40000,idealEdgeLength:()=>160,edgeElasticity:()=>60,gravity:0.3,padding:30}}).run();bf.classList.add('on');bl.classList.remove('on');}};
document.getElementById('b_fit').onclick=()=>cy.fit(30);
function shot(){{return cy.png({{full:false,scale:2,bg:bg}});}}
function say(m){{const s=document.getElementById('msg');s.textContent=m;setTimeout(()=>s.textContent='',3000);}}
document.getElementById('b_copy').onclick=async()=>{{try{{const blob=await (await fetch(shot())).blob();await navigator.clipboard.write([new ClipboardItem({{'image/png':blob}})]);say('Copied to the clipboard.');}}catch(e){{say('Clipboard not available here; use Save PNG.');}}}};
document.getElementById('b_save').onclick=()=>{{const a=document.createElement('a');a.href=shot();a.download='terrebonne-evidence-graph-'+new Date().toISOString().slice(0,10)+'.png';a.click();say('Saved.');}};
</script></body></html>'''
open(os.path.join(HERE, 'evidence_graph.html'), 'w', encoding='utf-8').write(page)
print('nodes', len(nodes), 'edges', len(edges), '-> evidence_graph.{svg,png,html,dot}')
