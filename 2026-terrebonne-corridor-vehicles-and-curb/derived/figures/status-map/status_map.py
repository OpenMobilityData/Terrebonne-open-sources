"""The status colours of the corridor charts on a map (owner's request, Nov 12, 2026): each dissemination area fronting
the lane coloured by its MODELLED automobiles as a percentage of its places, green under 80 %, yellow 80 to 100 %, red
over 100 % (the thresholds and colours of fig_lib.status_column, so the map and the charts agree area by area).
A: places = legal curb at 5.5 m + the private places of the area's small buildings (calibrated estimate; the
   off-street-corridor chart). B: places = legal curb alone, the limiting case in which every registered automobile
   is kept on the street (the curb-and-automobiles chart). A percentage compares registered vehicles with capacity;
   it is not a measure of how full the street is.
Run:  ~/.venvs/omd/bin/python derived/figures/status-map/status_map.py"""
import json
import sys
from pathlib import Path

import geopandas as gpd
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Rectangle
from shapely.affinity import rotate
from shapely.ops import linemerge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import CRS, LANE, ROOT, TABLES  # noqa: E402

T = {"en": dict(
        title="Modelled automobiles as a share of places, area by area: the status colours of the corridor charts on a map",
        sub="Each area fronting the lane: automobiles registered to its households (MODELLED from the SAAQ file of 2024) as a percentage of its places (MEASURED).\n"
            "A: places at the curb and private places of small buildings. B: places at the curb alone, the case in which every registered automobile is kept on the street.",
        a="A. Curb and private places", b="B. Curb alone (every automobile kept on the street)", lane="the lane (rue de Terrebonne)",
        hatch="A, hatched: most households in buildings of six dwellings or more, whose garages are not counted ({n} areas)",
        low="under 80 %", mid="80 to 100 %", high="over 100 %",
        tot="Corridor: {a} modelled automobiles; {c} curb places at 5.5 m; {p} private places. A: {ra} %; B: {rb} %.",
        note="A share compares registered vehicles with capacity; it is not a measure of how full the street is (no occupancy has been counted since the lane was built). Curb: legal curb by block face,\n"
             "an upper bound (driveways, hydrants, bus stops, hourly and permit rules not deducted). Private places: cars that can leave without another being moved, small buildings only; garage\n"
             "interiors and the {g} larger buildings' garages not counted. Automobiles: the central estimate; each area's 90 % interval is in the corridor-parking-map table."),
     "fr": dict(
        title="Automobiles modélisées en part des places, aire par aire : les couleurs d’état des graphiques du corridor sur une carte",
        sub="Chaque aire riveraine de la piste : automobiles immatriculées à ses ménages (MODÉLISÉES d’après le fichier SAAQ de 2024) en pourcentage de ses places (MESURÉES).\n"
            "A : places en bordure et places privées des petits immeubles. B : places en bordure seulement, le cas où chaque automobile immatriculée est gardée dans la rue.",
        a="A. Bordure et places privées", b="B. Bordure seulement (chaque automobile gardée dans la rue)", lane="la piste (rue de Terrebonne)",
        hatch="A, hachuré : la plupart des ménages dans des immeubles de six logements ou plus, dont les garages ne sont pas comptés ({n} aires)",
        low="moins de 80 %", mid="80 à 100 %", high="plus de 100 %",
        tot="Corridor : {a} automobiles modélisées ; {c} places en bordure à 5,5 m ; {p} places privées. A : {ra} % ; B : {rb} %.",
        note="Une part compare des véhicules immatriculés à une capacité ; elle ne mesure pas le taux d’occupation de la rue (aucun relevé d’occupation depuis la construction de la piste). Bordure :\n"
             "bordure légale par côté d’îlot, borne supérieure (entrées, bornes d’incendie, arrêts d’autobus, règles horaires et vignettes non déduits). Places privées : voitures qui peuvent partir sans en\n"
             "déplacer une autre, petits immeubles seulement ; intérieurs de garage et garages des {g} grands immeubles non comptés. Automobiles : estimation centrale ; l’intervalle à 90 % de chaque aire\n"
             "figure au tableau de la carte corridor-parking-map."),
     }


def state(r):
    return (F.GOOD, "#ffffff") if r < 0.8 else (F.WARNING, "#0b0b0b") if r <= 1.0 else (F.CRITICAL, "#ffffff")


def pct(r, lang):
    close = abs(r - 1) < 0.005 or abs(r - 0.8) < 0.005                 # at a threshold: one decimal, as in the charts
    s = f"{100 * r:.1f} %" if close else f"{100 * r:.0f} %"
    return s if lang == "en" else s.replace(".", ",")


