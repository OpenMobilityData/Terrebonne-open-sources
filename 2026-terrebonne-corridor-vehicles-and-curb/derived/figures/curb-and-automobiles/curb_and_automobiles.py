"""Per corridor area: modelled automobiles (with interval) beside the curb places its legal curb would hold.
Run:  ~/.venvs/omd/bin/python derived/figures/curb-and-automobiles/curb_and_automobiles.py"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402

T = {"en": dict(title="If every vehicle were kept on the street: modelled automobiles and legal curb",
                sub="Blue: automobiles registered to the area's households and businesses, modelled, with 90 % interval. Orange: vehicles the area's legal curb\n"
                    "would hold at 5.5 m each (bar: 6 m to 5 m), an upper bound. Private parking is left out: this is the case where every vehicle is kept at the curb.",
                x="vehicles", a="modelled automobiles", b="curb places (upper bound)", clip="{v} →"),
     "fr": dict(title="Si chaque véhicule était garé sur rue : automobiles modélisées et bordure légale",
                sub="Bleu : automobiles immatriculées par les ménages et entreprises de l’aire, modélisées, intervalle à 90 %. Orange : véhicules que contiendrait\n"
                    "la bordure légale de l’aire à 5,5 m chacun (barre : 6 m à 5 m), une borne supérieure. Le stationnement privé est laissé de côté : c’est le cas où chaque\n"
                    "véhicule est garé en bordure.",
                x="véhicules", a="automobiles modélisées", b="places en bordure (borne supérieure)", clip="{v} →")}
XMAX = 660


def main():
    d = F.corridor()
    y = np.arange(len(d))[::-1]
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 8.2))
        ax.hlines(y + 0.16, d.low_90, d.high_90, color=F.BLUE, lw=3, alpha=0.5, capstyle="round")
        ax.plot(d.automobiles_modelled, y + 0.16, "o", color=F.BLUE, ms=7, mec=F.SURFACE, mew=1.5, label=t["a"])
        p = d.legal_m / 5.5
        ax.hlines(y - 0.16, (d.legal_m / 6).clip(upper=XMAX), (d.legal_m / 5).clip(upper=XMAX), color=F.ORANGE, lw=3, alpha=0.5, capstyle="round")
        ax.plot(p.where(p <= XMAX), y - 0.16, "D", color=F.ORANGE, ms=6, mec=F.SURFACE, mew=1.5, label=t["b"])
        for yi, v in zip(y, p):
            if v > XMAX:
                ax.text(XMAX, yi - 0.16, t["clip"].format(v=F.num(v, lang)), fontsize=8, color=F.MUTED, ha="right", va="center")
        ax.set_yticks(y); ax.set_yticklabels([F.fr_frontage(s) if lang == "fr" else s for s in d.frontage], fontsize=8.5)
        ax.grid(axis="x"); ax.grid(axis="y", visible=False); ax.set_xlim(0, XMAX); ax.set_xlabel(t["x"])
        ax.legend(loc="lower right", fontsize=9)
        F.finish(fig, HERE, "curb_and_automobiles", lang, t["title"], t["sub"], top=0.85, bottom=0.14, left=0.3)
    print("OK curb_and_automobiles")


if __name__ == "__main__":
    main()
