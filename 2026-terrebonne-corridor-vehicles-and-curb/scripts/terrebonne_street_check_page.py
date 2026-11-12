"""The owner's street-level check of every building addressed on rue de Terrebonne along the lane (owner's decision,
Nov 12, 2026): it replaces the aerial reading of October 25, 2026 behind the « 89 of 123 buildings, 72 % » of the
1954 folder and the parking note, because the owner's check of the corridor sample showed that a view from above
misses driveways (readers' « no » wrong in 15 of 23).

Frame (owner, Nov 12): every lot of the City's assessment roll addressed on rue de Terrebonne whose point projects
onto the lane (west end just west of Belmore to Girouard), plus any residential row of the 1954 table
(buildings_geo.csv, addressed on Terrebonne, inside the lane) that no such lot matches. Each card shows the lot's
enlarged aerial crop with the lot outlined in red, its address as an Apple Maps Look Around link, and the same form
as the corridor check. The page shows NO earlier reading (neither the October 25 aerial reading nor the 1954 plans);
the lots the owner already judged in the corridor sample of 112 are pre-filled with his own answers, marked, and
editable (owner's choice, Nov 12). New storage key: terrebonne-street-check-v1.

Outputs: ~/Terrebonne-data/terrebonne-street-check/{index.html, items.json, img/}  (working page, outside git)
         ../1954-underwriters-plans-terrebonne-garages/derived/street_check_frame.csv  (the frame, no reading)
Run:  ~/.venvs/omd/bin/python scripts/terrebonne_street_check_page.py     (after offstreet_crops.py)
"""
import csv
import html
import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from shapely.ops import linemerge

import offstreet_crops as C
import offstreet_strips as S
from corridor_lib import CRS, GARAGES, LANE, ROOT, TABLES

OUT = Path.home() / "Terrebonne-data" / "terrebonne-street-check"
FRAME = GARAGES / "street_check_frame.csv"
OWNER = ROOT / "derived" / "readings" / "owner_check.json"
KEY = "terrebonne-street-check-v1"
FIELDS = ("car_access", "kind", "places_independent", "places_total", "garage", "basis", "note")


def in_lane_1954(r):
    t = r["building_type"].lower()
    return (r["addressed_on"] == "Terrebonne" and "outside the lane" not in r["cross_streets"]
            and not any(k in t for k in ("institutional", "vacant")) and r["garage_1954"] in ("yes", "no"))


