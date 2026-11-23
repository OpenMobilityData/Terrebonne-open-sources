"""Rue de Terrebonne: the parking places that exist today on its one parking band, net of driveway entrances and fire hydrants
(refinement of November 23, 2026 of the figure « 238 places at 5.5 m », which deducted neither), and the comparison with the
places the borough's 2023 study projected block by block for the design retained.

Inputs, all in derived/tables/:
  terrebonne_legal_stretches_today.csv   where today's signs allow parking on the band: each stretch of legal curb as an interval
                                         along the street (metres from its west end), from curb_stretches.geojson (curb_supply.py);
                                         weight 0.5 = a stretch claimed both by an all-time prohibition and by a parking rule
  terrebonne_offstreet_marks_2023-11-19.csv  the off-street parking spaces seen from the street on a bicycle ride of Sunday,
                                         November 19, 2023, marked by hand at their entrance by the author (side of the street,
                                         metres from the west end; good to a few metres); spaces opening onto a cross street
                                         are not in the table
  terrebonne_hydrant_clearances.csv      3 m on each side of every fire hydrant within 20 m of the centre line, on its side of
                                         the street (Highway Safety Code, art. 386 par. 2; City of Montréal, « Bornes d'incendie »,
                                         CC BY 4.0, file of November 15, 2026, hydrants marked EXISTANT)
  exp_2023_annexe_c_places_by_block.csv  EXP, « Étude de mobilité sur la rue de Terrebonne » (2023), Annexe C: places by tronçon and
                                         side: counted (initial), « mise aux normes », and with scénario 3, the design retained;
                                         unit = the block or blocks of the géobase the row belongs to
  terrebonne_places_today_by_block.csv   the result per block, with the unit of Annexe C each block belongs to

Method: marks on the same side less than GAP m apart are one entrance; an entrance takes ENTRANCE m of curb, centred on its
marks; each legal stretch is cut at every entrance and hydrant clearance on its side, and whole cars of CAR m are counted in each
piece that remains. Former spaces converted to another use are not counted as entrances. There is no bus stop on the street.

The two lengths (one pair, used by every count of places in this folder since November 23, 2026):
  ENTRANCE = 4.0 m: the median length of the 88 curb cuts measured on the street with the City's 2015 airborne LiDAR
             (curb_cuts_lidar.py, derived/curb_cut_test.json; quartiles 2.5 and 6 m for the cuts matched to a lot: the range
             printed; shared driveways measure no wider, so one width for every entrance).
  CAR = 5.37 m: the length at which the method comes within about 1 % of the 2023 study's count on the LIKE-FOR-LIKE block
             faces, those where the street as built and the design retained (scénario 3) place the parking on the same side
             (the count moves in steps: lengths of 5.38 to 5.41 m give half a place under or over). The study's total of
             171 (Tableau 7-1) is not like-for-like with the street as built: 5 of its places are on the block from Girouard to
             Earnscliffe, east of the lane; others are on curb where the street as built has no parking; and the street as built
             has places where scénario 3 has none (the table printed below).
Earlier versions: 238 (legal curb / 5.5 m, signs alone, as first published); in drafts of November 23, 2026 that were not
published, 160 (5.5 m a car, 3.5 m an entrance) and 170.5 (5.25 m, set on the total of 171).

Usage: ~/.venvs/omd/bin/python scripts/terrebonne_places_today.py
       prints the totals and the comparison, checks them against the tables, writes derived/terrebonne_places_today.json
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
T = ROOT / "derived/tables"
CAR, GAP, ENTRANCE, RANGE = 5.37, 3.5, 4.0, (6.0, 2.5)
legal = pd.read_csv(T / "terrebonne_legal_stretches_today.csv")
marks = pd.read_csv(T / "terrebonne_offstreet_marks_2023-11-19.csv")
hyd = pd.read_csv(T / "terrebonne_hydrant_clearances.csv")
exp = pd.read_csv(T / "exp_2023_annexe_c_places_by_block.csv")
ref = pd.read_csv(T / "terrebonne_places_today_by_block.csv")


def entrances(w):
    out = []
    for curb, g in marks[~marks.converted].sort_values("at_m").groupby("curb"):
        s, i = g.at_m.tolist(), 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and s[j + 1] - s[j] < GAP:
                j += 1
            out.append((curb, s[i] - w / 2, s[j] + w / 2)); i = j + 1
    return out + [(r.curb, r.from_m, r.to_m) for r in hyd.itertuples()]


def places(w=ENTRANCE, car=CAR):
    """whole cars per (block, side)"""
    cuts = entrances(w); total = {}
    for r in legal.itertuples():
        pieces = [(r.from_m, r.to_m)]
        for curb, a, b in cuts:
            if curb != r.curb:
                continue
            pieces = [q for x, y in pieces for q in ([(x, y)] if b <= x or a >= y else [(x, a)] * (a > x) + [(b, y)] * (b < y))]
        total[(r.ID_TRC, r.curb)] = total.get((r.ID_TRC, r.curb), 0) + sum(int((y - x) // car) for x, y in pieces) * r.weight
    return total


stated = places(); lo = sum(places(RANGE[0]).values()); hi = sum(places(RANGE[1]).values())
n_ent = len(entrances(ENTRANCE)) - len(hyd)
legal_m = float((legal.to_m - legal.from_m).mul(legal.weight).sum())
print(f"entrances on rue de Terrebonne: {n_ent}; hydrant clearances: {len(hyd)}")
print(f"places today, net of driveway entrances and hydrants: {sum(stated.values()):.1f} at {CAR} m a car and {ENTRANCE} m an entrance ({lo:.1f} to {hi:.1f} for entrances of {RANGE[0]} m to {RANGE[1]} m)")
print(f"by the signs alone: {legal_m:.0f} m of legal curb; {legal_m / CAR:.0f} places by legal curb / {CAR} m; {legal_m / 5.5:.0f} at 5.5 m")
print(f"table terrebonne_places_today_by_block.csv: {ref.places_today.sum():.1f} ({ref.places_today_lo.sum():.1f} to {ref.places_today_hi.sum():.1f})")
assert abs(sum(stated.values()) - ref.places_today.sum()) <= 1.0 and abs(lo - ref.places_today_lo.sum()) <= 1.0 and abs(hi - ref.places_today_hi.sum()) <= 1.0, "the tables and the published figure disagree"

# --- like for like with the 2023 study's scénario 3 (Annexe C), by unit and side
unit = dict(zip(ref.ID_TRC, ref.exp_unit))


def by_unit(tot):
    out = {}
    for (trc, curb), n in tot.items():
        out[(unit[trc], curb)] = out.get((unit[trc], curb), 0) + n
    return out


legal_u = {}
for r in legal.itertuples():
    legal_u[(unit[r.ID_TRC], r.curb)] = legal_u.get((unit[r.ID_TRC], r.curb), 0) + (r.to_m - r.from_m) * r.weight
exp3 = {(u, sd): int(exp[exp.unit == u][f"scenario3_{sd}"].sum()) for u in exp.unit.unique() for sd in "NS"}
ours = by_unit(stated)
rows = [{"unit": u, "side": sd, "legal_m_today": round(legal_u.get((u, sd), 0), 1), "places_today": ours.get((u, sd), 0), "exp_scenario3": exp3[(u, sd)]}
        for u in dict.fromkeys(ref.exp_unit) for sd in "NS"]
cmp_ = pd.DataFrame(rows); cmp_["like_for_like"] = (cmp_.legal_m_today >= CAR) & (cmp_.exp_scenario3 > 0)
L = cmp_[cmp_.like_for_like]; keys = list(zip(L.unit, L.side))
scan = {round(5.30 + 0.01 * i, 2): sum(by_unit(places(car=round(5.30 + 0.01 * i, 2))).get(k, 0) for k in keys) for i in range(16)}
east = int(exp[exp.unit == "east of the lane"][["scenario3_N", "scenario3_S"]].sum().sum())
out = {"car_m": CAR, "entrance_m": ENTRANCE, "entrance_m_range": list(RANGE), "same_entrance_within_m": GAP,
       "places_today": float(sum(stated.values())), "places_today_low": float(lo), "places_today_high": float(hi),
       "entrances": n_ent, "hydrant_clearances": int(len(hyd)), "legal_m": round(legal_m, 1), "places_by_legal_curb": round(legal_m / CAR, 1),
       "like_for_like": {"faces": int(len(L)), "exp": int(L.exp_scenario3.sum()), "this_method": float(L.places_today.sum()),
                         "mean_absolute_difference_per_face": round(float((L.places_today - L.exp_scenario3).abs().mean()), 2),
                         "car_m_scan": scan},
       "exp_scenario3": {"total_table_7_1": 171, "east_of_the_lane": east, "on_the_lane_blocks": 171 - east,
                         "where_no_parking_today": int(cmp_[(cmp_.exp_scenario3 > 0) & ~cmp_.like_for_like].exp_scenario3.sum()),
                         "west_of_coronation": exp3[("west end to Belmore", "S")] + exp3[("Belmore to Coronation", "S")], "cavendish_to_madison_north": exp3[("Cavendish to Madison", "N")]},
       "this_method_where_exp_has_none": float(cmp_[cmp_.exp_scenario3 == 0].places_today.sum()),
       "first_published": {"legal_m": 1306, "places_at_5_5m": 238}}
out["like_for_like"]["difference_pct"] = round(100 * (out["like_for_like"]["this_method"] / out["like_for_like"]["exp"] - 1), 1)
out["like_for_like"]["car_m_nearest"] = [c for c, v in scan.items() if abs(v - out["like_for_like"]["exp"]) == min(abs(x - out["like_for_like"]["exp"]) for x in scan.values())]
assert exp.scenario3_N.sum() + exp.scenario3_S.sum() == 171 and out["exp_scenario3"]["on_the_lane_blocks"] == out["like_for_like"]["exp"] + out["exp_scenario3"]["where_no_parking_today"]
assert abs(out["like_for_like"]["this_method"] - out["like_for_like"]["exp"]) <= 0.015 * out["like_for_like"]["exp"], "the car length is no longer within 1.5 % of the study's count on the like-for-like faces"
ref2 = pd.read_csv(T / "terrebonne_places_today_vs_exp_scenario3.csv")
assert (ref2.places_today.round(1).tolist() == cmp_.places_today.round(1).tolist()) and (ref2.like_for_like.tolist() == cmp_.like_for_like.tolist()), "the comparison table disagrees"
print(cmp_.to_string(index=False))
print({k: v for k, v in out["like_for_like"].items() if k != "car_m_scan"}, out["exp_scenario3"], "ours where the study has none:", out["this_method_where_exp_has_none"])
print("car length scan on the like-for-like faces (study:", out["like_for_like"]["exp"], "):", scan)
json.dump(out, open(ROOT / "derived/terrebonne_places_today.json", "w"), indent=1)
print("OK terrebonne_places_today")
