"""Stage 5a: the reading frame for private parking and the imagery strips to read it from.

Frame: every building with at least one dwelling (City assessment roll; the condominium units of one building share
a lot outline and count as one building) whose lot lies in the corridor's 22 dissemination areas. Each building is
attached to the block face of the street of its address (the nearest géobase segment bearing that street's name,
and the side the lot is on) and numbered within that face.

Strips: for each block face (cut in two when longer than 130 m), the Gouvernement du Québec's continuous aerial
imagery (WMS Imagerie_Continue, layer Imagerie_GQ; leaf-off, about 8 cm per pixel; the mosaic predates the 2024
lane) resampled at 10 pixels per metre in the frame of the street segment (street at the bottom, lots above), with
every lot outlined and the buildings of the frame numbered. The images are kept outside the repository.

Outputs: derived/tables/offstreet_frame.csv (one row per building); strips in STRIPS (outside the repository)
Run:  ~/.venvs/omd/bin/python scripts/offstreet_strips.py [--no-fetch]
"""
import hashlib
import io
import sys
import time
import urllib.request

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from PIL import Image, ImageDraw, ImageFont
from pyproj import Transformer

from corridor_lib import CRS, DA_SHP, GEOBASE, ROLL, TABLES, TP

STRIPS = TP / "quebec-imagerie" / "corridor-blocks-2026-11-11"
WMS = ("https://servicesmatriciels.mern.gouv.qc.ca/erdas-iws/ogc/wms/Imagerie_Continue?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap"
       "&LAYERS=Imagerie_GQ&STYLES=&SRS=EPSG:4326&FORMAT=image/jpeg&BBOX={w:.6f},{s:.6f},{e:.6f},{n:.6f}&WIDTH={W}&HEIGHT={H}")
PPM, DEPTH, BACK, PAD, MAXLEN = 10, 52.0, 7.0, 12.0, 130.0
OUT = ("autoroute", "pont", "tunnel", "voie", "ruelle")
TO_LL = Transformer.from_crs(CRS, 4326, always_xy=True)


def last_word(s):
    s = str(s).split("(")[0].replace("-", " ").strip().lower()
    return s.split()[-1] if s else ""


