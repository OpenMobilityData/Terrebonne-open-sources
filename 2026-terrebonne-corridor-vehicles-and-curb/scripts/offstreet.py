"""Stage 5: private (off-street) parking in the corridor: measured, with its error measured too.

1. Rue de Terrebonne (folder 1954-underwriters-plans-terrebonne-garages): the buildings addressed on the street, read
   on October 25, 2026 on the 1954-55 Underwriters' plans (garage as built) and on aerial imagery (driveway or apron);
   one place counted per building with either. Kept as first published; the check below shows that a reading from
   above misses part of the driveways.
2. The corridor's 22 dissemination areas: every lot holding a dwelling (2,358) was read on enlarged aerial crops by
   independent readers under a written protocol (derived/readings/; offstreet_readings_v2.py). The owner then judged,
   from street-level imagery and without seeing any reading, a random sample of 112 lots drawn beforehand
   (derived/readings/owner_check.json). The estimate for the buildings of five dwellings or fewer applies, to the lots
   of each reader answer (yes, unclear, no), the share with car access and the mean number of places the owner found
   for the sampled lots of that answer; intervals by resampling the checked lots (2,000 draws, 90 %).
   Places: « independent » = cars that can stand there and leave without another being moved; « total » = all cars
   the surface holds, one behind another included. Garage interiors are not counted.
   Buildings of six dwellings or more: counted, not given places: in the owner's sample most of those with parking
   have an underground garage whose places cannot be seen.

Outputs: derived/tables/offstreet_terrebonne_by_sector.csv, offstreet_measured_by_da.csv; derived/offstreet.json
Run:  ~/.venvs/omd/bin/python scripts/offstreet.py   (after corridor.py and offstreet_readings_v2.py)
"""
import json
import sys

import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

from corridor_lib import GARAGES, ROOT, TABLES

