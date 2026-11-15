"""Ranking: registered automobiles and light trucks per 100 curb parking places, the ranked FSAs of the City of
Montréal, 2024 (derived/tables/fsa_ratio.csv), highest first. H4A and H4B (the lane lies in H4B west of Royal and in
H4A east of it) are marked; the names of the boroughs are those holding at least a quarter of the FSA's City curb.

Bar: every block face without a sign counted as legal curb (the method of the map). Open circle: the same count on
the block faces that carry at least one sign (less curb, so a higher value): the two readings bracket what the sign
inventory can say about faces without a sign.
Run:  ~/.venvs/omd/bin/python derived/figures/fsa-ratio-ranking/fsa_ratio_ranking.py
"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from ratio_lib import LANE_FSAS  # noqa: E402

XMAX = 200
CDN = "Côte-des-Neiges–Notre-Dame-de-Grâce"
T = {"en": dict(
        title="Registered automobiles per 100 street parking places:\nthe {n} ranked postal areas (FSAs) of the City of Montréal, 2024",
        sub="Automobiles and light trucks registered in the City part of each FSA (SAAQ, December 31, 2024; type inferred)\nper 100 places of legal curb, at 5.5 m a place. The limiting case in which every registered automobile is kept on\n"
            "the street: it is not a measure of how full the streets are or of how hard parking is.",
        lane={"H4B": "the lane, west of Royal", "H4A": "the lane, east of Royal"},
        bar_lane="FSAs of the bike lane on rue de Terrebonne", bar="other FSAs", dot="the same, counting only the block faces that carry a sign",
        hundred="100: as many registered\nautomobiles as places", median="median {m}", off="{v} (off the scale)",
        x="registered automobiles and light trucks per 100 places of legal curb",
        note="Legal curb: each block face of the City’s géobase (local streets, collectors and arterials), less 10 m at each end, less the stretches where a sign\n"
             "forbids stopping or parking at all times; an upper bound (driveways, hydrants, bus stops, hourly, permit, street-cleaning and seasonal rules are not\n"
             "deducted). Vehicles kept off the street, visitors and vehicles from elsewhere are not counted. At 5 m a place every value is 9 % lower, at 6 m 9 % higher.\n"
             "Not ranked: {inc} FSAs where the borough’s sign inventory is incomplete, {uns} where over 40 % of the curb carries no sign, {fl} with vehicles registered to\n"
             "businesses, {sm} with fewer than 1,000 automobiles in the City part. Boroughs named: those holding at least a quarter of the FSA’s City curb.",
        src="Sources: SAAQ, vehicles released under the access Act (file 03.06.34729); City of Montréal, géobase and inventory of parking signs (CC BY 4.0).\n"
            "FSA boundaries: DMTI Spatial, CanMap Postal Code Suite v2024.3. Tables and scripts: OpenMobilityData/Terrebonne-open-sources."),
     "fr": dict(
        title="Automobiles immatriculées pour 100 places de stationnement sur rue :\nles {n} régions postales (RTA) classées de la Ville de Montréal, 2024",
        sub="Automobiles et camions légers immatriculés dans la partie de chaque RTA située dans la Ville (SAAQ, 31 décembre 2024 ;\ntype inféré) pour 100 places de bordure légale, à 5,5 m la place. Le cas limite où chaque automobile immatriculée est gardée\n"
            "dans la rue : ce n’est pas une mesure de l’occupation des rues ni de la difficulté de se stationner.",
        lane={"H4B": "la piste, à l’ouest de Royal", "H4A": "la piste, à l’est de Royal"},
        bar_lane="RTA de la piste cyclable de la rue de Terrebonne", bar="autres RTA", dot="la même mesure, sur les seuls côtés d’îlot qui portent un panneau",
        hundred="100 : autant d’automobiles\nimmatriculées que de places", median="médiane {m}", off="{v} (hors échelle)",
        x="automobiles et camions légers immatriculés pour 100 places de bordure légale",
        note="Bordure légale : chaque côté d’îlot de la géobase de la Ville (rues locales, collectrices et artères), moins 10 m à chaque extrémité, moins les tronçons\n"
             "où un panneau interdit l’arrêt ou le stationnement en tout temps ; une borne supérieure (entrées charretières, bornes d’incendie, arrêts d’autobus, règles\n"
             "horaires, vignettes, entretien et règles saisonnières non déduits). Les véhicules gardés hors rue, les visiteurs et les véhicules d’ailleurs ne sont pas comptés.\n"
             "À 5 m la place, chaque valeur est 9 % plus basse ; à 6 m, 9 % plus haute. Hors classement : {inc} RTA où l’inventaire de la signalisation de l’arrondissement\n"
             "est incomplet, {uns} où plus de 40 % de la bordure est sans panneau, {fl} où des véhicules sont immatriculés au nom d’entreprises, {sm} de moins de 1 000 automobiles\n"
             "dans la partie située dans la Ville. Arrondissements nommés : ceux qui comptent au moins le quart de la bordure de la RTA située dans la Ville.",
        src="Sources : SAAQ, véhicules communiqués en vertu de la Loi sur l’accès (dossier 03.06.34729) ; Ville de Montréal, géobase et inventaire de la signalisation\n"
            "de stationnement (CC BY 4.0). Limites des RTA : DMTI Spatial, CanMap Postal Code Suite v2024.3. Tableaux et scripts : OpenMobilityData/Terrebonne-open-sources."),
     }


def main():
    d = F.table(); N = F.numbers()
    k = d[d.status == F.RANKED].sort_values("rank")
    n = len(k); y = np.arange(n)[::-1]
    st = d.status.fillna(""); cnt = lambda s: int(st.str.contains(s).sum())      # noqa: E731
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 14.2))
        lane = k.index.isin(LANE_FSAS)
        ax.barh(y, k.per100, height=0.66, color=np.where(lane, F.ORANGE, F.BLUE), zorder=3)
        sg = 100 * k.automobiles_per_place_signed_faces_only
        inside = sg <= XMAX
        ax.scatter(sg[inside], y[inside.values], s=20, facecolor=F.SURFACE, edgecolor=F.INK, linewidth=0.9, zorder=5)
        for yi, v in zip(y[~inside.values], sg[~inside]):
            ax.scatter([XMAX - 2], [yi], s=20, facecolor=F.SURFACE, edgecolor=F.INK, linewidth=0.9, zorder=5)
            ax.text(XMAX - 5, yi, t["off"].format(v=f"{v:.0f}"), ha="right", va="center", fontsize=8, color=F.MUTED, zorder=5)
        ax.axvline(100, color=F.INK, lw=0.9, ls=(0, (4, 3)), zorder=2)
        ax.text(101.5, n - 0.2, t["hundred"], fontsize=8, color=F.INK, va="bottom", ha="left", linespacing=1.15)
        med = 100 * N["ratio_median"]
        ax.axvline(med, color=F.MUTED, lw=0.8, zorder=2)
        ax.text(med - 1.5, n - 0.2, t["median"].format(m=f"{med:.0f}"), fontsize=8, color=F.MUTED, va="bottom", ha="right")
        tr = ax.get_yaxis_transform()
        for yi, (fsa, r) in zip(y, k.iterrows()):
            mark = fsa in LANE_FSAS
            ax.text(r.per100 - 1.6, yi, f"{r.per100:.0f}", va="center", ha="right", fontsize=8.6, fontweight="bold", color=F.INK if mark else "#ffffff", zorder=6)
            if mark:                                                                # the value sits inside the bar end; the note clears the open circle
                ax.text(max(r.per100, 100 * r.automobiles_per_place_signed_faces_only) + 3, yi, t["lane"][fsa], va="center", ha="left", fontsize=9, fontweight="bold",
                        color=F.INK, zorder=6, bbox=dict(boxstyle="square,pad=0.12", fc=F.SURFACE, ec="none"))
            b = F.boroughs_label(r.boroughs)
            ax.text(-0.012, yi, b, transform=tr, ha="right", va="center", fontsize=8.2, color=F.INK if (CDN in b or mark) else F.MUTED, fontweight="bold" if mark else "normal")
            ax.text(-0.555, yi, fsa, transform=tr, ha="left", va="center", fontsize=9, fontweight="bold", color=F.INK)
            ax.text(-0.575, yi, f"{r['rank']:.0f}", transform=tr, ha="right", va="center", fontsize=8, color=F.MUTED)
        ax.set_yticks([]); ax.set_ylim(-0.7, n + 1.6); ax.set_xlim(0, XMAX)
        ax.set_xticks(range(0, XMAX + 1, 25)); ax.tick_params(axis="x", labelsize=8.5)
        ax.set_xlabel(t["x"], fontsize=9, labelpad=6)
        fig.subplots_adjust(left=0.395, right=0.975, top=0.868, bottom=0.15)
        fig.text(0.02, 0.985, t["title"].format(n=n), fontsize=13.5, fontweight="bold", va="top", linespacing=1.2)
        fig.text(0.02, 0.946, t["sub"], fontsize=9.6, color=F.MUTED, va="top", linespacing=1.3)
        ly = 0.884
        for i, (c, lab) in enumerate(((F.ORANGE, t["bar_lane"]), (F.BLUE, t["bar"]))):
            x0 = 0.02 + 0.40 * i
            fig.patches.append(Rectangle((x0, ly - 0.004), 0.022, 0.008, transform=fig.transFigure, fc=c, ec="none"))
            fig.text(x0 + 0.03, ly, lab, fontsize=9, va="center")
        fig.lines.append(Line2D([0.56], [ly], transform=fig.transFigure, marker="o", ms=5, mfc=F.SURFACE, mec=F.INK, mew=0.9, ls="none"))
        fig.text(0.572, ly, t["dot"], fontsize=9, va="center")
        fig.text(0.02, 0.012, t["note"].format(inc=cnt("inventory incomplete"), uns=cnt("without any sign"), fl=cnt("businesses"), sm=cnt("fewer than")) + "\n" + t["src"],
                 fontsize=7.6, color=F.MUTED, va="bottom", linespacing=1.3)
        F.save(fig, HERE, "fsa_ratio_ranking", lang)
    print("ranked:", n, "; lane FSAs:", {f: (int(k.loc[f, "rank"]), int(k.loc[f, "per100"])) for f in LANE_FSAS})
    print("OK fsa_ratio_ranking")


if __name__ == "__main__":
    main()
