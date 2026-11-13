"""On an area's own snow-loading night, the share of its registered automobiles that would not fit in its places (owner's
question, Nov 12, 2026: « the percentage of residents who would have to park outside of their DA »). Central case of the note
(section 4.7): half of the area's curb under a ban on its loading night; private places included; automobiles MODELLED (SAAQ
2024 below the FSA), places MEASURED. Nothing about the order of loading is assumed: the figure holds whichever night the
area's streets are cleared. For each area that overflows, the spare curb in the corridor areas that touch it (after their own
residents have used their private places), on an ordinary night and if they are under the same ban that night.
Run:  ~/.venvs/omd/bin/python derived/figures/snow-loading-overflow/snow_loading_overflow.py   (after scripts/snow_loading.py)"""
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from shapely.affinity import rotate
from shapely.ops import linemerge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import CRS, DISTRICTS, LANE, TABLES  # noqa: E402

BINS = [(0.0, 0.0, "#eceee9", F.INK), (0.0, 0.15, "#fde0c5", F.INK), (0.15, 0.30, "#f6a96c", F.INK), (0.30, 0.50, "#e0662e", "#ffffff"), (0.50, 1.0, "#9c3a12", "#ffffff")]
T = {"en": dict(
        title="On a snow-loading night, what share of a zone's residents would have to park their car in another zone?",
        sub="Each zone along the lane on the night its streets are cleared, if half its curb is banned (the note's central case), counting driveways and garages. The share does not depend on\n"
            "the order in which the City clears streets. Most zones fit all their cars; where some do not, the curb in the zones next to them has room for them",
        exc=",\nand also if they are cleared the same night, except next to zone {a}.",
        none="all fit", bins=["up to 15 %", "15 to 30 %", "30 to 50 %", "over 50 %"],
        lab="{p} %\n≈{n} cars", hatch="hatched: mostly large buildings, whose underground garages are not counted (overstated)",
        side="Zones that would not fit all their cars, and the spare curb next door",
        row="zone {no}: {n} cars; spare curb in touching zones {s} ({h} if they are loaded the same night)",
        lane="the lane", dist="Loyola | NDG district line",
        foot="Cars: registered automobiles of the zone's households (SAAQ, Dec. 31, 2024), MODELLED below the postal district; they stand in for overnight demand. Places: legal curb at 5.5 m per car\n"
             "(MEASURED, an upper bound) and driveways and garages of buildings of five dwellings or fewer (MEASURED, calibrated on a street-level check). Which streets are cleared on which night is not\n"
             "published; half the curb a night is an assumption (one side at a time). Capacity, not occupancy. Preliminary results, not peer reviewed. github.com/OpenMobilityData/Terrebonne-open-sources"),
     "fr": dict(
        title="Une nuit de chargement de la neige, quelle part des résidents d’une zone devrait garer sa voiture dans une autre zone ?",
        sub="Chaque zone le long de la piste la nuit où ses rues sont déneigées, si la moitié de sa bordure est interdite (cas central de la note), entrées et garages compris. La part ne dépend pas de\n"
            "l’ordre dans lequel la Ville déneige les rues. La plupart des zones logent toutes leurs voitures ; là où ce n’est pas le cas, la bordure des zones voisines a de la place",
        exc=",\nmême si elles sont déneigées la même nuit, sauf autour de la zone {a}.",
        none="toutes logées", bins=["jusqu’à 15 %", "15 à 30 %", "30 à 50 %", "plus de 50 %"],
        lab="{p} %\n≈{n} voit.", hatch="hachuré : surtout de grands immeubles, dont les garages souterrains ne sont pas comptés (surestimé)",
        side="Zones qui ne logeraient pas toutes leurs voitures, et la bordure libre à côté",
        row="zone {no} : {n} voitures ; bordure libre dans les zones contiguës {s} ({h} si elles sont déneigées la même nuit)",
        lane="la piste", dist="limite des districts Loyola | NDG",
        foot="Voitures : automobiles immatriculées des ménages de la zone (SAAQ, 31 déc. 2024), MODÉLISÉES sous la RTA ; elles tiennent lieu de la demande de nuit. Places : bordure légale à 5,5 m par voiture\n"
             "(MESURÉE, borne supérieure) et entrées et garages des immeubles de cinq logements ou moins (MESURÉS, calés sur une vérification de la rue). Les rues déneigées chaque nuit ne sont pas\n"
             "publiées ; la moitié de la bordure par nuit est une hypothèse (un côté à la fois). Capacité, pas occupation. Résultats préliminaires, non révisés par des pairs. github.com/OpenMobilityData/Terrebonne-open-sources")}


def colour(v):
    if v <= 0:
        return BINS[0][2:]
    for lo, hi, fc, ink in BINS[1:]:
        if lo < v <= hi:
            return fc, ink
    return BINS[-1][2:]