def frame():
    cor = pd.read_csv(TABLES / "da_corridor.csv", dtype={"dauid": str})
    ids = cor[cor.set == "corridor"].dauid
    da = gpd.read_file(DA_SHP, columns=["DAUID"], where="DAUID LIKE '2466%'").to_crs(CRS)
    da = da[da.DAUID.isin(ids)]
    box = da.to_crs(4326).total_bounds
    r = pyogrio.read_dataframe(ROLL, bbox=tuple(box), columns=["ID_UEV", "CIVIQUE_DEBUT", "CIVIQUE_FIN", "NOM_RUE", "NOMBRE_LOGEMENT", "LIBELLE_UTILISATION", "ANNEE_CONSTRUCTION"]).to_crs(CRS)
    r["key"] = [hashlib.md5(g.wkb).hexdigest()[:12] for g in r.geometry]
    lots = r.drop_duplicates("key").set_index("key")
    agg = r.groupby("key").agg(dwellings=("NOMBRE_LOGEMENT", "sum"), units=("ID_UEV", "size"), uev_ids=("ID_UEV", lambda x: " ".join(sorted(map(str, x))[:6])),
                               civic_lo=("CIVIQUE_DEBUT", "min"), civic_hi=("CIVIQUE_FIN", "max"))
    lots = lots[["NOM_RUE", "LIBELLE_UTILISATION", "ANNEE_CONSTRUCTION", "geometry"]].join(agg)
    pt = gpd.GeoDataFrame(lots[[]], geometry=lots.geometry.representative_point(), crs=CRS)
    lots["dauid"] = gpd.sjoin(pt, da, predicate="within", how="left").DAUID.reindex(lots.index)
    alll = lots.copy()                                             # every lot, for the outlines
    b = lots[(lots.dwellings.fillna(0) > 0) & lots.dauid.notna()].copy()
    g = gpd.read_file(GEOBASE).to_crs(CRS)
    g = g[~g.TYP_VOIE.isin(OUT)].cx[da.total_bounds[0] - 200:da.total_bounds[2] + 200, da.total_bounds[1] - 200:da.total_bounds[3] + 200].reset_index(drop=True)
    g["w"] = g.NOM_VOIE.map(last_word)
    seg, side, tpos = [], [], []
    for key, row in b.iterrows():
        p = row.geometry.representative_point(); w = last_word(row.NOM_RUE)
        cand = g[g.w == w]
        d = cand.geometry.distance(row.geometry) if len(cand) else pd.Series(dtype=float)
        if len(d) == 0 or d.min() > 45:
            cand = g; d = cand.geometry.distance(row.geometry)
        i = d.idxmin(); line = g.geometry[i]; t = line.project(p)
        a = line.interpolate(max(t - 1, 0)); c = line.interpolate(min(t + 1, line.length))
        cr = (c.x - a.x) * (p.y - a.y) - (c.y - a.y) * (p.x - a.x)
        seg.append(int(g.ID_TRC[i])); side.append("L" if cr > 0 else "R"); tpos.append(t)
    b["ID_TRC"], b["side"], b["t"] = seg, side, tpos
    L = g.set_index("ID_TRC").geometry.length
    b["part"] = [0 if L[s] <= MAXLEN else int(t >= L[s] / 2) for s, t in zip(b.ID_TRC, b.t)]
    b["strip"] = [f"{s}{sd}{p}" for s, sd, p in zip(b.ID_TRC, b.side, b.part)]
    b = b.sort_values(["strip", "t"])
    b["label"] = b.groupby("strip").cumcount() + 1
    b["street"] = b.ID_TRC.map(g.set_index("ID_TRC").NOM_VOIE)
    b["large"] = b.dwellings > 5
    out = b.reset_index()[["strip", "label", "key", "street", "NOM_RUE", "civic_lo", "civic_hi", "dwellings", "units", "large", "LIBELLE_UTILISATION",
                           "ANNEE_CONSTRUCTION", "dauid", "ID_TRC", "side", "uev_ids"]].rename(columns={"NOM_RUE": "roll_street", "LIBELLE_UTILISATION": "use", "ANNEE_CONSTRUCTION": "year_built"})
    out.to_csv(TABLES / "offstreet_frame.csv", index=False)
    print(f"buildings in the frame: {len(out)} ({int(out.large.sum())} of six dwellings or more); dwellings {int(out.dwellings.sum())}; strips: {out.strip.nunique()}; largest strip: {out.groupby('strip').size().max()} buildings")
    return b, alll, g.set_index("ID_TRC")


