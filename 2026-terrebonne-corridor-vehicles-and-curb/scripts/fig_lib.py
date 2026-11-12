"""Shared chart style (the palette of the other OpenMobilityData repositories, checked with the dataviz palette
validator). Text wears ink colours, never the series colour."""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corridor_lib import ROOT, TABLES  # noqa: E402

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID, AXIS, SURFACE, GREY = "#1f2428", "#5f6b74", "#e2e4e1", "#c9cdd2", "#ffffff", "#9aa3ab"
SEQ = matplotlib.colors.LinearSegmentedColormap.from_list("blue", ["#e6eff9", "#9cc0ea", "#2a78d6", "#123f7a"])
SRC = {
    "en": "Sources: SAAQ, vehicles released under the access Act (file 03.06.34729), December 31, 2024, type inferred; Statistics Canada, 2021 Census;\n"
          "City of Montréal, géobase, parking-sign inventory and assessment roll (CC BY 4.0). Automobiles below the FSA are MODELLED, not measured.",
    "fr": "Sources : SAAQ, véhicules communiqués en vertu de la Loi sur l’accès (dossier 03.06.34729), 31 décembre 2024, type inféré ; Statistique Canada,\n"
          "Recensement de 2021 ; Ville de Montréal, géobase, inventaire de la signalisation de stationnement et rôle foncier (CC BY 4.0).\n"
          "Sous la RTA, les automobiles sont MODÉLISÉES, non mesurées.",
}
plt.rcParams.update({
    "font.family": "Helvetica Neue", "font.size": 10, "text.color": INK, "axes.labelcolor": MUTED,
    "axes.edgecolor": AXIS, "xtick.color": MUTED, "ytick.color": MUTED, "axes.spines.top": False,
    "axes.spines.right": False, "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y",
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True, "xtick.major.size": 0,
    "ytick.major.size": 0, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "svg.fonttype": "none",
    "legend.frameon": False,
})


def num(x, lang, dec=0):
    s = f"{x:,.{dec}f}"
    return s if lang == "en" else s.replace(",", " ").replace(".", ",")


def numbers():
    return json.load(open(ROOT / "derived/numbers.json"))


def corridor():
    d = pd.read_csv(TABLES / "da_corridor.csv", dtype={"dauid": str})
    return d[d.set == "corridor"].sort_values(["west_to_east", "frontage"]).reset_index(drop=True)


def row_bands(ax, n):
    """One band per row so that the markers of an area read as a group: alternate rows shaded, a thin rule between rows."""
    for i in range(n):
        if i % 2 == 0:
            ax.axhspan(i - 0.5, i + 0.5, color="#f1f2f0", zorder=0, lw=0)
    for i in range(n + 1):
        ax.axhline(i - 0.5, color=GRID, lw=0.8, zorder=0.5)
    ax.set_ylim(-0.5, n - 0.5)
    ax.tick_params(axis="y", length=0)


def fr_frontage(s):
    return s.replace("west end", "extrémité ouest").replace("N:", "N :").replace("S:", "S :")


def finish(fig, here, stem, lang, title, subtitle, note="", top=0.84, bottom=0.17, left=0.07, right=0.97):
    fig.text(0.012, 0.975, title, fontsize=13, fontweight="bold", va="top")
    fig.text(0.012, 0.925, subtitle, fontsize=10, color=MUTED, va="top")
    fig.text(0.012, 0.012, (note + "\n" if note else "") + SRC[lang], fontsize=7.5, color=MUTED, va="bottom")
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)
    for ext in ("png", "svg"):
        fig.savefig(Path(here) / f"{stem}_{lang}.{ext}", dpi=200)
    plt.close(fig)