def main():
    a = pd.read_csv(TABLES / "snow_loading_areas.csv", dtype={"dauid": str})
    g = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS); g = g[g.set == "corridor"][["dauid", "geometry"]].merge(a, on="dauid")
    assert len(g) == 22
    lane = gpd.read_file(LANE).to_crs(CRS)
    U = lane.geometry.union_all(); L = linemerge(U) if U.geom_type == "MultiLineString" else U
    a_, z_ = np.array(L.coords[0]), np.array(L.coords[-1])
    if a_[0] > z_[0]:
        a_, z_ = z_, a_
    ANG = np.degrees(np.arctan2(z_[1] - a_[1], z_[0] - a_[0])); ORG = tuple(((a_ + z_) / 2).tolist())
    rot = lambda s: s.map(lambda x: rotate(x, -ANG, origin=ORG))
    dist = gpd.read_file(DISTRICTS).to_crs(CRS)
    loy, ndg = (dist[dist.NOM_DISTRICT == n].geometry.union_all() for n in ("Loyola", "Notre-Dame-de-Grâce"))
    line = gpd.GeoSeries([loy.boundary.intersection(ndg.boundary).intersection(g.geometry.union_all().buffer(30))], crs=CRS)
    g["geometry"] = rot(g.geometry); lane["geometry"] = rot(lane.geometry); line = rot(line)
    over = g[g.overflow_q50_share > 0].sort_values("no")
    for lang, t in T.items():
        fig = plt.figure(figsize=(16, 9))
        ax = fig.add_axes([0.005, 0.355, 0.99, 0.53])
        g.plot(ax=ax, color=[colour(v)[0] for v in g.overflow_q50_share], edgecolor=F.SURFACE, linewidth=1.6)
        g[g.large_building_share > 0.5].plot(ax=ax, facecolor="none", edgecolor=F.SURFACE, hatch="///", linewidth=0)
        lane.plot(ax=ax, color=F.INK, linewidth=1.0, linestyle=(0, (3, 2)))
        line.plot(ax=ax, color=F.INK, linewidth=2.2)
        ytop = g.geometry.bounds.maxy.max()
        for r in g.itertuples():
            p = r.geometry.representative_point(); fc, ink = colour(r.overflow_q50_share)
            if r.overflow_q50_share <= 0:
                ax.text(p.x, p.y, f"{r.no}", ha="center", va="center", fontsize=9, color=F.INK, fontweight="bold", zorder=6)
                continue
            txt = f"{r.no}\n" + t["lab"].format(p=f"{100 * r.overflow_q50_share:.0f}", n=f"{r.overflow_q50_automobiles:.0f}")
            box = dict(boxstyle="round,pad=0.3", fc=fc, ec=F.SURFACE, lw=1.2)
            narrow = (r.geometry.bounds[2] - r.geometry.bounds[0]) < 120
            if narrow:                                           # a thin area: the label above the map, with a pointer
                ax.annotate(txt, xy=(p.x, r.geometry.bounds[3] - 20), xytext=(p.x, ytop + 50), ha="center", va="bottom", fontsize=10, color=ink, fontweight="bold",
                            linespacing=1.1, zorder=7, bbox=box, arrowprops=dict(arrowstyle="-", color=F.INK, lw=1))
            else:
                ax.text(p.x, p.y, txt, ha="center", va="center", fontsize=10, color=ink, fontweight="bold", linespacing=1.1, zorder=6, bbox=box)
        ax.set_axis_off(); ax.set_aspect("equal"); ax.autoscale_view()
        y0_, y1_ = ax.get_ylim(); ax.set_ylim(y0_, max(y1_, ytop + 215))
        # legend
        y0 = 0.30
        items = [(BINS[0][2], t["none"])] + [(b[2], lab) for b, lab in zip(BINS[1:], t["bins"])]
        for k, (fc, lab) in enumerate(items):
            fig.patches.append(Rectangle((0.015 + 0.105 * k, y0), 0.014, 0.022, transform=fig.transFigure, fc=fc, ec="none"))
            fig.text(0.033 + 0.105 * k, y0 + 0.011, lab, fontsize=10.5, va="center", color=F.INK)
        fig.patches.append(Rectangle((0.015, y0 - 0.04), 0.026, 0.022, transform=fig.transFigure, fc=F.GREY, ec=F.SURFACE, hatch="///", lw=0))
        fig.text(0.046, y0 - 0.029, t["hatch"], fontsize=10.5, va="center", color=F.INK)
        fig.text(0.015, y0 - 0.07, f"—— {t['dist']}     - - - {t['lane']}", fontsize=10.5, va="center", color=F.INK)
        # the overflowing areas and the room next to them
        fig.text(0.56, y0 + 0.02, t["side"], fontsize=11.5, fontweight="bold", va="center", color=F.INK)
        for k, r in enumerate(over.itertuples()):
            fig.text(0.56, y0 - 0.012 - 0.026 * k, t["row"].format(no=r.no, n=f"{r.overflow_q50_automobiles:.0f}", s=f"{r.adjacent_spare_curb_places:.0f}",
                                                                   h=f"{r.adjacent_spare_curb_places_if_also_loaded:.0f}"), fontsize=10, va="center", color=F.INK)
        fig.text(0.012, 0.975, t["title"], fontsize=16.5, fontweight="bold", va="top", color=F.INK)
        short = over[over.overflow_q50_automobiles > over.adjacent_spare_curb_places_if_also_loaded].no.tolist()
        fig.text(0.012, 0.925, t["sub"] + (t["exc"].format(a=", ".join(map(str, short))) if short else "."), fontsize=11, color=F.MUTED, va="top", linespacing=1.3)
        fig.text(0.012, 0.012, t["foot"], fontsize=8.3, color=F.MUTED, va="bottom", linespacing=1.35)
        for ext in ("png", "svg"):
            fig.savefig(HERE / f"snow_loading_overflow_{lang}.{ext}", dpi=200)
        plt.close(fig)
    print("OK snow_loading_overflow")


if __name__ == "__main__":
    main()
