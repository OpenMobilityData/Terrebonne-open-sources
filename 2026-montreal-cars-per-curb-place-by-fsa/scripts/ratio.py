"""Stage 2: registered automobiles and light trucks per curb parking place, by FSA, City of Montréal.

Unit: the City part of each forward sortation area (FSA). Automobiles: the SAAQ file of December 31, 2024 released
under the access Act (file 03.06.34729), vehicles whose record gives the municipality of Montréal, by FSA; the type
(automobile or light truck) is INFERRED from make, model and model year (Quebec-vehicle-registrations,
derived/tables/type_by_fsa_municipality.csv). Curb: stage 1, the faces whose side lies in the City. Places: legal
curb at 5.5 m a place (an assumption; 5 and 6 m as bounds).

An FSA is ranked when (a) at least 90 % of its City curb lies in boroughs whose sign inventory is complete (the
remainder then takes the share forbidden at all times measured in the FSA's complete part), (b) its City part holds
at least 1,000 registered automobiles and light trucks, (c) it is not one of the six FSAs whose registered count
exceeds 1.5 times what their census profile predicts (vehicles registered to businesses; corridor analysis), and
(d) no more than 40 % of its curb, net of ends, lies on block faces that carry no sign at all. A face without a sign
counts as legal curb; where such faces are park roads, service roads of autoroutes or industrial boulevards the
places may not exist, and the ratio then depends on that reading (H3C: parc Jean-Drapeau, Cité du Havre; H1J: Anjou's
industrial sector). For every FSA the table also gives the ratio counted on the faces that carry a sign only.

The ratio is the limiting case in which every registered automobile is kept at the curb. It is not a measure of
parking pressure or of how hard parking is: vehicles kept off the street, visitors and vehicles from elsewhere are
not in it, and hourly, permit, street-cleaning and seasonal rules, driveways, hydrants and bus stops are not deducted
from the curb.

Outputs: derived/tables/fsa_ratio.csv, derived/numbers.json
Run:  ~/.venvs/omd/bin/python scripts/ratio.py
"""
import json

import numpy as np
import pandas as pd

from ratio_lib import FLEET, LANE_FSAS, MAX_UNSIGNED, MIN_AUTOS, MIN_COMPLETE, MONTREAL, PLACE_BOUNDS, PLACE_M, ROOT, TABLES, VEHICLES, YEAR

RANKED = "ranked"
INCOMPLETE = "not ranked: sign inventory incomplete"
SMALL = f"not ranked: fewer than {MIN_AUTOS:,} automobiles registered in the City part"
FLEETS = "not ranked: vehicles registered to businesses"
UNSIGNED = f"not ranked: more than {MAX_UNSIGNED:g} % of the curb on block faces without any sign"