sys.path.insert(0, str(GARAGES))
SECTORS = (("residential west", 0, 11), ("institutional", 12, 16), ("residential east", 17, 28))
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
    lo_t, hi_t = proportion_confint(k, n, alpha=0.05, method="wilson")
    share = k / n
    print(f"share of buildings read with a garage as built or a driveway today: {k} of {n} = {100 * share:.1f} % ({100 * lo_t:.1f} to {100 * hi_t:.1f})")

    # 2. measured: every lot of the corridor read from above (offstreet_readings_v2.py), calibrated on the owner's check
    m = pd.read_csv(TABLES / "offstreet_readings_v2.csv", dtype={"dauid": str})
    o = pd.read_csv(TABLES / "offstreet_owner_check.csv")
    sm = m[~m.large]; lg = m[m.large]
    chk = o[(~o.large) & o.car_access_owner.isin(["yes", "no"])].copy()
    chk["acc"] = (chk.car_access_owner == "yes").astype(float)
    chk["pi"] = chk.places_independent_owner.fillna(0); chk["pt"] = chk.places_total_owner.fillna(0)
    ANS = ["yes", "unclear", "no"]
    counts = sm.groupby(["dauid", "car_access"]).size().unstack(fill_value=0).reindex(columns=ANS, fill_value=0).reindex(cor.index, fill_value=0)

    def rates(samp):
        g = samp.groupby("car_access")[["acc", "pi", "pt"]].mean(); ov = samp[["acc", "pi", "pt"]].mean()
        return np.array([(g.loc[k] if k in g.index else ov).values for k in ANS])          # 3 reader answers x (access, independent, total)

    R0 = rates(chk); E0 = counts.values @ R0                                               # areas x 3
    rng = np.random.default_rng(20261112)
    EB = np.array([counts.values @ rates(chk.sample(len(chk), replace=True, random_state=int(rng.integers(1e9)))) for _ in range(2000)])   # draws x areas x 3
    q = lambda a, pq: np.quantile(a, pq, axis=0)
    s = pd.DataFrame({"small_buildings": counts.sum(axis=1), "read_yes": counts.yes, "read_unclear": counts.unclear, "read_no": counts.no,
                      "with_access": E0[:, 0].round(0), "private_independent": E0[:, 1].round(0), "private_independent_low": q(EB[:, :, 1], 0.05).round(0),
                      "private_independent_high": q(EB[:, :, 1], 0.95).round(0), "private_total": E0[:, 2].round(0), "private_total_low": q(EB[:, :, 2], 0.05).round(0),
                      "private_total_high": q(EB[:, :, 2], 0.95).round(0)}, index=cor.index)
    s["large_buildings"] = lg.groupby("dauid").size().reindex(cor.index, fill_value=0)
    s["dwellings_in_large_buildings"] = lg.groupby("dauid").dwellings.sum().reindex(cor.index, fill_value=0)
    s = s.join(cor[["frontage", "west_to_east", "households", "automobiles_modelled", "low_90", "high_90", "legal_m"]])
    s["curb_places"] = (s.legal_m / PLACE).round(0)
    s["curb_plus_private_independent"] = (s.legal_m / PLACE + E0[:, 1]).round(0)
    s["automobiles_per_place_curb_only"] = (s.automobiles_modelled / (s.legal_m / PLACE)).round(2)
    s["automobiles_per_place_with_private"] = (s.automobiles_modelled / (s.legal_m / PLACE + E0[:, 1])).round(2)
    s = s.sort_values(["west_to_east", "frontage"])
    s.to_csv(TABLES / "offstreet_measured_by_da.csv")
    C = json.load(open(ROOT / "derived/numbers.json"))["sets"]["corridor"]
    T0 = E0.sum(axis=0); TB = EB.sum(axis=1)
    lo, hi = np.quantile(TB, 0.05, axis=0), np.quantile(TB, 0.95, axis=0)
    ol = o[o.large]
    tot = {"small_buildings": int(len(sm)), "read_yes": int(counts.yes.sum()), "read_unclear": int(counts.unclear.sum()), "read_no": int(counts.no.sum()),
           "with_access": int(round(T0[0])), "with_access_low": int(round(lo[0])), "with_access_high": int(round(hi[0])), "share_with_access": round(float(T0[0] / len(sm)), 3),
           "private_independent": int(round(T0[1])), "private_independent_low": int(round(lo[1])), "private_independent_high": int(round(hi[1])),
           "private_total": int(round(T0[2])), "private_total_low": int(round(lo[2])), "private_total_high": int(round(hi[2])),
           "large_buildings": int(len(lg)), "dwellings_in_large_buildings": int(lg.dwellings.sum()),
           "curb_places": C["places_5.5m"], "automobiles_modelled": C["automobiles_modelled"]}
    tot["curb_plus_private"] = tot["curb_places"] + tot["private_independent"]
    tot["curb_plus_private_low"] = C["places_6.0m"] + tot["private_independent_low"]; tot["curb_plus_private_high"] = C["places_5.0m"] + tot["private_independent_high"]
    tot["per_place_curb_only"] = round(C["automobiles_modelled"] / tot["curb_places"], 2)
    tot["per_place_with_private"] = round(C["automobiles_modelled"] / tot["curb_plus_private"], 2)
    tot["areas_over_curb_only"] = int((s.automobiles_modelled > s.legal_m / PLACE).sum())
    tot["areas_over_with_private"] = int((s.automobiles_modelled > s.curb_plus_private_independent).sum())
    by = chk.groupby("car_access").agg(n=("acc", "size"), yes=("acc", "sum"), pi=("pi", "sum"), pt=("pt", "sum"))
    check = {"small_judged": int(len(chk)), "small_yes": int(chk.acc.sum()), "small_cannot_tell": int(((~o.large) & ~o.car_access_owner.isin(["yes", "no"])).sum()),
             "small_share": round(float(chk.acc.mean()), 3), "independent_per_lot": round(float(chk.pi.mean()), 2), "total_per_lot": round(float(chk.pt.mean()), 2),
             "by_reader_answer": {k: {"lots": int(by.n[k]), "owner_yes": int(by.yes[k]), "independent": int(by.pi[k]), "total": int(by.pt[k])} for k in ANS},
             "large_sampled": int(len(ol)), "large_yes": int((ol.car_access_owner == "yes").sum()), "large_no": int((ol.car_access_owner == "no").sum()),
             "large_cannot_tell": int((~ol.car_access_owner.isin(["yes", "no"])).sum()),
             "large_underground_garage": int(((ol.car_access_owner == "yes") & (ol.kind_owner == "parking lot")).sum())}
    plo, phi = proportion_confint(check["small_yes"], check["small_judged"], alpha=0.05, method="wilson")
    check["small_share_low"], check["small_share_high"] = round(plo, 3), round(phi, 3)
    print(json.dumps({"corridor": tot, "check": check}, indent=1))
    w = ts[ts.sector == "whole lane"].iloc[0]
    json.dump({"measured": {"buildings_read": n, "with_garage_or_driveway": k, "share": round(share, 3), "share_low": round(lo_t, 3), "share_high": round(hi_t, 3),
                            "whole_lane": {a: (float(v) if isinstance(v, (float, np.floating)) else int(v)) for a, v in w.items() if a != "sector"}},
               "corridor": tot, "check": check}, open(ROOT / "derived/offstreet.json", "w"), indent=1)
    print("OK offstreet")


if __name__ == "__main__":
    main()