def render(strip, bs, alll, g, fetch=True):
    trc = int(bs.ID_TRC.iloc[0]); sd = bs.side.iloc[0]; part = int(bs.part.iloc[0])
    line = g.geometry[trc]; L = line.length
    u0, u1 = (0, L) if L <= MAXLEN else ((0, L / 2) if part == 0 else (L / 2, L))
    u0 -= PAD; u1 += PAD
    a, c = np.array(line.coords[0]), np.array(line.coords[-1])
    # straight frame through the segment's ends (the corridor's segments are straight or nearly so)
    e = (c - a) / np.linalg.norm(c - a); n = np.array([-e[1], e[0]]) * (1 if sd == "L" else -1)
    W, H = int((u1 - u0) * PPM), int((DEPTH + BACK) * PPM)
    uu = u0 + (np.arange(W) + 0.5) / PPM; vv = DEPTH - (np.arange(H) + 0.5) / PPM
    if sd == "R":
        uu = uu[::-1]                                             # keep the street at the bottom and the image unmirrored
    U, V = np.meshgrid(uu, vv)
    X = a[0] + U * e[0] + V * n[0]; Y = a[1] + U * e[1] + V * n[1]
    lon, lat = TO_LL.transform(X, Y)
    w, s_, e_, n_ = lon.min() - 2e-5, lat.min() - 2e-5, lon.max() + 2e-5, lat.max() + 2e-5
    raw = STRIPS / "wms" / f"{strip}.jpg"
    if not raw.exists():
        if not fetch:
            return False
        mx = (e_ - w) * 78500; my = (n_ - s_) * 111200
        url = WMS.format(w=w, s=s_, e=e_, n=n_, W=int(mx / 0.08), H=int(my / 0.08))
        req = urllib.request.Request(url, headers={"User-Agent": "corridor-imagery-reader/1.0"})
        data = urllib.request.urlopen(req, timeout=180).read()
        Image.open(io.BytesIO(data)).verify()
        raw.write_bytes(data); time.sleep(0.6)
    src = np.asarray(Image.open(raw).convert("RGB")); sh, sw = src.shape[:2]
    col = np.clip(((lon - w) / (e_ - w) * sw).astype(int), 0, sw - 1); rw = np.clip(((n_ - lat) / (n_ - s_) * sh).astype(int), 0, sh - 1)
    im = Image.fromarray(src[rw, col]); d = ImageDraw.Draw(im, "RGBA")
    f1 = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20); f2 = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)

    def P(x, y):
        q = np.array([x, y]) - a; u = q @ e; v = q @ n
        px = (u - u0) * PPM if sd == "L" else (u1 - u) * PPM
        return (px, (DEPTH - v) * PPM)

    near = alll[alll.geometry.distance(line) < DEPTH + 15]
    for key, row in near.iterrows():
        polys = row.geometry.geoms if row.geometry.geom_type == "MultiPolygon" else [row.geometry]
        mine = key in bs.index
        for poly in polys:
            pts = [P(x, y) for x, y in poly.exterior.coords]
            if not any(-20 < px < W + 20 and -20 < py < H + 20 for px, py in pts):
                continue
            d.line(pts, fill=(255, 220, 0, 255) if mine else (0, 200, 255, 150), width=3 if mine else 1)
    for key, row in bs.iterrows():
        p = row.geometry.representative_point(); x, y = P(p.x, p.y)
        x = min(max(x, 4), W - 60); y = min(max(y, 4), H - 44)
        lab = str(int(row.label)) + ("*" if row.large else "")
        d.rectangle([x - 3, y - 2, x + 14 + 11 * len(lab), y + 22], fill=(255, 220, 0, 235)); d.text((x, y), lab, fill=(0, 0, 0, 255), font=f1)
        civ = str(row.civic_lo) + ("" if row.civic_hi == row.civic_lo else f"-{row.civic_hi}")
        d.rectangle([x - 3, y + 23, x + 8 + 7 * len(civ), y + 38], fill=(255, 255, 255, 200)); d.text((x, y + 24), civ, fill=(0, 0, 0, 255), font=f2)
    d.rectangle([0, H - 20, W, H], fill=(0, 0, 0, 170))
    d.text((6, H - 18), f"strip {strip}   {g.NOM_VOIE[trc]}   street at the bottom, lots above   10 px = 1 m   yellow = buildings to read (* = six dwellings or more)", fill=(255, 255, 255, 255), font=f2)
    im.save(STRIPS / f"{strip}.png")
    return True


def main():
    (STRIPS / "wms").mkdir(parents=True, exist_ok=True)
    b, alll, g = frame()
    only = next((a.split("=")[1].split(",") for a in sys.argv if a.startswith("--only=")), None)
    n = 0
    for strip, bs in b.groupby("strip"):
        if only and strip not in only:
            continue
        n += render(strip, bs, alll, g, fetch="--no-fetch" not in sys.argv)
    print(f"strips rendered: {n} -> {STRIPS}")
    print("OK offstreet_strips")


if __name__ == "__main__":
    main()
