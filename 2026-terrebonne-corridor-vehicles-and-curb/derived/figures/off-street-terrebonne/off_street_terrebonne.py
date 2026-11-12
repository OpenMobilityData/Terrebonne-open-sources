"""Measured on rue de Terrebonne: every lot addressed on the street along the lane, judged from street level by the
owner (Nov 12, 2026): the modelled automobiles of the dwellings in its buildings of five dwellings or fewer, their
private places as counted lot by lot (independent places), and today's curb.
Run:  ~/.venvs/omd/bin/python derived/figures/off-street-terrebonne/off_street_terrebonne.py"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import TABLES  # noqa: E402

T = {"en": dict(title="Rue de Terrebonne itself: automobiles, private places and curb",
                sub="The {n} buildings of five dwellings or fewer on the street, judged from street level on Nov. 12, 2026 ({d} dwellings).\n"
                    "Blue: their modelled automobiles. Green: their private places, counted lot by lot. Orange: the street's one parking band today.",
                a="modelled automobiles of those dwellings", b="private places, independent (measured)", c="curb places on Terrebonne today (5.5 m)", y="vehicles",
                names=["residential west\n(west end – Cavendish)", "institutional\n(Cavendish – Grand)", "residential east\n(Grand – Girouard)", "whole lane"],
                note="Not in the figure: the {g} larger buildings ({gd} dwellings; {gu} with an underground garage whose places cannot be counted), garage interiors, places in tandem\n({pt} places in all on the small lots), the cross streets' curb, visitors. On a night of 2015 the City's LiDAR shows {l} cars on the lots along the street and {c} at its curbs."),
     "fr": dict(title="La rue de Terrebonne elle-même : automobiles, places privées et bordure",
                sub="Les {n} immeubles de cinq logements ou moins de la rue, vérifiés à hauteur de rue le 12 nov. 2026 ({d} logements).\n"
                    "Bleu : leurs automobiles modélisées. Vert : leurs places privées, comptées lot par lot. Orange : l’unique bande de la rue aujourd’hui.",
                a="automobiles modélisées de ces logements", b="places privées indépendantes (mesurées)", c="places en bordure rue de Terrebonne aujourd’hui (5,5 m)", y="véhicules",
                names=["résidentiel ouest\n(extrémité ouest – Cavendish)", "institutionnel\n(Cavendish – Grand)", "résidentiel est\n(Grand – Girouard)", "toute la piste"],
                note="Hors figure : les {g} grands immeubles ({gd} logements; {gu} avec un garage souterrain dont les places ne peuvent être comptées), l’intérieur des garages, les places en file\n({pt} places en tout sur les petits lots), la bordure des rues transversales, les visiteurs. Une nuit de 2015, le LiDAR de la Ville montre {l} voitures sur les terrains et {c} en bordure.")}


def main():
    s = pd.read_csv(TABLES / "offstreet_terrebonne_by_sector.csv")
    x = np.arange(len(s)); w = 0.26; whole = s.iloc[-1]
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 5.8))
        for k, (col, c, lab) in enumerate((("modelled_automobiles_small_judged", F.BLUE, t["a"]), ("private_places_independent", F.AQUA, t["b"]),
                                           ("curb_places_on_terrebonne_today_5.5m", F.ORANGE, t["c"]))):
            xs = x + (k - 1) * (w + 0.015)
            ax.bar(xs, s[col], w, color=c, label=lab)
            for xi, v in zip(xs, s[col]):
                ax.text(xi, v + 3, F.num(v, lang), ha="center", fontsize=9)
        ax.set_xticks(x); ax.set_xticklabels(t["names"]); ax.set_ylabel(t["y"]); ax.set_ylim(0, 290)
        ax.legend(loc="upper left", fontsize=9)
        sub = t["sub"].format(n=int(whole.small_lots_judged), d=int(whole.dwellings_small_judged))
        note = t["note"].format(g=int(whole.large_lots), gd=int(whole.dwellings_large), gu=int(whole.large_with_underground_garage), pt=int(whole.private_places_total),
                                l=int(whole.cars_on_lots_2015_night), c=int(whole.cars_at_curbs_2015_night))
        F.finish(fig, HERE, "off_street_terrebonne", lang, t["title"], sub, note, top=0.8, bottom=0.27)
    print("OK off_street_terrebonne")


if __name__ == "__main__":
    main()
