"""Stage 5c: the owner's check page for private parking: a random sample of lots, each with its crop (the lot
outlined in red), its address and a link to street-level imagery, and a form whose answers are exported as JSON.

The sample is drawn once, with a fixed seed, before any second-pass reading exists: 100 buildings of five
dwellings or fewer and 12 of six or more, at random without replacement (derived/readings/owner_check_sample.csv).
The page shows no reading by anyone else. It is written outside the repository (it is a working page).

Run:  ~/.venvs/omd/bin/python scripts/offstreet_check_page.py     (after offstreet_crops.py)
"""
import html
import json
from pathlib import Path

import numpy as np
import pandas as pd

import offstreet_crops as C
import offstreet_strips as S
from corridor_lib import ROOT, TABLES

OUT = Path.home() / "Terrebonne-data" / "corridor-parking-check"
SAMPLE = ROOT / "derived" / "readings" / "owner_check_sample.csv"
SEED, N_SMALL, N_LARGE = 20261112, 100, 12


def main():
    b, alll, g = S.frame()
    crops = pd.read_csv(TABLES / "offstreet_crops.csv")
    if SAMPLE.exists():
        s = pd.read_csv(SAMPLE)
    else:
        rng = np.random.default_rng(SEED)
        keys = list(rng.choice(sorted(b.index[~b.large]), N_SMALL, replace=False)) + list(rng.choice(sorted(b.index[b.large]), N_LARGE, replace=False))
        s = pd.DataFrame({"key": keys}); s = s.sample(frac=1, random_state=SEED).reset_index(drop=True)
        s.insert(0, "n", s.index + 1)
        s = s.merge(crops[["key", "crop", "label"]], on="key")
        s.to_csv(SAMPLE, index=False)
    (OUT / "img").mkdir(parents=True, exist_ok=True)
    items = []
    for r in s.itertuples():
        row = b.loc[r.key]
        rows = crops[crops.crop == r.crop]
        C.render(r.crop, rows, b, alll, g, out=OUT / "img" / f"{r.n:03d}.png", highlight=r.key, fetch=False)
        line = g.geometry[int(row.ID_TRC)]; p = row.geometry.representative_point()
        q = line.interpolate(line.project(p)); lon, lat = S.TO_LL.transform(q.x, q.y); plon, plat = S.TO_LL.transform(p.x, p.y)
        civ = str(row.civic_lo) + ("" if row.civic_hi == row.civic_lo else f"–{row.civic_hi}")
        items.append({"n": int(r.n), "key": r.key, "crop": r.crop, "label": int(r.label), "address": f"{civ} {str(row.NOM_RUE).split('(')[0].strip()}",
                      "dwellings": int(row.dwellings), "large": bool(row.large),
                      "sv": f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat:.6f},{lon:.6f}",
                      "map": f"https://www.google.com/maps/search/?api=1&query={plat:.6f},{plon:.6f}"})
    cards = "\n".join(f"""<section class="card" id="c{i['n']}" data-key="{i['key']}">
<h2>{i['n']} of {len(items)} · {html.escape(i['address'])} <small>{i['dwellings']} dwelling{'s' if i['dwellings'] != 1 else ''} · lot {i['label']} on crop {i['crop']}</small></h2>
<img loading="lazy" src="img/{i['n']:03d}.png" alt="aerial crop, lot outlined in red">
<p class="links"><a target="_blank" rel="noopener" href="{i['sv']}">Street-level view</a> · <a target="_blank" rel="noopener" href="{i['map']}">Map</a></p>
<div class="form">
<label>Car access <select data-f="car_access"><option value=""></option><option>yes</option><option>no</option><option>cannot tell</option></select></label>
<label>Kind <select data-f="kind"><option value=""></option><option>own driveway</option><option>shared driveway</option><option>front pad</option><option>rear</option><option>parking lot</option><option>none</option></select></label>
<label>Places, independent <input type="number" min="0" data-f="places_independent"></label>
<label>Places, total <input type="number" min="0" data-f="places_total"></label>
<label>Garage <select data-f="garage"><option value=""></option><option>yes</option><option>no</option><option>cannot tell</option></select></label>
<label>Judged from <select data-f="basis"><option value=""></option><option>street-level imagery</option><option>on the street</option><option>own knowledge</option><option>the aerial crop only</option></select></label>
<label class="wide">Note <input type="text" data-f="note"></label>
</div></section>""" for i in items)
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Private parking check</title>
<style>
:root{{--bg:#fbfbfa;--ink:#1f2428;--mut:#5f6b74;--line:#d9dcd8;--card:#fff;--acc:#2a78d6}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181a;--ink:#e8eaec;--mut:#a3adb5;--line:#33383c;--card:#1e2124;--acc:#6aa8ee}}}}
body{{background:var(--bg);color:var(--ink);font:16px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:0;padding:16px}}
main{{max-width:1100px;margin:0 auto}} h1{{font-size:1.4rem}} h2{{font-size:1.05rem;margin:0 0 8px}} h2 small{{color:var(--mut);font-weight:400;margin-left:8px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px;margin:18px 0}} .card.done{{border-color:var(--acc)}}
img{{max-width:100%;height:auto;border-radius:4px}} .links a{{color:var(--acc)}}
.form{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}} label{{display:flex;flex-direction:column;font-size:.85rem;color:var(--mut)}}
label.wide{{grid-column:1/-1}} select,input{{font:inherit;padding:6px;border:1px solid var(--line);border-radius:4px;background:var(--bg);color:var(--ink)}}
.bar{{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:2;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
button{{font:inherit;padding:7px 14px;border-radius:6px;border:1px solid var(--acc);background:var(--acc);color:#fff;cursor:pointer}}
details{{margin:10px 0}} li{{margin:4px 0}}
</style></head><body><main>
<h1>Private parking along the Terrebonne corridor: check of {len(items)} lots drawn at random</h1>
<div class="bar"><span id="count"></span><button id="export">Export the answers (JSON)</button><span style="color:var(--mut)">Answers are kept in this browser as you go.</span></div>
<details open><summary>What to judge</summary>
<ul>
<li><b>Car access:</b> can a car be driven off the street and left standing clear of the sidewalk, on a surface that serves the lot outlined in <b style="color:#e33">red</b>? Its own driveway, a driveway shared with the neighbour (both lots count), a front pad where a car fits between the sidewalk and the building even if part of it is on public ground, a rear pad off a lane or side street, or a parking lot.</li>
<li><b>Places, independent:</b> cars that can stand there and leave without another car being moved. A shared single-width passage itself holds none; count the lot's own space at the end of it.</li>
<li><b>Places, total:</b> all the cars the surface holds, one behind another included. Garage interiors are not counted in either number.</li>
<li><b>Garage:</b> yes if there is one (here you may count what you know or can see from the street).</li>
<li>The aerial image is older than the 2024 lane. Judge the lot as it is in the most recent view you have, and say in the note if it has changed.</li>
<li>« Cannot tell » is a valid answer.</li>
</ul></details>
{cards}
</main>
<script>
const K='corridor-parking-check-v1'; let st={{}}; try{{st=JSON.parse(localStorage.getItem(K)||'{{}}')}}catch(e){{}}
const cards=[...document.querySelectorAll('.card')];
function refresh(){{let n=0;cards.forEach(c=>{{const a=st[c.dataset.key]||{{}};const d=!!a.car_access;c.classList.toggle('done',d);if(d)n++}});document.getElementById('count').textContent=n+' of '+cards.length+' answered'}}
cards.forEach(c=>{{const a=st[c.dataset.key]||{{}};c.querySelectorAll('[data-f]').forEach(el=>{{if(a[el.dataset.f]!==undefined)el.value=a[el.dataset.f];el.addEventListener('change',()=>{{st[c.dataset.key]=st[c.dataset.key]||{{}};st[c.dataset.key][el.dataset.f]=el.value;try{{localStorage.setItem(K,JSON.stringify(st))}}catch(e){{}}refresh()}})}})}});
document.getElementById('export').addEventListener('click',()=>{{const out=cards.map(c=>Object.assign({{key:c.dataset.key,n:+c.id.slice(1)}},st[c.dataset.key]||{{}}));const b=new Blob([JSON.stringify({{exported:new Date().toISOString(),answers:out}},null,1)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='corridor_parking_check_'+new Date().toISOString().slice(0,10)+'.json';a.click()}});
refresh();
</script></body></html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    json.dump(items, open(OUT / "items.json", "w"), indent=1, ensure_ascii=False)
    print(f"check page: {OUT / 'index.html'} ({len(items)} lots: {sum(not i['large'] for i in items)} of five dwellings or fewer, {sum(i['large'] for i in items)} larger)")
    print("OK offstreet_check_page")


if __name__ == "__main__":
    main()
