"""Stage 1: legal curb by block face over the City of Montréal, summed by forward sortation area (FSA).

The method is the corridor analysis's (../2026-terrebonne-corridor-vehicles-and-curb/scripts/curb_supply.py), applied
to every street of the City's géobase. A block face is one side of one géobase segment, which runs from the centre
of one intersection to the centre of the next. Its legal curb is its length, less 10 m at each end (5 m for the cross
street's half roadway, an assumption, and the 5 m next to an intersection where the Highway Safety Code forbids
stopping, art. 386, par. 4), less the stretches where a sign of the City's inventory forbids stopping or parking at
all times (« \\A EN TOUT TEMPS », « \\P EN TOUT TEMPS »). The stretch a sign governs runs from its pole to the next
pole in the direction of its arrow; a sign without an arrow governs the stretches on both sides of its pole. The
arrow coding is the one found on the whole City in Quebec-vehicle-registrations/scripts/street_space.py, except on a
face where the other coding leaves fewer stretches claimed both by an all-time prohibition and by another parking
rule; a stretch still claimed both ways counts for half. One block face of rue de Terrebonne is read from the street
instead of from the inventory, as in the corridor analysis (OBSERVED below; recorded November 23, 2026). Driveways, hydrants, bus stops, hourly rules, permit zones,
street-cleaning and seasonal rules are not deducted: an upper bound on legal curb. A face with no sign at all counts
as legal over its whole length net of the ends.

Streets counted: the géobase's classes 0 (local streets), 5 (collectors), 6 (secondary arterials) and 7 (main
arterials). Left out: class 1 (certain pedestrian ways), 2 (business places), 3 (quays), 4 (private: the port, park
and railway roads, the Circuit Gilles-Villeneuve), 8 (autoroutes) and 9 (projected streets), as the City's dataset
page defines them, and by street type autoroutes, bridges, tunnels, ramps (« voie ») and back lanes. (The corridor
analysis left out by street type only; its two FSAs hold two such faces, 0.9 km.) Each face carries the borough and the
municipality the géobase gives for its side, and the FSA whose polygon (DMTI Spatial, CanMap Postal Code Suite
v2024.3, under licence, not redistributed) contains the point 12 m to its side of the segment's midpoint.

A borough's sign inventory is taken as complete at 8 poles or more per km of curb. Where it is complete, a face
with no sign is counted as legal curb; the tables give, for each borough and FSA, the share of the curb that lies on
such faces, and the legal curb of the faces that carry at least one sign (a lower reading, used as a sensitivity). The face-by-face file stays
outside the repository (it would reproduce the FSA boundaries); the tables here are sums.

Outputs (derived/tables/): curb_by_borough.csv, curb_by_fsa.csv, curb_by_fsa_borough.csv, check_against_corridor.csv
Run:  ~/.venvs/omd/bin/python scripts/curb_by_fsa.py
"""
import geopandas as gpd
import numpy as np
import pandas as pd
from shapely import line_locate_point
from shapely.geometry import Point

from ratio_lib import CACHE, CORRIDOR, CRS, DENSE, FSA_SHP, GEOBASE, SIGNS, TABLES

OUT = ("autoroute", "pont", "tunnel", "voie", "ruelle")
PUBLIC = (0, 5, 6, 7)   # géobase CLASSE: local streets, collectors, secondary arterials, main arterials
HALF_ROADWAY = 5.0   # m: the part of each segment end that lies in the cross street's own roadway (assumption)
CLEARANCE = 5.0      # m: no stopping within 5 m of an intersection (Highway Safety Code, art. 386, par. 4)
END = HALF_ROADWAY + CLEARANCE
SIDE_OFFSET = 12.0
BANS = ["\\A EN TOUT TEMPS", "\\P EN TOUT TEMPS"]
# As in the corridor analysis (curb_supply.py). Block faces read from the street instead of from the inventory (author's observation on photographs of November 2026,
# recorded November 23, 2026). Keyed by segment and by one pole of the face; the states are those of the face's stretches
# in the order of the segment's own direction (the segment runs westward).
OBSERVED = {
    (1320361, "299368"): ["banned", "legal", "banned"],   # rue de Terrebonne, Mayfair to Mariette, south side: two no-stopping signs near the corners, both
                                                          # entered with the same arrow code, so that either coding forbids the 63 m between them; no other sign
                                                          # on the face. Parking is allowed there: read as on the neighbouring faces, the end signs pointing to
                                                          # the corners, parking between them. (West of Coronation the street is two-way and has no parking, as
                                                          # the inventory says.)
}


