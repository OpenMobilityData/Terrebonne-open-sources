"""Stage 2: legal curb by block face in the two FSAs of the lane (H4A, H4B), from the City's géobase and its
sign inventory, and each face's dissemination area.

A block face is one side of one géobase segment. Its legal curb is its length, less 5 m at each end
(assumption for intersections), less the stretches where a sign forbids stopping or parking at all times
(« \\A EN TOUT TEMPS », « \\P EN TOUT TEMPS »). The stretch a sign governs runs from its pole to the next pole
in the direction of its arrow; a sign without an arrow governs the stretches on both sides of its pole. The arrow
coding is the one found on the whole City in Quebec-vehicle-registrations/scripts/street_space.py, except on a
face where the other coding leaves fewer stretches claimed both by an all-time prohibition and by another
parking rule (hours, days, time limit, permit: a rule that implies parking exists there); a stretch still claimed
both ways counts for half. This reading is finer than street_space.py's (which counts a sign without an arrow for
half of each stretch), and was checked on rue de Terrebonne, where the layout is known. Driveways, hydrants, bus
stops, hourly rules, permit zones and the seasonal rules are not deducted: this is an upper bound on legal curb.

A face belongs to the dissemination area that contains the point 12 m to its side of the segment's midpoint
(dissemination-area boundaries follow street centre lines).

Outputs (derived/tables/): block_faces.csv, block_faces.geojson, curb_by_da.csv, terrebonne_curb_by_block.csv
Run:  ~/.venvs/omd/bin/python scripts/curb_supply.py
"""
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import line_locate_point
from shapely.geometry import Point

from corridor_lib import CRS, DA_SHP, FSAS, GEOBASE, LANE, SIGNS, TABLES

OUT = ("autoroute", "pont", "tunnel", "voie", "ruelle")
END = 5.0
SIDE_OFFSET = 12.0
BANS = ["\\A EN TOUT TEMPS", "\\P EN TOUT TEMPS"]


def study_area():
    sh = pd.read_csv(TABLES / "da_fsa_shares.csv", dtype={"dauid": str})
    ids = sh[sh.fsa.isin(FSAS)].dauid.unique()
    da = gpd.read_file(DA_SHP, columns=["DAUID"], where="DAUID LIKE '2466%'").to_crs(CRS)
    return da[da.DAUID.isin(ids)].reset_index(drop=True)


def side_of(line, t, L, pts):
    a = gpd.GeoSeries(line, crs=CRS).interpolate(np.clip(t - 1, 0, None)).values
    b = gpd.GeoSeries(line, crs=CRS).interpolate(np.clip(t + 1, None, L)).values
    ax, ay, bx, by = [np.array(v) for v in ([p.x for p in a], [p.y for p in a], [p.x for p in b], [p.y for p in b])]
    cross = (bx - ax) * (np.array([p.y for p in pts]) - ay) - (by - ay) * (np.array([p.x for p in pts]) - ax)
    return np.where(cross > 0, "L", "R"), (ax, ay, bx, by)


