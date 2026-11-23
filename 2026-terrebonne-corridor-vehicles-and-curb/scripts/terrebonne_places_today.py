"""Rue de Terrebonne: the parking places that exist today on its one parking band, net of driveway entrances and fire hydrants
(refinement of November 23, 2026 of the figure « 238 places at 5.5 m », which deducted neither).

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
Method: marks on the same side less than GAP m apart are one entrance; an entrance takes W_OWN m of curb (W_SHARED for a parking
lot, a garage or a shared lane), centred on its marks; each legal stretch is cut at every entrance and hydrant clearance on its
side, and whole cars of CAR m are counted in each piece that remains. CAR, W_OWN and W_SHARED are assumptions; the range printed
is for entrances of 5.5 m to 3 m. There is no bus stop on the street. Former spaces converted to another use are not counted
as entrances.

Usage: ~/.venvs/omd/bin/python scripts/terrebonne_places_today.py     (prints the totals; compares them with terrebonne_places_today_by_block.csv)
"""
from pathlib import Path

import pandas as pd

T = Path(__file__).resolve().parent.parent / "derived/tables"
CAR, GAP, W_OWN, W_SHARED = 5.5, 3.5, 3.5, 6.0
legal = pd.read_csv(T / "terrebonne_legal_stretches_today.csv")
marks = pd.read_csv(T / "terrebonne_offstreet_marks_2023-11-19.csv")
hyd = pd.read_csv(T / "terrebonne_hydrant_clearances.csv")


def entrances(w_own, w_shared):
    out = []
    for curb, g in marks[~marks.converted].sort_values("at_m").groupby("curb"):
        s, sh, i = g.at_m.tolist(), g.kind.str.startswith("shared").tolist(), 0
        while i < len(s):
            j = i
            while j + 1 < len(s) and s[j + 1] - s[j] < GAP:
                j += 1
            w = w_shared if any(sh[i:j + 1]) else w_own
            out.append((curb, s[i] - w / 2, s[j] + w / 2)); i = j + 1
    return out + [(r.curb, r.from_m, r.to_m) for r in hyd.itertuples()]


def places(w_own, w_shared, car=CAR):
    cuts = entrances(w_own, w_shared); total = {}
    for r in legal.itertuples():
        pieces = [(r.from_m, r.to_m)]
        for curb, a, b in cuts:
            if curb != r.curb:
                continue
            pieces = [q for x, y in pieces for q in ([(x, y)] if b <= x or a >= y else [(x, a)] * (a > x) + [(b, y)] * (b < y))]
        total[r.ID_TRC] = total.get(r.ID_TRC, 0) + sum(int((y - x) // car) for x, y in pieces) * r.weight
    return total


stated = places(W_OWN, W_SHARED); lo = sum(places(5.5, 7.0).values()); hi = sum(places(3.0, 5.0).values())
n_ent = len(entrances(W_OWN, W_SHARED)) - len(hyd)
print(f"entrances on rue de Terrebonne: {n_ent}; hydrant clearances: {len(hyd)}")
print(f"places today, net of driveway entrances and hydrants: {sum(stated.values()):.1f} at {CAR} m a car and {W_OWN} m an entrance ({lo:.1f} to {hi:.1f} for entrances of 5.5 m to 3 m)")
print(f"by the signs alone: {sum(int((r.to_m - r.from_m) // CAR) * r.weight for r in legal.itertuples()):.1f} whole cars per legal stretch; {(legal.to_m - legal.from_m).mul(legal.weight).sum() / CAR:.0f} by legal curb / {CAR} m")
ref = pd.read_csv(T / "terrebonne_places_today_by_block.csv")
print(f"table terrebonne_places_today_by_block.csv: {ref.places_today.sum():.1f} ({ref.places_today_lo.sum():.1f} to {ref.places_today_hi.sum():.1f})")
assert abs(sum(stated.values()) - ref.places_today.sum()) <= 1.0, "the tables and the published figure disagree"
