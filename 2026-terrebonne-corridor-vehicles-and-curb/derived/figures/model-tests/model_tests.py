"""The two tests of the model: each FSA left out in turn (predicted against registered), and the downscaling
test one level up (a group's total shared among its FSAs: model against the split in proportion to households).
Run:  ~/.venvs/omd/bin/python derived/figures/model-tests/model_tests.py"""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "scripts"))
import fig_lib as F  # noqa: E402
from corridor_lib import TABLES  # noqa: E402

T = {"en": dict(title="Testing the model where the answer is known: FSAs",
                sub="Left: each FSA's rate predicted by a model fitted without it. Right: a group of neighbouring FSAs' registered total shared among\n"
                    "its members, by the model and in proportion to households; error of each member's share.",
                x1="registered automobiles per household", y1="predicted when left out", h1="Each FSA left out in turn", h2="Sharing a group's total among its FSAs",
                m="model", p="in proportion to households", y2="absolute error of the share (%)", med="median", fleet="FSAs with fleets registered to businesses\n(registered more than 1.5 times predicted)"),
     "fr": dict(title="Le modèle mis à l’épreuve là où la réponse est connue : les RTA",
                sub="À gauche : le taux de chaque RTA prédit par un modèle ajusté sans elle. À droite : le total immatriculé d’un groupe de RTA voisines\n"
                    "réparti entre ses membres, par le modèle et au prorata des ménages ; erreur de la part de chaque membre.",
                x1="automobiles immatriculées par ménage", y1="prédit lorsque la RTA est retirée", h1="Chaque RTA retirée à son tour", h2="Répartir le total d’un groupe entre ses RTA",
                m="modèle", p="au prorata des ménages", y2="erreur absolue de la part (%)", med="médiane", fleet="RTA comptant des parcs immatriculés par des entreprises\n(immatriculé supérieur à 1,5 fois le prédit)")}


def main():
    lo = pd.read_csv(TABLES / "lofo_errors.csv", index_col=0)
    ds = pd.read_csv(TABLES / "downscaling_test.csv")
    rng = np.random.default_rng(1)
    for lang, t in T.items():
        fig, (a, b) = plt.subplots(1, 2, figsize=(10, 5.6), gridspec_kw={"width_ratios": [1.15, 1]})
        fl = lo["registered_over_1.5_times_predicted"]
        a.plot([0.25, 7], [0.25, 7], color=F.GREY, lw=1)
        a.scatter(lo.automobiles_per_household[~fl], lo.predicted_when_left_out[~fl], s=26, color=F.BLUE, edgecolor=F.SURFACE, linewidth=0.8, zorder=3)
        a.scatter(lo.automobiles_per_household[fl], lo.predicted_when_left_out[fl], s=30, facecolor=F.SURFACE, edgecolor=F.BLUE, linewidth=1.4, zorder=3)
        for k in ("H4A", "H4B"):
            a.annotate(k, (lo.automobiles_per_household[k], lo.predicted_when_left_out[k]), xytext=(26, -16) if k == "H4A" else (-44, 26), textcoords="offset points", fontsize=8.5,
                       arrowprops=dict(arrowstyle="-", color=F.MUTED, lw=0.7))
        a.text(1.45, 0.32, t["fleet"], fontsize=8, color=F.MUTED, va="center")
        a.set_xscale("log"); a.set_yscale("log"); a.set_xlim(0.25, 7); a.set_ylim(0.25, 7)
        tk = [0.3, 0.5, 1, 2, 4]
        for ax_ in (a.xaxis, a.yaxis):
            ax_.set_major_locator(plt.FixedLocator(tk)); ax_.set_major_formatter(plt.FuncFormatter(lambda v, _: F.num(v, lang, 1))); ax_.set_minor_locator(plt.NullLocator())
        a.grid(axis="x"); a.set_xlabel(t["x1"]); a.set_ylabel(t["y1"]); a.set_title(t["h1"], fontsize=10.5, loc="left")
        for i, (col, c, name) in enumerate((("model_error_pct", F.BLUE, t["m"]), ("households_error_pct", F.ORANGE, t["p"]))):
            v = ds[col].abs().clip(upper=80)
            b.scatter(i + rng.uniform(-0.16, 0.16, len(v)), v, s=18, color=c, alpha=0.55, edgecolor="none")
            med = ds[col].abs().median()
            b.hlines(med, i - 0.3, i + 0.3, color=F.INK, lw=2)
            b.text(i + 0.33, med, f"{t['med']} {F.num(med, lang, 1)} %", fontsize=8.5, va="center")
        b.set_xticks([0, 1]); b.set_xticklabels([t["m"], t["p"]]); b.set_xlim(-0.5, 1.9); b.set_ylim(0, 82)
        b.set_ylabel(t["y2"]); b.set_title(t["h2"], fontsize=10.5, loc="left")
        F.finish(fig, HERE, "model_tests", lang, t["title"], t["sub"], top=0.78, bottom=0.2, left=0.08)
    print("OK model_tests")


if __name__ == "__main__":
    main()
