"""Measured on rue de Terrebonne: the buildings read on the 1954-55 plans and today's imagery, their dwellings'
modelled automobiles, the private places (one per building with a garage or driveway, a floor) and today's curb.
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
                sub="The {n} buildings addressed on the street that were read ({d} dwellings). Blue: modelled automobiles of those dwellings. Green: private places,\n"
                    "one per building with a garage as built (1954–55 plans) or a driveway today (imagery): a floor. Orange: places of the street's one parking band today.",
                a="modelled automobiles of the dwellings read", b="private places (measured, floor)", c="curb places on Terrebonne today (5.5 m)", y="vehicles",
                names=["residential west\n(west end – Cavendish)", "institutional\n(Cavendish – Grand)", "residential east\n(Grand – Girouard)", "whole lane"],
                note="Not in the figure: the buildings not read (larger apartment buildings, sheets missing), the cross streets' curb, visitors. On a night of 2015 the City's LiDAR shows\n{l} cars on the lots along the street and {c} at its curbs."),
     "fr": dict(title="La rue de Terrebonne elle-même : automobiles, places privées et bordure",
                sub="Les {n} immeubles ayant leur adresse sur la rue qui ont été relevés ({d} logements). Bleu : automobiles modélisées de ces logements. Vert : places privées,\n"
                    "une par immeuble ayant un garage d’origine (plans de 1954–1955) ou une entrée aujourd’hui (imagerie) : un plancher. Orange : places de l’unique bande de la rue aujourd’hui.",
                a="automobiles modélisées des logements relevés", b="places privées (mesurées, plancher)", c="places en bordure rue de Terrebonne aujourd’hui (5,5 m)", y="véhicules",
                names=["résidentiel ouest\n(extrémité ouest – Cavendish)", "institutionnel\n(Cavendish – Grand)", "résidentiel est\n(Grand – Girouard)", "toute la piste"],
                note="Hors figure : les immeubles non relevés (grands immeubles d’appartements, feuilles manquantes), la bordure des rues transversales, les visiteurs. Une nuit de 2015, le LiDAR\nde la Ville montre {l} voitures sur les terrains le long de la rue et {c} en bordure.")}


def main():
    s = pd.read_csv(TABLES / "offstreet_terrebonne_by_sector.csv")
    x = np.arange(len(s)); w = 0.26; whole = s.iloc[-1]
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 5.8))
        for k, (col, c, lab) in enumerate((("modelled_automobiles_of_those_dwellings", F.BLUE, t["a"]), ("offstreet_places_floor", F.AQUA, t["b"]),
                                           ("curb_places_on_terrebonne_today_5.5m", F.ORANGE, t["c"]))):
            xs = x + (k - 1) * (w + 0.015)
            ax.bar(xs, s[col], w, color=c, label=lab)
            for xi, v in zip(xs, s[col]):
                ax.text(xi, v + 3, F.num(v, lang), ha="center", fontsize=9)
        ax.set_xticks(x); ax.set_xticklabels(t["names"]); ax.set_ylabel(t["y"]); ax.set_ylim(0, 290)
        ax.legend(loc="upper left", fontsize=9)
        sub = t["sub"].format(n=int(whole.buildings_read), d=int(whole.dwellings_in_buildings_read))
        note = t["note"].format(l=int(whole.cars_on_lots_2015_night), c=int(whole.cars_at_curbs_2015_night))
        F.finish(fig, HERE, "off_street_terrebonne", lang, t["title"], sub, note, top=0.8, bottom=0.27)
    print("OK off_street_terrebonne")


if __name__ == "__main__":
    main()