def main():
    v = pd.read_csv(VEHICLES, dtype={"muni_code": str})
    v = v[(v.year == YEAR) & (v.vtype == "AU") & v.fsa.str.match(r"^H\d[A-Z]$", na=False)]
    au = pd.DataFrame({"automobiles_city": v[v.muni_code == MONTREAL].groupby("fsa").n.sum(), "automobiles_all_municipalities": v.groupby("fsa").n.sum()})
    c = pd.read_csv(TABLES / "curb_by_fsa.csv", index_col=0)
    d = c.join(au, how="outer")
    d["automobiles_city"] = d.automobiles_city.fillna(0.0); d["city_curb_m"] = d.city_curb_m.fillna(0.0)
    no_curb = d[(d.city_curb_m == 0) & (d.automobiles_city > 0)]
    d = d[d.city_curb_m > 0].copy()
    ok = d.share_city_curb_complete >= MIN_COMPLETE
    free = 1 - d.complete_banned_m / d.complete_net_m                       # share of the curb net of ends that is legal, complete part
    d["legal_curb_m"] = np.where(ok, d.complete_legal_m + d.incomplete_net_m * free, np.nan)
    d["legal_curb_m_signed_faces_only"] = np.where(ok, d.complete_legal_m_signed_faces_only * (1 + d.incomplete_net_m / d.complete_net_m), np.nan)
    d["places"] = d.legal_curb_m / PLACE_M
    d["automobiles_per_place"] = d.automobiles_city / d.places
    for L in PLACE_BOUNDS:
        d[f"automobiles_per_place_at_{L:g}_m"] = d.automobiles_city / (d.legal_curb_m / L)
    d["automobiles_per_place_signed_faces_only"] = d.automobiles_city / (d.legal_curb_m_signed_faces_only / PLACE_M)
    d["automobiles_per_100_m_legal_curb"] = 100 * d.automobiles_city / d.legal_curb_m
    d["status"] = np.select([~ok, d.automobiles_city < MIN_AUTOS, d.index.isin(FLEET), d.pct_net_on_faces_without_sign_complete > MAX_UNSIGNED],
                            [INCOMPLETE, SMALL, FLEETS, UNSIGNED], RANKED)
    d["automobiles_per_100_places"] = (100 * d.automobiles_per_place).round()
    d["pct_automobiles_registered_in_city"] = 100 * d.automobiles_city / d.automobiles_all_municipalities
    r = d.status == RANKED
    d.loc[r, "rank"] = d.loc[r, "automobiles_per_place"].rank(ascending=False, method="first")
    d.loc[r, "rank_signed_faces_only"] = d.loc[r, "automobiles_per_place_signed_faces_only"].rank(ascending=False, method="first")
    d["main_borough"] = d.boroughs.str.split(";").str[0].str.replace(r" \d+ %$", "", regex=True)
    cols = ["status", "rank", "automobiles_city", "legal_curb_m", "places", "automobiles_per_place", "automobiles_per_100_places"] + [f"automobiles_per_place_at_{L:g}_m" for L in PLACE_BOUNDS] + [
        "automobiles_per_100_m_legal_curb", "automobiles_per_place_signed_faces_only", "rank_signed_faces_only", "city_curb_m", "share_city_curb_complete",
        "share_curb_in_city", "pct_automobiles_registered_in_city", "automobiles_all_municipalities", "pct_banned_of_net_complete",
        "pct_net_on_faces_without_sign_complete", "poles_per_km_complete", "main_borough", "boroughs", "other_municipalities"]
    out = d[cols].sort_values(["rank", "status"], na_position="last")
    out.index.name = "fsa"
    out.round({"automobiles_city": 0, "legal_curb_m": 0, "places": 0, "automobiles_per_place": 3, "automobiles_per_place_at_5_m": 3, "automobiles_per_place_at_6_m": 3,
               "automobiles_per_100_m_legal_curb": 2, "automobiles_per_place_signed_faces_only": 3, "city_curb_m": 0, "pct_automobiles_registered_in_city": 1,
               "automobiles_all_municipalities": 0}).to_csv(TABLES / "fsa_ratio.csv")

    k = d[r]
    tot_au = v[v.muni_code == MONTREAL].n.sum()
    N = {"year": YEAR, "place_m": PLACE_M, "fsas_with_city_curb": int(len(d)), "ranked": int(r.sum()),
         "status_counts": d.status.value_counts().to_dict(),
         "fsas_by_status": {s: sorted(d.index[d.status == s]) for s in (INCOMPLETE, SMALL, FLEETS, UNSIGNED)},
         "automobiles_city_h_fsas": round(tot_au), "automobiles_ranked": round(k.automobiles_city.sum()),
         "pct_automobiles_ranked": round(100 * k.automobiles_city.sum() / tot_au, 1),
         "automobiles_in_fsas_without_city_curb": round(no_curb.automobiles_city.sum()),
         "legal_curb_km_ranked": round(k.legal_curb_m.sum() / 1000, 1), "places_ranked": round(k.places.sum()),
         "ratio_all_ranked": round(k.automobiles_city.sum() / k.places.sum(), 3),
         "ratio_median": round(k.automobiles_per_place.median(), 3), "ratio_min": round(k.automobiles_per_place.min(), 3), "ratio_max": round(k.automobiles_per_place.max(), 3),
         "fsa_min": k.automobiles_per_place.idxmin(), "fsa_max": k.automobiles_per_place.idxmax(),
         "ranked_at_100_or_more_per_100_places": int((k.automobiles_per_100_places >= 100).sum()),
         "ranked_on_signed_faces_only_median": round(k.automobiles_per_place_signed_faces_only.median(), 3),
         "rank_correlation_with_signed_faces_only": round(k.automobiles_per_place.corr(k.automobiles_per_place_signed_faces_only, method="spearman"), 3),
         "lane_fsas": {f: {"rank": int(d.loc[f, "rank"]), "automobiles": round(d.loc[f, "automobiles_city"]), "legal_curb_km": round(d.loc[f, "legal_curb_m"] / 1000, 1),
                           "places": round(d.loc[f, "places"]), "ratio": round(d.loc[f, "automobiles_per_place"], 3), "per_100_places": int(d.loc[f, "automobiles_per_100_places"]),
                           "ratio_at_5_m": round(d.loc[f, "automobiles_per_place_at_5_m"], 3), "ratio_at_6_m": round(d.loc[f, "automobiles_per_place_at_6_m"], 3),
                           "ratio_signed_faces_only": round(d.loc[f, "automobiles_per_place_signed_faces_only"], 3), "rank_signed_faces_only": int(d.loc[f, "rank_signed_faces_only"])}
                       for f in LANE_FSAS}}
    json.dump(N, open(ROOT / "derived/numbers.json", "w"), indent=1, ensure_ascii=False)
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
    print(out[["status", "rank", "automobiles_city", "legal_curb_m", "places", "automobiles_per_place", "automobiles_per_place_signed_faces_only", "rank_signed_faces_only",
               "share_city_curb_complete", "pct_automobiles_registered_in_city", "pct_net_on_faces_without_sign_complete", "main_borough"]].round(2).to_string())
    print(json.dumps({k_: v_ for k_, v_ in N.items() if k_ != "fsas_by_status"}, indent=1, ensure_ascii=False))
    print("OK ratio")


if __name__ == "__main__":
    main()