def main():
    b, alll, g = S.frame()
    crops = pd.read_csv(TABLES / "offstreet_crops.csv")
    lane = gpd.read_file(LANE).to_crs(CRS).geometry.union_all()
    lane = linemerge(lane) if lane.geom_type == "MultiLineString" else lane
    L = lane.length

    def along(geom):
        p = geom.representative_point(); return lane.project(p), lane.distance(p)

    t = b[b.NOM_RUE.str.contains("Terrebonne", na=False)].copy()
    pos = [along(gm) for gm in t.geometry]
    t["t"], t["dist"] = [p[0] for p in pos], [p[1] for p in pos]
    beyond = t[(t.t <= 1.0) | (t.t >= L - 1.0) | (t.dist > 45)]
    t = t.drop(beyond.index)

    # the 1954 table: match by roll unit, then by the point
    u2k = {}
    for key, r in b.iterrows():
        for u in str(r.uev_ids).split():
            u2k[u.zfill(8)] = key
    rows = [r for r in csv.DictReader(open(GARAGES / "buildings_geo.csv", encoding="utf-8")) if in_lane_1954(r)]
    match, extra = {}, []
    for r in rows:
        ks = {u2k.get(u.zfill(8)) for u in re.split("[; ]", r["uev_id"]) if u} - {None}
        if not ks:
            p = gpd.GeoSeries([Point(float(r["lon"]), float(r["lat"]))], crs=4326).to_crs(CRS).iloc[0]
            hit = b[b.geometry.contains(p)]
            ks = set(hit.index[:1])
        if ks:
            for k in ks:
                match.setdefault(k, []).append(f"{r['sheet']} {r['side']} {r['civic_numbers']}")
        else:
            extra.append(r)
    for k in match:
        if k not in t.index and k in b.index:            # a 1954 Terrebonne building whose roll lot is addressed elsewhere
            row = b.loc[[k]].copy(); p = along(row.geometry.iloc[0]); row["t"], row["dist"] = p
            t = pd.concat([t, row])
    print(f"roll lots on Terrebonne along the lane: {len(t)} (dropped beyond the lane: {len(beyond)}: "
          f"{', '.join(str(x) for x in sorted(beyond.civic_lo))}); 1954 rows: {len(rows)}, matched to a lot {len(rows) - len(extra)}, unmatched {len(extra)}")
    for r in extra:
        print("   unmatched 1954 row:", r["sheet"], r["side"], r["civic_numbers"], r["building_type"])

    # the owner's answers already given in the corridor sample (pre-filled, editable)
    pre = {a["key"]: {f: a.get(f, "") for f in FIELDS} for a in json.load(open(OWNER))["answers"] if a["key"] in t.index and a.get("car_access")}

    # order: north side west to east, then south side west to east
    lane_side = []
    for gm in t.geometry:
        p = gm.representative_point(); s = lane.project(p)
        a = lane.interpolate(max(s - 1, 0)); c = lane.interpolate(min(s + 1, L))
        lane_side.append("N" if (c.x - a.x) * (p.y - a.y) - (c.y - a.y) * (p.x - a.x) > 0 else "S")
    t["lane_side"] = lane_side
    # the geobase line runs east to west or west to east: orient so that t grows eastward
    east = lane.interpolate(L).x > lane.interpolate(0).x
    t["east_m"] = t.t if east else L - t.t
    if not east:
        t["lane_side"] = t.lane_side.map({"N": "S", "S": "N"})
    t = t.sort_values(["lane_side", "east_m"])

    (OUT / "img").mkdir(parents=True, exist_ok=True)
    items, frame = [], []
    for n, (key, row) in enumerate(t.iterrows(), start=1):
        cr = crops[crops.key == key].iloc[0]
        C.render(cr.crop, crops[crops.crop == cr.crop], b, alll, g, out=OUT / "img" / f"{n:03d}.png", highlight=key, fetch=False)
        p = row.geometry.representative_point(); plon, plat = S.TO_LL.transform(p.x, p.y)
        line = g.geometry[int(row.ID_TRC)]; q = line.interpolate(line.project(p)); lon, lat = S.TO_LL.transform(q.x, q.y)
        lo, hi = str(row.civic_lo).strip(), str(row.civic_hi).strip()
        civ = lo + ("" if hi == lo else f"–{hi}")
        street = str(row.NOM_RUE).split("(")[0].strip()
        if "Terrebonne" not in street and match.get(key):                # corner lot: give its Terrebonne frontage number (no reading)
            street += " (corner; Terrebonne frontage " + ", ".join(m.split(" ", 2)[2] for m in match[key]) + ")"
        items.append({"n": n, "key": key, "crop": cr.crop, "label": int(cr.label), "address": f"{civ} {street}", "side": row.lane_side,
                      "dwellings": int(row.dwellings), "large": bool(row.large), "prefill": pre.get(key),
                      "apple": f"https://maps.apple.com/look-around?coordinate={plat:.6f},{plon:.6f}",
                      "sv": f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat:.6f},{lon:.6f}",
                      "map": f"https://www.google.com/maps/search/?api=1&query={plat:.6f},{plon:.6f}"})
        frame.append({"n": n, "key": key, "civic_lo": lo, "civic_hi": hi, "roll_street": str(row.NOM_RUE).split("(")[0].strip(), "side": row.lane_side,
                      "east_m": round(row.east_m, 1), "dwellings": int(row.dwellings), "large": bool(row.large), "year_built": row.ANNEE_CONSTRUCTION,
                      "uev_ids": row.uev_ids, "rows_1954": "; ".join(match.get(key, [])), "in_owner_sample": key in pre})
    pd.DataFrame(frame).to_csv(FRAME, index=False)

    def card(i):
        pf = i["prefill"]
        tag = ('<p class="pre">Pre-filled with your own answers from the corridor check (sample of 112). Change anything that is wrong.</p>' if pf else "")
        return f"""<section class="card" id="c{i['n']}" data-key="{i['key']}"{' data-pre=' + chr(39) + html.escape(json.dumps(pf)) + chr(39) if pf else ''}>
<h2>{i['n']} of {len(items)} · <a target="_blank" rel="noopener" href="{i['apple']}" title="Open in Apple Maps, Look Around">{html.escape(i['address'])}</a> <small>{i['side']} side · {i['dwellings']} dwelling{'s' if i['dwellings'] != 1 else ''} · lot {i['label']} on crop {i['crop']}</small></h2>
{tag}<img loading="lazy" src="img/{i['n']:03d}.png" alt="aerial crop, lot outlined in red">
<p class="links"><a target="_blank" rel="noopener" href="{i['apple']}">Apple Maps (Look Around)</a> · <a target="_blank" rel="noopener" href="{i['sv']}">Google street-level view</a> · <a target="_blank" rel="noopener" href="{i['map']}">Google map</a></p>
<div class="form">
<label>Car access <select data-f="car_access"><option value=""></option><option>yes</option><option>no</option><option>cannot tell</option></select></label>
<label>Kind <select data-f="kind"><option value=""></option><option>own driveway</option><option>shared driveway</option><option>front pad</option><option>rear</option><option>parking lot</option><option>none</option></select></label>
<label>Places, independent <input type="number" min="0" data-f="places_independent"></label>
<label>Places, total <input type="number" min="0" data-f="places_total"></label>
<label>Garage <select data-f="garage"><option value=""></option><option>yes</option><option>no</option><option>cannot tell</option></select></label>
<label>Judged from <select data-f="basis"><option value=""></option><option>street-level imagery</option><option>on the street</option><option>own knowledge</option><option>the aerial crop only</option></select></label>
<label class="wide">Note <input type="text" data-f="note"></label>
</div></section>"""

    nside = {s: sum(i["side"] == s for i in items) for s in "NS"}
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Terrebonne street check</title>
<style>
:root{{--bg:#fbfbfa;--ink:#1f2428;--mut:#5f6b74;--line:#d9dcd8;--card:#fff;--acc:#2a78d6;--pre:#8a5a00}}
@media (prefers-color-scheme:dark){{:root{{--bg:#16181a;--ink:#e8eaec;--mut:#a3adb5;--line:#33383c;--card:#1e2124;--acc:#6aa8ee;--pre:#e0b05a}}}}
body{{background:var(--bg);color:var(--ink);font:16px/1.45 -apple-system,Helvetica,Arial,sans-serif;margin:0;padding:16px}}
main{{max-width:1100px;margin:0 auto}} h1{{font-size:1.4rem}} h2{{font-size:1.05rem;margin:0 0 8px}} h2 small{{color:var(--mut);font-weight:400;margin-left:8px}} h2 a{{color:var(--acc)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px;margin:18px 0}} .card.done{{border-color:var(--acc)}}
.pre{{color:var(--pre);font-size:.9rem;margin:0 0 8px}}
img{{max-width:100%;height:auto;border-radius:4px}} .links a{{color:var(--acc)}}
.form{{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:10px}} label{{display:flex;flex-direction:column;font-size:.85rem;color:var(--mut)}}
label.wide{{grid-column:1/-1}} select,input{{font:inherit;padding:6px;border:1px solid var(--line);border-radius:4px;background:var(--bg);color:var(--ink)}}
.bar{{position:sticky;top:0;background:var(--bg);padding:8px 0;border-bottom:1px solid var(--line);z-index:2;display:flex;gap:12px;align-items:center;flex-wrap:wrap}}
button{{font:inherit;padding:7px 14px;border-radius:6px;border:1px solid var(--acc);background:var(--acc);color:#fff;cursor:pointer}}
details{{margin:10px 0}} li{{margin:4px 0}}
</style></head><body><main>
<h1>Rue de Terrebonne, building by building: street-level check of {len(items)} lots</h1>
<p style="color:var(--mut)">Every lot addressed on Terrebonne along the lane, west end to Girouard: north side west to east (cards 1–{nside['N']}), then south side west to east (cards {nside['N'] + 1}–{len(items)}). {len(pre)} cards are pre-filled with your answers from the corridor sample.</p>
<div class="bar"><span id="count"></span><button id="export">Export the answers (JSON)</button><span style="color:var(--mut)">Answers are kept in this browser as you go.</span></div>
<details open><summary>What to judge</summary>
<ul>
<li><b>Car access:</b> can a car be driven off the street and left standing clear of the sidewalk, on a surface that serves the lot outlined in <b style="color:#e33">red</b>? Its own driveway, a driveway shared with the neighbour (both lots count), a front pad where a car fits between the sidewalk and the building even if part of it is on public ground, a rear pad off a lane or side street, or a parking lot.</li>
<li><b>Places, independent:</b> cars that can stand there and leave without another car being moved. A shared single-width passage itself holds none; count the lot's own space at the end of it.</li>
<li><b>Places, total:</b> all the cars the surface holds, one behind another included. Garage interiors are not counted in either number.</li>
<li><b>Garage:</b> yes if there is one today (here you may count what you know or can see from the street).</li>
<li>The aerial image is older than the 2024 lane. Judge the lot as it is in the most recent view you have, and say in the note if it has changed.</li>
<li>« Cannot tell » is a valid answer.</li>
</ul></details>
{chr(10).join(card(i) for i in items)}
</main>
<script>
const K='{KEY}'; let st={{}}; try{{st=JSON.parse(localStorage.getItem(K)||'{{}}')}}catch(e){{}}
const cards=[...document.querySelectorAll('.card')];
cards.forEach(c=>{{if(c.dataset.pre&&!st[c.dataset.key]){{st[c.dataset.key]=Object.assign({{prefilled:'owner_check corridor sample'}},JSON.parse(c.dataset.pre))}}}});
try{{localStorage.setItem(K,JSON.stringify(st))}}catch(e){{}}
function refresh(){{let n=0;cards.forEach(c=>{{const a=st[c.dataset.key]||{{}};const d=!!a.car_access;c.classList.toggle('done',d);if(d)n++}});document.getElementById('count').textContent=n+' of '+cards.length+' answered'}}
cards.forEach(c=>{{const a=st[c.dataset.key]||{{}};c.querySelectorAll('[data-f]').forEach(el=>{{if(a[el.dataset.f]!==undefined)el.value=a[el.dataset.f];el.addEventListener('change',()=>{{st[c.dataset.key]=st[c.dataset.key]||{{}};st[c.dataset.key][el.dataset.f]=el.value;st[c.dataset.key].edited=new Date().toISOString();try{{localStorage.setItem(K,JSON.stringify(st))}}catch(e){{}}refresh()}})}})}});
document.getElementById('export').addEventListener('click',()=>{{const out=cards.map(c=>Object.assign({{key:c.dataset.key,n:+c.id.slice(1)}},st[c.dataset.key]||{{}}));const b=new Blob([JSON.stringify({{exported:new Date().toISOString(),page:K,answers:out}},null,1)],{{type:'application/json'}});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='terrebonne_street_check_'+new Date().toISOString().slice(0,10)+'.json';a.click()}});
refresh();
</script></body></html>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    json.dump(items, open(OUT / "items.json", "w"), indent=1, ensure_ascii=False)
    print(f"check page: {OUT / 'index.html'} ({len(items)} lots: N {nside['N']}, S {nside['S']}; {sum(i['large'] for i in items)} of six dwellings or more; pre-filled {len(pre)})")
    print(f"frame: {FRAME}")
    print("OK terrebonne_street_check_page")


if __name__ == "__main__":
    main()
