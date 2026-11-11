"""Modelled automobiles per household for each corridor area, with 90 % intervals, west to east.
Run:  ~/.venvs/omd/bin/python derived/figures/area-estimates/area_estimates.py"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402

T = {"en": dict(title="Modelled automobiles per household, corridor areas from west to east",
                sub="Point: the model's estimate, scaled to the FSA's registered total. Bar: 90 % interval. Thin bar: the interval if the unexplained\n"
                    "spread among dissemination areas is twice the one measured among FSAs. Grey lines: the registered rates of H4B and H4A.",
                x="automobiles and light trucks per household, 2024 (modelled)", reg="registered"),
     "fr": dict(title="Automobiles modélisées par ménage, aires du corridor d’ouest en est",
                sub="Point : estimation du modèle, ramenée au total immatriculé de la RTA. Barre : intervalle à 90 %. Barre fine : l’intervalle si la dispersion\n"
                    "inexpliquée entre aires de diffusion est le double de celle mesurée entre RTA. Lignes grises : taux immatriculés de H4B et H4A.",
                x="automobiles et camions légers par ménage, 2024 (modélisé)", reg="immatriculé")}


def main():
    d = F.corridor(); N = F.numbers()
    y = np.arange(len(d))[::-1]
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 8))
        hh = d.households
        ax.hlines(y, d.low_90_wide / hh, d.high_90_wide / hh, color=F.BLUE, lw=1, alpha=0.55)
        ax.hlines(y, d.low_90 / hh, d.high_90 / hh, color=F.BLUE, lw=3.2, alpha=0.55, capstyle="round")
        ax.plot(d.per_household, y, "o", color=F.BLUE, ms=7, mec=F.SURFACE, mew=1.5)
        for k in ("H4B", "H4A"):
            v = N["fsa"][k]["per_household"]
            ax.axvline(v, color=F.GREY, lw=1, ls=(0, (4, 3)))
            ax.text(v, len(d) - 0.35, f"{k} {t['reg']} {F.num(v, lang, 2)}", fontsize=8, color=F.MUTED, ha="right" if k == "H4B" else "left", va="bottom")
        ax.set_yticks(y); ax.set_yticklabels([F.fr_frontage(s) if lang == "fr" else s for s in d.frontage], fontsize=8.5)
        ax.set_ylim(-0.7, len(d) + 0.3)
        ax.grid(axis="x"); ax.grid(axis="y", visible=False)
        ax.set_xlabel(t["x"]); ax.set_xlim(0.3, max(1.9, (d.high_90_wide / hh).max() * 1.03))
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: F.num(v, lang, 1)))
        F.finish(fig, HERE, "area_estimates", lang, t["title"], t["sub"], top=0.86, bottom=0.14, left=0.3)
    print("OK area_estimates")


if __name__ == "__main__":
    main()
