"""Stage 5: private (off-street) parking: what is measured, and a scenario for the corridor.

MEASURED, for the buildings addressed on rue de Terrebonne only (folder 1954-underwriters-plans-terrebonne-garages):
each building read on the 1954-55 Underwriters' plans (garage as built) and on present-day aerial imagery (driveway
or paved apron). A building with either is counted for ONE off-street place: a floor (a driveway may hold more; a
garage may no longer be used for a car). Buildings not read (no plan sheet; larger apartment buildings) are not in
this part.

SCENARIO, for the corridor's 22 dissemination areas: the share of buildings with a garage or driveway measured on
rue de Terrebonne (with its 95 % interval) is applied to every building of five dwellings or fewer in the City's
assessment roll, one place each; buildings of six dwellings or more are given none, because nothing was measured
for them. The cross streets were not read: this is an assumption, labelled as such wherever it is used.

Outputs: derived/tables/offstreet_terrebonne_by_sector.csv, offstreet_scenario_by_da.csv; derived/offstreet.json
Run:  ~/.venvs/omd/bin/python scripts/offstreet.py   (after corridor.py)
"""
import json
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

from corridor_lib import CACHE, CRS, DA_SHP, GARAGES, ROOT, TABLES

sys.path.insert(0, str(GARAGES))
SECTORS = (("residential west", 0, 11), ("institutional", 12, 16), ("residential east", 17, 28))
SMALL = 5            # dwellings: buildings up to this size take the share measured on Terrebonne
PLACE = 5.5


