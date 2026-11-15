"""Maps: registered automobiles and light trucks per 100 curb parking places, by forward sortation area (FSA), City of
Montréal, 2024 (the City part of each FSA; stage 2, derived/tables/fsa_ratio.csv).

  fsa_ratio_map_{en,fr}         the whole City
  fsa_ratio_map_west_{en,fr}    the same map enlarged on Côte-des-Neiges–Notre-Dame-de-Grâce and its neighbours

One hue, five classes of the value as printed (a whole number, so label and colour agree). FSAs without a ranked
value are drawn on a neutral ground: hatched where the curb data are missing or incomplete (the borough's sign
inventory is incomplete, or more than 40 % of the curb lies on block faces without any sign), dotted where the FSA is
left out for another reason (vehicles registered to businesses; fewer than 1,000 automobiles in the City part). The
electoral districts of Notre-Dame-de-Grâce, Loyola and Snowdon (2025) are outlined. The map is turned 34° clockwise
(the island lies across the page; the arrow gives north).

FSA boundaries: DMTI Spatial, CanMap Postal Code Suite v2024.3 (under licence; drawn here, not redistributed).
Run:  ~/.venvs/omd/bin/python derived/figures/fsa-ratio-map/fsa_ratio_map.py
"""
import sys
import textwrap
from pathlib import Path

import geopandas as gpd
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from shapely import maximum_inscribed_circle
from shapely.affinity import rotate
from shapely.geometry import box as sbox

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from ratio_lib import CRS, DISTRICTS, FSA_SHP, LANE, LANE_FSAS, LIMITS, OUTLINED  # noqa: E402