def side_of(line, t, L, pts):
    a = gpd.GeoSeries(line, crs=CRS).interpolate(np.clip(t - 1, 0, None)).values
    b = gpd.GeoSeries(line, crs=CRS).interpolate(np.clip(t + 1, None, L)).values
    ax, ay, bx, by = [np.array(v) for v in ([p.x for p in a], [p.y for p in a], [p.x for p in b], [p.y for p in b])]
    cross = (bx - ax) * (np.array([p.y for p in pts]) - ay) - (by - ay) * (np.array([p.x for p in pts]) - ax)
    return np.where(cross > 0, "L", "R")


def main():
    g = gpd.read_file(GEOBASE).to_crs(CRS)
    g = g[~g.TYP_VOIE.isin(OUT)].reset_index(drop=True)
    g["L"] = g.geometry.length
    s = pd.read_csv(SIGNS, dtype=str)
    s = s[(s.DESCRIPTION_REP == "Réel") & s.PAS_SUR_RUE.isna() & (s.DESCRIPTION_CAT == "STATIONNEMENT")]
    s["x"] = s.X.astype(float); s["y"] = s.Y.astype(float)
    s["ban"] = s.DESCRIPTION_RPA.str.strip().isin(BANS)
    poles = s.groupby("POTEAU_ID_POT").agg(x=("x", "first"), y=("y", "first")).reset_index()
    pg = gpd.GeoDataFrame(poles, geometry=gpd.points_from_xy(poles.x, poles.y), crs=CRS)
    j = gpd.sjoin_nearest(pg, g[["ID_TRC", "L", "geometry"]], max_distance=20, distance_col="d").drop_duplicates("POTEAU_ID_POT")
    line = g.geometry.loc[j.index_right].values
    j["t"] = line_locate_point(line, j.geometry.values)
    j["side"] = side_of(line, j.t.values, j.L.values, j.geometry.values)
    pol = j[["POTEAU_ID_POT", "ID_TRC", "L", "t", "side"]]
    sg = s[s.POTEAU_ID_POT.isin(pol.POTEAU_ID_POT)][["POTEAU_ID_POT", "FLECHE_PAN", "ban"]].copy()
    sg["arrow"] = pd.to_numeric(sg.FLECHE_PAN, errors="coerce").fillna(0).astype(int)
    signmap = {k: list(zip(v.arrow, v.ban)) for k, v in sg.groupby("POTEAU_ID_POT")}
    groups = {k: v.sort_values("t") for k, v in pol.groupby(["ID_TRC", "side"])}
    print(f"parking-sign poles: {len(poles)}; placed on a street within 20 m: {len(pol)}; block faces with poles: {len(groups)}", flush=True)

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

    ban_len, flipped, conflicts = {}, 0, 0
    observed = []
    for (trc, side), v in groups.items():
        L = v.L.iloc[0]; ts = [0.0] + list(v.t) + [L]; ids = [None] + list(v.POTEAU_ID_POT) + [None]
        b1, o1 = claims(ids, side, True); b2, o2 = claims(ids, side, False)
        c1, c2 = int((b1 & o1).sum()), int((b2 & o2).sum())
        if c2 < c1:
            ban, other = b2, o2; flipped += 1
        else:
            ban, other = b1, o1
        conflicts += int((ban & other).sum())
        w = np.where(ban & other, 0.5, np.where(ban, 1.0, 0.0))
        obs = [v_ for (t_, p_), v_ in OBSERVED.items() if t_ == trc and p_ in ids]
        if obs:
            assert len(obs[0]) == len(w), f"observed states of {trc}: {len(obs[0])} given, {len(w)} stretches"
            w = np.array([1.0 if x == "banned" else 0.0 for x in obs[0]]); observed.append((trc, side))
        tot = 0.0
        for k in range(len(w)):
            if w[k]:
                lo, hi = max(ts[k], END), min(ts[k + 1], L - END)
                tot += w[k] * max(0.0, hi - lo)
        ban_len[(trc, side)] = tot
    assert len(observed) == len(OBSERVED), f"faces read from the street: {len(observed)} found of {len(OBSERVED)}"
    print(f"block faces read from the street instead of the inventory: {observed}", flush=True)
    print(f"faces read with the other arrow coding: {flipped}; stretches still claimed both ways (counted for half): {conflicts}", flush=True)

    mid = g.geometry.interpolate(0.5, normalized=True)
    a = g.geometry.interpolate((g.L / 2 - 1).clip(lower=0)); b = g.geometry.interpolate((g.L / 2 + 1).clip(upper=g.L))
    ux = (b.x - a.x) / 2; uy = (b.y - a.y) / 2
    rows = []
    for side, sgn, arr, lim in (("L", 1, "ARR_GCH", "LIM_GCH"), ("R", -1, "ARR_DRT", "LIM_DRT")):
        f = g[["ID_TRC", "NOM_VOIE", "TYP_VOIE", "CLASSE", "L"]].copy()
        f["side"] = side; f["borough"] = g[arr]; f["municipality"] = g[lim]
        f["geometry"] = [Point(m.x - sgn * SIDE_OFFSET * y_, m.y + sgn * SIDE_OFFSET * x_) for m, x_, y_ in zip(mid, ux, uy)]
        rows.append(f)
    faces = gpd.GeoDataFrame(pd.concat(rows, ignore_index=True), geometry="geometry", crs=CRS)
    faces["net_m"] = (faces.L - 2 * END).clip(lower=0)
    faces["banned_m"] = [min(ban_len.get((t, sd), 0.0), n_) for t, sd, n_ in zip(faces.ID_TRC, faces.side, faces.net_m)]
    faces["legal_m"] = faces.net_m - faces.banned_m
    faces["poles"] = [len(groups[(t, sd)]) if (t, sd) in groups else 0 for t, sd in zip(faces.ID_TRC, faces.side)]
    faces = faces.rename(columns={"L": "length_m", "NOM_VOIE": "street", "TYP_VOIE": "street_type", "CLASSE": "road_class"})

    fsa = gpd.read_file(FSA_SHP, where="PROV = 'QC'")
    fsa = fsa[fsa.FSA.str.startswith("H")][["FSA", "geometry"]].to_crs(CRS)
    hit = gpd.sjoin(faces[["geometry"]], fsa, predicate="within", how="left")
    hit = hit[~hit.index.duplicated()]
    faces["fsa"] = hit.FSA.reindex(faces.index).values
    miss = faces.fsa.isna()
    if miss.any():                                           # a point just outside every polygon (shore): the nearest FSA within 100 m
        near = gpd.sjoin_nearest(faces.loc[miss, ["geometry"]], fsa, max_distance=100)
        near = near[~near.index.duplicated()]
        faces.loc[near.index, "fsa"] = near.FSA.values
    print(f"block faces: {len(faces)}; FSA from the nearest polygon within 100 m: {int(miss.sum() - faces.fsa.isna().sum())}; without FSA: {int(faces.fsa.isna().sum())} "
          f"({faces[faces.fsa.isna()].length_m.sum() / 1000:.1f} km)", flush=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(faces.drop(columns="geometry")).to_parquet(CACHE / "block_faces_city.parquet")

    # check: the faces of the corridor analysis (H4A, H4B), computed there on a cropped copy of the same files
    c = pd.read_csv(CORRIDOR / "derived/tables/block_faces.csv")
    m = c.merge(faces[["ID_TRC", "side", "net_m", "banned_m", "legal_m", "poles"]], on=["ID_TRC", "side"], how="left", suffixes=("_corridor", "_city"))
    assert m.legal_m_city.notna().all(), "corridor faces missing from the city-wide table"
    chk = pd.DataFrame([{"faces_compared": len(m), "legal_km_corridor": round(m.legal_m_corridor.sum() / 1000, 3), "legal_km_city": round(m.legal_m_city.sum() / 1000, 3),
                         "faces_differing_by_more_than_0.1_m": int(((m.legal_m_corridor - m.legal_m_city).abs() > 0.1).sum()),
                         "largest_difference_m": round((m.legal_m_corridor - m.legal_m_city).abs().max(), 2),
                         "faces_with_a_different_pole_count": int((m.poles_corridor != m.poles_city).sum())}])
    chk.to_csv(TABLES / "check_against_corridor.csv", index=False)
    print("check against the corridor analysis:", chk.iloc[0].to_dict(), flush=True)

    out = faces[~faces.road_class.isin(PUBLIC) & (faces.municipality == "Montréal")]
    print("left out by class, City (km of curb):", (out.groupby("road_class").length_m.sum() / 1000).round(1).to_dict(), flush=True)
    faces = faces[faces.road_class.isin(PUBLIC)].reset_index(drop=True)
    faces["signed"] = faces.poles > 0
    city = faces[faces.municipality == "Montréal"]
    bt = city.groupby("borough").agg(block_faces=("ID_TRC", "size"), curb_km=("length_m", lambda x: x.sum() / 1000), net_km=("net_m", lambda x: x.sum() / 1000),
                                     banned_km=("banned_m", lambda x: x.sum() / 1000), poles=("poles", "sum"))
    bt["poles_per_km"] = bt.poles / bt.curb_km
    bt["inventory"] = np.where(bt.poles_per_km >= DENSE, "complete", "incomplete")
    bt["pct_banned_of_net"] = np.where(bt.inventory == "complete", 100 * bt.banned_km / bt.net_km, np.nan)
    bt["legal_km"] = np.where(bt.inventory == "complete", bt.net_km - bt.banned_km, np.nan)
    loc = city[city.road_class == 0]; art = city[city.road_class != 0]
    bt["pct_net_on_faces_without_sign_local"] = 100 * loc[~loc.signed].groupby("borough").net_m.sum().reindex(bt.index, fill_value=0) / loc.groupby("borough").net_m.sum()
    bt["pct_net_on_faces_without_sign_collectors_arterials"] = 100 * art[~art.signed].groupby("borough").net_m.sum().reindex(bt.index, fill_value=0) / art.groupby("borough").net_m.sum()
    bt.round(2).sort_values("curb_km", ascending=False).to_csv(TABLES / "curb_by_borough.csv")
    print(bt.round(1).sort_values("poles_per_km", ascending=False).to_string(), flush=True)

    faces["part"] = np.where(faces.municipality != "Montréal", "other municipality", "City, " + faces.borough.map(bt.inventory).fillna("incomplete") + " inventory")
    fb = faces[faces.fsa.notna()].assign(place=np.where(faces.loc[faces.fsa.notna(), "municipality"] == "Montréal", faces.loc[faces.fsa.notna(), "borough"],
                                                        faces.loc[faces.fsa.notna(), "municipality"]))
    t = fb.groupby(["fsa", "part", "place"]).agg(block_faces=("ID_TRC", "size"), curb_m=("length_m", "sum"), net_m=("net_m", "sum"), banned_m=("banned_m", "sum"),
                                                  legal_m=("legal_m", "sum"), poles=("poles", "sum")).reset_index()
    t.loc[t.part != "City, complete inventory", ["banned_m", "legal_m"]] = np.nan      # no reading where the inventory is incomplete or absent
    t.round(1).to_csv(TABLES / "curb_by_fsa_borough.csv", index=False)

    comp = fb[fb.part == "City, complete inventory"]; part = fb[fb.part == "City, incomplete inventory"]; oth = fb[fb.part == "other municipality"]
    w = pd.DataFrame(index=sorted(fb.fsa.unique()))
    w["complete_curb_m"] = comp.groupby("fsa").length_m.sum(); w["complete_net_m"] = comp.groupby("fsa").net_m.sum()
    w["complete_banned_m"] = comp.groupby("fsa").banned_m.sum(); w["complete_legal_m"] = comp.groupby("fsa").legal_m.sum()
    w["complete_poles"] = comp.groupby("fsa").poles.sum()
    w["complete_net_m_on_faces_without_sign"] = comp[~comp.signed].groupby("fsa").net_m.sum()
    w["complete_legal_m_signed_faces_only"] = comp[comp.signed].groupby("fsa").legal_m.sum()
    w["incomplete_curb_m"] = part.groupby("fsa").length_m.sum(); w["incomplete_net_m"] = part.groupby("fsa").net_m.sum()
    w["other_municipality_curb_m"] = oth.groupby("fsa").length_m.sum()
    w = w.fillna(0.0)
    w["city_curb_m"] = w.complete_curb_m + w.incomplete_curb_m
    w["share_city_curb_complete"] = (w.complete_curb_m / w.city_curb_m).where(w.city_curb_m > 0)
    w["share_curb_in_city"] = w.city_curb_m / (w.city_curb_m + w.other_municipality_curb_m)
    w["poles_per_km_complete"] = (1000 * w.complete_poles / w.complete_curb_m).where(w.complete_curb_m > 0)
    w["pct_banned_of_net_complete"] = (100 * w.complete_banned_m / w.complete_net_m).where(w.complete_net_m > 0)
    w["pct_net_on_faces_without_sign_complete"] = (100 * w.complete_net_m_on_faces_without_sign / w.complete_net_m).where(w.complete_net_m > 0)
    sh = fb[fb.municipality == "Montréal"].groupby(["fsa", "borough"]).length_m.sum().reset_index()
    sh["s"] = sh.length_m / sh.groupby("fsa").length_m.transform("sum")
    w["boroughs"] = sh[sh.s >= 0.02].sort_values("s", ascending=False).groupby("fsa").apply(
        lambda x: "; ".join(f"{b} {100 * s_:.0f} %" for b, s_ in zip(x.borough, x.s)), include_groups=False)
    om = oth.groupby(["fsa", "municipality"]).length_m.sum().reset_index().sort_values("length_m", ascending=False)
    w["other_municipalities"] = om.groupby("fsa").municipality.apply("; ".join)
    w.index.name = "fsa"
    w.round({c: 1 for c in w.columns if c.endswith("_m")} | {"share_city_curb_complete": 4, "share_curb_in_city": 4, "poles_per_km_complete": 1,
                                                              "pct_banned_of_net_complete": 2, "pct_net_on_faces_without_sign_complete": 1}).to_csv(TABLES / "curb_by_fsa.csv")
    cc = w[w.city_curb_m > 0]
    print(f"FSAs with City curb: {len(cc)}; City curb {cc.city_curb_m.sum() / 1000:.0f} km, of which {cc.complete_curb_m.sum() / 1000:.0f} km in boroughs with a complete inventory; "
          f"legal there {cc.complete_legal_m.sum() / 1000:.0f} km ({100 * cc.complete_banned_m.sum() / cc.complete_net_m.sum():.1f} % of the curb net of ends forbidden at all times)")
    print("OK curb_by_fsa")


if __name__ == "__main__":
    main()
