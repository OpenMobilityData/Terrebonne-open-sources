#!/usr/bin/env python3
"""Loading nights and the corridor's places: modelled automobiles as a share of places when snow loading bans parking.

What the City publishes (checked November 12, 2026, donnees.montreal.ca):
  * truckloads hauled per snow-removal sector per day (« Contrats et transactions de déneigement », CC BY 4.0;
    daily table Terrebonne-access-requests/2026-300/derived/loading_daily.csv);
  * the sector polygons for every season (« Secteurs de déneigement », CC BY 4.0);
  * the free and paying lots open during loading (« Stationnements gratuits et payants (déneigement) », CC BY 4.0).
  Which street, which side, which night: NOT published. Info-Neige / Planif-Neige is a live API (token required); the
  portal offers no history of it. So the night each block face was under a ban is unknown; it is replaced by assumptions.

Assumptions (owner's choices, November 12, 2026), each stated in the note:
  operation   a run of loading days in a sector (one-day gaps allowed) with at least OP_MIN truckloads (100; 50 and 200
              as sensitivity); smaller runs are spot removals, left out. A full operation reaches every street of the
              sector once: each block face is under a ban for one night per operation.
  q           the share of an area's curb under a ban on each of its loading nights: 25 % (its streets spread over
              four nights, a side at a time), 50 % (one side a night, two nights: the central case), 100 % (both sides the
              same night). With one ban-night per face per operation, an area has 1/q loading nights per operation.
  hours       the ban covers the night, when registered cars are at home (signs give the hours; not read here).
  scales      AREA: cars stay in their own dissemination area. DISTRICT: cars can move anywhere in the district's part of
              the corridor; on each night the share of the corridor's curb under a ban is that night's truckloads in the
              sector over the operation's total (loading assumed to proceed evenly over the sector). q plays no part at
              this scale.
  free lot    the Doug-Harvey arena lot (4985 West Hill, 20 places, 18:00-07:00), on the City's list in 2020-21 to
              2023-24 and not in 2024-25 or 2025-26: added in the winters it was listed, in full to each area within
              LOT_RADIUS m and to its district. No other listed lot lies within 1.5 km of the corridor.
Places: legal curb at 5.5 m (MEASURED, an upper bound) and private places of small buildings (MEASURED with a measured
error); automobiles MODELLED (SAAQ 2024 by FSA, shared among areas). A share of places compares capacity; it is not
occupancy.

Usage: ~/.venvs/omd/bin/python scripts/snow_loading.py
Writes derived/tables/snow_loading_{operations,areas,area_nights,district_nights,districts}.csv and derived/snow_loading.json.
"""
import glob
import json
import sys
import warnings
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

from corridor_lib import CRS, DISTRICTS, REPO, ROOT, TABLES, TP

warnings.filterwarnings("ignore", category=RuntimeWarning)
WINTERS = range(2021, 2026)                      # named by the year of December 1
OP_MIN, OP_SENS = 100, (50, 200)
QS = (0.25, 0.5, 1.0)
PLACE_M = 5.5
LOT_RADIUS = 500
# Passes (owner's decision, Nov 12, 2026): a run of loading days counts as several passes through the sector when it is both
# longer and heavier than the sector's median full operation: passes = max(1, min(nights / median nights, truckloads / median
# truckloads)); each night's share = its share of the run's truckloads x passes (at most 1). Without it, the run of Feb 8 -
# Mar 2, 2025 (22 nights after 34 and 36.8 cm) counted as one pass and its nights were diluted. --passes=one gives the earlier
# rule (one pass per run), kept as a sensitivity in derived/sensitivity/one-pass/. --out=DIR writes the tables and JSON there.
PASSES = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--passes=")), "length-volume")
OUT = next((Path(a.split("=", 1)[1]) for a in sys.argv[1:] if a.startswith("--out=")), None)
LOADING = REPO.parent / "Terrebonne-access-requests" / "2026-300" / "derived" / "loading_daily.csv"
SECTORS = TP / "montreal-opendata" / "secteurs-deneigement"
LOTS = TP / "montreal-opendata" / "stationnements-deneigement"
LOT_FILES = {2021: "stationnements_h_2021_2022", 2022: "stationnements_h_2022_2023", 2023: "stationnements-h-2023-2024",
             2024: "stationnements-h-2024-2025", 2025: "stationnements-h-2025-2026"}


def season(y0):
    return f"{y0}-{y0 + 1}"