ANGLE = -34.0                     # degrees; the map is turned 34° clockwise
HATCHED = ("sign inventory incomplete", "block faces without any sign")
T = {"en": dict(
        title="Registered automobiles per 100 street parking places, by postal area (FSA): City of Montréal, 2024",
        sub="Automobiles and light trucks registered in the City part of each FSA (SAAQ, December 31, 2024; type inferred) per 100 places of legal curb, at 5.5 m a place.\n"
            "The limiting case in which every registered automobile is kept on the street: it is not a measure of how full the streets are or of how hard parking is.",
        title_w="Registered automobiles per 100 street parking places, by postal area (FSA): Côte-des-Neiges–Notre-Dame-de-Grâce and its neighbours, 2024",
        legend="Automobiles per 100 places", n="{n} FSAs", n1="1 FSA",
        hatch="Curb data missing or incomplete: the borough’s inventory of parking signs\nis incomplete ({a} FSAs), or over 40 % of the curb carries no sign ({b})",
        dots="Left out of the ranking: vehicles registered to businesses ({a} FSAs),\nor fewer than 1,000 automobiles in the City part ({b})",
        town="Other municipalities (not part of the City)", dist="Electoral districts of Notre-Dame-de-Grâce, Loyola and Snowdon (2025)",
        lane="Bike lane on rue de Terrebonne", km="km", district="{d} district", small="Too small to label:",
        key="H4B: {b} · H4A: {a} · median of the {n} ranked FSAs: {m} · all {n} together: {t}",
        note="Legal curb: each block face of the City’s géobase (local streets, collectors and arterials), less 10 m at each end, less the stretches where a sign forbids stopping or parking at all times; an upper bound\n"
             "(driveways, hydrants, bus stops, hourly, permit, street-cleaning and seasonal rules are not deducted). Vehicles kept off the street, visitors and vehicles from elsewhere are not counted. At 5 m a place\n"
             "every value is 9 % lower, at 6 m 9 % higher; the order of the FSAs does not change. An FSA shared with another municipality is shown for its City part (automobiles whose record gives Montréal).",
        src="Sources: SAAQ, vehicles released under the access Act (file 03.06.34729); City of Montréal, géobase, inventory of parking signs, administrative limits, electoral districts (CC BY 4.0).\n"
            "FSA boundaries: DMTI Spatial, CanMap Postal Code Suite v2024.3. Tables and scripts: OpenMobilityData/Terrebonne-open-sources, 2026-montreal-cars-per-curb-place-by-fsa."),
     "fr": dict(
        title="Automobiles immatriculées pour 100 places de stationnement sur rue, par région postale (RTA) : Ville de Montréal, 2024",
        sub="Automobiles et camions légers immatriculés dans la partie de chaque RTA située dans la Ville (SAAQ, 31 décembre 2024 ; type inféré) pour 100 places de bordure légale, à 5,5 m la place.\n"
            "Le cas limite où chaque automobile immatriculée est gardée dans la rue : ce n’est pas une mesure de l’occupation des rues ni de la difficulté de se stationner.",
        title_w="Automobiles immatriculées pour 100 places de stationnement sur rue, par région postale (RTA) : Côte-des-Neiges–Notre-Dame-de-Grâce et ses voisins, 2024",
        legend="Automobiles pour 100 places", n="{n} RTA", n1="1 RTA",
        hatch="Données de bordure manquantes ou incomplètes : l’inventaire de la signalisation de stationnement\nde l’arrondissement est incomplet ({a} RTA), ou plus de 40 % de la bordure est sans panneau ({b})",
        dots="Hors classement : véhicules immatriculés au nom d’entreprises ({a} RTA),\nou moins de 1 000 automobiles dans la partie située dans la Ville ({b})",
        town="Autres municipalités (hors de la Ville)", dist="Districts électoraux de Notre-Dame-de-Grâce, de Loyola et de Snowdon (2025)",
        lane="Piste cyclable de la rue de Terrebonne", km="km", district="district de {d}", small="Trop petites pour l’étiquette :",
        key="H4B : {b} · H4A : {a} · médiane des {n} RTA classées : {m} · les {n} ensemble : {t}",
        note="Bordure légale : chaque côté d’îlot de la géobase de la Ville (rues locales, collectrices et artères), moins 10 m à chaque extrémité, moins les tronçons où un panneau interdit l’arrêt ou le stationnement en tout temps ;\n"
             "une borne supérieure (entrées charretières, bornes d’incendie, arrêts d’autobus, règles horaires, vignettes, entretien et règles saisonnières non déduits). Les véhicules gardés hors rue, les visiteurs et les véhicules\n"
             "d’ailleurs ne sont pas comptés. À 5 m la place, chaque valeur est 9 % plus basse ; à 6 m, 9 % plus haute ; l’ordre des RTA ne change pas. Une RTA partagée avec une autre municipalité est montrée pour sa partie\n"
             "située dans la Ville (automobiles dont le dossier indique Montréal).",
        src="Sources : SAAQ, véhicules communiqués en vertu de la Loi sur l’accès (dossier 03.06.34729) ; Ville de Montréal, géobase, inventaire de la signalisation de stationnement, limites administratives,\n"
            "districts électoraux (CC BY 4.0). Limites des RTA : DMTI Spatial, CanMap Postal Code Suite v2024.3. Tableaux et scripts : OpenMobilityData/Terrebonne-open-sources, 2026-montreal-cars-per-curb-place-by-fsa."),
     }


def layers():
    lim = gpd.read_file(LIMITS).to_crs(CRS)
    city = lim[lim.TYPE == "Arrondissement"]; towns = lim[lim.TYPE != "Arrondissement"][["NOM", "geometry"]].copy()
    U = city.geometry.union_all()
    fsa = gpd.read_file(FSA_SHP, where="PROV = 'QC'")
    fsa = fsa[fsa.FSA.str.startswith("H")][["FSA", "geometry"]].to_crs(CRS).dissolve("FSA").reset_index()
    fsa["geometry"] = fsa.geometry.intersection(U)
    fsa = fsa.explode(index_parts=False)
    fsa = fsa[fsa.geometry.geom_type.isin(["Polygon"]) & (fsa.geometry.area > 5000)].dissolve("FSA").reset_index()   # slivers along the limits dropped
    d = F.table()
    fsa = fsa.merge(d[["status", "per100"]], left_on="FSA", right_index=True, how="left")
    dist = gpd.read_file(DISTRICTS).to_crs(CRS); dist = dist[dist.NOM_DISTRICT.isin(OUTLINED)][["NOM_DISTRICT", "geometry"]]
    lane = gpd.read_file(LANE).to_crs(CRS)[["geometry"]]
    org = U.centroid
    for g in (fsa, towns, dist, lane):
        g["geometry"] = g.geometry.map(lambda x: rotate(x, ANGLE, origin=org))
    cityr = gpd.GeoSeries([rotate(U, ANGLE, origin=org)], crs=CRS)
    return fsa, towns, dist, lane, cityr, d


