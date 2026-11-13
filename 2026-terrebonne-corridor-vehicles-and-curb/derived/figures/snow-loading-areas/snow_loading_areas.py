"""Per corridor area: modelled automobiles as a share of places on an ordinary night and on the area's own snow-loading
night, under the three assumptions on the share of its curb under a ban (25, 50, 100 %); A with private places, B curb alone.
Run:  ~/.venvs/omd/bin/python derived/figures/snow-loading-areas/snow_loading_areas.py   (after scripts/snow_loading.py)"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import ROOT, TABLES  # noqa: E402

CAP = 4.0                                    # x axis ends at 400 %; beyond it the marker sits on the edge with its value
QCOL = {25: "#9cc0ea", 50: "#2a78d6", 100: "#123f7a"}
T = {"en": dict(title="Snow-loading nights: modelled automobiles as a share of places, area by area",
                sub="Grey: an ordinary night. Blue, light to dark: the night the area's own streets are under a loading ban, if the ban takes 25 %, 50 % (central case)\n"
                    "or 100 % of its legal curb that night. Which streets are loaded on which night is not published: these are assumptions, not observations.\n"
                    "A share of places compares capacity, not occupancy; registered automobiles stand in for overnight demand.",
                A="A. Curb and private places", B="B. Curb alone (at 100 % no curb is left)", x="modelled automobiles as % of places",
                o="ordinary night", q="loading night, {q} % of the curb under a ban", nights="nights a winter\npushed over 100 %\n(50 %, A)",
                already="over 100 %\nalready", none="",
                note="Places: legal curb at 5.5 m (measured, upper bound) and private places of buildings of five dwellings or fewer (measured, calibrated on a street-level check).\n"
                     "Nights a winter: full loading operations in the area's sector (≥ {op} truckloads), mean of the five winters {w0} to {w1}, two nights an operation at 50 %. Hatched: most households in\n"
                     "buildings of six dwellings or more, whose garages are not counted. City of Montréal, snow-removal transactions and sectors (CC BY 4.0)."),
     "fr": dict(title="Nuits de chargement de la neige : automobiles modélisées en part des places, aire par aire",
                sub="Gris : une nuit ordinaire. Bleu, du clair au foncé : la nuit où les rues de l’aire sont visées par l’interdiction de chargement, si elle retire 25 %, 50 % (cas central)\n"
                    "ou 100 % de sa bordure légale cette nuit-là. Les rues chargées chaque nuit ne sont pas publiées : ce sont des hypothèses, non des observations.\n"
                    "Une part des places compare des capacités, pas l’occupation ; les automobiles immatriculées tiennent lieu de la demande de nuit.",
                A="A. Bordure et places privées", B="B. Bordure seulement (à 100 %, plus de bordure)", x="automobiles modélisées en % des places",
                o="nuit ordinaire", q="nuit de chargement, {q} % de la bordure interdite", nights="nuits par hiver\nau-delà de 100 %\n(50 %, A)",
                already="déjà au-delà\nde 100 %", none="",
                note="Places : bordure légale à 5,5 m (mesurée, borne supérieure) et places privées des immeubles de cinq logements ou moins (mesurées, calées sur une vérification de la rue).\n"
                     "Nuits par hiver : opérations complètes de chargement dans le secteur de l’aire (≥ {op} chargements), moyenne des cinq hivers {w0} à {w1}, deux nuits par opération à 50 %. Hachurées :\n"
                     "aires où la plupart des ménages vivent dans des immeubles de six logements ou plus, dont les garages ne sont pas comptés. Ville de Montréal, transactions et secteurs de déneigement (CC BY 4.0).")}


def panel(ax, y, a, kind, lang, t, hatch):
    ord_ = a[f"share_ordinary_{kind}"].values
    ax.axvline(1.0, color=F.INK, lw=1, zorder=1)
    for i, h in zip(y, hatch):
        if h:
            ax.axhspan(i - 0.5, i + 0.5, fill=False, hatch="////", ec="#d5d8d3", lw=0, zorder=0.6)
    for q in ((25, 50, 100) if kind == "with_private" else (25, 50)):    # B at 100 %: no curb left, the share is undefined
        v = a[f"share_q{q}_{kind}"].replace(np.inf, np.nan).values
        vv = np.where(np.isnan(v), CAP, np.minimum(v, CAP))
        if q == max((25, 50, 100) if kind == "with_private" else (25, 50)):
            ax.hlines(y, ord_, vv, color=QCOL[q], lw=1.2, zorder=2)
        ax.plot(vv, y, "o", color=QCOL[q], ms=7.5, mec=F.SURFACE, mew=1.5, zorder=4, label=t["q"].format(q=q))
        for i, raw in zip(y, v):
            if np.isnan(raw) or raw > CAP:
                ax.text(CAP + 0.06, i, "∞" if np.isnan(raw) else f"{100 * raw:.0f} %", va="center", ha="left", fontsize=7.5, color=F.MUTED, clip_on=False)
    ax.plot(ord_, y, "o", color=F.GREY, ms=7.5, mec=F.SURFACE, mew=1.5, zorder=5, label=t["o"])
    ax.set_xlim(0, CAP); ax.set_xticks([0, 1, 2, 3, 4]); ax.set_xticklabels([f"{100 * k} %" for k in range(5)])
    ax.grid(axis="x"); ax.grid(axis="y", visible=False); ax.set_xlabel(t["x"])
    F.row_bands(ax, len(y))
    ax.set_title(t["A"] if kind == "with_private" else t["B"], loc="left", fontsize=10.5, fontweight="bold", color=F.INK)


def main():
    a = pd.read_csv(TABLES / "snow_loading_areas.csv", dtype={"dauid": str}).sort_values("no").reset_index(drop=True)
    S = json.load(open(ROOT / "derived/snow_loading.json"))
    y = np.arange(len(a))[::-1]
    hatch = (a.large_building_share > 0.5).values
    for lang, t in T.items():
        fig, (axA, axB) = plt.subplots(1, 2, figsize=(13, 10.4), sharey=True)
        panel(axA, y, a, "with_private", lang, t, hatch)
        panel(axB, y, a, "curb_only", lang, t, hatch)
        labels = [f"{n}. " + (F.fr_frontage(v) if lang == "fr" else v) for n, v in zip(a.no, a.frontage)]
        axA.set_yticks(y); axA.set_yticklabels(labels, fontsize=8.2)
        tr = axB.get_yaxis_transform()
        axB.text(1.13, len(y) - 0.42, t["nights"], transform=tr, ha="center", va="bottom", fontsize=8, color=F.MUTED, linespacing=1.1, clip_on=False)
        for i, r in zip(y, a.itertuples()):
            lab = t["already"] if r.share_ordinary_with_private > 1 else F.num(r.nights_per_winter_q50_with_private, lang, 1)
            axB.text(1.13, i, lab, transform=tr, ha="center", va="center", fontsize=8.5 if r.share_ordinary_with_private <= 1 else 7,
                     color=F.INK, fontweight="bold" if r.nights_per_winter_q50_with_private > 0 else "normal", clip_on=False, linespacing=1.0)
        h, l = axA.get_legend_handles_labels()
        order = [3, 0, 1, 2]
        fig.legend([h[k] for k in order], [l[k] for k in order], loc="upper left", bbox_to_anchor=(0.008, 0.885), ncol=4, fontsize=9, columnspacing=1.2, handletextpad=0.3)
        w = [x[:5] + x[-2:] for x in S["winters"]]
        F.finish(fig, HERE, "snow_loading_areas", lang, t["title"], t["sub"],
                 t["note"].format(op=S["operation_min_truckloads"], w0=w[0].replace("-", "–"), w1=w[-1].replace("-", "–")), top=0.815, bottom=0.15, left=0.25, right=0.88)
    print("OK snow_loading_areas")


if __name__ == "__main__":
    main()