def main():
    import frame
    d = pd.read_csv(TABLES / "da_corridor.csv", dtype={"dauid": str}).set_index("dauid")
    cor = d[d.set == "corridor"]
    tb = pd.read_csv(TABLES / "terrebonne_curb_by_block.csv", dtype={"dauid": str})
    tb["block"] = np.repeat(np.arange(len(tb) // 2), 2)
    key = tb.set_index(["block", "curb_side"]).dauid

    # 1. measured: the buildings addressed on Terrebonne that were read on the imagery
    b = pd.read_csv(GARAGES / "buildings_geo.csv")
    b = b[(b.addressed_on == "Terrebonne") & b.driveway_today.isin(["yes", "no", "unclear"])].copy()
    b["either"] = (b.garage_1954 == "yes") | (b.driveway_today == "yes")
    edges = np.array(frame.CUM)
    b["blk"] = np.clip(np.searchsorted(edges, b.u_m.values, side="right") - 1, 0, len(edges) - 2)
    b["dauid"] = [key.get((k, s)) for k, s in zip(b.blk, b.side)]
    b["rate"] = b.dauid.map(d.per_household)
    b["modelled"] = b.logements.fillna(0) * b.rate
    lc = pd.read_csv(GARAGES / "lidar_cars_by_block.csv"); oc = pd.read_csv(GARAGES / "on_street_cars_by_block.csv")
    rows = []
    for name, a, z in SECTORS + (("whole lane", 0, 28),):
        x = b[b.blk.between(a, z)]; t = tb[tb.block.between(a, z)]
        l = lc[lc.block.between(a, z)]; o = oc[oc.block.between(a, z)]
        rows.append({"sector": name, "buildings_read": len(x), "with_garage_or_driveway": int(x.either.sum()),
                     "dwellings_in_buildings_read": int(x.logements.fillna(0).sum()),
                     "dwellings_in_buildings_with_garage_or_driveway": int(x[x.either].logements.fillna(0).sum()),
                     "modelled_automobiles_of_those_dwellings": round(x.modelled.sum(), 1),
                     "offstreet_places_floor": int(x.either.sum()),
                     "curb_places_on_terrebonne_today_5.5m": round(t.legal_m.sum() / PLACE),
                     "cars_on_lots_2015_night": int(l.lot_N.sum() + l.lot_S.sum()),
                     "cars_at_curbs_2015_night": int(o.lidar_by_eye_N.sum() + o.lidar_by_eye_S.sum())})
    ts = pd.DataFrame(rows); ts.to_csv(TABLES / "offstreet_terrebonne_by_sector.csv", index=False)
    pd.set_option("display.width", 250); print(ts.T.to_string())
    k, n = int(b.either.sum()), len(b)
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    share = k / n
    print(f"share of buildings read with a garage as built or a driveway today: {k} of {n} = {100 * share:.1f} % ({100 * lo:.1f} to {100 * hi:.1f})")

    # 2. scenario: the corridor's buildings from the assessment roll
    r = gpd.read_parquet(CACHE / "roll_dwelling_points.parquet")
    da = gpd.read_file(DA_SHP, columns=["DAUID"], where="DAUID LIKE '2466%'").to_crs(CRS)
    da = da[da.DAUID.isin(cor.index)]
    j = gpd.sjoin(r, da, predicate="within")
    j["key"] = j.geometry.x.round(0).astype(int).astype(str) + "_" + j.geometry.y.round(0).astype(int).astype(str)   # condominium units of one building share a point
    bl = j.groupby(["DAUID", "key"]).NOMBRE_LOGEMENT.sum().rename("dw").reset_index()
    g = bl.groupby("DAUID")
    s = pd.DataFrame({"buildings": g.size(), "dwellings_roll": g.dw.sum(),
                      "small_buildings": g.apply(lambda x: int((x.dw <= SMALL).sum()), include_groups=False),
                      "dwellings_in_small_buildings": g.apply(lambda x: x[x.dw <= SMALL].dw.sum(), include_groups=False),
                      "large_buildings": g.apply(lambda x: int((x.dw > SMALL).sum()), include_groups=False),
                      "dwellings_in_large_buildings": g.apply(lambda x: x[x.dw > SMALL].dw.sum(), include_groups=False)})
    s.index.name = "dauid"
    s["offstreet_scenario"] = (s.small_buildings * share).round(0)
    s["offstreet_scenario_low"] = (s.small_buildings * lo).round(0); s["offstreet_scenario_high"] = (s.small_buildings * hi).round(0)
    s = s.join(cor[["frontage", "west_to_east", "households", "automobiles_modelled", "low_90", "high_90", "legal_m"]])
    s["curb_places"] = (s.legal_m / PLACE).round(0)
    s["curb_plus_offstreet"] = s.curb_places + s.offstreet_scenario
    s["automobiles_per_place_curb_only"] = (s.automobiles_modelled / s.curb_places).round(2)
    s["automobiles_per_place_with_offstreet"] = (s.automobiles_modelled / s.curb_plus_offstreet).round(2)
    s = s.sort_values(["west_to_east", "frontage"])
    s.to_csv(TABLES / "offstreet_scenario_by_da.csv")
    C = json.load(open(ROOT / "derived/numbers.json"))["sets"]["corridor"]
    tot = {"buildings": int(s.buildings.sum()), "dwellings_roll": int(s.dwellings_roll.sum()), "small_buildings": int(s.small_buildings.sum()),
           "dwellings_in_small_buildings": int(s.dwellings_in_small_buildings.sum()), "large_buildings": int(s.large_buildings.sum()),
           "dwellings_in_large_buildings": int(s.dwellings_in_large_buildings.sum()),
           "offstreet_scenario": int(round(s.small_buildings.sum() * share)), "offstreet_scenario_low": int(round(s.small_buildings.sum() * lo)),
           "offstreet_scenario_high": int(round(s.small_buildings.sum() * hi)), "curb_places": C["places_5.5m"]}
    tot["curb_plus_offstreet"] = tot["curb_places"] + tot["offstreet_scenario"]
    tot["curb_plus_offstreet_low"] = C["places_6.0m"] + tot["offstreet_scenario_low"]; tot["curb_plus_offstreet_high"] = C["places_5.0m"] + tot["offstreet_scenario_high"]
    tot["automobiles_modelled"] = C["automobiles_modelled"]
    tot["per_place_curb_only"] = round(C["automobiles_modelled"] / tot["curb_places"], 2)
    tot["per_place_with_offstreet"] = round(C["automobiles_modelled"] / tot["curb_plus_offstreet"], 2)
    tot["areas_over_curb_only"] = int((s.automobiles_modelled > s.legal_m / PLACE).sum())
    tot["areas_over_with_offstreet"] = int((s.automobiles_modelled > s.legal_m / PLACE + s.small_buildings * share).sum())
    print(json.dumps(tot, indent=1))
    w = ts[ts.sector == "whole lane"].iloc[0]
    json.dump({"measured": {"buildings_read": n, "with_garage_or_driveway": k, "share": round(share, 3), "share_low": round(lo, 3), "share_high": round(hi, 3),
                            "whole_lane": {a: (float(v) if isinstance(v, (float, np.floating)) else int(v)) for a, v in w.items() if a != "sector"}},
               "scenario": tot, "small_building_max_dwellings": SMALL}, open(ROOT / "derived/offstreet.json", "w"), indent=1)
    print("OK offstreet")


if __name__ == "__main__":
    main()