def halo(w=1.6, c=F.SURFACE):
    return [pe.withStroke(linewidth=w, foreground=c)]


def draw(ax, L, lang, zoom):
    fsa, towns, dist, lane, cityr, d = L
    towns.plot(ax=ax, color=F.TOWN, edgecolor=F.AXIS, linewidth=0.5)
    na = fsa[fsa.status != F.RANKED]
    hat = na.status.fillna("").str.contains("|".join(HATCHED))
    na[hat].plot(ax=ax, facecolor=F.GROUND, edgecolor=F.GREY, hatch="////", linewidth=0)
    na[~hat & na.status.notna()].plot(ax=ax, facecolor=F.GROUND, edgecolor=F.GREY, hatch="....", linewidth=0)
    na[na.status.isna()].plot(ax=ax, color=F.GROUND, linewidth=0)
    rk = fsa[fsa.status == F.RANKED].copy(); rk["k"] = rk.per100.map(F.klass)
    rk.plot(ax=ax, color=[F.RAMP[k] for k in rk.k], linewidth=0)
    fsa.boundary.plot(ax=ax, color=F.SURFACE, linewidth=0.9 if zoom else 0.6)
    cityr.boundary.plot(ax=ax, color=F.MUTED, linewidth=0.5)
    dist.boundary.plot(ax=ax, color=F.SURFACE, linewidth=3.6 if zoom else 2.6)
    dist.boundary.plot(ax=ax, color=F.INK, linewidth=1.8 if zoom else 1.2)
    lane.plot(ax=ax, color=F.SURFACE, linewidth=4.2 if zoom else 2.6); lane.plot(ax=ax, color=F.ORANGE, linewidth=2.4 if zoom else 1.4)
    return rk


def room(g):
    """Centre and radius (m) of the largest circle that fits in the polygon's largest part."""
    g = max(g.geoms, key=lambda x: x.area) if g.geom_type in ("MultiPolygon", "GeometryCollection") else g
    c = maximum_inscribed_circle(g, tolerance=20)
    return c.coords[0], c.length


def label_fsas(ax, L, rk, zoom, box=None):
    """FSA code and value where the label fits (the size steps down with the room; the table holds every value)."""
    fsa = L[0]; skipped = []
    steps = ((420, 10.5), (290, 9), (195, 7.4)) if zoom else ((900, 7.6), (420, 6.6), (280, 5.6))       # (radius needed in m, font size)
    for r in fsa.itertuples():
        g = r.geometry if box is None else r.geometry.intersection(box)
        if g.is_empty or g.area < 150000:
            continue
        (x, y), rad = room(g)
        if r.status == F.RANKED:
            fs = next((f for need, f in steps if rad >= need), None)
            if fs is None:
                skipped.append(r.FSA); continue
            if zoom and r.FSA in LANE_FSAS:
                fs = 12
            ax.text(x, y, f"{r.FSA}\n{r.per100:.0f}", ha="center", va="center", fontsize=fs, color=F.LABEL_INK[F.klass(r.per100)], fontweight="bold", linespacing=1.05, zorder=6)
        elif isinstance(r.status, str) and rad >= (330 if zoom else 900):
            ax.text(x, y, r.FSA, ha="center", va="center", fontsize=8 if zoom else 5.4, color=F.MUTED, zorder=6, path_effects=halo(1.4, F.GROUND))
    return skipped


