"""Per corridor area: modelled automobiles, the places of the legal curb, and curb plus private parking under the
scenario (Terrebonne's measured share of buildings with a garage or driveway applied to the area's small buildings).
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

T = {"en": dict(title="With private parking added: a scenario for the corridor",
                sub="Blue: modelled automobiles (90 % interval). Orange: places of the legal curb at 5.5 m (upper bound). Green: curb plus one private place for\n"
                    "{p} % of the area's buildings of five dwellings or fewer, the share with a garage or driveway MEASURED on rue de Terrebonne ({lo}–{hi} %).\n"
                    "The cross streets were not read: for them this share is an assumption. Larger buildings are given no private place.",
                x="vehicles", a="modelled automobiles", b="curb places (upper bound)", c="curb + private places (scenario)",
                note="Corridor: {au} modelled automobiles; {cp} curb places; {tp} with the scenario's {op} private places ({ol}–{oh})."),
     "fr": dict(title="Avec le stationnement privé : un scénario pour le corridor",
                sub="Bleu : automobiles modélisées (intervalle à 90 %). Orange : places de la bordure légale à 5,5 m (borne supérieure). Vert : bordure plus une place\n"
                    "privée pour {p} % des immeubles de cinq logements ou moins de l’aire, la part ayant un garage ou une entrée MESURÉE rue de Terrebonne ({lo}–{hi} %).\n"
                    "Les rues transversales n’ont pas été relevées : pour elles, cette part est une hypothèse. Aucune place privée n’est attribuée aux immeubles plus grands.",
                x="véhicules", a="automobiles modélisées", b="places en bordure (borne supérieure)", c="bordure + places privées (scénario)",
                note="Corridor : {au} automobiles modélisées ; {cp} places en bordure ; {tp} avec les {op} places privées du scénario ({ol}–{oh}).")}


def main():
    s = pd.read_csv(TABLES / "offstreet_scenario_by_da.csv", dtype={"dauid": str})
    O = json.load(open(ROOT / "derived/offstreet.json")); M, S = O["measured"], O["scenario"]
    y = np.arange(len(s))[::-1]
    for lang, t in T.items():
        fig, ax = plt.subplots(figsize=(10, 8.6))
        ax.hlines(y + 0.24, s.low_90, s.high_90, color=F.BLUE, lw=3, alpha=0.5, capstyle="round")
        ax.plot(s.automobiles_modelled, y + 0.24, "o", color=F.BLUE, ms=7, mec=F.SURFACE, mew=1.5, label=t["a"])
        ax.plot(s.legal_m / 5.5, y, "D", color=F.ORANGE, ms=6, mec=F.SURFACE, mew=1.5, label=t["b"])
        ax.hlines(y - 0.24, s.legal_m / 5.5 + s.offstreet_scenario_low, s.legal_m / 5.5 + s.offstreet_scenario_high, color=F.AQUA, lw=3, alpha=0.5, capstyle="round")
        ax.plot(s.legal_m / 5.5 + s.offstreet_scenario, y - 0.24, "s", color=F.AQUA, ms=6.5, mec=F.SURFACE, mew=1.5, label=t["c"])
        ax.set_yticks(y); ax.set_yticklabels([F.fr_frontage(v) if lang == "fr" else v for v in s.frontage], fontsize=8.5)
        ax.grid(axis="x"); ax.grid(axis="y", visible=False); ax.set_xlim(0, 800); ax.set_xlabel(t["x"])
        ax.legend(loc="lower right", fontsize=9)
        f0 = lambda v: F.num(100 * v, lang, 0)
        sub = t["sub"].format(p=f0(M["share"]), lo=f0(M["share_low"]), hi=f0(M["share_high"]))
        note = t["note"].format(au=F.num(S["automobiles_modelled"], lang), cp=F.num(S["curb_places"], lang), tp=F.num(S["curb_plus_offstreet"], lang),
                                op=F.num(S["offstreet_scenario"], lang), ol=F.num(S["offstreet_scenario_low"], lang), oh=F.num(S["offstreet_scenario_high"], lang))
        F.finish(fig, HERE, "off_street_corridor", lang, t["title"], sub, note, top=0.84, bottom=0.15, left=0.3)
    print("OK off_street_corridor")


if __name__ == "__main__":
    main()
