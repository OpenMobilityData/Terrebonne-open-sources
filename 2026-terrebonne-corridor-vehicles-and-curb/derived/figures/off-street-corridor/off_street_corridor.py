"""Per corridor area: modelled automobiles, the places of the legal curb, and curb plus private places as measured
(every lot read from above, calibrated on the owner's check of a random sample from street-level imagery).
Run:  ~/.venvs/omd/bin/python derived/figures/off-street-corridor/off_street_corridor.py"""
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

T = {"en": dict(title="With private parking added: the corridor, area by area",
                sub="Blue: modelled automobiles (90 % interval). Orange: places of the legal curb at 5.5 m (upper bound). Green: curb plus the private places\n"
                    "of buildings of five dwellings or fewer, counting only places a car can leave without another being moved (90 % interval).\n"
                    "Every lot was read on aerial imagery; the estimate is calibrated on {n} lots judged by the author from street-level imagery.",
                x="vehicles", a="modelled automobiles", b="curb places (upper bound)", c="curb + private places (measured)",
                note="Corridor: {au} modelled automobiles; {cp} curb places; {tp} with {op} private places ({ol}–{oh}). Not counted: garage interiors,\nand the parking of the {lb} buildings of six dwellings or more ({ld} dwellings), several of which have an underground garage."),
     "fr": dict(title="Avec le stationnement privé : le corridor, aire par aire",
                sub="Bleu : automobiles modélisées (intervalle à 90 %). Orange : places de la bordure légale à 5,5 m (borne supérieure). Vert : bordure plus les places\n"
                    "privées des immeubles de cinq logements ou moins, en ne comptant que celles d’où une voiture peut sortir sans en déplacer une autre (intervalle à 90 %).\n"
                    "Chaque terrain a été relevé sur imagerie aérienne ; l’estimation est calée sur {n} terrains jugés par l’auteur à partir d’images prises de la rue.",
                x="véhicules", a="automobiles modélisées", b="places en bordure (borne supérieure)", c="bordure + places privées (mesurées)",
                note="Corridor : {au} automobiles modélisées ; {cp} places en bordure ; {tp} avec {op} places privées ({ol}–{oh}). Non comptés : l’intérieur des garages\net le stationnement des {lb} immeubles de six logements ou plus ({ld} logements), dont plusieurs ont un garage souterrain.")}


def main():
    s = pd.read_csv(TABLES / "offstreet_measured_by_da.csv", dtype={"dauid": str})
    O = json.load(open(ROOT / "derived/offstreet.json")); S, K = O["corridor"], O["check"]
    y = np.arange(len(s))[::-1]; curb = s.legal_m / 5.5
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 8.6))
        ax.hlines(y + 0.24, s.low_90, s.high_90, color=F.BLUE, lw=3, alpha=0.5, capstyle="round")
        ax.plot(s.automobiles_modelled, y + 0.24, "o", color=F.BLUE, ms=7, mec=F.SURFACE, mew=1.5, label=t["a"])
        ax.plot(curb, y, "D", color=F.ORANGE, ms=6, mec=F.SURFACE, mew=1.5, label=t["b"])
        ax.hlines(y - 0.24, curb + s.private_independent_low, curb + s.private_independent_high, color=F.AQUA, lw=3, alpha=0.5, capstyle="round")
        ax.plot(curb + s.private_independent, y - 0.24, "s", color=F.AQUA, ms=6.5, mec=F.SURFACE, mew=1.5, label=t["c"])
        ax.set_yticks(y); ax.set_yticklabels([F.fr_frontage(v) if lang == "fr" else v for v in s.frontage], fontsize=8.5)
        ax.grid(axis="x"); ax.grid(axis="y", visible=False); ax.set_xlim(0, 860); ax.set_xlabel(t["x"])
        ax.legend(loc="lower right", fontsize=9)
        note = t["note"].format(au=F.num(S["automobiles_modelled"], lang), cp=F.num(S["curb_places"], lang), tp=F.num(S["curb_plus_private"], lang),
                                op=F.num(S["private_independent"], lang), ol=F.num(S["private_independent_low"], lang), oh=F.num(S["private_independent_high"], lang),
                                lb=S["large_buildings"], ld=F.num(S["dwellings_in_large_buildings"], lang))
        F.finish(fig, HERE, "off_street_corridor", lang, t["title"], t["sub"].format(n=K["small_judged"]), note, top=0.84, bottom=0.16, left=0.3)
    print("OK off_street_corridor")


if __name__ == "__main__":
    main()