def furniture(ax, zoom, km=5):
    """North arrow and scale bar, on open water: top right on the City map, bottom left on the enlarged one."""
    nx, ny = np.sin(np.radians(-ANGLE)), np.cos(np.radians(-ANGLE))
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    ln = 0.07 * (y1 - y0)
    bx, by = (x0 + 0.045 * (x1 - x0), y0 + 0.13 * (y1 - y0)) if zoom else (x1 - 0.035 * (x1 - x0), y1 - 0.16 * (y1 - y0))
    ax.annotate("", xy=(bx + ln * nx, by + ln * ny), xytext=(bx, by), arrowprops=dict(arrowstyle="-|>,head_width=0.3,head_length=0.6", color=F.INK, lw=1.4))
    ax.text(bx + 1.35 * ln * nx, by + 1.35 * ln * ny, "N", ha="center", va="center", fontsize=10, fontweight="bold")
    sx, sy = (x0 + 0.03 * (x1 - x0), y0 + 0.05 * (y1 - y0)) if zoom else (x1 - 0.03 * (x1 - x0) - km * 1000, y0 + 0.04 * (y1 - y0))
    ax.plot([sx, sx + km * 1000], [sy, sy], color=F.INK, lw=1.6, solid_capstyle="butt")
    ax.text(sx + km * 500, sy + 0.012 * (y1 - y0), f"{km} km", ha="center", va="bottom", fontsize=8, color=F.INK)


def legend(fig, d, lang, t, x=0.012, y=0.215, w=0.019, h=0.022, gap=0.118):
    rk = d[d.status == F.RANKED]; counts = rk.per100.map(F.klass).value_counts()
    fig.text(x, y + 0.036, t["legend"], fontsize=10, fontweight="bold", va="center")
    for i in range(len(F.CLASSES)):
        fig.patches.append(Rectangle((x + gap * i, y), w, h, transform=fig.transFigure, fc=F.RAMP[i], ec="none"))
        n = int(counts.get(i, 0))
        fig.text(x + gap * i + w + 0.005, y + h / 2, f"{F.class_label(i, lang)}  ({t['n1'] if n == 1 else t['n'].format(n=n)})", fontsize=9, va="center")
    st = d.status.fillna("")
    cnt = lambda s: int(st.str.contains(s).sum())                                         # noqa: E731
    rows = [("////", t["hatch"].format(a=cnt("inventory incomplete"), b=cnt("without any sign"))), ("....", t["dots"].format(a=cnt("businesses"), b=cnt("fewer than")))]
    for i, (hh, lab) in enumerate(rows):
        fig.patches.append(Rectangle((x, y - 0.050 - 0.052 * i), w, h, transform=fig.transFigure, fc=F.GROUND, ec=F.GREY, hatch=hh, lw=0))
        fig.text(x + w + 0.005, y - 0.050 - 0.052 * i + h / 2, lab, fontsize=9, va="center", linespacing=1.2)
    x2 = 0.60
    fig.patches.append(Rectangle((x2, y - 0.050), w, h, transform=fig.transFigure, fc=F.TOWN, ec=F.AXIS, lw=0.6))
    fig.text(x2 + w + 0.005, y - 0.050 + h / 2, t["town"], fontsize=9, va="center")
    fig.lines.append(Line2D([x2, x2 + w], [y - 0.075] * 2, transform=fig.transFigure, color=F.INK, lw=1.4))
    fig.text(x2 + w + 0.005, y - 0.075, t["dist"], fontsize=9, va="center")
    fig.lines.append(Line2D([x2, x2 + w], [y - 0.100] * 2, transform=fig.transFigure, color=F.ORANGE, lw=2))
    fig.text(x2 + w + 0.005, y - 0.100, t["lane"], fontsize=9, va="center")