def sector_key(name):
    """CDN-301A and CDN-301B (2019-2022 polygons) load under CDN-301 in the transactions."""
    return "CDN-301" if name.startswith("CDN-301") else name


def operations(loads, y0, op_min):
    """Runs of loading days per sector within Dec 1 - Mar 31, one-day gaps allowed; each night's share of its run."""
    idx = pd.date_range(f"{y0}-12-01", f"{y0 + 1}-03-31")
    rows, nights = [], []
    for sec, g in loads[loads.season == season(y0)].groupby("sector"):
        d = g.groupby("day").loads.sum().reindex(idx).fillna(0)
        runs, cur, gap = [], [], 0
        for day, v in d.items():
            if v > 0:
                if cur and gap > 1:
                    runs.append(cur); cur = []
                cur.append((day, v)); gap = 0
            else:
                gap += 1
        if cur:
            runs.append(cur)
        for k, r in enumerate(runs):
            tot = sum(v for _, v in r)
            full = tot >= op_min
            rows.append(dict(season=season(y0), sector=sec, start=r[0][0].date(), end=r[-1][0].date(), loading_days=len(r),
                             truckloads=int(tot), full_operation=full))
            if full:
                nights += [dict(season=season(y0), sector=sec, start=r[0][0].date(), day=day, share_of_operation=v / tot) for day, v in r]
    return pd.DataFrame(rows), pd.DataFrame(nights)


