"""Stage 5a, second pass: enlarged, shadow-lifted crops for reading private parking lot by lot.

Each crop shows up to five neighbouring lots of one strip (one side of one street segment) at 20 pixels per metre
(a building of six dwellings or more, or a lot too large for that scale, gets a crop of its own at a smaller
scale), from the roadway's edge to the rear of the lots, in the frame of the street segment: street at the bottom.
The imagery is the Gouvernement du Québec's continuous aerial imagery (WMS Imagerie_Continue, layer Imagerie_GQ,
about 8 cm per pixel, leaf-off). Dark tones are lifted (y = 1.25 x / (x + 0.25) on each channel) so that surfaces
in building shadow can be seen; nothing else is altered. Crops are kept outside the repository.

Outputs: derived/tables/offstreet_crops.csv (crop, strip, label, key, px_per_m); images in CROPS
Run:  ~/.venvs/omd/bin/python scripts/offstreet_crops.py [--only=<crop>,...] [--highlight=<key>:<outfile>]
"""
import io
import sys
import time
import urllib.request

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

import offstreet_strips as S
from corridor_lib import TABLES, TP

CROPS = TP / "quebec-imagerie" / "corridor-crops-2026-11-11"
GROUP, PPM, MAXPX, V0, MARGIN = 5, 20.0, 1150, 2.5, 4.0
A_LIFT = 0.25


def uv_frame(line, sd):
    a, c = np.array(line.coords[0]), np.array(line.coords[-1])
    e = (c - a) / np.linalg.norm(c - a); n = np.array([-e[1], e[0]]) * (1 if sd == "L" else -1)
    return a, e, n


def lot_uv(geom, a, e, n):
    polys = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    out = []
    for p in polys:
        q = np.array(p.exterior.coords) - a
        out.append(np.c_[q @ e, q @ n])
    return out


def groups(b, g):
    rows = []
    for strip, bs in b.groupby("strip"):
        line = g.geometry[int(bs.ID_TRC.iloc[0])]; a, e, n = uv_frame(line, bs.side.iloc[0])
        cur, k = [], 0
        def flush():
            nonlocal cur, k
            if cur:
                k += 1
                rows.extend({"crop": f"{strip}_{k}", "strip": strip, "label": int(r.label), "key": key} for key, r in cur)
                cur = []
        for key, r in bs.sort_values("label").iterrows():
            uv = np.vstack(lot_uv(r.geometry, a, e, n))
            big = r.large or (uv[:, 0].max() - uv[:, 0].min()) > 32 or uv[:, 1].max() > 62
            if big:
                flush(); cur = [(key, r)]; flush()
            else:
                cur.append((key, r))
                if len(cur) == GROUP:
                    flush()
        flush()
    return pd.DataFrame(rows)