def main():
    L = layers(); fsa, towns, dist, lane, cityr, d = L
    N = F.numbers()
    for lang, t in T.items():
        key = t["key"].format(b=N["lane_fsas"]["H4B"]["per_100_places"], a=N["lane_fsas"]["H4A"]["per_100_places"], n=N["ranked"],
                              m=f"{100 * N['ratio_median']:.0f}", t=f"{100 * N['ratio_all_ranked']:.0f}")
        for zoom in (False, True):
            fig = plt.figure(figsize=(16, 10.6))
            ax = fig.add_axes([0.005, 0.265, 0.99, 0.635])
            rk = draw(ax, L, lang, zoom)
            if zoom:
                b = dist.total_bounds; m = 2600
                x0, x1, y0, y1 = b[0] - m, b[2] + m, b[1] - m, b[3] + m
                want = (0.99 * 16) / (0.635 * 10.6)                                        # fill the axes: widen the box to the axes' shape
                cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
                if (x1 - x0) / (y1 - y0) < want:
                    x0, x1 = cx - want * (y1 - y0) / 2, cx + want * (y1 - y0) / 2
                else:
                    y0, y1 = cy - (x1 - x0) / want / 2, cy + (x1 - x0) / want / 2
                ax.set_xlim(x0, x1); ax.set_ylim(y0, y1)
                bx = sbox(x0, y0, x1, y1)
                skipped = label_fsas(ax, L, rk, True, bx)
                for r in towns.itertuples():
                    g = r.geometry.intersection(bx)
                    if not g.is_empty and g.area > 400000:
                        p = g.representative_point()
                        ax.text(p.x, p.y, r.NOM, ha="center", va="center", fontsize=8, color=F.MUTED, style="italic", zorder=6)
                for r in dist.itertuples():                                                    # district names just outside the outline, on a white tag
                    b = r.geometry.bounds; top = r.NOM_DISTRICT == "Snowdon"
                    px = b[0] + {"Snowdon": 0.30, "Loyola": 0.14, "Notre-Dame-de-Grâce": 0.46}[r.NOM_DISTRICT] * (b[2] - b[0])
                    edge = r.geometry.boundary.intersection(sbox(px - 150, b[1] - 10, px + 150, b[3] + 10))
                    py = (edge.bounds[3] + 0.022 * (y1 - y0)) if top else (edge.bounds[1] - 0.022 * (y1 - y0))
                    ax.text(px, py, t["district"].format(d=r.NOM_DISTRICT), ha="center", va="center", fontsize=9, color=F.INK, zorder=7,
                            bbox=dict(boxstyle="round,pad=0.25", fc=F.SURFACE, ec=F.INK, lw=0.6))
            else:
                ax.set_aspect("equal"); ax.autoscale_view()
                skipped = label_fsas(ax, L, rk, False)
                for r in towns.itertuples():
                    if r.geometry.area > 5.5e6:
                        p = r.geometry.representative_point()
                        ax.text(p.x, p.y, r.NOM, ha="center", va="center", fontsize=5.6, color=F.MUTED, style="italic", zorder=6)
            ax.set_aspect("equal"); ax.set_axis_off()
            furniture(ax, zoom, km=1 if zoom else 5)
            fig.text(0.012, 0.978, t["title_w"] if zoom else t["title"], fontsize=13.5, fontweight="bold", va="top")
            fig.text(0.012, 0.947, t["sub"], fontsize=10, color=F.MUTED, va="top", linespacing=1.3)
            legend(fig, d, lang, t)
            fig.text(0.60, 0.251, key, fontsize=10, fontweight="bold", va="center")
            foot = "\n".join(textwrap.fill(x.replace("\n", " "), 250) for x in (t["note"], t["src"]))
            fig.text(0.012, 0.012, foot, fontsize=7.6, color=F.MUTED, va="bottom", linespacing=1.3)
            if skipped:
                vals = d.loc[sorted(skipped), "per100"]
                fig.text(0.60, 0.226, t["small"] + " " + ", ".join(f"{f} {v:.0f}" for f, v in vals.items()), fontsize=9, va="center")
            if lang == "en":
                print("west" if zoom else "city", "labels left off the map (listed under it):", sorted(skipped))
            F.save(fig, HERE, "fsa_ratio_map_west" if zoom else "fsa_ratio_map", lang)
    rk = d[d.status == F.RANKED]
    print("classes:", {F.class_label(i, "en"): int((rk.per100.map(F.klass) == i).sum()) for i in range(len(F.CLASSES))})
    print("OK fsa_ratio_map")


if __name__ == "__main__":
    main()
