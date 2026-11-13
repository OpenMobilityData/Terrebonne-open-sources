"""District scale: night by night, December 1 to March 31, five winters, modelled automobiles as a share of the places of the
district's part of the corridor, the night's share of the curb under a loading ban taken from the sector's truckloads.
Run:  ~/.venvs/omd/bin/python derived/figures/snow-loading-districts/snow_loading_districts.py   (after scripts/snow_loading.py)"""
import json
import sys
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import ROOT, TABLES  # noqa: E402

T = {"en": dict(title="Snow-loading nights, district by district: modelled automobiles as a share of places",
                sub="Each night from December 1 to March 31. If displaced cars can park anywhere in the district's part of the corridor, the night's loss of curb is the\n"
                    "share of the operation's truckloads hauled in the sector that night (loading assumed to proceed evenly over the sector).\n"
                    "Orange: curb alone. Green: curb and private places. Shaded: the share of the curb under a ban that night. Capacity, not occupancy.",
                cols={"Loyola": "Loyola district", "Notre-Dame-de-Grâce": "Notre-Dame-de-Grâce district"},
                curb="curb alone", withp="curb and private places", ban="curb under a ban",
                over="{n} nights over 100 % (curb alone)", none="no night over 100 %",
                note="Places: legal curb at 5.5 m (measured, upper bound) and private places of small buildings (measured). Automobiles MODELLED. Loading: City of Montréal,\n"
                     "snow-removal transactions by sector and day; operations of ≥ {op} truckloads; spot removals left out. Loyola includes the Doug-Harvey free lot (20 places) in the winters it was listed."),
     "fr": dict(title="Nuits de chargement de la neige, district par district : automobiles modélisées en part des places",
                sub="Chaque nuit du 1er décembre au 31 mars. Si les voitures déplacées peuvent se garer n’importe où dans la partie du corridor qui est dans le district, la bordure perdue\n"
                    "cette nuit-là est la part des chargements de l’opération faits dans le secteur cette nuit-là (chargement supposé uniforme dans le secteur).\n"
                    "Orange : bordure seulement. Vert : bordure et places privées. Ombré : part de la bordure interdite cette nuit-là. Capacité, pas occupation.",
                cols={"Loyola": "District de Loyola", "Notre-Dame-de-Grâce": "District de Notre-Dame-de-Grâce"},
                curb="bordure seulement", withp="bordure et places privées", ban="bordure interdite",
                over="{n} nuits au-delà de 100 % (bordure seulement)", none="aucune nuit au-delà de 100 %",
                note="Places : bordure légale à 5,5 m (mesurée, borne supérieure) et places privées des petits immeubles (mesurées). Automobiles MODÉLISÉES. Chargement : Ville de Montréal,\n"
                     "transactions de déneigement par secteur et par jour ; opérations de ≥ {op} chargements ; chargements ponctuels exclus. Loyola compte le stationnement gratuit de l’aréna Doug-Harvey (20 places) les hivers où il était listé.")}


def main():
    d = pd.read_csv(TABLES / "snow_loading_district_nights.csv", parse_dates=["day"])
    S = json.load(open(ROOT / "derived/snow_loading.json"))
    seasons = S["winters"]; dists = ["Loyola", "Notre-Dame-de-Grâce"]
    for lang, t in T.items():
        fig, axes = plt.subplots(len(seasons), 2, figsize=(13, 11), sharey=True)
        for i, ss in enumerate(seasons):
            for j, dn in enumerate(dists):
                ax = axes[i, j]; x = d[(d.season == ss) & (d.district == dn)]
                ax.fill_between(x.day, 0, x.share_of_curb_under_ban, step="mid", color="#d9dcd6", lw=0, label=t["ban"])
                ax.axhline(1.0, color=F.INK, lw=1)
                ax.plot(x.day, x.share_curb_only, color=F.ORANGE, lw=2, label=t["curb"], drawstyle="steps-mid")
                ax.plot(x.day, x.share_with_private, color=F.AQUA, lw=2, label=t["withp"], drawstyle="steps-mid")
                n = int((x.share_curb_only > 1).sum())
                ax.text(0.99, 0.985, t["over"].format(n=n) if n else t["none"], transform=ax.transAxes, ha="right", va="top", fontsize=8, color=F.INK)
                ax.set_ylim(0, 1.8); ax.set_yticks([0, 0.5, 1.0, 1.5]); ax.set_yticklabels(["0", "50 %", "100 %", "150 %"])
                ax.xaxis.set_major_locator(mdates.MonthLocator()); ax.xaxis.set_major_formatter(mdates.DateFormatter("%b" if lang == "en" else "%m"))
                if lang == "fr":
                    ax.set_xticks(ax.get_xticks()); ax.set_xticklabels(["déc.", "janv.", "févr.", "mars", "avr."][:len(ax.get_xticks())])
                if j == 0:
                    ax.set_ylabel(ss[:5].replace("-", "–") + ss[-2:], rotation=0, ha="right", va="center", color=F.INK, fontsize=9.5)
                if i == 0:
                    ax.set_title(t["cols"][dn], loc="left", fontsize=10.5, fontweight="bold", color=F.INK)
        h, l = axes[0, 0].get_legend_handles_labels()
        fig.legend(h[::-1], l[::-1], loc="upper left", bbox_to_anchor=(0.10, 0.875), ncol=3, fontsize=9)
        F.finish(fig, HERE, "snow_loading_districts", lang, t["title"], t["sub"], t["note"].format(op=S["operation_min_truckloads"]),
                 top=0.83, bottom=0.12, left=0.11, right=0.98)
    print("OK snow_loading_districts")


if __name__ == "__main__":
    main()