def render(crop, rows, b, alll, g, out=None, highlight=None, fetch=True):
    bs = b.loc[rows.key]
    line = g.geometry[int(bs.ID_TRC.iloc[0])]; sd = bs.side.iloc[0]; a, e, n = uv_frame(line, sd)
    uv = np.vstack([np.vstack(lot_uv(geom, a, e, n)) for geom in bs.geometry])
    u0, u1 = uv[:, 0].min() - MARGIN, uv[:, 0].max() + MARGIN
    v0, v1 = min(V0, uv[:, 1].min() - 7.5), uv[:, 1].max() + 3.0
    ppm = min(PPM, MAXPX / (u1 - u0), MAXPX / (v1 - v0))
    W, H = int((u1 - u0) * ppm), int((v1 - v0) * ppm)
    uu = u0 + (np.arange(W) + 0.5) / ppm; vv = v1 - (np.arange(H) + 0.5) / ppm
    if sd == "R":
        uu = uu[::-1]
    U, V = np.meshgrid(uu, vv)
    X = a[0] + U * e[0] + V * n[0]; Y = a[1] + U * e[1] + V * n[1]
    lon, lat = S.TO_LL.transform(X, Y)
    w, s_, e_, n_ = lon.min() - 2e-5, lat.min() - 2e-5, lon.max() + 2e-5, lat.max() + 2e-5
    raw = CROPS / "wms" / f"{crop}.jpg"
    if not raw.exists():
        if not fetch:
            return None
        mx = (e_ - w) * 78500; my = (n_ - s_) * 111200
        url = S.WMS.format(w=w, s=s_, e=e_, n=n_, W=int(mx / 0.08), H=int(my / 0.08))
        req = urllib.request.Request(url, headers={"User-Agent": "corridor-imagery-reader/1.0"})
        data = urllib.request.urlopen(req, timeout=180).read()
        Image.open(io.BytesIO(data)).verify()
        raw.write_bytes(data); time.sleep(0.5)
    src = np.asarray(Image.open(raw).convert("RGB")).astype(np.float32) / 255.0; sh, sw = src.shape[:2]
    # bilinear sampling
    fx = np.clip((lon - w) / (e_ - w) * sw - 0.5, 0, sw - 1.001); fy = np.clip((n_ - lat) / (n_ - s_) * sh - 0.5, 0, sh - 1.001)
    x0 = fx.astype(int); y0 = fy.astype(int); dx = (fx - x0)[..., None]; dy = (fy - y0)[..., None]
    img = (src[y0, x0] * (1 - dx) * (1 - dy) + src[y0, x0 + 1] * dx * (1 - dy) + src[y0 + 1, x0] * (1 - dx) * dy + src[y0 + 1, x0 + 1] * dx * dy)
    img = (1 + A_LIFT) * img / (img + A_LIFT)
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im, "RGBA")
    f1 = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22); f2 = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)

    def P(u, v):
        return ((u - u0) * ppm if sd == "L" else (u1 - u) * ppm, (v1 - v) * ppm)

    near = alll[alll.geometry.distance(line) < v1 + 10]
    for key, row in near.iterrows():
        mine = key in bs.index
        for q in lot_uv(row.geometry, a, e, n):
            if q[:, 0].max() < u0 - 5 or q[:, 0].min() > u1 + 5:
                continue
            pts = [P(x, y) for x, y in q]
            if highlight and key == highlight:
                d.line(pts, fill=(255, 40, 40, 255), width=4)
            elif mine:
                d.line(pts, fill=(255, 225, 0, 230), width=2)
            else:
                d.line(pts, fill=(0, 200, 255, 110), width=1)
    for key, row in bs.iterrows():
        q = np.vstack(lot_uv(row.geometry, a, e, n))
        x, y = P(q[:, 0].mean(), q[:, 1].max() - 3.0)
        lab = str(int(row.label)) + ("*" if row.large else "")
        x = min(max(x - 12, 3), W - 80); y = min(max(y, 3), H - 60)
        col = (255, 90, 90, 240) if highlight and key == highlight else (255, 225, 0, 235)
        d.rectangle([x - 3, y - 2, x + 14 + 12 * len(lab), y + 24], fill=col); d.text((x, y), lab, fill=(0, 0, 0, 255), font=f1)
        civ = str(row.civic_lo) + ("" if row.civic_hi == row.civic_lo else f"-{row.civic_hi}")
        d.rectangle([x - 3, y + 25, x + 8 + 8 * len(civ), y + 41], fill=(255, 255, 255, 215)); d.text((x, y + 26), civ, fill=(0, 0, 0, 255), font=f2)
    d.rectangle([0, H - 20, W, H], fill=(0, 0, 0, 175))
    d.text((6, H - 18), f"{crop}  {g.NOM_VOIE[int(bs.ID_TRC.iloc[0])]}  street at the bottom  {ppm:.0f} px = 1 m  car = {4.7 * ppm:.0f} x {1.9 * ppm:.0f} px  shadows lifted", fill=(255, 255, 255, 255), font=f2)
    im.save(out or (CROPS / f"{crop}.png"))
    return ppm


def main():
    (CROPS / "wms").mkdir(parents=True, exist_ok=True)
    b, alll, g = S.frame()
    t = groups(b, g)
    only = next((x.split("=")[1].split(",") for x in sys.argv if x.startswith("--only=")), None)
    ppms = {}
    for crop, rows in t.groupby("crop", sort=False):
        if only and crop not in only:
            continue
        ppms[crop] = render(crop, rows, b, alll, g)
    if not only:
        t["px_per_m"] = t.crop.map(ppms).round(1)
        t.to_csv(TABLES / "offstreet_crops.csv", index=False)
    print(f"crops: {t.crop.nunique()} for {len(t)} buildings; rendered {len(ppms)} -> {CROPS}")
    print("OK offstreet_crops")


if __name__ == "__main__":
    main()
