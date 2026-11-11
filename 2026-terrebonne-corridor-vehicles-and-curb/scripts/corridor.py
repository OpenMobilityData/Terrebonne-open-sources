"""Stage 4: the corridor: modelled automobiles and measured legal curb by dissemination area, the sets of areas
(fronting the lane; within about one block; the rest of the two FSAs), and the check against the cars seen
along rue de Terrebonne on the 2015 LiDAR night.

Sets: « corridor » = the dissemination areas that hold a block face of rue de Terrebonne along the lane (they
reach about one block to each side: Somerled is about 260 m north of the lane, Monkland about 285 m south; the
share of each area within 300 m of the lane is in the table); « rest » = the other areas with a part in H4A or
H4B; « all » = both.

Automobiles are MODELLED below the FSA (demand_model.py); curb is MEASURED from the sign inventory
(curb_supply.py). Places are legal curb divided by 5, 5.5 and 6 m: an upper bound (driveways, hydrants, bus
stops, hourly and permit rules not deducted). Off-street parking is measured only for the buildings addressed
on rue de Terrebonne (1954-55 plans and present-day imagery): it is in no ratio here (see offstreet.py).

Outputs (derived/tables/): da_corridor.csv, da_corridor.geojson, corridor_sets.csv, lidar_check_by_sector.csv,
lidar_check_by_da.csv; derived/numbers.json
Run:  ~/.venvs/omd/bin/python scripts/corridor.py
"""
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from corridor_lib import CACHE, CRS, DA_SHP, FSAS, GARAGES, LANE, ROOT, SAAQ, TABLES, TP, YEAR

sys.path.insert(0, str(GARAGES))
PLACE = (5.0, 5.5, 6.0)
BAND = 300.0
SECTORS = (("residential west", 0, 11), ("institutional", 12, 16), ("residential east", 17, 28))