def main():
    global T_OUT, J_OUT
    T_OUT, J_OUT = (OUT, OUT) if OUT else (TABLES, ROOT / "derived")
    T_OUT.mkdir(parents=True, exist_ok=True)
    m = pd.read_csv(TABLES / "offstreet_measured_by_da.csv", dtype={"dauid": str}).sort_values(["west_to_east", "frontage"]).reset_index(drop=True)
    m["no"] = np.arange(1, len(m) + 1)
    m["curb_places"] = m.legal_m / PLACE_M
    g = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS)
    cor = g[g.set == "corridor"][["dauid", "geometry"]].merge(m, on="dauid")
    assert len(cor) == 22
    dist = gpd.read_file(DISTRICTS).to_crs(CRS)[["NOM_DISTRICT", "geometry"]]
    ov = gpd.overlay(cor[["dauid", "geometry"]], dist, how="intersection"); ov["a"] = ov.area
    cor["district"] = cor.dauid.map(ov.sort_values("a", ascending=False).drop_duplicates("dauid").set_index("dauid").NOM_DISTRICT)

    cs = gpd.read_file(TABLES / "curb_stretches.geojson").to_crs(CRS)
    cs = cs[cs.dauid.isin(cor.dauid) & cs.state.isin(["legal", "half"])].reset_index(drop=True)
    cs["length_m"] = np.where(cs.state == "half", 0.5, 1.0) * cs.length_m      # a stretch claimed both ways counts for half (curb_supply.py)
    cs = cs[(cs.length_m > 0) & ~cs.geometry.is_empty].reset_index(drop=True)
    assert abs(cs.length_m.sum() - cor.legal_m.sum()) < 5, (cs.length_m.sum(), cor.legal_m.sum())

    ld = pd.read_csv(LOADING, parse_dates=["day"])
    ld = ld[ld.ArrondissementCode == "CDN"].copy(); ld["sector"] = ld.NomSecteur.map(sector_key)

    # each legal stretch's sector, season by season (largest overlap among the sectors that load that season)
    share = []
    for y0 in WINTERS:
        s = gpd.read_file(SECTORS / f"secteurs_deneigement_saison_{season(y0)}.geojson").to_crs(CRS)
        s = s[s.ArrondissementCode == "CDN"].copy(); s["sector"] = s.NomSecteur.map(sector_key)
        s = s[s.sector.isin(set(ld[ld.season == season(y0)].sector))]
        s = s.dissolve("sector").reset_index(); s["geometry"] = s.buffer(0)
        j = gpd.overlay(cs[["dauid", "length_m", "geometry"]].assign(i=cs.index), s[["sector", "geometry"]], how="intersection", keep_geom_type=True)
        j["ov"] = j.length
        best = j.sort_values("ov").groupby("i").tail(1)
        miss = cs.index.difference(best.i)          # 2021-22: stretches lying only in stale polygons (CDN-72/73, no loads that season)
        if len(miss):
            near = gpd.sjoin_nearest(cs.loc[miss, ["dauid", "length_m", "geometry"]].assign(i=miss), s[["sector", "geometry"]], distance_col="d")
            print(f"{season(y0)}: {len(miss)} stretch(es), {cs.loc[miss].length_m.sum():.0f} m, outside every loading sector: nearest sector", sorted(near.sector.unique()), f"({near.d.max():.0f} m)")
            best = pd.concat([best, near.drop_duplicates("i")[["dauid", "length_m", "i", "sector"]]])
        assert best.i.nunique() == len(cs)
        t = best.groupby(["dauid", "sector"]).length_m.sum().reset_index(); t["season"] = season(y0)
        share.append(t)
    share = pd.concat(share)

    # the free lot, by winter
    lot_by = {}
    for y0, f in LOT_FILES.items():
        lots = gpd.read_file(LOTS / f"{f}.geojson").to_crs(CRS)
        near = lots[lots.distance(cor.geometry.union_all()) < LOT_RADIUS]
        lot_by[y0] = [(r.geometry, int(r.NBR_PLA), r.EMPLACEMENT, r.HEURES) for r in near.itertuples()]
    lot_area = {y0: {r.dauid: sum(n for p, n, *_ in L if r.geometry.distance(p) <= LOT_RADIUS) for r in cor.itertuples()} for y0, L in lot_by.items()}
    lot_district = {y0: {d: sum(n for p, n, *_ in L if dist[dist.NOM_DISTRICT == d].geometry.iloc[0].distance(p) <= LOT_RADIUS) for d in cor.district.unique()} for y0, L in lot_by.items()}

    ops_all, nights_by = [], {}
    for op_min in (OP_MIN,) + OP_SENS:
        o, n = zip(*[operations(ld, y0, op_min) for y0 in WINTERS])
        nights_by[op_min] = pd.concat(n)
        if op_min == OP_MIN:
            ops_all = pd.concat(o)
    full = ops_all[ops_all.full_operation].copy()
    med = full.groupby("sector")[["loading_days", "truckloads"]].median()
    full["passes"] = 1.0
    if PASSES == "length-volume":
        full["passes"] = [max(1.0, min(r.loading_days / med.loc[r.sector, "loading_days"], r.truckloads / med.loc[r.sector, "truckloads"])) for r in full.itertuples()]
        for k, nn in nights_by.items():
            o = pd.concat([operations(ld, y0, k)[0] for y0 in WINTERS]); o = o[o.full_operation]
            o["passes"] = [max(1.0, min(r.loading_days / med.loc[r.sector, "loading_days"], r.truckloads / med.loc[r.sector, "truckloads"])) for r in o.itertuples()]
            nn = nn.merge(o[["season", "sector", "start", "passes"]], on=["season", "sector", "start"], how="left")
            nn["share_of_operation"] = (nn.share_of_operation * nn.passes).clip(upper=1.0)
            nights_by[k] = nn.drop(columns="passes")
        print("passes method:", PASSES, "| median full operation by sector:", med.to_dict("index"))
        print(full[full.passes > 1][["season", "sector", "start", "end", "loading_days", "truckloads", "passes"]].round(2).to_string(index=False))
    ops_all = ops_all.merge(full[["season", "sector", "start", "passes"]], on=["season", "sector", "start"], how="left")
    ops_all.to_csv(T_OUT / "snow_loading_operations.csv", index=False)

    def n_ops(sec, ss):
        return float(full[(full.sector == sec) & (full.season == ss)].passes.sum())

    # ---------------- area scale: each area on its own loading nights
    area_rows, night_rows = [], []
    for r in cor.itertuples():
        for y0 in WINTERS:
            ss = season(y0)
            parts = share[(share.dauid == r.dauid) & (share.season == ss)]
            lot = lot_area[y0][r.dauid]
            for q in QS:
                for p in parts.itertuples():
                    lost = q * p.length_m / PLACE_M
                    avail_with = r.curb_places - lost + r.private_independent + lot
                    avail_curb = r.curb_places - lost + lot
                    k = n_ops(p.sector, ss)
                    rw = r.automobiles_modelled / avail_with
                    rc = r.automobiles_modelled / avail_curb if avail_curb > 0.5 else np.inf
                    # ordinary nights (no ban): an area already over 100 % is flagged, its loading nights are not counted
                    ow = r.automobiles_modelled / (r.curb_places + r.private_independent + lot)
                    oc = r.automobiles_modelled / (r.curb_places + lot)
                    owl, owh = r.low_90 / (r.curb_places + r.private_independent + lot), r.high_90 / (r.curb_places + r.private_independent + lot)
                    night_rows.append(dict(no=r.no, dauid=r.dauid, district=r.district, season=ss, sector=p.sector, q=q,
                                           operations=k, loading_nights=round(k / q), free_lot_places=lot,
                                           share_with_private=rw, share_with_private_low=r.low_90 / avail_with, share_with_private_high=r.high_90 / avail_with,
                                           share_curb_only=rc,
                                           over_100_ordinary_with_private=ow > 1, over_100_ordinary_curb_only=oc > 1,
                                           nights_over_100_with_private=round(k / q) * ((rw > 1) & (ow <= 1)),
                                           nights_over_100_curb_only=round(k / q) * ((rc > 1) & (oc <= 1)),
                                           nights_over_100_with_private_low=round(k / q) * ((r.low_90 / avail_with > 1) & (owl <= 1)),
                                           nights_over_100_with_private_high=round(k / q) * ((r.high_90 / avail_with > 1) & (owh <= 1))))
    an = pd.DataFrame(night_rows)
    an.to_csv(T_OUT / "snow_loading_area_nights.csv", index=False)
    # per area: ordinary share, the share on its loading night (main sector, last winter's sectors), nights over 100 % per winter
    agg = an.groupby(["no", "q"]).agg(nights_with=("nights_over_100_with_private", "sum"), nights_curb=("nights_over_100_curb_only", "sum"),
                                     nights_with_low=("nights_over_100_with_private_low", "sum"), nights_with_high=("nights_over_100_with_private_high", "sum"),
                                     loading_nights=("loading_nights", "sum")).reset_index()
    nw = len(WINTERS)
    rows = []
    for r in cor.sort_values("no").itertuples():
        row = dict(no=r.no, dauid=r.dauid, frontage=r.frontage, district=r.district,
                   sectors_2025_26="; ".join(sorted(share[(share.dauid == r.dauid) & (share.season == season(max(WINTERS)))].sector)),
                   automobiles_modelled=r.automobiles_modelled, low_90=r.low_90, high_90=r.high_90,
                   curb_places=round(r.curb_places), private_places=r.private_independent,
                   large_building_share=min(1.0, r.dwellings_in_large_buildings / r.households),
                   share_ordinary_with_private=r.automobiles_modelled / (r.curb_places + r.private_independent),
                   share_ordinary_curb_only=r.automobiles_modelled / r.curb_places,
                   share_ordinary_with_private_low=r.low_90 / (r.curb_places + r.private_independent),
                   share_ordinary_with_private_high=r.high_90 / (r.curb_places + r.private_independent))
        parts25 = share[(share.dauid == r.dauid) & (share.season == season(max(WINTERS)))]
        for q in QS:
            # the share on the area's loading night: its largest sector part under a ban (2025-26 sectors, no lot)
            lost = q * parts25.length_m.max() / PLACE_M
            avail = r.curb_places - lost + r.private_independent
            row[f"share_q{int(q * 100)}_with_private"] = r.automobiles_modelled / avail
            row[f"share_q{int(q * 100)}_with_private_low"] = r.low_90 / avail
            row[f"share_q{int(q * 100)}_with_private_high"] = r.high_90 / avail
            row[f"share_q{int(q * 100)}_curb_only"] = r.automobiles_modelled / (r.curb_places - lost) if r.curb_places - lost > 0.5 else np.inf
            a = agg[(agg.no == r.no) & (agg.q == q)].iloc[0]
            row[f"nights_per_winter_q{int(q * 100)}_with_private"] = a.nights_with / nw
            row[f"nights_per_winter_q{int(q * 100)}_with_private_low"] = a.nights_with_low / nw
            row[f"nights_per_winter_q{int(q * 100)}_with_private_high"] = a.nights_with_high / nw
            row[f"nights_per_winter_q{int(q * 100)}_curb_only"] = a.nights_curb / nw
            row[f"loading_nights_per_winter_q{int(q * 100)}"] = a.loading_nights / nw
        rows.append(row)
    areas = pd.DataFrame(rows)
    # overflow (owner's question, Nov 12, 2026): on the area's own loading night, the share of its modelled automobiles that do not
    # fit in its places (private places included), and the spare CURB in the areas that touch it that night, after their own
    # residents have used their private places (private places are not available to others). Ordinary nights for comparison.
    for q in QS:
        r = areas[f"share_q{int(q * 100)}_with_private"]
        areas[f"overflow_q{int(q * 100)}_share"] = np.where(r > 1, 1 - 1 / r, 0.0)
        areas[f"overflow_q{int(q * 100)}_automobiles"] = areas.automobiles_modelled * areas[f"overflow_q{int(q * 100)}_share"]
        for b_ in ("low", "high"):
            rb = areas[f"share_q{int(q * 100)}_with_private_{b_}"]
            areas[f"overflow_q{int(q * 100)}_share_{b_}"] = np.where(rb > 1, 1 - 1 / rb, 0.0)
    ro = areas.share_ordinary_with_private
    areas["overflow_ordinary_share"] = np.where(ro > 1, 1 - 1 / ro, 0.0)
    spare = (areas.curb_places - (areas.automobiles_modelled - areas.private_places).clip(lower=0)).clip(lower=0)
    geo = cor.set_index("dauid").geometry
    nb = {d: [e for e in geo.index if e != d and geo[d].buffer(5).intersects(geo[e])] for d in geo.index}
    areas["adjacent_areas"] = [", ".join(str(int(areas.loc[areas.dauid == e, "no"].iloc[0])) for e in nb[d]) for d in areas.dauid]
    areas["adjacent_spare_curb_places"] = [float(spare[areas.dauid.isin(nb[d])].sum()) for d in areas.dauid]
    spare_half = (0.5 * areas.curb_places - (areas.automobiles_modelled - areas.private_places).clip(lower=0)).clip(lower=0)   # neighbours under the same ban that night
    areas["adjacent_spare_curb_places_if_also_loaded"] = [float(spare_half[areas.dauid.isin(nb[d])].sum()) for d in areas.dauid]
    areas.to_csv(T_OUT / "snow_loading_areas.csv", index=False, float_format="%.3f")

    # ---------------- district scale: night by night
    curb_ds = share.merge(cor[["dauid", "district"]], on="dauid").groupby(["season", "district", "sector"]).length_m.sum() / PLACE_M
    dn = []
    for op_min, nights in nights_by.items():
        for y0 in WINTERS:
            ss = season(y0)
            idx = pd.date_range(f"{y0}-12-01", f"{y0 + 1}-03-31")
            nt = nights[nights.season == ss] if len(nights) else nights
            for d, x in cor.groupby("district"):
                autos, curb, priv, lot = x.automobiles_modelled.sum(), x.curb_places.sum(), x.private_independent.sum(), lot_district[y0][d]
                lo, hi = x.low_90.sum(), x.high_90.sum()
                for day in idx:
                    lost = sum(curb_ds.get((ss, d, sec), 0) * v for sec, v in nt[nt.day == day][["sector", "share_of_operation"]].itertuples(index=False))
                    aw, ac = curb - lost + priv + lot, curb - lost + lot
                    dn.append(dict(operation_min_truckloads=op_min, season=ss, district=d, day=day.date(), curb_places_under_ban=lost,
                                   share_of_curb_under_ban=lost / curb, free_lot_places=lot,
                                   share_with_private=autos / aw, share_with_private_low=lo / aw, share_with_private_high=hi / aw,
                                   share_curb_only=autos / ac))
    dn = pd.DataFrame(dn)
    dn[dn.operation_min_truckloads == OP_MIN].drop(columns="operation_min_truckloads").to_csv(T_OUT / "snow_loading_district_nights.csv", index=False, float_format="%.4f")
    ds = dn.groupby(["operation_min_truckloads", "district", "season"]).agg(
        loading_nights=("curb_places_under_ban", lambda v: int((v > 0).sum())),
        max_share_of_curb_under_ban=("share_of_curb_under_ban", "max"),
        share_ordinary_with_private=("share_with_private", "min"), max_share_with_private=("share_with_private", "max"),
        max_share_with_private_high=("share_with_private_high", "max"),
        nights_over_100_with_private=("share_with_private", lambda v: int((v > 1).sum())),
        nights_over_100_with_private_high=("share_with_private_high", lambda v: int((v > 1).sum())),
        share_ordinary_curb_only=("share_curb_only", "min"), max_share_curb_only=("share_curb_only", "max"),
        nights_over_100_curb_only=("share_curb_only", lambda v: int((v > 1).sum()))).reset_index()
    ds.to_csv(T_OUT / "snow_loading_districts.csv", index=False, float_format="%.3f")

    # ---------------- summary
    def by_q(q, col):
        return {"areas_over_100_on_loading_night": int((areas[f"share_q{int(q * 100)}_{col}"] > 1).sum()),
                "of_which_over_100_on_ordinary_nights": int((areas[f"share_ordinary_{col}"] > 1).sum()),
                "areas_pushed_over_100_by_loading": int(((areas[f"share_q{int(q * 100)}_{col}"] > 1) & (areas[f"share_ordinary_{col}"] <= 1)).sum()),
                "mean_nights_per_winter_pushed_over_100_corridor_areas": round(float(areas[f"nights_per_winter_q{int(q * 100)}_{col}"].mean()), 2)}
    D = ds[ds.operation_min_truckloads == OP_MIN]
    out = {"winters": [season(y) for y in WINTERS], "window": "December 1 to March 31", "operation_min_truckloads": OP_MIN,
           "operations_per_winter": {s: {sec: int(n) for sec, n in g.groupby("sector").size().items()} for s, g in full.groupby("season")},
           "spot_runs_left_out": int((~ops_all.full_operation).sum()),
           "overflow_q50": {"areas_with_overflow": int((areas.overflow_q50_share > 0).sum()),
                            "areas_overflow_exceeds_adjacent_spare_curb": [int(n) for n in areas.no[areas.overflow_q50_automobiles > areas.adjacent_spare_curb_places]],
                            "areas_overflow_exceeds_adjacent_spare_curb_if_also_loaded": [int(n) for n in areas.no[areas.overflow_q50_automobiles > areas.adjacent_spare_curb_places_if_also_loaded]]},
           "sector_curb_km_2025_26": {k: round(v / 1000, 2) for k, v in share[share.season == season(max(WINTERS))].groupby("sector").length_m.sum().items()},
           "free_lot": {season(y): [dict(places=n, where=w, hours=h) for _, n, w, h in L] for y, L in lot_by.items()},
           "area_scale": {f"q{int(q * 100)}": {"with_private": by_q(q, "with_private"), "curb_only": by_q(q, "curb_only")} for q in QS},
           "district_scale": {d: {"nights_over_100_with_private": dict(zip(x.season, map(int, x.nights_over_100_with_private))),
                                  "nights_over_100_with_private_high": dict(zip(x.season, map(int, x.nights_over_100_with_private_high))),
                                  "nights_over_100_curb_only": dict(zip(x.season, map(int, x.nights_over_100_curb_only))),
                                  "loading_nights": dict(zip(x.season, map(int, x.loading_nights))),
                                  "max_share_with_private": dict(zip(x.season, map(lambda v: round(float(v), 3), x.max_share_with_private))),
                                  "max_share_curb_only": dict(zip(x.season, map(lambda v: round(float(v), 3), x.max_share_curb_only))),
                                  "max_share_of_curb_under_ban": dict(zip(x.season, map(lambda v: round(float(v), 3), x.max_share_of_curb_under_ban)))}
                              for d, x in D.groupby("district")},
           "district_sensitivity_operation_min": {int(k): {d: {"nights_over_100_curb_only_total": int(x.nights_over_100_curb_only.sum()),
                                                              "nights_over_100_with_private_total": int(x.nights_over_100_with_private.sum()),
                                                              "loading_nights_total": int(x.loading_nights.sum())}
                                                          for d, x in g.groupby("district")} for k, g in ds.groupby("operation_min_truckloads")}}
    out["passes_method"] = PASSES
    out["runs_with_more_than_one_pass"] = [dict(season=r.season, sector=r.sector, start=str(r.start), end=str(r.end), nights=int(r.loading_days), truckloads=int(r.truckloads),
                                                passes=round(float(r.passes), 2)) for r in full[full.passes > 1.0].itertuples() if r.sector in ("CDN-301", "CDN-111", "CDN-112", "CDN-105", "CDN-106")]
    out["median_full_operation"] = {k: v for k, v in med.round(1).to_dict("index").items() if k in ("CDN-301", "CDN-111", "CDN-112")}
    json.dump(out, open(J_OUT / "snow_loading.json", "w"), indent=1, ensure_ascii=False, default=str)
    print(json.dumps(out, indent=1, ensure_ascii=False, default=str)[:4000])
    print(areas[["no", "district", "sectors_2025_26", "share_ordinary_with_private", "share_q50_with_private", "nights_per_winter_q50_with_private", "share_q50_curb_only", "nights_per_winter_q50_curb_only"]].round(2).to_string())
    print("OK snow_loading")


if __name__ == "__main__":
    main()