def main():
    g = gpd.read_file(TABLES / "da_corridor.geojson").to_crs(CRS)
    m = pd.read_csv(TABLES / "offstreet_measured_by_da.csv", dtype={"dauid": str})
    m = m.sort_values(["west_to_east", "frontage"]).reset_index(drop=True); m["no"] = np.arange(1, len(m) + 1)
    curb = m.legal_m / 5.5
    m["r_with"] = m.automobiles_modelled / (curb + m.private_independent); m["r_curb"] = m.automobiles_modelled / curb
    m["large_share"] = (m.dwellings_in_large_buildings / m.households).clip(upper=1)          # households in buildings of six dwellings or more (approx.)
    cor = g[g.set == "corridor"][["dauid", "geometry"]].merge(m, on="dauid"); assert len(cor) == 22
    lane = gpd.read_file(LANE).to_crs(CRS)
    U = lane.geometry.union_all(); L = linemerge(U) if U.geom_type == "MultiLineString" else U
    a_, z_ = np.array(L.coords[0]), np.array(L.coords[-1])
    if a_[0] > z_[0]:
        a_, z_ = z_, a_
    ANG = np.degrees(np.arctan2(z_[1] - a_[1], z_[0] - a_[0])); ORG = tuple(((a_ + z_) / 2).tolist())
    cor["geometry"] = cor.geometry.map(lambda x: rotate(x, -ANG, origin=ORG)); lane["geometry"] = lane.geometry.map(lambda x: rotate(x, -ANG, origin=ORG))
    O = json.load(open(ROOT / "derived/offstreet.json"))["corridor"]; N = F.numbers()["sets"]["corridor"]
    ra = N["automobiles_modelled"] / (N["places_5.5m"] + O["private_independent"]); rb = N["automobiles_modelled"] / N["places_5.5m"]
    nx, ny = np.sin(np.radians(ANG)), np.cos(np.radians(ANG))
    for lang, t in T.items():
        fig = plt.figure(figsize=(16, 11.5))
        for k, (col, head, box) in enumerate((("r_with", t["a"], [0.01, 0.53, 0.98, 0.33]), ("r_curb", t["b"], [0.01, 0.17, 0.98, 0.33]))):
            ax = fig.add_axes(box)
            cor.plot(ax=ax, color=[state(r)[0] for r in cor[col]], edgecolor=F.SURFACE, linewidth=1.6)
            lane.plot(ax=ax, color=F.INK, linewidth=0.9, linestyle=(0, (3, 2)))
            if col == "r_with":                                                       # where most private parking is not counted
                cor[cor.large_share > 0.5].plot(ax=ax, facecolor="none", edgecolor=F.SURFACE, hatch="///", linewidth=0)
            for r in cor.itertuples():
                p = r.geometry.representative_point(); fc, ink = state(getattr(r, col))
                ax.text(p.x, p.y, f"{r.no}\n{pct(getattr(r, col), lang)}", fontsize=8.5, ha="center", va="center", color=ink, fontweight="bold", linespacing=1.15, zorder=6,
                        bbox=dict(boxstyle="round,pad=0.25", fc=fc, ec="none"))
            ax.set_axis_off(); ax.set_aspect("equal"); ax.autoscale_view()
            ax.set_title(head, loc="left", fontsize=10.5, color=F.INK, pad=2)
            x0_, x1_ = ax.get_xlim(); y0_, y1_ = ax.get_ylim(); ln = 0.08 * (y1_ - y0_)
            bx, by = x1_ - 0.03 * (x1_ - x0_), y1_ - 0.25 * (y1_ - y0_)
            ax.annotate("", xy=(bx + ln * nx, by + ln * ny), xytext=(bx, by), arrowprops=dict(arrowstyle="-|>,head_width=0.3,head_length=0.6", color=F.INK, lw=1.5))
            ax.text(bx + 1.4 * ln * nx, by + 1.4 * ln * ny, "N", ha="center", va="center", fontsize=10, fontweight="bold", color=F.INK)
        for k, (c, lab) in enumerate(((F.GOOD, t["low"]), (F.WARNING, t["mid"]), (F.CRITICAL, t["high"]))):
            fig.patches.append(Rectangle((0.012 + 0.11 * k, 0.139), 0.012, 0.012, transform=fig.transFigure, fc=c, ec="none"))
            fig.text(0.028 + 0.11 * k, 0.145, lab, fontsize=9, color=F.INK, va="center")
        fig.lines.append(matplotlib.lines.Line2D([0.36, 0.385], [0.145] * 2, transform=fig.transFigure, color=F.INK, lw=1, ls=(0, (3, 2))))
        fig.text(0.39, 0.145, t["lane"], fontsize=9, color=F.INK, va="center")
        fig.patches.append(Rectangle((0.012, 0.117), 0.022, 0.014, transform=fig.transFigure, fc=F.GREY, ec=F.SURFACE, hatch="///", lw=0))
        fig.text(0.038, 0.124, t["hatch"].format(n=int((m.large_share > 0.5).sum())), fontsize=9, color=F.INK, va="center")
        fig.text(0.012, 0.100, t["tot"].format(a=F.num(N["automobiles_modelled"], lang), c=F.num(N["places_5.5m"], lang), p=F.num(O["private_independent"], lang),
                                              ra=F.num(100 * ra, lang), rb=F.num(100 * rb, lang)), fontsize=9, color=F.INK)
        F.finish(fig, HERE, "status_map", lang, t["title"], t["sub"], t["note"].format(g=O["large_buildings"]), top=0.99, bottom=0.01, left=0.0, right=1.0)
    print("states A:", {s: int(sum(state(r)[0] == c for r in m.r_with)) for s, c in (("green", F.GOOD), ("yellow", F.WARNING), ("red", F.CRITICAL))},
          "B:", {s: int(sum(state(r)[0] == c for r in m.r_curb)) for s, c in (("green", F.GOOD), ("yellow", F.WARNING), ("red", F.CRITICAL))})
    print("OK status_map")


if __name__ == "__main__":
    main()