def main():
    dv = pd.read_csv(TABLES / "da_vehicles.csv", dtype={"dauid": str}).set_index("dauid")
    cb = pd.read_csv(TABLES / "curb_by_da.csv", dtype={"dauid": str}).set_index("dauid")
    z = np.load(CACHE / "da_vehicle_draws.npz", allow_pickle=True)
    pos = {d: i for i, d in enumerate(z["dauid"])}
    da = gpd.read_file(DA_SHP, columns=["DAUID"], where="DAUID LIKE '2466%'").to_crs(CRS)
    da = da[da.DAUID.isin(dv.index)].set_index("DAUID")
    lane = gpd.read_file(LANE).to_crs(CRS).geometry.union_all()
    band = lane.buffer(BAND, cap_style="flat")
    tb = pd.read_csv(TABLES / "terrebonne_curb_by_block.csv", dtype={"dauid": str})
    fronting = set(tb.dauid)
    d = dv.join(cb[["block_faces", "curb_m", "net_m", "banned_m", "legal_m"]])
    d["share_within_300m"] = (da.geometry.intersection(band).area / da.geometry.area).reindex(d.index).round(2)
    d["set"] = np.where(d.index.isin(fronting), "corridor", "rest")
    extra = d[(d.set == "rest") & (d.share_within_300m >= 0.5)]
    print(f"areas fronting the lane: {len(fronting)}; their surface within {BAND:.0f} m of the lane: median {100 * d[d.set == 'corridor'].share_within_300m.median():.0f} %; "
          f"other areas with half their surface or more within {BAND:.0f} m: {len(extra)}")
    d["places_5.5m"] = (d.legal_m / 5.5).round(0)
    d["automobiles_per_place_5.5m"] = (d.automobiles_modelled / d["places_5.5m"]).round(2)
    d["automobiles_per_place_low_90"] = (d.low_90 / d["places_5.5m"]).round(2)
    d["automobiles_per_place_high_90"] = (d.high_90 / d["places_5.5m"]).round(2)
    tf = tb.groupby("dauid").agg(terrebonne_frontage_m=("length_m", "sum"), terrebonne_legal_m=("legal_m", "sum"))
    d = d.join(tf)
    # a readable name for each corridor area: side of Terrebonne and the cross streets its frontage runs between
    names = pd.read_csv(GARAGES / "on_street_cars_by_block.csv").block_name.str.replace("–", "|").str.split("|")
    seg0 = tb.assign(block=np.repeat(np.arange(len(tb) // 2), 2))
    lab, order = {}, {}
    for (da_id, side), v in seg0.groupby(["dauid", "curb_side"]):
        a0 = names[v.block.min()][0] or "west end"; b0 = names[v.block.max()][1]
        lab.setdefault(da_id, []).append(f"{side}: {a0} – {b0}"); order[da_id] = min(order.get(da_id, 99), v.block.min())
    d["frontage"] = pd.Series({k: "; ".join(v) for k, v in lab.items()})
    d["west_to_east"] = pd.Series(order)
    d.to_csv(TABLES / "da_corridor.csv")
    g = gpd.GeoDataFrame(d.reset_index(), geometry=da.geometry.reindex(d.index).values, crs=CRS).to_crs(4326)
    g.to_file(TABLES / "da_corridor.geojson", driver="GeoJSON", COORDINATE_PRECISION=6)

    def total(ids, key="draws"):
        a = z[key][[pos[i] for i in ids]].sum(axis=0)
        return np.quantile(a, [0.05, 0.95])

    rows = []
    sets = {"corridor": d.index[d.set == "corridor"], "rest": d.index[d.set == "rest"], "all": d.index}
    for name, ids in sets.items():
        s = d.loc[ids]; lo, hi = total(ids); lo2, hi2 = total(ids, "draws_wide")
        r = {"set": name, "dissemination_areas": len(ids), "households": int(s.households.sum()),
             "automobiles_modelled": int(s.automobiles_modelled.sum()), "low_90": int(lo), "high_90": int(hi), "low_90_wide": int(lo2), "high_90_wide": int(hi2),
             "per_household": s.automobiles_modelled.sum() / s.households.sum(), "per_household_low_90": lo / s.households.sum(), "per_household_high_90": hi / s.households.sum(),
             "alt_3_variables": int(s.alt_3_variables.sum()), "alt_6_variables": int(s.alt_6_variables.sum()),
             "curb_km": s.curb_m.sum() / 1000, "forbidden_at_all_times_km": s.banned_m.sum() / 1000, "legal_curb_km": s.legal_m.sum() / 1000}
        for L in PLACE:
            r[f"places_{L}m"] = int(s.legal_m.sum() / L)
        r["automobiles_per_place_5.5m"] = s.automobiles_modelled.sum() / (s.legal_m.sum() / 5.5)
        r["automobiles_per_place_low_90"] = lo / (s.legal_m.sum() / 5.5); r["automobiles_per_place_high_90"] = hi / (s.legal_m.sum() / 5.5)
        r["legal_curb_m_per_household"] = s.legal_m.sum() / s.households.sum()
        rows.append(r)
    cs = pd.DataFrame(rows); cs.round(2).to_csv(TABLES / "corridor_sets.csv", index=False)
    pd.set_option("display.width", 250)
    print(cs.round(2).T.to_string())

    # the 2015 LiDAR night: cars at the curbs and on the lots along rue de Terrebonne, against the dwellings
    # addressed on the street (City roll) and the modelled rate of the areas holding them
    import frame
    lc = pd.read_csv(GARAGES / "lidar_cars_by_block.csv"); oc = pd.read_csv(GARAGES / "on_street_cars_by_block.csv")
    roll = gpd.read_file(TP / "montreal-opendata/unites-evaluation-fonciere/terrebonne_bbox_extract.geojson")
    roll = roll[roll.NOM_RUE.str.contains("Terrebonne", case=False, na=False) & (roll.NOMBRE_LOGEMENT.fillna(0) > 0)].copy()
    uv = [frame.to_uv(*frame.to_EN(a, b)) for a, b in zip(roll._lon, roll._lat)]
    roll["u"] = [a for a, _ in uv]; roll["v"] = [b for _, b in uv]
    roll = roll[(roll.u >= -30) & (roll.u <= frame.LENGTH + 30)]       # the selection of the parking note (573 dwellings)
    edges = np.array(frame.CUM)
    roll["block"] = np.clip(np.searchsorted(edges, roll.u.values, side="right") - 1, 0, len(edges) - 2)
    roll["side"] = np.where(roll.v > 0, "N", "S")
    seg = tb.assign(block=np.repeat(np.arange(len(tb) // 2), 2))
    key = seg.set_index(["block", "curb_side"]).dauid
    roll["dauid"] = [key.get((b, s)) for b, s in zip(roll.block, roll.side)]
    cars = []
    for b in lc.block:
        for s in ("N", "S"):
            cars.append({"block": b, "side": s, "dauid": key.get((b, s)), "curb_cars": int(oc.loc[oc.block == b, f"lidar_by_eye_{s}"].iloc[0]),
                         "lot_cars": int(lc.loc[lc.block == b, f"lot_{s}"].iloc[0])})
    cars = pd.DataFrame(cars)
    cars["dwellings"] = [roll[(roll.block == b) & (roll.side == s)].NOMBRE_LOGEMENT.sum() for b, s in zip(cars.block, cars.side)]
    rate = d.per_household
    cars["modelled"] = cars.dwellings * cars.dauid.map(rate)
    srows = []
    for name, a, b in SECTORS + (("whole lane", 0, 28),):
        x = cars[cars.block.between(a, b)]
        srows.append({"sector": name, "blocks": b - a + 1, "dwellings_addressed_on_terrebonne": int(x.dwellings.sum()),
                      "cars_at_curbs_2015_night": int(x.curb_cars.sum()), "cars_on_lots_2015_night": int(x.lot_cars.sum()),
                      "cars_seen_per_dwelling": (x.curb_cars.sum() + x.lot_cars.sum()) / x.dwellings.sum(),
                      "modelled_automobiles_per_household": x.modelled.sum() / x.dwellings.sum(),
                      "modelled_automobiles_for_those_dwellings": x.modelled.sum()})
    ls = pd.DataFrame(srows); ls.round(2).to_csv(TABLES / "lidar_check_by_sector.csv", index=False)
    print(ls.round(2).to_string(index=False))
    byda = cars.groupby("dauid").agg(dwellings=("dwellings", "sum"), curb_cars=("curb_cars", "sum"), lot_cars=("lot_cars", "sum"), modelled=("modelled", "sum"))
    byda["cars_seen"] = byda.curb_cars + byda.lot_cars
    byda["modelled_per_household"] = byda.index.map(rate)
    byda["cars_seen_per_dwelling"] = byda.cars_seen / byda.dwellings.where(byda.dwellings > 0)
    byda.round(2).to_csv(TABLES / "lidar_check_by_da.csv")
    ok = byda[byda.dwellings >= 10]
    rho, p = spearmanr(ok.modelled, ok.cars_seen)
    rho2, p2 = spearmanr(ok.modelled_per_household, ok.cars_seen_per_dwelling)
    print(f"areas with 10 dwellings or more on Terrebonne: {len(ok)}; rank correlation, modelled automobiles of those dwellings against cars seen: {rho:.2f} (p = {p:.3f}); "
          f"per dwelling: {rho2:.2f} (p = {p2:.3f})")

    fs = pd.read_csv(SAAQ / "derived/tables/fsa_vehicles_census.csv")
    fs = fs[(fs.year == YEAR) & fs.fsa.isin(FSAS)].set_index("fsa")
    spec = pd.read_csv(TABLES / "model_specifications.csv").set_index("specification")
    dsum = pd.read_csv(TABLES / "downscaling_summary.csv")
    kk = pd.read_csv(TABLES / "fsa_scale_factors.csv").set_index("fsa")
    hc = pd.read_csv(TABLES / "fsa_households_check.csv").set_index("fsa")
    t = tb.groupby("curb_side")[["length_m", "net_m", "banned_m", "legal_m"]].sum()
    N = {"generated": datetime.now(ZoneInfo("America/Toronto")).strftime("%Y-%m-%d %H:%M"), "year": YEAR,
         "fsa": {i: {"automobiles_inferred": int(fs.automobiles_light_trucks_inferred[i]), "households": int(fs.households[i]),
                     "per_household": round(float(fs.au_per_household[i]), 2), "scale_factor": round(float(kk.scale_factor[i]), 3),
                     "households_from_da_pct": float(hc.households_pct_difference[i])} for i in FSAS},
         "sets": {r["set"]: {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k != "set"} for r in rows},
         "corridor_share_within_300m_median": float(d[d.set == "corridor"].share_within_300m.median()),
         "da": {"n": len(d), "per_household_p10": float(d.per_household.quantile(0.1)), "per_household_median": float(d.per_household.median()),
                "per_household_p90": float(d.per_household.quantile(0.9)), "per_household_min": float(d.per_household.min()), "per_household_max": float(d.per_household.max()),
                "half_width_90_median_pct": float(100 * ((d.high_90 - d.low_90) / 2 / d.automobiles_modelled).median()),
                "half_width_90_wide_median_pct": float(100 * ((d.high_90_wide - d.low_90_wide) / 2 / d.automobiles_modelled).median()),
                "per_place_p10": float(d["automobiles_per_place_5.5m"].quantile(0.1)), "per_place_median": float(d["automobiles_per_place_5.5m"].median()),
                "per_place_p90": float(d["automobiles_per_place_5.5m"].quantile(0.9))},
         "model": {"fsas": 114, "chosen": spec.index[spec.chosen][0], "lofo": spec.round(1).reset_index().to_dict("records"),
                   "downscaling": dsum.round(1).to_dict("records")},
         "terrebonne_curb": {s: {k: round(float(v)) for k, v in t.loc[s].items()} for s in t.index},
         "terrebonne_legal_m": round(float(t.legal_m.sum())), "terrebonne_places_5.5m": round(float(t.legal_m.sum() / 5.5)),
         "lidar": {"sectors": ls.round(2).to_dict("records"), "areas": int(len(ok)), "dwellings": int(cars.dwellings.sum()), "rho_count": round(float(rho), 2), "p_count": round(float(p), 3),
                   "rho_rate": round(float(rho2), 2), "p_rate": round(float(p2), 3)}}
    json.dump(N, open(ROOT / "derived/numbers.json", "w"), indent=1, ensure_ascii=False)
    print("OK corridor")


if __name__ == "__main__":
    main()