def main():
    da = study_area()
    box = da.total_bounds + np.array([-300, -300, 300, 300])
    g = gpd.read_file(GEOBASE).to_crs(CRS)
    g = g[~g.TYP_VOIE.isin(OUT)].cx[box[0]:box[2], box[1]:box[3]].reset_index(drop=True)
    g["L"] = g.geometry.length
    s = pd.read_csv(SIGNS, dtype=str)
    s = s[(s.DESCRIPTION_REP == "Réel") & s.PAS_SUR_RUE.isna() & (s.DESCRIPTION_CAT == "STATIONNEMENT")]
    s["x"] = s.X.astype(float); s["y"] = s.Y.astype(float)
    s = s[s.x.between(box[0], box[2]) & s.y.between(box[1], box[3])]
    s["ban"] = s.DESCRIPTION_RPA.str.strip().isin(BANS)
    poles = s.groupby("POTEAU_ID_POT").agg(x=("x", "first"), y=("y", "first"), installed=("DATE_CONCEPTION_POT", "max")).reset_index()
    pg = gpd.GeoDataFrame(poles, geometry=gpd.points_from_xy(poles.x, poles.y), crs=CRS)
    j = gpd.sjoin_nearest(pg, g[["ID_TRC", "L", "geometry"]], max_distance=20, distance_col="d").drop_duplicates("POTEAU_ID_POT")
    line = g.geometry.loc[j.index_right].values
    j["t"] = line_locate_point(line, j.geometry.values)
    j["side"], _ = side_of(line, j.t.values, j.L.values, j.geometry.values)
    pol = j[["POTEAU_ID_POT", "ID_TRC", "L", "t", "side"]]
    sg = s[s.POTEAU_ID_POT.isin(pol.POTEAU_ID_POT)][["POTEAU_ID_POT", "FLECHE_PAN", "ban"]].copy()
    sg["arrow"] = pd.to_numeric(sg.FLECHE_PAN, errors="coerce").fillna(0).astype(int)
    signmap = {k: list(zip(v.arrow, v.ban)) for k, v in sg.groupby("POTEAU_ID_POT")}
    groups = {k: v.sort_values("t") for k, v in pol.groupby(["ID_TRC", "side"])}

    def claims(ids, side, code2_forward_on_right):
        """Per stretch between neighbouring poles (and the two ends): claimed by an all-time prohibition, claimed
        by another parking rule (hours, days, time limit, permit: parking exists there)."""
        n = len(ids) - 1; ban = np.zeros(n, dtype=bool); other = np.zeros(n, dtype=bool)
        for i in range(1, len(ids) - 1):
            for ar, is_ban in signmap.get(ids[i], []):
                if ar in (2, 3):
                    fwd = (ar == 2) == (code2_forward_on_right == (side == "R"))
                    ks = [i] if fwd else [i - 1]
                else:                                       # no arrow, double arrow: both stretches
                    ks = [i - 1, i]
                for k in ks:
                    (ban if is_ban else other)[k] = True
        return ban, other

    out, flipped, conflicts, n_arrowed = {}, 0, 0, 0
    for (trc, side), v in groups.items():
        L = v.L.iloc[0]; ts = [0.0] + list(v.t) + [L]; ids = [None] + list(v.POTEAU_ID_POT) + [None]
        # the arrow coding found on the whole City (street_space.py); the other one for this face if it leaves
        # fewer stretches claimed both by an all-time prohibition and by another parking rule
        b1, o1 = claims(ids, side, True); b2, o2 = claims(ids, side, False)
        c1, c2 = int((b1 & o1).sum()), int((b2 & o2).sum())
        has_arrow = any(ar in (2, 3) for i in ids[1:-1] for ar, _ in signmap.get(i, []))
        n_arrowed += has_arrow
        if c2 < c1:
            ban, other = b2, o2; flipped += 1
        else:
            ban, other = b1, o1
        conflicts += int((ban & other).sum())
        w = np.where(ban & other, 0.5, np.where(ban, 1.0, 0.0))
        tot = 0.0
        for k in range(len(w)):
            if w[k]:
                lo, hi = max(ts[k], END), min(ts[k + 1], L - END)
                tot += w[k] * max(0.0, hi - lo)
        out[(trc, side)] = tot
    print(f"block faces with poles: {len(groups)}; with arrowed signs: {n_arrowed}; read with the other arrow coding: {flipped}; "
          f"stretches still claimed both ways (counted for half): {conflicts}")
    ban_len = out

    rows = []
    mid = g.geometry.interpolate(0.5, normalized=True)
    a = g.geometry.interpolate(g.L / 2 - 1); b = g.geometry.interpolate(g.L / 2 + 1)
    ux = (b.x - a.x) / 2; uy = (b.y - a.y) / 2
    for side, sgn, odd in (("L", 1, None), ("R", -1, None)):
        f = g[["ID_TRC", "NOM_VOIE", "TYP_VOIE", "SENS_CIR", "L"]].copy()
        f["side"] = side
        f["pt"] = [Point(m.x - sgn * SIDE_OFFSET * y_, m.y + sgn * SIDE_OFFSET * x_) for m, x_, y_ in zip(mid, ux, uy)]
        f["geometry"] = g.geometry.values
        rows.append(f)
    faces = pd.concat(rows, ignore_index=True)
    faces["net_m"] = (faces.L - 2 * END).clip(lower=0)
    faces["banned_m"] = [min(ban_len.get((t, sd), 0.0), n_) for t, sd, n_ in zip(faces.ID_TRC, faces.side, faces.net_m)]
    faces["legal_m"] = faces.net_m - faces.banned_m
    faces["poles"] = [len(groups[(t, sd)]) if (t, sd) in groups else 0 for t, sd in zip(faces.ID_TRC, faces.side)]
    pts = gpd.GeoDataFrame(faces[["ID_TRC", "side"]], geometry=list(faces.pt), crs=CRS)
    hit = gpd.sjoin(pts, da, predicate="within", how="left")
    faces["dauid"] = hit.DAUID.values
    faces = faces[faces.dauid.notna()].drop(columns="pt").rename(columns={"L": "length_m", "NOM_VOIE": "street", "TYP_VOIE": "street_type", "SENS_CIR": "direction_code"})
    # compass side of the face (N/S/E/W of the centre line), for reading
    gf = gpd.GeoDataFrame(faces, geometry="geometry", crs=CRS)
    lane = gpd.read_file(LANE).to_crs(CRS).geometry.union_all()
    gf["on_lane"] = (gf.street.str.contains("Terrebonne", case=False, na=False)) & (gf.geometry.interpolate(0.5, normalized=True).distance(lane) < 5)
    cols = ["ID_TRC", "side", "street_type", "street", "dauid", "length_m", "net_m", "banned_m", "legal_m", "poles", "on_lane"]
    gf[cols].round(1).to_csv(TABLES / "block_faces.csv", index=False)
    out = gf[cols + ["geometry"]].round({"length_m": 1, "net_m": 1, "banned_m": 1, "legal_m": 1}).to_crs(4326)
    out.to_file(TABLES / "block_faces.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)
    by = gf.groupby("dauid").agg(block_faces=("ID_TRC", "size"), curb_m=("length_m", "sum"), net_m=("net_m", "sum"),
                                 banned_m=("banned_m", "sum"), legal_m=("legal_m", "sum"), poles=("poles", "sum"))
    by["poles_per_km"] = 1000 * by.poles / by.curb_m
    by.round(1).to_csv(TABLES / "curb_by_da.csv")
    print(f"dissemination areas: {len(da)}; block faces: {len(gf)}; curb {gf.length_m.sum() / 1000:.1f} km; "
          f"net of ends {gf.net_m.sum() / 1000:.1f} km; forbidden at all times {gf.banned_m.sum() / 1000:.1f} km "
          f"({100 * gf.banned_m.sum() / gf.net_m.sum():.1f} %); legal {gf.legal_m.sum() / 1000:.1f} km; poles per km {1000 * gf.poles.sum() / gf.length_m.sum():.1f}")
    t = gf[gf.on_lane]
    # side of Terrebonne: the lane runs south-west to north-east; left of a segment digitised eastward is the north side
    x0 = t.geometry.apply(lambda l: l.coords[0][0]); x1 = t.geometry.apply(lambda l: l.coords[-1][0])
    east = x1 > x0
    t = t.assign(curb_side=np.where((t.side == "L") == east, "N", "S"), x_mid=(x0 + x1) / 2).sort_values(["x_mid", "curb_side"])
    tb = t[["ID_TRC", "curb_side", "dauid", "length_m", "net_m", "banned_m", "legal_m", "poles"]].round(1)
    tb.to_csv(TABLES / "terrebonne_curb_by_block.csv", index=False)
    print("Terrebonne along the lane, by side:")
    print(t.groupby("curb_side")[["length_m", "net_m", "banned_m", "legal_m", "poles"]].sum().round(0).to_string())
    print("OK curb_supply")


if __name__ == "__main__":
    main()
