"""Check, not input: cars seen along rue de Terrebonne on the 2015 LiDAR night (curbs and lots) against the
modelled automobiles of the dwellings addressed on the street, by sector.
Run:  ~/.venvs/omd/bin/python derived/figures/lidar-check/lidar_check.py"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import TABLES  # noqa: E402

T = {"en": dict(title="A check from another source: cars seen along Terrebonne on a 2015 night",
                sub="Per dwelling addressed on rue de Terrebonne (City roll). Grey: cars counted by eye on the City's 2015 night LiDAR, at the curbs and on the\n"
                    "lots along the street. Blue: the model's 2024 automobiles per household for the areas holding those dwellings.",
                a="cars seen, 2015 night (curbs and lots)", b="modelled automobiles, 2024", y="per dwelling",
                names=["residential west\n(west end – Cavendish)", "institutional\n(Cavendish – Grand)", "residential east\n(Grand – Girouard)", "whole lane"],
                note="The two are not the same quantity: the LiDAR sees visitors' cars and the lots of churches, schools and corner buildings, and misses cars inside garages or away;\nnine years separate them. The check is on the order of magnitude."),
     "fr": dict(title="Une vérification par une autre source : les voitures vues le long de Terrebonne une nuit de 2015",
                sub="Par logement ayant son adresse rue de Terrebonne (rôle de la Ville). Gris : voitures comptées à l’œil sur le LiDAR nocturne de 2015 de la Ville,\n"
                    "en bordure et sur les terrains le long de la rue. Bleu : automobiles par ménage du modèle (2024) pour les aires où se trouvent ces logements.",
                a="voitures vues, nuit de 2015 (bordures et terrains)", b="automobiles modélisées, 2024", y="par logement",
                names=["résidentiel ouest\n(extrémité ouest – Cavendish)", "institutionnel\n(Cavendish – Grand)", "résidentiel est\n(Grand – Girouard)", "toute la piste"],
                note="Les deux grandeurs diffèrent : le LiDAR voit les voitures des visiteurs et les terrains des églises, écoles et immeubles d’angle, et ne voit pas les voitures dans les garages\nou absentes ; neuf ans les séparent. La vérification porte sur l’ordre de grandeur.")}


def main():
    s = pd.read_csv(TABLES / "lidar_check_by_sector.csv")
    x = np.arange(len(s)); w = 0.34
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 5.6))
        for off, col, c, lab in ((-w / 2 - 0.01, "cars_seen_per_dwelling", F.GREY, t["a"]), (w / 2 + 0.01, "modelled_automobiles_per_household", F.BLUE, t["b"])):
            ax.bar(x + off, s[col], w, color=c, label=lab)
            for xi, v in zip(x + off, s[col]):
                ax.text(xi, v + 0.02, F.num(v, lang, 2), ha="center", fontsize=9)
        ax.set_xticks(x); ax.set_xticklabels(t["names"]); ax.set_ylabel(t["y"]); ax.set_ylim(0, 1.3)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: F.num(v, lang, 1)))
        ax.legend(loc="upper center", ncol=2, fontsize=9, bbox_to_anchor=(0.5, 1.02))
        F.finish(fig, HERE, "lidar_check", lang, t["title"], t["sub"], t["note"], top=0.8, bottom=0.26)
    print("OK lidar_check")


if __name__ == "__main__":
    main()
